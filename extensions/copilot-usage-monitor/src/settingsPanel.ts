import * as vscode from "vscode";
import {
  CONFIG_SECTION,
  HEX_COLOR,
  validThreshold,
  getThresholdConfig,
  getColorConfig,
  DEFAULT_URGENCY_COLORS,
  URGENCY_THRESHOLDS,
  syncColorsToWorkbench,
  ColorConfig,
} from "./types";

/**
 * The settings form rendered inline in the dashboard webview (toggled by the
 * gear), as in the Claude and Codex monitors: state, the save and reset
 * configuration writes, and the CSS / HTML / JS builders the dashboard
 * stitches into its single webview document. Copilot has one monthly figure,
 * so there is no "apply thresholds to" choice; the Organization section adds
 * Connect and Disconnect.
 */

type Level = "moderate" | "high" | "critical";

export interface DraftState {
  thresholds: { moderate: number; high: number; critical: number };
  colors: { moderate: string; high: string; critical: string };
  compact: boolean;
}

/** What the Organization section shows. The organization login itself is never rendered. */
export interface OrganizationStatus {
  configured: boolean;
  connected: boolean;
}

export const SETTINGS_DEFAULTS: DraftState = {
  thresholds: { moderate: URGENCY_THRESHOLDS.moderate, high: URGENCY_THRESHOLDS.high, critical: URGENCY_THRESHOLDS.critical },
  colors: { moderate: DEFAULT_URGENCY_COLORS.moderate, high: DEFAULT_URGENCY_COLORS.high, critical: DEFAULT_URGENCY_COLORS.critical },
  compact: false,
};

/** The current persisted settings, read from VS Code configuration. */
export function currentSettings(): DraftState {
  return {
    thresholds: getThresholdConfig(),
    colors: getColorConfig(),
    compact: vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("compactStatusBar", false),
  };
}

/** Persist a settings draft; returns the values actually stored. */
export async function saveSettings(d: DraftState): Promise<DraftState> {
  const config = vscode.workspace.getConfiguration(CONFIG_SECTION);
  const target = vscode.ConfigurationTarget.Global;
  // Sequential writes: concurrent config.update() calls can overwrite each other.
  await config.update("thresholds.moderate", d.thresholds.moderate, target);
  await config.update("thresholds.high", d.thresholds.high, target);
  await config.update("thresholds.critical", d.thresholds.critical, target);
  await config.update("colors.moderate", d.colors.moderate, target);
  await config.update("colors.high", d.colors.high, target);
  await config.update("colors.critical", d.colors.critical, target);
  await config.update("compactStatusBar", d.compact, target);
  await syncColorsToWorkbench(d.colors as ColorConfig);
  return currentSettings();
}

/** Clear the display settings back to defaults; the organization connection is untouched. */
export async function resetSettings(): Promise<DraftState> {
  const config = vscode.workspace.getConfiguration(CONFIG_SECTION);
  const target = vscode.ConfigurationTarget.Global;
  await config.update("thresholds.moderate", undefined, target);
  await config.update("thresholds.high", undefined, target);
  await config.update("thresholds.critical", undefined, target);
  await config.update("colors.moderate", undefined, target);
  await config.update("colors.high", undefined, target);
  await config.update("colors.critical", undefined, target);
  await config.update("compactStatusBar", undefined, target);
  await syncColorsToWorkbench(SETTINGS_DEFAULTS.colors as ColorConfig);
  return { ...SETTINGS_DEFAULTS };
}

/**
 * Component CSS for the inline settings form. Every selector is a
 * settings-specific class or id, so it composes with the dashboard's styles.
 */
