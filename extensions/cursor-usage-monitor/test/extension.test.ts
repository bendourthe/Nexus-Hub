import { describe, expect, it } from "vitest";
import { activate, deactivate } from "../src/extension";
import { METER_FILL_COLOR } from "../src/types";

describe("Phase 4 extension scaffold", () => {
  it("activates and deactivates without registering UI resources", () => {
    expect(() => activate({} as never)).not.toThrow();
    expect(() => deactivate()).not.toThrow();
  });

  it("locks the Phase 5 meter color", () => {
    expect(METER_FILL_COLOR).toBe("#4682B4");
  });
});
