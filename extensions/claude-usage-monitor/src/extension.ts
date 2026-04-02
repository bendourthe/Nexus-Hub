import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import { StatusBarManager } from "./statusBarManager";
import { UsageFetcher, FetchError } from "./usageFetcher";
import { DashboardPanel } from "./dashboardPanel";
import { AutoSwitcher } from "./autoSwitcher";
import { getRecommendation, getOverallUrgency } from "./recommendations";
import { UrgencyLevel, AutoSwitchAction, UsageData, formatModelName } from "./types";

const RECOMMEND_COMMAND = "claude-usage.recommend";
const RESET_COMMAND = "claude-usage.reset";
const DASHBOARD_COMMAND = "claude-usage.dashboard";
const REFRESH_COMMAND = "claude-usage.refresh";

let consecutiveFailures = 0;
let lastFetchError: FetchError | undefined;
let failureNotificationShown = false;
let fetchInFlight = false;

export function activate(context: vscode.ExtensionContext): void {
  const log = vscode.window.createOutputChannel("Claude Usage Monitor");
  const store = new UsageStore(context.globalState);
  const fetcher = new UsageFetcher();
  const autoSwitcher = new AutoSwitcher(store, log);
  const statusBar = new StatusBarManager(store, DASHBOARD_COMMAND);

  const config = vscode.workspace.getConfiguration("claudeUsage");
  if (config.get<boolean>("showInStatusBar", true)) {
    statusBar.show();
  }

  // Wire up auto-refresh: when the timer fires, trigger a fetch
  statusBar.setAutoRefreshCallback(() => autoFetchAndUpdate(fetcher, store, statusBar, autoSwitcher, log));

  // Wire up reset-expiry detection: when a cached reset timestamp passes, refetch
  statusBar.setResetExpiredCallback(() => autoFetchAndUpdate(fetcher, store, statusBar, autoSwitcher, log));

  // Startup reminder: if a model switch is active from a previous session, notify once
  const startupState = store.getAutoSwitchState();
  if (startupState.modelAutoSwitched && startupState.switchedToModel) {
    const switchedTo = formatModelName(startupState.switchedToModel);
    const modelId = startupState.switchedToModel;
    vscode.window
      .showInformationMessage(
        `Auto-switch active: New conversations will use ${switchedTo}. To apply in your current conversation, run /model ${modelId} (or use the "/" button > Switch model).`,
        "Show Dashboard",
      )
      .then((choice) => {
        if (choice === "Show Dashboard") {
          vscode.commands.executeCommand(DASHBOARD_COMMAND);
        }
      });
  }

  // When new terminals open, apply pending model switch to Claude Code terminals
  const terminalListener = vscode.window.onDidOpenTerminal((terminal) => {
    autoSwitcher.applyPendingSwitchToTerminal(terminal);
  });

  // Auto-fetch on activation (silent)
  if (config.get<boolean>("autoFetch", true)) {
    autoFetchAndUpdate(fetcher, store, statusBar, autoSwitcher, log);
  }

  // Command: Show dashboard panel
  const dashboardCommand = vscode.commands.registerCommand(DASHBOARD_COMMAND, () => {
    const data = store.getWithFreshCountdowns();
    const timeSince = store.getTimeSinceUpdate();

    DashboardPanel.show(data, timeSince, lastFetchError, {
      onRefresh: async () => {
        statusBar.showLoading();
        await autoFetchAndUpdate(fetcher, store, statusBar, autoSwitcher, log);
      },
      onOpenUsagePage: () =>
        vscode.env.openExternal(vscode.Uri.parse("https://claude.ai/settings/usage")),
    }, context.extensionUri, store.getAutoSwitchState());
  });

  // Command: Refresh
  const refreshCommand = vscode.commands.registerCommand(REFRESH_COMMAND, async () => {
    statusBar.showLoading();
    const result = await fetcher.fetch(store.getCurrentModel());
    if (result.success) {
      consecutiveFailures = 0;
      lastFetchError = undefined;
      failureNotificationShown = false;
      statusBar.resetBackoff();
      await store.save(result.data);
      await evaluateAndNotify(result.data, store, autoSwitcher, log);
      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError, store.getAutoSwitchState());
      vscode.window.showInformationMessage("Claude usage data refreshed.");
    } else {
      statusBar.refresh();
      if (result.error.code !== "rate-limited") {
        vscode.window.showWarningMessage(
          `Fetch failed: ${UsageFetcher.getErrorMessage(result.error)}`,
          "Dismiss"
        );
      }
    }
  });

  // Command: Show model recommendation
  const recommendCommand = vscode.commands.registerCommand(RECOMMEND_COMMAND, () => {
    const data = store.get();

    if (!data) {
      vscode.window
        .showInformationMessage(
          "No usage data available. Run 'Claude Usage: Refresh' first.",
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

    if (recommendation.suggestedModel) {
      items.push({
        label: `$(arrow-right) Suggested: ${formatModelName(recommendation.suggestedModel)}`,
        description: "Use this model for your current tasks",
      });
    }

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
        title: "Claude Usage: Model Recommendation",
        placeHolder: "Review recommendation and tips",
      })
      .then((selected) => {
        if (selected?.label.includes("Refresh usage data")) {
          vscode.commands.executeCommand(REFRESH_COMMAND);
        }
      });
  });

  // Command: Clear stored data
  const resetCommand = vscode.commands.registerCommand(RESET_COMMAND, async () => {
    const confirm = await vscode.window.showWarningMessage(
      "Clear all stored Claude usage data?",
      { modal: true },
      "Clear"
    );

    if (confirm === "Clear") {
      await store.clear();
      statusBar.refresh();
      vscode.window.showInformationMessage("Claude usage data cleared.");
    }
  });

  // Watch for config changes
  const configWatcher = vscode.workspace.onDidChangeConfiguration((event) => {
    if (event.affectsConfiguration("claudeUsage.showInStatusBar")) {
      const show = vscode.workspace
        .getConfiguration("claudeUsage")
        .get<boolean>("showInStatusBar", true);
      if (show) {
        statusBar.show();
      } else {
        statusBar.hide();
      }
    }

    if (
      event.affectsConfiguration("claudeUsage.refreshInterval") ||
      event.affectsConfiguration("claudeUsage.autoFetch")
    ) {
      statusBar.hide();
      statusBar.show();
    }

    // Multi-window auto-switch propagation: when another window writes
    // lastSwitchedModel, apply the switch to local Claude Code terminals.
    if (event.affectsConfiguration("claudeUsage.autoSwitch.lastSwitchedModel")) {
      if (!autoSwitcher.isSwitching()) {
        const targetModel = vscode.workspace
          .getConfiguration("claudeUsage.autoSwitch")
          .get<string>("lastSwitchedModel", "");
        if (targetModel) {
          log.appendLine(`[Extension] Config change: lastSwitchedModel="${targetModel}" from another window`);
          autoSwitcher.applyRemoteSwitch(targetModel);
        }
      }
      statusBar.refresh();
      DashboardPanel.updateIfOpen(
        store.getWithFreshCountdowns(),
        store.getTimeSinceUpdate(),
        lastFetchError,
        store.getAutoSwitchState(),
      );
    }

  });

  context.subscriptions.push(
    dashboardCommand,
    refreshCommand,
    recommendCommand,
    resetCommand,
    configWatcher,
    terminalListener,
    log,
    { dispose: () => statusBar.dispose() }
  );
}

