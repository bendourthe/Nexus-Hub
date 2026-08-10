import * as vscode from "vscode";
import type { ProviderError, UsageMetric, UsageSnapshot, UsageState } from "./types";
import { formatResetCountdown } from "./usageStore";

export const GITHUB_BAR_FILL = "#008080";
const GITHUB_ICON = "$(github-icon)";
const ICON_GAP = "\u2002";

export class StatusBarManager {
  private readonly item: vscode.StatusBarItem;

  public constructor(private readonly dashboardCommandId: string) {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 101);
    this.item.command = dashboardCommandId;
    this.item.name = "GitHub Usage Monitor";
  }

  public show(state: UsageState): void {
    this.item.text = buildStatusText(state.data, state.state === "stale", undefined, isNotConnected(state));
    this.item.tooltip = buildHoverMarkdown(state);
    this.item.show();
  }

  public showLoading(): void {
    this.item.text = "$(sync~spin) GitHub Usage";
    this.item.tooltip = "Refreshing authorized GitHub billing usage.";
  }

  public dispose(): void { this.item.dispose(); }
}

/** True when the state means "no credential at all", rather than a failed request. */
export function isNotConnected(state: UsageState): boolean {
  return state.data === undefined && state.error?.code === "not-connected";
}

/**
 * Which metric the status bar shows.
 *
 * `actions-minutes` is the default because it is the metric with a real published
 * entitlement for most accounts, and therefore the one most likely to produce a
 * meaningful percentage. `highest` is the pre-v3.16.3 behaviour, retained as an
 * explicit choice rather than as the only option.
 */
export type StatusBarMetric = "actions-minutes" | "actions-storage" | "copilot" | "highest";

/**
 * Picks the metric named by the setting, or null when this snapshot does not carry it.
 *
 * Every access is `?? null`-guarded rather than assumed present. A snapshot cached
 * by an older version can be missing a metric entirely, and an `undefined` reaching
 * the formatter renders as a crash or a bare "undefined" rather than the honest
 * unavailable indicator.
 */
export function selectStatusMetric(snapshot: UsageSnapshot, choice: StatusBarMetric): UsageMetric | null {
  if (choice === "highest") {
    const ranked = [snapshot.copilot, snapshot.actionsMinutes, snapshot.actionsStorage]
      .filter((metric): metric is UsageMetric & { percentage: number } => metric?.percentage != null)
      .sort((left, right) => right.percentage - left.percentage);
    return ranked[0] ?? null;
  }
  if (choice === "actions-minutes") return snapshot.actionsMinutes ?? null;
  if (choice === "actions-storage") return snapshot.actionsStorage ?? null;
  return snapshot.copilot ?? null;
}

export function buildStatusText(
  snapshot: UsageSnapshot | undefined,
  stale = false,
  compact?: boolean,
  notConnected = false,
  metricChoice?: StatusBarMetric
): string {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const isCompact = compact ?? config.get<boolean>("compactStatusBar", false);
  const choice = metricChoice ?? config.get<StatusBarMetric>("statusBarMetric", "actions-minutes");
  const label = isCompact ? "" : "GitHub Usage: ";
  // `--` reads as "a number that failed to load". An unconnected install has not
  // failed at anything, so it says what is actually true instead.
  if (notConnected) return `${GITHUB_ICON}${ICON_GAP}${label}Not connected`;
  if (snapshot === undefined) return `${GITHUB_ICON}${ICON_GAP}${label}--${stale ? " $(warning)" : ""}`;

  const metric = selectStatusMetric(snapshot, choice);
  // A selected metric that this owner does not report gets an honest indicator, NOT
  // a silent fall back to a different metric. A status bar quietly showing a number
  // other than the one the user chose is a correctness bug, not graceful degradation.
  if (metric === null) {
    const summary = choice === "highest" && snapshot.copilot !== undefined ? formatAmount(snapshot.copilot) : "n/a";
    return `${GITHUB_ICON}${ICON_GAP}${label}${summary}${stale ? " $(warning)" : ""}`;
  }
  // A percentage when the allowance is known; the absolute amount when it is not.
  // Never a fabricated percentage - that is the data contract's rule, and it is why
  // the Copilot option usually shows an amount rather than a share.
  const summary = metric.percentage === null ? formatAmount(metric) : `${Math.round(metric.percentage)}%`;
  return `${GITHUB_ICON}${ICON_GAP}${label}${summary}${stale ? " $(warning)" : ""}`;
}

