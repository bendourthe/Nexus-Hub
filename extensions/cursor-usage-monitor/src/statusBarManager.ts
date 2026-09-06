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
  const showLabel =
    compactMode
      ? false
      : vscode.workspace
          .getConfiguration("cursorUsage")
          .get<boolean>("showStatusBarLabel", true);
  const label = showLabel ? "Cursor Usage: " : "";
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
      `<span style="opacity:0.6">Cursor Usage</span><br><br><strong>Not connected yet</strong><br><em>Click to allow live usage tracking - it takes one prompt.</em><br><br>${escapeHtml(state.error.message)}`
    );
    return markdown;
  }

  const snapshot = state.data;
  const freshness =
    state.state === "stale"
      ? `$(warning) Stale: ${escapeHtml(staleReasonLabel(snapshot.staleReason))}`
      : "Fresh";
  const bars =
    hoverBar("Cursor Models", snapshot.cursorModels, resetLine(snapshot, now)) +
    hoverBar("Other Models", snapshot.otherModels, resetLine(snapshot, now)) +
    onDemandBar(snapshot, now);

  markdown.appendMarkdown(
    `<span style="opacity:0.6">Cursor Usage</span><br><br>` +
      (state.state === "stale"
        ? `<span style="color:#cca700">&#9888; ${escapeHtml(state.error.message)}</span><br><br>`
        : "") +
      bars +
      `<span style="opacity:0.6">Source: ${escapeHtml(sourceLabel(snapshot))} &middot; ${freshness} &middot; updated ${escapeHtml(relativeTime(snapshot.fetchedAt, now))}</span>`
  );
  return markdown;
}

/**
 * Bar geometry shared with the sibling Claude and Codex monitors.
 *
 * The bars are inline SVG data-URIs rather than repeated block characters. Block
 * characters quantize to whole glyphs, so a 1.7% pool and a 9% pool render
 * identically, and they cannot be given a rounded cap. An SVG gives exact width and
 * a pill shape (rx = half the height) at any percentage.
 */
const HOVER_BAR_WIDTH = 360;
const HOVER_BAR_HEIGHT = 6;
const HOVER_FONT_SIZE = 12;

