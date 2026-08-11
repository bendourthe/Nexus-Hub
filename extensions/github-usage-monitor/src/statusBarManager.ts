import * as vscode from "vscode";
import type { ProviderError, UsageMetric, UsageSnapshot, UsageState } from "./types";
import { formatResetCountdown, formatResetDateTime } from "./usageStore";

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

  public show(state: UsageState, accountLabel?: string | null): void {
    this.item.text = buildStatusText(state.data, state.state === "stale", undefined, isNotConnected(state));
    this.item.tooltip = buildHoverMarkdown(state, undefined, accountLabel);
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
/** Short name for the status bar, so the percentage says what it measures. */
/**
 * Display unit. The API's `ai-credits` is an identifier, not a word a user would
 * write, and it reads as machine output beside "minutes" and "gigabytes".
 */
export function displayUnit(unit: string): string {
  return unit === "ai-credits" ? "credits" : unit;
}

export function statusMetricName(metric: UsageMetric): string {
  return ({
    "copilot-ai-credits": "AI credits",
    "copilot-premium-requests": "premium requests",
    "actions-minutes": "actions minutes",
    "actions-storage": "actions storage"
  } as const)[metric.kind];
}

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
  // Name the metric alongside the number. Three metrics can occupy this slot, and a
  // bare "7%" does not say which one the user chose to watch.
  return `${GITHUB_ICON}${ICON_GAP}${label}${summary} (${statusMetricName(metric)})${stale ? " $(warning)" : ""}`;
}

/**
 * Who the figures belong to, in the reader's terms.
 *
 * "Owner: SupiraMedical (organization)" was the REST vocabulary leaking into the UI.
 * It reads as "the person who owns this", which is precisely the wrong idea when the
 * signed-in user and the billed organization are different identities - the normal
 * case for a work account. Both are named on their own line instead.
 */
export function identityLines(owner: UsageSnapshot["owner"], accountLabel?: string | null): string {
  const user = accountLabel === undefined || accountLabel === null || accountLabel === ""
    ? ""
    : `User: ${escapeHtml(accountLabel)}<br>`;
  const label =
    owner.scope === "user" ? "Personal account" : owner.scope === "organization" ? "Organization" : "Enterprise";
  return `${user}${label}: ${escapeHtml(owner.name)}<br>`;
}

export function buildHoverMarkdown(state: UsageState, now = Date.now(), accountLabel?: string | null): vscode.MarkdownString {
  const md = new vscode.MarkdownString("", true);
  md.supportThemeIcons = true;
  md.supportHtml = true;
  // Required for the data-URI <img> bars: an untrusted MarkdownString strips them,
  // which would leave the hover with three captions and no bars at all.
  md.isTrusted = true;
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
    metricSection("Copilot AI credits", snapshot.copilot, now, isDarkTheme()),
    metricSection("Actions minutes", snapshot.actionsMinutes, now, isDarkTheme()),
    metricSection("Actions storage", snapshot.actionsStorage, now, isDarkTheme())
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
    identityLines(snapshot.owner, accountLabel) +
    `Source: ${snapshot.source} - ${freshness}<br>` +
    `Updated: ${escapeHtml(relativeTime(snapshot.fetchedAt, now))}` +
    (state.error ? `<br><br>$(warning) ${escapeHtml(state.error.message)}` : "")
  );
  return md;
}

/**
 * Width of the hover's progress bar, in CSS pixels. Matches the sibling monitors.
 */
const HOVER_BAR_WIDTH = 280;

/** Label colors have to follow the theme; the SVG cannot inherit CSS variables. */
function isDarkTheme(): boolean {
  const kind = vscode.window.activeColorTheme.kind;
  return kind === vscode.ColorThemeKind.Dark || kind === vscode.ColorThemeKind.HighContrast;
}

