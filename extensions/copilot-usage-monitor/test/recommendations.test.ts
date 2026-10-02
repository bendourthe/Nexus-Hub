import { afterEach, describe, expect, it } from "vitest";
import { buildUsageSuggestion, classifyUrgency, getActiveUrgency, getRecommendation, triggerPercent } from "../src/recommendations";
import type { QuotaRow, UsageData } from "../src/types";
import { headlineOf } from "../src/types";
import { __resetStubState, __setStubConfig } from "./vscode-stub";

const quota = (percent: number): QuotaRow => ({ id: "chat", label: "Chat", percent, entitlement: 100, remaining: 100 - percent });
const personalAt = (percent: number, resetsAt: number | null = Date.UTC(2026, 10, 1)): UsageData => ({
  personal: { planLabel: "Copilot Pro", quotas: [quota(percent)], primary: quota(percent), creditsUsed: 0, resetsAt },
  lastUpdated: 0,
  dataSource: "api",
});

describe("recommendations", () => {
  afterEach(() => __resetStubState());

  it("classifies against the configured thresholds", () => {
    expect([10, 50, 75, 95].map(classifyUrgency)).toEqual(["low", "moderate", "high", "critical"]);
    __setStubConfig("copilotUsage", "thresholds.moderate", 20);
    expect(classifyUrgency(25)).toBe("moderate");
  });

  it("has no urgency or trigger without a percentage", () => {
    const member: UsageData = { personal: { planLabel: "Copilot Business", quotas: [], primary: null, creditsUsed: 4, resetsAt: null }, lastUpdated: 0, dataSource: "api" };
    expect(getActiveUrgency(member)).toBe("low");
    expect(triggerPercent(member)).toBe(-1);
    expect(triggerPercent(undefined)).toBe(-1);
    expect(buildUsageSuggestion(member)).toBeNull();
    expect(getRecommendation(member).message).toBe("GitHub sets no personal limit for this seat, so there is no percentage to track.");
    expect(getRecommendation(undefined).message).toContain("No Copilot usage figure yet");
  });

  it.each([
    [55, "moderate", "Chat at 55%. Batch related requests into fewer prompts to stretch the allowance. It resets on November 1."],
    [80, "high", "Chat at 80%. Keep to essential tasks until the reset. It resets on November 1."],
    [97, "critical", "Chat at 97%. Pause non-essential Copilot work until the reset. It resets on November 1."],
  ])("builds the %i%% suggestion", (percent, urgency, message) => {
    const data = personalAt(percent);
    expect(buildUsageSuggestion(data)!.message).toBe(message);
    expect(getRecommendation(data)).toMatchObject({ urgency, message });
  });

  it("omits the reset sentence when GitHub gave no reset date, and stays healthy below moderate", () => {
    const suggestion = buildUsageSuggestion(personalAt(60, null))!;
    expect(suggestion.message).toBe("Chat at 60%. Batch related requests into fewer prompts to stretch the allowance.");
    expect(suggestion.resetLabel).toBe("Reset date not reported");
    expect(getRecommendation(personalAt(10)).message).toBe("Copilot usage is healthy. Keep working normally.");
  });

  it("falls back to the pool's credits when the organization has no seat count and no personal figure", () => {
    const data: UsageData = {
      organization: { used: 3, total: 0, percent: null, seats: 0, planType: "unknown", creditsPerSeat: 0, approximate: false, approximateReasons: [], resetsAt: 0, models: [] },
      lastUpdated: 0,
      dataSource: "api",
    };
    expect(headlineOf(data)).toEqual({ kind: "credits", creditsUsed: 3, label: "Organization pool" });
    expect(headlineOf({ lastUpdated: 0, dataSource: "api" })).toEqual({ kind: "none" });
  });
});
