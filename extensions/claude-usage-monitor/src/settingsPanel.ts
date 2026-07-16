import * as vscode from "vscode";
import {
  getThresholdConfig,
  getColorConfig,
  getThresholdMetric,
  DEFAULT_URGENCY_COLORS,
  URGENCY_THRESHOLDS,
  syncColorsToWorkbench,
  ColorConfig,
  ThresholdMetric,
} from "./types";
import { getConfiguredProviderId } from "./providers";

type Level = "moderate" | "high" | "critical";

interface DraftState {
  metric: ThresholdMetric;
  thresholds: { moderate: number; high: number; critical: number };
  colors: { moderate: string; high: string; critical: string };
}

interface SettingsMessage {
  command: "save" | "reset" | "setProvider";
  draft?: DraftState;
  provider?: string;
}

const FACTORY_DEFAULTS: DraftState = {
  metric: "highest",
  thresholds: { moderate: URGENCY_THRESHOLDS.moderate, high: URGENCY_THRESHOLDS.high, critical: URGENCY_THRESHOLDS.critical },
  colors: { moderate: DEFAULT_URGENCY_COLORS.moderate, high: DEFAULT_URGENCY_COLORS.high, critical: DEFAULT_URGENCY_COLORS.critical },
};

export class SettingsPanel {
  private static currentPanel: SettingsPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel) {
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

    this.panel.webview.onDidReceiveMessage(
      async (message: SettingsMessage) => {
        const config = vscode.workspace.getConfiguration("claudeUsage");
        const target = vscode.ConfigurationTarget.Global;

        if (message.command === "setProvider" && message.provider) {
          // Provider lives in the usageMonitor namespace and applies immediately
          // (independent of the threshold/color draft save flow).
          await vscode.workspace
            .getConfiguration("usageMonitor")
            .update("provider", message.provider, target);
          return;
        }

        if (message.command === "save" && message.draft) {
          const d = message.draft;
          // Sequential writes to avoid race conditions — concurrent config.update()
          // calls can overwrite each other when modifying the same settings file.
          await config.update("thresholdMetric",     d.metric,              target);
          await config.update("thresholds.moderate", d.thresholds.moderate, target);
          await config.update("thresholds.high",     d.thresholds.high,     target);
          await config.update("thresholds.critical", d.thresholds.critical, target);
          await config.update("colors.moderate",     d.colors.moderate,     target);
          await config.update("colors.high",         d.colors.high,         target);
          await config.update("colors.critical",     d.colors.critical,     target);
          await syncColorsToWorkbench(d.colors as ColorConfig);

          // Confirm persisted values back to the webview so it shows actual state
          const persisted: DraftState = {
            metric: getThresholdMetric(),
            thresholds: getThresholdConfig(),
            colors: getColorConfig(),
          };
          this.panel.webview.postMessage({ command: "loadSettings", settings: persisted });
        }

        if (message.command === "reset") {
          await config.update("thresholdMetric",     undefined, target);
          await config.update("thresholds.moderate", undefined, target);
          await config.update("thresholds.high",     undefined, target);
          await config.update("thresholds.critical", undefined, target);
          await config.update("colors.moderate",     undefined, target);
          await config.update("colors.high",         undefined, target);
          await config.update("colors.critical",     undefined, target);
          await syncColorsToWorkbench(FACTORY_DEFAULTS.colors as ColorConfig);
          this.panel.webview.postMessage({ command: "loadSettings", settings: FACTORY_DEFAULTS });
        }
      },
      null,
      this.disposables
    );

    this.panel.webview.html = this.getHtml();
  }

  static show(extensionUri?: vscode.Uri): SettingsPanel {
    if (SettingsPanel.currentPanel) {
      SettingsPanel.currentPanel.panel.webview.html = SettingsPanel.currentPanel.getHtml();
      SettingsPanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      return SettingsPanel.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      "claudeUsageSettings",
      "Claude Usage: Settings",
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );

    if (extensionUri) {
      panel.iconPath = {
        light: vscode.Uri.joinPath(extensionUri, "icons", "claude-dark.svg"),
        dark:  vscode.Uri.joinPath(extensionUri, "icons", "claude-light.svg"),
      };
    }

    SettingsPanel.currentPanel = new SettingsPanel(panel);
    return SettingsPanel.currentPanel;
  }

  private dispose(): void {
    SettingsPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) { d.dispose(); }
    this.disposables = [];
  }

  private getHtml(): string {
    const thresholds = getThresholdConfig();
    const colors = getColorConfig();
    const metric = getThresholdMetric();
    const provider = getConfiguredProviderId();

    const initialJson = JSON.stringify({
      metric,
      thresholds,
      colors,
    });

    const defaultsJson = JSON.stringify(FACTORY_DEFAULTS);

    const levelSection = (
      level: Level,
      label: string,
      description: string,
      threshold: number,
      color: string
    ): string => {
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
              <input
                type="range" min="1" max="99"
                value="${threshold}"
                class="threshold-slider"
                data-level="${level}"
                oninput="onSlider(this)"
              />
              <span class="slider-value" id="val-${level}">${threshold}%</span>
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Status bar color</label>
            <div class="color-group">
              <div class="picker-wrapper${isNone ? " dimmed" : ""}" id="wrapper-${level}">
                <input
                  type="color"
                  class="color-input"
                  id="picker-${level}"
                  data-level="${level}"
                  value="${pickerValue}"
                  oninput="onColorPick(this)"
                  ${isNone ? "disabled" : ""}
                />
              </div>
              <input
                type="text"
                class="hex-input${isNone ? " dimmed" : ""}"
                id="hex-${level}"
                data-level="${level}"
                value="${hexDisplay}"
                placeholder="${isNone ? "none" : "#rrggbb"}"
                maxlength="7"
                oninput="onHexInput(this)"
                onblur="onHexBlur(this)"
                ${isNone ? "disabled" : ""}
              />
              <button
                class="none-btn${isNone ? " active" : ""}"
                id="none-${level}"
                data-level="${level}"
                onclick="onNone(this)"
              >None</button>
            </div>
          </div>
        </div>`;
    };

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Usage Settings</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    color: var(--vscode-foreground);
    background: var(--vscode-editor-background);
    padding: 24px;
    max-width: 620px;
  }

  h1 { font-size: 18px; font-weight: 600; margin-bottom: 6px; }

  .subtitle {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    margin-bottom: 24px;
  }

  /* Metric selector */
  .metric-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .metric-label {
    font-size: 12px;
    white-space: nowrap;
  }

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

  /* Level sections */
  .level-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
  }

  .level-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .level-badge {
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    padding: 2px 8px; border-radius: 3px;
  }
  .level-moderate { background: rgba(204,167,0,0.18); color: #cca700; }
  .level-high     { background: rgba(240,100,60,0.18); color: #f0643c; }
  .level-critical { background: rgba(220,50,50,0.22);  color: #e05555; }

  .level-desc { font-size: 12px; color: var(--vscode-descriptionForeground); }

  .field-row {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 12px;
  }
  .field-row:last-child { margin-bottom: 0; }

  .field-label { font-size: 12px; min-width: 120px; flex-shrink: 0; }

  /* Slider */
  .slider-group { display: flex; align-items: center; gap: 10px; flex: 1; }
  .threshold-slider { flex: 1; accent-color: var(--vscode-button-background); cursor: pointer; }
  .slider-value { font-size: 13px; font-weight: 600; min-width: 38px; }

  /* Color row */
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
    font-size: 12px;
    width: 72px;
    padding: 3px 6px;
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

  /* Footer buttons */
  .footer {
    display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px;
  }

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
  #resetBtn.dirty {
    background: #5a1a1a;
    color: #f48080;
    border-color: #e05555;
  }
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
</style>
</head>
<body>
<h1>Claude Usage Settings</h1>
<p class="subtitle">Adjust thresholds and colors. Click <strong>Save changes</strong> to apply.</p>

<div class="metric-section">
  <label class="metric-label" for="provider-select">Provider</label>
  <select id="provider-select" class="metric-select" onchange="onProvider(this)">
    <option value="claude" ${provider === "claude" ? "selected" : ""}>Claude (Anthropic)</option>
    <option value="codex" ${provider === "codex" ? "selected" : ""}>Codex (ChatGPT)</option>
  </select>
</div>

<div class="metric-section">
  <label class="metric-label" for="metric-select">Apply thresholds to</label>
  <select id="metric-select" class="metric-select" onchange="onMetric(this)">
    <option value="highest" ${metric === "highest" ? "selected" : ""}>Highest (auto)</option>
    <option value="session" ${metric === "session" ? "selected" : ""}>Current Session</option>
    <option value="weekly"  ${metric === "weekly"  ? "selected" : ""}>Weekly</option>
  </select>
</div>

${levelSection("moderate", "Moderate", "First alert level",    thresholds.moderate, colors.moderate)}
${levelSection("high",     "High",     "Elevated alert level", thresholds.high,     colors.high)}
${levelSection("critical", "Critical", "Maximum alert level",  thresholds.critical, colors.critical)}

<div class="footer">
  <button id="resetBtn" class="footer-btn" onclick="onReset()" disabled>Reset to Defaults</button>
  <button id="saveBtn"  class="footer-btn" onclick="onSave()"  disabled>Save changes</button>
</div>

<script>
  const vscode = acquireVsCodeApi();
  const HEX_RE = /^#[0-9a-fA-F]{6}$/;

  const DEFAULTS = ${defaultsJson};
  const original = ${initialJson};
  // Deep copy
  let draft = JSON.parse(JSON.stringify(original));

  function isDirty() {
    return JSON.stringify(draft) !== JSON.stringify(original);
  }

  function isNotDefault() {
    return JSON.stringify(draft) !== JSON.stringify(DEFAULTS);
  }

  function updateButtons() {
    const hasDraft   = isDirty();
    const notDefault = isNotDefault();
    const saveBtn  = document.getElementById('saveBtn');
    const resetBtn = document.getElementById('resetBtn');

    saveBtn.disabled  = !hasDraft;
    resetBtn.disabled = !notDefault;
    saveBtn.classList.toggle('dirty',  hasDraft);
    resetBtn.classList.toggle('dirty', notDefault);
  }

  // --- Provider (applies immediately, independent of the save draft) ---
  function onProvider(el) {
    vscode.postMessage({ command: 'setProvider', provider: el.value });
  }

  // --- Metric ---
  function onMetric(el) {
    draft.metric = el.value;
    updateButtons();
  }

  // --- Threshold slider ---
  function onSlider(el) {
    const level = el.dataset.level;
    const value = parseInt(el.value, 10);
    document.getElementById('val-' + level).textContent = value + '%';
    draft.thresholds[level] = value;
    updateButtons();
  }

  // --- Color picker (swatch) ---
  function onColorPick(el) {
    const level = el.dataset.level;
    const hex   = el.value;
    const hexInput = document.getElementById('hex-' + level);
    hexInput.value = hex;
    hexInput.classList.remove('invalid');
    draft.colors[level] = hex;
    updateButtons();
  }

  // --- Hex text input (live) ---
  function onHexInput(el) {
    const level = el.dataset.level;
    const raw   = el.value.trim();
    const hex   = raw.startsWith('#') ? raw : '#' + raw;
    if (HEX_RE.test(hex)) {
      el.classList.remove('invalid');
      document.getElementById('picker-' + level).value = hex;
      draft.colors[level] = hex;
      updateButtons();
    } else {
      el.classList.add('invalid');
    }
  }

  // --- Hex blur: restore if still invalid ---
  function onHexBlur(el) {
    if (el.classList.contains('invalid')) {
      const level = el.dataset.level;
      el.value = draft.colors[level];
      el.classList.remove('invalid');
    }
  }

  // --- None toggle ---
  function onNone(btn) {
    const level   = btn.dataset.level;
    const isNone  = btn.classList.contains('active');
    const picker  = document.getElementById('picker-' + level);
    const wrapper = document.getElementById('wrapper-' + level);
    const hexInp  = document.getElementById('hex-' + level);

    if (isNone) {
      // Re-enable color
      btn.classList.remove('active');
      picker.disabled = false;
      hexInp.disabled = false;
      wrapper.classList.remove('dimmed');
      hexInp.classList.remove('dimmed');
      hexInp.placeholder = '#rrggbb';
      const restored = picker.value;
      hexInp.value    = restored;
      draft.colors[level] = restored;
    } else {
      // Disable (none)
      btn.classList.add('active');
      picker.disabled = true;
      hexInp.disabled = true;
      wrapper.classList.add('dimmed');
      hexInp.classList.add('dimmed');
      hexInp.value       = '';
      hexInp.placeholder = 'none';
      draft.colors[level] = 'none';
    }
    updateButtons();
  }

  // --- Save ---
  function onSave() {
    vscode.postMessage({ command: 'save', draft: JSON.parse(JSON.stringify(draft)) });
    // Extension will postMessage back with { command: 'loadSettings', settings: ... }
    // to confirm persisted values — do not optimistically mark as clean here.
  }

  // --- Reset ---
  function onReset() {
    vscode.postMessage({ command: 'reset' });
    // Extension will postMessage back with { command: 'loadSettings', settings: DEFAULTS }
  }

  // --- Apply settings to DOM (used by loadSettings message from extension) ---
  function applySettings(settings) {
    // Metric selector
    document.getElementById('metric-select').value = settings.metric;
    draft.metric = settings.metric;

    for (const level of ['moderate', 'high', 'critical']) {
      const threshold = settings.thresholds[level];
      const color     = settings.colors[level];
      const isNone    = color === 'none';

      // Slider + readout
      const slider = document.querySelector('.threshold-slider[data-level="' + level + '"]');
      slider.value = threshold;
      document.getElementById('val-' + level).textContent = threshold + '%';
      draft.thresholds[level] = threshold;

      // Color controls
      const picker  = document.getElementById('picker-'  + level);
      const hexInp  = document.getElementById('hex-'     + level);
      const wrapper = document.getElementById('wrapper-' + level);
      const noneBtn = document.getElementById('none-'    + level);

      if (isNone) {
        picker.disabled = true;
        hexInp.disabled = true;
        wrapper.classList.add('dimmed');
        hexInp.classList.add('dimmed');
        hexInp.value       = '';
        hexInp.placeholder = 'none';
        noneBtn.classList.add('active');
      } else {
        picker.disabled = false;
        hexInp.disabled = false;
        wrapper.classList.remove('dimmed');
        hexInp.classList.remove('dimmed');
        picker.value       = color;
        hexInp.value       = color;
        hexInp.placeholder = '#rrggbb';
        hexInp.classList.remove('invalid');
        noneBtn.classList.remove('active');
      }
      draft.colors[level] = color;
    }

    // Mark as clean so buttons disable
    Object.assign(original, JSON.parse(JSON.stringify(draft)));
    updateButtons();
  }

  // --- Receive messages from the extension ---
  window.addEventListener('message', event => {
    const msg = event.data;
    if (msg.command === 'loadSettings') {
      applySettings(msg.settings);
    }
  });

  // Set initial button states based on whether current settings differ from defaults
  updateButtons();
</script>
</body>
</html>`;
  }
}
