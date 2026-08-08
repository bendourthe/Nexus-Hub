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

export class SettingsPanel {
  private panel: vscode.WebviewPanel | undefined;
  public show(auth?: AuthDisplay): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel("githubUsageSettings", "GitHub Billing Usage Settings", vscode.ViewColumn.One, { enableScripts: true });
      this.panel.onDidDispose(() => { this.panel = undefined; });
      this.panel.webview.onDidReceiveMessage((message: { command?: string }) => {
        if (message.command) void vscode.commands.executeCommand(`github-usage.${message.command}`);
      });
    }
    this.panel.webview.html = renderSettings(readSettings(), auth);
    this.panel.reveal();
  }
}

export function readSettings(): SettingsValues {
  const config = vscode.workspace.getConfiguration("githubUsage");
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
    <div>
      <button data-command="logIn">Log in / switch account</button>
      <button data-command="logOut">Log out of this monitor</button>
    </div>
    <p class="note">Logging out clears only this extension's binding. It never signs you out of the editor's GitHub session, so Copilot is unaffected.</p>
  </fieldset>`;
}

export function renderSettings(
  values: SettingsValues,
  auth?: AuthDisplay
): string {
  const field = (label: string, value: string | number | null) => `<label>${label}<input value="${escapeHtml(value === null ? "" : String(value))}" readonly></label>`;
  return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-settings';"><style>:root{color-scheme:light dark}body{max-width:760px;margin:0 auto;padding:28px;color:var(--vscode-editor-foreground);background:var(--vscode-editor-background);font:13px/1.5 var(--vscode-font-family)}h1{font-size:26px}fieldset{border:1px solid var(--vscode-widget-border);margin:18px 0;padding:16px}legend{font-weight:700}label{display:grid;grid-template-columns:210px 1fr;gap:12px;margin:9px 0;align-items:center}input{padding:6px;color:var(--vscode-input-foreground);background:var(--vscode-input-background);border:1px solid var(--vscode-input-border)}button{padding:7px 12px;margin:4px;color:var(--vscode-button-foreground);background:var(--vscode-button-background);border:0}button:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}.note{color:var(--vscode-descriptionForeground)}@media(max-width:560px){label{grid-template-columns:1fr}}</style></head><body><h1>GitHub Billing Usage Settings</h1><p class="note">This monitor reports Actions minutes and storage, plus Copilot billing, for the one billing owner configured below. Tokens are stored only in VS Code SecretStorage and are never displayed here. A token is accepted only after GitHub validates access for the configured owner.</p>${auth === undefined ? "" : renderAuthSection(auth)}<fieldset><legend>Billing owner</legend>${field("Scope", values.billingScope)}${field("Owner", values.billingOwner)}${field("Copilot metric", values.copilotMetric)}</fieldset><fieldset><legend>Verified allowances</legend>${field("Copilot", values.copilotAllowance)}${field("Actions minutes", values.actionsMinutesAllowance)}${field("Actions storage", values.actionsStorageAllowance)}</fieldset><fieldset><legend>Refresh and alerts</legend>${field("Refresh interval (minutes)", values.refreshInterval)}${field("Compact status bar", String(values.compactStatusBar))}${field("Alert metric", values.alertMetric)}${field("Moderate threshold", values.moderate)}${field("High threshold", values.high)}${field("Critical threshold", values.critical)}${field("Notification timeout", values.notificationTimeoutSeconds)}${field("Moderate color", values.moderateColor)}${field("High color", values.highColor)}${field("Critical color", values.criticalColor)}</fieldset><div><button data-command="setToken">Set token</button><button data-command="rotateToken">Rotate token</button><button data-command="validateToken">Validate token</button><button data-command="clearToken">Clear token</button><button data-command="openNativeSettings">Edit settings</button></div><script nonce="settings">const vscode=acquireVsCodeApi();document.querySelectorAll('[data-command]').forEach((button)=>button.addEventListener('click',()=>vscode.postMessage({command:button.dataset.command})));</script></body></html>`;
}

function optionalNumber(value: unknown): number | null { return typeof value === "number" && Number.isFinite(value) ? value : null; }
