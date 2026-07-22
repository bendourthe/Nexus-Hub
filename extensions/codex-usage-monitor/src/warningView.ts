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
 * Visibility is gated by the `codexUsage.warningActive` context key: the view
 * (and its container icon) exist only while a warning is live, so revealing it
 * on a threshold crossing and dismissing it via Cancel both map cleanly onto
 * flipping that context key. Icons render as a stacked, narrow card. VS Code
 * notifications render `$(...)` literally and collapse newlines, so the icon-rich
 * layout is only achievable in a webview.
 */
export const WARNING_VIEW_ID = "codexUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "codexUsage.warningActive";

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
    const label = "Codex";
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
