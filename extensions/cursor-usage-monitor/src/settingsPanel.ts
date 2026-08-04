import * as vscode from "vscode";
import type { AlertMetric, Thresholds } from "./recommendations";
import { DEFAULT_THRESHOLDS } from "./recommendations";
import { renderWebviewDocument } from "./webview";

export interface SettingsDraft {
  refreshInterval: number;
  alertMetric: AlertMetric;
  thresholds: Thresholds;
  compactStatusBar: boolean;
}

export const SETTINGS_DEFAULTS: SettingsDraft = {
  refreshInterval: 10,
  alertMetric: "highest",
  thresholds: { ...DEFAULT_THRESHOLDS },
  compactStatusBar: false
};

const SETTING_KEYS = [
  "refreshInterval",
  "alertMetric",
  "thresholds.moderate",
  "thresholds.high",
  "thresholds.critical",
  "compactStatusBar"
] as const;

type SettingKey = (typeof SETTING_KEYS)[number];

export const SETTINGS_UPDATE_ERROR =
  "Settings could not be updated. Previous settings were restored where possible.";

export class SettingsPanel {
  private panel: vscode.WebviewPanel | undefined;

  public show(): void {
    if (this.panel === undefined) {
      this.panel = vscode.window.createWebviewPanel(
        "cursorUsageSettings",
        "Cursor Usage Settings",
        vscode.ViewColumn.One,
        { enableScripts: true }
      );
      this.panel.onDidDispose(() => {
        this.panel = undefined;
      });
      this.panel.webview.onDidReceiveMessage(
        async (message: { command?: string; draft?: unknown }) => {
          if (message.command === "save") {
            const errors = validateSettings(message.draft);
            if (errors.length > 0) {
              await this.postValidationError(errors);
              return;
            }
            try {
              const saved = await saveSettings(
                message.draft as SettingsDraft
              );
              await this.panel?.webview.postMessage({
                command: "settingsSaved",
                settings: saved
              });
            } catch {
              await this.postValidationError([SETTINGS_UPDATE_ERROR]);
            }
          } else if (message.command === "reset") {
            try {
              const reset = await resetSettings();
              await this.panel?.webview.postMessage({
                command: "settingsSaved",
                settings: reset
              });
            } catch {
              await this.postValidationError([SETTINGS_UPDATE_ERROR]);
            }
          }
        }
      );
    }
    this.panel.webview.html = renderSettings(readSettings());
    this.panel.reveal();
  }

  public update(): void {
    if (this.panel !== undefined) {
      this.panel.webview.html = renderSettings(readSettings());
    }
  }

  public dispose(): void {
    this.panel?.dispose();
    this.panel = undefined;
  }

  private async postValidationError(errors: string[]): Promise<void> {
    await this.panel?.webview.postMessage({
      command: "validationError",
      errors
    });
  }
}

export function readSettings(): SettingsDraft {
  const config = vscode.workspace.getConfiguration("cursorUsage");
  const candidate: SettingsDraft = {
    refreshInterval: config.get(
      "refreshInterval",
      SETTINGS_DEFAULTS.refreshInterval
    ),
    alertMetric: normalizeAlertMetric(
      config.get("alertMetric", SETTINGS_DEFAULTS.alertMetric)
    ),
    thresholds: {
      moderate: config.get(
        "thresholds.moderate",
        SETTINGS_DEFAULTS.thresholds.moderate
      ),
      high: config.get(
        "thresholds.high",
        SETTINGS_DEFAULTS.thresholds.high
      ),
      critical: config.get(
        "thresholds.critical",
        SETTINGS_DEFAULTS.thresholds.critical
      )
    },
    compactStatusBar: config.get(
      "compactStatusBar",
      SETTINGS_DEFAULTS.compactStatusBar
    )
  };
  return validateSettings(candidate).length === 0
    ? candidate
    : cloneDefaults();
}

export function validateSettings(value: unknown): string[] {
  if (!isRecord(value)) {
    return ["Settings must be an object."];
  }

  const thresholds = value.thresholds;
  const errors: string[] = [];
  if (
    typeof value.refreshInterval !== "number" ||
    !Number.isFinite(value.refreshInterval) ||
    value.refreshInterval < 1 ||
    value.refreshInterval > 120
  ) {
    errors.push("Refresh interval must be from 1 to 120 minutes.");
  }
  if (!isAlertMetric(value.alertMetric)) {
    errors.push("Alert metric must be Highest, Cursor Models, or Other Models.");
  }
  if (typeof value.compactStatusBar !== "boolean") {
    errors.push("Compact status bar must be enabled or disabled.");
  }
  if (!isRecord(thresholds)) {
    errors.push("Thresholds must be provided.");
  } else {
    const values = [
      thresholds.moderate,
      thresholds.high,
      thresholds.critical
    ];
    if (
      !values.every(
        (threshold) =>
          typeof threshold === "number" &&
          Number.isFinite(threshold) &&
          threshold >= 1 &&
          threshold <= 100
      )
    ) {
      errors.push("Thresholds must be numbers from 1 to 100.");
    } else if (
      !(
        (thresholds.moderate as number) < (thresholds.high as number) &&
        (thresholds.high as number) < (thresholds.critical as number)
      )
    ) {
      errors.push(
        "Thresholds must increase from moderate to high to critical."
      );
    }
  }
  return errors;
}

export async function saveSettings(
  draft: SettingsDraft
): Promise<SettingsDraft> {
  const errors = validateSettings(draft);
  if (errors.length > 0) {
    throw new TypeError(errors.join(" "));
  }
  await updateSettings([
    ["refreshInterval", draft.refreshInterval],
    ["alertMetric", draft.alertMetric],
    ["thresholds.moderate", draft.thresholds.moderate],
    ["thresholds.high", draft.thresholds.high],
    ["thresholds.critical", draft.thresholds.critical],
    ["compactStatusBar", draft.compactStatusBar]
  ]);
  return readSettings();
}

