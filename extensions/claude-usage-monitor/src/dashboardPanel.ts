import * as vscode from "vscode";
import { UsageData, formatModelName, is1MContext, baseModelId } from "./types";
import { FetchError, UsageFetcher } from "./usageFetcher";
import {
  getRecommendation,
} from "./recommendations";

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
    private fetchError: FetchError | undefined,
    private callbacks: DashboardCallbacks
  ) {
    this.panel = panel;

    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

    this.panel.webview.onDidReceiveMessage(
      (message: { command: string }) => {
        switch (message.command) {
          case "refresh":
            this.panel.webview.postMessage({ command: "setLoading" });
            this.callbacks.onRefresh();
            break;
          case "openUsagePage":
            this.callbacks.onOpenUsagePage();
            break;
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
    fetchError: FetchError | undefined,
    callbacks: DashboardCallbacks,
    extensionUri?: vscode.Uri
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
      callbacks
    );
    return DashboardPanel.currentPanel;
  }

  update(data: UsageData | undefined, timeSince: string, fetchError?: FetchError): void {
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
    fetchError: FetchError | undefined
  ): void {
    if (!DashboardPanel.currentPanel) {
      return;
    }
    DashboardPanel.currentPanel.data = data;
    DashboardPanel.currentPanel.timeSince = timeSince;
    DashboardPanel.currentPanel.fetchError = fetchError;
    DashboardPanel.currentPanel.panel.webview.html = DashboardPanel.currentPanel.getHtml();
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
          <span>${escapeHtml(UsageFetcher.getErrorMessage(this.fetchError!))}</span>
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

    const is1MModel = is1MContext(data.currentModel);
    const extraCreditsBanner = is1MModel
      ? `<div class="info-banner">
          <span class="info-icon">&#9432;</span>
          <span>1M context models use <strong>extra credits</strong> instead of your standard usage allowance.
          Switch to ${escapeHtml(formatModelName(baseModelId(data.currentModel)))} for standard usage.</span>
        </div>`
      : "";

    const recommendation = getRecommendation(data);
    const sourceLabel = data.dataSource === "api" ? "Auto-fetched" : "Manually entered";

    return this.wrapHtml(`
      ${errorBanner}
      ${extraCreditsBanner}
      <h2>Claude Usage Dashboard</h2>

      <div class="section">
        <h3>Current Session</h3>
        ${this.renderProgressBar(data.session.percent, data.session.resetsIn, data.session.resetsAt)}
      </div>

      <div class="section">
        <h3>Weekly (All Models)</h3>
        ${this.renderProgressBar(data.weeklyAllModels.percent, data.weeklyAllModels.resetsIn, data.weeklyAllModels.resetsAt)}
      </div>

      <div class="section">
        <h3>Weekly (Sonnet)</h3>
        ${this.renderProgressBar(data.weeklySonnet.percent, data.weeklySonnet.resetsIn, data.weeklySonnet.resetsAt)}
      </div>

      ${data.extraUsage && data.extraUsage.isEnabled ? `
      <div class="section">
        <h3>Extra Credits</h3>
        <div class="extra-credits-info">$${data.extraUsage.usedCredits.toFixed(2)} / $${data.extraUsage.monthlyLimit.toFixed(2)} used this month</div>
        ${data.extraUsage.utilization != null ? this.renderProgressBar(Math.round(data.extraUsage.utilization), "monthly", null) : ""}
      </div>
      ` : ""}

      <div class="divider"></div>

      <div class="section">
        <h3>Current Model</h3>
        <div class="model-name">${escapeHtml(formatModelName(data.currentModel))}</div>
      </div>

      <div class="section">
        <h3>Recommendation</h3>
        <p class="recommendation urgency-${recommendation.urgency}">${escapeHtml(recommendation.message)}</p>
        ${recommendation.suggestedModel ? `<p class="suggested-model">Suggested: <strong>${escapeHtml(formatModelName(recommendation.suggestedModel))}</strong></p>` : ""}
      </div>

      ${recommendation.tips.length > 0 ? `
      <div class="section">
        <h3>Tips</h3>
        <ul class="tips">
          ${recommendation.tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("\n")}
        </ul>
      </div>
      ` : ""}

      <div class="divider"></div>

      <div class="actions">
        <button id="refreshBtn" onclick="send('refresh')">Refresh Now</button>
        <button onclick="send('openUsagePage')" class="secondary">Open Usage Page</button>
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
      <span class="progress-subtitle"${attr}>Resets: ${escapeHtml(resetsIn)}</span>
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
  </style>
</head>
<body>
  ${body}
  <script>
    const vscode = acquireVsCodeApi();
    function send(command) {
      vscode.postMessage({ command });
    }
    // Live countdown: recompute "Resets: Xh Ym" labels from embedded epoch timestamps
    function fmtCountdown(epochMs) {
      const diff = epochMs - Date.now();
      if (diff <= 0) return "soon";
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      return h > 0 ? h + "h " + m + "m" : m + "m";
    }
    setInterval(function() {
      document.querySelectorAll("[data-resets-at]").forEach(function(el) {
        const epoch = Number(el.dataset.resetsAt);
        if (epoch) { el.textContent = "Resets: " + fmtCountdown(epoch); }
      });
    }, 60000);
    // Loading state: disable Refresh button when a fetch is in progress
    window.addEventListener("message", function(event) {
      if (event.data.command === "setLoading") {
        const btn = document.getElementById("refreshBtn");
        if (btn) { btn.textContent = "Refreshing\u2026"; btn.disabled = true; }
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

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
