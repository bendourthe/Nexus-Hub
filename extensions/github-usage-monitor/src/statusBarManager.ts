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

export function buildStatusText(
  snapshot: UsageSnapshot | undefined,
  stale = false,
  compact?: boolean,
  notConnected = false
): string {
  const isCompact = compact ?? vscode.workspace.getConfiguration("githubUsageMonitor").get<boolean>("compactStatusBar", false);
  const label = isCompact ? "" : "GitHub Usage: ";
  // `--` reads as "a number that failed to load". An unconnected install has not
  // failed at anything, so it says what is actually true instead.
  if (notConnected) return `${GITHUB_ICON}${ICON_GAP}${isCompact ? "" : "GitHub Usage: "}Not connected`;
  if (snapshot === undefined) return `${GITHUB_ICON}${ICON_GAP}${label}--${stale ? " $(warning)" : ""}`;
  const metrics = [snapshot.copilot, snapshot.actionsMinutes, snapshot.actionsStorage]
    .filter((metric): metric is UsageMetric & { percentage: number } => metric.percentage !== null)
    .sort((left, right) => right.percentage - left.percentage);
  const highest = metrics[0];
  const summary = highest === undefined ? formatAmount(snapshot.copilot) : `${Math.round(highest.percentage)}%`;
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
  const freshness = snapshot.stale || state.state === "stale" ? "Stale cache" : "Fresh";
  md.appendMarkdown(
    `**GitHub Usage Monitor**<br><br>${sections}` +
    `Owner: ${escapeHtml(snapshot.owner.name)} (${snapshot.owner.scope})<br>` +
    `Source: ${snapshot.source} - ${freshness}<br>` +
    `Updated: ${escapeHtml(relativeTime(snapshot.fetchedAt, now))}` +
    (state.error ? `<br><br>$(warning) ${escapeHtml(state.error.message)}` : "")
  );
  return md;
}

function metricSection(label: string, metric: UsageMetric, now: number): string {
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
