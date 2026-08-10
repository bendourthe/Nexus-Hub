import * as vscode from "vscode";
import type { UsageMetric, UsageState } from "./types";
import { escapeHtml, formatAmount, isNotConnected, GITHUB_BAR_FILL } from "./statusBarManager";
import { formatResetCountdown } from "./usageStore";
import { explainMissingPercentage } from "./providers/allowances";

export class DashboardPanel {
  private panel: vscode.WebviewPanel | undefined;
  public show(state: UsageState): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel("githubUsageMonitorDashboard", "GitHub Usage Monitor", vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
      this.panel.onDidDispose(() => { this.panel = undefined; });
      this.panel.webview.onDidReceiveMessage((message: { command?: string }) => {
        if (message.command) void vscode.commands.executeCommand(`githubUsageMonitor.${message.command}`);
      });
    }
    this.panel.webview.html = renderDashboard(state);
    this.panel.reveal();
  }
}

export function renderDashboard(state: UsageState, now = Date.now()): string {
  const nonce = "githubUsageMonitorDashboard";
  const body = state.data === undefined
    ? (isNotConnected(state) ? renderNotConnected() : renderNoData(state))
    : renderSnapshot(state, now);
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';"><style>${styles()}</style></head><body>${body}<script nonce="${nonce}">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-command]').forEach((button)=>button.addEventListener('click',()=>vscode.postMessage({command:button.dataset.command})));</script></body></html>`;
}

/**
 * The unconnected state, which is a starting point rather than a failure.
 *
 * Deliberately NOT styled as an error. A user who has not connected, or who chose
 * not to, is in a valid state; presenting it as a failure is inaccurate and is
 * nagging by other means. One sentence on what the monitor does, one primary action,
 * and an explicit statement of what is read and what is not - because the honest
 * answer to "why does this want my GitHub account" belongs where the question is
 * asked, not buried in a README.
 */
function renderNotConnected(): string {
  return `<main><header><div><p class="eyebrow">Not connected</p><h1>GitHub Usage Monitor</h1></div></header>` +
    `<section class="notice" role="status">` +
    `<p>Connect a GitHub account to see your current-month Actions and Copilot usage in the status bar.</p>` +
    `<div class="actions"><button data-command="logIn">Connect GitHub account</button></div>` +
    `<p class="explain"><strong>What it reads:</strong> billing usage for one owner you configure, and whether each repository is public or private. ` +
    `<strong>What it does not read:</strong> your code, your commits, or the contents of any repository. Nothing leaves your machine except the request to GitHub.</p>` +
    `</section></main>`;
}

/** A connected monitor that still has no data - a real failure, styled as one. */
function renderNoData(state: UsageState): string {
  return `<main><h1>GitHub Usage Monitor</h1><p class="eyebrow">Actions minutes and storage, plus Copilot billing, for one billing owner you configure</p><section class="notice error" role="status"><strong>No billing data available.</strong><p>${escapeHtml(state.error?.message ?? "Set a token and refresh.")}</p></section>${actions()}</main>`;
}

function renderSnapshot(state: UsageState, now: number): string {
  const snapshot = state.data!;
  const warning = state.state === "stale" || state.error
    ? `<section class="notice warning" role="status"><strong>Last-known-good data.</strong><p>${escapeHtml(state.error?.message ?? "This snapshot is stale.")}</p></section>` : "";
  return `<main><header><div><p class="eyebrow">Actions minutes and storage, plus Copilot billing, for one billing owner</p><h1>GitHub Usage Monitor</h1><p>Billing owner: ${escapeHtml(snapshot.owner.name)} - ${snapshot.owner.scope} scope</p></div><div class="freshness"><strong>${snapshot.stale ? "Stale" : "Fresh"}</strong><span>${escapeHtml(new Date(snapshot.fetchedAt).toLocaleString())}</span></div></header>${warning}<nav aria-label="Usage sections"><a href="#copilot">Copilot</a><a href="#actions">Actions</a><a href="#details">Billing detail</a></nav><section id="copilot"><h2>Copilot</h2>${metricCard(snapshot.copilot, now)}</section><section id="actions"><h2>Actions</h2><div class="metrics">${metricCard(snapshot.actionsMinutes, now)}${metricCard(snapshot.actionsStorage, now)}</div></section><section id="details"><h2>Billing detail</h2>${breakdowns(snapshot.copilot)}${breakdowns(snapshot.actionsMinutes)}${breakdowns(snapshot.actionsStorage)}</section>${actions()}</main>`;
}

/**
 * One metric card, rendered per allowance state.
 *
 * Three states, three distinct treatments, and no blanks:
 *
 *   - `verified`   teal meter plus the percentage.
 *   - `none`       bordered absolute treatment plus a line stating that the plan
 *                  includes no allowance for this product, so the figure IS the
 *                  total rather than a share of a limit.
 *   - `unknown`    bordered absolute treatment plus a line naming what would make a
 *                  percentage available.
 *
 * Neither `none` nor `unknown` may render `0%` or `100%` for a null allowance. That
 * is the data contract's line 71 and the visual contract's line 39, and it is the
 * rule that rejected the original "treat unknown as zero and fill the bar" proposal.
 *
 * A verified percentage is derived from `drawdown`, never from `used`. `used` is
 * gross consumption including free public-repository usage; on the account this was
 * measured against it was 1,287 minutes where the drawdown was about 121.
 */
function metricCard(metric: UsageMetric, now: number): string {
  const pct = metric.percentage === null ? null : Math.max(0, metric.percentage);
  // Provenance is shown beside the value, never just the value. "2,000 min" alone
  // invites the reading that GitHub said so; naming where it came from does not, and
  // it is what makes the override worth reaching for when the figure is wrong for an
  // account (data packs, Education benefits, and negotiated terms are invisible to
  // the API, so a published per-plan figure cannot detect its own disagreement).
  const provenance =
    metric.allowanceSource === "manual"
      ? "set by you"
      : metric.allowanceSource === "plan-table"
        ? "published figure for your plan, not read from your account"
        : String(metric.allowanceSource);
  const limit =
    metric.allowanceState === "none"
      ? "None included with your plan"
      : metric.allowance === null
        ? "Not established"
        : `${metric.allowance} ${escapeHtml(metric.unit)} <span class="explain">(${escapeHtml(provenance)})</span>`;
  const reset = metric.reset === null ? "Not reported" : `${formatResetCountdown(metric.reset.at, now)} - ${escapeHtml(metric.reset.label)}`;
  // `typeof`, not `!== null`: a snapshot cached by an older version carries no
  // `drawdown` field at all, and `undefined` would render as NaN. Cached snapshots
  // outlive the upgrade that adds a field, so every new field must tolerate absence.
  const counted =
    typeof metric.drawdown !== "number" || !Number.isFinite(metric.drawdown)
      ? ""
      : `<div><dt>Counted</dt><dd>${formatNumber(metric.drawdown)} ${escapeHtml(metric.unit)}${metric.drawdownBasis === "reconstructed" ? " (reconstructed)" : ""}</dd></div>`;
  const body =
    pct === null
      ? `<div class="absolute" aria-label="Absolute usage; no percentage available">${formatAmount(metric)}</div><p class="explain">${escapeHtml(explainMissingPercentage(metric))}</p>`
      : `<div class="meter" role="meter" aria-label="${label(metric)} usage" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(pct)}"><span style="width:${Math.min(100, pct)}%"></span></div>${metric.drawdownBasis === "reconstructed" ? `<p class="explain">Reconstructed from private-repository usage. GitHub does not publish this figure, so it is an estimate rather than its own number.</p>` : ""}`;
  return `<article class="metric"><div class="metric-head"><h3>${label(metric)}</h3><strong>${pct === null ? formatAmount(metric) : `${Math.round(pct)}%`}</strong></div>${body}<dl><div><dt>Used</dt><dd>${formatAmount(metric)}</dd></div>${counted}<div><dt>Allowance</dt><dd>${limit}</dd></div><div><dt>Net cost</dt><dd>${metric.netAmount === null ? "Not reported" : `$${metric.netAmount.toFixed(2)}`}</dd></div><div><dt>Reset</dt><dd>${reset}</dd></div></dl></article>`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function breakdowns(metric: UsageMetric): string {
  if (metric.breakdowns.length === 0) return "";
  const rows = metric.breakdowns.map((row) => `<tr><td>${escapeHtml(row.product)}</td><td>${escapeHtml(row.sku)}</td><td>${row.grossQuantity} ${escapeHtml(row.unit)}</td><td>${row.discountQuantity ?? "-"}</td><td>${row.netAmount === null ? "-" : `$${row.netAmount.toFixed(2)}`}</td></tr>`).join("");
  return `<h3>${label(metric)}</h3><div class="table-scroll"><table><thead><tr><th>Product</th><th>SKU</th><th>Gross usage</th><th>Discount</th><th>Net cost</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

// "Override allowances" rather than "Enter allowances": nothing has to be entered
// for the monitor to work, and labelling it as entry implies a setup step that the
// plan-derived denominator has already done. Phase 4 restructures this row.
function actions(): string { return `<div class="actions"><button data-command="openBillingPage">Open GitHub billing page</button><button data-command="logIn">Connect / switch account</button><button data-command="refresh">Refresh now</button><button data-command="manualEntry">Override allowances</button><button data-command="settings">Settings</button><button class="secondary" data-command="clearData">Clear data</button></div>`; }
function label(metric: UsageMetric): string { return ({"copilot-ai-credits":"Copilot AI credits","copilot-premium-requests":"Copilot premium requests","actions-minutes":"Actions minutes","actions-storage":"Actions storage"} as const)[metric.kind]; }
function styles(): string { return `:root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);font:13px/1.5 var(--vscode-font-family)}main{max-width:1040px;margin:0 auto;padding:28px}header{display:grid;grid-template-columns:2fr 1fr;gap:24px;align-items:end;border-bottom:1px solid var(--vscode-widget-border);padding-bottom:20px}.eyebrow{text-transform:uppercase;letter-spacing:.08em;color:var(--vscode-descriptionForeground)}h1{font-size:32px;margin:4px 0}h2{font-size:20px;margin-top:32px}.freshness{display:flex;flex-direction:column;text-align:right}nav{display:flex;gap:18px;padding:14px 0}a{color:var(--vscode-textLink-foreground)}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.metric{border-left:3px solid ${GITHUB_BAR_FILL};padding:14px 16px;background:var(--vscode-editorWidget-background)}.metric-head{display:flex;justify-content:space-between;gap:16px;align-items:baseline}.metric h3{margin:0}.meter{height:8px;background:color-mix(in srgb,${GITHUB_BAR_FILL} 20%,transparent);border-radius:4px;overflow:hidden;margin:14px 0}.meter span{display:block;height:100%;background:${GITHUB_BAR_FILL}}.absolute{border:1px dashed var(--vscode-widget-border);padding:10px;margin:14px 0;font-weight:600}.explain{color:var(--vscode-descriptionForeground);margin:6px 0 0;font-size:12px}dl{margin:0}dl div{display:grid;grid-template-columns:92px 1fr;gap:8px}dt{color:var(--vscode-descriptionForeground)}dd{margin:0}.notice{padding:12px 14px;margin:18px 0;border-left:4px solid}.notice.warning{border-color:var(--vscode-notificationsWarningIcon-foreground)}.notice.error{border-color:var(--vscode-notificationsErrorIcon-foreground)}.notice p{margin:4px 0 0}.table-scroll{overflow:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--vscode-widget-border)}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:28px}button{border:1px solid transparent;padding:7px 12px;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit}button:hover,button:focus-visible{background:var(--vscode-button-hoverBackground);outline:2px solid var(--vscode-focusBorder);outline-offset:2px}button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}@media(max-width:600px){main{padding:18px}header{grid-template-columns:1fr}.freshness{text-align:left}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}`; }
