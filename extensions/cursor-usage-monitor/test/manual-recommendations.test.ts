import { describe, expect, it } from "vitest";
import {
  buildManualSnapshot,
  manualEntryTemplate,
  parseManualSnapshotInput,
  validateManualSnapshot,
  type ManualSnapshotInput
} from "../src/manualEntry";
import {
  buildUsageSuggestion,
  classifyUrgency,
  crossedUnnotifiedThreshold,
  pickTriggerMetric
} from "../src/recommendations";
import type { ProviderError, UsageState } from "../src/types";

const now = Date.parse("2026-08-04T18:00:00Z");
type FreshUsageState = Extract<UsageState, { state: "fresh" }>;

function input(): ManualSnapshotInput {
  return {
    cursorModels: { used: 80, limit: 100, unit: "requests" },
    otherModels: { used: 40, limit: 100, unit: "requests" },
    onDemandEnabled: true,
    personalSpend: { amount: 12.5, currency: "USD" },
    periodStartsAt: "2026-08-01T00:00:00Z",
    resetsAt: "2026-09-01T00:00:00Z"
  };
}

function freshState(): FreshUsageState {
  const result = buildManualSnapshot(input(), now);
  if (!result.ok) {
    throw new Error(result.errors.join(" "));
  }
  return { state: "fresh", data: result.value };
}

const offline: ProviderError = {
  code: "network-error",
  message: "offline",
  sourceAttempt: "html-scrape",
  recoverable: true
};

describe("manual usage snapshot", () => {
  it("parses the runtime schema and provides an empty entry template", () => {
    expect(parseManualSnapshotInput(input())).toEqual(input());
    expect(parseManualSnapshotInput(manualEntryTemplate())).toEqual(
      manualEntryTemplate()
    );
    expect(
      parseManualSnapshotInput({
        ...input(),
        cursorModels: { used: 10, limit: 20, unit: "credits" }
      })
    ).toBeUndefined();
    expect(parseManualSnapshotInput(null)).toBeUndefined();
  });

  it("constructs a typed manual snapshot and calculates only known percentages", () => {
    const result = buildManualSnapshot(input(), now);
    expect(result).toMatchObject({
      ok: true,
      value: {
        source: "manual",
        cursorModels: {
          percentUsed: 80,
          percentOrigin: "calculated"
        },
        otherModels: {
          percentUsed: 40,
          percentOrigin: "calculated"
        },
        onDemand: {
          enabled: true,
          personalSpend: { amount: 12.5, currency: "USD" }
        },
        teamContext: {
          sharedSpendLimit: null,
          dynamicSpendLimit: null
        },
        stale: false
      }
    });
  });

  it("keeps unknown denominators absolute and normalizes disabled on-demand", () => {
    const draft = input();
    draft.cursorModels.limit = null;
    draft.onDemandEnabled = false;
    draft.personalSpend = null;
    const result = buildManualSnapshot(draft, now);
    expect(result).toMatchObject({
      ok: true,
      value: {
        cursorModels: {
          used: { value: 80, unit: "requests" },
          limit: null,
          percentUsed: null,
          percentOrigin: null
        },
        onDemand: { enabled: false, personalSpend: null }
      }
    });
  });

  it("rejects invalid quantities, currency, dates, and inconsistent spend", () => {
    const draft = input();
    draft.cursorModels = { used: -1, limit: 0, unit: "tokens" };
    draft.otherModels = { used: null, limit: 10, unit: "requests" };
    draft.onDemandEnabled = null;
    draft.personalSpend = { amount: -2, currency: "usd" };
    draft.periodStartsAt = "not-a-date";
    draft.resetsAt = "also-bad";
    const errors = validateManualSnapshot(draft);
    expect(errors).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Cursor Models used"),
        expect.stringContaining("Cursor Models limit"),
        expect.stringContaining("Other Models cannot"),
        expect.stringContaining("Personal on-demand"),
        expect.stringContaining("Period start"),
        expect.stringContaining("Reset time")
      ])
    );
    expect(buildManualSnapshot(draft, now)).toEqual({ ok: false, errors });
  });

  it("requires reset to follow the period start", () => {
    const draft = input();
    draft.resetsAt = draft.periodStartsAt;
    expect(validateManualSnapshot(draft)).toContain(
      "Reset time must be after the period start."
    );
  });

  it("rejects a wholly empty manual entry", () => {
    const empty = manualEntryTemplate();
    expect(validateManualSnapshot(empty)).toContain(
      "Enter at least one usage, on-demand, or period value."
    );
    expect(buildManualSnapshot(empty, now)).toMatchObject({ ok: false });
  });
});

