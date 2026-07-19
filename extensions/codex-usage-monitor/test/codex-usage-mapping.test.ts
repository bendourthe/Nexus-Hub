import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mapCodexUsageResponse } from "../src/providers/codex";

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

  it("defaults the weekly metric when only a primary window is present", () => {
    const payload = { rate_limits: { primary: { used_percent: 12, reset_after_seconds: 3600 } } };
    const model = mapCodexUsageResponse(payload);
    expect(model!.session.percent).toBe(12);
    expect(model!.weeklyAllModels).toEqual({ percent: 0, resetsIn: "N/A", resetsAt: null });
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
