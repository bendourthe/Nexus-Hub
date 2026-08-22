import * as vscode from "vscode";
import type { ActionsDrawdownDetail, BillingOwner, UsageMetric, UsageState } from "./types";
import { displayUnit, escapeHtml, formatAmount, isNotConnected, GITHUB_BAR_FILL } from "./statusBarManager";
import { formatResetCountdown, formatResetDateTime } from "./usageStore";
import { explainMissingPercentage, isAllowanceExhausted } from "./providers/allowances";
import { describeDrawdownProvenance } from "./providers/enrich";
import {
  readSettings,
  settingsScriptJs,
  settingsSectionHtml,
  settingsStylesCss,
  type AuthDisplay
} from "./settingsPanel";

/** A settings write requested by the panel. Validated by the receiver, never trusted. */
export type SettingUpdateHandler = (key: unknown, value: unknown) => void;

export class DashboardPanel {
  private panel: vscode.WebviewPanel | undefined;

  /**
   * `onSettingUpdate` is a callback rather than a registered command deliberately.
   * A command would have to be declared in `package.json` to satisfy the
   * declared-equals-registered parity check, which would put an argument-taking
   * internal write in the Command Palette where invoking it does nothing useful.
   */
  public constructor(private readonly onSettingUpdate?: SettingUpdateHandler) {}

  /**
   * Renders the single panel. There is no second webview: v3.16.3 Phase 4 folded
   * the settings form into this document, so `retainContextWhenHidden` also
   * preserves the settings section's open/closed state across a hide.
   */
  /**
   * Re-renders the panel ONLY if it is already open.
   *
   * `show()` reveals the panel, which is wrong for a background refresh - a timer
   * firing must not throw an editor tab in the user's face. Without this, the panel
   * kept whatever HTML it was last given: on an account switch the status bar cleared
   * its warning while the panel went on displaying the previous account's error.
   */
  public update(state: UsageState, auth?: AuthDisplay): void {
    if (this.panel === undefined) return;
    this.panel.webview.html = renderDashboard(state, undefined, auth);
  }

  public show(state: UsageState, auth?: AuthDisplay): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel("githubUsageMonitorDashboard", "GitHub Usage Monitor", vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
      this.panel.onDidDispose(() => { this.panel = undefined; });
      this.panel.webview.onDidReceiveMessage((message: { command?: string; key?: unknown; value?: unknown }) => {
        if (message.command === "updateSetting") {
          this.onSettingUpdate?.(message.key, message.value);
          return;
        }
        if (message.command) void vscode.commands.executeCommand(`githubUsageMonitor.${message.command}`);
      });
    }
    this.panel.webview.html = renderDashboard(state, undefined, auth);
    this.panel.reveal();
  }
}

