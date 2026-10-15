import { describe, expect, it } from "vitest";
import {
  allMetrics,
  buildUsageSuggestion,
  findSwitchGroup,
  getActiveUrgency,
  getRecommendation,
  pickTriggerMetric,
} from "../src/recommendations";
import { UNTRACKED_PERCENT, type UsageData } from "../src/types";

// The vscode stub returns config defaults, so thresholds resolve to 50 / 75 / 95
// and the metric to "highest" - enough to exercise the recommendation branches.
function makeData(overrides: Partial<UsageData> = {}, other = { session: 0, weekly: 0 }): UsageData {
  return {
    session: { percent: 0, resetsIn: "2h", resetsAt: null },
    weeklyAllModels: { percent: 0, resetsIn: "3d", resetsAt: null },
    currentModel: "Gemini Models",
    lastUpdated: 0,
    additionalLimits: [
      { label: "Claude and GPT Models: Current Session", percent: other.session, resetsIn: "1h", resetsAt: null },
      { label: "Claude and GPT Models: Weekly", percent: other.weekly, resetsIn: "4d", resetsAt: null },
    ],
    ...overrides,
  };
}

describe("Antigravity recommendations", () => {
  it("lists every window of every model group, headline group first", () => {
    const metrics = allMetrics(makeData());
    expect(metrics.map((m) => `${m.group}/${m.label}`)).toEqual([
      "Gemini Models/Current Session",
      "Gemini Models/Weekly",
      "Claude and GPT Models/Current Session",
      "Claude and GPT Models/Weekly",
    ]);
  });

  it("skips an untracked headline window", () => {
    const data = makeData({ session: { percent: UNTRACKED_PERCENT, resetsIn: "N/A", resetsAt: null } });
    expect(allMetrics(data).some((m) => m.group === "Gemini Models" && m.label === "Current Session")).toBe(false);
  });

  it("alerts on the other model group too when the metric is 'highest'", () => {
    const data = makeData({}, { session: 0, weekly: 80 });
    const trigger = pickTriggerMetric(data);
    expect(trigger).toMatchObject({ group: "Claude and GPT Models", label: "Weekly", percent: 80 });
    expect(getActiveUrgency(data)).toBe("high");
  });

  it("suggests switching to the group that still has quota at critical usage", () => {
    const data = makeData({ session: { percent: 97, resetsIn: "2h", resetsAt: null } });
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion!.switchModel).toBe("Claude and GPT Models");
    expect(suggestion!.message).toContain("Gemini Models Current Session usage at 97%");
    expect(suggestion!.message).toContain("switch the agent to Claude and GPT Models");
    expect(suggestion!.effortAdvice.toLowerCase()).toContain("pause");
  });

  it("offers no switch when every group is at or above the moderate threshold", () => {
    const data = makeData({ session: { percent: 97, resetsIn: "2h", resetsAt: null } }, { session: 60, weekly: 10 });
    expect(findSwitchGroup(data, "Gemini Models")).toBeNull();
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion!.switchModel).toBeNull();
    expect(suggestion!.message).not.toContain("switch the agent");
  });

  it("advises throttling at moderate usage", () => {
    const data = makeData({ session: { percent: 55, resetsIn: "2h", resetsAt: null } });
    const suggestion = buildUsageSuggestion(data, pickTriggerMetric(data));
    expect(suggestion!.effortAdvice.toLowerCase()).toContain("throttle");
  });

  it("returns null below the moderate threshold", () => {
    const data = makeData({ session: { percent: 20, resetsIn: "2h", resetsAt: null } });
    expect(buildUsageSuggestion(data, pickTriggerMetric(data))).toBeNull();
  });

  it("getRecommendation names the switch target at critical usage", () => {
    const rec = getRecommendation(makeData({ weeklyAllModels: { percent: 98, resetsIn: "3d", resetsAt: null } }));
    expect(rec.urgency).toBe("critical");
    expect(rec.suggestedModel).toBe("Claude and GPT Models");
    expect(rec.message).toContain("Switch the agent to Claude and GPT Models");
  });

  it("getRecommendation is healthy when usage is low", () => {
    const rec = getRecommendation(makeData());
    expect(rec.urgency).toBe("low");
    expect(rec.suggestedModel).toBeNull();
    expect(rec.message.toLowerCase()).toContain("healthy");
  });
});
