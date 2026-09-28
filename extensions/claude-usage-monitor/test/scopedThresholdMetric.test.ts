import { afterEach, describe, expect, it } from "vitest";
import { getActiveUrgency, pickTriggerMetric, buildUsageSuggestion } from "../src/recommendations";
import { getThresholdMetric, type UsageData } from "../src/types";
import { settingsSectionHtml, currentSettings } from "../src/settingsPanel";
import { __resetStubState, __setStubConfig } from "./vscode-stub";

const data: UsageData = {
  session: { percent: 12, resetsIn: "3h", resetsAt: null },
  weeklyAllModels: { percent: 34, resetsIn: "4d", resetsAt: null },
  weeklyScoped: { percent: 86, resetsIn: "2d", resetsAt: null, label: "Fable" },
  currentModel: "opus" as UsageData["currentModel"],
  lastUpdated: Date.now(),
};

describe("scoped weekly threshold metric", () => {
  afterEach(() => __resetStubState());

  it("keeps the default highest metric scoped-bar-neutral", () => {
    expect(getThresholdMetric()).toBe("highest");
    expect(pickTriggerMetric(data)?.percent).toBe(34);
    expect(getActiveUrgency(data)).toBe("low");
  });

  it("uses the account-provided scoped limit and label when explicitly selected", () => {
    __setStubConfig("claudeUsage", "thresholdMetric", "weeklyScoped");
    expect(getThresholdMetric()).toBe("weeklyScoped");
    const trigger = pickTriggerMetric(data);
    expect(trigger).toEqual({ percent: 86, resetsIn: "2d", label: "Weekly (Fable)" });
    expect(getActiveUrgency(data)).toBe("high");
    expect(buildUsageSuggestion(data, trigger!)?.message).toContain("Weekly (Fable) usage at 86%");
    expect(settingsSectionHtml(currentSettings())).toContain('<option value="weeklyScoped" selected>');
  });

  it("does not substitute session or all-models data when the scoped limit is absent", () => {
    __setStubConfig("claudeUsage", "thresholdMetric", "weeklyScoped");
    const unscoped: UsageData = { ...data, session: { ...data.session, percent: 98 }, weeklyScoped: undefined };
    expect(pickTriggerMetric(unscoped)).toBeNull();
    expect(getActiveUrgency(unscoped)).toBe("low");
  });
});
