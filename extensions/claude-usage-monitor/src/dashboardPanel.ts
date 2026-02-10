import * as vscode from "vscode";
import { UsageData, MODEL_DISPLAY_NAMES } from "./types";
import {
  getRecommendation,
} from "./recommendations";

export interface DashboardCallbacks {
  onRefresh: () => void;
  onManualInput: () => void;
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
    private callbacks: DashboardCallbacks
  ) {
    this.panel = panel;

    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

    this.panel.webview.onDidReceiveMessage(
      (message: { command: string }) => {
        switch (message.command) {
          case "refresh":
            this.callbacks.onRefresh();
            break;
          case "manualInput":
            this.callbacks.onManualInput();
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
    callbacks: DashboardCallbacks,
    extensionUri?: vscode.Uri
  ): DashboardPanel {
    if (DashboardPanel.currentPanel) {
      DashboardPanel.currentPanel.data = data;
      DashboardPanel.currentPanel.timeSince = timeSince;
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
      callbacks
    );
    return DashboardPanel.currentPanel;
  }

  update(data: UsageData | undefined, timeSince: string): void {
    this.data = data;
    this.timeSince = timeSince;
    this.panel.webview.html = this.getHtml();
  }

  private getHtml(): string {
    const data = this.data;

    if (!data) {
      return this.wrapHtml(`
        <div class="empty-state">
          <h2>No Usage Data</h2>
          <p>Usage data will appear here once auto-fetch completes or you enter data manually.</p>
          <div class="actions">
            <button onclick="send('refresh')">Fetch Now</button>
            <button onclick="send('manualInput')" class="secondary">Enter Manually</button>
          </div>
        </div>
      `);
    }

    const recommendation = getRecommendation(data);
    const sourceLabel = data.dataSource === "api" ? "Auto-fetched" : "Manually entered";

    return this.wrapHtml(`
      <h2>Claude Usage Dashboard</h2>

      <div class="section">
        <h3>Current Session</h3>
        ${this.renderProgressBar(data.session.percent, `Resets: ${data.session.resetsIn}`)}
      </div>

      <div class="section">
        <h3>Weekly (All Models)</h3>
        ${this.renderProgressBar(data.weeklyAllModels.percent, `Resets: ${data.weeklyAllModels.resetsIn}`)}
      </div>

      <div class="section">
        <h3>Weekly (Sonnet)</h3>
        ${this.renderProgressBar(data.weeklySonnet.percent, `Resets: ${data.weeklySonnet.resetsIn}`)}
      </div>

      <div class="divider"></div>

      <div class="section">
        <div class="model-label">Current Model: <strong>${escapeHtml(MODEL_DISPLAY_NAMES[data.currentModel])}</strong></div>
      </div>

      <div class="section">
        <h3>Recommendation</h3>
        <p class="recommendation urgency-${recommendation.urgency}">${escapeHtml(recommendation.message)}</p>
        ${recommendation.suggestedModel ? `<p class="suggested-model">Suggested: <strong>${escapeHtml(MODEL_DISPLAY_NAMES[recommendation.suggestedModel])}</strong></p>` : ""}
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
        <button onclick="send('refresh')">Refresh Now</button>
        <button onclick="send('manualInput')" class="secondary">Manual Input</button>
        <button onclick="send('openUsagePage')" class="secondary">Open Usage Page</button>
      </div>

      <p class="last-updated">${sourceLabel} ${escapeHtml(this.timeSince)}</p>
    `);
  }

  private renderProgressBar(percent: number, subtitle: string): string {
    return `
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${percent}%;"></div>
        </div>
        <span class="progress-label">${percent}%</span>
      </div>
      <span class="progress-subtitle">${escapeHtml(subtitle)}</span>
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
    .model-label {
      font-size: 13px;
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
