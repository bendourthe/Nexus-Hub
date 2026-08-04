import * as vscode from "vscode";
import {
  escapeHtml,
  formatMoney,
  formatQuantity
} from "./formatters";
import {
  METER_FILL_COLOR,
  type IncludedUsageMeter,
  type UsageSnapshot,
  type UsageState
} from "./types";
import { renderWebviewDocument } from "./webview";

export class DashboardPanel {
  private panel: vscode.WebviewPanel | undefined;

  public show(state: UsageState): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel(
        "cursorUsageDashboard",
        "Cursor Usage",
        vscode.ViewColumn.One,
        { enableScripts: true, retainContextWhenHidden: true }
      );
      this.panel.onDidDispose(() => {
        this.panel = undefined;
      });
      this.panel.webview.onDidReceiveMessage(
        (message: { command?: string }) => {
          if (isDashboardCommand(message.command)) {
            void vscode.commands.executeCommand(
              `cursor-usage.${message.command}`
            );
          }
        }
      );
    }
    this.panel.webview.html = renderDashboard(state);
    this.panel.reveal();
  }

  public update(state: UsageState): void {
    if (this.panel !== undefined) {
      this.panel.webview.html = renderDashboard(state);
    }
  }

  public dispose(): void {
    this.panel?.dispose();
    this.panel = undefined;
  }
}

export function renderDashboard(
  state: UsageState,
  now = Date.now(),
  nonce?: string
): string {
  const body =
    state.state === "empty"
      ? renderEmpty(state.error.message)
      : renderSnapshot(state, now);
  return renderWebviewDocument({
    body,
    styles: dashboardStyles(),
    script: `const vscode = acquireVsCodeApi();
    document.querySelectorAll('[data-command]').forEach((control) => {
      control.addEventListener('click', () => {
        vscode.postMessage({ command: control.getAttribute('data-command') });
      });
    });`,
    ...(nonce === undefined ? {} : { nonce })
  });
}

function renderEmpty(message: string): string {
  return `<main>
    <h1>Cursor Usage</h1>
    <section class="notice error" role="status">
      <strong>No usage data available.</strong>
      <p>${escapeHtml(message)}</p>
    </section>
    ${actions()}
  </main>`;
}

function renderSnapshot(
  state: Exclude<UsageState, { state: "empty" }>,
  now: number
): string {
  const snapshot = state.data;
  const stale =
    state.state === "stale"
      ? `<section class="notice warning" role="status">
          <strong>Stale usage snapshot.</strong>
          <p>${escapeHtml(state.error.message)} Percentages are not used for alerts until fresh data returns.</p>
        </section>`
      : "";
  return `<main>
    <header>
      <div>
        <p class="eyebrow">Personal included usage</p>
        <h1>Cursor Usage</h1>
        <p>Cursor Models and Other Models remain separate pools.</p>
      </div>
      <div class="freshness">
        <strong>${state.state === "stale" ? "Stale" : "Fresh"}</strong>
        <span>${escapeHtml(formatTimestamp(snapshot.fetchedAt))}</span>
        <span>${escapeHtml(sourceLabel(snapshot))}</span>
      </div>
    </header>
    ${stale}
    <section aria-labelledby="included-heading">
      <h2 id="included-heading">Included Usage</h2>
      <div class="meters">
        ${meterCard("Cursor Models", snapshot.cursorModels, snapshot)}
        ${meterCard("Other Models", snapshot.otherModels, snapshot)}
      </div>
    </section>
    <section class="context-grid" aria-label="Billing context">
      ${onDemandCard(snapshot)}
      ${teamContextCard(snapshot)}
    </section>
    <section class="details" aria-labelledby="period-heading">
      <h2 id="period-heading">Period and freshness</h2>
      <dl>
        <div><dt>Period starts</dt><dd>${escapeHtml(formatOptionalTimestamp(snapshot.period.startsAt))}</dd></div>
        <div><dt>Resets</dt><dd>${escapeHtml(formatReset(snapshot.period.resetsAt, now))}</dd></div>
        <div><dt>Source</dt><dd>${escapeHtml(sourceLabel(snapshot))}</dd></div>
        <div><dt>Updated</dt><dd>${escapeHtml(formatTimestamp(snapshot.fetchedAt))}</dd></div>
      </dl>
    </section>
    ${actions()}
  </main>`;
}

