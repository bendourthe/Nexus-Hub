import * as vscode from "vscode";
import { DEFAULT_THRESHOLDS, type AlertMetric } from "./recommendations";

/**
 * The dashboard's INLINE settings form.
 *
 * Ported deliberately from the Claude monitor rather than reinvented: the CSS,
 * `levelSection`, the section markup, and the client script below are copied
 * byte-for-byte, because "looks the same" is a property that a reimplementation
 * drifts away from on the first divergent tweak. Only the parts that must differ
 * are rewritten - the configuration namespace, the metric options (Cursor has two
 * included pools rather than a session and a week), and the status-bar label text.
 *
 * The standalone settings webview is retained for the command that opens it, but
 * the dashboard's gear now toggles this inline form, matching the sibling monitors.
 */

type Level = "moderate" | "high" | "critical";

export const DEFAULT_URGENCY_COLORS: Record<Level, string> = {
  moderate: "#cca700",
  high: "#f0643c",
  critical: "#e05555"
};

export interface DraftState {
  metric: AlertMetric;
  thresholds: { moderate: number; high: number; critical: number };
  colors: { moderate: string; high: string; critical: string };
  compact: boolean;
}

export const SETTINGS_DEFAULTS: DraftState = {
  metric: "highest",
  thresholds: {
    moderate: DEFAULT_THRESHOLDS.moderate,
    high: DEFAULT_THRESHOLDS.high,
    critical: DEFAULT_THRESHOLDS.critical
  },
  colors: { ...DEFAULT_URGENCY_COLORS },
  compact: false
};

function config(): vscode.WorkspaceConfiguration {
  return vscode.workspace.getConfiguration("cursorUsage");
}

/** The current persisted settings, read from VS Code configuration. */
export function currentSettings(): DraftState {
  const c = config();
  return {
    metric: c.get<AlertMetric>("alertMetric", "highest"),
    thresholds: {
      moderate: c.get<number>("thresholds.moderate", DEFAULT_THRESHOLDS.moderate),
      high: c.get<number>("thresholds.high", DEFAULT_THRESHOLDS.high),
      critical: c.get<number>("thresholds.critical", DEFAULT_THRESHOLDS.critical)
    },
    colors: {
      moderate: c.get<string>("colors.moderate", DEFAULT_URGENCY_COLORS.moderate),
      high: c.get<string>("colors.high", DEFAULT_URGENCY_COLORS.high),
      critical: c.get<string>("colors.critical", DEFAULT_URGENCY_COLORS.critical)
    },
    // The dashboard's toggle drives the label, which is the setting a user actually
    // means by "hide the words"; compactStatusBar also abbreviates the pool names.
    compact: !c.get<boolean>("showStatusBarLabel", true)
  };
}

/**
 * Persist a settings draft; returns the values actually stored.
 *
 * Only CHANGED keys are written. Every `config.update` is a write to the user's
 * settings file that fires `onDidChangeConfiguration`, and the dashboard rebuilds
 * its entire webview on that event. Writing all eight keys unconditionally meant a
 * single toggle triggered eight writes and eight rebuilds, which is what made the
 * panel sit unresponsive for seconds and then appear to discard the change.
 *
 * The writes stay sequential rather than concurrent: parallel `config.update` calls
 * against the same settings file can overwrite each other.
 */
export async function saveSettings(d: DraftState): Promise<DraftState> {
  const c = config();
  const target = vscode.ConfigurationTarget.Global;
  const before = currentSettings();
  const writes: Array<[string, unknown]> = [];

  if (d.metric !== before.metric) writes.push(["alertMetric", d.metric]);
  for (const level of ["moderate", "high", "critical"] as const) {
    if (d.thresholds[level] !== before.thresholds[level]) {
      writes.push([`thresholds.${level}`, d.thresholds[level]]);
    }
    if (d.colors[level] !== before.colors[level]) {
      writes.push([`colors.${level}`, d.colors[level]]);
    }
  }
  if (d.compact !== before.compact) {
    writes.push(["showStatusBarLabel", !d.compact]);
  }

  for (const [key, value] of writes) {
    await c.update(key, value, target);
  }
  return currentSettings();
}

/** Clear all settings back to defaults; returns the defaults. */
export async function resetSettings(): Promise<DraftState> {
  const c = config();
  const target = vscode.ConfigurationTarget.Global;
  for (const key of [
    "alertMetric",
    "thresholds.moderate",
    "thresholds.high",
    "thresholds.critical",
    "colors.moderate",
    "colors.high",
    "colors.critical",
    "showStatusBarLabel"
  ]) {
    await c.update(key, undefined, target);
  }
  return { ...SETTINGS_DEFAULTS };
}

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
  .metric-select {
    flex: 1;
    background: var(--vscode-dropdown-background);
    color: var(--vscode-dropdown-foreground);
    border: 1px solid var(--vscode-dropdown-border);
    border-radius: 3px;
    padding: 4px 8px;
    font-family: var(--vscode-font-family);
    font-size: 12px;
    cursor: pointer;
  }

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
  #saveBtn.dirty:hover { background: var(--vscode-button-hoverBackground); }`;
}

