import * as vscode from "vscode";
import { DashboardPanel } from "./dashboardPanel";
import {
  buildManualSnapshot,
  manualEntryTemplate,
  parseManualSnapshotInput,
  type ManualSnapshotInput
} from "./manualEntry";
import {
  buildUsageSuggestion,
  crossedUnnotifiedThreshold,
  type NotifiedSeverity,
  type UsageSuggestion
} from "./recommendations";
import { readSettings, SettingsPanel } from "./settingsPanel";
import { StatusBarManager } from "./statusBarManager";
import type {
  FreshUsageSnapshot,
  ProviderResult,
  UsageSnapshot,
  UsageState
} from "./types";
import { describeProvenance, UsageStore } from "./usageStore";
import { providerError } from "./providers/errors";
import {
  ICONS8_ATTRIBUTION_URL,
  WARNING_ACTIVE_CONTEXT,
  WARNING_VIEW_ID,
  WarningViewProvider
} from "./warningView";

export const COMMAND_IDS = {
  dashboard: "cursor-usage.dashboard",
  refresh: "cursor-usage.refresh",
  recommend: "cursor-usage.recommend",
  settings: "cursor-usage.settings",
  manualEntry: "cursor-usage.manualEntry",
  clearData: "cursor-usage.clearData",
  revokeConsent: "cursor-usage.revokeConsent",
  connectLive: "cursor-usage.connectLive",
  openNativeSettings: "cursor-usage.openNativeSettings",
  openUsagePage: "cursor-usage.openUsagePage"
} as const;

const CURSOR_USAGE_PAGE_URL = "https://cursor.com/dashboard/usage";
const EXTENSION_SETTINGS_QUERY = "@ext:nexus-hub.cursor-usage-monitor";
const CONFIGURATION_SECTION = "cursorUsage";
const REFRESH_PERSISTENCE_ERROR =
  "Cursor Usage: could not save refreshed usage. Existing data remains displayed.";
const MANUAL_PERSISTENCE_ERROR =
  "Cursor Usage: could not save manual usage. Existing data remains displayed.";
const CLEAR_PERSISTENCE_ERROR =
  "Cursor Usage: could not clear stored usage. Existing data remains displayed.";
const REVOKE_PERSISTENCE_ERROR =
  "Cursor Usage: could not fully revoke live access. Existing data remains displayed.";

interface UsageProviderLike {
  fetch(signal?: AbortSignal): Promise<ProviderResult<UsageSnapshot>>;
}

type IntervalHandle = ReturnType<typeof setInterval>;
type TimeoutHandle = ReturnType<typeof setTimeout>;
type RefreshReason = "automatic" | "manual";

export interface RuntimeDependencies {
  provider: UsageProviderLike;
  /**
   * A boolean for a fixed capability, or a thunk when the answer is resolved
   * asynchronously after activation (session adapter present, consent granted).
   */
  liveTransportCapable: boolean | (() => boolean);
  /** Clears the live-transport consent decision. Absent when no gate is wired. */
  revokeLiveConsent?: () => Promise<void>;
  /**
   * Re-asks for live-transport consent and re-resolves capability, returning
   * whether live access ended up available.
   *
   * This exists because a DECLINED decision is deliberately never re-prompted on a
   * timer or on activation - that is what stops the gate becoming nagware. But a
   * user who clicks "Connect" is asking, and refusing to re-ask them would leave the
   * decision permanently unreachable from the interface. An explicit action may
   * reopen a declined decision; automation may not.
   */
  reconnectLive?: () => Promise<boolean>;
  now?: () => number;
  setInterval?: (callback: () => void, delay: number) => IntervalHandle;
  clearInterval?: (handle: IntervalHandle) => void;
  setTimeout?: (callback: () => void, delay: number) => TimeoutHandle;
  clearTimeout?: (handle: TimeoutHandle) => void;
}

const CONFIGURATION_CHANGE_DEBOUNCE_MS = 50;

