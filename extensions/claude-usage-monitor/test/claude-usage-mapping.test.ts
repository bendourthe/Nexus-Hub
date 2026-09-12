import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mapClaudeUsageResponse } from "../src/providers/claude";

// Freeze time so relative reset windows and duration labels are deterministic.
const NOW = Date.UTC(2026, 8, 11, 12, 0, 0); // 2026-09-11T12:00:00Z
const TWO_HOURS = 2 * 60 * 60 * 1000;
const FOUR_DAYS = 4 * 24 * 60 * 60 * 1000;

const SESSION_RESET = new Date(NOW + TWO_HOURS).toISOString();
const WEEKLY_RESET = new Date(NOW + FOUR_DAYS).toISOString();

describe("mapClaudeUsageResponse", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("reads session, all-models weekly, and the model-scoped weekly limit from the limits array", () => {
    const model = mapClaudeUsageResponse(
      {
        limits: [
          { kind: "session", group: "session", percent: 72, resets_at: SESSION_RESET },
          { kind: "weekly_all", group: "weekly", percent: 43, resets_at: WEEKLY_RESET },
          {
            kind: "weekly_scoped",
            group: "weekly",
            percent: 0,
            resets_at: WEEKLY_RESET,
            scope: { model: { id: null, display_name: "Fable" } },
          },
        ],
      },
      "claude-opus-5[1m]"
    );

    expect(model.session.percent).toBe(72);
    expect(model.session.resetsAt).toBe(NOW + TWO_HOURS);
    expect(model.weeklyAllModels.percent).toBe(43);
    expect(model.weeklyScoped).toEqual({
      percent: 0,
      resetsIn: model.weeklyAllModels.resetsIn,
      resetsAt: NOW + FOUR_DAYS,
      label: "Fable",
    });
  });

  it("falls back to the flat five_hour / seven_day fields when limits is absent", () => {
    const model = mapClaudeUsageResponse(
      {
        five_hour: { utilization: 60, resets_at: SESSION_RESET },
        seven_day: { utilization: 30, resets_at: WEEKLY_RESET },
      },
      "claude-opus-5"
    );

    expect(model.session.percent).toBe(60);
    expect(model.weeklyAllModels.percent).toBe(30);
    expect(model.weeklyScoped).toBeUndefined();
  });

  it("omits the scoped weekly bar when the account reports no scoped limit", () => {
    const model = mapClaudeUsageResponse(
      {
        limits: [
          { kind: "session", group: "session", percent: 10, resets_at: SESSION_RESET },
          { kind: "weekly_all", group: "weekly", percent: 5, resets_at: WEEKLY_RESET },
        ],
      },
      "claude-sonnet-5"
    );

    expect(model.weeklyScoped).toBeUndefined();
  });

  it("skips a scoped entry that carries no display name rather than inventing a label", () => {
    const model = mapClaudeUsageResponse(
      {
        limits: [
          {
            kind: "weekly_scoped",
            group: "weekly",
            percent: 12,
            resets_at: WEEKLY_RESET,
            scope: { model: { id: null, display_name: "  " } },
          },
        ],
      },
      "claude-opus-5"
    );

    expect(model.weeklyScoped).toBeUndefined();
  });

  it("reports an absent window as zero with no reset rather than throwing", () => {
    const model = mapClaudeUsageResponse({}, "claude-opus-5");

    expect(model.session).toEqual({ percent: 0, resetsIn: "N/A", resetsAt: null });
    expect(model.weeklyAllModels).toEqual({ percent: 0, resetsIn: "N/A", resetsAt: null });
    expect(model.weeklyScoped).toBeUndefined();
  });

  it("converts extra-usage minor units to dollars", () => {
    const model = mapClaudeUsageResponse(
      {
        extra_usage: {
          is_enabled: true,
          monthly_limit: 50_000,
          used_credits: 9_853,
          utilization: 19.706,
        },
      },
      "claude-opus-5"
    );

    expect(model.extraUsage).toEqual({
      isEnabled: true,
      monthlyLimit: 500,
      usedCredits: 98.53,
      utilization: 19.706,
    });
  });
});
