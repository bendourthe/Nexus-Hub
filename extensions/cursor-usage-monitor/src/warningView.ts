import * as vscode from "vscode";
import { METER_FILL_COLOR } from "./types";
import { escapeHtml, formatQuantity } from "./formatters";
import type { UsageSuggestion } from "./recommendations";
import { renderWebviewDocument } from "./webview";

export const WARNING_VIEW_ID = "cursorUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "cursorUsage.warningActive";
export const ICONS8_ATTRIBUTION_URL =
  "https://icons8.com/icon/DiGZkjCzyZXn/cursor-ai";

export interface WarningCallbacks {
  onOpenDashboard(): void;
  onDismiss(): void;
  onOpenAttribution(): void;
}

export class WarningViewProvider implements vscode.WebviewViewProvider {
  private view: vscode.WebviewView | undefined;
  private suggestion: UsageSuggestion | undefined;
  private callbacks: WarningCallbacks | undefined;

  public constructor(private readonly extensionUri: vscode.Uri) {}

  public resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri]
    };
    view.onDidDispose(() => {
      if (this.view === view) {
        this.view = undefined;
      }
    });
    view.webview.onDidReceiveMessage(
      (message: { command?: string }) => {
        if (message.command === "dashboard") {
          this.callbacks?.onOpenDashboard();
        } else if (message.command === "dismiss") {
          void this.dismiss();
        } else if (message.command === "attribution") {
          this.callbacks?.onOpenAttribution();
        }
      }
    );
    view.webview.html = this.render(view.webview);
  }

  public async show(
    suggestion: UsageSuggestion,
    callbacks: WarningCallbacks
  ): Promise<void> {
    this.suggestion = suggestion;
    this.callbacks = callbacks;
    await vscode.commands.executeCommand(
      "setContext",
      WARNING_ACTIVE_CONTEXT,
      true
    );
    if (this.view !== undefined) {
      this.view.webview.html = this.render(this.view.webview);
      this.view.show(true);
    } else {
      await vscode.commands.executeCommand(`${WARNING_VIEW_ID}.focus`);
    }
  }

  public async dismiss(): Promise<void> {
    this.suggestion = undefined;
    this.callbacks?.onDismiss();
    await vscode.commands.executeCommand(
      "setContext",
      WARNING_ACTIVE_CONTEXT,
      false
    );
    // Clearing the context hides the VIEW, but the side bar stays parked on this
    // now-empty container - which presents as a blank black panel with the warning
    // icon still lit, looking like the dismiss failed. Move focus back to the
    // Explorer so dismissing actually returns the user somewhere useful.
    //
    // Failure here is deliberately swallowed: the dismiss itself has already
    // succeeded, and a host without the Explorer command must not turn a successful
    // dismiss into a visible error.
    try {
      await vscode.commands.executeCommand("workbench.view.explorer");
    } catch {
      // Nothing to recover: the warning is already dismissed.
    }
  }

  private render(webview: vscode.Webview): string {
    const image = webview.asWebviewUri(
      vscode.Uri.joinPath(
        this.extensionUri,
        "icons",
        "cursor-ai-48.png"
      )
    );
    return renderWarning(
      this.suggestion,
      image.toString(),
      webview.cspSource
    );
  }
}

export function renderWarning(
  suggestion: UsageSuggestion | undefined,
  imageUri = "cursor-ai-48.png",
  cspSource = "'self'",
  nonce?: string
): string {
  const content =
    suggestion === undefined
      ? `<p role="status">No active Cursor usage warning.</p>`
      : warningContent(suggestion, imageUri);
  return renderWebviewDocument({
    body: content,
    styles: warningStyles(),
    script: `const vscode = acquireVsCodeApi();
    document.querySelectorAll('[data-command]').forEach((control) => {
      control.addEventListener('click', (event) => {
        if (control.tagName === 'A') {
          event.preventDefault();
        }
        vscode.postMessage({ command: control.getAttribute('data-command') });
      });
    });`,
    cspDirectives: [`img-src ${cspSource}`],
    ...(nonce === undefined ? {} : { nonce })
  });
}

const ICON = {
  gauge:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14" aria-hidden="true"><path d="M12 14l4-4"/><path d="M3 20a9 9 0 1 1 18 0"/></svg>',
  clock:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14" aria-hidden="true"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></svg>',
  chart:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13" aria-hidden="true"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/></svg>'
};

/**
 * The warning panel, structured to match the Claude and Codex monitors: a centred
 * brand block, the usage ring, an advice list under one heading, a reset line, and a
 * footer naming the source alongside the two actions.
 */
function warningContent(
  suggestion: UsageSuggestion,
  imageUri: string
): string {
  const severity = capitalize(suggestion.severity);
  const absoluteUsage =
    suggestion.meter.used === null
      ? ""
      : `<div class="rec">${ICON.chart}<span>Absolute usage: ${escapeHtml(formatQuantity(suggestion.meter.used))}</span></div>`;
  const allowance =
    suggestion.meter.limit === null
      ? ""
      : `<div class="rec">${ICON.chart}<span>Allowance: ${escapeHtml(formatQuantity(suggestion.meter.limit))}</span></div>`;
  return `<main class="warn">
    <button class="close" data-command="dismiss" aria-label="Dismiss warning">&#10005;</button>
    <div class="brand">
      <img class="brand-logo" src="${escapeHtml(imageUri)}" width="48" height="48" alt="">
      <div class="brand-title">
        <div class="brand-name">Cursor</div>
        <div class="brand-sub">Usage Monitor</div>
      </div>
    </div>
    <section class="severity ${suggestion.severity}" role="alert">
      <strong>${severityIcon(suggestion.severity)} ${severity} usage warning</strong>
      <p>${escapeHtml(suggestion.message)}</p>
    </section>
    ${usageRing(suggestion)}
    <div class="rec-head"><span>Ways to extend your usage</span></div>
    <div class="recs">
      <div class="rec">${ICON.gauge}<span>${escapeHtml(suggestion.recommendation)}</span></div>
      ${absoluteUsage}
      ${allowance}
    </div>
    <div class="reset-box">
      ${ICON.clock}<span>Usage resets at the end of the billing period.</span>
    </div>
    <div class="divider"></div>
    <div class="footer">
      <span class="source">${ICON.chart}<span>Source: Cursor Usage Monitor</span></span>
      <div class="footer-actions">
        <button class="secondary" data-command="dashboard">Open Dashboard</button>
        <button class="primary" data-command="dismiss">OK</button>
      </div>
    </div>
    <p class="credit">Cursor AI icon by <a href="${ICONS8_ATTRIBUTION_URL}" data-command="attribution">Icons8</a>.</p>
  </main>`;
}

