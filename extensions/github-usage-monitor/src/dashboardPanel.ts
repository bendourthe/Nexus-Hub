import * as vscode from "vscode";
import type { UsageMetric, UsageState } from "./types";
import { escapeHtml, formatAmount, GITHUB_BAR_FILL } from "./statusBarManager";
import { formatResetCountdown } from "./usageStore";

export class DashboardPanel {
  private panel: vscode.WebviewPanel | undefined;
  public show(state: UsageState): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel("githubUsageDashboard", "GitHub Billing Usage", vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
      this.panel.onDidDispose(() => { this.panel = undefined; });
      this.panel.webview.onDidReceiveMessage((message: { command?: string }) => {
        if (message.command) void vscode.commands.executeCommand(`github-usage.${message.command}`);
      });
    }
    this.panel.webview.html = renderDashboard(state);
    this.panel.reveal();
  }
}

export function renderDashboard(state: UsageState, now = Date.now()): string {
  const nonce = "githubUsageDashboard";
  const body = state.data === undefined
    ? `<main><h1>GitHub Billing Usage</h1><p class="eyebrow">Actions minutes and storage, plus Copilot billing, for one billing owner you configure</p><section class="notice error" role="status"><strong>No billing data available.</strong><p>${escapeHtml(state.error?.message ?? "Set a token and refresh.")}</p></section>${actions()}</main>`
    : renderSnapshot(state, now);
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';"><style>${styles()}</style></head><body>${body}<script nonce="${nonce}">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-command]').forEach((button)=>button.addEventListener('click',()=>vscode.postMessage({command:button.dataset.command})));</script></body></html>`;
}

function renderSnapshot(state: UsageState, now: number): string {
  const snapshot = state.data!;
  const warning = state.state === "stale" || state.error
    ? `<section class="notice warning" role="status"><strong>Last-known-good data.</strong><p>${escapeHtml(state.error?.message ?? "This snapshot is stale.")}</p></section>` : "";
  return `<main><header><div><p class="eyebrow">Actions minutes and storage, plus Copilot billing, for one billing owner</p><h1>GitHub Billing Usage</h1><p>Billing owner: ${escapeHtml(snapshot.owner.name)} - ${snapshot.owner.scope} scope</p></div><div class="freshness"><strong>${snapshot.stale ? "Stale" : "Fresh"}</strong><span>${escapeHtml(new Date(snapshot.fetchedAt).toLocaleString())}</span></div></header>${warning}<nav aria-label="Usage sections"><a href="#copilot">Copilot</a><a href="#actions">Actions</a><a href="#details">Billing detail</a></nav><section id="copilot"><h2>Copilot</h2>${metricCard(snapshot.copilot, now)}</section><section id="actions"><h2>Actions</h2><div class="metrics">${metricCard(snapshot.actionsMinutes, now)}${metricCard(snapshot.actionsStorage, now)}</div></section><section id="details"><h2>Billing detail</h2>${breakdowns(snapshot.copilot)}${breakdowns(snapshot.actionsMinutes)}${breakdowns(snapshot.actionsStorage)}</section>${actions()}</main>`;
}

function metricCard(metric: UsageMetric, now: number): string {
  const pct = metric.percentage === null ? null : Math.max(0, metric.percentage);
  const limit = metric.allowance === null ? "Allowance unknown - absolute usage only" : `${metric.allowance} ${escapeHtml(metric.unit)} (${metric.allowanceSource})`;
  const reset = metric.reset === null ? "Not reported" : `${formatResetCountdown(metric.reset.at, now)} - ${escapeHtml(metric.reset.label)}`;
  return `<article class="metric"><div class="metric-head"><h3>${label(metric)}</h3><strong>${pct === null ? formatAmount(metric) : `${Math.round(pct)}%`}</strong></div>${pct === null ? `<div class="absolute" aria-label="Absolute usage; allowance unknown">${formatAmount(metric)}</div>` : `<div class="meter" role="meter" aria-label="${label(metric)} usage" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(pct)}"><span style="width:${Math.min(100, pct)}%"></span></div>`}<dl><div><dt>Used</dt><dd>${formatAmount(metric)}</dd></div><div><dt>Allowance</dt><dd>${limit}</dd></div><div><dt>Net cost</dt><dd>${metric.netAmount === null ? "Not reported" : `$${metric.netAmount.toFixed(2)}`}</dd></div><div><dt>Reset</dt><dd>${reset}</dd></div></dl></article>`;
}

function breakdowns(metric: UsageMetric): string {
  if (metric.breakdowns.length === 0) return "";
  const rows = metric.breakdowns.map((row) => `<tr><td>${escapeHtml(row.product)}</td><td>${escapeHtml(row.sku)}</td><td>${row.grossQuantity} ${escapeHtml(row.unit)}</td><td>${row.discountQuantity ?? "-"}</td><td>${row.netAmount === null ? "-" : `$${row.netAmount.toFixed(2)}`}</td></tr>`).join("");
  return `<h3>${label(metric)}</h3><div class="table-scroll"><table><thead><tr><th>Product</th><th>SKU</th><th>Gross usage</th><th>Discount</th><th>Net cost</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function actions(): string { return `<div class="actions"><button data-command="openBillingPage">Open GitHub billing page</button><button data-command="logIn">Connect / switch account</button><button data-command="refresh">Refresh now</button><button data-command="manualEntry">Enter allowances</button><button data-command="settings">Settings</button><button class="secondary" data-command="clearData">Clear data</button></div>`; }
