import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import { StatusBarManager } from "./statusBarManager";
import { UsageFetcher, FetchError } from "./usageFetcher";
import { DashboardPanel } from "./dashboardPanel";
import { SettingsPanel } from "./settingsPanel";
import { getRecommendation, getOverallUrgency, getActiveUrgency } from "./recommendations";
import { UrgencyLevel, UsageData, formatModelName, getThresholdConfig, getThresholdMetric, getNotificationTimeoutMs, syncColorsToWorkbench, getColorConfig } from "./types";

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

const RECOMMEND_COMMAND = "claude-usage.recommend";
const RESET_COMMAND = "claude-usage.reset";
const DASHBOARD_COMMAND = "claude-usage.dashboard";
const REFRESH_COMMAND = "claude-usage.refresh";
const SETTINGS_COMMAND = "claude-usage.settings";

let consecutiveFailures = 0;
let lastFetchError: FetchError | undefined;
let failureNotificationShown = false;
let fetchInFlight = false;

// In-memory threshold tracker — intentionally not persisted so it resets on every
// VS Code startup. This ensures the user sees a notification on startup when usage
// is already above a threshold, while still avoiding duplicate popups within a session.
const notifiedThresholds = new Set<number>();

export function activate(context: vscode.ExtensionContext): void {
  const store = new UsageStore(context.globalState);
  const fetcher = new UsageFetcher();
  const statusBar = new StatusBarManager(store, DASHBOARD_COMMAND, SETTINGS_COMMAND);

  const config = vscode.workspace.getConfiguration("claudeUsage");
  if (config.get<boolean>("showInStatusBar", true)) {
    statusBar.show();
  }

  // Wire up auto-refresh: when the timer fires, trigger a fetch
  statusBar.setAutoRefreshCallback(() => autoFetchAndUpdate(fetcher, store, statusBar));

  // Wire up reset-expiry detection: when a cached reset timestamp passes, refetch
  statusBar.setResetExpiredCallback(() => autoFetchAndUpdate(fetcher, store, statusBar));

  // Apply user color settings to workbench.colorCustomizations on startup
  syncColorsToWorkbench(getColorConfig());

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
        statusBar.showLoading();
        await autoFetchAndUpdate(fetcher, store, statusBar);
      },
      onOpenUsagePage: () =>
        vscode.env.openExternal(vscode.Uri.parse("https://claude.ai/settings/usage")),
      onOpenSettings: () => vscode.commands.executeCommand(SETTINGS_COMMAND),
    }, context.extensionUri);
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
      await evaluateAndNotify(result.data);
      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
      showAutoDismissNotification("Claude Usage: usage data refreshed.", "info");
    } else {
      statusBar.refresh();
      if (result.error.code !== "rate-limited") {
        showAutoDismissNotification(
          `Claude Usage: fetch failed - ${UsageFetcher.getErrorMessage(result.error)}`,
          "warning"
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

  // Command: Open settings panel
  const settingsCommand = vscode.commands.registerCommand(SETTINGS_COMMAND, () => {
    SettingsPanel.show(context.extensionUri);
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

    // When the model changes in Claude Code, refresh status bar and dashboard immediately.
    if (event.affectsConfiguration("claudeCode.selectedModel")) {
      statusBar.refresh();
      DashboardPanel.updateIfOpen(
        store.getWithFreshCountdowns(),
        store.getTimeSinceUpdate(),
        lastFetchError,
      );
    }

    // When threshold, color, or metric settings change, re-evaluate the status bar immediately.
    if (
      event.affectsConfiguration("claudeUsage.thresholds") ||
      event.affectsConfiguration("claudeUsage.colors") ||
      event.affectsConfiguration("claudeUsage.thresholdMetric")
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
    const result = await fetcher.fetch(store.getCurrentModel());
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
        showAutoDismissNotification(`Claude Usage: ${recommendation.message}`, "warning");
      }

      statusBar.refresh();
      DashboardPanel.updateIfOpen(store.getWithFreshCountdowns(), store.getTimeSinceUpdate(), lastFetchError);
    } else {
      consecutiveFailures++;
      lastFetchError = result.error;

      if (result.error.code === "rate-limited") {
        statusBar.applyBackoff();
        // Don't show popup for rate-limiting (known upstream Anthropic issue)
      } else if (consecutiveFailures >= 2 && !failureNotificationShown) {
        // Only show popup for actionable errors
        failureNotificationShown = true;
        showAutoDismissNotification(
          `Claude Usage: auto-fetch failed - ${UsageFetcher.getErrorMessage(result.error)}`,
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
 * notification the first time each threshold is crossed in a usage cycle.
 * Only the highest unnotified threshold fires a notification per evaluation.
 */
/**
 * Evaluate usage against suggestion thresholds and show a one-time VS Code
 * notification the first time each threshold is crossed in a session.
 * Uses an in-memory set so the state resets on every VS Code startup — this
 * guarantees the user sees a notification on launch when usage is already high.
 * Only the highest unnotified threshold fires a notification per evaluation.
 * Returns true if a notification was shown, false otherwise.
 */
async function evaluateAndNotify(data: UsageData): Promise<boolean> {
  const t = getThresholdConfig();
  const metric = getThresholdMetric();

  let triggerPercent: number;
  let resetIn: string;
  let triggerLabel: string;
  switch (metric) {
    case "highest": {
      const candidates = [
        { percent: data.session.percent,          resetsIn: data.session.resetsIn,          label: "Current Session" },
        { percent: data.weeklyAllModels.percent,  resetsIn: data.weeklyAllModels.resetsIn,  label: "Weekly (All Models)" },
        { percent: data.weeklySonnet.percent,     resetsIn: data.weeklySonnet.resetsIn,     label: "Weekly (Sonnet)" },
      ];
      const top = candidates.reduce((a, b) => a.percent >= b.percent ? a : b);
      triggerPercent = top.percent;
      resetIn        = top.resetsIn;
      triggerLabel   = top.label;
      break;
    }
    case "weekly":
      triggerPercent = data.weeklyAllModels.percent;
      resetIn = data.weeklyAllModels.resetsIn;
      triggerLabel = "Weekly (All Models)";
      break;
    case "sonnet":
      triggerPercent = data.weeklySonnet.percent;
      resetIn = data.weeklySonnet.resetsIn;
      triggerLabel = "Weekly (Sonnet)";
      break;
    default:
      triggerPercent = data.session.percent;
      resetIn = data.session.resetsIn;
      triggerLabel = "Current Session";
      break;
  }

  // Reset within-session tracking when usage drops below the moderate threshold.
  if (triggerPercent < t.moderate) {
    notifiedThresholds.clear();
    return false;
  }

  const isOpus = /opus|fable|default/i.test(data.currentModel);
  // Long-form weekly resets start with a weekday name ("Tuesday July 7th at ...");
  // "Resets in" only reads correctly for duration-style values ("2h 20m").
  const resetSuffix = /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)/.test(resetIn)
    ? ` Resets ${resetIn}.`
    : ` Resets in ${resetIn}.`;

  // Determine the single applicable threshold bucket and its message.
  // Only one notification fires — the one that matches the current usage level.
  let bucket: number;
  let message: string;

  const pct = Math.round(triggerPercent);
  if (triggerPercent >= t.critical) {
    bucket = t.critical;
    message = `${triggerLabel} usage at ${pct}% \u2192 Switch to Haiku and set Effort to Low to avoid hitting your limit.${resetSuffix}`;
  } else if (triggerPercent >= t.high) {
    bucket = t.high;
    message = isOpus
      ? `${triggerLabel} usage at ${pct}% \u2192 Switch to Sonnet and reduce Effort to High or Medium.${resetSuffix}`
      : `${triggerLabel} usage at ${pct}% \u2192 Reduce Effort to High or Medium.${resetSuffix}`;
  } else {
    // Moderate band: nudge Effort down regardless of model. No model swap yet.
    bucket = t.moderate;
    message = `${triggerLabel} usage at ${pct}% \u2192 Reduce Effort to High or Medium to extend your remaining usage.${resetSuffix}`;
  }

  // Already notified for this bucket in the current session — nothing to do.
  if (notifiedThresholds.has(bucket)) {
    return false;
  }

  // Mark this bucket and every lower one as notified so they never fire
  // individually if usage continues to climb during the same session.
  [t.critical, t.high, t.moderate].filter(thresh => triggerPercent >= thresh).forEach(thresh => notifiedThresholds.add(thresh));

  showAutoDismissNotification(`Claude Usage: ${message}`, "warning");
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
