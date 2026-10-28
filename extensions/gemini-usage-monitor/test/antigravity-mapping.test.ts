import { describe, expect, it } from "vitest";
import { bucketWindow, mapQuotaSummary, readBucket, readPlanLabel } from "../src/providers/antigravity";
import { UNTRACKED_PERCENT } from "../src/types";

// Shape recorded from a live Antigravity IDE 2.5.5 RetrieveUserQuotaSummary
// response (2026-10-14); bucket ids replaced, fractions varied for coverage.
const NOW = Date.UTC(2026, 9, 14, 22, 0, 0);
function summary(geminiWeekly = 1, gemini5h = 1, otherWeekly: number | null = 0.6, other5h = 0.25) {
  return {
    response: {
      groups: [
        {
          displayName: "Gemini Models",
          description: "Models within this group: Gemini Flash, Gemini Pro",
          buckets: [
            { bucketId: "b1", displayName: "Weekly Limit Remaining", window: "weekly", remainingFraction: geminiWeekly, resetTime: "2026-10-21T22:10:04Z" },
            { bucketId: "b2", displayName: "Five Hour Limit Remaining", window: "5h", remainingFraction: gemini5h, resetTime: "2026-10-15T03:10:04Z" },
          ],
        },
        {
          displayName: "Claude and GPT models",
          description: "Models within this group: Claude Opus, Claude Sonnet, GPT-OSS",
          buckets: [
            { bucketId: "b3", displayName: "Weekly Limit Remaining", window: "weekly", ...(otherWeekly === null ? {} : { remainingFraction: otherWeekly }), resetTime: "2026-10-21T22:10:04Z" },
            { bucketId: "b4", displayName: "Five Hour Limit Remaining", window: "5h", remainingFraction: other5h, resetTime: "2026-10-15T03:10:04Z" },
          ],
        },
      ],
      description: "Within each group, models share a weekly limit and a 5-hour limit.",
    },
  };
}
const USER_STATUS = { userStatus: { userTier: { description: "Google AI Pro" } } };