export function settingsStylesCss(): string {
  return `
  .settings-section { margin-top: 4px; }
  .settings-subtitle { font-size: 12px; color: var(--vscode-descriptionForeground); margin: 2px 0 16px 0; }

  .metric-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .metric-label { font-size: 12px; white-space: nowrap; }

  .toggle-row { justify-content: flex-start; }
  .toggle-switch { position: relative; display: inline-block; width: 34px; height: 18px; flex-shrink: 0; }
  .toggle-switch input { opacity: 0; width: 0; height: 0; }
  .toggle-track {
    position: absolute; inset: 0; cursor: pointer;
    background: var(--vscode-input-background, #3c3c3c);
    border: 1px solid var(--vscode-panel-border); border-radius: 9px;
    transition: background 0.15s;
  }
  .toggle-track::before {
    content: ""; position: absolute; height: 12px; width: 12px; left: 2px; top: 2px;
    background: var(--vscode-foreground); border-radius: 50%; transition: transform 0.15s;
  }
  .toggle-switch input:checked + .toggle-track {
    background: var(--vscode-button-background); border-color: var(--vscode-button-background);
  }
  .toggle-switch input:checked + .toggle-track::before {
    transform: translateX(16px);
    background: var(--vscode-button-foreground);
  }
  .toggle-hint { font-size: 12px; color: var(--vscode-descriptionForeground); }

  .level-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .level-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
  .level-badge {
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 2px 8px; border-radius: 3px;
  }
  .level-moderate { background: rgba(204,167,0,0.18); color: #cca700; }
  .level-high     { background: rgba(240,100,60,0.18); color: #f0643c; }
  .level-critical { background: rgba(220,50,50,0.22);  color: #e05555; }
  .level-desc { font-size: 12px; color: var(--vscode-descriptionForeground); }

  .field-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .field-row:last-child { margin-bottom: 0; }
  .field-label { font-size: 12px; min-width: 120px; flex-shrink: 0; }

  .slider-group { display: flex; align-items: center; gap: 10px; flex: 1; }
  .threshold-slider { flex: 1; accent-color: var(--vscode-button-background); cursor: pointer; }
  .slider-value { font-size: 13px; font-weight: 600; min-width: 38px; }

  .color-group { display: flex; align-items: center; gap: 8px; }
  .picker-wrapper {
    width: 34px; height: 22px; border-radius: 3px; overflow: hidden;
    border: 1px solid var(--vscode-panel-border); flex-shrink: 0;
    transition: opacity 0.15s;
  }
  .picker-wrapper.dimmed { opacity: 0.3; }
  .color-input {
    width: 46px; height: 30px; border: none; padding: 0; cursor: pointer;
    background: none; margin-top: -4px; margin-left: -6px;
  }
  .color-input:disabled { cursor: not-allowed; }
  .hex-input {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 12px; width: 72px; padding: 3px 6px;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border, var(--vscode-panel-border));
    border-radius: 3px;
  }
  .hex-input:disabled { opacity: 0.35; cursor: not-allowed; }
  .hex-input.invalid { border-color: #e05555; }
  .none-btn {
    padding: 3px 10px; border-radius: 3px;
    border: 1px solid var(--vscode-button-secondaryBorder, var(--vscode-panel-border));
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    font-family: var(--vscode-font-family); font-size: 12px; cursor: pointer;
  }
  .none-btn:hover { background: var(--vscode-button-secondaryHoverBackground); }
  .none-btn.active {
    border-color: var(--vscode-focusBorder);
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
  }

  .settings-footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
  .footer-btn {
    padding: 6px 16px; border-radius: 4px;
    font-family: var(--vscode-font-family); font-size: 12px;
    cursor: pointer; border: 1px solid transparent;
    transition: opacity 0.15s, background 0.1s;
  }
  .footer-btn:disabled { opacity: 0.38; cursor: not-allowed; }
  #resetBtn {
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    border-color: var(--vscode-button-secondaryBorder, var(--vscode-panel-border));
  }
  #resetBtn:not(:disabled):hover { background: var(--vscode-button-secondaryHoverBackground); }
  #resetBtn.dirty { background: #5a1a1a; color: #f48080; border-color: #e05555; }
  #resetBtn.dirty:hover { background: #6e1f1f; }
  #saveBtn {
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    border-color: var(--vscode-button-secondaryBorder, var(--vscode-panel-border));
  }
  #saveBtn:not(:disabled):hover { background: var(--vscode-button-secondaryHoverBackground); }
  #saveBtn.dirty {
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    border-color: var(--vscode-button-background);
  }
  #saveBtn.dirty:hover { background: var(--vscode-button-hoverBackground); }

  .org-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .org-status { font-size: 12px; margin: 0 0 10px 0; }
  .org-hint { font-size: 12px; color: var(--vscode-descriptionForeground); margin: 0 0 10px 0; }
  .org-actions { display: flex; gap: 8px; flex-wrap: wrap; }`;
}