export async function resetSettings(): Promise<SettingsDraft> {
  await updateSettings(SETTING_KEYS.map((key) => [key, undefined]));
  return cloneDefaults();
}

async function updateSettings(
  updates: ReadonlyArray<readonly [SettingKey, unknown]>
): Promise<void> {
  const config = vscode.workspace.getConfiguration("cursorUsage");
  const previous = new Map(
    updates.map(([key]) => [key, config.inspect<unknown>(key)?.globalValue])
  );
  const attempted: SettingKey[] = [];

  try {
    for (const [key, value] of updates) {
      attempted.push(key);
      await config.update(key, value, vscode.ConfigurationTarget.Global);
    }
  } catch (error) {
    for (const key of attempted.reverse()) {
      try {
        await config.update(
          key,
          previous.get(key),
          vscode.ConfigurationTarget.Global
        );
      } catch {
        // Rollback is best effort; the original update failure remains primary.
      }
    }
    throw error;
  }
}

export function renderSettings(
  values: SettingsDraft,
  nonce?: string
): string {
  const option = (value: AlertMetric, label: string): string =>
    `<option value="${value}"${values.alertMetric === value ? " selected" : ""}>${label}</option>`;
  const threshold = (key: keyof Thresholds, label: string): string =>
    `<label for="threshold-${key}">${label}<input id="threshold-${key}" name="${key}" type="number" min="1" max="100" value="${values.thresholds[key]}"></label>`;
  const body = `<main>
    <h1>Cursor Usage Settings</h1>
    <p class="note">Settings affect local display and alerts only. Live transport remains disabled until runtime wiring is explicitly enabled.</p>
    <form id="settings-form">
      <fieldset>
        <legend>Refresh and display</legend>
        <label for="refresh">Refresh interval (minutes)<input id="refresh" type="number" min="1" max="120" value="${values.refreshInterval}"></label>
        <label for="metric">Apply thresholds to<select id="metric">${option("highest", "Highest (automatic)")}${option("cursorModels", "Cursor Models")}${option("otherModels", "Other Models")}</select></label>
        <label class="checkbox" for="compact"><input id="compact" type="checkbox"${values.compactStatusBar ? " checked" : ""}>Compact status bar</label>
      </fieldset>
      <fieldset>
        <legend>Thresholds</legend>
        ${threshold("moderate", "Moderate")}
        ${threshold("high", "High")}
        ${threshold("critical", "Critical")}
      </fieldset>
      <div id="validation" role="alert" aria-live="polite"></div>
      <div class="actions">
        <button type="submit">Save changes</button>
        <button type="button" class="secondary" data-command="reset">Reset defaults</button>
      </div>
    </form>
  </main>`;
  const script = `const vscode = acquireVsCodeApi();
    const form = document.getElementById('settings-form');
    const validation = document.getElementById('validation');
    const value = (id) => document.getElementById(id).value;
    const collect = () => ({
      refreshInterval: Number(value('refresh')),
      alertMetric: value('metric'),
      thresholds: {
        moderate: Number(value('threshold-moderate')),
        high: Number(value('threshold-high')),
        critical: Number(value('threshold-critical'))
      },
      compactStatusBar: document.getElementById('compact').checked
    });
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      vscode.postMessage({ command: 'save', draft: collect() });
    });
    document.querySelector('[data-command="reset"]').addEventListener('click', () => {
      vscode.postMessage({ command: 'reset' });
    });
    window.addEventListener('message', (event) => {
      if (event.data.command === 'validationError') {
        validation.textContent = event.data.errors.join(' ');
      } else if (event.data.command === 'settingsSaved') {
        validation.textContent = 'Settings saved.';
      }
    });`;
  return renderWebviewDocument({
    body,
    styles: settingsStyles(),
    script,
    ...(nonce === undefined ? {} : { nonce })
  });
}

function settingsStyles(): string {
  return `:root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);font:13px/1.5 var(--vscode-font-family)}main{max-width:720px;margin:0 auto;padding:28px}h1{font-size:26px}fieldset{border:1px solid var(--vscode-widget-border);margin:18px 0;padding:16px}legend{font-weight:700}label{display:grid;grid-template-columns:220px 1fr;gap:12px;margin:10px 0;align-items:center}.checkbox{grid-template-columns:auto 1fr;justify-content:start}input,select{padding:6px;color:var(--vscode-input-foreground);background:var(--vscode-input-background);border:1px solid var(--vscode-input-border);font:inherit}.note{color:var(--vscode-descriptionForeground)}#validation{min-height:1.5em;color:var(--vscode-errorForeground)}.actions{display:flex;gap:8px}button{padding:7px 12px;border:1px solid transparent;color:var(--vscode-button-foreground);background:var(--vscode-button-background);font:inherit}button.secondary{color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground)}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--vscode-focusBorder);outline-offset:2px}@media(max-width:560px){label{grid-template-columns:1fr}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}@media(forced-colors:active){fieldset,input,select,button{border-color:CanvasText}}`;
}

function normalizeAlertMetric(value: unknown): AlertMetric {
  return isAlertMetric(value) ? value : SETTINGS_DEFAULTS.alertMetric;
}

function isAlertMetric(value: unknown): value is AlertMetric {
  return (
    value === "highest" ||
    value === "cursorModels" ||
    value === "otherModels"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function cloneDefaults(): SettingsDraft {
  return {
    ...SETTINGS_DEFAULTS,
    thresholds: { ...SETTINGS_DEFAULTS.thresholds }
  };
}
