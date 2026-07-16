import { describe, expect, it } from "vitest";
import { buildUsageSuggestion, getRecommendation, pickTriggerMetric } from "../src/recommendations";
import type { UsageData } from "../src/types";

// The vscode stub returns config defaults, so thresholds resolve to 50 / 75 / 95
// and the metric to "highest" - enough to exercise the recommendation branches.
function makeData(overrides: Partial<UsageData>): UsageData {
  return {
    session: { percent: 0, resetsIn: "2h", resetsAt: null },
    weeklyAllModels: { percent: 0, resetsIn: "3d", resetsAt: null },
    currentModel: "codex",
    lastUpdated: 0,
    ...overrides,
  };
}

describe("Codex recommendations", () => {
  it("advises wait/rotate with no model switch at critical usage", () => {
    const data = makeData({ providerId: "codex", session: { percent: 97, resetsIn: "2h", resetsAt: null } });
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion).not.toBeNull();
    expect(suggestion!.switchModel).toBeNull();
    expect(suggestion!.effortAdvice.toLowerCase()).toContain("rotate");
    expect(suggestion!.message).toContain("Codex");
  });

  it("advises throttling at moderate usage", () => {
    const data = makeData({ providerId: "codex", session: { percent: 55, resetsIn: "2h", resetsAt: null } });
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion!.switchModel).toBeNull();
    expect(suggestion!.effortAdvice.toLowerCase()).toContain("throttle");
  });

  it("getRecommendation suggests no model and mentions account rotation at critical", () => {
    const data = makeData({ providerId: "codex", session: { percent: 98, resetsIn: "2h", resetsAt: null } });
    const rec = getRecommendation(data);
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message.toLowerCase()).toContain("account");
  });
});

describe("Claude recommendations are unchanged", () => {
  it("suggests switching Opus to Sonnet at high usage", () => {
    const data = makeData({
      providerId: undefined,
      currentModel: "claude-opus-4-6",
      session: { percent: 80, resetsIn: "2h", resetsAt: null },
    });
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion!.switchModel).toBe("Sonnet");
  });
});
