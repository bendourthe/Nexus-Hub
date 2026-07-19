import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import { StatusBarManager } from "./statusBarManager";
import {
  UsageProvider,
  ProviderFetchError,
  CodexUsageProvider,
  describeProviderError,
} from "./providers";
import { DashboardPanel } from "./dashboardPanel";
import { SettingsPanel } from "./settingsPanel";
import { WarningViewProvider, WARNING_VIEW_ID, WARNING_ACTIVE_CONTEXT } from "./warningView";
import { getRecommendation, getActiveUrgency, pickTriggerMetric, buildUsageSuggestion, classifyUrgency } from "./recommendations";
import { UrgencyLevel, UsageData, getThresholdConfig, getNotificationTimeoutMs, syncColorsToWorkbench, getColorConfig } from "./types";

type NotificationSeverity = "info" | "warning";

/**
 * Show a non-blocking, self-dismissing notification. Uses
 * `vscode.window.withProgress` because `showWarningMessage` cannot be
 * programmatically dismissed - if VS Code is in the background, those popups
 * stack indefinitely until the user clicks each X.
 *
 * The timeout is clamped to a sane range; the user can also click the X (cancel)
 * to dismiss early. The "_severity" parameter is reserved for future styling;
 * `withProgress` itself does not support a severity color, but we honor the
 * argument so call-sites read consistently.
 */
function showAutoDismissNotification(message: string, _severity: NotificationSeverity = "warning"): void {
  const timeoutMs = getNotificationTimeoutMs();
  void vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: message,
      cancellable: true,
    },
    async (_progress, token) => {
      return new Promise<void>((resolve) => {
        const timer = setTimeout(resolve, timeoutMs);
        token.onCancellationRequested(() => {
          clearTimeout(timer);
          resolve();
        });
      });
    }
  );
}

const RECOMMEND_COMMAND = "codex-usage.recommend";
const RESET_COMMAND = "codex-usage.reset";
const DASHBOARD_COMMAND = "codex-usage.dashboard";
const REFRESH_COMMAND = "codex-usage.refresh";
const SETTINGS_COMMAND = "codex-usage.settings";
const MANUAL_COMMAND = "codex-usage.enterManual";

// The ChatGPT usage/limits page users read to enter usage manually.
const CODEX_USAGE_PAGE_URL = "https://chatgpt.com/codex/settings/usage";

let consecutiveFailures = 0;
let lastFetchError: ProviderFetchError | undefined;
let failureNotificationShown = false;
let fetchInFlight = false;
// The warning WebviewView provider, created in activate() so evaluateAndNotify
// (module-level) can reveal the sidebar warning when a threshold is crossed.
let warningView: WarningViewProvider | undefined;

// In-memory threshold tracker — intentionally not persisted so it resets on every
// VS Code startup. This ensures the user sees a notification on startup when usage
// is already above a threshold, while still avoiding duplicate popups within a session.
const notifiedThresholds = new Set<number>();

