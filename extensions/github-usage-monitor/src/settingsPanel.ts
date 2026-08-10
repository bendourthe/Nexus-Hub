import * as vscode from "vscode";
import { escapeHtml } from "./statusBarManager";
import {
  describeCapability,
  type BillingAuthCapability
} from "./providers/capability";
import {
  describeBinding,
  type MonitorBinding
} from "./providers/sessionBinding";

/**
 * The settings form used to be its own webview panel. As of v3.16.3 Phase 4 it
 * renders INLINE inside the dashboard webview, toggled by a gear in the action row,
 * so this module exposes the form as three embeddable pieces the dashboard stitches
 * into its single document: CSS, HTML, and client JS. There is no standalone panel.
 *
 * The composition shape is ported from `extensions/claude-usage-monitor`, which
 * solved the same problem in v3.14.6. Porting a proven in-repo pattern beats
 * inventing a second one, and it keeps the two monitors recognizably the same
 * product to a user who runs both.
 *
 * The section is read-only in this phase. Phase 5 makes the fields editable in
 * place; this phase moves them into the dashboard and gets the shell right first.
 */

/**
 * The auth block rendered above the settings fields. Kept separate from
 * `SettingsValues` because it is runtime state rather than configuration, and
 * because it must always be renderable even when nothing is configured yet.
 */
export interface AuthDisplay {
  binding: MonitorBinding | null;
  /** The billing target this verdict belongs to, e.g. "organization:acme". */
  target: string;
  capability: BillingAuthCapability;
  hasStoredToken: boolean;
}

export interface SettingsValues {
  billingScope: string;
  billingOwner: string;
  copilotMetric: string;
  copilotAllowance: number | null;
  actionsMinutesAllowance: number | null;
  actionsStorageAllowance: number | null;
  refreshInterval: number;
  compactStatusBar: boolean;
  alertMetric: string;
  moderate: number;
  high: number;
  critical: number;
  notificationTimeoutSeconds: number;
  moderateColor: string;
  highColor: string;
  criticalColor: string;
}

export function readSettings(): SettingsValues {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  return {
    billingScope: config.get("billingScope", "user"), billingOwner: config.get("billingOwner", ""), copilotMetric: config.get("copilotMetric", "ai-credits"),
    copilotAllowance: optionalNumber(config.get("allowances.copilot", null)), actionsMinutesAllowance: optionalNumber(config.get("allowances.actionsMinutes", null)), actionsStorageAllowance: optionalNumber(config.get("allowances.actionsStorage", null)),
    refreshInterval: config.get("refreshInterval", 10), compactStatusBar: config.get("compactStatusBar", false), alertMetric: config.get("alertMetric", "highest"),
    moderate: config.get("thresholds.moderate", 50), high: config.get("thresholds.high", 75), critical: config.get("thresholds.critical", 95), notificationTimeoutSeconds: config.get("notificationTimeoutSeconds", 12),
    moderateColor: config.get("colors.moderate", "#cca700"), highColor: config.get("colors.high", "#f0643c"), criticalColor: config.get("colors.critical", "#e05555")
  };
}

export function validateThresholds(values: Pick<SettingsValues, "moderate" | "high" | "critical">): string | null {
  if (![values.moderate, values.high, values.critical].every((value) => Number.isFinite(value) && value >= 1 && value <= 100)) return "Thresholds must be numbers from 1 to 100.";
  return values.moderate < values.high && values.high < values.critical ? null : "Thresholds must increase from moderate to high to critical.";
}

/**
 * The auth section. Always states WHICH account the monitor is bound to, and the
 * verdict for the configured target with its reason. A blocked target that merely
 * looked broken is what drives a user to paste a broader credential than the
 * situation needs, so the reason is shown rather than only the failure.
 */
export function renderAuthSection(auth: AuthDisplay): string {
  const statusWord =
    auth.capability.status === "supported"
      ? "Connected"
      : auth.capability.status === "blocked"
        ? "Blocked"
        : "Not checked";
  const credential = auth.hasStoredToken
    ? "A token is stored in SecretStorage for this extension."
    : "No token is stored; this extension uses the editor's GitHub session when that works.";

  return `<fieldset>
    <legend>Authorization</legend>
    <p class="note"><strong>${escapeHtml(statusWord)}</strong> for <code>${escapeHtml(auth.target)}</code></p>
    <p class="note">${escapeHtml(describeBinding(auth.binding))}</p>
    <p class="note">${escapeHtml(describeCapability(auth.capability))}</p>
    <p class="note">${escapeHtml(credential)}</p>
    <p class="note">Logging out clears only this extension's binding. It never signs you out of the editor's GitHub session, so Copilot is unaffected.</p>
  </fieldset>`;
}

/**
 * Component CSS for the inline settings form.
 *
 * Deliberately omits base `body` / `*` rules and generic element selectors so it
 * composes with the dashboard's own styles rather than clobbering them; every
 * selector here is a settings-specific class or id.
 */
