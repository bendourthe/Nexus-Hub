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
  getThresholdMetric,
  syncActiveColorToWorkbench,
  syncColorsToWorkbench,
} from "../src/types";
import {
  __resetStubState,
  __setStubConfig,
  configurationUpdates,
  stubConfig,
} from "./vscode-stub";

const draft: DraftState = {
  metric: "weekly",
  thresholds: { moderate: 40, high: 70, critical: 90 },
  colors: { moderate: "#112233", high: "#445566", critical: "none" },
  compact: true,
};

describe("settings persistence", () => {
  afterEach(() => __resetStubState());

  it("reads configured values and migrates legacy color names", () => {
    __setStubConfig("codexUsage", "thresholdMetric", "session");
    __setStubConfig("codexUsage", "thresholds.moderate", 42);
    __setStubConfig("codexUsage", "thresholds.high", 73);
    __setStubConfig("codexUsage", "thresholds.critical", 96);
    __setStubConfig("codexUsage", "colors.moderate", "warning");
    __setStubConfig("codexUsage", "colors.high", "#123456");
    __setStubConfig("codexUsage", "colors.critical", "error");
    __setStubConfig("codexUsage", "compactStatusBar", true);

    expect(currentSettings()).toEqual({
      metric: "session",
      thresholds: { moderate: 42, high: 73, critical: 96 },
      colors: {
        moderate: DEFAULT_URGENCY_COLORS.moderate,
        high: "#123456",
        critical: DEFAULT_URGENCY_COLORS.critical,
      },
      compact: true,
    });
    expect(getThresholdMetric()).toBe("session");
  });

  it("persists a complete draft and synchronizes workbench colors", async () => {
    const saved = await saveSettings(draft);

    expect(saved).toEqual(draft);
    expect(stubConfig.codexUsage.compactStatusBar).toBe(true);
    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": "#445566",
    });
    expect(configurationUpdates.filter((u) => u.section === "codexUsage")).toHaveLength(8);
  });

  it("clears all settings and restores default workbench colors", async () => {
    await saveSettings(draft);
    configurationUpdates.length = 0;

    const reset = await resetSettings();

    expect(reset).toEqual(SETTINGS_DEFAULTS);
    expect(currentSettings()).toEqual(SETTINGS_DEFAULTS);
    expect(configurationUpdates.filter((u) => u.section === "codexUsage")).toHaveLength(8);
    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": DEFAULT_URGENCY_COLORS.high,
      "statusBarItem.errorBackground": DEFAULT_URGENCY_COLORS.critical,
    });
  });

  it("clamps notification timeouts and rejects unknown threshold metric values", () => {
    __setStubConfig("codexUsage", "notificationTimeoutSeconds", 1);
    expect(getNotificationTimeoutMs()).toBe(3_000);
    __setStubConfig("codexUsage", "notificationTimeoutSeconds", 90);
    expect(getNotificationTimeoutMs()).toBe(60_000);
    __setStubConfig("codexUsage", "notificationTimeoutSeconds", 15);
    expect(getNotificationTimeoutMs()).toBe(15_000);
    __setStubConfig("codexUsage", "thresholdMetric", "unknown");
    expect(getThresholdMetric()).toBe("highest");
  });
});

describe("workbench color synchronization", () => {
  afterEach(() => __resetStubState());

  it("removes stale and disabled entries while preserving unrelated customizations", async () => {
    __setStubConfig("workbench", "colorCustomizations", {
      "editor.background": "#000000",
      "codexUsageMonitor.moderateBackground": "#aaaaaa",
      "statusBarItem.warningBackground": "#bbbbbb",
      "statusBarItem.errorBackground": "#cccccc",
    });

    await syncColorsToWorkbench({ moderate: "none", high: "none", critical: "#123456" });

    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "editor.background": "#000000",
      "statusBarItem.errorBackground": "#123456",
    });
  });

  it("updates the shared warning color for high and moderate urgency only when needed", async () => {
    const colors = { moderate: "#111111", high: "#222222", critical: "#333333" };
    await syncActiveColorToWorkbench("high", colors);
    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": "#222222",
    });

    configurationUpdates.length = 0;
    await syncActiveColorToWorkbench("high", colors);
    expect(configurationUpdates).toHaveLength(0);

    await syncActiveColorToWorkbench("moderate", colors);
    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": "#111111",
    });
  });

  it("does not let low or critical display ticks overwrite an active high color", async () => {
    const colors = { moderate: "#cca700", high: "#f0643c", critical: "#e05555" };
    __setStubConfig("workbench", "colorCustomizations", {
      "statusBarItem.warningBackground": colors.high,
    });

    await syncActiveColorToWorkbench("low", colors);
    await syncActiveColorToWorkbench("critical", colors);

    expect(stubConfig.workbench.colorCustomizations).toEqual({
      "statusBarItem.warningBackground": colors.high,
    });
    expect(configurationUpdates).toHaveLength(0);
  });

  it("ignores invalid color values rather than writing malformed customizations", async () => {
    await syncColorsToWorkbench({ moderate: "warning", high: "bad", critical: "error" });
    expect(getColorConfig()).toEqual(DEFAULT_URGENCY_COLORS);
    expect(configurationUpdates).toHaveLength(0);
  });
});

describe("inline settings assets", () => {
  afterEach(() => __resetStubState());

  it("renders selected, compact, disabled-color, and client-script state", () => {
    const html = settingsSectionHtml(draft);
    const css = settingsStylesCss();
    const script = settingsScriptJs(draft);

    expect(html).toContain('<option value="weekly"  selected>');
    expect(html).toContain('id="compact-toggle" onchange="onCompact(this)" checked');
    expect(html).toContain('id="picker-critical"');
    expect(html).toContain('placeholder="none"');
    expect(css).toContain(".settings-section");
    expect(css).toContain("#saveBtn.dirty");
    expect(script).toContain('let settingsOriginal = {"metric":"weekly"');
    expect(script).toContain("function applySettings(settings)");
    expect(script).toContain("function toggleSettings()");
  });
});
