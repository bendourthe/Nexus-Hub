import * as crypto from "crypto";
import * as vscode from "vscode";
import { BAR_FILL, OrganizationUsage, PersonalUsage, UsageData } from "./types";
import { formatCreditCount, formatElapsed, formatPercent, formatResetLabel } from "./usageStore";
import { NOT_CONNECTED_HINT } from "./recommendations";
import { WINDOW_LABEL } from "./types";
import { ProviderFetchError, ProviderFetchErrorCode, describeProviderError } from "./providers";
import { getRecommendation } from "./recommendations";
import {
  OrganizationStatus,
  parseDraft,
  currentSettings,
  saveSettings,
  resetSettings,
  settingsStylesCss,
  settingsSectionHtml,
  settingsScriptJs,
} from "./settingsPanel";

export interface DashboardCallbacks {
  onRefresh: () => void;
  onOpenUsagePage: () => void;
  onSignIn: () => void;
  onSwitchAccount: () => void;
  onConnectOrganization: () => void;
  onDisconnectOrganization: () => void;
}

/** Codes whose fix is a GitHub sign-in or account choice in VS Code. */
const SIGN_IN_CODES: ReadonlySet<ProviderFetchErrorCode> = new Set(["no-credentials", "token-invalid"]);

const ROUNDING_NOTE =
  "The percentage is computed from GitHub's unrounded usage. GitHub's AI usage page rounds its headline to whole credits, so the two can differ by a fraction of a percent.";

