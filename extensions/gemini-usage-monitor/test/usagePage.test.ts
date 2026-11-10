import { describe, expect, it } from "vitest";
import { openUsagePage } from "../src/usagePage";

/** A fake command runner: the named commands throw, every other one succeeds. */
function runner(failing: string[]) {
  const calls: unknown[][] = [];
  const execute = async (command: string, ...args: unknown[]): Promise<unknown> => {
    calls.push([command, ...args]);
    if (failing.includes(command)) {
      throw new Error(`command '${command}' not found`);
    }
    return undefined;
  };
  return { calls, execute };
}

describe("openUsagePage", () => {
  it("opens the Models screen through antigravity.openSettings on current builds", async () => {
    const { calls, execute } = runner([]);
    expect(await openUsagePage(execute)).toBe("antigravity.openSettings");
    expect(calls).toEqual([["antigravity.openSettings", "Models"]]);
  });

  it("falls back to the older settings-page command, then the settings window", async () => {
    const older = runner(["antigravity.openSettings"]);
    expect(await openUsagePage(older.execute)).toBe("workbench.action.openAntigravitySettingsWithId");
    expect(older.calls[1]).toEqual(["workbench.action.openAntigravitySettingsWithId", undefined, "Models"]);

    const oldest = runner(["antigravity.openSettings", "workbench.action.openAntigravitySettingsWithId"]);
    expect(await openUsagePage(oldest.execute)).toBe("workbench.action.openAntigravitySettings");
  });

  it("returns undefined without throwing when no settings command exists", async () => {
    const none = runner([
      "antigravity.openSettings",
      "workbench.action.openAntigravitySettingsWithId",
      "workbench.action.openAntigravitySettings",
    ]);
    await expect(openUsagePage(none.execute)).resolves.toBeUndefined();
    expect(none.calls).toHaveLength(3);
  });
});
