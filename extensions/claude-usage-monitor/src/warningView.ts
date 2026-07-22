import * as vscode from "vscode";
import { UrgencyLevel } from "./types";
import { formatResetLabel } from "./usageStore";
import { UsageSuggestion } from "./recommendations";

/**
 * The usage-threshold warning as a WebviewView hosted in a narrow activity-bar
 * container, rather than a full-width editor tab. A WebviewView lives in a
 * contributed view container and fills only the (user-resizable) sidebar width,
 * which keeps the warning from stealing a whole editor column.
 *
 * Visibility is gated by the `claudeUsage.warningActive` context key: the view
 * (and its container icon) exist only while a warning is live, so revealing it
 * on a threshold crossing and dismissing it via Cancel both map cleanly onto
 * flipping that context key. Icons render as a stacked, narrow card. VS Code
 * notifications render `$(...)` literally and collapse newlines, so the icon-rich
 * layout is only achievable in a webview.
 */
export const WARNING_VIEW_ID = "claudeUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "claudeUsage.warningActive";

export interface WarningCallbacks {
  onOpenDashboard: () => void;
}

const URGENCY_COLOR: Record<UrgencyLevel, string> = {
  low: "#3fb950",
  moderate: "#d29922",
  high: "#db6d28",
  critical: "#f85149",
};

const LOGO_DATA_URI =
  "data:image/png;base64,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";