export function deactivate(): void {
  // Cleanup handled by subscriptions
}

async function autoFetchAndUpdate(
  fetcher: UsageFetcher,
  store: UsageStore,
  statusBar: StatusBarManager,
  autoSwitcher: AutoSwitcher,
  log: vscode.OutputChannel,
): Promise<void> {
  if (fetchInFlight) {
    // A fetch is already running; clear any loading states that the caller may have set
    statusBar.refresh();
    DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError, store.getAutoSwitchState());
    return;
  }
  fetchInFlight = true;
  try {
    const result = await fetcher.fetch(store.getCurrentModel());
    if (result.success) {
      consecutiveFailures = 0;
      lastFetchError = undefined;
      failureNotificationShown = false;
      statusBar.resetBackoff();

      const previousUrgency = store.getLastUrgency();
      await store.save(result.data);

      const newUrgency = getOverallUrgency(result.data);
      await store.saveLastUrgency(newUrgency);

      // Evaluate auto-switch thresholds and apply model/effort changes
      await evaluateAndNotify(result.data, store, autoSwitcher, log);

      // Only show recommendation notification when urgency escalates
      if (previousUrgency && urgencyEscalated(previousUrgency, newUrgency)) {
        const recommendation = getRecommendation(result.data);
        vscode.window
          .showWarningMessage(`Claude Usage: ${recommendation.message}`, "Show Dashboard")
          .then((action) => {
            if (action === "Show Dashboard") {
              vscode.commands.executeCommand(DASHBOARD_COMMAND);
            }
          });
      }

      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError, store.getAutoSwitchState());
    } else {
      consecutiveFailures++;
      lastFetchError = result.error;

      if (result.error.code === "rate-limited") {
        statusBar.applyBackoff();
        // Don't show popup for rate-limiting (known upstream Anthropic issue)
      } else if (consecutiveFailures >= 2 && !failureNotificationShown) {
        // Only show popup for actionable errors
        failureNotificationShown = true;
        vscode.window.showWarningMessage(
          `Auto-fetch failed: ${UsageFetcher.getErrorMessage(result.error)}`,
          "Dismiss"
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
 * Run auto-switch evaluation and show notifications. If a model switch occurred,
 * re-save the stored data with the updated current model so the dashboard reflects it.
 */
async function evaluateAndNotify(
  data: UsageData,
  store: UsageStore,
  autoSwitcher: AutoSwitcher,
  log: vscode.OutputChannel,
): Promise<void> {
  let switchActions: AutoSwitchAction[] = [];
  try {
    switchActions = await autoSwitcher.evaluate(data);
    for (const action of switchActions) {
      showAutoSwitchNotification(action, autoSwitcher);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    log.appendLine(`[Extension] Auto-switch evaluation failed: ${msg}`);
    vscode.window.showWarningMessage(
      `Auto-switch evaluation failed: ${msg}. Check Output > "Claude Usage Monitor" for details.`,
    );
    return;
  }

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

function showAutoSwitchNotification(action: AutoSwitchAction, autoSwitcher: AutoSwitcher): void {
  const pct = action.triggerPercent;
  const termCount = action.terminalCount ?? 0;

  switch (action.kind) {
    case "model-switched": {
      // settings.json is always updated; terminal count indicates live sessions reached
      const applied = termCount > 0
        ? `Applied to ${termCount} active session${termCount > 1 ? "s" : ""}. `
        : "";
      const manual = `New conversations will use ${action.to} automatically. For your current conversation, run /model ${action.to} or use the "/" button > Switch model.`;
      vscode.window
        .showInformationMessage(
          `Auto-switch: Model changed from ${action.from} to ${action.to} (usage at ${pct}%). ${applied}${manual}`,
          "Undo",
        )
        .then((choice) => {
          if (choice === "Undo") {
            autoSwitcher.undoModelSwitch();
          }
        });
      break;
    }

    case "model-restored": {
      const applied = termCount > 0
        ? `Applied to ${termCount} active session${termCount > 1 ? "s" : ""}. `
        : "";
      const manual = `New conversations will use ${action.to} automatically. For your current conversation, run /model ${action.to} or use the "/" button > Switch model.`;
      vscode.window.showInformationMessage(
        `Auto-switch: Usage dropped to ${pct}%. Model restored to ${action.to}. ${applied}${manual}`,
      );
      break;
    }

    case "usage-advisory":
      if (action.message) {
        vscode.window.showInformationMessage(action.message, "Dismiss");
      }
      break;
  }
}
