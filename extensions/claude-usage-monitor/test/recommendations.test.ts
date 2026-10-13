import { afterEach, describe, expect, it } from "vitest";
import {
  classifyUrgency,
  getOverallUrgency,
  getRecommendation,
  getUrgencyColor,
  getUrgencyEmoji,
} from "../src/recommendations";
import type { UsageData } from "../src/types";
import { __resetStubState, __setStubConfig } from "./vscode-stub";

// Pure-logic coverage for the recommendation helpers that had no unit tests
// (v4.13 known gap AR-32). Defaults: moderate 50, high 75, critical 95.

function usage(session: number, weekly: number, model: string, scoped = 0): UsageData {
  return {
    session: { percent: session, resetsIn: "3h", resetsAt: null },
    weeklyAllModels: { percent: weekly, resetsIn: "4d", resetsAt: null },
    weeklyScoped: { percent: scoped, resetsIn: "2d", resetsAt: null, label: "Fable" },
    currentModel: model as UsageData["currentModel"],
    lastUpdated: 0,
  };
}

afterEach(() => __resetStubState());

describe("classifyUrgency", () => {
  it.each([
    [0, "low"],
    [49, "low"],
    [50, "moderate"],
    [74, "moderate"],
    [75, "high"],
    [94, "high"],
    [95, "critical"],
    [100, "critical"],
  ])("classifies %i%% as %s at the default thresholds", (percent, level) => {
    expect(classifyUrgency(percent)).toBe(level);
  });

  it("uses valid configured thresholds", () => {
    __setStubConfig("claudeUsage", "thresholds.moderate", 20);
    __setStubConfig("claudeUsage", "thresholds.high", 30);
    __setStubConfig("claudeUsage", "thresholds.critical", 40);
    expect(classifyUrgency(19)).toBe("low");
    expect(classifyUrgency(20)).toBe("moderate");
    expect(classifyUrgency(30)).toBe("high");
    expect(classifyUrgency(40)).toBe("critical");
  });

  it.each([0, 100, "60", Number.NaN])("falls back to the default when a threshold is %s", (bad) => {
    __setStubConfig("claudeUsage", "thresholds.high", bad);
    expect(classifyUrgency(74)).toBe("moderate");
    expect(classifyUrgency(75)).toBe("high");
  });
});

describe("getOverallUrgency", () => {
  it("returns the higher of session and weekly all-models", () => {
    expect(getOverallUrgency(usage(96, 10, "sonnet"))).toBe("critical");
    expect(getOverallUrgency(usage(10, 80, "sonnet"))).toBe("high");
    expect(getOverallUrgency(usage(55, 60, "sonnet"))).toBe("moderate");
    expect(getOverallUrgency(usage(5, 5, "sonnet"))).toBe("low");
  });

  it("ignores the scoped weekly bar", () => {
    expect(getOverallUrgency(usage(5, 5, "sonnet", 99))).toBe("low");
  });
});

describe("getRecommendation", () => {
  it("tells the user to wait when only the session is critical", () => {
    const rec = getRecommendation(usage(96, 40, "opus"));
    expect(rec.urgency).toBe("critical");
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message).toContain("Wait for the reset");
    expect(rec.message).toContain("resets in 3h");
  });

  it("suggests the standard-context model for a high session on a 1M variant", () => {
    const rec = getRecommendation(usage(80, 40, "opus[1m]"));
    expect(rec.suggestedModel).toBe("opus");
    expect(rec.message).toContain("1M context variant");
  });

  it("switches to Haiku when weekly usage is critical", () => {
    const rec = getRecommendation(usage(10, 96, "sonnet"));
    expect(rec.suggestedModel).toBe("haiku");
    expect(rec.message).toContain("Highest: Weekly at 96%");
  });

  it("drops Opus-class models to Sonnet when weekly usage is high", () => {
    expect(getRecommendation(usage(10, 80, "opus")).suggestedModel).toBe("sonnet");
    expect(getRecommendation(usage(10, 80, "fable")).suggestedModel).toBe("sonnet");
  });

  it("keeps a non-Opus model and reduces Effort when weekly usage is high", () => {
    const rec = getRecommendation(usage(10, 80, "sonnet"));
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message).toContain("Reduce Effort to High or Medium until the weekly reset");
  });

  it("drops Opus to Sonnet when the session is high", () => {
    const rec = getRecommendation(usage(80, 10, "opus"));
    expect(rec.suggestedModel).toBe("sonnet");
    expect(rec.message).toContain("Session usage is 80%");
  });

  it("keeps a non-Opus model when the session is high", () => {
    const rec = getRecommendation(usage(80, 10, "haiku"));
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message).toContain("Session usage is 80%");
  });

  it("reports healthy usage per model class when everything is low", () => {
    const opus = getRecommendation(usage(5, 5, "opus"));
    expect(opus.urgency).toBe("low");
    expect(opus.message).toContain("Continue using");
    expect(opus.tips).toHaveLength(1);
    const sonnet = getRecommendation(usage(5, 5, "sonnet"));
    expect(sonnet.message).toContain("All usage levels are healthy");
    expect(sonnet.tips).toHaveLength(2);
  });

  it("nudges Effort down at moderate usage and adds tips by metric", () => {
    const rec = getRecommendation(usage(60, 70, "opus"));
    expect(rec.urgency).toBe("moderate");
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message).toContain("Highest: Weekly at 70%");
    expect(rec.tips).toContain("Use /compact to reduce context window consumption in long conversations.");
    expect(rec.tips).toContain("Use plan mode for complex tasks to reduce iteration cycles.");
    expect(rec.tips.some((t) => t.startsWith("Use Sonnet for standard coding"))).toBe(true);
    expect(rec.tips.some((t) => t.startsWith("Start new conversations"))).toBe(false);
  });
});

describe("urgency presentation", () => {
  it.each([
    ["low", "statusBarItem.prominentBackground", "$(check)"],
    ["moderate", "statusBarItem.warningBackground", "$(warning)"],
    ["high", "statusBarItem.errorBackground", "$(flame)"],
    ["critical", "statusBarItem.errorBackground", "$(error)"],
  ] as const)("maps %s to its color and icon", (level, color, icon) => {
    expect(getUrgencyColor(level)).toBe(color);
    expect(getUrgencyEmoji(level)).toBe(icon);
  });
});