export function renderDashboard(state: UsageState, now = Date.now(), auth?: AuthDisplay): string {
  const nonce = "githubUsageMonitorDashboard";
  const body = state.data === undefined
    ? (isNotConnected(state) ? renderNotConnected() : renderNoData(state, auth))
    : renderSnapshot(state, now, auth);
  // The settings section renders even on the unconnected and no-data states, so the
  // gear is never a control that does nothing. Its script runs under the SAME nonce
  // as the dashboard's, rather than adding a second inline block, which is what
  // keeps the Content-Security-Policy shape unchanged.
  const settings = settingsSectionHtml(readSettings(), auth);
  // Splice into the placeholder so the section sits INSIDE <main> and inherits its
  // 500px column. Appending after </main> left it spanning the full window width,
  // which is what made the expanded form look nothing like its sibling.
  const withSettings = body.includes("<!--SETTINGS-->")
    ? body.replace("<!--SETTINGS-->", settings)
    : `${body}${settings}`;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';"><style>${styles()}${settingsStylesCss()}</style></head><body>${withSettings}<script nonce="${nonce}">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-command]').forEach((button)=>button.addEventListener('click',()=>vscode.postMessage({command:button.dataset.command})));const gear=document.getElementById('settings-toggle');if(gear)gear.addEventListener('click',()=>toggleSettings());${settingsScriptJs()}</script></body></html>`;
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
function renderNoData(state: UsageState, auth?: AuthDisplay): string {
  // Carries the same account header as the populated panel. A failing state is
  // exactly when the user needs to see which identity was tried and to switch it,
  // and this state previously offered no account control at all.
  return `<main>${accountHeader(auth, null)}<p class="eyebrow">Actions minutes and storage, plus Copilot billing, for one billing owner you configure</p><section class="notice error" role="status"><strong>No billing data available.</strong><p>${escapeHtml(state.error?.message ?? "Set a token and refresh.")}</p></section><!--SETTINGS-->${actions()}</main>`;
}

/**
 * The panel body, laid out like its Claude and Codex siblings.
 *
 * v3.16.3 rendered a marketing-style header, a tagline, an in-page nav, definition
 * lists per metric, and an always-open billing table. That is a document; a usage
 * monitor is a glance. This is the sibling shape: a quiet title, one section per
 * metric with a bar and a one-line subtitle, the action row, and everything else
 * folded away behind a disclosure.
 */
function renderSnapshot(state: UsageState, now: number, auth?: AuthDisplay): string {
  const snapshot = state.data!;
  const warning = state.state === "stale" || state.error
    ? `<div class="notice">&#9888; Showing last-known-good data${state.error ? `: ${escapeHtml(state.error.message)}` : "."}</div>`
    : "";
  const detail = `${breakdowns(snapshot.copilot)}${breakdowns(snapshot.actionsMinutes)}${breakdowns(snapshot.actionsStorage)}`;
  const actionsSplit = actionsBreakdown(snapshot.actionsDrawdownDetail);
  // Collapsed by default: it is reference material, not something to read on every
  // glance, and open-by-default was pushing the meters off the top of the panel.
  const details = detail === "" ? "" : `<details class="detail"><summary>Billing detail</summary>${detail}</details>`;
  return `<main>` +
    accountHeader(auth, snapshot.owner) +
    warning +
    metricCard(snapshot.copilot, now) +
    metricCard(snapshot.actionsMinutes, now) +
    metricCard(snapshot.actionsStorage, now) +
    `<div class="divider"></div>` +
    actionsSplit +
    details +
    // The settings section renders ABOVE the action row, matching the Claude
    // monitor: the gear expands a panel in place and the buttons stay beneath it,
    // rather than the buttons jumping to the top of a long expanded form.
    `<!--SETTINGS-->` +
    actions() +
    // Freshness only. The identity moved to the header on 2026-08-11, and repeating
    // it here said the same thing twice in two different vocabularies.
    `<p class="last-updated">${snapshot.stale ? "Stale" : "Updated"} ${escapeHtml(formatResetCountdown(now + (now - snapshot.fetchedAt), now))} ago</p>` +
    `</main>`;
}

/**
 * The title, with the bound identity beside it.
 *
 * Promoted out of the Settings section 2026-08-11. WHICH account and WHICH billing
 * owner the figures describe is not a setting - it is the caption for every number
 * on the panel, and folding it behind a gear meant the one fact that makes the
 * figures interpretable was the one fact that was hidden. Both are named, because
 * they differ routinely: a personal login reading an organization's billing is the
 * normal case, not the exception.
 */