describe("mapQuotaSummary", () => {
  it("maps the Gemini group to the headline pair and inverts remaining into used", () => {
    const model = mapQuotaSummary(summary(0.7, 0.42), USER_STATUS, NOW)!;
    expect(model.weeklyAllModels.percent).toBe(30);
    expect(model.session.percent).toBe(58);
    expect(model.session.resetsAt).toBe(Date.parse("2026-10-15T03:10:04Z"));
    expect(model.currentModel).toBe("Gemini Models");
    expect(model.planLabel).toBe("Google AI Pro");
    expect(model.dataSource).toBe("api");
    expect(model.lastUpdated).toBe(NOW);
  });

  it("maps every other group to labeled rows, session first", () => {
    const model = mapQuotaSummary(summary(), USER_STATUS, NOW)!;
    expect(model.additionalLimits?.map((r) => [r.label, r.percent])).toEqual([
      ["Claude and GPT Models: Current Session", 75],
      ["Claude and GPT Models: Weekly", 40],
    ]);
  });

  it("reads a missing remainingFraction as exhausted, as Antigravity's panel does", () => {
    const model = mapQuotaSummary(summary(1, 1, null), USER_STATUS, NOW)!;
    expect(model.additionalLimits?.[1]).toMatchObject({ label: "Claude and GPT Models: Weekly", percent: 100 });
  });

  it("falls back to the first group and a generic plan when Gemini or the status is absent", () => {
    const raw = summary();
    raw.response.groups.shift();
    const model = mapQuotaSummary(raw, undefined, NOW)!;
    expect(model.currentModel).toBe("Claude and GPT Models");
    expect(model.planLabel).toBe("Antigravity");
    expect(model.additionalLimits).toBeUndefined();
  });

  // The 2026-10-28 Models & Usage layout: a weekly-only "Gemini 4 Argon" group, and
  // a Claude and GPT group whose weekly limit is spent and whose 5-hour figure is blank.
  function layout20261028() {
    const raw = summary(0.83, 0.7, null) as { response: { groups: Record<string, unknown>[] } };
    const claude = raw.response.groups[1] as { buckets: Record<string, unknown>[] };
    delete claude.buckets[1].remainingFraction;
    raw.response.groups.unshift({
      displayName: "Gemini 4 Argon",
      buckets: [{ displayName: "Gemini 4 Argon Weekly Limit", window: "weekly", remainingFraction: 0.93, resetTime: "2026-10-21T22:10:04Z" }],
    });
    return raw;
  }

  it("keeps Gemini Models as the headline even when Gemini 4 Argon is listed first", () => {
    const model = mapQuotaSummary(layout20261028(), USER_STATUS, NOW)!;
    expect(model.currentModel).toBe("Gemini Models");
    expect(model.session.percent).toBe(30);
    expect(model.weeklyAllModels.percent).toBe(17);
    expect(model.additionalLimits?.map((r) => [r.label, r.percent])).toEqual([
      ["Gemini 4 Argon: Weekly", 7],
      ["Claude and GPT Models: Weekly", 100],
    ]);
  });

  it("hides a blank 5-hour figure while the weekly limit is spent instead of reporting it 100% used", () => {
    const model = mapQuotaSummary(layout20261028(), USER_STATUS, NOW)!;
    expect(model.additionalLimits?.some((r) => r.label === "Claude and GPT Models: Current Session")).toBe(false);
  });

  it("still reads a blank 5-hour figure as exhausted when the weekly limit is not spent", () => {
    const raw = summary(1, 1, 0.5);
    delete (raw.response.groups[1].buckets[1] as Record<string, unknown>).remainingFraction;
    const model = mapQuotaSummary(raw, USER_STATUS, NOW)!;
    expect(model.additionalLimits?.[0]).toMatchObject({ label: "Claude and GPT Models: Current Session", percent: 100 });
  });

  it("keeps an unclassified bucket visible under its own label instead of dropping it", () => {
    const raw = summary() as { response: { groups: Record<string, unknown>[] } };
    (raw.response.groups[0].buckets as Record<string, unknown>[]).push({ displayName: "Daily Burst Limit", window: "daily", remainingFraction: 0.4 });
    const model = mapQuotaSummary(raw, USER_STATUS, NOW)!;
    expect(model.additionalLimits).toContainEqual(expect.objectContaining({ label: "Gemini Models: Daily Burst Limit", percent: 60 }));
  });

  it("returns null when no group carries a usable window", () => {
    expect(mapQuotaSummary({ response: { groups: [] } })).toBeNull();
    expect(mapQuotaSummary({ response: { groups: [{ displayName: "X", buckets: [{ window: "daily" }] }] } })).toBeNull();
    expect(mapQuotaSummary("not json")).toBeNull();
    expect(mapQuotaSummary(null)).toBeNull();
  });
});

describe("bucket helpers", () => {
  it("classifies buckets by window id, then by label", () => {
    expect(bucketWindow({ window: "5h" })).toBe("session");
    expect(bucketWindow({ window: "weekly" })).toBe("weekly");
    expect(bucketWindow({ displayName: "Five Hour Limit Remaining" })).toBe("session");
    expect(bucketWindow({ displayName: "Weekly Limit Remaining" })).toBe("weekly");
    expect(bucketWindow({ window: "daily" })).toBeNull();
  });

  it("treats a disabled bucket as untracked and clamps out-of-range fractions", () => {
    expect(readBucket({ disabled: true, remainingFraction: 0.5 }).percent).toBe(UNTRACKED_PERCENT);
    expect(readBucket({ remainingFraction: 1.4 }).percent).toBe(0);
    expect(readBucket({ remainingFraction: -2 }).percent).toBe(100);
    expect(readBucket({ remainingFraction: 0.5, resetTime: "garbage" })).toMatchObject({ resetsAt: null, resetsIn: "N/A" });
  });

  it("reads the plan label only from userStatus.userTier.description", () => {
    expect(readPlanLabel(USER_STATUS)).toBe("Google AI Pro");
    expect(readPlanLabel({ userStatus: { userTier: { description: "" } } })).toBeUndefined();
    expect(readPlanLabel(undefined)).toBeUndefined();
  });
});
