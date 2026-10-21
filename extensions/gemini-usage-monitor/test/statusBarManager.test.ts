import { afterEach, describe, expect, it } from "vitest";
import { StatusBarManager } from "../src/statusBarManager";
import type { UsageStore } from "../src/usageStore";
import { UNTRACKED_PERCENT, type UsageMetricRow } from "../src/types";
import { __resetStubState, __setStubConfig, createdStatusBarItems } from "./vscode-stub";

/** A minimal no-data store; enough to exercise the constructor priority scheme. */
const emptyStore = {
  getWithFreshCountdowns: () => undefined,
  getTimeSinceUpdate: () => "just now",
  hasResetExpired: () => false,
} as unknown as UsageStore;

/**
 * A store returning one usage record. `session`/`weekly` percentages may be
 * UNTRACKED_PERCENT to model a window the account does not expose. Exercises the
 * data path (adaptive status text + the now-stubbed MarkdownString tooltip).
 */
function dataStore(session: number, weekly: number, additionalLimits?: UsageMetricRow[]): UsageStore {
  const data = {
    session: { percent: session, resetsIn: "N/A", resetsAt: null },
    weeklyAllModels: { percent: weekly, resetsIn: "N/A", resetsAt: null },
    currentModel: "Gemini Models",
    lastUpdated: Date.now(),
    dataSource: "manual" as const,
    planLabel: "Google AI Pro",
    additionalLimits,
  };
  return {
    getWithFreshCountdowns: () => data,
    getTimeSinceUpdate: () => "just now",
    hasResetExpired: () => false,
  } as unknown as UsageStore;
}

describe("StatusBarManager (Antigravity)", () => {
  afterEach(() => __resetStubState());

  // v3.14.6: settings moved inline into the dashboard, so there is no gear item -
  // only the single usage item. Its priority (103) sits below the Claude monitor's
  // 105 and above GitHub Copilot's ~100.5 slot, so the usage items group together
  // with Copilot to their right ("Copilot last").
  it("creates a single usage item at priority 103 (no gear item)", () => {
    __resetStubState();
    new StatusBarManager(emptyStore, "gemini-usage.dashboard");
    expect(createdStatusBarItems).toHaveLength(1);
    expect(createdStatusBarItems[0].priority).toBe(103);
  });

  // v3.14.5 Phase 5.2: compact-mode toggle drops the "Gemini Usage: " label; compact is the default.
  it("is compact by default and shows the full label when compactStatusBar is off", () => {
    __resetStubState();
    const mgr = new StatusBarManager(dataStore(42, 10), "gemini-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(gemini-icon)\u200242% (current) 10% (week)");

    __setStubConfig("geminiUsage", "compactStatusBar", false);
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(gemini-icon)\u2002Gemini Usage: 42% (current) 10% (week)");
  });

  // v3.14.6 issue 3: a weekly-only plan (no 5-hour "session" window) must not
  // render a dead "--% (current)"; only the tracked window(s) appear.
  it("omits the untracked 5-hour window from the status bar (weekly-only plan)", () => {
    __resetStubState();
    const mgr = new StatusBarManager(dataStore(UNTRACKED_PERCENT, 91), "gemini-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(gemini-icon)\u200291% (week)");
  });

  it("renders the other model group as tooltip rows after the Gemini pair", () => {
    __resetStubState();
    const mgr = new StatusBarManager(
      dataStore(20, 10, [
        { label: "Claude and GPT Models: Current Session", percent: 25, resetsIn: "2h", resetsAt: null },
        { label: "Claude & GPT <beta>: Weekly", percent: 40, resetsIn: "4d", resetsAt: null },
      ]),
      "gemini-usage.dashboard",
    );

    mgr.refresh();
    const tooltip = createdStatusBarItems[0].tooltip as { value: string };
    expect(tooltip.value).toContain(encodeURIComponent("Gemini Models: Weekly"));
    expect(tooltip.value).toContain(encodeURIComponent("Claude and GPT Models: Current Session"));
    // Server-provided labels are escaped before they enter the inline SVG.
    expect(tooltip.value).toContain(encodeURIComponent("Claude &amp; GPT &lt;beta&gt;: Weekly"));
    expect(tooltip.value.indexOf(encodeURIComponent("Gemini Models: Weekly")))
      .toBeLessThan(tooltip.value.indexOf(encodeURIComponent("Claude and GPT Models: Current Session")));
  });

  it("shows a single -- placeholder when there is no data at all", () => {
    __resetStubState();
    const mgr = new StatusBarManager(emptyStore, "gemini-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(gemini-icon)\u2002--");
  });
});
