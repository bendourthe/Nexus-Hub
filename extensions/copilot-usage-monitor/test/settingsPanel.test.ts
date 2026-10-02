import { afterEach, describe, expect, it } from "vitest";
import {
  SETTINGS_DEFAULTS,
  currentSettings,
  resetSettings,
  saveSettings,
  settingsScriptJs,
  settingsSectionHtml,
  settingsStylesCss,
  type DraftState,
} from "../src/settingsPanel";
import {
  DEFAULT_URGENCY_COLORS,
  getColorConfig,
  getNotificationTimeoutMs,
  getThresholdConfig,
  syncActiveColorToWorkbench,
  syncColorsToWorkbench,
} from "../src/types";
import { __resetStubState, __setStubConfig, configurationUpdates, stubConfig } from "./vscode-stub";

const draft: DraftState = {
  thresholds: { moderate: 40, high: 70, critical: 90 },
  colors: { moderate: "#112233", high: "#445566", critical: "none" },
  compact: true,
};

describe("settings persistence", () => {
  afterEach(() => __resetStubState());

  it("reads the copilotUsage settings with the siblings' defaults", () => {
    expect(currentSettings()).toEqual(SETTINGS_DEFAULTS);
    expect(getThresholdConfig()).toEqual({ moderate: 50, high: 75, critical: 95 });
    expect(getColorConfig()).toEqual(DEFAULT_URGENCY_COLORS);
    __setStubConfig("copilotUsage", "thresholds.high", 80);
    __setStubConfig("copilotUsage", "colors.high", "#123456");
    __setStubConfig("copilotUsage", "compactStatusBar", true);
    expect(currentSettings()).toMatchObject({ thresholds: { high: 80 }, colors: { high: "#123456" }, compact: true });
  });

  it("saves a draft sequentially under copilotUsage and syncs workbench colors", async () => {
    const saved = await saveSettings(draft);
    expect(saved).toEqual(draft);
    expect(configurationUpdates.filter((u) => u.section === "copilotUsage").map((u) => u.key)).toEqual([
      "thresholds.moderate",
      "thresholds.high",
      "thresholds.critical",
      "colors.moderate",
      "colors.high",
      "colors.critical",
      "compactStatusBar",
    ]);
    expect(stubConfig.workbench.colorCustomizations).toEqual({ "statusBarItem.warningBackground": "#445566" });
  });

  it("resets display settings without touching the organization connection", async () => {
    __setStubConfig("copilotUsage", "organization", "acme-co");
    await saveSettings(draft);
    expect(await resetSettings()).toEqual(SETTINGS_DEFAULTS);
    expect(stubConfig.copilotUsage).toEqual({ organization: "acme-co" });
    expect(configurationUpdates.some((u) => u.key === "organization")).toBe(false);
  });

  it("clamps the notification timeout to 3..60 seconds", () => {
    expect(getNotificationTimeoutMs()).toBe(12_000);
    __setStubConfig("copilotUsage", "notificationTimeoutSeconds", 1);
    expect(getNotificationTimeoutMs()).toBe(3_000);
    __setStubConfig("copilotUsage", "notificationTimeoutSeconds", 600);
    expect(getNotificationTimeoutMs()).toBe(60_000);
  });

  it("swaps the shared warning background per level and leaves low and critical alone", async () => {
    const colors = { moderate: "#111111", high: "#222222", critical: "#333333" };
    await syncActiveColorToWorkbench("low", colors);
    await syncActiveColorToWorkbench("critical", colors);
    expect(configurationUpdates).toEqual([]);
    await syncActiveColorToWorkbench("moderate", colors);
    await syncActiveColorToWorkbench("moderate", colors);
    expect(configurationUpdates).toHaveLength(1);
    await syncActiveColorToWorkbench("high", { ...colors, high: "none" });
    expect(stubConfig.workbench.colorCustomizations).toEqual({});
    await syncActiveColorToWorkbench("high", { ...colors, high: "not-a-hex" });
    expect(configurationUpdates).toHaveLength(2);
  });

  it("writes only changed workbench colors and removes those set to none", async () => {
    await syncColorsToWorkbench({ moderate: "#111111", high: "#222222", critical: "#333333" });
    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": "#222222",
      "statusBarItem.errorBackground": "#333333",
    });
    const before = configurationUpdates.length;
    await syncColorsToWorkbench({ moderate: "#111111", high: "#222222", critical: "#333333" });
    expect(configurationUpdates.length).toBe(before);
    await syncColorsToWorkbench({ moderate: "none", high: "none", critical: "none" });
    expect(stubConfig.workbench.colorCustomizations).toEqual({});
  });
});

describe("settings markup", () => {
  it("renders the form, the levels, and the Organization section", () => {
    const html = settingsSectionHtml(draft, { configured: false, connected: false });
    expect(html).toContain('id="settings-section"');
    expect(html).toContain("<h3>Organization</h3>");
    expect(html).toContain('Hide the "Copilot Usage: " label in the status bar');
    expect(html).toContain('id="compact-toggle" data-change="onCompact" checked');
    expect(html).toContain('id="none-critical" data-level="critical" data-click="onNone"');
    expect(html).toContain('value="#112233"');
    expect(settingsStylesCss()).toContain(".org-section");
    const script = settingsScriptJs(draft);
    expect(script).toContain("function applySettings(settings)");
    expect(script).not.toContain("metric");
  });
});