/** Escape a value for an HTML attribute. */
function escapeAttr(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/**
 * JSON for embedding in an inline <script>: "<" becomes \u003c, so no value
 * can close the script element.
 */
export function jsonForScript(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

/**
 * Validate a draft posted by the webview before anything is written. Returns
 * null for any malformed field, so a forged message writes nothing.
 */
export function parseDraft(raw: unknown): DraftState | null {
  if (!isRecord(raw) || !isRecord(raw.thresholds) || !isRecord(raw.colors) || typeof raw.compact !== "boolean") {
    return null;
  }
  const levels: Level[] = ["moderate", "high", "critical"];
  const thresholds = { moderate: 0, high: 0, critical: 0 };
  const colors = { moderate: "", high: "", critical: "" };
  for (const level of levels) {
    const t = raw.thresholds[level];
    const c = raw.colors[level];
    if (typeof t !== "number" || validThreshold(t, -1) !== t) {
      return null;
    }
    if (typeof c !== "string" || (c !== "none" && !HEX_COLOR.test(c))) {
      return null;
    }
    thresholds[level] = t;
    colors[level] = c;
  }
  return { thresholds, colors, compact: raw.compact };
}

function levelSection(level: Level, label: string, description: string, threshold: number, color: string): string {
  // Values come from settings a workspace can set, so they are validated and
  // escaped before they reach an attribute.
  const safeThreshold = validThreshold(threshold, URGENCY_THRESHOLDS[level]);
  const isNone = color === "none";
  const pickerValue = isNone || !HEX_COLOR.test(color) ? DEFAULT_URGENCY_COLORS[level] : color;
  const hexDisplay = escapeAttr(isNone ? "" : pickerValue);
  return `
        <div class="level-section">
          <div class="level-header">
            <span class="level-badge level-${level}">${label}</span>
            <span class="level-desc">${description}</span>
          </div>
          <div class="field-row">
            <label class="field-label">Threshold</label>
            <div class="slider-group">
              <input type="range" min="1" max="99" value="${safeThreshold}" class="threshold-slider" data-level="${level}" data-input="onSlider" />
              <span class="slider-value" id="val-${level}">${safeThreshold}%</span>
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Status bar color</label>
            <div class="color-group">
              <div class="picker-wrapper${isNone ? " dimmed" : ""}" id="wrapper-${level}">
                <input type="color" class="color-input" id="picker-${level}" data-level="${level}" value="${escapeAttr(pickerValue)}" data-input="onColorPick" ${isNone ? "disabled" : ""} />
              </div>
              <input type="text" class="hex-input${isNone ? " dimmed" : ""}" id="hex-${level}" data-level="${level}" value="${hexDisplay}" placeholder="${isNone ? "none" : "#rrggbb"}" maxlength="7" data-input="onHexInput" data-blur="onHexBlur" ${isNone ? "disabled" : ""} />
              <button class="none-btn${isNone ? " active" : ""}" id="none-${level}" data-level="${level}" data-click="onNone">None</button>
            </div>
          </div>
        </div>`;
}

/** The Organization and GitHub account sections. */
function organizationSection(org: OrganizationStatus): string {
  const status = org.connected
    ? "Connected. The status bar shows the organization's shared pool."
    : org.configured
      ? "An organization is set, but no token is stored."
      : "Not connected. The status bar shows your own plan.";
  return `
        <div class="org-section">
          <h3>Organization</h3>
          <p class="org-status">${status}</p>
          <p class="org-hint">Owners and billing managers can connect a read-only fine-grained token to show the organization's AI-credit pool. The token stays in VS Code secret storage.</p>
          <div class="org-actions">
            <button class="footer-btn" data-command="connectOrganization">${org.connected ? "Reconnect" : "Connect"}</button>
            <button class="footer-btn" data-command="disconnectOrganization" ${org.configured || org.connected ? "" : "disabled"}>Disconnect</button>
          </div>
        </div>
        <div class="org-section">
          <h3>GitHub account</h3>
          <p class="org-hint">The personal figure comes from the GitHub account chosen for this extension in VS Code, whatever repository is open.</p>
          <div class="org-actions">
            <button class="footer-btn" data-command="switchAccount">Switch GitHub account</button>
          </div>
        </div>`;
}

/** The inline settings section markup (hidden by default; the dashboard gear toggles it). */
export function settingsSectionHtml(state: DraftState, org: OrganizationStatus): string {
  const { thresholds, colors, compact } = state;
  return `
      <div class="divider"></div>
      <div id="settings-section" class="settings-section" hidden>
        <h2>Settings</h2>
        <p class="settings-subtitle">Adjust thresholds, colors, and display. Click Save changes to apply.</p>

        ${organizationSection(org)}

        <div class="metric-section toggle-row">
          <span class="metric-label">Compact status bar</span>
          <label class="toggle-switch">
            <input type="checkbox" id="compact-toggle" data-change="onCompact" ${compact ? "checked" : ""}/>
            <span class="toggle-track"></span>
          </label>
          <span class="toggle-hint">Hide the "Copilot Usage: " label in the status bar</span>
        </div>

        ${levelSection("moderate", "Moderate", "First alert level", thresholds.moderate, colors.moderate)}
        ${levelSection("high", "High", "Elevated alert level", thresholds.high, colors.high)}
        ${levelSection("critical", "Critical", "Maximum alert level", thresholds.critical, colors.critical)}

        <div class="settings-footer">
          <button id="resetBtn" class="footer-btn" data-click="onReset" disabled>Reset to Defaults</button>
          <button id="saveBtn"  class="footer-btn" data-click="onSave"  disabled>Save changes</button>
        </div>
      </div>`;
}

/**
 * The settings form's client JS, meant to be concatenated into the dashboard's
 * single <script>. It does NOT call acquireVsCodeApi() or register a message
 * listener - it reuses the dashboard's `vscode` handle, and the dashboard's
 * message listener calls `applySettings` on the `loadSettings` message.
 */
export function settingsScriptJs(state: DraftState): string {
  const initialJson = jsonForScript(state);
  const defaultsJson = jsonForScript(SETTINGS_DEFAULTS);
  return `
    const HEX_RE = /^#[0-9a-fA-F]{6}$/;
    const SETTINGS_DEFAULTS = ${defaultsJson};
    let settingsOriginal = ${initialJson};
    let settingsDraft = JSON.parse(JSON.stringify(settingsOriginal));

    function settingsDirty() { return JSON.stringify(settingsDraft) !== JSON.stringify(settingsOriginal); }
    function settingsNotDefault() { return JSON.stringify(settingsDraft) !== JSON.stringify(SETTINGS_DEFAULTS); }
    function updateButtons() {
      const saveBtn = document.getElementById('saveBtn');
      const resetBtn = document.getElementById('resetBtn');
      if (!saveBtn || !resetBtn) return;
      const dirty = settingsDirty(), notDefault = settingsNotDefault();
      saveBtn.disabled = !dirty; resetBtn.disabled = !notDefault;
      saveBtn.classList.toggle('dirty', dirty); resetBtn.classList.toggle('dirty', notDefault);
    }
    function onCompact(el) { settingsDraft.compact = el.checked; updateButtons(); }
    function onSlider(el) {
      const level = el.dataset.level; const value = parseInt(el.value, 10);
      document.getElementById('val-' + level).textContent = value + '%';
      settingsDraft.thresholds[level] = value; updateButtons();
    }
    function onColorPick(el) {
      const level = el.dataset.level; const hex = el.value;
      const hexInput = document.getElementById('hex-' + level);
      hexInput.value = hex; hexInput.classList.remove('invalid');
      settingsDraft.colors[level] = hex; updateButtons();
    }
    function onHexInput(el) {
      const level = el.dataset.level; const raw = el.value.trim();
      const hex = raw.startsWith('#') ? raw : '#' + raw;
      if (HEX_RE.test(hex)) {
        el.classList.remove('invalid');
        document.getElementById('picker-' + level).value = hex;
        settingsDraft.colors[level] = hex; updateButtons();
      } else { el.classList.add('invalid'); }
    }
    function onHexBlur(el) {
      if (el.classList.contains('invalid')) {
        const level = el.dataset.level; el.value = settingsDraft.colors[level]; el.classList.remove('invalid');
      }
    }
    function onNone(btn) {
      const level = btn.dataset.level; const isNone = btn.classList.contains('active');
      const picker = document.getElementById('picker-' + level);
      const wrapper = document.getElementById('wrapper-' + level);
      const hexInp = document.getElementById('hex-' + level);
      if (isNone) {
        btn.classList.remove('active'); picker.disabled = false; hexInp.disabled = false;
        wrapper.classList.remove('dimmed'); hexInp.classList.remove('dimmed');
        hexInp.placeholder = '#rrggbb'; const restored = picker.value; hexInp.value = restored;
        settingsDraft.colors[level] = restored;
      } else {
        btn.classList.add('active'); picker.disabled = true; hexInp.disabled = true;
        wrapper.classList.add('dimmed'); hexInp.classList.add('dimmed');
        hexInp.value = ''; hexInp.placeholder = 'none'; settingsDraft.colors[level] = 'none';
      }
      updateButtons();
    }
    function onSave() { vscode.postMessage({ command: 'save', draft: JSON.parse(JSON.stringify(settingsDraft)) }); }
    function onReset() { vscode.postMessage({ command: 'reset' }); }
    function applySettings(settings) {
      const compactEl = document.getElementById('compact-toggle');
      if (compactEl) { compactEl.checked = !!settings.compact; }
      settingsDraft.compact = !!settings.compact;
      for (const level of ['moderate', 'high', 'critical']) {
        const threshold = settings.thresholds[level]; const color = settings.colors[level];
        const isNone = color === 'none';
        const slider = document.querySelector('.threshold-slider[data-level="' + level + '"]');
        slider.value = threshold; document.getElementById('val-' + level).textContent = threshold + '%';
        settingsDraft.thresholds[level] = threshold;
        const picker = document.getElementById('picker-' + level);
        const hexInp = document.getElementById('hex-' + level);
        const wrapper = document.getElementById('wrapper-' + level);
        const noneBtn = document.getElementById('none-' + level);
        if (isNone) {
          picker.disabled = true; hexInp.disabled = true;
          wrapper.classList.add('dimmed'); hexInp.classList.add('dimmed');
          hexInp.value = ''; hexInp.placeholder = 'none'; noneBtn.classList.add('active');
        } else {
          picker.disabled = false; hexInp.disabled = false;
          wrapper.classList.remove('dimmed'); hexInp.classList.remove('dimmed');
          picker.value = color; hexInp.value = color; hexInp.placeholder = '#rrggbb';
          hexInp.classList.remove('invalid'); noneBtn.classList.remove('active');
        }
        settingsDraft.colors[level] = color;
      }
      settingsOriginal = JSON.parse(JSON.stringify(settingsDraft));
      updateButtons();
    }
    // Toggle the inline settings section; persist open/closed across re-renders.
    function toggleSettings() {
      const s = document.getElementById('settings-section');
      if (!s) return;
      const willOpen = s.hasAttribute('hidden');
      if (willOpen) { s.removeAttribute('hidden'); s.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      else { s.setAttribute('hidden', ''); }
      try { const st = vscode.getState() || {}; st.settingsOpen = willOpen; vscode.setState(st); } catch (e) {}
    }
    // Every control is wired here rather than with inline handlers, which the
    // dashboard's Content-Security-Policy forbids. Only these names and these
    // commands can be reached from markup.
    const SETTINGS_HANDLERS = { onSlider, onColorPick, onHexInput, onHexBlur, onNone, onCompact, onSave, onReset, toggleSettings };
    const WEBVIEW_COMMANDS = ['refresh', 'openUsagePage', 'signIn', 'switchAccount', 'connectOrganization', 'disconnectOrganization'];
    function dispatch(attr, event) {
      const el = event.target && event.target.closest ? event.target.closest('[' + attr + ']') : null;
      if (!el) return;
      const name = el.getAttribute(attr);
      if (attr === 'data-command') {
        if (WEBVIEW_COMMANDS.indexOf(name) !== -1) vscode.postMessage({ command: name });
        return;
      }
      if (Object.prototype.hasOwnProperty.call(SETTINGS_HANDLERS, name)) SETTINGS_HANDLERS[name](el);
    }
    document.addEventListener('click', function (e) { dispatch('data-command', e); dispatch('data-click', e); });
    document.addEventListener('input', function (e) { dispatch('data-input', e); });
    document.addEventListener('change', function (e) { dispatch('data-change', e); });
    document.addEventListener('focusout', function (e) { dispatch('data-blur', e); });
    // Restore the open/closed state after a re-render.
    (function () {
      try {
        const st = vscode.getState() || {};
        if (st.settingsOpen) { const s = document.getElementById('settings-section'); if (s) s.removeAttribute('hidden'); }
      } catch (e) {}
      updateButtons();
    })();`;
}
