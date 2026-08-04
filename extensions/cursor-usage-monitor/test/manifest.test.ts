import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { COMMAND_IDS } from "../src/extension";

const manifest = JSON.parse(
  readFileSync(resolve(__dirname, "../package.json"), "utf8")
) as {
  contributes: {
    commands: Array<{ command: string }>;
    configuration: { properties: Record<string, unknown> };
    icons: Record<string, unknown>;
    views: Record<string, Array<Record<string, unknown>>>;
    viewsContainers: {
      activitybar: Array<Record<string, unknown>>;
    };
  };
};

describe("runtime manifest", () => {
  it("contributes every registered command exactly once", () => {
    expect(
      manifest.contributes.commands.map((entry) => entry.command).sort()
    ).toEqual(Object.values(COMMAND_IDS).sort());
  });

  it("wires the warning activity bar, view, icon font, and configuration", () => {
    expect(manifest.contributes.icons).toHaveProperty("cursor-icon");
    expect(manifest.contributes.viewsContainers.activitybar).toContainEqual(
      expect.objectContaining({
        id: "cursorUsageWarning",
        icon: "icons/warning.svg"
      })
    );
    expect(manifest.contributes.views.cursorUsageWarning).toContainEqual(
      expect.objectContaining({
        id: "cursorUsageWarningView",
        type: "webview",
        when: "cursorUsage.warningActive"
      })
    );
    expect(
      Object.keys(manifest.contributes.configuration.properties)
    ).toEqual(
      expect.arrayContaining([
        "cursorUsage.autoFetch",
        "cursorUsage.refreshInterval",
        "cursorUsage.showInStatusBar",
        "cursorUsage.compactStatusBar",
        "cursorUsage.alertMetric",
        "cursorUsage.thresholds.moderate",
        "cursorUsage.thresholds.high",
        "cursorUsage.thresholds.critical",
        "cursorUsage.staleAfterMinutes"
      ])
    );
    expect(
      Object.keys(manifest.contributes.configuration.properties)
    ).not.toEqual(expect.arrayContaining([expect.stringMatching(/colors?/iu)]));
  });

  it("does not expose credentials, tokens, or secrets as settings", () => {
    expect(
      Object.keys(manifest.contributes.configuration.properties)
    ).not.toEqual(
      expect.arrayContaining([
        expect.stringMatching(/credential|token|secret/iu)
      ])
    );
  });
});