export function buildHoverMarkdown(state: UsageState, now = Date.now()): vscode.MarkdownString {
  const md = new vscode.MarkdownString("", true);
  md.supportThemeIcons = true;
  md.supportHtml = true;
  if (state.data === undefined) {
    if (isNotConnected(state)) {
      md.appendMarkdown(
        "**GitHub Usage Monitor**<br><br>Not connected to GitHub, so there is nothing to report yet." +
        "<br><br>This monitor reads billing usage for one owner you configure. It never reads your code." +
        "<br><br>Click to open the panel and connect."
      );
      return md;
    }
    md.appendMarkdown(`**GitHub Usage Monitor**<br><br>${escapeHtml(state.error?.message ?? "No billing data yet.")}<br><br>Click to open the dashboard.`);
    return md;
  }
  const snapshot = state.data;
  const sections = [
    metricSection("Copilot", snapshot.copilot, now),
    metricSection("Actions minutes", snapshot.actionsMinutes, now),
    metricSection("Actions storage", snapshot.actionsStorage, now)
  ].join("");
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const choice = config.get<StatusBarMetric>("statusBarMetric", "actions-minutes");
  const selected = selectStatusMetric(snapshot, choice);
  // Explains the "n/a" the status bar shows, rather than leaving the user to guess
  // why their chosen metric is blank.
  const unavailable = selected === null && choice !== "highest"
    ? `$(warning) The status bar is set to show ${escapeHtml(choice)}, which this owner does not report.<br><br>`
    : "";
  const freshness = snapshot.stale || state.state === "stale" ? "Stale cache" : "Fresh";
  md.appendMarkdown(
    `**GitHub Usage Monitor**<br><br>${unavailable}${sections}` +
    `Owner: ${escapeHtml(snapshot.owner.name)} (${snapshot.owner.scope})<br>` +
    `Source: ${snapshot.source} - ${freshness}<br>` +
    `Updated: ${escapeHtml(relativeTime(snapshot.fetchedAt, now))}` +
    (state.error ? `<br><br>$(warning) ${escapeHtml(state.error.message)}` : "")
  );
  return md;
}

function metricSection(label: string, metric: UsageMetric | undefined, now: number): string {
  // A snapshot cached by an older version can be missing a metric entirely. Rendering
  // it as an omission is honest; letting `undefined` reach the formatter throws and
  // takes the whole tooltip down.
  if (metric === undefined) return `**${label}** - not reported<br><br>`;
  const amount = formatAmount(metric);
  const costs = formatCosts(metric);
  const reset = metric.reset === null ? "Reset: not reported" : `Reset: ${formatResetCountdown(metric.reset.at, now)} (${escapeHtml(metric.reset.label)})`;
  if (metric.percentage === null || metric.allowance === null) {
    // The hover mirrors the panel's three states rather than collapsing them into
    // one "unknown". A Copilot metric with no plan allowance is a different fact
    // from an Actions metric whose drawdown could not be reconstructed, and a user
    // reading the tooltip deserves to know which they are looking at.
    const reason =
      metric.allowanceState === "none"
        ? "No allowance included with your plan"
        : "Allowance not established";
    return `**${label}** - ${amount}<br>${reason}<br>${costs}${reset}<br><br>`;
  }
  const percent = Math.max(0, metric.percentage);
  const width = Math.min(100, Math.round(percent));
  const bar = `<span style="color:${GITHUB_BAR_FILL}">${"&#9608;".repeat(Math.max(1, Math.ceil(width / 10)))}</span>`;
  return `**${label}** - ${amount} of ${formatNumber(metric.allowance)} ${escapeHtml(metric.unit)} (${Math.round(percent)}%)<br>${bar}<br>Allowance: ${metric.allowanceSource}<br>${costs}${reset}<br><br>`;
}

function formatCosts(metric: UsageMetric): string {
  if (metric.grossAmount === null && metric.netAmount === null) return "Cost: not reported<br>";
  return `Cost: gross ${money(metric.grossAmount)}, discount ${money(metric.discountAmount)}, net ${money(metric.netAmount)}<br>`;
}

export function formatAmount(metric: UsageMetric): string { return `${formatNumber(metric.used)} ${escapeHtml(metric.unit)}`; }
function formatNumber(value: number): string { return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value); }
function money(value: number | null): string { return value === null ? "unknown" : `$${value.toFixed(2)}`; }
function relativeTime(timestamp: number, now: number): string { const minutes = Math.max(0, Math.floor((now - timestamp) / 60_000)); return minutes === 0 ? "just now" : `${minutes} min ago`; }
export function escapeHtml(value: string): string { return value.replace(/&/gu, "&amp;").replace(/</gu, "&lt;").replace(/>/gu, "&gt;").replace(/"/gu, "&quot;").replace(/'/gu, "&#39;"); }