function meterCard(
  label: string,
  meter: IncludedUsageMeter,
  snapshot: UsageSnapshot
): string {
  const used = formatQuantity(meter.used);
  const limit = formatQuantity(meter.limit);
  const reset = formatOptionalTimestamp(snapshot.period.resetsAt);
  if (meter.percentUsed === null) {
    return `<article class="metric">
      <div class="metric-head"><h3>${label}</h3><strong>${escapeHtml(used)}</strong></div>
      <div class="absolute" aria-label="${label} absolute usage; allowance unavailable">
        Allowance unavailable - absolute usage only
      </div>
      <dl>
        <div><dt>Used</dt><dd>${escapeHtml(used)}</dd></div>
        <div><dt>Allowance</dt><dd>Unavailable</dd></div>
        <div><dt>Reset</dt><dd>${escapeHtml(reset)}</dd></div>
      </dl>
    </article>`;
  }

  const rounded = Math.round(meter.percentUsed);
  const fill = Math.round(Math.min(100, Math.max(0, meter.percentUsed)));
  const amountText = [
    `${rounded}%`,
    ...(meter.used === null ? [] : [`${used} used`]),
    ...(meter.limit === null ? [] : [`${limit} allowance`])
  ].join("; ");
  return `<article class="metric">
    <div class="metric-head"><h3>${label}</h3><strong>${rounded}%</strong></div>
    <div class="meter" role="meter" aria-label="${label} included usage" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${fill}" aria-valuetext="${escapeHtml(amountText)}">
      <span class="fill fill-${fill}"></span>
    </div>
    <dl>
      <div><dt>Used</dt><dd>${escapeHtml(used)}</dd></div>
      <div><dt>Allowance</dt><dd>${escapeHtml(limit)}</dd></div>
      <div><dt>Reset</dt><dd>${escapeHtml(reset)}</dd></div>
    </dl>
  </article>`;
}

function onDemandCard(snapshot: UsageSnapshot): string {
  let state = "Unknown";
  if (snapshot.onDemand.enabled === true) {
    state = "Enabled";
  } else if (snapshot.onDemand.enabled === false) {
    state = "Disabled";
  }
  const spend =
    snapshot.onDemand.enabled === true
      ? formatMoney(snapshot.onDemand.personalSpend)
      : "Not applicable";
  return `<article class="context">
    <h2>Personal on-demand</h2>
    <dl>
      <div><dt>State</dt><dd>${state}</dd></div>
      <div><dt>Personal spend</dt><dd>${escapeHtml(spend)}</dd></div>
    </dl>
  </article>`;
}

function teamContextCard(snapshot: UsageSnapshot): string {
  const limit = snapshot.teamContext.sharedSpendLimit;
  let dynamic = "Not reported";
  if (snapshot.teamContext.dynamicSpendLimit === true) {
    dynamic = "Dynamic shared limit";
  } else if (snapshot.teamContext.dynamicSpendLimit === false) {
    dynamic = "Fixed shared limit";
  }
  return `<article class="context">
    <h2>Shared team context</h2>
    <p class="context-note">Shared pool context only - not a personal allowance.</p>
    <dl>
      <div><dt>Shared pool</dt><dd>${escapeHtml(formatMoney(limit))}</dd></div>
      <div><dt>Limit type</dt><dd>${dynamic}</dd></div>
    </dl>
  </article>`;
}

