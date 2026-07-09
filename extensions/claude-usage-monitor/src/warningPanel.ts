import * as vscode from "vscode";
import { UrgencyLevel } from "./types";
import { formatResetLabel } from "./usageStore";
import { UsageSuggestion } from "./recommendations";

/**
 * A webview panel that renders the usage-threshold warning as a rich card
 * (warning header, a circular usage ring, per-recommendation icon rows, a reset
 * box, and actions). This is the webview counterpart to the plain notification
 * toast: VS Code notifications render `$(...)` literally and collapse newlines,
 * so icons and a stacked layout are only achievable in a webview. Introduced in
 * v3.11.2 after the notification-toast approach could not render the mockup.
 *
 * A single panel instance is reused (revealed + re-rendered) so repeated
 * threshold crossings update one tab rather than stacking tabs.
 */
export interface WarningCallbacks {
  onOpenDashboard: () => void;
}

const URGENCY_COLOR: Record<UrgencyLevel, string> = {
  low: "#3fb950",
  moderate: "#d29922",
  high: "#db6d28",
  critical: "#f85149",
};

export class WarningPanel {
  private static currentPanel: WarningPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    private suggestion: UsageSuggestion,
    private urgency: UrgencyLevel,
    private callbacks: WarningCallbacks,
  ) {
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      (message: { command: string }) => {
        switch (message.command) {
          case "cancel":
            this.dispose();
            break;
          case "openDashboard":
            this.callbacks.onOpenDashboard();
            break;
        }
      },
      null,
      this.disposables,
    );
    this.panel.webview.html = this.getHtml();
  }

  static show(
    suggestion: UsageSuggestion,
    urgency: UrgencyLevel,
    callbacks: WarningCallbacks,
    extensionUri?: vscode.Uri,
  ): WarningPanel {
    if (WarningPanel.currentPanel) {
      WarningPanel.currentPanel.suggestion = suggestion;
      WarningPanel.currentPanel.urgency = urgency;
      WarningPanel.currentPanel.callbacks = callbacks;
      WarningPanel.currentPanel.panel.webview.html = WarningPanel.currentPanel.getHtml();
      WarningPanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      return WarningPanel.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      "claudeUsageWarning",
      "Claude Usage Warning",
      vscode.ViewColumn.Beside,
      { enableScripts: true },
    );

    if (extensionUri) {
      panel.iconPath = {
        light: vscode.Uri.joinPath(extensionUri, "icons", "claude-dark.svg"),
        dark: vscode.Uri.joinPath(extensionUri, "icons", "claude-light.svg"),
      };
    }

    WarningPanel.currentPanel = new WarningPanel(panel, suggestion, urgency, callbacks);
    return WarningPanel.currentPanel;
  }

  private getHtml(): string {
    const s = this.suggestion;
    const color = URGENCY_COLOR[this.urgency];
    const pct = Math.max(0, Math.min(100, Math.round(s.percent)));

    // Ring geometry: an SVG circle whose visible arc is `pct` of its circumference.
    const r = 52;
    const circumference = 2 * Math.PI * r;
    const arc = (pct / 100) * circumference;

    const switchRow = s.switchModel
      ? `<div class="rec">${ICON.swap}<span>Switch to a lighter model (<strong>${escapeHtml(s.switchModel)}</strong>)</span></div>`
      : "";

    // "Resets in 3h 7m" / "Resets on Tuesday ..." -> "Usage will reset in 3h 7m."
    const resetSentence = "Usage will " + formatResetLabel(s.resetsIn).replace(/^Resets/, "reset") + ".";

    return this.wrapHtml(`
      <div class="card">
        <div class="header">
          <span class="warn-icon" style="color:${color}">${ICON.warning}</span>
          <h1>Claude Usage Warning</h1>
          <button class="close" onclick="send('cancel')" title="Close" aria-label="Close">${ICON.close}</button>
        </div>

        <div class="divider"></div>

        <div class="body">
          <div class="ring-wrap">
            <svg class="ring" viewBox="0 0 120 120" width="132" height="132" aria-hidden="true">
              <circle class="ring-track" cx="60" cy="60" r="${r}" fill="none" stroke-width="10"/>
              <circle cx="60" cy="60" r="${r}" fill="none" stroke="${color}" stroke-width="10"
                      stroke-linecap="round" stroke-dasharray="${arc.toFixed(2)} ${circumference.toFixed(2)}"
                      transform="rotate(-90 60 60)"/>
            </svg>
            <div class="ring-center">
              <div class="ring-pct">${pct}%</div>
              <div class="ring-label">${escapeHtml(s.label)}</div>
            </div>
          </div>

          <div class="recs">
            <div class="rec-head">${ICON.bulb}<span>Consider the following recommendations:</span></div>
            ${switchRow}
            <div class="rec">${ICON.gauge}<span>${escapeHtml(s.effortAdvice)}</span></div>
          </div>
        </div>

        <div class="reset-box">
          ${ICON.clock}<span>${escapeHtml(resetSentence)}</span>
        </div>

        <div class="divider"></div>

        <div class="footer">
          <span class="source">${ICON.chart}<span>Source: Claude Usage Monitor</span></span>
          <span class="footer-actions">
            <button class="secondary" onclick="send('openDashboard')">Open Dashboard</button>
            <button class="primary" onclick="send('cancel')">Cancel</button>
          </span>
        </div>
      </div>
    `);
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
      padding: 24px;
      display: flex;
      justify-content: center;
    }
    .card {
      width: 100%;
      max-width: 620px;
      border: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.35));
      border-radius: 10px;
      padding: 20px 24px;
      background: var(--vscode-editorWidget-background, var(--vscode-editor-background));
    }
    .header {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header h1 {
      font-size: 22px;
      font-weight: 700;
      margin: 0;
      flex: 1;
      color: var(--vscode-editor-foreground);
    }
    .warn-icon svg { display: block; width: 30px; height: 30px; }
    .close {
      background: transparent;
      border: none;
      color: var(--vscode-descriptionForeground, var(--vscode-foreground));
      cursor: pointer;
      padding: 4px;
      opacity: 0.7;
      border-radius: 4px;
    }
    .close:hover { opacity: 1; background: var(--vscode-toolbar-hoverBackground, rgba(128,128,128,0.2)); }
    .close svg { display: block; width: 18px; height: 18px; }
    .divider {
      border-top: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      margin: 16px 0;
    }
    .body {
      display: flex;
      align-items: center;
      gap: 28px;
    }
    .ring-wrap { position: relative; flex-shrink: 0; width: 132px; height: 132px; }
    .ring-track { stroke: rgba(128,128,128,0.25); }
    .ring-center {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      pointer-events: none;
    }
    .ring-pct { font-size: 30px; font-weight: 700; line-height: 1; }
    .ring-label { font-size: 12px; opacity: 0.7; margin-top: 4px; }
    .recs { flex: 1; display: flex; flex-direction: column; gap: 16px; }
    .rec-head, .rec {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 15px;
      line-height: 1.4;
    }
    .rec-head { font-weight: 500; }
    .rec-head svg, .rec svg { flex-shrink: 0; width: 22px; height: 22px; }
    .icon-bulb { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-swap { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-gauge { color: var(--vscode-charts-green, #3fb950); }
    .icon-clock { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-chart { color: var(--vscode-descriptionForeground, #8b949e); }
    .rec strong { font-weight: 700; }
    .reset-box {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      border: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      border-radius: 8px;
      font-size: 14px;
    }
    .reset-box svg { flex-shrink: 0; width: 20px; height: 20px; }
    .footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .source {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      opacity: 0.8;
    }
    .source svg { width: 18px; height: 18px; }
    .footer-actions { display: flex; gap: 8px; }
    button {
      padding: 8px 18px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-family: var(--vscode-font-family);
    }
    button.primary { color: var(--vscode-button-foreground); background: var(--vscode-button-background); }
    button.primary:hover { background: var(--vscode-button-hoverBackground); }
    button.secondary { color: var(--vscode-button-secondaryForeground); background: var(--vscode-button-secondaryBackground); }
    button.secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
  </style>
</head>
<body>
  ${body}
  <script>
    const vscode = acquireVsCodeApi();
    function send(command) { vscode.postMessage({ command }); }
  </script>
</body>
</html>`;
  }

  private dispose(): void {
    WarningPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }
}

// Inline SVG icons (self-contained; no font/resource loading, works under the
// default webview CSP). Line-style, currentColor, so CSS classes tint them.
const ICON = {
  warning:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  close:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  bulb:
    '<span class="icon-bulb"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg></span>',
  swap:
    '<span class="icon-swap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg></span>',
  gauge:
    '<span class="icon-gauge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="m13.4 12.6 3.6-3.6"/><path d="M3.5 18a9 9 0 1 1 17 0"/></svg></span>',
  clock:
    '<span class="icon-clock"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></svg></span>',
  chart:
    '<span class="icon-chart"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="20" x2="6" y2="13"/><line x1="12" y1="20" x2="12" y2="8"/><line x1="18" y1="20" x2="18" y2="11"/></svg></span>',
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