function accountHeader(auth: AuthDisplay | undefined, owner: BillingOwner | null): string {
  const user = auth?.binding?.accountLabel ?? null;
  const connected = user !== null || owner !== null;
  // Labelled rows rather than a bare name plus a parenthetical. "SupiraMedical
  // (organization)" made the reader work out which of the two identities they were
  // looking at; naming both fields removes the question.
  const rows = connected
    ? `${user === null ? "" : row("User", user)}${owner === null ? "" : row(ownerFieldLabel(owner), owner.name)}`
    : `<div class="acct-line acct-muted">Not connected</div>`;
  // Every account action lives here, and ONLY here. Splitting "who am I" from
  // "change who I am" across a header and a collapsed settings pane meant the answer
  // and the control for the same question sat in two places.
  const controls = connected
    ? `<button class="acct-btn" data-command="logIn">Switch</button>` +
      `<button class="acct-btn" data-command="logOut">Log out</button>`
    : `<button class="acct-btn acct-btn-primary" data-command="logIn">Log in</button>`;
  return `<header class="panel-head">` +
    `<h2>GitHub Usage Monitor</h2>` +
    `<div class="acct" aria-label="Connected account and billing owner">${rows}` +
    `<div class="acct-actions">${controls}</div></div>` +
    `</header>`;
}

/** One labelled identity row. */
function row(label: string, value: string): string {
  return `<div class="acct-line"><span class="acct-key">${escapeHtml(label)}</span> <span class="acct-val">${escapeHtml(value)}</span></div>`;
}

/**
 * What to call the billing owner, in the reader's terms rather than the API's.
 *
 * "Owner" is the REST vocabulary and means nothing to someone looking at a usage
 * panel - and it reads as "the person who owns this", which is exactly the confusion
 * to avoid when the user and the organization are different identities.
 */
