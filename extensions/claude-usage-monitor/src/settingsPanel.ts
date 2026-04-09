import * as vscode from "vscode";
import { ColorOption, getThresholdConfig, getColorConfig } from "./types";

type Level = "moderate" | "high" | "critical";

interface SettingsMessage {
  command: "updateThreshold" | "updateColor" | "resetDefaults";
  level?: Level;
  value?: number;
  color?: ColorOption;
}

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
        switch (message.command) {
          case "updateThreshold":
            if (message.level !== undefined && message.value !== undefined) {
              await config.update(
                `thresholds.${message.level}`,
                message.value,
                vscode.ConfigurationTarget.Global
              );
            }
            break;
          case "updateColor":
            if (message.level !== undefined && message.color !== undefined) {
              await config.update(
                `colors.${message.level}`,
                message.color,
                vscode.ConfigurationTarget.Global
              );
            }
            break;
          case "resetDefaults":
            await Promise.all([
              config.update("thresholds.moderate", undefined, vscode.ConfigurationTarget.Global),
              config.update("thresholds.high",     undefined, vscode.ConfigurationTarget.Global),
              config.update("thresholds.critical", undefined, vscode.ConfigurationTarget.Global),
              config.update("colors.moderate",     undefined, vscode.ConfigurationTarget.Global),
              config.update("colors.high",         undefined, vscode.ConfigurationTarget.Global),
              config.update("colors.critical",     undefined, vscode.ConfigurationTarget.Global),
            ]);
            // Reload the webview with restored defaults
            this.panel.webview.html = this.getHtml();
            break;
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
        dark: vscode.Uri.joinPath(extensionUri, "icons", "claude-light.svg"),
      };
    }

    SettingsPanel.currentPanel = new SettingsPanel(panel);
    return SettingsPanel.currentPanel;
  }

  private dispose(): void {
    SettingsPanel.currentPanel = undefined;
    this.panel.dispose();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }

  private getHtml(): string {
    const thresholds = getThresholdConfig();
    const colors = getColorConfig();

    const levelRow = (
      level: Level,
      label: string,
      description: string,
      threshold: number,
      color: ColorOption
    ): string => {
      const warnActive  = color === "warning" ? " active" : "";
      const errActive   = color === "error"   ? " active" : "";
      const noneActive  = color === "none"    ? " active" : "";
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
                type="range"
                min="1"
                max="99"
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
              <button class="color-btn warning-btn${warnActive}" data-level="${level}" data-color="warning" onclick="onColor(this)">
                <span class="color-swatch warning-swatch"></span> Warning
              </button>
              <button class="color-btn error-btn${errActive}" data-level="${level}" data-color="error" onclick="onColor(this)">
                <span class="color-swatch error-swatch"></span> Error
              </button>
              <button class="color-btn none-btn${noneActive}" data-level="${level}" data-color="none" onclick="onColor(this)">
                <span class="color-swatch none-swatch"></span> None
              </button>
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
    max-width: 600px;
  }

  h1 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 6px;
    color: var(--vscode-foreground);
  }

  .subtitle {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    margin-bottom: 28px;
  }

  .level-section {
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
    background: var(--vscode-editor-background);
  }

  .level-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .level-badge {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 3px;
  }

  .level-moderate { background: rgba(204,167,0,0.18); color: #cca700; }
  .level-high     { background: rgba(240,100,60,0.18); color: #f0643c; }
  .level-critical { background: rgba(220,50,50,0.22);  color: #e05555; }

  .level-desc {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }

  .field-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .field-row:last-child { margin-bottom: 0; }

  .field-label {
    font-size: 12px;
    color: var(--vscode-foreground);
    min-width: 120px;
    flex-shrink: 0;
  }

  .slider-group {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
  }

  .threshold-slider {
    flex: 1;
    accent-color: var(--vscode-button-background);
    cursor: pointer;
    height: 4px;
  }

  .slider-value {
    font-size: 13px;
    font-weight: 600;
    min-width: 38px;
    color: var(--vscode-foreground);
  }

  .color-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .color-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 4px;
    border: 1px solid var(--vscode-button-secondaryBorder, var(--vscode-panel-border));
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    font-family: var(--vscode-font-family);
    font-size: 12px;
    cursor: pointer;
    transition: border-color 0.1s, background 0.1s;
  }

  .color-btn:hover {
    background: var(--vscode-button-secondaryHoverBackground);
  }

  .color-btn.active {
    border-color: var(--vscode-focusBorder);
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
  }

  .color-swatch {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .warning-swatch { background: #cca700; }
  .error-swatch   { background: #e05555; }
  .none-swatch    { background: var(--vscode-panel-border); }

  .footer {
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
  }

  .reset-btn {
    padding: 6px 16px;
    border-radius: 4px;
    border: 1px solid var(--vscode-button-secondaryBorder, var(--vscode-panel-border));
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    font-family: var(--vscode-font-family);
    font-size: 12px;
    cursor: pointer;
  }

  .reset-btn:hover {
    background: var(--vscode-button-secondaryHoverBackground);
  }
</style>
</head>
<body>
<h1>Claude Usage Settings</h1>
<p class="subtitle">Configure urgency thresholds and status bar highlight colors. Changes take effect immediately.</p>

${levelRow("moderate", "Moderate", "First alert level", thresholds.moderate, colors.moderate)}
${levelRow("high",     "High",     "Elevated alert level", thresholds.high, colors.high)}
${levelRow("critical", "Critical", "Maximum alert level", thresholds.critical, colors.critical)}

<div class="footer">
  <button class="reset-btn" onclick="onReset()">Reset to Defaults</button>
</div>

<script>
  const vscode = acquireVsCodeApi();

  function send(msg) {
    vscode.postMessage(msg);
  }

  function onSlider(el) {
    const level = el.dataset.level;
    const value = parseInt(el.value, 10);
    document.getElementById('val-' + level).textContent = value + '%';
    send({ command: 'updateThreshold', level, value });
  }

  function onColor(el) {
    const level = el.dataset.level;
    const color = el.dataset.color;

    // Update active state within this level's color group
    el.closest('.color-group').querySelectorAll('.color-btn').forEach(function(btn) {
      btn.classList.remove('active');
    });
    el.classList.add('active');

    send({ command: 'updateColor', level, color });
  }

  function onReset() {
    send({ command: 'resetDefaults' });
  }
</script>
</body>
</html>`;
  }
}