function actions(): string {
  return `<div class="actions" aria-label="Dashboard actions">
    <button data-command="refresh">Refresh now</button>
    <button data-command="manualEntry">Enter usage manually</button>
    <button data-command="settings">Settings</button>
    <button class="secondary" data-command="clearData">Clear data</button>
  </div>`;
}

function dashboardStyles(): string {
  const fillClasses = Array.from(
    { length: 101 },
    (_, value) => `.fill-${value}{width:${value}%}`
  ).join("");
  return `:root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);font:13px/1.5 var(--vscode-font-family)}main{max-width:960px;margin:0 auto;padding:28px}header{display:grid;grid-template-columns:2fr 1fr;gap:24px;align-items:end;border-bottom:1px solid var(--vscode-widget-border);padding-bottom:20px}.eyebrow{text-transform:uppercase;letter-spacing:.08em;color:var(--vscode-descriptionForeground)}h1{font-size:30px;margin:4px 0}h2{font-size:19px;margin-top:28px}.freshness{display:flex;flex-direction:column;text-align:right}.meters,.context-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.metric,.context,.details{border-left:3px solid ${METER_FILL_COLOR};padding:16px;background:var(--vscode-editorWidget-background)}.metric-head{display:flex;justify-content:space-between;gap:16px;align-items:baseline}.metric h3{margin:0}.meter{height:10px;background:var(--vscode-progressBar-background);border:1px solid var(--vscode-contrastBorder,transparent);border-radius:5px;overflow:hidden;margin:14px 0}.fill{display:block;height:100%;background:${METER_FILL_COLOR}}.absolute{border:1px dashed var(--vscode-widget-border);padding:10px;margin:14px 0;font-weight:600}.context-grid{margin-top:18px}.context h2{margin-top:0}.context-note{color:var(--vscode-descriptionForeground)}dl{margin:0}dl div{display:grid;grid-template-columns:112px 1fr;gap:8px}dt{color:var(--vscode-descriptionForeground)}dd{margin:0}.details{margin-top:18px}.details h2{margin-top:0}.notice{padding:12px 14px;margin:18px 0;border-left:4px solid}.notice.warning{border-color:var(--vscode-notificationsWarningIcon-foreground)}.notice.error{border-color:var(--vscode-notificationsErrorIcon-foreground)}.notice p{margin:4px 0 0}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:28px}button{border:1px solid transparent;padding:7px 12px;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit}button:hover{background:var(--vscode-button-hoverBackground)}button:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}${fillClasses}@media(max-width:600px){main{padding:18px}header{grid-template-columns:1fr}.freshness{text-align:left}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}@media(forced-colors:active){.meter{forced-color-adjust:none;border-color:CanvasText;background:Canvas}.fill{background:Highlight}.metric,.context,.details{border-color:CanvasText}button{border-color:ButtonText}}`;
}

function formatReset(value: string | null, now: number): string {
  if (value === null) {
    return "Not reported";
  }
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    return "Not reported";
  }
  const minutes = Math.max(0, Math.ceil((parsed - now) / 60_000));
  return `${formatTimestamp(value)} (${minutes} min remaining)`;
}

function formatOptionalTimestamp(value: string | null): string {
  return value === null ? "Not reported" : formatTimestamp(value);
}

function formatTimestamp(value: string): string {
  const parsed = Date.parse(value);
  return Number.isFinite(parsed)
    ? new Date(parsed).toLocaleString("en-US")
    : "Not reported";
}

function sourceLabel(snapshot: UsageSnapshot): string {
  return snapshot.source === "cache"
    ? `cache (from ${snapshot.cachedFrom})`
    : snapshot.source;
}

function isDashboardCommand(
  value: string | undefined
): value is "refresh" | "manualEntry" | "settings" | "clearData" {
  return (
    value === "refresh" ||
    value === "manualEntry" ||
    value === "settings" ||
    value === "clearData"
  );
}