export class CursorUsageRuntime implements vscode.Disposable {
  private readonly store: UsageStore;
  private readonly statusBar = new StatusBarManager(COMMAND_IDS.dashboard);
  private readonly dashboard = new DashboardPanel();
  private readonly settings = new SettingsPanel();
  private readonly warningView: WarningViewProvider;
  private readonly disposables: vscode.Disposable[] = [];
  private readonly highestNotified = new Map<string, NotifiedSeverity>();
  private readonly now: () => number;
  private readonly scheduleInterval: (
    callback: () => void,
    delay: number
  ) => IntervalHandle;
  private readonly cancelInterval: (handle: IntervalHandle) => void;
  private readonly scheduleTimeout: (
    callback: () => void,
    delay: number
  ) => TimeoutHandle;
  private readonly cancelTimeout: (handle: TimeoutHandle) => void;
  private state: UsageState;
  private refreshPromise: Promise<void> | undefined;
  private refreshController: AbortController | undefined;
  private refreshTimer: IntervalHandle | undefined;
  private configurationTimer: TimeoutHandle | undefined;
  private generation = 0;
  private started = false;
  private disposed = false;

  public constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly dependencies: RuntimeDependencies
  ) {
    this.now = dependencies.now ?? Date.now;
    this.scheduleInterval =
      dependencies.setInterval ??
      ((callback, delay) => setInterval(callback, delay));
    this.cancelInterval =
      dependencies.clearInterval ?? ((handle) => clearInterval(handle));
    this.scheduleTimeout =
      dependencies.setTimeout ??
      ((callback, delay) => setTimeout(callback, delay));
    this.cancelTimeout =
      dependencies.clearTimeout ?? ((handle) => clearTimeout(handle));
    this.store = this.createStore();
    this.state = this.hydrate();
    this.warningView = new WarningViewProvider(context.extensionUri);
  }

  public start(): void {
    if (this.started || this.disposed) {
      return;
    }
    this.started = true;

    void vscode.commands.executeCommand(
      "setContext",
      WARNING_ACTIVE_CONTEXT,
      false
    );
    this.disposables.push(
      vscode.window.registerWebviewViewProvider(
        WARNING_VIEW_ID,
        this.warningView,
        { webviewOptions: { retainContextWhenHidden: true } }
      ),
      ...this.registerCommands(),
      vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration(CONFIGURATION_SECTION)) {
          this.scheduleConfigurationChanged();
        }
      })
    );

    void this.renderState();
    this.restartRefreshTimer();
    if (this.shouldPoll()) {
      void this.refresh("automatic");
    }
  }

  public refresh(reason: RefreshReason = "manual"): Promise<void> {
    if (this.disposed) {
      return Promise.resolve();
    }
    if (!this.liveCapable()) {
      this.state = this.hydrate();
      void this.renderState();
      if (reason === "manual") {
        void vscode.window.showInformationMessage(
          `Cursor Usage: live refresh is unavailable. ${this.provenanceNotice()}`
        );
      }
      return Promise.resolve();
    }
    if (this.refreshPromise !== undefined) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performRefresh(reason).finally(() => {
      this.refreshPromise = undefined;
    });
    return this.refreshPromise;
  }

  public dispose(): void {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.stopConfigurationTimer();
    this.stopRefreshTimer();
    this.cancelActiveRefresh();
    void this.warningView.dismiss();
    for (const disposable of this.disposables.splice(0).reverse()) {
      disposable.dispose();
    }
    this.dashboard.dispose();
    this.settings.dispose();
    this.statusBar.dispose();
    this.highestNotified.clear();
  }

  private registerCommands(): vscode.Disposable[] {
    return [
      vscode.commands.registerCommand(COMMAND_IDS.dashboard, () => {
        this.dashboard.show(this.state);
      }),
      vscode.commands.registerCommand(COMMAND_IDS.refresh, () =>
        this.refresh("manual")
      ),
      vscode.commands.registerCommand(COMMAND_IDS.recommend, () =>
        this.showRecommendation()
      ),
      vscode.commands.registerCommand(COMMAND_IDS.settings, () => {
        this.settings.show();
      }),
      vscode.commands.registerCommand(
        COMMAND_IDS.manualEntry,
        (input?: unknown) => this.saveManualEntry(input)
      ),
      vscode.commands.registerCommand(COMMAND_IDS.clearData, () =>
        this.clearData()
      ),
      vscode.commands.registerCommand(COMMAND_IDS.revokeConsent, () =>
        this.revokeConsent()
      ),
      vscode.commands.registerCommand(COMMAND_IDS.connectLive, () =>
        this.connectLive()
      ),
      vscode.commands.registerCommand(
        COMMAND_IDS.openNativeSettings,
        () =>
          vscode.commands.executeCommand(
            "workbench.action.openSettings",
            EXTENSION_SETTINGS_QUERY
          )
      ),
      vscode.commands.registerCommand(COMMAND_IDS.openUsagePage, () =>
        vscode.env.openExternal(vscode.Uri.parse(CURSOR_USAGE_PAGE_URL))
      )
    ];
  }

  private async performRefresh(reason: RefreshReason): Promise<void> {
    const generation = this.generation;
    const controller = new AbortController();
    this.refreshController = controller;
    if (this.showInStatusBar()) {
      this.statusBar.showLoading();
    }

    try {
      const result = await this.fetchUsage(controller.signal);
      if (this.refreshIsObsolete(controller, generation)) {
        return;
      }

      let nextState: UsageState;
      try {
        nextState = await this.store.resolveFetch(result, this.now());
      } catch {
        if (!this.refreshIsObsolete(controller, generation)) {
          await this.renderState(false);
          void vscode.window.showWarningMessage(REFRESH_PERSISTENCE_ERROR);
        }
        return;
      }
      if (this.refreshIsObsolete(controller, generation)) {
        return;
      }
      this.state = nextState;
      await this.renderState();
      if (reason === "manual") {
        const message = result.ok
          ? "Cursor Usage: usage data refreshed."
          : `Cursor Usage: ${result.error.message}`;
        void vscode.window.showInformationMessage(message);
      }
    } finally {
      if (this.refreshController === controller) {
        this.refreshController = undefined;
      }
    }
  }

  private async fetchUsage(
    signal: AbortSignal
  ): Promise<ProviderResult<UsageSnapshot>> {
    try {
      return await this.dependencies.provider.fetch(signal);
    } catch {
      return {
        ok: false,
        error: providerError("network-error", null)
      };
    }
  }

  private async saveManualEntry(input: unknown): Promise<void> {
    const draft =
      input === undefined
        ? await this.promptForManualEntry()
        : this.parseManualInput(input);
    if (draft === undefined) {
      return;
    }

    const result = buildManualSnapshot(draft, this.now());
    if (!result.ok) {
      void vscode.window.showWarningMessage(
        `Cursor Usage: ${result.errors.join(" ")}`
      );
      return;
    }

    let saved: FreshUsageSnapshot;
    try {
      saved = await this.store.saveManual(result.value);
    } catch {
      await this.renderState(false);
      void vscode.window.showWarningMessage(MANUAL_PERSISTENCE_ERROR);
      return;
    }
    this.state = { state: "fresh", data: saved };
    await this.renderState();
    void vscode.window.showInformationMessage(
      "Cursor Usage: manual usage saved locally."
    );
  }

  private async promptForManualEntry(): Promise<
    ManualSnapshotInput | undefined
  > {
    const raw = await vscode.window.showInputBox({
      title: "Cursor Usage: Manual Entry",
      prompt:
        "Enter a JSON usage snapshot. Values stay in extension global storage; credentials are never accepted here.",
      value: JSON.stringify(manualEntryTemplate())
    });
    if (raw === undefined) {
      return undefined;
    }

    try {
      return this.parseManualInput(JSON.parse(raw) as unknown);
    } catch {
      void vscode.window.showWarningMessage(
        "Cursor Usage: manual entry must be valid JSON."
      );
      return undefined;
    }
  }

  private parseManualInput(value: unknown): ManualSnapshotInput | undefined {
    const draft = parseManualSnapshotInput(value);
    if (draft === undefined) {
      void vscode.window.showWarningMessage(
        "Cursor Usage: manual entry does not match the expected usage schema."
      );
    }
    return draft;
  }

  private async clearData(): Promise<void> {
    const confirmation = await vscode.window.showWarningMessage(
      "Clear cached and manual Cursor usage data?",
      { modal: true },
      "Clear"
    );
    if (confirmation !== "Clear") {
      return;
    }

    const previousState = this.state;
    this.cancelActiveRefresh();
    try {
      await this.store.clear();
    } catch {
      this.state = previousState;
      await this.renderState(false);
      void vscode.window.showWarningMessage(CLEAR_PERSISTENCE_ERROR);
      return;
    }
    this.highestNotified.clear();
    await this.warningView.dismiss();
    this.state = emptyState();
    await this.renderState(false);
    void vscode.window.showInformationMessage(
      "Cursor Usage: stored usage and alert state cleared."
    );
  }

  /**
   * Re-evaluates live capability after activation resolved it asynchronously.
   * Called once consent and the session adapter have both been settled.
   */
  public capabilityChanged(): void {
    if (this.disposed || !this.started) {
      return;
    }
    this.restartRefreshTimer();
    if (this.shouldPoll()) {
      void this.refresh("automatic");
      return;
    }
    void this.renderState();
  }

  /**
   * Clears the consent decision and the credential-derived cache in one action, so
   * revoking never leaves behind data the session read produced. Manually entered
   * usage is the user's own and is deliberately preserved.
   */
  /**
   * Asks for live access again, then refreshes if it was granted.
   *
   * When no gate is wired (`reconnectLive` absent) this degrades to a plain refresh
   * rather than reporting a failure, so the button is never a dead control.
   */
  private async connectLive(): Promise<void> {
    if (this.dependencies.reconnectLive === undefined) {
      await this.refresh("manual");
      return;
    }
    const granted = await this.dependencies.reconnectLive();
    if (granted) {
      await this.refresh("manual");
      return;
    }
    // Declining is a first-class outcome, so it gets a plain statement of what
    // still works rather than an error or a second ask.
    void vscode.window.showInformationMessage(
      "Cursor Usage: live access was not granted. Stored and manually entered usage stay available."
    );
  }

  private async revokeConsent(): Promise<void> {
    const confirmation = await vscode.window.showWarningMessage(
      "Revoke live Cursor usage access? This clears the consent decision and any usage cached from it. Manually entered usage is kept.",
      { modal: true },
      "Revoke"
    );
    if (confirmation !== "Revoke") {
      return;
    }

    this.cancelActiveRefresh();
    try {
      await this.store.clearCache();
      await this.dependencies.revokeLiveConsent?.();
    } catch {
      await this.renderState(false);
      void vscode.window.showWarningMessage(REVOKE_PERSISTENCE_ERROR);
      return;
    }
    this.state = this.hydrate();
    this.restartRefreshTimer();
    await this.renderState(false);
    void vscode.window.showInformationMessage(
      "Cursor Usage: live access revoked and cached live usage cleared."
    );
  }

  private async showRecommendation(): Promise<void> {
    const suggestion = this.currentSuggestion();
    if (suggestion === null) {
      const message =
        this.state.state === "stale"
          ? "Cursor Usage: recommendations require fresh usage data."
          : "Cursor Usage: no threshold recommendation is active.";
      void vscode.window.showInformationMessage(message);
      return;
    }
    await this.showWarning(suggestion);
  }

  private onConfigurationChanged(): void {
    if (this.disposed) {
      return;
    }
    this.store.setStaleAfterMs(this.staleAfterMs());
    this.state = this.hydrate();
    this.restartRefreshTimer();
    this.settings.update();
    void this.renderState();
  }

  private scheduleConfigurationChanged(): void {
    if (this.disposed) {
      return;
    }
    this.stopConfigurationTimer();
    this.configurationTimer = this.scheduleTimeout(() => {
      this.configurationTimer = undefined;
      this.onConfigurationChanged();
    }, CONFIGURATION_CHANGE_DEBOUNCE_MS);
  }

  private stopConfigurationTimer(): void {
    if (this.configurationTimer === undefined) {
      return;
    }
    this.cancelTimeout(this.configurationTimer);
    this.configurationTimer = undefined;
  }

  private createStore(): UsageStore {
    return new UsageStore(this.context.globalState, this.staleAfterMs());
  }

  private staleAfterMs(): number {
    const staleAfterMinutes = this.configuration().get<number>(
      "staleAfterMinutes",
      30
    );
    return Math.max(1, staleAfterMinutes) * 60_000;
  }

  private hydrate(): UsageState {
    const snapshot =
      this.store.getCache(this.now()) ?? this.store.getManual(this.now());
    if (snapshot === undefined) {
      return emptyState();
    }
    if (!snapshot.stale) {
      return { state: "fresh", data: snapshot };
    }
    return {
      state: "stale",
      data: snapshot,
      error: {
        ...providerError("endpoint-unavailable", null),
        message: `${describeProvenance(snapshot)}. No fresh live usage is available.`
      }
    };
  }

  private async renderState(evaluateAlerts = true): Promise<void> {
    if (this.showInStatusBar()) {
      this.statusBar.show(this.state);
    } else {
      this.statusBar.hide();
    }
    this.dashboard.update(this.state);

    if (!evaluateAlerts) {
      return;
    }
    const suggestion = this.currentSuggestion();
    if (suggestion === null) {
      await this.warningView.dismiss();
      return;
    }
    if (!crossedUnnotifiedThreshold(suggestion, this.highestNotified)) {
      return;
    }
    this.highestNotified.set(
      suggestion.notificationKey,
      suggestion.severity
    );
    await this.showWarning(suggestion);
  }

  private currentSuggestion(): UsageSuggestion | null {
    const settings = readSettings();
    return buildUsageSuggestion(
      this.state,
      settings.alertMetric,
      settings.thresholds
    );
  }

  private async showWarning(suggestion: UsageSuggestion): Promise<void> {
    await this.warningView.show(suggestion, {
      onOpenDashboard: () => {
        void vscode.commands.executeCommand(COMMAND_IDS.dashboard);
      },
      onDismiss: () => undefined,
      onOpenAttribution: () => {
        void vscode.env.openExternal(vscode.Uri.parse(ICONS8_ATTRIBUTION_URL));
      }
    });
  }

  private configuration(): vscode.WorkspaceConfiguration {
    return vscode.workspace.getConfiguration(CONFIGURATION_SECTION);
  }

  private showInStatusBar(): boolean {
    return this.configuration().get<boolean>("showInStatusBar", true);
  }

  private shouldPoll(): boolean {
    return (
      this.liveCapable() && this.configuration().get<boolean>("autoFetch", true)
    );
  }

  private liveCapable(): boolean {
    const capability = this.dependencies.liveTransportCapable;
    return typeof capability === "function" ? capability() : capability;
  }

  /** Describes what is on screen right now, so a notice never implies live data. */
  private provenanceNotice(): string {
    if (this.state.state === "empty") {
      return "No cached or manual usage is stored yet.";
    }
    return `Showing ${describeProvenance(this.state.data).toLowerCase()}.`;
  }

  private restartRefreshTimer(): void {
    this.stopRefreshTimer();
    if (!this.shouldPoll()) {
      return;
    }
    const minutes = this.configuration().get<number>("refreshInterval", 10);
    this.refreshTimer = this.scheduleInterval(() => {
      void this.refresh("automatic");
    }, Math.max(1, minutes) * 60_000);
  }

  private stopRefreshTimer(): void {
    if (this.refreshTimer === undefined) {
      return;
    }
    this.cancelInterval(this.refreshTimer);
    this.refreshTimer = undefined;
  }

  private cancelActiveRefresh(): void {
    this.generation += 1;
    this.refreshController?.abort();
    this.refreshController = undefined;
  }

  private refreshIsObsolete(
    controller: AbortController,
    generation: number
  ): boolean {
    return (
      controller.signal.aborted ||
      this.disposed ||
      generation !== this.generation
    );
  }
}

function emptyState(): UsageState {
  return {
    state: "empty",
    error: {
      ...providerError("endpoint-unavailable", null),
      message:
        "No cached or manual Cursor usage is available. Allow live usage access, or enter usage manually."
    }
  };
}