function hoverBarImage(label: string, right: string, percent: number): string {
  const textY = HOVER_FONT_SIZE;
  const barY = textY + 6;
  const svgHeight = barY + HOVER_BAR_HEIGHT;
  const clamped = Math.min(100, Math.max(0, percent));
  const fillWidth = Math.round((HOVER_BAR_WIDTH * clamped) / 100);
  // Defensive read: `activeColorTheme` is absent on some hosts and in headless
  // runs, and an unguarded `.kind` throws from inside a tooltip builder - which
  // surfaces as a status bar that silently never updates. Dark is the safer default
  // because its text colors stay legible on a light background, while the reverse
  // does not.
  const themeKind = vscode.window.activeColorTheme?.kind;
  const isDark =
    themeKind === undefined ||
    themeKind === vscode.ColorThemeKind.Dark ||
    themeKind === vscode.ColorThemeKind.HighContrast;
  const labelColor = isDark ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.92)";
  const dimColor = isDark ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.55)";
  const radius = HOVER_BAR_HEIGHT / 2;
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${HOVER_BAR_WIDTH}" height="${svgHeight}">` +
    `<text x="0" y="${textY}" fill="${labelColor}" font-weight="bold" font-family="system-ui,sans-serif" font-size="${HOVER_FONT_SIZE}">${escapeHtml(label)}</text>` +
    `<text x="${HOVER_BAR_WIDTH}" y="${textY}" fill="${dimColor}" font-family="system-ui,sans-serif" font-size="${HOVER_FONT_SIZE}" text-anchor="end">${escapeHtml(right)}</text>` +
    `<rect y="${barY}" width="${HOVER_BAR_WIDTH}" height="${HOVER_BAR_HEIGHT}" rx="${radius}" fill="${METER_FILL_COLOR}33"/>` +
    `<rect y="${barY}" width="${fillWidth}" height="${HOVER_BAR_HEIGHT}" rx="${radius}" fill="${METER_FILL_COLOR}"/>` +
    `</svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function hoverBarBlock(label: string, right: string, percent: number, note: string): string {
  const svgHeight = HOVER_FONT_SIZE + 6 + HOVER_BAR_HEIGHT;
  return (
    `<img alt="${escapeHtml(`${label} ${right}`)}" src="${hoverBarImage(label, right, percent)}" width="${HOVER_BAR_WIDTH}" height="${svgHeight}"><br>` +
    `<em>${note}</em><br><br>`
  );
}

/** One included-usage pool. */
function hoverBar(
  label: string,
  meter: IncludedUsageMeter,
  reset: string
): string {
  const percentUsed = meter.percentUsed;
  const detail = [
    meter.used === null ? null : `${escapeHtml(formatQuantity(meter.used))} used`,
    meter.limit === null
      ? null
      : `allowance ${escapeHtml(formatQuantity(meter.limit))}`
  ].filter((part): part is string => part !== null);
  const note =
    detail.length === 0 ? reset : `${detail.join(" &middot; ")}<br>${reset}`;
  if (percentUsed === null) {
    // No allowance reported, so a bar would imply a denominator that does not
    // exist. The sibling monitors take the same "state it plainly" path.
    return (
      `<span style="font-weight:bold">${escapeHtml(label)}</span> ` +
      `${escapeHtml(formatQuantity(meter.used))}<br>` +
      `<em>Allowance unavailable; absolute usage only<br>${reset}</em><br><br>`
    );
  }
  return hoverBarBlock(label, formatPercent(percentUsed), percentUsed, note);
}

/**
 * On-demand spend, measured against the pool it actually draws from.
 *
 * The pool is SHARED, so personal spend alone answers the wrong question. What
 * determines whether the next request is billable is how much is left in the pool,
 * which is why the bar tracks the pool and the personal figure is stated beside it.
 * A pool can be drawn past its limit, so the bar clamps and the note says so rather
 * than rendering a bar wider than its track.
 */
function onDemandBar(snapshot: UsageSnapshot, now: number): string {
  const team = snapshot.teamContext;
  // `?? null` rather than a bare read: these fields are additive, so a snapshot
  // cached by an older build carries them as undefined. The declared type says
  // `Money | null`, which is exactly the assurance that does not survive persisted
  // data.
  const limit = team.sharedSpendLimit ?? null;
  const used = team.sharedSpendUsed ?? null;
  const remaining = team.sharedSpendRemaining ?? null;
  const personal = snapshot.onDemand.personalSpend ?? null;
  const yours = personal === null ? "not reported" : formatMoney(personal);

  if (snapshot.onDemand.enabled !== true) {
    return (
      `<span style="font-weight:bold">Extra Credits</span><br>` +
      `<em>On-demand spending is off for this account</em><br><br>`
    );
  }
  if (limit === null || limit.amount <= 0 || used === null) {
    return (
      `<span style="font-weight:bold">Extra Credits</span><br>` +
      `<em>${escapeHtml(yours)} used by your account &middot; shared limit not reported</em><br><br>`
    );
  }

  const percent = (used.amount / limit.amount) * 100;
  const left =
    remaining === null
      ? ""
      : remaining.amount <= 0
        ? " &middot; none left"
        : ` &middot; ${escapeHtml(formatMoney(remaining))} left`;
  // Two lines, matching the sibling monitors: the organization's draw against the
  // shared limit on top, the user's own contribution in italics beneath. Personal
  // spend alone is the misleading reading - it looks like headroom that the pool
  // may not actually have.
  const note =
    `${escapeHtml(formatMoney(used))} / ${escapeHtml(formatMoney(limit))} used this month by the organization${left}` +
    `<br><em>(${escapeHtml(yours)} used by your account)</em>` +
    `<br>Resets ${escapeHtml(formatReset(snapshot, now))}`;
  return hoverBarBlock("Extra Credits", formatPercent(percent), percent, note);
}

/** The reset sentence repeated under each included-usage bar. */
function resetLine(snapshot: UsageSnapshot, now: number): string {
  return `Resets ${escapeHtml(formatReset(snapshot, now))}`;
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
