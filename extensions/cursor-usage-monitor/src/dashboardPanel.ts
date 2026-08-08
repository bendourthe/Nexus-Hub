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
import { getRecommendation } from "./recommendations";
import { CONSENT_PROMPT_WILL_NOT_READ } from "./providers/consent";
import {
  currentSettings,
  resetSettings,
  saveSettings,
  settingsBindJs,
  settingsScriptJs,
  settingsSectionHtml,
  settingsStylesCss,
  type DraftState
} from "./embeddedSettings";
import { renderWebviewDocument } from "./webview";

/**
 * The usage dashboard, deliberately structured to match the Claude and Codex
 * monitors: one narrow centred column, uppercase section labels, a progress bar per
 * pool, then Current Model / Recommendation / Tips, the INLINE settings form the
 * gear toggles, and a footer of actions.
 *
 * One implementation difference from those siblings, kept on purpose. They use
 * inline `onclick=` handlers and inline `style="width:..."`, which only works
 * without a strict Content-Security-Policy. This webview runs under a nonce CSP
 * that forbids both, so the same visuals are produced with delegated listeners and
 * width classes. Matching their look must not mean inheriting a weaker CSP.
 */
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
        async (message: { command?: string; draft?: DraftState }) => {
          if (message.command === "save" && message.draft) {
            // Persist the inline form, then echo the STORED values back rather than
            // the draft: a value the configuration layer clamped or rejected must
            // show its real state, not what the user typed.
            const persisted = await saveSettings(message.draft);
            this.panel?.webview.postMessage({
              command: "loadSettings",
              settings: persisted
            });
            return;
          }
          if (message.command === "reset") {
            const persisted = await resetSettings();
            this.panel?.webview.postMessage({
              command: "loadSettings",
              settings: persisted
            });
            return;
          }
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
    function send(command) { vscode.postMessage({ command: command }); }
    document.querySelectorAll('[data-command]').forEach((control) => {
      control.addEventListener('click', () => send(control.getAttribute('data-command')));
    });
    const settingsToggle = document.getElementById('settingsToggle');
    if (settingsToggle) {
      settingsToggle.addEventListener('click', () => {
        toggleSettings();
        const open = !document.getElementById('settings-section').hidden;
        vscode.setState({ settingsOpen: open });
      });
    }
    // Setting webview.html re-creates the DOM, so the open/closed state of the
    // settings form has to be restored explicitly. Without this a configuration
    // change collapsed the form the moment it was saved, which reads as the change
    // being discarded.
    (function restoreSettingsOpen() {
      const previous = vscode.getState();
      const section = document.getElementById('settings-section');
      if (previous && previous.settingsOpen && section) { section.hidden = false; }
    })();
    ${settingsScriptJs(currentSettings())}
    ${settingsBindJs()}
    window.addEventListener('message', (event) => {
      if (event.data && event.data.command === 'loadSettings') {
        applySettings(event.data.settings);
      }
    });`,
    ...(nonce === undefined ? {} : { nonce })
  });
}

function renderEmpty(message: string): string {
  // A first-run screen, not an error screen. Automatic tracking WORKS as of the
  // verified RPC, so this asks for consent rather than explaining an absence.
  // Manual entry survives for anyone who declines, with its weakness stated: a
  // pasted figure is frozen at the moment it was entered.
  return `<main>
    <h2>Cursor Usage Dashboard</h2>
    <div class="empty-state">
      <h3 class="empty-title">Not connected yet</h3>
      <p><strong>Live tracking is available, and off until you allow it.</strong></p>
      <p>Your real usage can be read automatically. Doing so needs your permission once, because it uses the same session Cursor itself signed you in with, read from Cursor's own local state. Nothing is read before you agree.</p>
      <div class="onboarding">
        <h3>Turn it on in one step</h3>
        <ol>
          <li><strong>Click "Connect live tracking".</strong> You will see one prompt stating exactly what is read and what is never read. Allow it, and your real figures appear here and in the status bar, refreshing on their own.</li>
        </ol>
        <p class="context-note">Prefer not to? Open your usage page and type the figures in by hand instead. Be aware of what that gives you: a snapshot frozen at the moment you enter it, which does not follow your usage and will quietly go out of date.</p>
        <p class="context-note">Whichever you choose, this is what is never read:</p>
        <ul class="context-note">${CONSENT_PROMPT_WILL_NOT_READ.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>
      </div>
      <div class="actions">
        <button data-command="connectLive">Connect live tracking</button>
        <button class="secondary" data-command="openUsagePage">Open my Cursor usage page</button>
        <button class="secondary" data-command="manualEntry">Enter figures by hand</button>
        <button class="secondary" data-command="settings">Settings</button>
      </div>
      <details class="diagnostic-detail">
        <summary>Technical detail</summary>
        <p>${escapeHtml(message)}</p>
      </details>
    </div>
  </main>`;
}

function renderSnapshot(
  state: Exclude<UsageState, { state: "empty" }>,
  now: number
): string {
  const snapshot = state.data;
  const recommendation = getRecommendation(snapshot);
  const errorBanner =
    state.state === "stale"
      ? `<div class="error-banner"><span class="error-icon">&#9888;</span><span><strong>Stale usage snapshot.</strong> ${escapeHtml(state.error.message)} Percentages are not used for alerts until fresh data returns.</span><button class="retry-btn" data-command="refresh">Retry</button></div>`
      : "";
  const sourceLabel =
    snapshot.source === "manual" ? "Manually entered" : "Auto-fetched";

  return `<main>
    ${errorBanner}
    <h2>Cursor Usage Dashboard</h2>

    <div class="section">
      <h3>Cursor Models</h3>
      ${poolBar(snapshot.cursorModels, snapshot, now)}
    </div>

    <div class="section">
      <h3>Other Models</h3>
      ${poolBar(snapshot.otherModels, snapshot, now)}
    </div>

    ${extraCreditsSection(snapshot, now)}

    <div class="divider"></div>

    <div class="section">
      <h3>Recommendation</h3>
      <p class="recommendation urgency-${recommendation.urgency}">${escapeHtml(recommendation.message)}</p>
      ${recommendation.suggestedPool === null ? "" : `<p class="suggested-model">Prefer: <strong>${escapeHtml(recommendation.suggestedPool)}</strong></p>`}
    </div>

    ${recommendation.tips.length === 0 ? "" : `<div class="section">
      <h3>Tips</h3>
      <ul class="tips">${recommendation.tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("")}</ul>
    </div>`}

    ${settingsSectionHtml(currentSettings())}

    <div class="divider"></div>

    <div class="actions">
      <button data-command="refresh">Refresh Now</button>
      <button class="link" data-command="openUsagePage">Open Usage Page</button>
      <button id="settingsToggle" class="icon-btn" title="Settings" aria-label="Settings">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.687.706-1.99 1.99l.169.31a1.464 1.464 0 0 1-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.697 1.283.707 2.687 1.99 1.99l.311-.17a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.687-.706 1.99-1.99l-.169-.31a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.697-1.283-.707-2.687-1.99-1.99l-.311.17a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/>
        </svg>
      </button>
    </div>

    <p class="last-updated">${escapeHtml(sourceLabel)} ${escapeHtml(formatTimestamp(snapshot.fetchedAt))}</p>
  </main>`;
}

/** One included-usage pool: a bar with a right-aligned percentage, then a reset line. */
function poolBar(
  meter: IncludedUsageMeter,
  snapshot: UsageSnapshot,
  now: number
): string {
  const reset = `Resets ${formatReset(snapshot.period.resetsAt, now)}`;
  if (meter.percentUsed === null) {
    return `<div class="absolute">${escapeHtml(formatQuantity(meter.used))}</div>
      <span class="progress-subtitle">Allowance unavailable - absolute usage only. ${escapeHtml(reset)}</span>`;
  }
  const detail = [
    meter.used === null ? null : `${formatQuantity(meter.used)} used`,
    meter.limit === null ? null : `allowance ${formatQuantity(meter.limit)}`
  ].filter((part): part is string => part !== null);
  return `${progressBar(meter.percentUsed, formatPercent(meter.percentUsed), "Included usage")}
    <span class="progress-subtitle">${detail.length === 0 ? "" : `${escapeHtml(detail.join(" - "))}. `}${escapeHtml(reset)}</span>`;
}

/**
 * Extra Credits, in the sibling monitors' two-line grammar.
 *
 * The headline states the ORGANIZATION's draw against the shared limit, because
 * that is what decides whether the next request is billable. The italic second line
 * gives the user's own contribution. Personal spend alone is the misleading reading:
 * $157.32 against a $200.00 limit looks like a fifth of the budget remains, and on a
 * real account the pool was fully drawn with nothing left.
 *
 * The Phase 2 rules are unchanged: never present the shared pool as a personal cap,
 * never divide it into a per-member figure, and drop the bar rather than approximate
 * when a fraction would be meaningless.
 */
function extraCreditsSection(snapshot: UsageSnapshot, now: number): string {
  const limit = snapshot.teamContext.sharedSpendLimit ?? null;
  const pooledUsed = snapshot.teamContext.sharedSpendUsed ?? null;
  const remaining = snapshot.teamContext.sharedSpendRemaining ?? null;
  const personal = snapshot.onDemand.personalSpend ?? null;
  const reset = `Resets ${formatReset(snapshot.period.resetsAt, now)}`;

  if (!snapshot.onDemand.enabled) {
    return `<div class="section">
      <h3>Extra Credits</h3>
      <div class="extra-credits-info">Not applicable</div>
      <span class="progress-subtitle">On-demand spending is off for this account.</span>
    </div>`;
  }

  const yours = personal === null ? "Not reported" : formatMoney(personal);
  const currencyMismatch =
    limit !== null && personal !== null && limit.currency !== personal.currency;
  if (limit === null || limit.amount <= 0 || currencyMismatch) {
    const why = currencyMismatch
      ? "The shared limit is reported in a different currency than your spend, so no percentage is shown."
      : "Shared limit not reported.";
    return `<div class="section">
      <h3>Extra Credits</h3>
      <div class="extra-credits-info">${escapeHtml(yours)} used by your account</div>
      <span class="progress-subtitle">Shared spend limit unavailable - spend only. ${escapeHtml(why)} Shared limit not reported. This limit is shared across your team, not a personal allowance. ${escapeHtml(reset)}</span>
    </div>`;
  }

  const pooledComparable =
    pooledUsed !== null && pooledUsed.currency === limit.currency;
  const personalPercent = spendFractionOfLimit(personal, limit);
  const percent = pooledComparable
    ? (pooledUsed.amount / limit.amount) * 100
    : (personalPercent ?? 0);
  const sharedLimitLine = `Shared limit ${formatMoney(limit)}.`;
  const headline = pooledComparable
    ? `${formatMoney(pooledUsed)} / ${formatMoney(limit)} used this month by the organization`
    : `${formatSpendAgainstLimit(personal, limit)} used this month`;
  const left =
    remaining === null
      ? ""
      : remaining.amount <= 0
        ? " The shared pool is fully spent - nothing left."
        : ` ${formatMoney(remaining)} left in the shared pool.`;
  const over =
    percent > 100
      ? " Over the shared limit; the bar is shown full."
      : "";
  const personalNote =
    personalPercent === null
      ? ""
      : ` (${formatPercent(personalPercent)} of the limit shared across your team)`;

  return `<div class="section">
    <h3>Extra Credits</h3>
    <div class="extra-credits-info">${escapeHtml(headline)}</div>
    <div class="extra-credits-personal">(${escapeHtml(yours)} used by your account)</div>
    ${progressBar(percent, formatPercent(percent), "On-demand spend against the shared team limit")}
    <span class="progress-subtitle">${escapeHtml(`${sharedLimitLine} ${formatSharedSpendNote(snapshot.period.resetsAt)}${left}${over}${personalNote}`)}</span>
  </div>`;
}

/** A pill-shaped track and fill, clamped so an over-limit pool cannot overflow. */
function progressBar(percent: number, label: string, ariaLabel: string): string {
  const clamped = Math.round(Math.min(100, Math.max(0, percent)));
  return `<div class="progress-container">
    <div class="progress-bar" role="meter" aria-label="${escapeHtml(ariaLabel)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${clamped}">
      <div class="progress-fill fill-${clamped}"></div>
    </div>
    <span class="progress-label">${escapeHtml(label)}</span>
  </div>`;
}

function formatTimestamp(value: string): string {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? "Unknown" : new Date(parsed).toLocaleString();
}

function formatReset(value: string | null, now: number): string {
  if (value === null) {
    return "Not reported";
  }
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return "Not reported";
  }
  const minutes = Math.max(0, Math.round((parsed - now) / 60000));
  return `${new Date(parsed).toLocaleString()} (${minutes} min remaining)`;
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

function dashboardStyles(): string {
  // Width classes rather than inline widths: this webview runs under a nonce CSP
  // that forbids inline style attributes, so the fill width comes from a class.
  const fillClasses = Array.from(
    { length: 101 },
    (_, value) => `.fill-${value}{width:${value}%}`
  ).join("");
  return `:root{color-scheme:light dark}
*{box-sizing:border-box}
body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);background:var(--vscode-editor-background);padding:20px;max-width:500px;margin:0 auto;font-size:13px;line-height:1.5}
h2{color:var(--vscode-editor-foreground);margin-top:0;font-size:16px}
h3{color:var(--vscode-editor-foreground);margin:0 0 8px 0;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.8}
.section{margin-bottom:16px}
.divider{border-top:1px solid var(--vscode-widget-border,rgba(128,128,128,0.35));margin:16px 0}
.error-banner{display:flex;align-items:center;gap:8px;padding:8px 12px;margin-bottom:16px;background:var(--vscode-inputValidation-warningBackground,rgba(255,204,0,0.1));border:1px solid var(--vscode-inputValidation-warningBorder,#cca700);border-radius:4px;font-size:12px;line-height:1.4}
.error-icon{flex-shrink:0;font-size:14px}
.retry-btn{margin-left:auto}
.progress-container{display:flex;align-items:center;gap:10px}
.progress-bar{flex:1;height:8px;background:rgba(128,128,128,0.2);border-radius:4px;overflow:hidden}
.progress-fill{height:100%;background:${METER_FILL_COLOR};border-radius:4px;transition:width 0.3s ease}
.progress-label{font-size:14px;font-weight:bold;min-width:40px;text-align:right}
.progress-subtitle{font-size:11px;opacity:0.7;display:block;margin-top:2px}
.extra-credits-info{font-size:13px;margin-bottom:2px}
.extra-credits-personal{font-size:12px;font-style:italic;opacity:0.75;margin-bottom:6px}
.absolute{font-size:14px;font-weight:600}
.recommendation{line-height:1.5;margin:4px 0}
.urgency-low{color:#3fb950}
.urgency-moderate{color:#d29922}
.urgency-high{color:#db6d28}
.urgency-critical{color:#f85149}
.suggested-model{margin:4px 0;font-size:13px}
.tips{padding-left:20px;margin:4px 0}
.tips li{line-height:1.6;font-size:12px}
.actions{display:flex;gap:8px;flex-wrap:wrap}
button{padding:6px 14px;border:none;border-radius:4px;cursor:pointer;font-size:12px;font-family:var(--vscode-font-family);color:var(--vscode-button-foreground);background:var(--vscode-button-background)}
button:hover{background:var(--vscode-button-hoverBackground)}
button:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}
button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}
button.secondary:hover{background:var(--vscode-button-secondaryHoverBackground)}
button.link{background:none;color:var(--vscode-foreground);padding:6px 8px}
button.link:hover{background:var(--vscode-toolbar-hoverBackground,rgba(128,128,128,0.2))}
button.icon-btn{display:inline-flex;align-items:center;justify-content:center;padding:6px;width:28px;height:28px;color:var(--vscode-foreground);background:none}
button.icon-btn:hover{background:var(--vscode-toolbar-hoverBackground,rgba(128,128,128,0.2))}
button.icon-btn svg{display:block}
.last-updated{font-size:11px;opacity:0.6;margin-top:12px}
.empty-state{padding:8px 0}
.empty-title{font-size:15px;text-transform:none;letter-spacing:0;opacity:1}
.onboarding{border-left:3px solid ${METER_FILL_COLOR};padding:14px;margin:16px 0;background:var(--vscode-editorWidget-background)}
.onboarding h3{margin-top:0}
.onboarding ol{margin:0;padding-left:20px}
.onboarding li{margin-bottom:8px}
.context-note{opacity:0.8;font-size:12px}
.diagnostic-detail{margin-top:16px;opacity:0.75;font-size:12px}
.diagnostic-detail summary{cursor:pointer}
${fillClasses}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
@media(forced-colors:active){.progress-bar{forced-color-adjust:none;border:1px solid CanvasText;background:Canvas}.progress-fill{background:Highlight}button{border:1px solid ButtonText}}
${settingsStylesCss()}`;
}