describe("threshold recommendations", () => {
  it("selects the highest or explicit personal meter", () => {
    const state = freshState();
    expect(pickTriggerMetric(state, "highest")?.key).toBe("cursorModels");
    expect(pickTriggerMetric(state, "otherModels")).toMatchObject({
      key: "otherModels",
      percent: 40
    });
  });

  it("suppresses stale states and percentage-unknown meters", () => {
    const state = freshState();
    const stale: UsageState = {
      state: "stale",
      data: {
        ...state.data,
        stale: true,
        staleReason: "fetch-failed"
      },
      error: offline
    };
    expect(pickTriggerMetric(stale, "highest")).toBeNull();
    expect(buildUsageSuggestion(stale, "highest")).toBeNull();

    const unknown: UsageState = {
      state: "fresh",
      data: {
        ...state.data,
        cursorModels: {
          ...state.data.cursorModels,
          percentUsed: null,
          percentOrigin: null
        }
      }
    };
    expect(pickTriggerMetric(unknown, "cursorModels")).toBeNull();
    expect(pickTriggerMetric(unknown, "highest")?.key).toBe("otherModels");
  });

  it("uses preserved thresholds and upward-only severity de-duplication", () => {
    expect(classifyUrgency(49)).toBe("low");
    expect(classifyUrgency(50)).toBe("moderate");
    expect(classifyUrgency(75)).toBe("high");
    expect(classifyUrgency(95)).toBe("critical");
    const suggestion = buildUsageSuggestion(freshState(), "highest");
    expect(suggestion).toMatchObject({
      bucket: 75,
      severity: "high",
      key: "cursorModels",
      percent: 80
    });
    expect(crossedUnnotifiedThreshold(suggestion, new Map())).toBe(true);
    expect(
      crossedUnnotifiedThreshold(
        suggestion,
        new Map([[suggestion?.notificationKey ?? "", "high"]])
      )
    ).toBe(false);

    const state = freshState();
    const lower = buildUsageSuggestion(
      {
        state: "fresh",
        data: {
          ...state.data,
          cursorModels: { ...state.data.cursorModels, percentUsed: 60 }
        }
      },
      "highest"
    );
    const higher = buildUsageSuggestion(
      {
        state: "fresh",
        data: {
          ...state.data,
          cursorModels: { ...state.data.cursorModels, percentUsed: 99 }
        }
      },
      "highest"
    );
    const notified = new Map([[suggestion?.notificationKey ?? "", "high"] as const]);
    expect(crossedUnnotifiedThreshold(lower, notified)).toBe(false);
    expect(crossedUnnotifiedThreshold(higher, notified)).toBe(true);
  });

  it("uses a stable calendar cycle when all period metadata is missing", () => {
    const state = freshState();
    const withoutPeriod = {
      ...state.data,
      period: { startsAt: null, resetsAt: null }
    };
    const first = buildUsageSuggestion(
      { state: "fresh", data: withoutPeriod },
      "highest"
    );
    const second = buildUsageSuggestion(
      {
        state: "fresh",
        data: {
          ...withoutPeriod,
          fetchedAt: "2026-08-04T18:10:00.000Z"
        }
      },
      "highest"
    );

    expect(first?.notificationKey).toBe(second?.notificationKey);
    expect(
      crossedUnnotifiedThreshold(
        second,
        new Map([[first?.notificationKey ?? "", "high"]])
      )
    ).toBe(false);

    const nextCalendarPeriod = buildUsageSuggestion(
      {
        state: "fresh",
        data: {
          ...withoutPeriod,
          fetchedAt: "2026-09-01T00:10:00.000Z"
        }
      },
      "highest"
    );
    expect(nextCalendarPeriod?.notificationKey).not.toBe(
      first?.notificationKey
    );
    expect(
      crossedUnnotifiedThreshold(
        nextCalendarPeriod,
        new Map([[first?.notificationKey ?? "", "high"]])
      )
    ).toBe(true);
  });

  it("isolates de-duplication by alert metric and threshold policy", () => {
    const state = freshState();
    const original = buildUsageSuggestion(state, "highest");
    const raisedThresholds = { moderate: 85, high: 90, critical: 99 };
    const raisedBelowThreshold = buildUsageSuggestion(
      state,
      "highest",
      raisedThresholds
    );
    expect(raisedBelowThreshold).toBeNull();

    const laterCrossingState: UsageState = {
      state: "fresh",
      data: {
        ...state.data,
        cursorModels: { ...state.data.cursorModels, percentUsed: 86 }
      }
    };
    const raisedCrossing = buildUsageSuggestion(
      laterCrossingState,
      "highest",
      raisedThresholds
    );
    const explicitMetric = buildUsageSuggestion(
      laterCrossingState,
      "cursorModels",
      raisedThresholds
    );
    const notified = new Map([
      [original?.notificationKey ?? "", "high" as const]
    ]);

    expect(raisedCrossing).toMatchObject({
      severity: "moderate",
      bucket: 85
    });
    expect(raisedCrossing?.notificationKey).not.toBe(
      original?.notificationKey
    );
    expect(explicitMetric?.notificationKey).not.toBe(
      raisedCrossing?.notificationKey
    );
    expect(crossedUnnotifiedThreshold(raisedCrossing, notified)).toBe(true);
  });

  it("returns no recommendation below the moderate threshold", () => {
    expect(buildUsageSuggestion(freshState(), "otherModels")).toBeNull();
    expect(
      buildUsageSuggestion({ state: "empty", error: offline }, "highest")
    ).toBeNull();
  });
});
