import * as vscode from "vscode";
import {
  escapeHtml,
  formatMoney,
  formatPercent,
  formatQuantity
} from "./formatters";
import {
  METER_FILL_COLOR,
  type IncludedUsageMeter,
  type UsageSnapshot,
  type UsageState
} from "./types";

const CURSOR_ICON = "$(cursor-icon)";
const ICON_GAP = "\u2002";

export class StatusBarManager {
  private readonly item: vscode.StatusBarItem;

  public constructor(private readonly dashboardCommandId: string) {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      102
    );
    this.item.command = dashboardCommandId;
    this.item.name = "Cursor Usage Monitor";
  }

  public show(state: UsageState): void {
    this.item.text = buildStatusText(state);
    this.item.tooltip = buildHoverMarkdown(state);
    this.item.show();
  }

  public showLoading(): void {
    this.item.text = "$(sync~spin) Cursor Usage";
    this.item.tooltip = "Refreshing Cursor usage.";
    this.item.show();
  }

  public hide(): void {
    this.item.hide();
  }

  public dispose(): void {
    this.item.dispose();
  }
}

export function buildStatusText(
  state: UsageState,
  compact?: boolean
): string {
  const compactMode =
    compact ??
    vscode.workspace
      .getConfiguration("cursorUsage")
      .get<boolean>("compactStatusBar", false);
  const label = compactMode ? "" : "Cursor Usage: ";
  if (state.state === "empty") {
    return `${CURSOR_ICON}${ICON_GAP}${label}--`;
  }

  const cursor = statusMeter(
    state.data.cursorModels,
    compactMode ? "C" : "Cursor"
  );
  const other = statusMeter(
    state.data.otherModels,
    compactMode ? "O" : "Other"
  );
  const stale = state.state === "stale" ? " $(warning)" : "";
  return `${CURSOR_ICON}${ICON_GAP}${label}${cursor} \u00b7 ${other}${stale}`;
}

export function buildHoverMarkdown(
  state: UsageState,
  now = Date.now()
): vscode.MarkdownString {
  const markdown = new vscode.MarkdownString("", true);
  markdown.supportThemeIcons = true;
  markdown.supportHtml = true;

  if (state.state === "empty") {
    // The hover is the only guidance a user gets without clicking, so it leads with
    // an invitation rather than a provider error code. "authorization-required"
    // reads as a fault; "two steps" reads as something to do. The raw message stays
    // available, below, for anyone diagnosing rather than starting out.
    markdown.appendMarkdown(
      `**Cursor Usage**<br><br>Not connected yet - click to set this up in two steps.<br><br>Cursor offers no personal usage API, so figures are copied from your usage page.<br><br>${escapeHtml(state.error.message)}`
    );
    return markdown;
  }

  const snapshot = state.data;
  const freshness =
    state.state === "stale"
      ? `$(warning) Stale: ${escapeHtml(staleReasonLabel(snapshot.staleReason))}`
      : "Fresh";
  markdown.appendMarkdown(
    `**Cursor Usage**<br><br>` +
      hoverMeter("Cursor Models", snapshot.cursorModels) +
      hoverMeter("Other Models", snapshot.otherModels) +
      `**On-demand** - ${escapeHtml(formatOnDemand(snapshot))}<br>` +
      `**Shared team context** - ${escapeHtml(formatTeamContext(snapshot))}<br><br>` +
      `Reset: ${escapeHtml(formatReset(snapshot, now))}<br>` +
      `Source: ${escapeHtml(sourceLabel(snapshot))}<br>` +
      `Freshness: ${freshness}<br>` +
      `Updated: ${escapeHtml(relativeTime(snapshot.fetchedAt, now))}` +
      (state.state === "stale"
        ? `<br><br>$(warning) ${escapeHtml(state.error.message)}`
        : "")
  );
  return markdown;
}

function statusMeter(meter: IncludedUsageMeter, label: string): string {
  if (meter.percentUsed !== null) {
    // Shares the dashboard's formatter so one pool cannot read 1.7% in the panel
    // and 2% in the status bar.
    return `${label} ${formatPercent(meter.percentUsed)}`;
  }
  return `${label} ${formatQuantity(meter.used)}`;
}

function hoverMeter(label: string, meter: IncludedUsageMeter): string {
  const used = formatQuantity(meter.used);
  if (meter.percentUsed === null) {
    return `**${label}** - ${escapeHtml(used)}<br>Allowance unavailable; absolute usage only.<br><br>`;
  }
  const percent = Math.max(0, meter.percentUsed);
  const blocks = Math.max(1, Math.ceil(Math.min(100, percent) / 10));
  const bar = `<span style="color:${METER_FILL_COLOR}">${"&#9608;".repeat(blocks)}</span>`;
  const absolute =
    meter.used === null
      ? ""
      : `<br>Absolute usage: ${escapeHtml(used)}`;
  const allowance =
    meter.limit === null
      ? "<br>Allowance: Not reported"
      : `<br>Allowance: ${escapeHtml(formatQuantity(meter.limit))}`;
  return (
    `**${label}** - ${formatPercent(meter.percentUsed)}${absolute}${allowance}` +
    `<br>${bar}<br><br>`
  );
}

function formatOnDemand(snapshot: UsageSnapshot): string {
  if (snapshot.onDemand.enabled === true) {
    return `Enabled; Personal spend ${formatMoney(snapshot.onDemand.personalSpend)}`;
  }
  if (snapshot.onDemand.enabled === false) {
    return "Disabled";
  }
  return "State unknown";
}

function formatTeamContext(snapshot: UsageSnapshot): string {
  const limit = snapshot.teamContext.sharedSpendLimit;
  if (limit === null) {
    return "Not reported";
  }
  let dynamic = "";
  if (snapshot.teamContext.dynamicSpendLimit === true) {
    dynamic = "; dynamic shared limit";
  } else if (snapshot.teamContext.dynamicSpendLimit === false) {
    dynamic = "; fixed shared limit";
  }
  return `${formatMoney(limit)} shared pool${dynamic}; not a personal allowance`;
}

function formatReset(snapshot: UsageSnapshot, now: number): string {
  if (snapshot.period.resetsAt === null) {
    return "Not reported";
  }
  const reset = Date.parse(snapshot.period.resetsAt);
  if (!Number.isFinite(reset)) {
    return "Not reported";
  }
  const minutes = Math.max(0, Math.ceil((reset - now) / 60_000));
  if (minutes < 60) {
    return `in ${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  return hours < 48
    ? `in ${hours}h ${minutes % 60}m`
    : new Date(reset).toLocaleString("en-US");
}

function sourceLabel(snapshot: UsageSnapshot): string {
  return snapshot.source === "cache"
    ? `cache (${snapshot.cachedFrom})`
    : snapshot.source;
}

function staleReasonLabel(reason: UsageSnapshot["staleReason"]): string {
  return reason?.replace(/-/gu, " ") ?? "unknown reason";
}

function relativeTime(timestamp: string, now: number): string {
  const parsed = Date.parse(timestamp);
  if (!Number.isFinite(parsed)) {
    return "unknown";
  }
  const minutes = Math.max(0, Math.floor((now - parsed) / 60_000));
  return minutes === 0 ? "just now" : `${minutes} min ago`;
}

