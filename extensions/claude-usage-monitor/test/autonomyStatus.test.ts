import { describe, expect, it } from "vitest";
import { parseAutonomyStatus } from "../src/autonomyStatus";

function status(entry: Record<string, unknown>): string {
  return JSON.stringify({ project: "/work/demo", platforms: [entry] });
}

describe("autonomy status presentation (Claude)", () => {
  it("renders verified off as a neutral persistent state", () => {
    const result = parseAutonomyStatus(
      status({ platform: "claude", supported: true, status: "off", tier: "off" }),
      "claude",
    );
    expect(result).toMatchObject({ mode: "off", text: "$(shield) Autonomy: Off" });
    expect(result.backgroundColor).toBeUndefined();
  });

  it("renders edits with a warning color and rounded-up TTL", () => {
    const result = parseAutonomyStatus(
      status({
        platform: "claude",
        supported: true,
        status: "active",
        tier: "edits_only",
        remaining_seconds: 3599,
      }),
      "claude",
    );
    expect(result).toMatchObject({
      mode: "edits",
      text: "$(shield) Autonomy: Edits 1h",
      backgroundColor: "statusBarItem.warningBackground",
    });
  });

  it("renders full with an error color", () => {
    const result = parseAutonomyStatus(
      status({
        platform: "claude",
        supported: true,
        status: "active",
        tier: "full",
        remaining_seconds: 3900,
      }),
      "claude",
    );
    expect(result).toMatchObject({
      mode: "full",
      text: "$(shield) Autonomy: Full 1h 5m",
      backgroundColor: "statusBarItem.errorBackground",
    });
  });

  it("renders expired as neutral without requiring a reload", () => {
    const result = parseAutonomyStatus(
      status({ platform: "claude", supported: true, status: "expired", tier: "full" }),
      "claude",
    );
    expect(result).toMatchObject({ mode: "expired", text: "$(shield) Autonomy: Expired" });
    expect(result.backgroundColor).toBeUndefined();
  });

  it("distinguishes a missing descriptor from verified off", () => {
    const result = parseAutonomyStatus(
      status({ platform: "claude", supported: false, status: "off" }),
      "claude",
    );
    expect(result.mode).toBe("unavailable");
    expect(result.text).toContain("Unavailable");
  });

  it("degrades malformed CLI output to unavailable", () => {
    expect(parseAutonomyStatus("not json", "claude").mode).toBe("unavailable");
  });
});
