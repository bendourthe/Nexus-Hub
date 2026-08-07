import * as vscode from "vscode";
import {
  escapeHtml,
  formatMoney,
  formatPercent,
  formatQuantity,
  formatSharedSpendNote,
  formatSpendAgainstLimit,
  spendFractionOfLimit
} from "./formatters";
import {
  METER_FILL_COLOR,
  type IncludedUsageMeter,
  type UsageSnapshot,
  type UsageState
} from "./types";
import { CONSENT_PROMPT_WILL_NOT_READ } from "./providers/consent";
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
  // This is a first-run screen, not an error screen. It used to lead with "Enter
  // usage manually", which asks the user to BE the data source and reads as a
  // broken extension.
  //
  // Automatic tracking WORKS as of Phase 6 (the verified RPC), so this screen's job
  // is to get consent, not to explain an absence. Connecting is the primary action.
  //
  // Manual entry survives as a genuine choice for someone who declines, but its
  // weakness is stated rather than hidden: a pasted figure is frozen at the moment
  // it was entered. An earlier draft of this screen led with manual entry and did
  // not say that, which made a stale number look like a live meter.
  return `<main>
    <h1>Cursor Usage</h1>
    <p class="eyebrow">Not connected yet</p>
    <section class="notice warning" role="status">
      <strong>Live tracking is available, and off until you allow it.</strong>
      <p>Your real usage can be read automatically. Doing so needs your permission once, because it uses the same session Cursor itself signed you in with, read from Cursor's own local state. Nothing is read before you agree.</p>
    </section>
    <section class="onboarding">
      <h2>Turn it on in one step</h2>
      <ol>
        <li><strong>Click "Connect live tracking".</strong> You will see one prompt stating exactly what is read and what is never read. Allow it, and your real figures appear here and in the status bar, refreshing on their own.</li>
      </ol>
      <p class="context-note">Prefer not to? You can open your usage page and type the figures in by hand instead. Be aware of what that gives you: a snapshot frozen at the moment you enter it, which does not follow your usage and will quietly go out of date.</p>
      <p class="context-note">Whichever you choose, this is what is never read:</p>
      <ul class="context-note">${CONSENT_PROMPT_WILL_NOT_READ.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>
    </section>
    <div class="actions" aria-label="Setup actions">
      <button data-command="connectLive">Connect live tracking</button>
      <button class="secondary" data-command="openUsagePage">Open my Cursor usage page</button>
      <button class="secondary" data-command="manualEntry">Enter figures by hand</button>
      <button class="secondary" data-command="settings">Settings</button>
    </div>
    <details class="diagnostic-detail">
      <summary>Technical detail</summary>
      <p>${escapeHtml(message)}</p>
    </details>
  </main>`;
}

function renderSnapshot(
  state: Exclude<UsageState, { state: "empty" }>,
  now: number
): string {
  const snapshot = state.data;
  const stale =
    state.state === "stale"
      ? `<div class="banner warning" role="status"><span aria-hidden="true">&#9888;</span><div><strong>Stale usage snapshot.</strong> ${escapeHtml(state.error.message)} Percentages are not used for alerts until fresh data returns.</div></div>`
      : "";
  return `<main>
    <h2>Cursor Usage Dashboard</h2>
    ${stale}
    ${poolSection("Cursor Models", snapshot.cursorModels, snapshot, now)}
    ${poolSection("Other Models", snapshot.otherModels, snapshot, now)}
    <div class="divider"></div>
    ${extraUsageSection(snapshot, now)}
    <div class="divider"></div>
    <div class="section">
      <h3>Period and freshness</h3>
      <dl>
        <div><dt>Period starts</dt><dd>${escapeHtml(formatOptionalTimestamp(snapshot.period.startsAt))}</dd></div>
        <div><dt>Resets</dt><dd>${escapeHtml(formatReset(snapshot.period.resetsAt, now))}</dd></div>
        <div><dt>Source</dt><dd>${escapeHtml(sourceLabel(snapshot))}</dd></div>
        <div><dt>Freshness</dt><dd>${state.state === "stale" ? "Stale" : "Fresh"}</dd></div>
        <div><dt>Updated</dt><dd>${escapeHtml(formatTimestamp(snapshot.fetchedAt))}</dd></div>
      </dl>
    </div>
    ${actions()}
  </main>`;
}

