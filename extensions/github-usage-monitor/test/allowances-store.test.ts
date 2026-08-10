import { beforeEach, describe, expect, it } from "vitest";
import { applyAllowances, applyMetricAllowance } from "../src/providers/allowances";
import { describeFallback, formatResetCountdown, UsageStore, type MementoLike } from "../src/usageStore";
import type { ProviderError, ProviderResult, UsageMetric, UsageSnapshot } from "../src/types";

class FakeMemento implements MementoLike {
  public values = new Map<string, unknown>();

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

const now = Date.UTC(2026, 7, 15);

function metric(kind: UsageMetric["kind"], unit: string, used: number): UsageMetric {
  return {
    kind,
    unit,
    used,
    drawdown: null,
    drawdownBasis: "unavailable",
    allowance: null,
    allowanceSource: "unknown",
    allowanceState: "unknown",
    percentage: null,
    reset: { at: Date.UTC(2026, 8, 1), kind: "reporting-period", label: "month" },
    breakdowns: [],
    grossAmount: null,
    discountAmount: null,
    netAmount: null
  };
}

function snapshot(overrides: Partial<UsageSnapshot> = {}): UsageSnapshot {
  return {
    owner: { scope: "user", name: "fixture-user" },
    periodStart: Date.UTC(2026, 7, 1),
    periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: now,
    source: "api",
    stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 125),
    actionsMinutes: metric("actions-minutes", "minutes", 500),
    actionsStorage: metric("actions-storage", "gigabyte-hours", 20),
    ...overrides
  };
}

describe("allowances", () => {
  it("lets a manual allowance override the plan-derived one", () => {
    // Manual wins because it is the only source that can be right when the published
    // per-plan figure is wrong for an account - data packs, Education benefits, and
    // negotiated terms are all invisible to the API.
    const result = applyMetricAllowance(
      metric("actions-minutes", "minutes", 500),
      {
        planTable: { "actions-minutes": { value: 2000, unit: "minutes" } },
        manual: { "actions-minutes": { value: 3000, unit: "minutes" } }
      },
      { drawdown: 300, drawdownBasis: "reconstructed" }
    );
    expect(result).toMatchObject({ allowance: 3000, allowanceSource: "manual", allowanceState: "verified", percentage: 10 });
  });

  it("uses the plan-derived allowance when the user has set none", () => {
    const result = applyMetricAllowance(
      metric("actions-minutes", "minutes", 500),
      { planTable: { "actions-minutes": { value: 2000, unit: "minutes" } } },
      { drawdown: 500, drawdownBasis: "reconstructed" }
    );
    expect(result).toMatchObject({ allowance: 2000, allowanceSource: "plan-table", allowanceState: "verified", percentage: 25 });
  });

  it("derives the percentage from the drawdown, NEVER from gross usage", () => {
    // The regression fixture for the defect this phase exists to fix. On a real
    // account gross Actions minutes read 1,287 for a month whose allowance drawdown
    // was about 121 against 2,000 included - dividing gross by the allowance renders
    // 64% where the truth is 6%.
    const result = applyMetricAllowance(
      metric("actions-minutes", "minutes", 1287),
      { planTable: { "actions-minutes": { value: 2000, unit: "minutes" } } },
      { drawdown: 120.7, drawdownBasis: "reconstructed" }
    );
    expect(result.percentage).toBeCloseTo(6.035, 3);
    expect(result.percentage).not.toBeCloseTo(64.35, 1);
  });

  it("withholds a percentage when the drawdown could not be reconstructed", () => {
    // A denominator alone is not enough. Without a numerator the honest output is an
    // explained absence, not a percentage derived from gross consumption.
    const result = applyMetricAllowance(
      metric("actions-minutes", "minutes", 1287),
      { planTable: { "actions-minutes": { value: 2000, unit: "minutes" } } },
      { drawdown: null, drawdownBasis: "unavailable" }
    );
    expect(result.allowanceState).toBe("unknown");
    expect(result.percentage).toBeNull();
  });

  it("reports a product with no plan allowance as none, not as unknown", () => {
    // Copilot Free carries no AI-credit entitlement, so the honest answer is that
    // there is nothing to draw against - distinct from a missing measurement.
    const result = applyMetricAllowance(
      metric("copilot-ai-credits", "ai-credits", 125),
      { manual: { "copilot-ai-credits": { value: 250, unit: "ai-credits" } } },
      { drawdown: 125, drawdownBasis: "reported" }
    );
    expect(result.allowanceState).toBe("none");
    expect(result.allowance).toBeNull();
    expect(result.percentage).toBeNull();
  });

  it("never renders 0% or 100% for a null allowance", () => {
    // Data contract line 71 and visual contract line 39, asserted directly.
    for (const kind of ["actions-minutes", "actions-storage", "copilot-ai-credits"] as const) {
      const result = applyMetricAllowance(metric(kind, "minutes", 0), {}, { drawdown: null, drawdownBasis: "unavailable" });
      expect(result.percentage).toBeNull();
      expect(result.percentage).not.toBe(0);
      expect(result.percentage).not.toBe(100);
    }
  });

  it("never produces an api allowance source, because no endpoint serves one", () => {
    const result = applyMetricAllowance(
      metric("actions-minutes", "minutes", 500),
      { planTable: { "actions-minutes": { value: 2000, unit: "minutes" } } },
      { drawdown: 500, drawdownBasis: "reconstructed" }
    );
    expect(result.allowanceSource).not.toBe("api");
  });

  it.each([
    { value: 0, unit: "ai-credits" },
    { value: -1, unit: "ai-credits" },
    { value: Number.NaN, unit: "ai-credits" },
    { value: 100, unit: "premium-requests" }
  ])("keeps invalid or mismatched allowance unknown", (candidate) => {
    const result = applyMetricAllowance(metric("copilot-ai-credits", "ai-credits", 125), {
      manual: { "copilot-ai-credits": candidate }
    });
    expect(result).toMatchObject({ allowance: null, allowanceSource: "unknown", percentage: null });
  });

  it("applies independent allowances across a snapshot", () => {
    const result = applyAllowances(
      snapshot(),
      {
        manual: {
          "copilot-ai-credits": { value: 250, unit: "ai-credits" },
          "actions-minutes": { value: 1000, unit: "minutes" }
        }
      },
      { "actions-minutes": { drawdown: 500, drawdownBasis: "reconstructed" } }
    );
    // Copilot has no plan allowance at all, so it is none regardless of any value set.
    expect(result.copilot.allowanceState).toBe("none");
    expect(result.copilot.percentage).toBeNull();
    expect(result.actionsMinutes.percentage).toBe(50);
    // Storage got no drawdown input, so it stays unknown rather than guessing.
    expect(result.actionsStorage.percentage).toBeNull();
    expect(result.actionsStorage.allowanceState).toBe("unknown");
  });
});

