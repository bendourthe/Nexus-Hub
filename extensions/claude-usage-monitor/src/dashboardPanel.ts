import * as vscode from "vscode";
import { UsageData, formatModelName } from "./types";
import { formatResetLabel, nextMonthlyResetLabel } from "./usageStore";
import { ProviderFetchError, describeProviderError } from "./providers";
import {
  getRecommendation,
  pickTriggerMetric,
  buildUsageSuggestion,
} from "./recommendations";
import {
  DraftState,
  currentSettings,
  saveSettings,
  resetSettings,
  settingsStylesCss,
  settingsSectionHtml,
  settingsScriptJs,
} from "./settingsPanel";

export interface DashboardCallbacks {
  onRefresh: () => void;
  onOpenUsagePage: () => void;
}

export class DashboardPanel {
  private static currentPanel: DashboardPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    private data: UsageData | undefined,
    private timeSince: string,
    private fetchError: ProviderFetchError | undefined,
    private callbacks: DashboardCallbacks,
  ) {
    this.panel = panel;

    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

    this.panel.webview.onDidReceiveMessage(
      async (message: { command: string; draft?: DraftState }) => {
        switch (message.command) {
          case "refresh":
            this.panel.webview.postMessage({ command: "setLoading" });
            this.callbacks.onRefresh();
            break;
          case "openUsagePage":
            this.callbacks.onOpenUsagePage();
            break;
          case "save": {
            // Persist the inline settings form. The extension's config watcher
            // re-renders this dashboard; we also echo the stored values back so
            // the form reflects them immediately.
            const persisted = await saveSettings(message.draft as DraftState);
            this.panel.webview.postMessage({ command: "loadSettings", settings: persisted });
            break;
          }
          case "reset": {
            const persisted = await resetSettings();
            this.panel.webview.postMessage({ command: "loadSettings", settings: persisted });
            break;
          }
        }
      },
      null,
      this.disposables
    );

    this.panel.webview.html = this.getHtml();
  }

  static show(
    data: UsageData | undefined,
    timeSince: string,
    fetchError: ProviderFetchError | undefined,
    callbacks: DashboardCallbacks,
    extensionUri?: vscode.Uri,
  ): DashboardPanel {
    if (DashboardPanel.currentPanel) {
      DashboardPanel.currentPanel.data = data;
      DashboardPanel.currentPanel.timeSince = timeSince;
      DashboardPanel.currentPanel.fetchError = fetchError;
      DashboardPanel.currentPanel.callbacks = callbacks;
      DashboardPanel.currentPanel.panel.webview.html =
        DashboardPanel.currentPanel.getHtml();
      DashboardPanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      return DashboardPanel.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      "claudeUsageDashboard",
      "Claude Usage",
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );

    if (extensionUri) {
      panel.iconPath = {
        light: vscode.Uri.joinPath(extensionUri, "icons", "claude-dark.svg"),
        dark: vscode.Uri.joinPath(extensionUri, "icons", "claude-light.svg"),
      };
    }

    DashboardPanel.currentPanel = new DashboardPanel(
      panel,
      data,
      timeSince,
      fetchError,
      callbacks,
    );
    return DashboardPanel.currentPanel;
  }

  update(data: UsageData | undefined, timeSince: string, fetchError?: ProviderFetchError): void {
    this.data = data;
    this.timeSince = timeSince;
    if (fetchError !== undefined) {
      this.fetchError = fetchError;
    }
    this.panel.webview.html = this.getHtml();
  }

  static updateIfOpen(
    data: UsageData | undefined,
    timeSince: string,
    fetchError: ProviderFetchError | undefined,
  ): void {
    if (!DashboardPanel.currentPanel) {
      return;
    }
    DashboardPanel.currentPanel.data = data;
    DashboardPanel.currentPanel.timeSince = timeSince;
    DashboardPanel.currentPanel.fetchError = fetchError;
    DashboardPanel.currentPanel.panel.webview.html = DashboardPanel.currentPanel.getHtml();
  }

  /** Reveal the inline settings section (used by the palette "Settings" command). */
  static revealSettings(): void {
    DashboardPanel.currentPanel?.panel.webview.postMessage({ command: "openSettings" });
  }

  private getHtml(): string {
    const data = this.data;

    // Only show error banner for actionable errors when no cached data is available,
    // or for non-rate-limit errors. Rate-limiting is a known upstream issue and should
    // not alarm the user when cached data is displayed.
    const showErrorBanner = this.fetchError &&
      (this.fetchError.code !== "rate-limited" || !data);

    const errorBanner = showErrorBanner
      ? `<div class="error-banner">
          <span class="error-icon">&#9888;</span>
          <span>${escapeHtml(describeProviderError(this.fetchError!))}</span>
          <button onclick="send('refresh')" class="retry-btn">Retry</button>
        </div>`
      : "";

    if (!data) {
      const emptyMessage = this.fetchError?.code === "rate-limited"
        ? "Waiting for first successful fetch. The usage API may be temporarily unavailable."
        : "Usage data will appear here once auto-fetch completes or you enter data manually.";

      return this.wrapHtml(`
        ${errorBanner}
        <div class="empty-state">
          <h2>No Usage Data</h2>
          <p>${escapeHtml(emptyMessage)}</p>
          <div class="actions">
            <button id="refreshBtn" onclick="send('refresh')">Fetch Now</button>
          </div>
        </div>
      `);
    }

    const recommendation = getRecommendation(data);
    const suggestion = activeSuggestion(data);
    const sourceLabel = data.dataSource === "api" ? "Auto-fetched" : "Manually entered";

    return this.wrapHtml(`
      ${errorBanner}
      <h2>Claude Usage Dashboard</h2>

      <div class="section">
        <h3>Current Session</h3>
        ${this.renderProgressBar(data.session.percent, data.session.resetsIn, data.session.resetsAt)}
      </div>

      <div class="section">
        <h3>Weekly</h3>
        ${this.renderProgressBar(data.weeklyAllModels.percent, data.weeklyAllModels.resetsIn, data.weeklyAllModels.resetsAt)}
      </div>

      ${data.extraUsage && data.extraUsage.isEnabled ? `
      <div class="section">
        <h3>Extra Credits</h3>
        <div class="extra-credits-info">$${data.extraUsage.usedCredits.toFixed(2)} / $${data.extraUsage.monthlyLimit.toFixed(2)} used this month</div>
        ${data.extraUsage.utilization != null ? this.renderProgressBar(Math.round(data.extraUsage.utilization), nextMonthlyResetLabel(), null) : ""}
      </div>
      ` : ""}

      <div class="divider"></div>

      <div class="section">
        <h3>Current Model</h3>
        <div class="model-name">${escapeHtml(formatModelName(data.currentModel))}</div>
      </div>

      <div class="section">
        <h3>Recommendation</h3>
        <p class="recommendation urgency-${recommendation.urgency}">${escapeHtml(suggestion ?? recommendation.message)}</p>
        ${!suggestion && recommendation.suggestedModel ? `<p class="suggested-model">Suggested: <strong>${escapeHtml(formatModelName(recommendation.suggestedModel))}</strong></p>` : ""}
      </div>

      ${recommendation.tips.length > 0 ? `
      <div class="section">
        <h3>Tips</h3>
        <ul class="tips">
          ${recommendation.tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("\n")}
        </ul>
      </div>
      ` : ""}

      ${settingsSectionHtml(currentSettings())}

      <div class="divider"></div>

      <div class="actions">
        <button id="refreshBtn" onclick="send('refresh')">Refresh Now</button>
        <button onclick="send('openUsagePage')" class="secondary">Open Usage Page</button>
        <button onclick="toggleSettings()" class="icon-btn" title="Settings" aria-label="Settings">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.687.706-1.99 1.99l.169.31a1.464 1.464 0 0 1-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.697 1.283.707 2.687 1.99 1.99l.311-.17a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.687-.706 1.99-1.99l-.169-.31a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.697-1.283-.707-2.687-1.99-1.99l-.311.17a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/>
          </svg>
        </button>
      </div>

      <p class="last-updated">${sourceLabel} ${escapeHtml(this.timeSince)}</p>
    `);
  }

  private renderProgressBar(percent: number, resetsIn: string, resetsAt: number | null): string {
    const attr = resetsAt != null ? ` data-resets-at="${resetsAt}"` : "";
    return `
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${percent}%;"></div>
        </div>
        <span class="progress-label">${percent}%</span>
      </div>
      <span class="progress-subtitle"${attr}>${escapeHtml(formatResetLabel(resetsIn))}</span>
    `;
  }

  private wrapHtml(body: string): string {
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      padding: 20px;
      max-width: 500px;
      margin: 0 auto;
    }
    h2 {
      color: var(--vscode-editor-foreground);
      margin-top: 0;
      font-size: 16px;
    }
    h3 {
      color: var(--vscode-editor-foreground);
      margin: 0 0 8px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      opacity: 0.8;
    }
    .section {
      margin-bottom: 16px;
    }
    .divider {
      border-top: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.35));
      margin: 16px 0;
    }
    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 16px;
      background: var(--vscode-inputValidation-warningBackground, rgba(255,204,0,0.1));
      border: 1px solid var(--vscode-inputValidation-warningBorder, #cca700);
      border-radius: 4px;
      font-size: 12px;
      line-height: 1.4;
    }
    .error-icon {
      flex-shrink: 0;
      font-size: 14px;
    }
    .info-banner {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 16px;
      background: var(--vscode-inputValidation-infoBackground, rgba(0,102,204,0.1));
      border: 1px solid var(--vscode-inputValidation-infoBorder, #007acc);
      border-radius: 4px;
      font-size: 12px;
      line-height: 1.4;
    }
    .info-icon {
      flex-shrink: 0;
      font-size: 14px;
    }
    .extra-credits-info {
      font-size: 13px;
      margin-bottom: 6px;
    }
    .retry-btn {
      flex-shrink: 0;
      margin-left: auto;
      padding: 3px 10px;
      font-size: 11px;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      color: var(--vscode-button-foreground);
      background: var(--vscode-button-background);
    }
    .retry-btn:hover {
      background: var(--vscode-button-hoverBackground);
    }
    .progress-container {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .progress-bar {
      flex: 1;
      height: 8px;
      background: rgba(128,128,128,0.2);
      border-radius: 4px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: #C15F3C;
      border-radius: 4px;
      transition: width 0.3s ease;
    }
    .progress-label {
      font-size: 14px;
      font-weight: bold;
      min-width: 40px;
      text-align: right;
    }
    .progress-subtitle {
      font-size: 11px;
      opacity: 0.7;
      display: block;
      margin-top: 2px;
    }
    .recommendation {
      line-height: 1.5;
      margin: 4px 0;
    }
    .urgency-low { color: #3fb950; }
    .urgency-moderate { color: #d29922; }
    .urgency-high { color: #db6d28; }
    .urgency-critical { color: #f85149; }
    .suggested-model {
      margin: 4px 0;
      font-size: 13px;
    }
    .model-name {
      font-size: 14px;
      font-weight: 600;
    }
    .tips {
      padding-left: 20px;
      margin: 4px 0;
    }
    .tips li {
      line-height: 1.6;
      font-size: 12px;
    }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    button {
      padding: 6px 14px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      font-family: var(--vscode-font-family);
      color: var(--vscode-button-foreground);
      background: var(--vscode-button-background);
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button.secondary {
      color: var(--vscode-button-secondaryForeground);
      background: var(--vscode-button-secondaryBackground);
    }
    button.secondary:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    button.icon-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px;
      width: 28px;
      height: 28px;
      color: var(--vscode-button-secondaryForeground);
      background: var(--vscode-button-secondaryBackground);
    }
    button.icon-btn:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    button.icon-btn svg {
      display: block;
    }
    .last-updated {
      font-size: 11px;
      opacity: 0.6;
      margin-top: 12px;
    }
    .empty-state {
      text-align: center;
      padding: 40px 0;
    }
    .empty-state p {
      opacity: 0.7;
      margin-bottom: 20px;
    }
    .empty-state .actions {
      justify-content: center;
    }
    ${settingsStylesCss()}
  </style>
</head>
<body>
  ${body}
  <script>
    const vscode = acquireVsCodeApi();
    function send(command) {
      vscode.postMessage({ command });
    }
    ${settingsScriptJs(currentSettings())}
    // Live countdown: recompute the reset labels from embedded epoch timestamps.
    // Mirrors formatResetTime + formatResetLabel in usageStore.ts: "Resets in 2h 20m"
    // under 24h; "Resets on Tuesday July 7th at 7:00 AM (3d 11h 28m)" for 24h+.
    function fmtCountdown(epochMs) {
      const diff = epochMs - Date.now();
      if (diff <= 0) return "Resets any moment";
      const totalM = Math.floor(diff / 60000);
      const h = Math.floor(totalM / 60);
      const m = totalM % 60;
      if (h < 24) return "Resets in " + (h > 0 ? h + "h " + m + "m" : m + " min");
      const d = new Date(epochMs);
      const weekday = d.toLocaleDateString("en-US", { weekday: "long" });
      const month = d.toLocaleDateString("en-US", { month: "long" });
      const day = d.getDate();
      const r10 = day % 10, r100 = day % 100;
      const suf = (r10 === 1 && r100 !== 11) ? "st" : (r10 === 2 && r100 !== 12) ? "nd" : (r10 === 3 && r100 !== 13) ? "rd" : "th";
      const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
      const days = Math.floor(h / 24);
      const hours = h % 24;
      return "Resets on " + weekday + " " + month + " " + day + suf + " at " + time +
        " (" + days + "d " + hours + "h " + m + "m)";
    }
    setInterval(function() {
      document.querySelectorAll("[data-resets-at]").forEach(function(el) {
        const epoch = Number(el.dataset.resetsAt);
        if (epoch) { el.textContent = fmtCountdown(epoch); }
      });
    }, 60000);
    // Loading state + inline-settings messages from the extension.
    window.addEventListener("message", function(event) {
      const msg = event.data;
      if (msg.command === "setLoading") {
        const btn = document.getElementById("refreshBtn");
        if (btn) { btn.textContent = "Refreshing\u2026"; btn.disabled = true; }
      } else if (msg.command === "loadSettings") {
        applySettings(msg.settings);
      } else if (msg.command === "openSettings") {
        const s = document.getElementById("settings-section");
        if (s) {
          s.removeAttribute("hidden");
          s.scrollIntoView({ behavior: "smooth", block: "start" });
          try { const st = vscode.getState() || {}; st.settingsOpen = true; vscode.setState(st); } catch (e) {}
        }
      }
    });
  </script>
</body>
</html>`;
  }

  private dispose(): void {
    DashboardPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }
}

/**
 * Returns the single most urgent suggestion message based on current usage,
 * or null when no threshold has been crossed. Delegates to the shared
 * pickTriggerMetric / buildUsageSuggestion pair (recommendations.ts) so the
 * dashboard and the toast popup agree under the same conditions.
 */
function activeSuggestion(data: UsageData): string | null {
  return buildUsageSuggestion(data, pickTriggerMetric(data))?.message ?? null;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