/**
 * One included-usage pool, in the sibling monitors' vertical grammar: an uppercase
 * section label, a full-width pill bar with the percentage right-aligned, and a
 * sub-line carrying the reset and any absolute figures.
 *
 * The percentage is the payload's own; it is never derived here. See the note on
 * `CURSOR_WIRE_CONTRACT` for why deriving it renders a healthy pool at ~1079%.
 */
function poolSection(
  label: string,
  meter: IncludedUsageMeter,
  snapshot: UsageSnapshot,
  now: number
): string {
  const reset = `Resets ${escapeHtml(formatReset(snapshot.period.resetsAt, now))}`;
  if (meter.percentUsed === null) {
    return `<div class="section">
      <h3>${escapeHtml(label)}</h3>
      <div class="absolute">${escapeHtml(formatQuantity(meter.used))}</div>
      <p class="sub">Allowance unavailable - absolute usage only.<br>${reset}</p>
    </div>`;
  }
  const detail = [
    meter.used === null ? null : `${escapeHtml(formatQuantity(meter.used))} used`,
    meter.limit === null
      ? null
      : `allowance ${escapeHtml(formatQuantity(meter.limit))}`
  ].filter((part): part is string => part !== null);
  return `<div class="section">
    <h3>${escapeHtml(label)}</h3>
    ${bar(meter.percentUsed, formatPercent(meter.percentUsed), `${label} usage`)}
    <p class="sub">${detail.length > 0 ? `${detail.join(" &middot; ")}<br>` : ""}${reset}</p>
  </div>`;
}

/**
 * On-demand spend, and the shared pool it draws from.
 *
 * The bar deliberately tracks the POOL rather than personal spend. Measuring
 * personal spend against the shared limit reads as headroom that may not exist: on
 * a real account, personal spend was 157.32 of a 200.00 limit (a comfortable-looking
 * 79%) while the pool itself was fully drawn with nothing left. Both figures are
 * therefore shown, with the bar on the one that decides whether the next request is
 * billable.
 *
 * The Phase 2 rules are unchanged and load-bearing: never present the shared pool as
 * a personal cap, never divide it into a per-member figure, drop the bar rather than
 * approximate when a fraction would be meaningless (absent limit, non-positive
 * limit, or a limit in a different currency than the spend), take the reset date
 * from the payload, and clamp an over-limit bar while saying so.
 */
function extraUsageSection(snapshot: UsageSnapshot, now: number): string {
  const team = snapshot.teamContext;
  const limit = team.sharedSpendLimit ?? null;
  const pooledUsed = team.sharedSpendUsed ?? null;
  const remaining = team.sharedSpendRemaining ?? null;
  const personal = snapshot.onDemand.personalSpend ?? null;
  const reset = `Resets ${escapeHtml(formatReset(snapshot.period.resetsAt, now))}`;
  const sharing =
    "This limit is shared across your team, not a personal allowance.";

  if (!snapshot.onDemand.enabled) {
    return `<div class="section">
      <h3>Personal on-demand</h3>
      <div class="absolute">Not applicable</div>
      <p class="sub">On-demand spending is off for this account.<br>${reset}</p>
    </div>`;
  }

  const yours = personal === null ? "Not reported" : formatMoney(personal);
  // A fraction across two currencies is meaningless, so it is dropped rather than
  // computed. `spendFractionOfLimit` already encodes that rule for the personal
  // reading; the same currency guard applies to the pooled reading.
  const currencyMismatch =
    limit !== null && personal !== null && limit.currency !== personal.currency;
  const pooledComparable =
    limit !== null &&
    limit.amount > 0 &&
    pooledUsed !== null &&
    pooledUsed.currency === limit.currency;

  if (limit === null || limit.amount <= 0 || currencyMismatch) {
    const why = currencyMismatch
      ? "The shared limit is reported in a different currency than your spend, so no percentage is shown."
      : "Shared limit not reported, so no percentage is shown.";
    return `<div class="section">
      <h3>Personal on-demand</h3>
      <div class="absolute">${escapeHtml(yours)}</div>
      <p class="sub">Shared spend limit unavailable - spend only.<br>${why}<br>${sharing}<br>${reset}</p>
    </div>`;
  }

  const personalFraction = spendFractionOfLimit(personal, limit);
  const percent = pooledComparable
    ? (pooledUsed.amount / limit.amount) * 100
    : (personalFraction ?? 0);
  const left =
    remaining === null
      ? ""
      : remaining.amount <= 0
        ? "<br><strong>The shared pool is fully spent - nothing left.</strong>"
        : `<br>${escapeHtml(formatMoney(remaining))} left in the shared pool.`;
  const pooledLine = pooledComparable
    ? `<br>Team has drawn ${escapeHtml(formatMoney(pooledUsed))} of ${escapeHtml(formatMoney(limit))}.`
    : "";
  const over =
    percent > 100
      ? "<br>Over the shared limit; the pool has been drawn past it and the bar is shown full."
      : "";
  const personalPercent =
    personalFraction === null
      ? ""
      : `${formatPercent(personalFraction)} of the limit shared across your team`;
  const overLimit =
    personalFraction !== null && personalFraction > 100
      ? "<br>Over the shared limit; the bar is shown full."
      : "";

  return `<div class="section">
    <h3>Personal on-demand</h3>
    ${bar(percent, `${escapeHtml(formatSpendAgainstLimit(personal, limit))}`, "On-demand spend against the shared team limit")}
    <p class="sub">Your spend ${escapeHtml(yours)}${personalPercent === "" ? "" : ` &middot; ${personalPercent}`}.${pooledLine}${left}<br>Shared limit ${escapeHtml(formatMoney(limit))}. ${sharing}<br>${reset}${over}${overLimit}</p>
  </div>
  <div class="section">
    <h3>Shared team context</h3>
    <p class="sub">${escapeHtml(formatSharedSpendNote(snapshot.period.resetsAt))}</p>
  </div>`;
}