describe("UsageStore", () => {
  let memento: FakeMemento;
  let store: UsageStore;

  beforeEach(() => {
    memento = new FakeMemento();
    store = new UsageStore(memento, 60_000);
  });

  it("saves fresh API data and labels it stale only after the threshold", async () => {
    await store.saveSuccess(snapshot());
    expect(store.get(now + 59_999)?.stale).toBe(false);
    expect(store.get(now + 60_000)?.stale).toBe(true);
  });

  it("returns fresh state and persists successful fetches", async () => {
    const result: ProviderResult<UsageSnapshot> = {
      ok: true,
      value: snapshot(),
      rate: { remaining: 10, resetAt: null, retryAfterMs: null }
    };
    await expect(store.resolveFetch(result, now)).resolves.toMatchObject({ state: "fresh" });
    expect(store.get(now)).toBeDefined();
  });

  it("returns stale cache with an error and never converts failure to zero", async () => {
    await store.saveSuccess(snapshot());
    const error: ProviderError = { code: "network-error", message: "offline" };
    const result = await store.resolveFetch({ ok: false, error, rate: { remaining: null, resetAt: null, retryAfterMs: null } }, now);
    expect(result).toMatchObject({ state: "stale", error, data: { source: "cache", stale: true } });
    expect(result.data?.copilot.used).toBe(125);
  });

  it("returns an actionable empty state when no cache exists", async () => {
    const error: ProviderError = { code: "invalid-token", message: "invalid" };
    await expect(
      store.resolveFetch({ ok: false, error, rate: { remaining: null, resetAt: null, retryAfterMs: null } }, now)
    ).resolves.toEqual({ state: "empty", error });
  });

  it("detects expired resets only when the snapshot predates the boundary", async () => {
    await store.saveSuccess(snapshot({ fetchedAt: Date.UTC(2026, 7, 31) }));
    expect(store.hasExpiredReset(Date.UTC(2026, 8, 1))).toBe(true);
    await store.saveSuccess(snapshot({ fetchedAt: Date.UTC(2026, 8, 1) }));
    expect(store.hasExpiredReset(Date.UTC(2026, 8, 1))).toBe(false);
  });

  it("clears alert deduplication only after a new API cycle", async () => {
    await store.saveSuccess(snapshot());
    await store.markThresholdNotified(75);
    await store.markThresholdNotified(75);
    expect(store.getAlertCycle()?.notifiedThresholds).toEqual([75]);

    await store.saveManualSnapshot(snapshot({ periodStart: Date.UTC(2026, 8, 1), source: "manual" }));
    expect(store.getAlertCycle()?.notifiedThresholds).toEqual([75]);

    await store.saveSuccess(snapshot({ periodStart: Date.UTC(2026, 8, 1) }));
    expect(store.getAlertCycle()?.notifiedThresholds).toEqual([]);
  });

  it("supports manual data and complete clearing", async () => {
    await store.saveManualSnapshot(snapshot());
    expect(store.get(now)?.source).toBe("manual");
    await store.clear();
    expect(store.get(now)).toBeUndefined();
    expect(store.getAlertCycle()).toBeUndefined();
    expect(store.hasExpiredReset(now)).toBe(false);
  });
});

describe("store labels", () => {
  it.each([
    [30_000, "1 min"],
    [60 * 60_000, "1h"],
    [90 * 60_000, "1h 30m"],
    [-1, "refresh due"]
  ])("formats reset countdown", (offset, expected) => {
    expect(formatResetCountdown(now + offset, now)).toBe(expected);
  });

  it("describes cache and empty fallbacks explicitly", () => {
    const error: ProviderError = { code: "network-error", message: "offline" };
    expect(describeFallback(error, true)).toContain("last-known-good");
    expect(describeFallback(error, false)).toContain("No usage data");
  });
});