export class WarningViewProvider implements vscode.WebviewViewProvider {
  private view: vscode.WebviewView | undefined;
  private suggestion: UsageSuggestion | undefined;
  private urgency: UrgencyLevel = "moderate";
  private callbacks: WarningCallbacks | undefined;

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true };

    view.onDidDispose(() => {
      // The view is torn down when the when-clause turns false; drop the stale ref
      // so the next show() re-reveals (and re-resolves) it instead of posting to a
      // disposed webview.
      if (this.view === view) {
        this.view = undefined;
      }
    });

    view.webview.onDidReceiveMessage((message: { command: string }) => {
      switch (message.command) {
        case "cancel":
          void this.hide();
          break;
        case "openDashboard":
          this.callbacks?.onOpenDashboard();
          break;
      }
    });

    view.webview.html = this.getHtml(view.webview);
  }

  /**
   * Reveal the warning for the given suggestion. Sets the context key so the
   * container becomes available, then either refreshes an already-resolved view
   * or focuses the view id to reveal it (which triggers resolveWebviewView and
   * renders the stored suggestion).
   */
  async show(
    suggestion: UsageSuggestion,
    urgency: UrgencyLevel,
    callbacks: WarningCallbacks,
  ): Promise<void> {
    this.suggestion = suggestion;
    this.urgency = urgency;
    this.callbacks = callbacks;

    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, true);

    if (this.view) {
      this.view.webview.html = this.getHtml(this.view.webview);
      this.view.show(true);
    } else {
      await vscode.commands.executeCommand(`${WARNING_VIEW_ID}.focus`);
    }
  }

  /** Dismiss the warning: flip the context key so the view and its container hide. */
  private async hide(): Promise<void> {
    this.suggestion = undefined;
    this.view = undefined;
    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, false);
  }

  private getHtml(webview: vscode.Webview): string {
    const s = this.suggestion;
    if (!s) {
      return this.wrapHtml(webview, `<p class="empty">No active usage warning.</p>`);
    }

    const color = URGENCY_COLOR[this.urgency];
    const label = "Claude";
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

    return this.wrapHtml(webview, `
      <div class="warn">
        <button class="close" data-command="cancel" title="Dismiss" aria-label="Dismiss">${ICON.close}</button>

        <div class="brand">
          <img class="brand-logo" src="${LOGO_DATA_URI}" alt="" />
          <div class="brand-title">
            <div class="brand-name">${escapeHtml(label)}</div>
            <div class="brand-sub">Usage Monitor</div>
          </div>
        </div>

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

        <div class="rec-head"><span>Ways to extend your usage</span></div>

        <div class="recs">
          ${switchRow}
          <div class="rec">${ICON.gauge}<span>${escapeHtml(s.effortAdvice)}</span></div>
        </div>

        <div class="reset-box">
          ${ICON.clock}<span>${escapeHtml(resetSentence)}</span>
        </div>

        <div class="divider"></div>

        <div class="footer">
          <span class="source">${ICON.chart}<span>Source: ${escapeHtml(label)} Usage Monitor</span></span>
          <div class="footer-actions">
            <button class="secondary" data-command="openDashboard">Open Dashboard</button>
            <button class="primary" data-command="cancel">OK</button>
          </div>
        </div>
      </div>
    `);
  }

  private wrapHtml(webview: vscode.Webview, body: string): string {
    // Nonce-gated script + strict CSP; buttons are wired with addEventListener
    // (not inline onclick), the reliable VS Code webview pattern.
    const nonce = getNonce();
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background, var(--vscode-editor-background));
      padding: 12px 14px;
    }
    .warn { width: 100%; position: relative; }
    .empty { opacity: 0.7; font-size: 13px; }
    /* Centered brand block: real product icon above a two-line "<PRODUCT>" / "Usage Monitor" title. */
    .brand {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      text-align: center;
      padding: 2px 0;
    }
    /* The full-color extension icon (data URI), sized down from its native resolution so it
       stays crisp; no tinting, so it renders in its original brand colors. */
    .brand-logo { display: block; width: 44px; height: 44px; }
    .brand-title { display: flex; flex-direction: column; align-items: center; gap: 2px; }
    .brand-name {
      font-size: 22px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      line-height: 1.1;
      color: var(--vscode-sideBarTitle-foreground, var(--vscode-foreground));
    }
    .brand-sub {
      font-size: 16px;
      font-weight: 600;
      line-height: 1.1;
      color: var(--vscode-sideBarTitle-foreground, var(--vscode-foreground));
    }
    /* Dismiss control pinned to the top-right corner, clear of the centered brand. */
    .close {
      position: absolute;
      top: 0;
      right: 0;
      background: transparent;
      border: none;
      color: var(--vscode-descriptionForeground, var(--vscode-foreground));
      cursor: pointer;
      padding: 3px;
      opacity: 0.7;
      border-radius: 4px;
    }
    .close:hover { opacity: 1; background: var(--vscode-toolbar-hoverBackground, rgba(128,128,128,0.2)); }
    .close svg { display: block; width: 16px; height: 16px; }
    .divider {
      border-top: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      margin: 12px 0;
    }
    /* Small, centered section heading below the ring (previously the large hero heading). */
    .rec-head {
      font-size: 13px;
      font-weight: 600;
      line-height: 1.3;
      text-align: center;
      opacity: 0.85;
      margin: 20px 0 12px;
    }
    .recs {
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: fit-content;
      max-width: 100%;
      margin: 0 auto;
    }
    .rec {
      display: flex;
      align-items: flex-start;
      gap: 9px;
      font-size: 13px;
      line-height: 1.4;
    }
    .rec svg { flex-shrink: 0; width: 18px; height: 18px; margin-top: 1px; }
    .icon-swap { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-gauge { color: var(--vscode-charts-green, #3fb950); }
    .icon-clock { color: var(--vscode-charts-blue, #4aa5f0); }
    .icon-chart { color: var(--vscode-descriptionForeground, #8b949e); }
    .rec strong { font-weight: 700; }
    /* Ring centered below the brand block. */
    .ring-wrap { position: relative; width: 132px; height: 132px; margin: 16px auto 0; }
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
    /* Extra breathing room between the ring and the reset indicator. */
    .reset-box {
      display: flex;
      align-items: flex-start;
      gap: 9px;
      padding: 11px 12px;
      margin-top: 20px;
      border: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.25));
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.4;
    }
    .reset-box svg { flex-shrink: 0; width: 18px; height: 18px; margin-top: 1px; }
    .footer {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .source {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      opacity: 0.8;
    }
    .source svg { width: 16px; height: 16px; }
    .footer-actions { display: flex; gap: 8px; }
    .footer-actions button { flex: 1; }
    button {
      padding: 7px 12px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12.5px;
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
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.querySelectorAll('[data-command]').forEach(function (el) {
      el.addEventListener('click', function () {
        vscode.postMessage({ command: el.getAttribute('data-command') });
      });
    });
  </script>
</body>
</html>`;
  }
}

// Inline SVG icons (self-contained; no font/resource loading). Line-style,
// currentColor, so CSS classes tint them.
const ICON = {
  warning:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  close:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
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

/** Random nonce for the webview's Content-Security-Policy script allowance. */
function getNonce(): string {
  let text = "";
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
