import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import { StatusBarManager } from "./statusBarManager";
import {
  CopilotOrganizationProvider,
  CopilotUsageProvider,
  connectOrganization,
  describeProviderError,
  disconnectOrganization,
  signIn,
  switchAccount,
} from "./providers";
import { configuredOrganization, disconnectMessage, organizationRoute } from "./providers/copilotOrganization";
import { DashboardPanel } from "./dashboardPanel";
import type { OrganizationStatus } from "./settingsPanel";
import { WarningViewProvider, WARNING_VIEW_ID, WARNING_ACTIVE_CONTEXT } from "./warningView";
import { buildUsageSuggestion, classifyUrgency, getActiveUrgency, getRecommendation, triggerPercent } from "./recommendations";
import { CONFIG_SECTION, UrgencyLevel, UsageData, getColorConfig, getNotificationTimeoutMs, getThresholdConfig, syncColorsToWorkbench } from "./types";
import { registerUpdateWatcher } from "./updateWatcher";
import { UsageService } from "./usageService";
import { UsageController } from "./usageController";

const DASHBOARD_COMMAND = "copilot-usage.dashboard";
const REFRESH_COMMAND = "copilot-usage.refresh";
const RECOMMEND_COMMAND = "copilot-usage.recommend";
const RESET_COMMAND = "copilot-usage.reset";
const SETTINGS_COMMAND = "copilot-usage.settings";
const CONNECT_COMMAND = "copilot-usage.connectOrganization";
const DISCONNECT_COMMAND = "copilot-usage.disconnectOrganization";
const SIGN_IN_COMMAND = "copilot-usage.signIn";
const SWITCH_ACCOUNT_COMMAND = "copilot-usage.switchAccount";

const PERSONAL_USAGE_PAGE_URL = "https://github.com/settings/billing";

/**
 * A self-dismissing notification. `withProgress` is used because
 * `showWarningMessage` cannot be dismissed programmatically and stacks while
 * VS Code is in the background.
 */
function showAutoDismissNotification(message: string): void {
  const timeoutMs = getNotificationTimeoutMs();
  void vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: message, cancellable: true },
    async (_progress, token) =>
      new Promise<void>((resolve) => {
        const timer = setTimeout(resolve, timeoutMs);
        token.onCancellationRequested(() => {
          clearTimeout(timer);
          resolve();
        });
      }),
  );
}

let warningView: WarningViewProvider | undefined;
let failureNotificationShown = false;
// In memory on purpose: a restart shows the warning again when usage is already high.
const notifiedThresholds = new Set<number>();