function label(metric: UsageMetric): string { return ({"copilot-ai-credits":"Copilot AI credits","copilot-premium-requests":"Copilot premium requests","actions-minutes":"Actions minutes","actions-storage":"Actions storage"} as const)[metric.kind]; }
function styles(): string { return `:root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);font:13px/1.5 var(--vscode-font-family)}main{max-width:1040px;margin:0 auto;padding:28px}header{display:grid;grid-template-columns:2fr 1fr;gap:24px;align-items:end;border-bottom:1px solid var(--vscode-widget-border);padding-bottom:20px}.eyebrow{text-transform:uppercase;letter-spacing:.08em;color:var(--vscode-descriptionForeground)}h1{font-size:32px;margin:4px 0}h2{font-size:20px;margin-top:32px}.freshness{display:flex;flex-direction:column;text-align:right}nav{display:flex;gap:18px;padding:14px 0}a{color:var(--vscode-textLink-foreground)}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.metric{border-left:3px solid ${GITHUB_BAR_FILL};padding:14px 16px;background:var(--vscode-editorWidget-background)}.metric-head{display:flex;justify-content:space-between;gap:16px;align-items:baseline}.metric h3{margin:0}.meter{height:8px;background:color-mix(in srgb,${GITHUB_BAR_FILL} 20%,transparent);border-radius:4px;overflow:hidden;margin:14px 0}.meter span{display:block;height:100%;background:${GITHUB_BAR_FILL}}.absolute{border:1px dashed var(--vscode-widget-border);padding:10px;margin:14px 0;font-weight:600}dl{margin:0}dl div{display:grid;grid-template-columns:92px 1fr;gap:8px}dt{color:var(--vscode-descriptionForeground)}dd{margin:0}.notice{padding:12px 14px;margin:18px 0;border-left:4px solid}.notice.warning{border-color:var(--vscode-notificationsWarningIcon-foreground)}.notice.error{border-color:var(--vscode-notificationsErrorIcon-foreground)}.notice p{margin:4px 0 0}.table-scroll{overflow:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--vscode-widget-border)}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:28px}button{border:1px solid transparent;padding:7px 12px;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit}button:hover,button:focus-visible{background:var(--vscode-button-hoverBackground);outline:2px solid var(--vscode-focusBorder);outline-offset:2px}button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}@media(max-width:600px){main{padding:18px}header{grid-template-columns:1fr}.freshness{text-align:left}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}`; }
