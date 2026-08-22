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
 * Phase 5 made the alert, status-bar, and refresh fields editable in place. They
 * write straight back through `postMessage`; `extension.ts` re-validates every
 * message before touching configuration, because a webview is a browser context
 * and cannot be trusted to gate its own writes.
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
  statusBarMetric: string;
  alertMetric: string;
  moderate: number;
  high: number;
  critical: number;
  moderateColor: string;
  highColor: string;
  criticalColor: string;
}

export function readSettings(): SettingsValues {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  return {
    billingScope: config.get("billingScope", "user"), billingOwner: config.get("billingOwner", ""), copilotMetric: config.get("copilotMetric", "ai-credits"),
    copilotAllowance: optionalNumber(config.get("allowances.copilot", null)), actionsMinutesAllowance: optionalNumber(config.get("allowances.actionsMinutes", null)), actionsStorageAllowance: optionalNumber(config.get("allowances.actionsStorage", null)),
    refreshInterval: config.get("refreshInterval", 10), compactStatusBar: config.get("compactStatusBar", false), statusBarMetric: config.get("statusBarMetric", "actions-minutes"), alertMetric: config.get("alertMetric", "actions-minutes"),
    moderate: config.get("thresholds.moderate", 50), high: config.get("thresholds.high", 75), critical: config.get("thresholds.critical", 95),
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
/**
 * Component CSS for the inline settings form, matched to the Claude monitor's
 * controls: bordered cards, a pill toggle, accent-coloured sliders with a live
 * value, and a colour swatch beside a hex field.
 *
 * Deliberately omits base `body` / `*` rules so it composes with the dashboard's own
 * styles rather than clobbering them; every selector is settings-specific.
 */
export function settingsStylesCss(): string {
  return `#settings-section{margin-top:4px}` +
    `.settings-subtitle{font-size:12px;color:var(--vscode-descriptionForeground);margin:2px 0 16px}` +
    `.set-group{margin:18px 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;opacity:0.8}` +
    `.set-card{border:1px solid var(--vscode-panel-border,var(--vscode-widget-border));border-radius:6px;padding:14px 16px;margin-bottom:12px}` +
    `.set-row{display:flex;align-items:center;gap:12px}` +
    `.set-label{font-size:12px;white-space:nowrap}` +
    `.set-hint{font-size:12px;color:var(--vscode-descriptionForeground)}` +
    `.set-line{display:flex;justify-content:space-between;gap:12px;font-size:12px;margin:4px 0}` +
    `.set-account .account-name{font-size:14px;font-weight:600;margin-bottom:10px}` +
    `.set-select{flex:1;background:var(--vscode-dropdown-background);color:var(--vscode-dropdown-foreground);` +
    `border:1px solid var(--vscode-dropdown-border);border-radius:3px;padding:4px 8px;font-family:var(--vscode-font-family);font-size:12px;cursor:pointer}` +
    `#settings-section input[type=number]{width:90px;padding:4px 6px;font:inherit;color:var(--vscode-input-foreground);` +
    `background:var(--vscode-input-background);border:1px solid var(--vscode-input-border,var(--vscode-widget-border));border-radius:3px}` +
    `.switch{position:relative;display:inline-block;width:34px;height:18px;flex-shrink:0}` +
    `.switch input{opacity:0;width:0;height:0}` +
    `.switch .track{position:absolute;inset:0;cursor:pointer;background:var(--vscode-input-background,#3c3c3c);` +
    `border:1px solid var(--vscode-panel-border,var(--vscode-widget-border));border-radius:9px;transition:background 0.15s}` +
    `.switch .track::before{content:"";position:absolute;height:12px;width:12px;left:2px;top:2px;` +
    `background:var(--vscode-foreground);border-radius:50%;transition:transform 0.15s}` +
    `.switch input:checked + .track{background:var(--vscode-button-background);border-color:var(--vscode-button-background)}` +
    `.switch input:checked + .track::before{transform:translateX(16px);background:var(--vscode-button-foreground)}` +
    `.level-header{display:flex;align-items:center;gap:10px;margin-bottom:16px}` +
    `.level-badge{font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;padding:2px 8px;border-radius:3px}` +
    `.level-moderate{background:rgba(204,167,0,0.18);color:#cca700}` +
    `.level-high{background:rgba(240,100,60,0.18);color:#f0643c}` +
    `.level-critical{background:rgba(220,50,50,0.22);color:#e05555}` +
    `.level-desc{font-size:12px;color:var(--vscode-descriptionForeground)}` +
    `.field-row{display:flex;align-items:center;gap:12px;margin-bottom:12px}` +
    `.field-row:last-child{margin-bottom:0}` +
    `.field-label{font-size:12px;min-width:120px;flex-shrink:0}` +
    `.slider-group{display:flex;align-items:center;gap:10px;flex:1}` +
    `.slider{flex:1;accent-color:var(--vscode-button-background);cursor:pointer}` +
    `.slider-value{font-size:13px;font-weight:600;min-width:38px}` +
    `.color-group{display:flex;align-items:center;gap:8px}` +
    `.picker-wrapper{width:34px;height:22px;border-radius:3px;overflow:hidden;` +
    `border:1px solid var(--vscode-panel-border,var(--vscode-widget-border));flex-shrink:0;display:inline-block}` +
    `.color-input{width:46px;height:30px;border:none;padding:0;cursor:pointer;background:none;margin:-4px 0 0 -6px}` +
    `.hex-input{font-family:var(--vscode-editor-font-family,monospace);font-size:12px;width:72px;padding:3px 6px;` +
    `background:var(--vscode-input-background);color:var(--vscode-input-foreground);` +
    `border:1px solid var(--vscode-input-border,var(--vscode-panel-border));border-radius:3px}` +
    `.hex-input.invalid{border-color:#e05555}` +
    `#settings-section .note{color:var(--vscode-descriptionForeground);margin:8px 0 0;font-size:11px}` +
    `#settings-section .field-value{color:var(--vscode-descriptionForeground)}` +
    `#settings-section .group-actions{display:flex;flex-wrap:wrap;gap:8px}` +
    `#settings-section .danger{border-color:var(--vscode-notificationsErrorIcon-foreground)}` +
    `#settings-section .invalid-note{color:var(--vscode-notificationsErrorIcon-foreground);font-size:12px}` +
    `#settings-section input:focus-visible,#settings-section select:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:1px}`;
}

/**
 * Editable configuration keys, and the type each one round-trips as.
 *
 * The handler in `extension.ts` validates against this map rather than trusting the
 * key a webview message carries. A webview is a browser context: a message arriving
 * with an arbitrary key would otherwise let it write ANY VS Code setting, which is a
 * wider capability than this panel needs.
 */
export const EDITABLE_SETTINGS: Readonly<Record<string, "number" | "string" | "boolean">> = {
  "thresholds.moderate": "number",
  "thresholds.high": "number",
  "thresholds.critical": "number",
  "colors.moderate": "string",
  "colors.high": "string",
  "colors.critical": "string",
  alertMetric: "string",
  statusBarMetric: "string",
  compactStatusBar: "boolean",
};

/** Whether a key/value pair may be written, checked before any configuration update. */
export function isEditableSetting(key: unknown, value: unknown): key is string {
  if (typeof key !== "string") return false;
  const expected = EDITABLE_SETTINGS[key];
  if (expected === undefined) return false;
  if (expected === "number") return typeof value === "number" && Number.isFinite(value);
  return typeof value === expected;
}

/**
 * The inline settings section markup, hidden by default and toggled by the gear.
 *
 * Editable in place as of Phase 5: thresholds, colors, the alert metric, the
 * status-bar metric, and the compact toggle all write straight back through
 * `postMessage`. The "Edit in VS Code settings" button is kept as a secondary escape
 * hatch - some users prefer it and it costs one button.
 *
 * Every command dropped from the action row also lives here, grouped. Nothing was
 * removed: the action row was shortened, not the capability, and each command stays
 * registered so the Command Palette continues to reach it.
 */
export function settingsSectionHtml(values: SettingsValues, auth?: AuthDisplay): string {
  const button = (command: string, label: string, extraClass = "secondary"): string =>
    `<button class="${extraClass}" data-command="${command}">${escapeHtml(label)}</button>`;
  const selectRow = (key: string, label: string, value: string, options: ReadonlyArray<readonly [string, string]>): string =>
    `<div class="set-card set-row"><label class="set-label" for="set-${key}">${escapeHtml(label)}</label>` +
    `<select id="set-${key}" class="set-select" data-setting="${key}" data-kind="string">` +
    options.map(([option, text]) => `<option value="${escapeHtml(option)}"${option === value ? " selected" : ""}>${escapeHtml(text)}</option>`).join("") +
    `</select></div>`;
  const toggleRow = (key: string, label: string, value: boolean, hint: string): string =>
    `<div class="set-card set-row"><span class="set-label">${escapeHtml(label)}</span>` +
    `<label class="switch"><input type="checkbox" id="set-${key}"${value ? " checked" : ""} data-setting="${key}" data-kind="boolean">` +
    `<span class="track"></span></label><span class="set-hint">${escapeHtml(hint)}</span></div>`;
  const sliderRow = (key: string, value: number, min: number, max: number, suffix: string): string =>
    `<div class="field-row"><label class="field-label" for="set-${key}">Threshold</label>` +
    `<div class="slider-group"><input type="range" class="slider" id="set-${key}" min="${min}" max="${max}" value="${value}" data-setting="${key}" data-kind="number">` +
    `<span class="slider-value" id="val-${key}">${value}${suffix}</span></div>` +
    `<span class="invalid-note" id="err-${key}" role="alert"></span></div>`;
  const colorRow = (key: string, value: string): string =>
    `<div class="field-row"><label class="field-label" for="set-${key}">Status bar color</label>` +
    `<div class="color-group"><span class="picker-wrapper"><input type="color" class="color-input" id="set-${key}" value="${escapeHtml(value)}" data-setting="${key}" data-kind="string"></span>` +
    `<input type="text" class="hex-input" value="${escapeHtml(value)}" data-hex-for="${key}" maxlength="7"></div></div>`;
  const level = (name: string, badge: string, description: string, thresholdKey: string, threshold: number, colorKey: string, color: string): string =>
    `<div class="set-card level"><div class="level-header"><span class="level-badge level-${name}">${escapeHtml(badge)}</span>` +
    `<span class="level-desc">${escapeHtml(description)}</span></div>` +
    sliderRow(thresholdKey, threshold, 1, 100, "%") + colorRow(colorKey, color) + `</div>`;

  return `<section id="settings-section" hidden aria-label="Settings">
    <div class="divider"></div>
    <h2>Settings</h2>
    <p class="settings-subtitle">Adjust the status bar, alerts, and refresh interval. Changes apply immediately. Account controls live at the top of the panel, beside the title.</p>

    <h3 class="set-group">Status bar</h3>
    ${selectRow("statusBarMetric", "Show in status bar", values.statusBarMetric, [
      ["actions-minutes", "Actions minutes (default)"],
      ["actions-storage", "Actions storage"],
      ["copilot", "Copilot AI credits"],
      ["highest", "Highest known percentage"]
    ])}
    ${toggleRow("compactStatusBar", "Compact status bar", values.compactStatusBar, "Hide the \"GitHub Usage: \" label")}

    <h3 class="set-group">Alerts</h3>
    ${selectRow("alertMetric", "Apply thresholds to", values.alertMetric, [
      ["actions-minutes", "Actions minutes (default)"],
      ["highest", "Highest known percentage"],
      ["actions-storage", "Actions storage"],
      ["copilot-ai-credits", "Copilot AI credits"],
      ["copilot-premium-requests", "Copilot premium requests"]
    ])}
    ${level("moderate", "Moderate", "First alert level", "thresholds.moderate", values.moderate, "colors.moderate", values.moderateColor)}
    ${level("high", "High", "Elevated alert level", "thresholds.high", values.high, "colors.high", values.highColor)}
    ${level("critical", "Critical", "Maximum alert level", "thresholds.critical", values.critical, "colors.critical", values.criticalColor)}

  </section>`;
}

/**
 * Client-side write-back and inline validation.
 *
 * Threshold ordering is checked in the webview so the message is shown beside the
 * offending field rather than as a notification, and an invalid draft is never sent
 * - `extension.ts` re-validates anyway, because a webview cannot be trusted to
 * gate its own writes.
 */
const SETTINGS_WRITE_BACK_JS = `
  const HEX_RE = /^#[0-9a-fA-F]{6}$/;
  function settingsValue(el){
    if(el.dataset.kind==='number')return Number(el.value);
    if(el.dataset.kind==='boolean')return el.checked;
    return el.value;
  }
  function thresholdOrderError(){
    const read=(k)=>Number((document.querySelector('[data-setting="'+k+'"]')||{}).value);
    const m=read('thresholds.moderate'),h=read('thresholds.high'),c=read('thresholds.critical');
    if(![m,h,c].every((v)=>Number.isFinite(v)&&v>=1&&v<=100))return 'Thresholds must be numbers from 1 to 100.';
    return (m<h&&h<c)?null:'Thresholds must increase from moderate to high to critical.';
  }
  function showFieldError(key,message){
    const note=document.getElementById('err-'+key);
    if(note)note.textContent=message||'';
  }
  function onSettingChange(el){
    const key=el.dataset.setting;
    if(key&&key.indexOf('thresholds.')===0){
      const error=thresholdOrderError();
      showFieldError(key,error);
      if(error)return;
      for(const other of ['thresholds.moderate','thresholds.high','thresholds.critical'])showFieldError(other,null);
    }
    vscode.postMessage({command:'updateSetting',key:key,value:settingsValue(el)});
  }
  document.querySelectorAll('[data-setting]').forEach(function(el){
    el.addEventListener('change',function(){onSettingChange(el);});
    if(el.classList.contains('slider')){
      el.addEventListener('input',function(){
        const out=document.getElementById('val-'+el.dataset.setting);
        if(out)out.textContent=el.value+'%';
      });
    }
    if(el.type==='color'){
      el.addEventListener('input',function(){
        const hex=document.querySelector('[data-hex-for="'+el.dataset.setting+'"]');
        if(hex){hex.value=el.value;hex.classList.remove('invalid');}
      });
    }
  });
  document.querySelectorAll('[data-hex-for]').forEach(function(hex){
    hex.addEventListener('input',function(){
      const raw=hex.value.trim();
      const value=raw.charAt(0)==='#'?raw:'#'+raw;
      if(!HEX_RE.test(value)){hex.classList.add('invalid');return;}
      hex.classList.remove('invalid');
      const picker=document.getElementById('set-'+hex.dataset.hexFor);
      if(picker)picker.value=value;
      vscode.postMessage({command:'updateSetting',key:hex.dataset.hexFor,value:value});
    });
  });
`;

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
  return SETTINGS_WRITE_BACK_JS +
    `function toggleSettings(){` +
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