export function ownerFieldLabel(owner: BillingOwner): string {
  switch (owner.scope) {
    case "user":
      return "Personal";
    case "organization":
      return "Organization";
    case "enterprise":
      return "Enterprise";
  }
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
  const reset =
    metric.reset === null
      ? ""
      : `<div class="sub">Resets ${escapeHtml(formatResetDateTime(metric.reset.at))}</div>`;
  const unit = displayUnit(metric.unit);

  const counted =
    typeof metric.drawdown === "number" && Number.isFinite(metric.drawdown)
      ? metric.drawdown
      : null;

  // No allowance exists for this product on this plan. Draw a FULL bar, greyed and
  // dimmed, rather than an empty one or no bar at all: an empty bar implies unused
  // headroom that does not exist, and no bar at all makes the card look broken
  // beside its neighbours. The grey and the transparency together say "this is not
  // a measurement against a limit".
  if (metric.allowanceState === "none") {
    return `<section class="section"><h3>${label(metric)}</h3>` +
      `<div class="bar-row"><div class="bar" role="meter" aria-label="${label(metric)}: no allowance included with your plan" aria-valuemin="0" aria-valuemax="100" aria-valuenow="100">` +
      `<div class="bar-fill none" style="width:100%"></div></div>` +
      `<span class="bar-pct none">n/a</span></div>` +
      `<div class="sub">${formatNumber(metric.used)} ${escapeHtml(unit)} used - your plan includes no allowance for this product</div>${reset}</section>`;
  }

  if (pct === null) {
    return `<section class="section"><h3>${label(metric)}</h3>` +
      `<div class="absolute" aria-label="Absolute usage; no percentage available">${formatNumber(metric.used)} ${escapeHtml(unit)}</div>` +
      `<div class="sub">${escapeHtml(explainMissingPercentage(metric))}</div>${reset}</section>`;
  }

  const shown = counted === null ? `${formatNumber(metric.used)} ${escapeHtml(unit)}` : `${formatNumber(counted)} ${escapeHtml(unit)}`;
  const estimate = metric.drawdownBasis === "reconstructed" ? ` <span class="est" title="GitHub does not publish this figure; it is reconstructed from private-repository usage.">est.</span>` : "";
  // Exhaustion renders as a full bar in the critical style with the TRUE percentage
  // beside it. The bar WIDTH is clamped because a 130% width is a layout bug, but
  // the NUMBER is not: the reported symptom was a meter reading 58% while GitHub
  // showed 2,000 of 2,000, and clamping the figure to 100 would tell the same kind
  // of lie in the other direction.
  const exhausted = isAllowanceExhausted(metric);
  const exhaustedNote = exhausted ? " - allowance exhausted" : "";
  return `<section class="section"><h3>${label(metric)}</h3>` +
    `<div class="bar-row">` +
    `<div class="bar" role="meter" aria-label="${label(metric)} usage${exhaustedNote}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.min(100, Math.round(pct))}" aria-valuetext="${Math.round(pct)}%${exhaustedNote}">` +
    `<div class="bar-fill${exhausted ? " exhausted" : ""}" style="width:${Math.min(100, pct)}%"></div></div>` +
    `<span class="bar-pct${exhausted ? " exhausted" : ""}">${Math.round(pct)}%</span></div>` +
    `<div class="sub">${shown} of ${formatNumber(metric.allowance ?? 0)} ${escapeHtml(unit)}${estimate}${exhausted ? " - <strong>exhausted</strong>" : ""}</div>${reset}</section>`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

/**
 * Rows beyond this are aggregated into a single "other" line.
 *
 * An account with a hundred repositories must not get a hundred rows in a sidebar
 * panel. Twelve covers the repositories that plausibly matter on a real account
 * while keeping the section scannable; the tail is summed rather than dropped, so
 * the rows still add up to the total.
 */
const REPOSITORY_ROW_CAP = 12;

/**
 * Where the Actions minutes went, and which of them counted.
 *
 * This is the section that answers "why do 366 public-repository runs cost me
 * nothing". Public rows visibly read as zero rather than being filtered out - a
 * filtered row leaves the same question unanswered, just less visibly.
 *
 * Repository names render unhashed here. They are the user's own data in their own
 * editor, unlike the probe's output, which is written to be pasted into an issue and
 * therefore hashes by default. The two conventions differ on purpose.
 */
function actionsBreakdown(detail: ActionsDrawdownDetail | undefined): string {
  if (detail === undefined || detail.repositories.length === 0) return "";

  const counted = detail.repositories.filter((row) => row.visibility !== "unknown");
  const unresolvedRows = detail.repositories.filter((row) => row.visibility === "unknown");
  const shown = counted.slice(0, REPOSITORY_ROW_CAP);
  const tail = counted.slice(REPOSITORY_ROW_CAP);

  const row = (name: string, visibility: string, raw: number, weighted: number): string =>
    `<tr><td>${escapeHtml(name)}</td>` +
    `<td class="vis ${escapeHtml(visibility)}">${escapeHtml(visibility)}</td>` +
    `<td class="num">${formatNumber(raw)}</td>` +
    `<td class="num${weighted === 0 ? " zero" : ""}">${formatNumber(weighted)}</td></tr>`;

  const tailRow = tail.length === 0
    ? ""
    : row(
      `other (${tail.length} repositories)`,
      "mixed",
      tail.reduce((sum, entry) => sum + entry.rawMinutes, 0),
      tail.reduce((sum, entry) => sum + entry.weightedMinutes, 0)
    );

  const unresolvedBlock = unresolvedRows.length === 0
    ? ""
    : `<p class="sub">Excluded because their visibility could not be read: ` +
      `${unresolvedRows.map((entry) => escapeHtml(entry.repositoryName)).join(", ")}. ` +
      `A private repository is invisible to a token without the <code>repo</code> scope, and those are exactly the ones that draw down.</p>`;

  return `<details class="detail"><summary>Actions minutes by repository</summary>` +
    // Two sentences, not one. The denominator (where the 2,000 comes from) and the
    // numerator (how the counted minutes were reconstructed) are different claims
    // with different reliability, and folding them together is how a provenance line
    // stops being read.
    `<p class="sub">${escapeHtml(detail.allowanceProvenance)}</p>` +
    `<p class="sub">${escapeHtml(describeDrawdownProvenance(detail))}</p>` +
    `<table class="repo-table"><thead><tr><th>Repository</th><th>Visibility</th><th class="num">Minutes</th><th class="num">Counted</th></tr></thead><tbody>` +
    shown.map((entry) => row(entry.repositoryName, entry.visibility, entry.rawMinutes, entry.weightedMinutes)).join("") +
    tailRow +
    `</tbody></table>${unresolvedBlock}</details>`;
}

function breakdowns(metric: UsageMetric): string {
  if (metric.breakdowns.length === 0) return "";
  const rows = metric.breakdowns.map((row) => `<tr><td>${escapeHtml(row.sku)}</td><td>${row.grossQuantity} ${escapeHtml(row.unit)}</td><td>${row.netAmount === null ? "-" : `$${row.netAmount.toFixed(2)}`}</td></tr>`).join("");
  return `<h4>${label(metric)}</h4><div class="table-scroll"><table><thead><tr><th>SKU</th><th>Usage</th><th>Net</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

/**
 * Exactly three controls, in this order: Refresh Now (primary, filled), Open GitHub
 * Billing Page (secondary, no fill), and a gear.
 *
 * The six-button row it replaces was the maintainer's complaint. Nothing was
 * removed, though - every dropped action moved into the settings section the gear
 * expands, and every command stays registered so the Command Palette still reaches
 * it. A shorter row is the goal; less capability is not.
 *
 * `aria-expanded` starts `false` because the section renders hidden; the toggle
 * script keeps it in step, including when a persisted open state is restored.
 */
function actions(): string {
  return `<div class="actions">` +
    `<button data-command="refresh">Refresh Now</button>` +
    `<button class="secondary" data-command="openBillingPage">Open GitHub Billing Page</button>` +
    `<button id="settings-toggle" class="icon-btn" title="Settings" aria-label="Settings" aria-expanded="false">` +
    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">` +
    `<path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.687.706-1.99 1.99l.169.31a1.464 1.464 0 0 1-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.697 1.283.707 2.687 1.99 1.99l.311-.17a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.687-.706 1.99-1.99l-.169-.31a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.697-1.283-.707-2.687-1.99-1.99l-.311.17a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/>` +
    `</svg></button></div>`;
}
function label(metric: UsageMetric): string { return ({"copilot-ai-credits":"Copilot AI credits","copilot-premium-requests":"Copilot premium requests","actions-minutes":"Actions minutes","actions-storage":"Actions storage"} as const)[metric.kind]; }
/**
 * Panel styles, matched to the Claude and Codex monitors so a user running more
 * than one sees the same product rather than three different ones: a 500px centred
 * column, 13px uppercase section labels, an 8px rounded track with the brand fill,
 * and the percentage right-aligned beside the bar.
 */
function styles(): string {
  return `:root{color-scheme:light dark}*{box-sizing:border-box}` +
    `body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);font-size:13px;line-height:1.5;margin:0}` +
    `main{max-width:500px;margin:0 auto;padding:20px}` +
    `h2{margin:0 0 16px;font-size:16px;color:var(--vscode-editor-foreground)}` +
    // Title left, identity right. `flex-start` on the wrap keeps the identity block
    // aligned to the title's cap height rather than floating against a taller row,
    // and `min-width:0` lets a long organization name ellipsize instead of pushing
    // the layout wider than the panel.
    `.panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px}` +
    `.panel-head h2{margin:0}` +
    `.acct{display:flex;flex-direction:column;align-items:flex-end;gap:2px;min-width:0}` +
    `.acct-line{font-size:11px;line-height:1.35;max-width:230px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}` +
    `.acct-key{opacity:0.6}` +
    `.acct-val{font-weight:600;opacity:0.95}` +
    `.acct-muted{opacity:0.6;font-style:italic}` +
    `.acct-actions{display:flex;gap:6px;margin-top:5px}` +
    `.acct-btn{background:none;border:1px solid var(--vscode-panel-border,rgba(128,128,128,0.4));color:var(--vscode-textLink-foreground);border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer}` +
    `.acct-btn:hover{background:var(--vscode-toolbar-hoverBackground,rgba(128,128,128,0.15))}` +
    `.acct-btn-primary{background:var(--vscode-button-background);color:var(--vscode-button-foreground);border-color:transparent}` +
    `h3{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.8}` +
    `h4{margin:14px 0 6px;font-size:12px;opacity:0.8}` +
    `.section{margin-bottom:16px}` +
    `.divider{border-top:1px solid var(--vscode-widget-border,rgba(128,128,128,0.35));margin:16px 0}` +
    `.bar-row{display:flex;align-items:center;gap:10px}` +
    `.bar{flex:1;height:8px;background:rgba(128,128,128,0.2);border-radius:4px;overflow:hidden}` +
    `.bar-fill{height:100%;background:${GITHUB_BAR_FILL};border-radius:4px;transition:width 0.3s ease}` +
    `.bar-pct{font-size:14px;font-weight:700;min-width:40px;text-align:right}` +
    `.bar-fill.none{background:var(--vscode-descriptionForeground,#888);opacity:0.35}` +
    `.bar-pct.none{opacity:0.5;font-weight:600}` +
    `.repo-table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}` +
    `.repo-table th{text-align:left;font-weight:600;padding:3px 6px;border-bottom:1px solid var(--vscode-widget-border,#4444)}` +
    `.repo-table td{padding:3px 6px}` +
    `.repo-table .num{text-align:right;font-variant-numeric:tabular-nums}` +
    `.repo-table .num.zero{opacity:0.5}` +
    `.repo-table .vis.public{color:var(--vscode-descriptionForeground)}` +
    `.bar-fill.exhausted{background:var(--vscode-notificationsErrorIcon-foreground,#e05555)}` +
    `.bar-pct.exhausted{color:var(--vscode-notificationsErrorIcon-foreground,#e05555)}` +
    `.absolute{font-size:14px;font-weight:700}` +
    `.sub{font-size:11px;opacity:0.7;margin-top:4px}` +
    `.est{opacity:0.65;font-style:italic}` +
    `.notice{padding:8px 12px;margin-bottom:16px;border-radius:4px;font-size:12px;background:var(--vscode-inputValidation-warningBackground,rgba(255,204,0,0.1));border:1px solid var(--vscode-inputValidation-warningBorder,#cca700)}` +
    `.detail{margin-bottom:16px}` +
    `.detail summary{cursor:pointer;font-size:12px;opacity:0.8;user-select:none}` +
    `.detail summary:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}` +
    `.table-scroll{overflow-x:auto}` +
    `table{width:100%;border-collapse:collapse;font-size:11px}` +
    `th,td{text-align:left;padding:4px 8px 4px 0;border-bottom:1px solid var(--vscode-widget-border,rgba(128,128,128,0.25))}` +
    `th{opacity:0.7;font-weight:600}` +
    `.actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:4px}` +
    `button{border:none;border-radius:4px;padding:6px 14px;cursor:pointer;font-family:var(--vscode-font-family);font-size:12px;color:var(--vscode-button-foreground);background:var(--vscode-button-background)}` +
    `button:hover{background:var(--vscode-button-hoverBackground)}` +
    `button:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}` +
    `button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}` +
    `button.secondary:hover{background:var(--vscode-button-secondaryHoverBackground)}` +
    `button.icon-btn{display:inline-flex;align-items:center;justify-content:center;padding:6px;width:28px;height:28px;color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}` +
    `button.icon-btn:hover{background:var(--vscode-button-secondaryHoverBackground)}` +
    `button.icon-btn svg{display:block}` +
    `.last-updated{font-size:11px;opacity:0.6;margin-top:12px}` +
    `@media(prefers-reduced-motion:reduce){.bar-fill{transition:none}}`;
}
