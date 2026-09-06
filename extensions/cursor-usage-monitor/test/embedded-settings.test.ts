import { beforeEach, describe, expect, it } from "vitest";
import {
  currentSettings,
  resetSettings,
  saveSettings,
  settingsSectionHtml,
  SETTINGS_DEFAULTS,
  type DraftState
} from "../src/embeddedSettings";
import { configuration } from "./vscode-stub";

/**
 * Round-trip tests for the inline settings form.
 *
 * These exist because a maintainer reported the Compact status bar toggle
 * "going back to untoggled on its own" after saving. That symptom has two possible
 * causes with very different fixes: the value never persisted, or the value
 * persisted and the UI was rebuilt in a way that discarded the displayed state.
 * Asserting the persistence layer on its own is what separates them.
 */

beforeEach(() => {
  configuration.clear();
});

function draft(overrides: Partial<DraftState> = {}): DraftState {
  return { ...SETTINGS_DEFAULTS, ...overrides };
}

describe("settings persistence", () => {
  it("round-trips the compact toggle", async () => {
    expect(currentSettings().compact).toBe(false);
    const persisted = await saveSettings(draft({ compact: true }));
    expect(persisted.compact).toBe(true);
    // Read back through a fresh call, not the returned value: the returned value
    // could be the draft echoed straight back and still be wrong on disk.
    expect(currentSettings().compact).toBe(true);
  });

  it("stores the toggle as showStatusBarLabel, inverted", async () => {
    // The label is what the user means by "hide the words"; compactStatusBar also
    // abbreviates the pool names, so the two are deliberately not the same setting.
    await saveSettings(draft({ compact: true }));
    expect(configuration.get("cursorUsage.showStatusBarLabel")).toBe(false);
    await saveSettings(draft({ compact: false }));
    expect(configuration.get("cursorUsage.showStatusBarLabel")).toBe(true);
    expect(currentSettings().compact).toBe(false);
  });

  it("round-trips the metric and thresholds", async () => {
    await saveSettings(
      draft({
        metric: "otherModels",
        thresholds: { moderate: 40, high: 60, critical: 80 }
      })
    );
    const read = currentSettings();
    expect(read.metric).toBe("otherModels");
    expect(read.thresholds).toEqual({ moderate: 40, high: 60, critical: 80 });
  });

  it("round-trips colors, including the none sentinel", async () => {
    await saveSettings(
      draft({ colors: { moderate: "none", high: "#123456", critical: "#abcdef" } })
    );
    const read = currentSettings();
    expect(read.colors.moderate).toBe("none");
    expect(read.colors.high).toBe("#123456");
  });

  it("resets every key back to its default", async () => {
    await saveSettings(
      draft({ compact: true, metric: "cursorModels", thresholds: { moderate: 10, high: 20, critical: 30 } })
    );
    const reset = await resetSettings();
    expect(reset).toEqual(SETTINGS_DEFAULTS);
    expect(currentSettings()).toEqual(SETTINGS_DEFAULTS);
  });
});

describe("settings markup", () => {
  it("renders the saved state, so a re-render cannot show a stale toggle", async () => {
    // The dashboard rebuilds its whole HTML on any configuration change. If the
    // markup were built from anything other than the persisted values, the form
    // would visibly revert the moment it was saved.
    await saveSettings(draft({ compact: true }));
    const html = settingsSectionHtml(currentSettings());
    expect(html).toContain('id="compact-toggle"');
    expect(html).toContain("checked");
  });

  it("uses no inline event handlers, which the panel's CSP would block", () => {
    // A verbatim copy of the sibling monitor's form renders correctly and does
    // nothing under a nonce CSP: every control is dead with no visible error.
    const html = settingsSectionHtml(currentSettings());
    expect(html).not.toMatch(/on(?:click|change|input|blur)=/u);
    expect(html).toContain("data-settings=");
  });

  it("offers Cursor's own pools as the threshold metric", () => {
    const html = settingsSectionHtml(currentSettings());
    expect(html).toContain('value="cursorModels"');
    expect(html).toContain('value="otherModels"');
    // The sibling's session/weekly options must not survive the port.
    expect(html).not.toContain('value="session"');
    expect(html).not.toContain('value="weekly"');
  });

  it("names the Cursor label in the toggle hint, not the sibling's", () => {
    const html = settingsSectionHtml(currentSettings());
    expect(html).toContain('Cursor Usage: ');
    expect(html).not.toContain('Claude Usage: ');
  });
});

describe("write amplification", () => {
  it("writes only the keys that actually changed", async () => {
    // Each write fires onDidChangeConfiguration, and the dashboard rebuilds its
    // whole webview on that event. Writing all eight keys for a single toggle meant
    // eight rebuilds, which is what made the panel sit unresponsive and then look
    // like it had discarded the change.
    const { configurationUpdates } = await import("./vscode-stub");
    configurationUpdates.length = 0;
    await saveSettings(draft({ compact: true }));
    expect(configurationUpdates).toHaveLength(1);
    expect(configurationUpdates[0]?.key).toBe("showStatusBarLabel");
  });

  it("writes nothing at all when the draft matches what is stored", async () => {
    const { configurationUpdates } = await import("./vscode-stub");
    await saveSettings(draft({ compact: true }));
    configurationUpdates.length = 0;
    await saveSettings(draft({ compact: true }));
    expect(configurationUpdates).toHaveLength(0);
  });
});
