import { describe, expect, it } from "vitest";
import { shapePaths, summarizeShape } from "../src/providers/wireShape";

/**
 * The probe doc forbids recording account names, emails, team ids, and usage
 * figures. This block is where that becomes enforceable: the summarizer's output
 * is the only thing that leaves the probe, so anything it can echo is a leak.
 */
const SENSITIVE_PAYLOAD = {
  accountName: "ben-dourthe",
  email: "someone@example.com",
  teamId: "team_9f8a7b6c",
  requestId: "req_abc123",
  activity: "Refactored the billing module for Acme Corp",
  billingCycle: { start: "2026-08-01T00:00:00Z", end: "2026-09-01T00:00:00Z" },
  includedUsage: {
    unit: "tokens",
    cursorModels: { usedTokens: 345123, limitTokens: 1000000, percentUsed: 34.51 }
  },
  onDemand: { enabled: true, spendCents: 1250, currency: "USD" }
};

describe("summarizeShape", () => {
  it("reports names and types, never values", () => {
    const summary = summarizeShape(SENSITIVE_PAYLOAD);

    // Field names survive: that is the point, they are what fixes the contract.
    expect(summary).toContain("cursorModels");
    expect(summary).toContain("usedTokens");
    expect(summary).toContain("spendCents");

    // Values do not.
    expect(summary).not.toContain("ben-dourthe");
    expect(summary).not.toContain("example.com");
    expect(summary).not.toContain("team_9f8a7b6c");
    expect(summary).not.toContain("req_abc123");
    expect(summary).not.toContain("Acme");
    expect(summary).not.toContain("345123");
    expect(summary).not.toContain("1000000");
    expect(summary).not.toContain("1250");
    expect(summary).not.toContain("34.51");
  });

  it("contains no digits except bounded array lengths", () => {
    const summary = summarizeShape(SENSITIVE_PAYLOAD);
    // No array in this payload, so a digit anywhere would be a leaked figure.
    expect(summary).not.toMatch(/\d/u);
  });

  it("distinguishes integer from decimal without echoing either", () => {
    expect(summarizeShape(345123)).toBe("integer");
    expect(summarizeShape(34.51)).toBe("decimal");
  });

  it("reports the two value classes that are units, not identifiers", () => {
    expect(summarizeShape("2026-08-01T00:00:00Z")).toBe("iso-timestamp");
    expect(summarizeShape("USD")).toBe("currency-code");
    expect(summarizeShape("tokens")).toBe("unit-word(tokens)");
    expect(summarizeShape("requests")).toBe("unit-word(requests)");
  });

  it("reduces any other string to the bare type", () => {
    for (const value of [
      "ben-dourthe",
      "someone@example.com",
      "team_9f8a7b6c",
      "Refactored the billing module",
      "ABCD",
      "usd-ish"
    ]) {
      expect(summarizeShape(value)).toBe("string");
    }
  });

  it("caps array output at a length and one element type", () => {
    const summary = summarizeShape([
      { product: "actions", quantity: 42 },
      { product: "copilot", quantity: 99 }
    ]);
    expect(summary).toContain("array<");
    expect(summary).toContain("[2]");
    expect(summary).toContain("quantity: integer");
    // Only the first element is described, and no quantity leaks.
    expect(summary).not.toContain("42");
    expect(summary).not.toContain("99");
    expect(summary).not.toContain("actions");
  });

  it("handles empty and null shapes", () => {
    expect(summarizeShape(null)).toBe("null");
    expect(summarizeShape([])).toBe("array<empty>");
    expect(summarizeShape({})).toBe("object<empty>");
  });

  it("stops at a bounded depth instead of recursing forever", () => {
    let nested: Record<string, unknown> = { leaf: 1 };
    for (let index = 0; index < 20; index += 1) {
      nested = { level: nested };
    }
    const summary = summarizeShape(nested);
    expect(summary).toContain("...");
    expect(summary.length).toBeLessThan(500);
  });

  it("survives a self-referential payload without hanging", () => {
    const cyclic: Record<string, unknown> = { name: "x" };
    cyclic.self = cyclic;
    // Depth capping, not cycle detection, is what saves this. Asserted because a
    // probe that hangs on a surprising payload is a probe that cannot be run.
    expect(() => summarizeShape(cyclic)).not.toThrow();
  });
});

describe("shapePaths", () => {
  it("lists dot-paths for diffing against the wire contract", () => {
    const paths = shapePaths({
      billingCycle: { start: "2026-08-01T00:00:00Z" },
      includedUsage: { cursorModels: { usedTokens: 1 } }
    });
    expect(paths).toEqual([
      "billingCycle.start",
      "includedUsage.cursorModels.usedTokens"
    ]);
  });

  it("emits no values, only paths", () => {
    const joined = shapePaths(SENSITIVE_PAYLOAD).join(" ");
    expect(joined).toContain("includedUsage.cursorModels.usedTokens");
    expect(joined).not.toContain("ben-dourthe");
    expect(joined).not.toMatch(/\d{4,}/u);
  });
});