/** A pill-shaped track and fill, clamped so an over-limit pool cannot overflow. */
function bar(percent: number, right: string, ariaLabel: string): string {
  const clamped = Math.round(Math.min(100, Math.max(0, percent)));
  return `<div class="bar-row">
    <div class="bar" role="meter" aria-label="${escapeHtml(ariaLabel)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${clamped}">
      <span class="fill fill-${clamped}"></span>
    </div>
    <span class="bar-value">${right}</span>
  </div>`;
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

  const percentText = formatPercent(meter.percentUsed);
  // The width class stays an integer so a nearly-empty pool still shows a visible
  // sliver, which is what keeps 1.7% and 100% distinguishable at a glance.
  const fill = Math.round(Math.min(100, Math.max(0, meter.percentUsed)));
  const amountText = [
    percentText,
    ...(meter.used === null ? [] : [`${used} used`]),
    ...(meter.limit === null ? [] : [`${limit} allowance`])
  ].join("; ");
  return `<article class="metric">
    <div class="metric-head"><h3>${label}</h3><strong>${percentText}</strong></div>
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
  if (snapshot.onDemand.enabled !== true) {
    return `<article class="context">
      <h2>Personal on-demand</h2>
      <dl>
        <div><dt>State</dt><dd>${state}</dd></div>
        <div><dt>Personal spend</dt><dd>Not applicable</dd></div>
      </dl>
    </article>`;
  }

  const spend = snapshot.onDemand.personalSpend;
  const limit = snapshot.teamContext.sharedSpendLimit;
  // On-demand is currency against a spend limit, so the headline stays in currency
  // and the percentage is only ever the bar's geometry.
  const amountText = formatSpendAgainstLimit(spend, limit);
  const fraction = spendFractionOfLimit(spend, limit);
  return `<article class="context">
    <h2>Personal on-demand</h2>
    <div class="metric-head"><h3>Spend</h3><strong>${escapeHtml(amountText)}</strong></div>
    ${onDemandBar(fraction, amountText)}
    <p class="context-note">${escapeHtml(formatSharedSpendNote(snapshot.period.resetsAt))}</p>
    <dl>
      <div><dt>State</dt><dd>${state}</dd></div>
      <div><dt>Personal spend</dt><dd>${escapeHtml(formatMoney(spend))}</dd></div>
      <div><dt>Shared limit</dt><dd>${escapeHtml(formatMoney(limit))}</dd></div>
    </dl>
  </article>`;
}

function onDemandBar(fraction: number | null, amountText: string): string {
  if (fraction === null) {
    return `<div class="absolute" aria-label="On-demand spend; shared limit unavailable">
      Shared spend limit unavailable - spend only
    </div>`;
  }
  const fill = Math.round(Math.min(100, Math.max(0, fraction)));
  const overLimit = fraction > 100 ? " Over the shared limit." : "";
  const valueText = `${amountText}; ${formatPercent(fraction)} of the limit shared across your team.${overLimit}`;
  return `<div class="meter" role="meter" aria-label="On-demand spend against the shared team limit" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${fill}" aria-valuetext="${escapeHtml(valueText)}">
    <span class="fill fill-${fill}"></span>
  </div>`;
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
    <button data-command="openUsagePage">Open my Cursor usage page</button>
    <button data-command="refresh">Refresh now</button>
    <button data-command="manualEntry">Update figures</button>
    <button data-command="settings">Settings</button>
    <button class="secondary" data-command="clearData">Clear data</button>
  </div>`;
}

