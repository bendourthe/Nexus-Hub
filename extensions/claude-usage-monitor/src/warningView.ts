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
        <div class="header">
          <span class="warn-icon" style="color:${color}">${ICON.warning}</span>
          <h1>Claude Usage Warning</h1>
          <button class="close" data-command="cancel" title="Dismiss" aria-label="Dismiss">${ICON.close}</button>
        </div>

        <div class="divider"></div>

        <div class="rec-head"><span>Ways to extend your usage</span></div>

        <div class="recs">
          ${switchRow}
          <div class="rec">${ICON.gauge}<span>${escapeHtml(s.effortAdvice)}</span></div>
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

        <div class="reset-box">
          ${ICON.clock}<span>${escapeHtml(resetSentence)}</span>
        </div>

        <div class="divider"></div>

        <div class="footer">
          <span class="source">${ICON.chart}<span>Source: Claude Usage Monitor</span></span>
          <div class="footer-actions">
            <button class="secondary" data-command="openDashboard">Open Dashboard</button>
            <button class="primary" data-command="cancel">Cancel</button>
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
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background, var(--vscode-editor-background));
      padding: 12px 14px;
    }
    .warn { width: 100%; }
    .empty { opacity: 0.7; font-size: 13px; }
    .header {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .header h1 {
      font-size: 15px;
      font-weight: 700;
      margin: 0;
      flex: 1;
      color: var(--vscode-sideBarTitle-foreground, var(--vscode-foreground));
    }
    .warn-icon svg { display: block; width: 22px; height: 22px; }
    .close {
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
    /* One-line, centered recommendations heading above the ring (wraps only if the
       sidebar is dragged very narrow). */
    .rec-head {
      font-size: 26px;
      font-weight: 500;
      line-height: 1.25;
      text-align: center;
      margin: 2px 0 16px;
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
    /* Ring centered below the recommendations. */
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