export function activate(context: vscode.ExtensionContext): void {
  // The warning sidebar starts hidden; it is revealed only when a threshold fires.
  void vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, false);
  warningView = new WarningViewProvider();
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(WARNING_VIEW_ID, warningView, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
  );

  const store = new UsageStore(context.globalState);
  const provider = new CodexUsageProvider();
  const statusBar = new StatusBarManager(store, DASHBOARD_COMMAND, SETTINGS_COMMAND);

  const config = vscode.workspace.getConfiguration("codexUsage");
  if (config.get<boolean>("showInStatusBar", true)) {
    statusBar.show();
  }

  // Wire up auto-refresh: when the timer fires, trigger a fetch
  statusBar.setAutoRefreshCallback(() => autoFetchAndUpdate(provider, store, statusBar));

  // Wire up reset-expiry detection: when a cached reset timestamp passes, refetch
  statusBar.setResetExpiredCallback(() => autoFetchAndUpdate(provider, store, statusBar));

  // Apply user color settings to workbench.colorCustomizations on startup
  syncColorsToWorkbench(getColorConfig());

  // Auto-fetch on activation (silent)
  if (config.get<boolean>("autoFetch", true)) {
    autoFetchAndUpdate(provider, store, statusBar);
  }

  // Command: Show dashboard panel
  const dashboardCommand = vscode.commands.registerCommand(DASHBOARD_COMMAND, () => {
    const data = store.getWithFreshCountdowns();
    const timeSince = store.getTimeSinceUpdate();

    DashboardPanel.show(data, timeSince, lastFetchError, {
      onRefresh: async () => {
        statusBar.showLoading();
        await autoFetchAndUpdate(provider, store, statusBar);
      },
      onOpenUsagePage: () =>
        vscode.env.openExternal(vscode.Uri.parse(CODEX_USAGE_PAGE_URL)),
      onOpenSettings: () => vscode.commands.executeCommand(SETTINGS_COMMAND),
      onEnterManual: () => vscode.commands.executeCommand(MANUAL_COMMAND),
    }, context.extensionUri);
  });

  // Command: Refresh
  const refreshCommand = vscode.commands.registerCommand(REFRESH_COMMAND, async () => {
    statusBar.showLoading();
    const result = await provider.fetchUsage();
    if (result.success) {
      consecutiveFailures = 0;
      lastFetchError = undefined;
      failureNotificationShown = false;
      statusBar.resetBackoff();
      await store.save(result.data);
      await evaluateAndNotify(result.data);
      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
      showAutoDismissNotification("Codex Usage: usage data refreshed.", "info");
    } else {
      statusBar.refresh();
      if (result.error.code !== "rate-limited") {
        showAutoDismissNotification(
          `Codex Usage: fetch failed - ${describeProviderError(result.error)}`,
          "warning"
        );
      }
    }
  });

  // Command: Show recommendation
  const recommendCommand = vscode.commands.registerCommand(RECOMMEND_COMMAND, () => {
    const data = store.get();

    if (!data) {
      vscode.window
        .showInformationMessage(
          "No usage data available. Run 'Codex Usage: Refresh' first.",
          "Refresh Now"
        )
        .then((action) => {
          if (action === "Refresh Now") {
            vscode.commands.executeCommand(REFRESH_COMMAND);
          }
        });
      return;
    }

    const recommendation = getRecommendation(data);
    const timeSince = store.getTimeSinceUpdate();

    const items: vscode.QuickPickItem[] = [
      {
        label: `$(info) ${recommendation.message}`,
        description: `Updated ${timeSince}`,
      },
    ];

    items.push({ label: "", kind: vscode.QuickPickItemKind.Separator });

    for (const tip of recommendation.tips) {
      items.push({ label: `$(lightbulb) ${tip}` });
    }

    items.push({ label: "", kind: vscode.QuickPickItemKind.Separator });
    items.push({
      label: "$(refresh) Refresh usage data",
      description: "Fetch latest usage from API",
    });

    vscode.window
      .showQuickPick(items, {
        title: "Codex Usage: Recommendation",
        placeHolder: "Review recommendation and tips",
      })
      .then((selected) => {
        if (selected?.label.includes("Refresh usage data")) {
          vscode.commands.executeCommand(REFRESH_COMMAND);
        }
      });
  });

  // Command: Open settings panel
  const settingsCommand = vscode.commands.registerCommand(SETTINGS_COMMAND, () => {
    SettingsPanel.show(context.extensionUri);
  });

  // Command: Enter usage manually (the guaranteed fallback when the undocumented
  // ChatGPT usage endpoint cannot be read). Writes a dataSource:"manual" record,
  // which the status bar and dashboard already render.
  const manualCommand = vscode.commands.registerCommand(MANUAL_COMMAND, async () => {
    const data = await promptManualUsage();
    if (!data) {
      return; // user cancelled
    }
    await store.save(data);
    await store.saveLastUrgency(getActiveUrgency(data));
    statusBar.refresh();
    DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
    showAutoDismissNotification("Codex Usage: manual usage saved.", "info");
  });

  // Command: Clear stored data
  const resetCommand = vscode.commands.registerCommand(RESET_COMMAND, async () => {
    const confirm = await vscode.window.showWarningMessage(
      "Clear all stored Codex usage data?",
      { modal: true },
      "Clear"
    );

    if (confirm === "Clear") {
      await store.clear();
      statusBar.refresh();
      vscode.window.showInformationMessage("Codex usage data cleared.");
    }
  });

  // Watch for config changes
  const configWatcher = vscode.workspace.onDidChangeConfiguration((event) => {
    if (event.affectsConfiguration("codexUsage.showInStatusBar")) {
      const show = vscode.workspace
        .getConfiguration("codexUsage")
        .get<boolean>("showInStatusBar", true);
      if (show) {
        statusBar.show();
      } else {
        statusBar.hide();
      }
    }

    if (
      event.affectsConfiguration("codexUsage.refreshInterval") ||
      event.affectsConfiguration("codexUsage.autoFetch")
    ) {
      statusBar.hide();
      statusBar.show();
    }

    // When threshold, color, or metric settings change, re-evaluate the status bar immediately.
    if (
      event.affectsConfiguration("codexUsage.thresholds") ||
      event.affectsConfiguration("codexUsage.colors") ||
      event.affectsConfiguration("codexUsage.thresholdMetric")
    ) {
      statusBar.refresh();
      DashboardPanel.updateIfOpen(
        store.getWithFreshCountdowns(),
        store.getTimeSinceUpdate(),
        lastFetchError,
      );
    }
  });

  context.subscriptions.push(
    dashboardCommand,
    refreshCommand,
    recommendCommand,
    resetCommand,
    settingsCommand,
    manualCommand,
    configWatcher,
    { dispose: () => statusBar.dispose() }
  );
}

