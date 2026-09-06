import * as vscode from "vscode";
import { UsageData, UrgencyLevel, ColorConfig, getColorConfig, getThresholdConfig, WORKBENCH_COLOR_KEYS, syncActiveColorToWorkbench } from "./types";
import { getActiveUrgency, pickTriggerMetric } from "./recommendations";
import { UsageStore, formatResetLabel, nextMonthlyResetLabel } from "./usageStore";

/** The Claude logo glyph, contributed as an icon font in package.json. */
const CLAUDE_ICON = "$(claude-icon)";

// A wider, non-collapsing gap between the icon and the text so the icon does not
// look glued to the numbers. An en-space (U+2002) is used instead of extra plain
// spaces, which the VS Code status bar can collapse to one, so the gap always renders.
const ICON_GAP = "\u2002";

// When the active metric is within this many percentage points below the
// moderate threshold (or already at/above it), the poll cadence drops to
// NEAR_THRESHOLD_INTERVAL_MS so a threshold crossing surfaces the warning
// within ~a minute rather than up to a full refresh interval later.
const NEAR_MODERATE_BAND = 10;
const NEAR_THRESHOLD_INTERVAL_MS = 60_000;

export class StatusBarManager {
  private readonly statusBarItem: vscode.StatusBarItem;
  private autoRefreshTimer: ReturnType<typeof setTimeout> | undefined;
  private autoRefreshEnabled = false;
  private displayTickTimer: ReturnType<typeof setInterval> | undefined;
  private onAutoRefresh: (() => void | Promise<void>) | undefined;
  private onResetExpired: (() => void) | undefined;
  private backoffMultiplier = 1;