/**
 * One SVG progress bar for the hover, as a data URI.
 *
 * Ported from the Claude and Codex monitors. v3.16.3 drew a run of Unicode full
 * blocks instead, which cannot render a rounded track, cannot show a partial fill,
 * and quantized the value to the nearest 10% - so it looked nothing like the
 * siblings sitting next to it in the same status bar.
 */
function hoverBar(label: string, percent: number, dark: boolean, noAllowance = false): string {
  const width = HOVER_BAR_WIDTH;
  const barHeight = 6;
  const fontSize = 12;
  const textY = fontSize;
  const barY = textY + 6;
  const height = barY + barHeight;
  const labelColor = dark ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.92)";
  const dimColor = dark ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.55)";
  const fill = Math.round((width * Math.min(100, Math.max(0, percent))) / 100);
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">` +
    `<text x="0" y="${textY}" fill="${labelColor}" font-weight="bold" font-family="system-ui,sans-serif" font-size="${fontSize}">${label}</text>` +
    `<text x="${width}" y="${textY}" fill="${dimColor}" font-family="system-ui,sans-serif" font-size="${fontSize}" text-anchor="end">${noAllowance ? "n/a" : `${Math.round(percent)}%`}</text>` +
    `<rect y="${barY}" width="${width}" height="${barHeight}" rx="3" fill="${noAllowance ? "rgba(128,128,128,0.18)" : "rgba(0,128,128,0.2)"}"/>` +
    `<rect y="${barY}" width="${fill}" height="${barHeight}" rx="3" fill="${noAllowance ? "rgba(128,128,128,0.45)" : GITHUB_BAR_FILL}"/>` +
    `</svg>`;
  return `<img alt="${label}" src="data:image/svg+xml,${encodeURIComponent(svg)}" width="${width}" height="${height}">`;
}

function metricSection(label: string, metric: UsageMetric | undefined, now: number, dark = true): string {
  // A snapshot cached by an older version can be missing a metric entirely. Rendering
  // it as an omission is honest; letting `undefined` reach the formatter throws and
  // takes the whole tooltip down.
  if (metric === undefined) return `<span style="font-weight:bold">${label}</span><br><em>Not reported</em><br><br>`;
  const reset =
    metric.reset === null ? "" : `<em>Resets ${escapeHtml(formatResetDateTime(metric.reset.at))}</em><br>`;

  if (metric.allowanceState === "none") {
    return `${hoverBar(label, 100, dark, true)}<br>` +
      `<em>${formatNumber(metric.used)} ${escapeHtml(displayUnit(metric.unit))} used - no allowance included with your plan</em><br>${reset}<br>`;
  }
  if (metric.percentage === null || metric.allowance === null) {
    return `<span style="font-weight:bold">${label}</span> ${formatAmount(metric)}<br><em>Allowance not established</em><br>${reset}<br>`;
  }

  const counted =
    typeof metric.drawdown === "number" && Number.isFinite(metric.drawdown)
      ? `${formatNumber(metric.drawdown)} ${escapeHtml(metric.unit)}`
      : formatAmount(metric);
  return `${hoverBar(label, Math.max(0, metric.percentage), dark)}<br>` +
    `<em>${counted} of ${formatNumber(metric.allowance)} ${escapeHtml(metric.unit)}</em><br>${reset}<br>`;
}

export function formatAmount(metric: UsageMetric): string { return `${formatNumber(metric.used)} ${escapeHtml(metric.unit)}`; }
function formatNumber(value: number): string { return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value); }
function money(value: number | null): string { return value === null ? "unknown" : `$${value.toFixed(2)}`; }
function relativeTime(timestamp: number, now: number): string { const minutes = Math.max(0, Math.floor((now - timestamp) / 60_000)); return minutes === 0 ? "just now" : `${minutes} min ago`; }
export function escapeHtml(value: string): string { return value.replace(/&/gu, "&amp;").replace(/</gu, "&lt;").replace(/>/gu, "&gt;").replace(/"/gu, "&quot;").replace(/'/gu, "&#39;"); }
