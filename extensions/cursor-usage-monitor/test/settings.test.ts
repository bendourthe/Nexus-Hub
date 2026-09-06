import { afterEach, describe, expect, it } from "vitest";
import {
  readSettings,
  renderSettings,
  resetSettings,
  saveSettings,
  SETTINGS_DEFAULTS,
  SETTINGS_UPDATE_ERROR,
  SettingsPanel,
  validateSettings,
  type SettingsDraft
} from "../src/settingsPanel";
import {
  configurationUpdates,
  failConfigurationUpdate,
  maximumConcurrentUpdates,
  resetVscodeStub,
  setConfiguration,
  webviewPanels
} from "./vscode-stub";

const draft: SettingsDraft = {
  refreshInterval: 15,
  alertMetric: "otherModels",
  thresholds: { moderate: 45, high: 70, critical: 90 },
  compactStatusBar: true
};

const priorDraft: SettingsDraft = {
  refreshInterval: 25,
  alertMetric: "cursorModels",
  thresholds: { moderate: 40, high: 65, critical: 85 },
  compactStatusBar: false
};

afterEach(() => resetVscodeStub());

describe("settings persistence and validation", () => {
  it("preserves the established defaults", () => {
    expect(SETTINGS_DEFAULTS).toEqual({
      refreshInterval: 10,
      alertMetric: "highest",
      thresholds: { moderate: 50, high: 75, critical: 95 },
      compactStatusBar: false
    });
    expect(readSettings()).toEqual(SETTINGS_DEFAULTS);
  });

  it("validates ranges, ordering, metrics, and booleans", () => {
    expect(validateSettings(draft)).toEqual([]);
    expect(validateSettings(null)).toContain("Settings must be an object.");
    expect(
      validateSettings({
        ...draft,
        refreshInterval: 0,
        alertMetric: "team",
        compactStatusBar: "yes",
        thresholds: { moderate: 80, high: 60, critical: 90 }
      })
    ).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Refresh interval"),
        expect.stringContaining("Alert metric"),
        expect.stringContaining("Compact status"),
        expect.stringContaining("increase")
      ])
    );
  });

  it("writes every setting globally and sequentially", async () => {
    const saved = await saveSettings(draft);
    expect(saved).toEqual(draft);
    expect(configurationUpdates).toHaveLength(6);
    expect(configurationUpdates.map((entry) => entry.key)).toEqual([
      "refreshInterval",
      "alertMetric",
      "thresholds.moderate",
      "thresholds.high",
      "thresholds.critical",
      "compactStatusBar"
    ]);
    expect(configurationUpdates.every((entry) => entry.target === 1)).toBe(
      true
    );
    expect(maximumConcurrentUpdates).toBe(1);
  });

  it("rejects invalid saves before writing and resets sequentially", async () => {
    await expect(
      saveSettings({ ...draft, refreshInterval: 1000 })
    ).rejects.toThrow("Refresh interval");
    expect(configurationUpdates).toHaveLength(0);

    await saveSettings(draft);
    configurationUpdates.length = 0;
    expect(await resetSettings()).toEqual(SETTINGS_DEFAULTS);
    expect(configurationUpdates).toHaveLength(6);
    expect(configurationUpdates.every((entry) => entry.value === undefined))
      .toBe(true);
    expect(maximumConcurrentUpdates).toBe(1);
  });

  it("falls back safely from corrupt persisted values", () => {
    setConfiguration("cursorUsage.alertMetric", "team");
    expect(readSettings()).toEqual(SETTINGS_DEFAULTS);
  });

  it("rolls back partial saves and resets when a sequential update fails", async () => {
    await saveSettings(priorDraft);
    configurationUpdates.length = 0;

    failConfigurationUpdate("cursorUsage.thresholds.high");
    await expect(saveSettings(draft)).rejects.toThrow();
    expect(readSettings()).toEqual(priorDraft);
    expect(configurationUpdates.map((entry) => entry.key)).toEqual([
      "refreshInterval",
      "alertMetric",
      "thresholds.moderate",
      "thresholds.high",
      "thresholds.moderate",
      "alertMetric",
      "refreshInterval"
    ]);
    expect(maximumConcurrentUpdates).toBe(1);

    configurationUpdates.length = 0;
    failConfigurationUpdate("cursorUsage.thresholds.high");
    await expect(resetSettings()).rejects.toThrow();
    expect(readSettings()).toEqual(priorDraft);
    expect(configurationUpdates.map((entry) => entry.key)).toEqual([
      "refreshInterval",
      "alertMetric",
      "thresholds.moderate",
      "thresholds.high",
      "thresholds.moderate",
      "alertMetric",
      "refreshInterval"
    ]);
    expect(maximumConcurrentUpdates).toBe(1);
  });
});

describe("settings renderer and panel", () => {
  it("renders editable accessible fields with strict CSP and no inline handlers", () => {
    const html = renderSettings(draft, "settings-nonce");
    expect(html).toContain('value="otherModels" selected');
    expect(html).toContain('id="compact" type="checkbox" checked');
    expect(html).not.toContain("Status colors");
    expect(html).not.toContain("color-moderate");
    expect(html).toContain("role=\"alert\"");
    expect(html).toContain(":focus-visible");
    expect(html).toContain("@media(forced-colors:active)");
    expect(html).toContain(
      "style-src 'nonce-settings-nonce'; script-src 'nonce-settings-nonce'"
    );
    expect(html).not.toContain("'unsafe-inline'");
    expect(html).not.toContain("onclick=");
  });

  it("reuses its panel and reports validation or saved state", async () => {
    const panel = new SettingsPanel();
    panel.show();
    panel.show();
    expect(webviewPanels).toHaveLength(1);

    await webviewPanels[0]?.webview.dispatch({
      command: "save",
      draft: { ...draft, refreshInterval: 0 }
    });
    expect(webviewPanels[0]?.webview.postedMessages[0]).toMatchObject({
      command: "validationError"
    });
    expect(configurationUpdates).toHaveLength(0);

    await webviewPanels[0]?.webview.dispatch({
      command: "save",
      draft
    });
    expect(webviewPanels[0]?.webview.postedMessages[1]).toMatchObject({
      command: "settingsSaved",
      settings: draft
    });
    panel.dispose();
  });

  it("reports fixed safe errors and restores settings after save or reset failures", async () => {
    await saveSettings(priorDraft);
    configurationUpdates.length = 0;
    const panel = new SettingsPanel();
    panel.show();

    failConfigurationUpdate("cursorUsage.thresholds.high");
    await webviewPanels[0]?.webview.dispatch({
      command: "save",
      draft
    });
    expect(webviewPanels[0]?.webview.postedMessages[0]).toEqual({
      command: "validationError",
      errors: [SETTINGS_UPDATE_ERROR]
    });
    expect(readSettings()).toEqual(priorDraft);

    failConfigurationUpdate("cursorUsage.thresholds.high");
    await webviewPanels[0]?.webview.dispatch({ command: "reset" });
    expect(webviewPanels[0]?.webview.postedMessages[1]).toEqual({
      command: "validationError",
      errors: [SETTINGS_UPDATE_ERROR]
    });
    expect(readSettings()).toEqual(priorDraft);
    expect(
      JSON.stringify(webviewPanels[0]?.webview.postedMessages)
    ).not.toContain("sensitive");
    panel.dispose();
  });
});