  constructor(
    private readonly store: UsageStore,
    private readonly dashboardCommandId: string
  ) {
    // Status-bar priority orders the two usage monitors left-to-right (VS Code
    // renders a higher Right-aligned priority further LEFT). Claude uses 105 and
    // Codex 103 - both ABOVE GitHub Copilot's ~100.5 slot, so the usage items
    // group together with Copilot to their right. There is no gear item: settings
    // now live inline in the dashboard, opened from this usage item.
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      105
    );
    this.statusBarItem.command = dashboardCommandId;
    this.statusBarItem.name = "Claude Usage Monitor";
  }

  setAutoRefreshCallback(callback: () => void | Promise<void>): void {
    this.onAutoRefresh = callback;
  }

  setResetExpiredCallback(callback: () => void): void {
    this.onResetExpired = callback;
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
    const data = this.store.getWithFreshCountdowns();
    this.updateDisplay(data);
  }

  showLoading(): void {
    this.statusBarItem.text = "$(sync~spin) Refreshing...";
    this.statusBarItem.tooltip = "Fetching usage data\u2026";
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
    const data = this.store.getWithFreshCountdowns();
    this.updateDisplay(data);

    if (this.onResetExpired && this.store.hasResetExpired()) {
      this.onResetExpired();
    }
  }

  private updateDisplay(data: UsageData | undefined): void {
    if (!data) {
      this.statusBarItem.text = this.statusText("--", "--", "");
      this.statusBarItem.tooltip = "Click to view Claude usage dashboard";
      this.statusBarItem.backgroundColor = undefined;
      return;
    }

    const overallUrgency = getActiveUrgency(data);
    const staleLabel = this.isDataStale(data) ? " $(warning)" : "";

    this.statusBarItem.text = this.statusText(
      String(data.session.percent),
      String(data.weeklyAllModels.percent),
      staleLabel,
    );

    this.statusBarItem.tooltip = this.buildTooltip(data);
    this.statusBarItem.backgroundColor = this.getBackgroundColor(overallUrgency);
    // Swap warningBackground hex between moderate and high colors (they share the same ThemeColor ID)
    void syncActiveColorToWorkbench(overallUrgency, getColorConfig());
  }

  /**
   * Build the status-bar text. The full form is
   * "<icon> Claude Usage: X% (current) Y% (week)"; when the user enables the
   * `claudeUsage.compactStatusBar` setting the "Claude Usage: " label is dropped,
   * leaving "<icon> X% (current) Y% (week)".
   */
  private statusText(sessionPct: string, weeklyPct: string, staleLabel: string): string {
    const compact = vscode.workspace
      .getConfiguration("claudeUsage")
      .get<boolean>("compactStatusBar", false);
    const label = compact ? "" : "Claude Usage: ";
    return `${CLAUDE_ICON}${ICON_GAP}${label}${sessionPct}% (current) ${weeklyPct}% (week)${staleLabel}`;
  }

  private isDataStale(data: UsageData): boolean {
    const config = vscode.workspace.getConfiguration("claudeUsage");
    const intervalMinutes = config.get<number>("refreshInterval", 5);
    const staleThresholdMs = intervalMinutes * 2 * 60_000;
    return Date.now() - data.lastUpdated > staleThresholdMs;
  }

  private buildTooltip(data: UsageData): vscode.MarkdownString {
    const timeSince = this.store.getTimeSinceUpdate();

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

    // Theme-aware text colors
    const kind = vscode.window.activeColorTheme.kind;
    const isDark =
      kind === vscode.ColorThemeKind.Dark ||
      kind === vscode.ColorThemeKind.HighContrast;
    const labelColor = isDark ? "rgba(255,255,255,0.92)" : "rgba(0,0,0,0.92)";
    const dimColor = isDark ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.55)";

    const sectionImg = (label: string, pct: number) => {
      const fillW = Math.round(W * Math.min(100, Math.max(0, pct)) / 100);
      const svg =
        `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${svgH}">` +
        `<text x="0" y="${textY}" fill="${labelColor}" font-weight="bold" font-family="system-ui,sans-serif" font-size="${fontSize}">${label}</text>` +
        `<text x="${W}" y="${textY}" fill="${dimColor}" font-family="system-ui,sans-serif" font-size="${fontSize}" text-anchor="end">${pct}%</text>` +
        `<rect y="${barY}" width="${W}" height="${barH}" rx="3" fill="rgba(193,95,60,0.2)"/>` +
        `<rect y="${barY}" width="${fillW}" height="${barH}" rx="3" fill="#C15F3C"/>` +
        `</svg>`;
      return `data:image/svg+xml,${encodeURIComponent(svg)}`;
    };

    const section = (label: string, pct: number, resetsIn: string) =>
      `<img src="${sectionImg(label, pct)}" width="${W}" height="${svgH}"><br>` +
      `<em>${formatResetLabel(resetsIn)}</em><br><br>`;

    const staleWarning = this.isDataStale(data)
      ? `<span style="color:#cca700">&#9888; Data may be stale (last updated ${timeSince})</span><br><br>`
      : "";

    // Extra Credits: mirror the dashboard section. When extra usage is disabled,
    // absent, or the monthly limit is 0 (no extra credit available on the
    // account), show an N/A line instead of a progress bar.
    const extra = data.extraUsage;
    const extraCredits =
      extra && extra.isEnabled && extra.monthlyLimit > 0
        ? `<img src="${sectionImg("Extra Credits", extra.utilization != null ? Math.round(extra.utilization) : 0)}" width="${W}" height="${svgH}"><br>` +
          `<em>$${extra.usedCredits.toFixed(2)} / $${extra.monthlyLimit.toFixed(2)} used this month &middot; ${formatResetLabel(nextMonthlyResetLabel())}</em><br><br>`
        : `<span style="color:${labelColor};font-weight:bold">Extra Credits</span><br>` +
          `<em style="color:${dimColor}">No extra credit available on your account</em><br><br>`;

    md.appendMarkdown(
      `<span style="opacity:0.6">Claude Usage</span><br><br>` +
      staleWarning +
      section("Current Session", data.session.percent, data.session.resetsIn) +
      section("Weekly", data.weeklyAllModels.percent, data.weeklyAllModels.resetsIn) +
      extraCredits +
      `<span style="opacity:0.6">Last updated: ${timeSince}</span>`
    );

    return md;
  }

  private getBackgroundColor(
    urgency: UrgencyLevel
  ): vscode.ThemeColor | undefined {
    if (urgency === "low") {
      return undefined;
    }
    const colors = getColorConfig();
    const colorOption = colors[urgency as keyof ColorConfig];
    if (!colorOption || colorOption === "none") {
      return undefined;
    }
    // Use VS Code's standard ThemeColor IDs, which are in the allowed list for
    // StatusBarItem.backgroundColor. Custom hex values are written to
    // workbench.colorCustomizations for these same keys by syncColorsToWorkbench().
    const colorId = WORKBENCH_COLOR_KEYS[urgency as keyof ColorConfig];
    return new vscode.ThemeColor(colorId);
  }

  /**
   * Arm a single self-rescheduling auto-refresh timer. Using setTimeout (not
   * setInterval) lets each cycle recompute its delay from the latest usage, so
   * the poll cadence tightens automatically as usage approaches a threshold and
   * relaxes again when usage is low.
   */
  private scheduleAutoRefresh(): void {
    this.autoRefreshEnabled = true;
    this.clearAutoRefreshTimer();
    const delay = this.computeRefreshDelayMs();
    this.autoRefreshTimer = setTimeout(() => {
      void this.runAutoRefresh();
    }, delay);
  }

  private async runAutoRefresh(): Promise<void> {
    try {
      if (this.onAutoRefresh) {
        await this.onAutoRefresh();
      }
    } finally {
      // Re-arm using the now-updated usage so the next delay reflects fresh data,
      // but only if auto-refresh was not turned off (hide/dispose) mid-fetch.
      if (this.autoRefreshEnabled) {
        this.scheduleAutoRefresh();
      }
    }
  }

  /**
   * Delay until the next auto-fetch. Defaults to the user-configured interval,
   * but shortens to NEAR_THRESHOLD_INTERVAL_MS once the active metric is within
   * NEAR_MODERATE_BAND points of (or above) the moderate threshold, so a warning
   * fires close to when the threshold is actually crossed. Rate-limit backoff
   * still scales both paths.
   */
  private computeRefreshDelayMs(): number {
    const config = vscode.workspace.getConfiguration("claudeUsage");
    const intervalMinutes = config.get<number>("refreshInterval", 10);
    const baseMs = intervalMinutes * 60_000 * this.backoffMultiplier;

    const data = this.store.getWithFreshCountdowns();
    if (!data) {
      return baseMs;
    }

    const percent = pickTriggerMetric(data).percent;
    const moderate = getThresholdConfig().moderate;
    if (percent >= moderate - NEAR_MODERATE_BAND) {
      return Math.min(baseMs, NEAR_THRESHOLD_INTERVAL_MS * this.backoffMultiplier);
    }
    return baseMs;
  }

  /** Fully stop auto-refresh (hide/dispose): clear the timer and disarm re-scheduling. */
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
