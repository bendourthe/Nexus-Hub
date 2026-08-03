import * as vscode from "vscode";
import type { UsageSuggestion } from "./recommendations";
import { escapeHtml, formatAmount } from "./statusBarManager";
import { formatResetCountdown } from "./usageStore";

export const WARNING_VIEW_ID = "githubUsageWarningView";
export const WARNING_ACTIVE_CONTEXT = "githubUsage.warningActive";

export interface WarningCallbacks { onOpenDashboard(): void; onDismiss(): void; }

export class WarningViewProvider implements vscode.WebviewViewProvider {
  private view: vscode.WebviewView | undefined;
  private suggestion: UsageSuggestion | undefined;
  private callbacks: WarningCallbacks | undefined;

  public constructor(private readonly extensionUri: vscode.Uri) {}

  public resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true, localResourceRoots: [this.extensionUri] };
    view.webview.onDidReceiveMessage((message: { command?: string }) => {
      if (message.command === "dashboard") this.callbacks?.onOpenDashboard();
      if (message.command === "dismiss") void this.dismiss();
    });
    view.webview.html = this.render(view.webview);
  }

  public async show(suggestion: UsageSuggestion, callbacks: WarningCallbacks): Promise<void> {
    this.suggestion = suggestion;
    this.callbacks = callbacks;
    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, true);
    if (this.view) this.view.webview.html = this.render(this.view.webview);
    else await vscode.commands.executeCommand(`${WARNING_VIEW_ID}.focus`);
  }

  public async dismiss(): Promise<void> {
    this.suggestion = undefined;
    this.callbacks?.onDismiss();
    await vscode.commands.executeCommand("setContext", WARNING_ACTIVE_CONTEXT, false);
  }

  private render(webview: vscode.Webview): string {
    const image = webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, "icons", "github-gradient.png"));
    return renderWarning(this.suggestion, image.toString(), Date.now(), webview.cspSource);
  }
}

export function renderWarning(suggestion: UsageSuggestion | undefined, imageUri = "github-gradient.png", now = Date.now(), cspSource = "'self'"): string {
  const webview = { cspSource };
  const content = suggestion === undefined ? `<p role="status">No active GitHub usage warning.</p>` : `<main><button class="close" data-command="dismiss" aria-label="Dismiss warning">&#10005;</button><header><img src="${escapeHtml(imageUri)}" width="44" height="44" alt=""><div><h1>GitHub</h1><p>Usage Monitor</p></div></header><section class="severity ${suggestion.urgency}" role="alert"><strong>${severityIcon(suggestion.urgency)} ${capitalize(suggestion.urgency)} usage</strong><p>${escapeHtml(suggestion.label)}</p></section><div class="value">${Math.round(suggestion.percent)}%</div><p>${formatAmount(suggestion.metric)} of ${suggestion.metric.allowance ?? "unknown"} ${escapeHtml(suggestion.metric.unit)}</p><p>${suggestion.metric.reset === null ? "Reset not reported." : `Resets in ${formatResetCountdown(suggestion.metric.reset.at, now)}.`}</p><p class="recommendation">${escapeHtml(suggestion.recommendation)}</p><footer><button data-command="dashboard">Open dashboard</button><button data-command="dismiss">Dismiss</button></footer><p class="credit"><a href="https://www.streamlinehq.com" title="Streamline icon attribution">Free icon from Streamline</a></p></main>`;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource}; style-src 'unsafe-inline'; script-src 'nonce-warning';"><style>:root{color-scheme:light dark}body{padding:14px;color:var(--vscode-sideBar-foreground);background:var(--vscode-sideBar-background);font:13px/1.5 var(--vscode-font-family)}main{position:relative}header{display:flex;gap:12px;align-items:center;margin-bottom:20px}h1{font-size:20px;margin:0}header p{margin:0;color:var(--vscode-descriptionForeground)}.close{position:absolute;right:0;top:0;background:transparent!important;color:var(--vscode-foreground)!important}.severity{border-left:4px solid;padding:10px;background:var(--vscode-editorWidget-background)}.severity.moderate{border-color:var(--vscode-notificationsWarningIcon-foreground)}.severity.high,.severity.critical{border-color:var(--vscode-notificationsErrorIcon-foreground)}.severity p{margin:2px 0}.value{font-size:34px;font-weight:700;margin-top:18px}.recommendation{border-top:1px solid var(--vscode-widget-border);padding-top:14px}footer{display:flex;gap:8px;margin-top:18px}button{padding:7px 10px;border:0;color:var(--vscode-button-foreground);background:var(--vscode-button-background)}button:focus-visible,a:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}.credit{font-size:11px;color:var(--vscode-descriptionForeground);margin-top:18px}.credit a{color:inherit}</style></head><body>${content}<script nonce="warning">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-command]').forEach((button)=>button.addEventListener('click',()=>vscode.postMessage({command:button.dataset.command})));</script></body></html>`;
}

function severityIcon(urgency: UsageSuggestion["urgency"]): string { return urgency === "moderate" ? "&#9888;" : urgency === "high" ? "&#9650;" : "&#9940;"; }
function capitalize(value: string): string { return value.charAt(0).toUpperCase() + value.slice(1); }