export class DashboardPanel {
  private static currentPanel: DashboardPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    private data: UsageData | undefined,
    private timeSince: string,
    private fetchError: ProviderFetchError | undefined,
    private orgStatus: OrganizationStatus,
    private callbacks: DashboardCallbacks,
  ) {
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      async (raw: unknown) => {
        // The webview is untrusted input: accept only known commands, and only
        // a fully valid settings draft.
        if (raw == null || typeof raw !== "object" || typeof (raw as { command?: unknown }).command !== "string") {
          return;
        }
        const message = raw as { command: string; draft?: unknown };
        switch (message.command) {
          case "refresh":
            this.panel.webview.postMessage({ command: "setLoading" });
            this.callbacks.onRefresh();
            break;
          case "openUsagePage":
            this.callbacks.onOpenUsagePage();
            break;
          case "signIn":
            this.callbacks.onSignIn();
            break;
          case "switchAccount":
            this.callbacks.onSwitchAccount();
            break;
          case "connectOrganization":
            this.callbacks.onConnectOrganization();
            break;
          case "disconnectOrganization":
            this.callbacks.onDisconnectOrganization();
            break;
          case "save": {
            const draft = parseDraft(message.draft);
            if (!draft) {
              break;
            }
            const persisted = await saveSettings(draft);
            this.panel.webview.postMessage({ command: "loadSettings", settings: persisted });
            break;
          }
          case "reset": {
            const persisted = await resetSettings();
            this.panel.webview.postMessage({ command: "loadSettings", settings: persisted });
            break;
          }
        }
      },
      null,
      this.disposables,
    );
    this.panel.webview.html = this.getHtml();
  }

  static show(
    data: UsageData | undefined,
    timeSince: string,
    fetchError: ProviderFetchError | undefined,
    orgStatus: OrganizationStatus,
    callbacks: DashboardCallbacks,
    extensionUri?: vscode.Uri,
  ): DashboardPanel {
    const current = DashboardPanel.currentPanel;
    if (current) {
      current.data = data;
      current.timeSince = timeSince;
      current.fetchError = fetchError;
      current.orgStatus = orgStatus;
      current.callbacks = callbacks;
      current.panel.webview.html = current.getHtml();
      current.panel.reveal(vscode.ViewColumn.Beside);
      return current;
    }
    const panel = vscode.window.createWebviewPanel("copilotUsageDashboard", "Copilot Usage", vscode.ViewColumn.Beside, {
      enableScripts: true,
    });
    if (extensionUri) {
      // A dark glyph on light themes and a light glyph on dark themes.
      panel.iconPath = {
        light: vscode.Uri.joinPath(extensionUri, "icons", "copilot-dark.svg"),
        dark: vscode.Uri.joinPath(extensionUri, "icons", "copilot-light.svg"),
      };
    }
    DashboardPanel.currentPanel = new DashboardPanel(panel, data, timeSince, fetchError, orgStatus, callbacks);
    return DashboardPanel.currentPanel;
  }

  static updateIfOpen(
    data: UsageData | undefined,
    timeSince: string,
    fetchError: ProviderFetchError | undefined,
    orgStatus?: OrganizationStatus,
  ): void {
    const current = DashboardPanel.currentPanel;
    if (!current) {
      return;
    }
    current.data = data;
    current.timeSince = timeSince;
    current.fetchError = fetchError;
    if (orgStatus) {
      current.orgStatus = orgStatus;
    }
    current.panel.webview.html = current.getHtml();
  }

  /** Reveal the inline settings section (used by the palette "Settings" command). */
  static revealSettings(): void {
    DashboardPanel.currentPanel?.panel.webview.postMessage({ command: "openSettings" });
  }

  /** The rendered document, exposed for tests. */
  static currentHtml(): string | undefined {
    return DashboardPanel.currentPanel?.panel.webview.html;
  }

  private errorBanner(error: ProviderFetchError | undefined, hasData: boolean): string {
    if (!error || (error.code === "rate-limited" && hasData)) {
      return "";
    }
    return banner(error);
  }

  private getHtml(): string {
    const data = this.data;
    const settings = settingsSectionHtml(currentSettings(), this.orgStatus);
    if (!data) {
      return this.wrapHtml(`
        ${this.errorBanner(this.fetchError, false)}
        <div class="empty-state">
          <h2>No Usage Data</h2>
          <p>${escapeHtml(emptyMessage(this.fetchError))}</p>
          <div class="actions">
            ${primaryAction(this.fetchError)}
            <button data-command="openUsagePage" class="secondary">Open Usage Page</button>
            ${gearButton()}
          </div>
        </div>
        ${settings}
      `);
    }

    const recommendation = getRecommendation(data);
    const partial = [
      data.organizationError ? banner(data.organizationError) : "",
      data.personalError ? banner(data.personalError) : "",
    ].join("");

    return this.wrapHtml(`
      ${this.errorBanner(this.fetchError, true)}
      ${partial}
      <h2>Copilot Usage Dashboard</h2>
      ${staleNote("organization pool", data.organization?.stale, data.organization?.fetchedAt ?? data.lastUpdated)}
      ${staleNote("personal", data.personal?.stale, data.personal?.fetchedAt ?? data.lastUpdated)}

      ${data.organization ? organizationSection(data.organization) : ""}
      ${data.personal ? personalSection(data.personal, Boolean(data.organization)) : ""}

      <div class="divider"></div>

      <div class="section">
        <h3>Recommendation</h3>
        <p class="recommendation urgency-${recommendation.urgency}">${escapeHtml(recommendation.message)}</p>
      </div>

      ${recommendation.tips.length > 0 ? `
      <div class="section">
        <h3>Tips</h3>
        <ul class="tips">
          ${recommendation.tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("\n")}
        </ul>
      </div>` : ""}

      ${settings}

      <div class="divider"></div>

      <div class="actions">
        <button id="refreshBtn" data-command="refresh">Refresh Now</button>
        <button data-command="openUsagePage" class="secondary">Open Usage Page</button>
        ${gearButton()}
      </div>

      <p class="last-updated">Auto-fetched ${escapeHtml(this.timeSince)}</p>
    `);
  }

  private wrapHtml(body: string): string {
    // A nonce-gated Content-Security-Policy: no inline handlers, no other
    // script, no network. Inline style attributes stay allowed for the bars.
    const nonce = crypto.randomBytes(16).toString("base64");
    const csp = `default-src 'none'; style-src ${this.panel.webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';`;
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      padding: 20px;
      max-width: 500px;
      margin: 0 auto;
    }
    h2 {
      color: var(--vscode-editor-foreground);
      margin-top: 0;
      font-size: 16px;
    }
    h3 {
      color: var(--vscode-editor-foreground);
      margin: 0 0 8px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      opacity: 0.8;
    }
    .section {
      margin-bottom: 16px;
    }
    .divider {
      border-top: 1px solid var(--vscode-widget-border, rgba(128,128,128,0.35));
      margin: 16px 0;
    }
    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 16px;
      background: var(--vscode-inputValidation-warningBackground, rgba(255,204,0,0.1));
      border: 1px solid var(--vscode-inputValidation-warningBorder, #cca700);
      border-radius: 4px;
      font-size: 12px;
      line-height: 1.4;
    }
    .error-icon {
      flex-shrink: 0;
      font-size: 14px;
    }
    .info-banner {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 16px;
      background: var(--vscode-inputValidation-infoBackground, rgba(0,102,204,0.1));
      border: 1px solid var(--vscode-inputValidation-infoBorder, #007acc);
      border-radius: 4px;
      font-size: 12px;
      line-height: 1.4;
    }
    .info-icon {
      flex-shrink: 0;
      font-size: 14px;
    }
    .extra-credits-info {
      font-size: 13px;
      display: block;
      margin-top: 6px;
    }
    .retry-btn {
      flex-shrink: 0;
      margin-left: auto;
      padding: 3px 10px;
      font-size: 11px;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      color: var(--vscode-button-foreground);
      background: var(--vscode-button-background);
    }
    .retry-btn:hover {
      background: var(--vscode-button-hoverBackground);
    }
    .progress-container {
      position: relative;
    }
    .progress-bar {
      width: 100%;
      height: 8px;
      background: rgba(128,128,128,0.2);
      border-radius: 4px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: ${BAR_FILL};
      border-radius: 4px;
      transition: width 0.3s ease;
    }
    .progress-label {
      position: absolute;
      right: 0;
      bottom: calc(100% + 8px);
      font-size: 14px;
      font-weight: bold;
      text-align: right;
    }
    .progress-subtitle {
      font-size: 11px;
      opacity: 0.7;
      display: block;
      margin-top: 2px;
    }
    .recommendation {
      line-height: 1.5;
      margin: 4px 0;
    }
    .urgency-low { color: #3fb950; }
    .urgency-moderate { color: #d29922; }
    .urgency-high { color: #db6d28; }
    .urgency-critical { color: #f85149; }
    .suggested-model {
      margin: 4px 0;
      font-size: 13px;
    }
    .model-name {
      font-size: 14px;
      font-weight: 600;
    }
    .tips {
      padding-left: 20px;
      margin: 4px 0;
    }
    .tips li {
      line-height: 1.6;
      font-size: 12px;
    }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    button {
      padding: 6px 14px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      font-family: var(--vscode-font-family);
      color: var(--vscode-button-foreground);
      background: var(--vscode-button-background);
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    button.secondary {
      color: var(--vscode-button-secondaryForeground);
      background: var(--vscode-button-secondaryBackground);
    }
    button.secondary:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    button.icon-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px;
      width: 28px;
      height: 28px;
      color: var(--vscode-button-secondaryForeground);
      background: var(--vscode-button-secondaryBackground);
    }
    button.icon-btn:hover {
      background: var(--vscode-button-secondaryHoverBackground);
    }
    button.icon-btn svg {
      display: block;
    }
    .last-updated {
      font-size: 11px;
      opacity: 0.6;
      margin-top: 12px;
    }
    .empty-state {
      text-align: center;
      padding: 40px 0;
    }
    .empty-state p {
      opacity: 0.7;
      margin-bottom: 20px;
    }
    .empty-state .actions {
      justify-content: center;
    }
    .note {
      font-size: 12px;
      opacity: 0.8;
      line-height: 1.4;
      margin: 6px 0 0 0;
    }
    ${settingsStylesCss()}
  </style>
</head>
<body>
  ${body}
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    function send(command) {
      vscode.postMessage({ command });
    }
    ${settingsScriptJs(currentSettings())}
    window.addEventListener("message", function(event) {
      const msg = event.data;
      if (msg.command === "setLoading") {
        const btn = document.getElementById("refreshBtn");
        if (btn) { btn.textContent = "Refreshing..."; btn.disabled = true; }
      } else if (msg.command === "loadSettings") {
        applySettings(msg.settings);
      } else if (msg.command === "openSettings") {
        const s = document.getElementById("settings-section");
        if (s) {
          s.removeAttribute("hidden");
          s.scrollIntoView({ behavior: "smooth", block: "start" });
          try { const st = vscode.getState() || {}; st.settingsOpen = true; vscode.setState(st); } catch (e) {}
        }
      }
    });
  </script>
</body>
</html>`;
  }

  private dispose(): void {
    DashboardPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }
}

function progressBar(percent: number, valueText: string, subtitle: string, detail?: string, detailTitle?: string): string {
  const width = Math.round(Math.min(100, Math.max(0, percent)) * 100) / 100;
  const title = detailTitle ? ` title="${escapeHtml(detailTitle)}"` : "";
  return `
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${width}%;"></div>
        </div>
        <span class="progress-label">${escapeHtml(valueText)}</span>
      </div>
      ${detail ? `<span class="extra-credits-info"${title}>${escapeHtml(detail)}</span>` : ""}
      <span class="progress-subtitle">${escapeHtml(subtitle)}</span>`;
}

function organizationSection(org: OrganizationUsage): string {
  const notes: string[] = [];
  if (org.approximateReasons.includes("seat-added")) {
    notes.push("Approximate: a seat was added this cycle, and GitHub does not publish how an added seat is prorated.");
  }
  if (org.approximateReasons.includes("pending-cancellation")) {
    notes.push("Approximate: a seat is pending cancellation; it still counts toward this month's pool.");
  }
  notes.push("Covers this organization only. A seat removed outright this cycle still counts toward the pool but is missing from the seat count, so the total can read low.");
  const planName = org.planType === "enterprise" ? "Enterprise" : org.planType === "business" ? "Business" : "";
  // Each model's share of the pool, as a percentage; never a credit count.
  const models = org.models.length > 0 && org.total > 0
    ? `<ul class="tips">${org.models.map((m) => `<li>${escapeHtml(m.model)}: ${formatPercent((m.used / org.total) * 100)}% of the pool</li>`).join("")}</ul>`
    : "";

  if (org.percent == null) {
    return `
      <div class="section">
        <h3>Organization Pool</h3>
        <div class="extra-credits-info">--% (${WINDOW_LABEL})</div>
        <p class="note">GitHub reported no Copilot seats for this organization, so there is no pool total and no percentage.</p>
      </div>`;
  }
  const approx = org.approximate ? " (approximate)" : "";
  return `
      <div class="section">
        <h3>Organization Pool${approx}</h3>
        ${progressBar(
          org.percent,
          `${org.approximate ? "~" : ""}${formatPercent(org.percent)}%`,
          formatResetLabel(org.resetsAt),
          `Pool: ${formatCreditCount(org.total)} credits${org.approximate ? ", approximate total" : ""} (${WINDOW_LABEL})`,
          ROUNDING_NOTE,
        )}
        <p class="note">${org.seats} ${planName} seat${org.seats === 1 ? "" : "s"} x ${formatCreditCount(org.creditsPerSeat)} credits per seat.</p>
        ${notes.map((n) => `<p class="note">${escapeHtml(n)}</p>`).join("")}
        ${models}
      </div>`;
}

/** A one-line note that a figure is the last good one, kept after a failed refresh. */
function staleNote(which: string, stale: boolean | undefined, fetchedAt: number): string {
  if (!stale) {
    return "";
  }
  return `<p class="note">The last refresh failed, so the ${which} figure below is from ${escapeHtml(formatElapsed(Date.now() - fetchedAt))}.</p>`;
}

function personalSection(personal: PersonalUsage, organizationConnected: boolean): string {
  if (personal.quotas.length === 0) {
    if (organizationConnected) {
      return "";
    }
    return `
      <div class="section">
        <h3>${escapeHtml(personal.planLabel)}</h3>
        <div class="extra-credits-info">--% (${WINDOW_LABEL})</div>
        <p class="note">${escapeHtml(NOT_CONNECTED_HINT)}</p>
        <button data-command="connectOrganization" class="retry-btn">Connect Organization</button>
        <span class="progress-subtitle">${escapeHtml(formatResetLabel(personal.resetsAt))}</span>
      </div>`;
  }
  const bars = personal.quotas
    .map(
      (q) => `
      <div class="section">
        <h3>${escapeHtml(q.label)}</h3>
        ${progressBar(
          q.percent,
          `${formatPercent(q.percent)}% (${WINDOW_LABEL})`,
          formatResetLabel(personal.resetsAt),
        )}
      </div>`,
    )
    .join("");
  return `
      <div class="section"><h3>Plan</h3><div class="model-name">${escapeHtml(personal.planLabel)}</div></div>
      ${bars}`;
}

function primaryAction(error: ProviderFetchError | undefined): string {
  if (error && SIGN_IN_CODES.has(error.code)) {
    return `<button id="refreshBtn" data-command="signIn">Sign in to GitHub</button>`;
  }
  if (error?.code === "choose-account") {
    return `<button id="refreshBtn" data-command="signIn">Choose GitHub account</button>`;
  }
  return `<button id="refreshBtn" data-command="refresh">Retry</button>`;
}

function emptyMessage(error: ProviderFetchError | undefined): string {
  if (!error) {
    return "No Copilot usage fetched yet. Press Retry to fetch it now.";
  }
  if (error.code === "rate-limited") {
    return "GitHub is rate-limiting usage requests right now. This clears on its own; press Retry in a moment.";
  }
  return describeProviderError(error);
}

function banner(error: { code: string; statusCode?: number }): string {
  const typed = error as ProviderFetchError;
  let action = `<button data-command="refresh" class="retry-btn">Retry</button>`;
  if (SIGN_IN_CODES.has(typed.code)) {
    action = `<button data-command="signIn" class="retry-btn">Sign in to GitHub</button>`;
  } else if (typed.code === "choose-account") {
    action = `<button data-command="signIn" class="retry-btn">Choose GitHub account</button>`;
  } else if (typed.code === "org-token-rejected" || typed.code === "org-not-connected") {
    action = `<button data-command="connectOrganization" class="retry-btn">Reconnect</button>`;
  } else if (typed.code === "org-access-denied") {
    action = "";
  }
  return `<div class="error-banner">
          <span class="error-icon">&#9888;</span>
          <span>${escapeHtml(describeProviderError(typed))}</span>
          ${action}
        </div>`;
}

function gearButton(): string {
  return `<button data-click="toggleSettings" class="icon-btn" title="Settings" aria-label="Settings">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.687.706-1.99 1.99l.169.31a1.464 1.464 0 0 1-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.697 1.283.707 2.687 1.99 1.99l.311-.17a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.687-.706 1.99-1.99l-.169-.31a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.697-1.283-.707-2.687-1.99-1.99l-.311.17a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/>
          </svg>
        </button>`;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
