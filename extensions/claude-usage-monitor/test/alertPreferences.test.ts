import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { usageAlertEnabled, usageAlertsFile } from "../src/alertPreferences";

describe("usageAlertEnabled", () => {
  let home: string; let previous: string | undefined;
  beforeEach(() => { previous = process.env.NEXUS_HUB_HOME; home = fs.mkdtempSync(path.join(os.tmpdir(), "alert-prefs-")); process.env.NEXUS_HUB_HOME = home; });
  afterEach(() => {
    fs.rmSync(home, { recursive: true, force: true });
    if (previous === undefined) { delete process.env.NEXUS_HUB_HOME; } else { process.env.NEXUS_HUB_HOME = previous; }
  });

  it("is enabled when the file is missing", () => { expect(usageAlertEnabled("claude")).toBe(true); });

  it("honors an explicit disable and leaves other providers enabled", () => {
    fs.writeFileSync(usageAlertsFile(), JSON.stringify({ claude: false }));
    expect(usageAlertEnabled("claude")).toBe(false);
    expect(usageAlertEnabled("codex")).toBe(true);
  });

  it("defaults to enabled for malformed, non-object, and array content", () => {
    for (const content of ["{not json", "null", "[false]", "7"]) {
      fs.writeFileSync(usageAlertsFile(), content);
      expect(usageAlertEnabled("claude")).toBe(true);
    }
  });

  it("defaults to enabled when the file is larger than 16 KiB", () => {
    fs.writeFileSync(usageAlertsFile(), JSON.stringify({ claude: false, pad: "x".repeat(17000) }));
    expect(usageAlertEnabled("claude")).toBe(true);
  });

  it("defaults to enabled when the path is not a regular file", () => {
    fs.mkdirSync(usageAlertsFile());
    expect(usageAlertEnabled("claude")).toBe(true);
  });

  it("ignores a symbolic link to a disabling file", (context) => {
    const target = path.join(home, "target.json");
    fs.writeFileSync(target, JSON.stringify({ claude: false }));
    try { fs.symlinkSync(target, usageAlertsFile()); } catch { context.skip(); return; }
    expect(usageAlertEnabled("claude")).toBe(true);
  });
});