/**
 * A ring rather than a bare number, matching the sibling Claude and Codex monitors.
 *
 * The arc is `percent` of the circumference, drawn from 12 o'clock by rotating the
 * circle -90 degrees, and clamped to 100 so an over-limit pool renders a full ring
 * instead of wrapping past its own start - a second lap would read as a low value.
 */
function usageRing(suggestion: UsageSuggestion): string {
  const percent = Math.max(0, Math.min(100, Math.round(suggestion.percent)));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const arc = (percent / 100) * circumference;
  return `<div class="ring-wrap">
    <svg class="ring" viewBox="0 0 120 120" width="132" height="132" role="meter" aria-label="${escapeHtml(suggestion.label)} usage" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}">
      <circle class="ring-track" cx="60" cy="60" r="${radius}" fill="none" stroke-width="10"/>
      <circle cx="60" cy="60" r="${radius}" fill="none" stroke="${METER_FILL_COLOR}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${arc.toFixed(2)} ${circumference.toFixed(2)}" transform="rotate(-90 60 60)"/>
    </svg>
    <div class="ring-center">
      <div class="ring-pct">${percent}%</div>
      <div class="ring-label">${escapeHtml(suggestion.label)}</div>
    </div>
  </div>`;
}

function warningStyles(): string {
  return `:root{color-scheme:light dark}*{box-sizing:border-box}body{padding:14px;color:var(--vscode-sideBar-foreground);background:var(--vscode-sideBar-background);font:13px/1.5 var(--vscode-font-family)}main{position:relative}.logo{display:block;width:48px;height:48px}h1{font-size:20px;margin:0}header p{margin:0;color:var(--vscode-descriptionForeground)}.close{position:absolute;right:0;top:0;background:transparent;color:var(--vscode-foreground)}.severity{border-left:4px solid;padding:10px;background:var(--vscode-editorWidget-background)}.severity.moderate{border-color:var(--vscode-notificationsWarningIcon-foreground)}.severity.high,.severity.critical{border-color:var(--vscode-notificationsErrorIcon-foreground)}.severity p{margin:2px 0}.ring-wrap{position:relative;width:132px;height:132px;margin:20px auto 8px}
.ring{display:block}
.ring-track{stroke:color-mix(in srgb,${METER_FILL_COLOR} 22%,transparent)}
.ring-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.ring-pct{font-size:30px;font-weight:700;line-height:1.1}
.ring-label{font-size:11px;opacity:.75;max-width:96px}
main{text-align:center}
.brand{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;padding:2px 0}
.brand-logo{display:block;width:48px;height:48px}
.brand-name{font-size:16px;font-weight:600}
.brand-sub{font-size:11px;opacity:.7}
.severity{text-align:left;margin-top:14px}
.rec-head{font-size:11px;text-transform:uppercase;letter-spacing:.06em;opacity:.7;margin:14px 0 8px;text-align:left}
.recs{display:flex;flex-direction:column;gap:8px;text-align:left}
.rec{display:flex;gap:8px;align-items:flex-start;font-size:12px;line-height:1.45}
.rec svg{flex-shrink:0;margin-top:2px;opacity:.8}
.reset-box{display:flex;gap:8px;align-items:center;margin-top:14px;padding:8px 10px;border-radius:4px;background:var(--vscode-editorWidget-background);font-size:12px;text-align:left}
.divider{border-top:1px solid var(--vscode-widget-border,rgba(128,128,128,.35));margin:14px 0}
.footer{display:flex;flex-direction:column;gap:10px;align-items:center}
.source{display:flex;gap:6px;align-items:center;font-size:11px;opacity:.65}
.footer-actions{display:flex;gap:8px;justify-content:center}
button{border-radius:4px}
button.primary{color:var(--vscode-button-foreground);background:var(--vscode-button-background)}.recommendation{border-top:1px solid var(--vscode-widget-border);padding-top:14px}footer{display:flex;gap:8px;margin-top:18px}button{padding:7px 10px;border:1px solid transparent;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit}button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}.credit{font-size:11px;color:var(--vscode-descriptionForeground);margin-top:18px}.credit a{color:var(--vscode-textLink-foreground)}button:focus-visible,a:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}@media(prefers-reduced-motion:reduce){*{transition:none!important}}@media(forced-colors:active){.logo{display:none}.ring-track{stroke:CanvasText}.severity,button{border-color:CanvasText}.severity.moderate,.severity.high,.severity.critical{border-color:CanvasText}}`;
}

function severityIcon(
  severity: UsageSuggestion["severity"]
): string {
  switch (severity) {
    case "moderate":
      return "&#9888;";
    case "high":
      return "&#9650;";
    case "critical":
      return "&#9940;";
  }
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
