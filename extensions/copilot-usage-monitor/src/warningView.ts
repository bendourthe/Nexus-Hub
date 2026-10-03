import * as vscode from "vscode";
import { UrgencyLevel } from "./types";
import { UsageSuggestion } from "./recommendations";
import { formatPercent } from "./usageStore";

/**
 * The usage-threshold warning as a WebviewView hosted in a narrow activity-bar
 * container, rather than a full-width editor tab. A WebviewView lives in a
 * contributed view container and fills only the (user-resizable) sidebar width,
 * which keeps the warning from stealing a whole editor column.
 *
 * Visibility is gated by the `copilotUsage.warningActive` context key: the view
 * (and its container icon) exist only while a warning is live, so revealing it
 * on a threshold crossing and dismissing it via Cancel both map cleanly onto
 * flipping that context key. Icons render as a stacked, narrow card. VS Code
 * notifications render `$(...)` literally and collapse newlines, so the icon-rich
 * layout is only achievable in a webview.
 */
export const WARNING_VIEW_ID = "copilotUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "copilotUsage.warningActive";

export interface WarningCallbacks {
  onOpenDashboard: () => void;
}

const URGENCY_COLOR: Record<UrgencyLevel, string> = {
  low: "#3fb950",
  moderate: "#d29922",
  high: "#db6d28",
  critical: "#f85149",
};

/** The GitHub Copilot logo (the extension icon at 88 px, displayed at 44 px). */
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
    const label = "Copilot";
    const pct = Math.max(0, Math.min(100, Math.round(s.percent)));

    // Ring geometry: an SVG circle whose visible arc is `pct` of its circumference.
    const r = 52;
    const circumference = 2 * Math.PI * r;
    const arc = (pct / 100) * circumference;

    // "Resets on November 1" -> "Usage will reset on November 1."
    const resetSentence = s.resetLabel.startsWith("Resets")
      ? "Usage will " + s.resetLabel.replace(/^Resets/, "reset") + "."
      : s.resetLabel + ".";

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
            <div class="ring-pct">${escapeHtml(formatPercent(s.percent))}%</div>
            <div class="ring-label">${escapeHtml(s.label)}</div>
          </div>
        </div>

        <div class="rec-head"><span>Ways to extend your usage</span></div>

        <div class="recs">
          <div class="rec">${ICON.gauge}<span>${escapeHtml(s.advice)}</span></div>
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
  close:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
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
