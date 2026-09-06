import { afterEach, describe, expect, it } from "vitest";
import { syncActiveColorToWorkbench } from "../src/types";
import {
  __resetStubState,
  __setStubConfig,
  configurationUpdates,
  stubConfig,
} from "./vscode-stub";

describe("workbench color synchronization", () => {
  afterEach(() => __resetStubState());

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
});