export function activate(context: vscode.ExtensionContext): void {
  registerUpdateWatcher(context, "Copilot Usage Monitor");
  void vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, false);
  warningView = new WarningViewProvider();
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(WARNING_VIEW_ID, warningView, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
  );

  const store = new UsageStore(context.globalState);
  const statusBar = new StatusBarManager(store, DASHBOARD_COMMAND);
  const service = new UsageService(new CopilotUsageProvider(), new CopilotOrganizationProvider(context.secrets));
  const controller = new UsageController(store, service, statusBar);

  const orgStatus = async (): Promise<OrganizationStatus> => {
    const connected = (await organizationRoute(context.secrets)) !== "none";
    return { configured: configuredOrganization() !== "", connected };
  };

  const redrawDashboard = async (): Promise<void> => {
    DashboardPanel.updateIfOpen(store.get(), store.getTimeSinceUpdate(), controller.lastFetchError, await orgStatus());
  };

  const fetchAndNotify = async (): Promise<void> => {
    const previousUrgency = store.getLastUrgency();
    const result = await controller.refresh();
    if (result.success) {
      failureNotificationShown = false;
      const urgency = getActiveUrgency(result.data);
      await store.saveLastUrgency(urgency);
      const fired = await evaluateAndNotify(result.data);
      if (!fired && previousUrgency && URGENCY_ORDER[urgency] > URGENCY_ORDER[previousUrgency]) {
        showAutoDismissNotification(`Copilot Usage: ${getRecommendation(result.data).message}`);
      }
    } else if (
      result.error.code !== "rate-limited" &&
      controller.consecutiveFailures >= 2 &&
      !failureNotificationShown
    ) {
      failureNotificationShown = true;
      showAutoDismissNotification(`Copilot Usage: auto-fetch failed. ${describeProviderError(result.error)}`);
    }
    await redrawDashboard();
  };

  const openDashboard = async (): Promise<void> => {
    DashboardPanel.show(
      store.get(),
      store.getTimeSinceUpdate(),
      controller.lastFetchError,
      await orgStatus(),
      {
        onRefresh: () => {
          statusBar.showLoading();
          void fetchAndNotify();
        },
        onOpenUsagePage: () => {
          const org = configuredOrganization();
          const url = org
            ? `https://github.com/organizations/${encodeURIComponent(org)}/settings/billing/ai_usage`
            : PERSONAL_USAGE_PAGE_URL;
          void vscode.env.openExternal(vscode.Uri.parse(url));
        },
        onSignIn: () => void vscode.commands.executeCommand(SIGN_IN_COMMAND),
        onSwitchAccount: () => void vscode.commands.executeCommand(SWITCH_ACCOUNT_COMMAND),
        onConnectOrganization: () => void vscode.commands.executeCommand(CONNECT_COMMAND),
        onDisconnectOrganization: () => void vscode.commands.executeCommand(DISCONNECT_COMMAND),
      },
      context.extensionUri,
    );
  };

  if (vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("showInStatusBar", true)) {
    statusBar.show();
  }
  statusBar.setAutoRefreshCallback(fetchAndNotify);
  statusBar.setResetExpiredCallback(() => void fetchAndNotify());
  void syncColorsToWorkbench(getColorConfig());
  if (vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("autoFetch", true)) {
    void fetchAndNotify();
  }

  context.subscriptions.push(
    vscode.commands.registerCommand(DASHBOARD_COMMAND, openDashboard),
    vscode.commands.registerCommand(REFRESH_COMMAND, async () => {
      statusBar.showLoading();
      await fetchAndNotify();
      if (controller.lastFetchError && controller.lastFetchError.code !== "rate-limited") {
        showAutoDismissNotification(`Copilot Usage: fetch failed. ${describeProviderError(controller.lastFetchError)}`);
      } else if (!controller.lastFetchError) {
        showAutoDismissNotification("Copilot Usage: usage data refreshed.");
      }
    }),
    vscode.commands.registerCommand(RECOMMEND_COMMAND, async () => {
      const data = store.get();
      if (!data) {
        const action = await vscode.window.showInformationMessage(
          "No Copilot usage data yet. Run 'Copilot Usage: Refresh' first.",
          "Refresh Now",
        );
        if (action === "Refresh Now") {
          void vscode.commands.executeCommand(REFRESH_COMMAND);
        }
        return;
      }
      const recommendation = getRecommendation(data);
      const items: vscode.QuickPickItem[] = [
        { label: `$(info) ${recommendation.message}`, description: `Updated ${store.getTimeSinceUpdate()}` },
        { label: "", kind: vscode.QuickPickItemKind.Separator },
        ...recommendation.tips.map((tip) => ({ label: `$(lightbulb) ${tip}` })),
        { label: "", kind: vscode.QuickPickItemKind.Separator },
        { label: "$(refresh) Refresh usage data", description: "Fetch the latest usage from GitHub" },
      ];
      const selected = await vscode.window.showQuickPick(items, {
        title: "Copilot Usage: Recommendation",
        placeHolder: "Review recommendation and tips",
      });
      if (selected?.label.includes("Refresh usage data")) {
        void vscode.commands.executeCommand(REFRESH_COMMAND);
      }
    }),
    vscode.commands.registerCommand(SETTINGS_COMMAND, async () => {
      await openDashboard();
      DashboardPanel.revealSettings();
    }),
    vscode.commands.registerCommand(RESET_COMMAND, async () => {
      const confirm = await vscode.window.showWarningMessage(
        "Clear all stored Copilot usage data? The organization connection is kept.",
        { modal: true },
        "Clear",
      );
      if (confirm === "Clear") {
        await controller.clear();
        await redrawDashboard();
        void vscode.window.showInformationMessage("Copilot usage data cleared.");
      }
    }),
    vscode.commands.registerCommand(CONNECT_COMMAND, async () => {
      if ((await connectOrganization(context.secrets)) === "connected") {
        await fetchAndNotify();
      }
      await redrawDashboard();
    }),
    vscode.commands.registerCommand(DISCONNECT_COMMAND, async () => {
      const route = await disconnectOrganization(context.secrets);
      await controller.organizationRemoved();
      await redrawDashboard();
      void vscode.window.showInformationMessage(disconnectMessage(route));
    }),
    vscode.commands.registerCommand(SIGN_IN_COMMAND, async () => {
      if (await signIn()) {
        await fetchAndNotify();
      }
    }),
    vscode.commands.registerCommand(SWITCH_ACCOUNT_COMMAND, async () => {
      if (await switchAccount()) {
        await fetchAndNotify();
      }
    }),
    vscode.authentication.onDidChangeSessions((event) => {
      if (event.provider.id === "github") {
        void fetchAndNotify();
      }
    }),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration(`${CONFIG_SECTION}.showInStatusBar`)) {
        if (vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("showInStatusBar", true)) {
          statusBar.show();
        } else {
          statusBar.hide();
        }
      }
      if (
        event.affectsConfiguration(`${CONFIG_SECTION}.refreshInterval`) ||
        event.affectsConfiguration(`${CONFIG_SECTION}.autoFetch`)
      ) {
        statusBar.hide();
        statusBar.show();
      }
      if (
        event.affectsConfiguration(`${CONFIG_SECTION}.writeUsageState`) &&
        !vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("writeUsageState", true)
      ) {
        controller.stateWritingDisabled();
      }
      if (
        event.affectsConfiguration(`${CONFIG_SECTION}.thresholds`) ||
        event.affectsConfiguration(`${CONFIG_SECTION}.colors`) ||
        event.affectsConfiguration(`${CONFIG_SECTION}.compactStatusBar`) ||
        event.affectsConfiguration(`${CONFIG_SECTION}.organization`)
      ) {
        statusBar.refresh();
        void redrawDashboard();
      }
    }),
    { dispose: () => statusBar.dispose() },
  );
}

export function deactivate(): void {
  // Cleanup is handled by subscriptions.
}

/**
 * Reveal the warning view the first time each threshold is crossed in this
 * session. Only the highest unnotified threshold fires per evaluation.
 */
async function evaluateAndNotify(data: UsageData): Promise<boolean> {
  const suggestion = buildUsageSuggestion(data);
  if (!suggestion) {
    notifiedThresholds.clear();
    return false;
  }
  if (notifiedThresholds.has(suggestion.bucket)) {
    return false;
  }
  const percent = triggerPercent(data);
  const t = getThresholdConfig();
  [t.critical, t.high, t.moderate].filter((threshold) => percent >= threshold).forEach((threshold) => notifiedThresholds.add(threshold));
  await warningView?.show(suggestion, classifyUrgency(percent), {
    onOpenDashboard: () => vscode.commands.executeCommand(DASHBOARD_COMMAND),
  });
  return true;
}

const URGENCY_ORDER: Record<UrgencyLevel, number> = { low: 0, moderate: 1, high: 2, critical: 3 };
