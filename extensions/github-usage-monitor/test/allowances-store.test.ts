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
    allowance: null,
    allowanceSource: "unknown",
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
  it("prefers a verified API allowance and calculates percentage", () => {
    const result = applyMetricAllowance(metric("actions-minutes", "minutes", 500), {
      api: { "actions-minutes": { value: 2000, unit: "minutes" } },
      manual: { "actions-minutes": { value: 3000, unit: "minutes" } }
    });
    expect(result).toMatchObject({ allowance: 2000, allowanceSource: "api", percentage: 25 });
  });

  it("uses an exact-unit manual allowance when API allowance is absent", () => {
    const result = applyMetricAllowance(metric("actions-storage", "gigabyte-hours", 20), {
      manual: { "actions-storage": { value: 100, unit: "gigabyte-hours" } }
    });
    expect(result).toMatchObject({ allowance: 100, allowanceSource: "manual", percentage: 20 });
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
    const result = applyAllowances(snapshot(), {
      manual: {
        "copilot-ai-credits": { value: 250, unit: "ai-credits" },
        "actions-minutes": { value: 1000, unit: "minutes" }
      }
    });
    expect(result.copilot.percentage).toBe(50);
    expect(result.actionsMinutes.percentage).toBe(50);
    expect(result.actionsStorage.percentage).toBeNull();
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
