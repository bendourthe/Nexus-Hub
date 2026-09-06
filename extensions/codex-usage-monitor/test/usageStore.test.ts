import type * as vscode from "vscode";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { UsageData } from "../src/types";
import {
  UsageStore,
  formatCreditCount,
  formatCreditUsageLine,
  formatResetLabel,
  formatResetTime,
  nextMonthlyResetAt,
  nextMonthlyResetLabel,
} from "../src/usageStore";

const NOW = Date.UTC(2026, 7, 2, 16, 0, 0);

function createMemento(): { memento: vscode.Memento; values: Map<string, unknown> } {
  const values = new Map<string, unknown>();
  const memento = {
    get<T>(key: string, defaultValue?: T): T | undefined {
      return values.has(key) ? values.get(key) as T : defaultValue;
    },
    async update(key: string, value: unknown): Promise<void> {
      if (value === undefined) {
        values.delete(key);
      } else {
        values.set(key, value);
      }
    },
    keys(): readonly string[] {
      return [...values.keys()];
    },
  } as vscode.Memento;
  return { memento, values };
}

function usageData(overrides: Partial<UsageData> = {}): UsageData {
  return {
    session: { percent: 20, resetsIn: "stale", resetsAt: NOW + 30 * 60_000 },
    weeklyAllModels: { percent: 30, resetsIn: "stale", resetsAt: NOW + 2 * 60 * 60_000 },
    currentModel: "Codex",
    lastUpdated: NOW,
    dataSource: "api",
    planLabel: "ChatGPT Plus",
    ...overrides,
  };
}

describe("UsageStore", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => vi.useRealTimers());

  it("returns empty-state values before data is saved", () => {
    const { memento } = createMemento();
    const store = new UsageStore(memento);

    expect(store.get()).toBeUndefined();
    expect(store.getWithFreshCountdowns()).toBeUndefined();
    expect(store.hasResetExpired()).toBe(false);
    expect(store.getTimeSinceUpdate()).toBe("never");
    expect(store.getLastUrgency()).toBeUndefined();
    expect(store.getSuggestionState()).toEqual({ notifiedThresholds: [] });
  });

  it("saves data and refreshes all tracked countdowns without mutating stored data", async () => {
    const { memento } = createMemento();
    const store = new UsageStore(memento);
    const data = usageData({
      extraCredits: {
        usedCredits: 750,
        monthlyLimit: 5_000,
        percent: 15,
        resetsIn: "stale",
        resetsAt: NOW + 90 * 60_000,
      },
    });

    await store.save(data);
    const fresh = store.getWithFreshCountdowns();

    expect(store.get()).toBe(data);
    expect(fresh?.session.resetsIn).toBe("30 min");
    expect(fresh?.weeklyAllModels.resetsIn).toBe("2h");
    expect(fresh?.extraCredits?.resetsIn).toBe("1h 30m");
    expect(data.extraCredits?.resetsIn).toBe("stale");
  });

  it("detects only reset windows that expired after the stored data was fetched", async () => {
    const { memento } = createMemento();
    const store = new UsageStore(memento);
    await store.save(usageData({
      lastUpdated: NOW - 2 * 60_000,
      session: { percent: 20, resetsIn: "expired", resetsAt: NOW - 60_000 },
      weeklyAllModels: { percent: 30, resetsIn: "future", resetsAt: NOW + 60_000 },
    }));
    expect(store.hasResetExpired()).toBe(true);

    await store.save(usageData({
      lastUpdated: NOW,
      session: { percent: 20, resetsIn: "expired", resetsAt: NOW - 60_000 },
      weeklyAllModels: { percent: 30, resetsIn: "N/A", resetsAt: null },
    }));
    expect(store.hasResetExpired()).toBe(false);
  });

  it("persists urgency and suggestion state, then clears every stored key", async () => {
    const { memento, values } = createMemento();
    const store = new UsageStore(memento);
    await store.save(usageData());
    await store.saveLastUrgency("high");
    await store.saveSuggestionState({ notifiedThresholds: [50, 75] });

    expect(store.getLastUrgency()).toBe("high");
    expect(store.getSuggestionState()).toEqual({ notifiedThresholds: [50, 75] });

    await store.clear();
    expect(values.size).toBe(0);
  });

  it.each([
    [NOW - 30_000, "just now"],
    [NOW - 17 * 60_000, "17 min ago"],
    [NOW - 3 * 60 * 60_000, "3h ago"],
    [NOW - 2 * 24 * 60 * 60_000, "2d ago"],
  ])("formats the last-update age for %s", async (lastUpdated, expected) => {
    const { memento } = createMemento();
    const store = new UsageStore(memento);
    await store.save(usageData({ lastUpdated }));
    expect(store.getTimeSinceUpdate()).toBe(expected);
  });
});

describe("usage reset formatting", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => vi.useRealTimers());

  it("formats elapsed, minute, hour, and multi-day reset windows", () => {
    expect(formatResetTime(NOW - 1)).toBe("any moment");
    expect(formatResetTime(NOW + 45 * 60_000)).toBe("45 min");
    expect(formatResetTime(NOW + 2 * 60 * 60_000)).toBe("2h");
    expect(formatResetTime(NOW + 2 * 60 * 60_000 + 15 * 60_000)).toBe("2h 15m");
    expect(formatResetTime(NOW + 3 * 24 * 60 * 60_000 + 4 * 60 * 60_000 + 15 * 60_000))
      .toMatch(/\(3d 4h 15m\)$/);
  });

  it("formats reset labels, monthly boundaries, and credit amounts", () => {
    expect(formatResetLabel("Tuesday July 7th at 7:00 AM")).toBe("Resets on Tuesday July 7th at 7:00 AM");
    expect(formatResetLabel("August 1")).toBe("Resets on August 1");
    expect(formatResetLabel("N/A")).toBe("Resets N/A");
    expect(formatResetLabel("any moment")).toBe("Resets any moment");
    expect(formatResetLabel("2h 15m")).toBe("Resets in 2h 15m");
    expect(nextMonthlyResetLabel()).toBe("September 1");
    expect(nextMonthlyResetAt()).toBe(Date.UTC(2026, 8, 1));
    expect(nextMonthlyResetAt(Date.UTC(2026, 11, 31))).toBe(Date.UTC(2027, 0, 1));
    expect(formatCreditCount(5_000)).toBe("5,000");
    expect(formatCreditCount(836.88)).toBe("837");
    expect(formatCreditUsageLine({
      usedCredits: 836.88,
      monthlyLimit: 5_000,
      percent: 17,
      resetsIn: "2d",
      resetsAt: NOW + 2 * 24 * 60 * 60_000,
      usedAmountUsd: 33.4752,
      limitAmountUsd: 200,
    })).toBe("837 out of 5,000 credits used ($33.48 / $200.00)");
    expect(formatCreditUsageLine({
      usedCredits: 836.88,
      monthlyLimit: 5_000,
      percent: 17,
      resetsIn: "2d",
      resetsAt: NOW + 2 * 24 * 60 * 60_000,
      usedAmountUsd: 33.4752,
    })).toBe("837 out of 5,000 credits used");
  });
});
