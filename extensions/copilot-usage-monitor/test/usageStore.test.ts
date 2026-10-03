import { describe, expect, it } from "vitest";
import type { UsageData } from "../src/types";
import {
  UsageStore,
  formatCreditCount,
  formatCredits,
  formatElapsed,
  formatPercent,
  formatResetLabel,
  nextMonthlyResetAt,
} from "../src/usageStore";
import { createMemento } from "./helpers";

const NOW = Date.UTC(2026, 9, 2, 0, 5);

describe("UsageStore", () => {
  it("saves, reads, and clears the cache and the last urgency", async () => {
    const store = new UsageStore(createMemento());
    expect(store.get()).toBeUndefined();
    expect(store.getTimeSinceUpdate()).toBe("never");
    expect(store.hasResetExpired()).toBe(false);
    const data: UsageData = { lastUpdated: NOW - 5 * 60_000, dataSource: "api" };
    await store.save(data);
    await store.saveLastUrgency("high");
    expect(store.get()).toEqual(data);
    expect(store.getLastUrgency()).toBe("high");
    expect(store.getTimeSinceUpdate(NOW)).toBe("5 min ago");
    await store.clear();
    expect(store.get()).toBeUndefined();
    expect(store.getLastUrgency()).toBeUndefined();
  });

  it("detects a monthly reset that passed after the last fetch", async () => {
    const store = new UsageStore(createMemento());
    const resetsAt = Date.UTC(2026, 10, 1);
    await store.save({
      personal: { planLabel: "Copilot Free", quotas: [], primary: null, creditsUsed: 0, resetsAt },
      lastUpdated: resetsAt - 1,
      dataSource: "api",
    });
    expect(store.hasResetExpired(resetsAt - 10)).toBe(false);
    expect(store.hasResetExpired(resetsAt + 10)).toBe(true);
  });
});

describe("formatters", () => {
  it.each([
    [0, "0"],
    [0.0068198, "0.01"],
    [99.2481, "99.25"],
    [100, "100"],
    [120, "100"],
    [-3, "0"],
    [42.5, "42.5"],
  ])("formatPercent(%f) = %s", (value, text) => {
    expect(formatPercent(value)).toBe(text);
  });

  it("formats credits with two decimals and counts as whole numbers", () => {
    expect(formatCredits(0.9069921)).toBe("0.91");
    expect(formatCredits(13_200)).toBe("13,200.00");
    expect(formatCreditCount(13_300)).toBe("13,300");
  });

  it.each([
    [30_000, "just now"],
    [5 * 60_000, "5 min ago"],
    [3 * 3_600_000, "3h ago"],
    [3 * 86_400_000, "3d ago"],
  ])("formatElapsed(%i) = %s", (ms, text) => {
    expect(formatElapsed(ms)).toBe(text);
  });

  it("computes the next monthly reset in UTC and labels it", () => {
    expect(nextMonthlyResetAt(NOW)).toBe(Date.UTC(2026, 10, 1));
    expect(nextMonthlyResetAt(Date.UTC(2026, 11, 31, 23))).toBe(Date.UTC(2027, 0, 1));
    expect(formatResetLabel(Date.UTC(2026, 10, 1))).toBe("Resets on November 1");
    expect(formatResetLabel(null)).toBe("Reset date not reported");
  });
});
