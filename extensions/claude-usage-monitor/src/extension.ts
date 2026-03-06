import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import { StatusBarManager } from "./statusBarManager";
import { UsageFetcher, FetchError } from "./usageFetcher";
import { DashboardPanel } from "./dashboardPanel";
import { collectUsageData, collectResetTimers } from "./inputCollector";
import { getRecommendation, getOverallUrgency } from "./recommendations";
import { MODEL_DISPLAY_NAMES, UrgencyLevel } from "./types";

const UPDATE_COMMAND = "claude-usage.update";
const RECOMMEND_COMMAND = "claude-usage.recommend";
const RESET_COMMAND = "claude-usage.reset";
const DASHBOARD_COMMAND = "claude-usage.dashboard";
const REFRESH_COMMAND = "claude-usage.refresh";

let consecutiveFailures = 0;
let lastFetchError: FetchError | undefined;
let failureNotificationShown = false;
let fetchInFlight = false;

export function activate(context: vscode.ExtensionContext): void {
  const store = new UsageStore(context.globalState);
  const fetcher = new UsageFetcher();
  const statusBar = new StatusBarManager(store, DASHBOARD_COMMAND);

  const config = vscode.workspace.getConfiguration("claudeUsage");
  if (config.get<boolean>("showInStatusBar", true)) {
    statusBar.show();
  }

  // Wire up auto-refresh: when the timer fires, trigger a fetch
  statusBar.setAutoRefreshCallback(() => autoFetchAndUpdate(fetcher, store, statusBar));

  // Wire up reset-expiry detection: when a cached reset timestamp passes, refetch
  statusBar.setResetExpiredCallback(() => autoFetchAndUpdate(fetcher, store, statusBar));

  // Auto-fetch on activation (silent)
  if (config.get<boolean>("autoFetch", true)) {
    autoFetchAndUpdate(fetcher, store, statusBar);
  }

  // Command: Show dashboard panel
  const dashboardCommand = vscode.commands.registerCommand(DASHBOARD_COMMAND, () => {
    const data = store.getWithFreshCountdowns();
    const timeSince = store.getTimeSinceUpdate();

    DashboardPanel.show(data, timeSince, lastFetchError, {
      onRefresh: async () => {
        await autoFetchAndUpdate(fetcher, store, statusBar);
        const updatedData = store.getWithFreshCountdowns();
        const updatedTime = store.getTimeSinceUpdate();
        DashboardPanel.show(updatedData, updatedTime, lastFetchError, {
          onRefresh: () => vscode.commands.executeCommand(REFRESH_COMMAND),
          onManualInput: () => vscode.commands.executeCommand(UPDATE_COMMAND),
          onOpenUsagePage: () =>
            vscode.env.openExternal(vscode.Uri.parse("https://claude.ai/settings/usage")),
        }, context.extensionUri);
      },
      onManualInput: () => vscode.commands.executeCommand(UPDATE_COMMAND),
      onOpenUsagePage: () =>
        vscode.env.openExternal(vscode.Uri.parse("https://claude.ai/settings/usage")),
    }, context.extensionUri);
  });

  // Command: Refresh (auto-fetch with manual fallback)
  const refreshCommand = vscode.commands.registerCommand(REFRESH_COMMAND, async () => {
    const result = await fetcher.fetch(store.getCurrentModel());
    if (result.success) {
      consecutiveFailures = 0;
      lastFetchError = undefined;
      failureNotificationShown = false;
      statusBar.resetBackoff();
      await store.save(result.data);
      statusBar.refresh();
      vscode.window.showInformationMessage("Claude usage data refreshed.");
    } else {
      if (result.error.code === "rate-limited") {
        // Don't alarm the user for rate-limiting (known upstream issue)
        vscode.window.showInformationMessage(
          "Usage API temporarily unavailable. Showing cached data."
        );
      } else {
        const action = await vscode.window.showWarningMessage(
          `Fetch failed: ${UsageFetcher.getErrorMessage(result.error)}`,
          "Enter Manually",
          "Dismiss"
        );
        if (action === "Enter Manually") {
          vscode.commands.executeCommand(UPDATE_COMMAND);
        }
      }
    }
  });

  // Command: Update usage data (manual input)
  const updateCommand = vscode.commands.registerCommand(UPDATE_COMMAND, async () => {
    const currentModel = store.getCurrentModel();
    const data = await collectUsageData(currentModel);

    if (!data) {
      return;
    }

    const withTimers = await vscode.window.showQuickPick(
      [
        { label: "Yes", description: "Enter reset timers for more accurate recommendations" },
        { label: "Skip", description: "Use default reset estimates" },
      ],
      { title: "Add reset timers?" }
    );

    let finalData = data;
    if (withTimers?.label === "Yes") {
      const updated = await collectResetTimers(data);
      if (updated) {
        finalData = updated;
      }
    }

    await store.save(finalData);
    statusBar.refresh();

    const recommendation = getRecommendation(finalData);
    const urgency = getOverallUrgency(finalData);

    if (urgency === "critical" || urgency === "high") {
      vscode.window
        .showWarningMessage(`Claude Usage: ${recommendation.message}`, "Show Tips")
        .then((action) => {
          if (action === "Show Tips") {
            showTipsPanel(recommendation.tips);
          }
        });
    } else {
      vscode.window.showInformationMessage(`Claude Usage: ${recommendation.message}`);
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
        label: `$(arrow-right) Suggested: ${MODEL_DISPLAY_NAMES[recommendation.suggestedModel]}`,
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
  });

  context.subscriptions.push(
    dashboardCommand,
    refreshCommand,
    updateCommand,
    recommendCommand,
    resetCommand,
    configWatcher,
    { dispose: () => statusBar.dispose() }
  );
}

export function deactivate(): void {
  // Cleanup handled by subscriptions
}

async function autoFetchAndUpdate(
  fetcher: UsageFetcher,
  store: UsageStore,
  statusBar: StatusBarManager
): Promise<void> {
  if (fetchInFlight) {
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
    } else {
      consecutiveFailures++;
      lastFetchError = result.error;

      if (result.error.code === "rate-limited") {
        statusBar.applyBackoff();
        // Don't show popup for rate-limiting (known upstream Anthropic issue)
      } else if (consecutiveFailures >= 2 && !failureNotificationShown) {
        // Only show popup for actionable errors (not rate-limiting)
        failureNotificationShown = true;
        const action = await vscode.window.showWarningMessage(
          `Auto-fetch failed: ${UsageFetcher.getErrorMessage(result.error)}`,
          "Enter Manually",
          "Dismiss"
        );
        if (action === "Enter Manually") {
          vscode.commands.executeCommand("claude-usage.update");
        }
      }

      statusBar.refresh();
    }
  } finally {
    fetchInFlight = false;
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

function showTipsPanel(tips: string[]): void {
  const panel = vscode.window.createWebviewPanel(
    "claudeUsageTips",
    "Claude Usage Tips",
    vscode.ViewColumn.Beside,
    {}
  );

  const tipsHtml = tips
    .map((tip) => `<li style="margin-bottom: 8px;">${escapeHtml(tip)}</li>`)
    .join("\n");

  panel.webview.html = `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: var(--vscode-font-family); padding: 16px; color: var(--vscode-foreground); }
    h2 { color: var(--vscode-editor-foreground); }
    ul { padding-left: 20px; }
    li { line-height: 1.6; }
  </style>
</head>
<body>
  <h2>Usage Optimization Tips</h2>
  <ul>${tipsHtml}</ul>
</body>
</html>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
