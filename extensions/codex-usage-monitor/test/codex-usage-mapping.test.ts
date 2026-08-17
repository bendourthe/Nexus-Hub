import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mapCodexUsageResponse } from "../src/providers/codex";
import { UNTRACKED_PERCENT } from "../src/types";

// Freeze time so relative reset windows and duration labels are deterministic.
const NOW = Date.UTC(2026, 6, 16, 12, 0, 0); // 2026-07-16T12:00:00Z
const TWO_H_THIRTY = 150 * 60 * 1000;
const THREE_DAYS = 3 * 24 * 60 * 60 * 1000;
const ONE_HOUR = 60 * 60 * 1000;

describe("mapCodexUsageResponse", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("maps a representative wham/usage payload onto the normalized model", () => {
    const payload = {
      plan_type: "chatgpt_plus",
      rate_limits: {
        primary: { used_percent: 42, reset_at: new Date(NOW + TWO_H_THIRTY).toISOString() },
        secondary: { used_percent: 10, reset_at: new Date(NOW + THREE_DAYS).toISOString() },
      },
      additional_rate_limits: [
        { name: "Codex tasks", used_percent: 20, reset_after_seconds: 3600 },
      ],
      credits: { has_credits: true, unlimited: false, balance: 5 },
      workspace_monthly_credit_limit: {
        used_credits: 0,
        monthly_limit: 5_000,
        reset_at: Math.floor((NOW + THREE_DAYS) / 1000),
      },
    };

    const model = mapCodexUsageResponse(payload);

    expect(model).not.toBeNull();
    expect(model!.dataSource).toBe("api");
    expect(model!.planLabel).toBe("ChatGPT Plus");
    expect(model!.currentModel).toBe("ChatGPT Plus");
    expect(model!.lastUpdated).toBe(NOW);

    // Primary window -> session metric.
    expect(model!.session.percent).toBe(42);
    expect(model!.session.resetsAt).toBe(NOW + TWO_H_THIRTY);
    expect(model!.session.resetsIn).toBe("2h 30m");

    // Secondary window -> weekly metric (percent + absolute reset are deterministic).
    expect(model!.weeklyAllModels.percent).toBe(10);
    expect(model!.weeklyAllModels.resetsAt).toBe(NOW + THREE_DAYS);

    // Additional limit row.
    expect(model!.additionalLimits).toEqual([
      { label: "Codex tasks", percent: 20, resetsIn: "1h", resetsAt: NOW + ONE_HOUR },
    ]);

    // Credits summary.
    expect(model!.creditsSummary).toBe("Credits: 5 remaining");
    expect(model!.extraCredits).toMatchObject({
      usedCredits: 0,
      monthlyLimit: 5_000,
      percent: 0,
      resetsAt: NOW + THREE_DAYS,
    });
  });

  it("maps camelCase monthly credit limits and derives usage from the remaining balance", () => {
    const model = mapCodexUsageResponse({
      rate_limit: {
        primary_window: {
          used_percent: 10,
          limit_window_seconds: 604800,
          reset_at: Math.floor((NOW + THREE_DAYS) / 1000),
        },
      },
      credits: {
        monthlyLimit: 5_000,
        balance: 4_250,
        resetAt: new Date(NOW + THREE_DAYS).toISOString(),
      },
    });

    expect(model!.extraCredits).toMatchObject({
      usedCredits: 750,
      monthlyLimit: 5_000,
      percent: 15,
      resetsAt: NOW + THREE_DAYS,
    });
  });

  it("maps the live spend-control individual limit as Extra Credits usage", () => {
    const model = mapCodexUsageResponse({
      plan_type: "team",
      rate_limit: {
        primary_window: {
          used_percent: 100,
          limit_window_seconds: 604800,
          reset_at: Math.floor((NOW + THREE_DAYS) / 1000),
        },
      },
      credits: { has_credits: true, unlimited: false, balance: null },
      spend_control: {
        reached: false,
        individual_limit: {
          source: "account_user_spend_controls",
          limit: 5_000,
          used: 225,
          remaining: 4_775,
          used_percent: 5,
          remaining_percent: 95,
          used_usd: 9,
          limit_usd: 200,
          reset_at: Math.floor((NOW + THREE_DAYS) / 1000),
        },
      },
    });

    expect(model!.creditsSummary).toBe("Credits: available");
    expect(model!.extraCredits).toMatchObject({
      usedCredits: 225,
      monthlyLimit: 5_000,
      percent: 5,
      resetsAt: NOW + THREE_DAYS,
      usedAmountUsd: 9,
      limitAmountUsd: 200,
    });
  });

  it("maps a top-level numeric workspace credit limit and credit-specific reset alias", () => {
    const model = mapCodexUsageResponse({
      weekly_limit: { used_percent: 25, reset_after_seconds: THREE_DAYS / 1000 },
      workspace_monthly_credit_limit: 5_000,
      credits_used: 1_250,
      credit_reset_at: Math.floor((NOW + THREE_DAYS) / 1000),
    });

    expect(model!.extraCredits).toMatchObject({
      usedCredits: 1_250,
      monthlyLimit: 5_000,
      percent: 25,
      resetsAt: NOW + THREE_DAYS,
    });
  });

  it("supports top-level primary/secondary windows", () => {
    const payload = {
      plan: "pro",
      primary: { utilization: 55, reset_after_seconds: 3600 },
      secondary: { utilization: 5, reset_after_seconds: THREE_DAYS / 1000 },
    };
    const model = mapCodexUsageResponse(payload);
    expect(model!.session.percent).toBe(55);
    expect(model!.session.resetsAt).toBe(NOW + ONE_HOUR);
    expect(model!.planLabel).toBe("Pro");
  });

  it("supports an array of rate-limit windows", () => {
    const payload = {
      rate_limits: [
        { used_percent: 30, reset_after_seconds: 3600 },
        { used_percent: 8, reset_after_seconds: THREE_DAYS / 1000 },
      ],
    };
    const model = mapCodexUsageResponse(payload);
    expect(model!.session.percent).toBe(30);
    expect(model!.weeklyAllModels.percent).toBe(8);
  });

  // v3.14.5 Phase 4.1: the undocumented endpoint may name its windows
  // primary_window / secondary_window (or five_hour_limit / weekly_limit),
  // nested under rate_limits or at the top level. Probe those aliases too.
  it("supports primary_window / secondary_window aliases (nested and top-level)", () => {
    const nested = mapCodexUsageResponse({
      rate_limits: {
        primary_window: { used_percent: 60, reset_after_seconds: 3600 },
        secondary_window: { used_percent: 15, reset_after_seconds: THREE_DAYS / 1000 },
      },
    });
    expect(nested!.session.percent).toBe(60);
    expect(nested!.weeklyAllModels.percent).toBe(15);

    const topLevel = mapCodexUsageResponse({
      primary_window: { used_percent: 33, reset_after_seconds: 3600 },
      secondary_window: { used_percent: 4, reset_after_seconds: THREE_DAYS / 1000 },
    });
    expect(topLevel!.session.percent).toBe(33);
    expect(topLevel!.weeklyAllModels.percent).toBe(4);
  });

  it("supports five_hour_limit / weekly_limit aliases", () => {
    const model = mapCodexUsageResponse({
      rate_limits: {
        five_hour_limit: { used_percent: 70, reset_after_seconds: 3600 },
        weekly_limit: { used_percent: 25, reset_after_seconds: THREE_DAYS / 1000 },
      },
    });
    expect(model!.session.percent).toBe(70);
    expect(model!.weeklyAllModels.percent).toBe(25);
  });

  it("marks the weekly window untracked when only a primary window is present", () => {
    const payload = { rate_limits: { primary: { used_percent: 12, reset_after_seconds: 3600 } } };
    const model = mapCodexUsageResponse(payload);
    expect(model!.session.percent).toBe(12);
    // Absent weekly window is now untracked (hidden by the UI), not a fake 0%.
    expect(model!.weeklyAllModels.percent).toBe(UNTRACKED_PERCENT);
  });

  it("maps a weekly-only plan with no 5-hour/session window (the current Codex reality)", () => {
    const payload = {
      rate_limits: {
        weekly_limit: { used_percent: 91, reset_after_seconds: THREE_DAYS / 1000 },
      },
    };
    const model = mapCodexUsageResponse(payload);
    expect(model).not.toBeNull();
    expect(model!.weeklyAllModels.percent).toBe(91);
    // No 5-hour window on this plan -> session is untracked, so the UI shows
    // only the weekly figure instead of a dead "--% (current)".
    expect(model!.session.percent).toBe(UNTRACKED_PERCENT);
  });

  // v3.14.6: the REAL wham/usage schema (captured from the live endpoint) nests
  // the windows under `rate_limit` (singular) as primary_window/secondary_window,
  // each with a `limit_window_seconds` duration and an epoch-seconds `reset_at`.
  it("maps the verified live schema: a Team plan with a single weekly window", () => {
    const payload = {
      plan_type: "team",
      rate_limit: {
        allowed: true,
        limit_reached: false,
        primary_window: {
          used_percent: 91,
          limit_window_seconds: 604800, // 7 days -> weekly, even though it is the PRIMARY window
          reset_after_seconds: 604800,
          reset_at: Math.floor((NOW + THREE_DAYS) / 1000), // epoch SECONDS
        },
        secondary_window: null,
      },
      credits: { has_credits: false, unlimited: false, balance: null },
    };
    const model = mapCodexUsageResponse(payload);
    expect(model).not.toBeNull();
    expect(model!.planLabel).toBe("Team");
    // The single 7-day window is classified as weekly (not mislabeled "session").
    expect(model!.weeklyAllModels.percent).toBe(91);
    expect(model!.weeklyAllModels.resetsAt).toBe(NOW + THREE_DAYS);
    // No 5-hour window on this plan -> session untracked, so the UI hides it.
    expect(model!.session.percent).toBe(UNTRACKED_PERCENT);
    // credits block present but empty -> no credits summary line.
    expect(model!.creditsSummary).toBeUndefined();
  });

  it("maps the verified live schema: a plan with both a 5-hour and a weekly window", () => {
    const payload = {
      plan_type: "plus",
      rate_limit: {
        primary_window: { used_percent: 40, limit_window_seconds: 18000, reset_at: Math.floor((NOW + ONE_HOUR) / 1000) },
        secondary_window: { used_percent: 12, limit_window_seconds: 604800, reset_at: Math.floor((NOW + THREE_DAYS) / 1000) },
      },
    };
    const model = mapCodexUsageResponse(payload);
    expect(model!.planLabel).toBe("Plus");
    // 5-hour window -> session; 7-day window -> weekly, classified by duration.
    expect(model!.session.percent).toBe(40);
    expect(model!.weeklyAllModels.percent).toBe(12);
  });

  it("reports unlimited credits", () => {
    const payload = {
      rate_limits: { primary: { used_percent: 1, reset_after_seconds: 3600 } },
      credits: { unlimited: true },
    };
    expect(mapCodexUsageResponse(payload)!.creditsSummary).toBe("Credits: unlimited");
  });

  describe("fail-soft paths return null", () => {
    it("null / non-object payloads", () => {
      expect(mapCodexUsageResponse(null)).toBeNull();
      expect(mapCodexUsageResponse("a string")).toBeNull();
      expect(mapCodexUsageResponse(42)).toBeNull();
    });

    it("empty object (no windows)", () => {
      expect(mapCodexUsageResponse({})).toBeNull();
    });

    it("primary window without a percentage", () => {
      expect(mapCodexUsageResponse({ rate_limits: { primary: { reset_after_seconds: 3600 } } })).toBeNull();
    });
  });
});
