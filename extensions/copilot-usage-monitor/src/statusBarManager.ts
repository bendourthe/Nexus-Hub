import * as vscode from "vscode";
import {
  BAR_FILL,
  BAR_TRACK,
  CONFIG_SECTION,
  ColorConfig,
  UrgencyLevel,
  UsageData,
  WORKBENCH_COLOR_KEYS,
  getColorConfig,
  getRefreshIntervalMinutes,
  getThresholdConfig,
  WINDOW_LABEL,
  headlineOf,
  syncActiveColorToWorkbench,
} from "./types";
import { getActiveUrgency, triggerPercent } from "./recommendations";
import { UsageStore, formatElapsed, formatPercent, formatResetLabel, poolUsageLine } from "./usageStore";
import { NOT_CONNECTED_HINT, noPercentHint } from "./recommendations";
import type { ProviderFetchError } from "./providers/types";

/** The GitHub Copilot glyph, contributed as an icon font in package.json. */
const COPILOT_ICON = "$(copilot-icon)";
// An en-space keeps the icon from looking glued to the text; plain spaces can collapse.
const ICON_GAP = "\u2002";
const NEAR_MODERATE_BAND = 10;
const NEAR_THRESHOLD_INTERVAL_MS = 60_000;

/**
 * The status-bar text for a cached figure, with the precedence of
 * {@link headlineOf}: a percentage of the month's window, "~" for an
 * approximate pool total, and `--% (month)` whenever no percentage exists. A
 * credit count is never shown (v4.13.8 Phase 6).
 */
export function statusText(data: UsageData | undefined, compact: boolean, staleLabel = ""): string {
  const label = compact ? "" : "Copilot: ";
  const headline = headlineOf(data);
  const body =
    headline.kind === "percent"
      ? `${headline.approximate ? "~" : ""}${formatPercent(headline.percent)}% (${WINDOW_LABEL})`
      : `--% (${WINDOW_LABEL})`;
  return `${COPILOT_ICON}${ICON_GAP}${label}${body}${staleLabel}`;
}

export class StatusBarManager {
  private readonly statusBarItem: vscode.StatusBarItem;
  private autoRefreshTimer: ReturnType<typeof setTimeout> | undefined;
  private autoRefreshEnabled = false;
  private displayTickTimer: ReturnType<typeof setInterval> | undefined;
  private onAutoRefresh: (() => void | Promise<void>) | undefined;
  private onResetExpired: (() => void) | undefined;
  private backoffMultiplier = 1;
  private lastError: ProviderFetchError | undefined;

