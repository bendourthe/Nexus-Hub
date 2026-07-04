import * as vscode from "vscode";
import { UsageData, UrgencyLevel, ColorConfig, getColorConfig, WORKBENCH_COLOR_KEYS, syncActiveColorToWorkbench } from "./types";
import { getActiveUrgency } from "./recommendations";
import { UsageStore, formatResetLabel, nextMonthlyResetLabel } from "./usageStore";

export class StatusBarManager {
  private readonly statusBarItem: vscode.StatusBarItem;
  private readonly gearItem: vscode.StatusBarItem;
  private autoRefreshTimer: ReturnType<typeof setInterval> | undefined;
  private displayTickTimer: ReturnType<typeof setInterval> | undefined;
  private onAutoRefresh: (() => void) | undefined;
  private onResetExpired: (() => void) | undefined;
  private backoffMultiplier = 1;

  constructor(
    private readonly store: UsageStore,
    private readonly dashboardCommandId: string,
    private readonly settingsCommandId: string
  ) {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = dashboardCommandId;
    this.statusBarItem.name = "Claude Usage Monitor";

    this.gearItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      99
    );
    this.gearItem.text = "$(gear)";
    this.gearItem.tooltip = "Claude Usage: Settings";
    this.gearItem.command = settingsCommandId;
    this.gearItem.name = "Claude Usage Settings";
  }

  setAutoRefreshCallback(callback: () => void): void {
    this.onAutoRefresh = callback;
  }

  setResetExpiredCallback(callback: () => void): void {
    this.onResetExpired = callback;
  }

  show(): void {
    this.refresh();
    this.statusBarItem.show();
    this.gearItem.show();
    this.startAutoRefreshTimer();
    this.startDisplayTick();
  }

  hide(): void {
    this.statusBarItem.hide();
    this.gearItem.hide();
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
    this.startAutoRefreshTimer();
  }

  resetBackoff(): void {
    if (this.backoffMultiplier !== 1) {
      this.backoffMultiplier = 1;
      this.startAutoRefreshTimer();
    }
  }

  dispose(): void {
    this.stopAutoRefreshTimer();
    this.stopDisplayTick();
    this.statusBarItem.dispose();
    this.gearItem.dispose();
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
      this.statusBarItem.text = "$(claude-icon) Claude Usage: --% (current) --% (week)";
      this.statusBarItem.tooltip = "Click to view Claude usage dashboard";
      this.statusBarItem.backgroundColor = undefined;
      this.gearItem.backgroundColor = undefined;
      return;
    }

    const overallUrgency = getActiveUrgency(data);
    const staleLabel = this.isDataStale(data) ? " $(warning)" : "";

    this.statusBarItem.text =
      `$(claude-icon) Claude Usage: ${data.session.percent}% (current) ${data.weeklyAllModels.percent}% (week)${staleLabel}`;

    this.statusBarItem.tooltip = this.buildTooltip(data);
    const bgColor = this.getBackgroundColor(overallUrgency);
    this.statusBarItem.backgroundColor = bgColor;
    // Mirror the urgency color on the gear so the user sees that the gear icon
    // belongs to the Claude Usage Monitor, and not to some unrelated extension.
    this.gearItem.backgroundColor = bgColor;
    // Swap warningBackground hex between moderate and high colors (they share the same ThemeColor ID)
    void syncActiveColorToWorkbench(overallUrgency, getColorConfig());
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

  private startAutoRefreshTimer(): void {
    this.stopAutoRefreshTimer();

    const config = vscode.workspace.getConfiguration("claudeUsage");
    const intervalMinutes = config.get<number>("refreshInterval", 5);
    const effectiveMs = intervalMinutes * 60_000 * this.backoffMultiplier;

    this.autoRefreshTimer = setInterval(() => {
      if (this.onAutoRefresh) {
        this.onAutoRefresh();
      }
    }, effectiveMs);
  }

  private stopAutoRefreshTimer(): void {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
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