function dashboardStyles(): string {
  // Width classes rather than inline widths: the panel runs under a strict CSP with
  // no inline style attributes, so the fill width has to come from a class.
  const fillClasses = Array.from(
    { length: 101 },
    (_, value) => `.fill-${value}{width:${value}%}`
  ).join("");
  return `:root{color-scheme:light dark}
*{box-sizing:border-box}
body{margin:0;background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);font:13px/1.5 var(--vscode-font-family)}
main{max-width:520px;margin:0 auto;padding:20px}
h2{font-size:16px;margin:0 0 16px}
h3{font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.5px;opacity:.8}
.section{margin-bottom:16px}
.divider{border-top:1px solid var(--vscode-widget-border,rgba(128,128,128,.35));margin:16px 0}
.bar-row{display:flex;align-items:center;gap:10px}
.bar{flex:1;height:8px;border-radius:4px;background:color-mix(in srgb,${METER_FILL_COLOR} 22%,transparent);overflow:hidden;border:1px solid var(--vscode-contrastBorder,transparent)}
.fill{display:block;height:100%;border-radius:4px;background:${METER_FILL_COLOR}}
.bar-value{flex-shrink:0;font-variant-numeric:tabular-nums;opacity:.85}
.absolute{font-weight:600;font-size:15px}
.sub{margin:6px 0 0;opacity:.75;font-size:12px}
.banner{display:flex;gap:8px;align-items:flex-start;padding:8px 12px;margin-bottom:16px;border-radius:4px;font-size:12px;line-height:1.4}
.banner.warning{background:var(--vscode-inputValidation-warningBackground,rgba(255,204,0,.1));border:1px solid var(--vscode-inputValidation-warningBorder,#cca700)}
.onboarding{border-left:3px solid ${METER_FILL_COLOR};padding:14px;margin:16px 0;background:var(--vscode-editorWidget-background)}
.onboarding h2{margin-top:0}
.onboarding ol{margin:0;padding-left:20px}
.onboarding li{margin-bottom:8px}
.context-note{opacity:.8;font-size:12px}
.diagnostic-detail{margin-top:16px;opacity:.75;font-size:12px}
.diagnostic-detail summary{cursor:pointer}
.eyebrow{text-transform:uppercase;letter-spacing:.08em;opacity:.6;font-size:11px;margin:0 0 4px}
h1{font-size:22px;margin:0 0 12px}
dl{margin:0}
dl div{display:grid;grid-template-columns:110px 1fr;gap:8px}
dt{opacity:.7}
dd{margin:0}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
button{border:1px solid transparent;padding:6px 12px;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit;border-radius:2px}
button:hover{background:var(--vscode-button-hoverBackground)}
button:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}
button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}
${fillClasses}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
@media(forced-colors:active){.bar{forced-color-adjust:none;border-color:CanvasText;background:Canvas}.fill{background:Highlight}button{border-color:ButtonText}}`;
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
):
  value is
    | "refresh"
    | "manualEntry"
    | "settings"
    | "clearData"
    | "openUsagePage"
    | "connectLive" {
  return (
    value === "refresh" ||
    value === "manualEntry" ||
    value === "settings" ||
    value === "clearData" ||
    value === "openUsagePage" ||
    value === "connectLive"
  );
}

/** Exposes the panel's command guard so a test can prove no button is inert. */
export function isDashboardCommandForTest(value: string | undefined): boolean {
  return isDashboardCommand(value);
}