export function deactivate(): void {
  // Cleanup handled by subscriptions
}

async function autoFetchAndUpdate(
  provider: UsageProvider,
  store: UsageStore,
  statusBar: StatusBarManager,
): Promise<void> {
  if (fetchInFlight) {
    // A fetch is already running; clear any loading states that the caller may have set
    statusBar.refresh();
    DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
    return;
  }
  fetchInFlight = true;
  try {
    const result = await provider.fetchUsage();
    if (result.success) {
      consecutiveFailures = 0;
      lastFetchError = undefined;
      failureNotificationShown = false;
      statusBar.resetBackoff();

      const previousUrgency = store.getLastUrgency();
      await store.save(result.data);

      const newUrgency = getActiveUrgency(result.data);
      await store.saveLastUrgency(newUrgency);

      // Evaluate suggestion thresholds and show one-time notifications.
      // If a suggestion notification fired, skip the urgency-escalation notification
      // — both describe the same event and would produce a duplicate popup.
      const suggestionFired = await evaluateAndNotify(result.data);

      if (!suggestionFired && previousUrgency && urgencyEscalated(previousUrgency, newUrgency)) {
        const recommendation = getRecommendation(result.data);
        showAutoDismissNotification(`Codex Usage: ${recommendation.message}`, "warning");
      }

      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
    } else {
      consecutiveFailures++;
      lastFetchError = result.error;

      if (result.error.code === "rate-limited") {
        statusBar.applyBackoff();
        // Don't show a popup for rate-limiting; showing cached data is enough.
      } else if (consecutiveFailures >= 2 && !failureNotificationShown) {
        // Only show popup for actionable errors
        failureNotificationShown = true;
        showAutoDismissNotification(
          `Codex Usage: auto-fetch failed - ${describeProviderError(result.error)}`,
          "warning"
        );
      }

      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
    }
  } finally {
    fetchInFlight = false;
  }
}