export function settingsStylesCss(): string {
  return `#settings-section{margin-top:8px}` +
    `#settings-section fieldset{border:1px solid var(--vscode-widget-border);margin:14px 0;padding:14px;border-radius:6px}` +
    `#settings-section legend{font-weight:700;padding:0 6px}` +
    `#settings-section .field{display:grid;grid-template-columns:210px 1fr;gap:12px;margin:8px 0;align-items:center}` +
    `#settings-section .field-value{color:var(--vscode-descriptionForeground)}` +
    `#settings-section .note{color:var(--vscode-descriptionForeground);margin:6px 0}` +
    `#settings-section .group-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}` +
    `#settings-section .danger{border-color:var(--vscode-notificationsErrorIcon-foreground)}` +
    `@media(max-width:560px){#settings-section .field{grid-template-columns:1fr}}`;
}

/**
 * The inline settings section markup, hidden by default and toggled by the gear.
 *
 * Every command dropped from the action row lives here, grouped. Nothing was
 * removed: the action row was shortened, not the capability, and each command also
 * stays registered so the Command Palette continues to reach it.
 */
export function settingsSectionHtml(values: SettingsValues, auth?: AuthDisplay): string {
  const field = (label: string, value: string | number | null): string =>
    `<div class="field"><span>${escapeHtml(label)}</span><span class="field-value">${escapeHtml(value === null || value === "" ? "not set" : String(value))}</span></div>`;
  const button = (command: string, label: string, extraClass = "secondary"): string =>
    `<button class="${extraClass}" data-command="${command}">${escapeHtml(label)}</button>`;

  return `<section id="settings-section" hidden aria-label="Settings">
    <h2>Settings</h2>
    <p class="note">This monitor reports Actions minutes and storage, plus Copilot billing, for the one billing owner configured below. Tokens are stored only in VS Code SecretStorage and are never displayed here.</p>
    ${auth === undefined ? "" : renderAuthSection(auth)}
    <fieldset><legend>Account</legend>
      ${field("Scope", values.billingScope)}${field("Owner", values.billingOwner)}${field("Copilot metric", values.copilotMetric)}
      <div class="group-actions">
        ${button("logIn", "Connect / switch account")}${button("logOut", "Log out of this monitor")}
        ${button("setToken", "Set token")}${button("rotateToken", "Rotate token")}${button("validateToken", "Validate token")}${button("clearToken", "Clear token")}
        ${button("diagnoseAuth", "Diagnose authorization")}
      </div>
    </fieldset>
    <fieldset><legend>Allowances</legend>
      ${field("Copilot", values.copilotAllowance)}${field("Actions minutes", values.actionsMinutesAllowance)}${field("Actions storage (GB)", values.actionsStorageAllowance)}
      <p class="note">Allowances are derived from your plan automatically. Override one only if your account includes a different amount than the published figure.</p>
      <div class="group-actions">${button("manualEntry", "Override allowances")}${button("openNativeSettings", "Edit in VS Code settings")}</div>
    </fieldset>
    <fieldset><legend>Refresh and alerts</legend>
      ${field("Refresh interval (minutes)", values.refreshInterval)}${field("Compact status bar", String(values.compactStatusBar))}${field("Alert metric", values.alertMetric)}
      ${field("Moderate threshold", values.moderate)}${field("High threshold", values.high)}${field("Critical threshold", values.critical)}
      ${field("Notification timeout", values.notificationTimeoutSeconds)}
      ${field("Moderate color", values.moderateColor)}${field("High color", values.highColor)}${field("Critical color", values.criticalColor)}
    </fieldset>
    <fieldset class="danger"><legend>Danger zone</legend>
      <p class="note">Removes the cached snapshot and alert state from this machine. Your GitHub account and stored token are untouched.</p>
      <div class="group-actions">${button("clearData", "Clear cached data")}</div>
    </fieldset>
  </section>`;
}

/**
 * The settings form's client JS, concatenated into the dashboard's single nonced
 * `<script>`.
 *
 * It deliberately does NOT call `acquireVsCodeApi()` - the dashboard already holds
 * that handle, and calling it twice throws. Running under the dashboard's nonce
 * rather than adding a second inline block is what keeps the Content-Security-Policy
 * shape unchanged.
 */
export function settingsScriptJs(): string {
  return `function toggleSettings(){` +
    `const s=document.getElementById('settings-section');const g=document.getElementById('settings-toggle');if(!s)return;` +
    `const willOpen=s.hasAttribute('hidden');` +
    `if(willOpen){s.removeAttribute('hidden');s.scrollIntoView({behavior:'smooth',block:'start'});}else{s.setAttribute('hidden','');}` +
    `if(g)g.setAttribute('aria-expanded',String(willOpen));` +
    // Persisted so the section survives a re-render: the dashboard rebuilds its
    // entire HTML on every refresh, which would otherwise slam the panel shut
    // underneath a user who had just opened it.
    `try{const st=vscode.getState()||{};st.settingsOpen=willOpen;vscode.setState(st);}catch(e){}}` +
    `(function(){try{const st=vscode.getState()||{};` +
    `if(st.settingsOpen){const s=document.getElementById('settings-section');const g=document.getElementById('settings-toggle');` +
    `if(s)s.removeAttribute('hidden');if(g)g.setAttribute('aria-expanded','true');}}catch(e){}})();`;
}

function optionalNumber(value: unknown): number | null { return typeof value === "number" && Number.isFinite(value) ? value : null; }