function levelSection(level: Level, label: string, description: string, threshold: number, color: string): string {
  const isNone = color === "none";
  const pickerValue = isNone || !color.startsWith("#") ? DEFAULT_URGENCY_COLORS[level] : color;
  const hexDisplay = isNone ? "" : pickerValue;
  return `
        <div class="level-section">
          <div class="level-header">
            <span class="level-badge level-${level}">${label}</span>
            <span class="level-desc">${description}</span>
          </div>
          <div class="field-row">
            <label class="field-label">Threshold</label>
            <div class="slider-group">
              <input type="range" min="1" max="99" value="${threshold}" class="threshold-slider" data-level="${level}" data-settings="slider" />
              <span class="slider-value" id="val-${level}">${threshold}%</span>
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Status bar color</label>
            <div class="color-group">
              <div class="picker-wrapper${isNone ? " dimmed" : ""}" id="wrapper-${level}">
                <input type="color" class="color-input" id="picker-${level}" data-level="${level}" value="${pickerValue}" data-settings="colorpick" ${isNone ? "disabled" : ""} />
              </div>
              <input type="text" class="hex-input${isNone ? " dimmed" : ""}" id="hex-${level}" data-level="${level}" value="${hexDisplay}" placeholder="${isNone ? "none" : "#rrggbb"}" maxlength="7" data-settings="hex" ${isNone ? "disabled" : ""} />
              <button class="none-btn${isNone ? " active" : ""}" id="none-${level}" data-level="${level}" data-settings="none">None</button>
            </div>
          </div>
        </div>`;
}

/** The inline settings section markup (hidden by default; the dashboard gear toggles it). */
export function settingsSectionHtml(state: DraftState): string {
  const { metric, thresholds, colors, compact } = state;
  return `
      <div class="divider"></div>
      <div id="settings-section" class="settings-section" hidden>
        <h2>Settings</h2>
        <p class="settings-subtitle">Adjust thresholds, colors, and display. Click Save changes to apply.</p>

        <div class="metric-section">
          <label class="metric-label" for="metric-select">Apply thresholds to</label>
          <select id="metric-select" class="metric-select" data-settings="metric">
            <option value="highest" ${metric === "highest" ? "selected" : ""}>Highest (auto)</option>
            <option value="cursorModels" ${metric === "cursorModels" ? "selected" : ""}>Cursor Models</option>
            <option value="otherModels"  ${metric === "otherModels"  ? "selected" : ""}>Other Models</option>
          </select>
        </div>

        <div class="metric-section toggle-row">
          <span class="metric-label">Compact status bar</span>
          <label class="toggle-switch">
            <input type="checkbox" id="compact-toggle" data-settings="compact" ${compact ? "checked" : ""}/>
            <span class="toggle-track"></span>
          </label>
          <span class="toggle-hint">Hide the "Cursor Usage: " label in the status bar</span>
        </div>

        ${levelSection("moderate", "Moderate", "First alert level",    thresholds.moderate, colors.moderate)}
        ${levelSection("high",     "High",     "Elevated alert level", thresholds.high,     colors.high)}
        ${levelSection("critical", "Critical", "Maximum alert level",  thresholds.critical, colors.critical)}

        <div class="settings-footer">
          <button id="resetBtn" class="footer-btn" data-settings="reset" disabled>Reset to Defaults</button>
          <button id="saveBtn"  class="footer-btn" data-settings="save"  disabled>Save changes</button>
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
  const initialJson = JSON.stringify(state);
  const defaultsJson = JSON.stringify(SETTINGS_DEFAULTS);
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
    function onMetric(el) { settingsDraft.metric = el.value; updateButtons(); }
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
      document.getElementById('metric-select').value = settings.metric;
      settingsDraft.metric = settings.metric;
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
    // Restore the open/closed state after a re-render.
    (function () {
      try {
        const st = vscode.getState() || {};
        if (st.settingsOpen) { const s = document.getElementById('settings-section'); if (s) s.removeAttribute('hidden'); }
      } catch (e) {}
      updateButtons();
    })();`;
}


/**
 * Wires the settings form's controls.
 *
 * The Claude monitor attaches its handlers with inline `onchange=` / `onclick=`
 * attributes, which a nonce Content-Security-Policy blocks outright - the form would
 * render correctly and do nothing. This binds the same handlers by data attribute
 * instead, so the markup stays identical in appearance while remaining CSP-safe.
 */
export function settingsBindJs(): string {
  return `
    document.querySelectorAll('[data-settings]').forEach((el) => {
      const kind = el.getAttribute('data-settings');
      if (kind === 'metric') { el.addEventListener('change', () => onMetric(el)); }
      else if (kind === 'compact') { el.addEventListener('change', () => onCompact(el)); }
      else if (kind === 'slider') { el.addEventListener('input', () => onSlider(el)); }
      else if (kind === 'colorpick') { el.addEventListener('input', () => onColorPick(el)); }
      else if (kind === 'hex') {
        el.addEventListener('input', () => onHexInput(el));
        el.addEventListener('blur', () => onHexBlur(el));
      }
      else if (kind === 'none') { el.addEventListener('click', () => onNone(el)); }
      else if (kind === 'reset') { el.addEventListener('click', () => onReset()); }
      else if (kind === 'save') { el.addEventListener('click', () => onSave()); }
    });`;
}