/**
 * Evaluate usage against suggestion thresholds and show a one-time VS Code
 * notification the first time each threshold is crossed in a session.
 * Uses an in-memory set so the state resets on every VS Code startup — this
 * guarantees the user sees a notification on launch when usage is already high.
 * Only the highest unnotified threshold fires a notification per evaluation.
 * Metric selection and message wording live in pickTriggerMetric /
 * buildUsageSuggestion (recommendations.ts), shared with the dashboard so the
 * popup and the dashboard suggestion always agree.
 * Returns true if a notification was shown, false otherwise.
 */
async function evaluateAndNotify(data: UsageData): Promise<boolean> {
  const trigger = pickTriggerMetric(data);
  const suggestion = buildUsageSuggestion(data, trigger);

  // Below the moderate threshold: reset within-session tracking.
  if (!suggestion) {
    notifiedThresholds.clear();
    return false;
  }

  // Already notified for this bucket in the current session — nothing to do.
  if (notifiedThresholds.has(suggestion.bucket)) {
    return false;
  }

  // Mark this bucket and every lower one as notified so they never fire
  // individually if usage continues to climb during the same session.
  const t = getThresholdConfig();
  [t.critical, t.high, t.moderate].filter(thresh => trigger.percent >= thresh).forEach(thresh => notifiedThresholds.add(thresh));

  // Reveal the rich warning in its narrow sidebar view (icons + usage ring +
  // stacked recommendations): VS Code notifications render `$(...)` literally and
  // collapse newlines, so the mockup's layout is only achievable in a webview.
  // A single view is reused across threshold crossings, and the notifiedThresholds
  // dedup above means it reveals at most once per bucket per session.
  await warningView?.show(
    suggestion,
    classifyUrgency(trigger.percent),
    { onOpenDashboard: () => vscode.commands.executeCommand(DASHBOARD_COMMAND) },
  );
  return true;
}

const URGENCY_ORDER: Record<UrgencyLevel, number> = {
  low: 0,
  moderate: 1,
  high: 2,
  critical: 3,
};

function urgencyEscalated(previous: UrgencyLevel, current: UrgencyLevel): boolean {
  return URGENCY_ORDER[current] > URGENCY_ORDER[previous];
}

/**
 * Prompt for the user's current Codex usage percentages and build a manual
 * {@link UsageData} record. Returns undefined if the user cancels either prompt.
 * This is the guaranteed fallback when the undocumented ChatGPT usage endpoint
 * cannot be read: the numbers come from the user reading their own usage page.
 */
async function promptManualUsage(): Promise<UsageData | undefined> {
  const session = await promptPercent(
    "Current 5-hour (session) usage %",
    "A whole number 0-100, read from your ChatGPT usage page",
  );
  if (session == null) {
    return undefined;
  }
  const weekly = await promptPercent(
    "Weekly usage %",
    "A whole number 0-100, read from your ChatGPT usage page",
  );
  if (weekly == null) {
    return undefined;
  }
  return {
    session: { percent: session, resetsIn: "N/A", resetsAt: null },
    weeklyAllModels: { percent: weekly, resetsIn: "N/A", resetsAt: null },
    currentModel: "Codex",
    lastUpdated: Date.now(),
    dataSource: "manual",
    planLabel: "Codex",
  };
}

/** Show an input box that accepts a whole number 0-100, or undefined on cancel. */
async function promptPercent(prompt: string, placeHolder: string): Promise<number | undefined> {
  const raw = await vscode.window.showInputBox({
    title: "Codex Usage: Enter Usage Manually",
    prompt,
    placeHolder,
    validateInput: (value) => {
      const n = Number(value.trim());
      if (value.trim() === "" || !Number.isFinite(n) || n < 0 || n > 100) {
        return "Enter a whole number between 0 and 100.";
      }
      return undefined;
    },
  });
  if (raw == null) {
    return undefined;
  }
  return Math.round(Number(raw.trim()));
}