  constructor(
    private readonly store: UsageStore,
    dashboardCommandId: string,
  ) {
    // Right-aligned priorities run left to right from high to low: Claude 105,
    // Codex 103, Cursor 102, this monitor 101, then GitHub Copilot's own item
    // (about 100.5), so the usage monitors group together with Copilot last.
    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 101);
    this.statusBarItem.command = dashboardCommandId;
    this.statusBarItem.name = "Copilot Usage Monitor";
  }

  setAutoRefreshCallback(callback: () => void | Promise<void>): void {
    this.onAutoRefresh = callback;
  }

  setResetExpiredCallback(callback: () => void): void {
    this.onResetExpired = callback;
  }

  /** The last fetch error, used for the tooltip when there is no cached figure. */
  setLastError(error: ProviderFetchError | undefined): void {
    this.lastError = error;
  }

  show(): void {
    this.refresh();
    this.statusBarItem.show();
    this.scheduleAutoRefresh();
    this.startDisplayTick();
  }

  hide(): void {
    this.statusBarItem.hide();
    this.stopAutoRefreshTimer();
    this.stopDisplayTick();
  }

  refresh(): void {
    this.updateDisplay(this.store.get());
  }

  showLoading(): void {
    this.statusBarItem.text = "$(sync~spin) Refreshing...";
    this.statusBarItem.tooltip = "Fetching Copilot usage from GitHub...";
  }

  applyBackoff(): void {
    this.backoffMultiplier = Math.min(this.backoffMultiplier * 2, 4);
    this.scheduleAutoRefresh();
  }

  resetBackoff(): void {
    if (this.backoffMultiplier !== 1) {
      this.backoffMultiplier = 1;
      this.scheduleAutoRefresh();
    }
  }

  dispose(): void {
    this.stopAutoRefreshTimer();
    this.stopDisplayTick();
    this.statusBarItem.dispose();
  }

  private tick(): void {
    this.refresh();
    if (this.onResetExpired && this.store.hasResetExpired()) {
      this.onResetExpired();
    }
  }

  private compact(): boolean {
    return vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("compactStatusBar", false);
  }

  private updateDisplay(data: UsageData | undefined): void {
    if (!data) {
      this.statusBarItem.text = statusText(undefined, this.compact());
      this.statusBarItem.tooltip = this.emptyTooltip();
      this.statusBarItem.backgroundColor = undefined;
      return;
    }
    const urgency = getActiveUrgency(data);
    const headline = headlineOf(data);
    const keptFigure = headline.kind === "percent" && headline.stale;
    const staleLabel = this.isDataStale(data) || keptFigure ? " $(warning)" : "";
    this.statusBarItem.text = statusText(data, this.compact(), staleLabel);
    this.statusBarItem.tooltip = this.buildTooltip(data);
    this.statusBarItem.backgroundColor = this.getBackgroundColor(urgency);
    void syncActiveColorToWorkbench(urgency, getColorConfig());
  }

  private emptyTooltip(): string {
    switch (this.lastError?.code) {
      case "no-credentials":
      case "token-invalid":
        return "Sign in to GitHub to see your Copilot usage. Click to open the dashboard.";
      case "choose-account":
        return "Choose which GitHub account to read. Click to open the dashboard.";
      default:
        return `${NOT_CONNECTED_HINT} Click to open the dashboard.`;
    }
  }

  private isDataStale(data: UsageData): boolean {
    const intervalMinutes = getRefreshIntervalMinutes();
    return Date.now() - data.lastUpdated > intervalMinutes * 2 * 60_000;
  }

  private buildTooltip(data: UsageData): vscode.MarkdownString {
    const md = new vscode.MarkdownString("", true);
    md.isTrusted = true;
    md.supportThemeIcons = true;
    md.supportHtml = true;

    const W = 280;
    const barH = 6;
    const fontSize = 12;
    const textY = fontSize;
    const barY = textY + 6;
    const svgH = barY + barH;
    const kind = vscode.window.activeColorTheme.kind;
    const isDark = kind === vscode.ColorThemeKind.Dark || kind === vscode.ColorThemeKind.HighContrast;
    const labelColor = isDark ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.92)";
    const dimColor = isDark ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.55)";

    const bar = (label: string, pct: number, valueText: string): string => {
      const fillW = Math.round((W * Math.min(100, Math.max(0, pct))) / 100);
      const svg =
        `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${svgH}">` +
        `<text x="0" y="${textY}" fill="${labelColor}" font-weight="bold" font-family="system-ui,sans-serif" font-size="${fontSize}">${escapeXml(label)}</text>` +
        `<text x="${W}" y="${textY}" fill="${dimColor}" font-family="system-ui,sans-serif" font-size="${fontSize}" text-anchor="end">${escapeXml(valueText)}</text>` +
        `<rect y="${barY}" width="${W}" height="${barH}" rx="3" fill="${BAR_TRACK}"/>` +
        `<rect y="${barY}" width="${fillW}" height="${barH}" rx="3" fill="${BAR_FILL}"/>` +
        `</svg>`;
      return `<img src="data:image/svg+xml,${encodeURIComponent(svg)}" width="${W}" height="${svgH}"><br>`;
    };

    const parts: string[] = [`<span style="opacity:0.6">Copilot Usage</span><br><br>`];
    if (this.isDataStale(data)) {
      parts.push(`<span style="color:#cca700">&#9888; Data may be stale (last updated ${this.store.getTimeSinceUpdate()})</span><br><br>`);
    }
    for (const half of [data.organization, data.personal]) {
      if (half?.stale) {
        const since = formatElapsed(Date.now() - (half.fetchedAt ?? data.lastUpdated));
        parts.push(`<span style="color:#cca700">&#9888; The last refresh failed; showing the figure from ${since}</span><br><br>`);
        break;
      }
    }
    const org = data.organization;
    if (org) {
      if (org.percent != null) {
        const approx = org.approximate ? "~" : "";
        parts.push(
          bar(`Organization pool (${WINDOW_LABEL})`, org.percent, `${approx}${formatPercent(org.percent)}%`) +
            `${poolUsageLine(org.used, org.total)}${org.approximate ? " (approximate total)" : ""}<br>` +
            `<em>${formatResetLabel(org.resetsAt)}</em><br><br>`,
        );
      } else {
        parts.push(`Organization pool: --% (${WINDOW_LABEL}). GitHub reported no Copilot seats, so there is no pool total.<br><br>`);
      }
    }
    const personal = data.personal;
    if (personal) {
      if (personal.quotas.length > 0) {
        for (const quota of personal.quotas) {
          parts.push(bar(`${quota.label} (${WINDOW_LABEL})`, quota.percent, `${formatPercent(quota.percent)}%`));
        }
        parts.push(`<em>${escapeHtml(personal.planLabel)}, ${formatResetLabel(personal.resetsAt)}</em><br><br>`);
      } else if (!org) {
        parts.push(`${escapeHtml(personal.planLabel)}: --% (${WINDOW_LABEL})<br><em>${escapeHtml(noPercentHint(personal))}</em><br><br>`);
      }
    }
    parts.push(`<span style="opacity:0.6">Last updated: ${this.store.getTimeSinceUpdate()}</span>`);
    md.appendMarkdown(parts.join(""));
    return md;
  }

  private getBackgroundColor(urgency: UrgencyLevel): vscode.ThemeColor | undefined {
    if (urgency === "low") {
      return undefined;
    }
    const colorOption = getColorConfig()[urgency as keyof ColorConfig];
    if (!colorOption || colorOption === "none") {
      return undefined;
    }
    return new vscode.ThemeColor(WORKBENCH_COLOR_KEYS[urgency as keyof ColorConfig]);
  }

  private scheduleAutoRefresh(): void {
    this.autoRefreshEnabled = true;
    this.clearAutoRefreshTimer();
    this.autoRefreshTimer = setTimeout(() => {
      void this.runAutoRefresh();
    }, this.computeRefreshDelayMs());
  }

  private async runAutoRefresh(): Promise<void> {
    try {
      await this.onAutoRefresh?.();
    } finally {
      if (this.autoRefreshEnabled) {
        this.scheduleAutoRefresh();
      }
    }
  }

  /** The configured interval, shortened to a minute near the moderate threshold; backoff scales both. */
  computeRefreshDelayMs(): number {
    const intervalMinutes = getRefreshIntervalMinutes();
    const baseMs = intervalMinutes * 60_000 * this.backoffMultiplier;
    const percent = triggerPercent(this.store.get());
    if (percent >= 0 && percent >= getThresholdConfig().moderate - NEAR_MODERATE_BAND) {
      return Math.min(baseMs, NEAR_THRESHOLD_INTERVAL_MS * this.backoffMultiplier);
    }
    return baseMs;
  }

  private stopAutoRefreshTimer(): void {
    this.autoRefreshEnabled = false;
    this.clearAutoRefreshTimer();
  }

  private clearAutoRefreshTimer(): void {
    if (this.autoRefreshTimer) {
      clearTimeout(this.autoRefreshTimer);
      this.autoRefreshTimer = undefined;
    }
  }

  private startDisplayTick(): void {
    this.stopDisplayTick();
    this.displayTickTimer = setInterval(() => this.tick(), 60_000);
  }

  private stopDisplayTick(): void {
    if (this.displayTickTimer) {
      clearInterval(this.displayTickTimer);
      this.displayTickTimer = undefined;
    }
  }
}

function escapeXml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeHtml(text: string): string {
  return escapeXml(text).replace(/"/g, "&quot;");
}
