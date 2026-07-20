import { afterEach, describe, expect, it } from "vitest";
import { StatusBarManager } from "../src/statusBarManager";
import type { UsageStore } from "../src/usageStore";
import { UNTRACKED_PERCENT } from "../src/types";
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
function dataStore(session: number, weekly: number): UsageStore {
  const data = {
    session: { percent: session, resetsIn: "N/A", resetsAt: null },
    weeklyAllModels: { percent: weekly, resetsIn: "N/A", resetsAt: null },
    currentModel: "Codex",
    lastUpdated: Date.now(),
    dataSource: "manual" as const,
    planLabel: "Codex",
  };
  return {
    getWithFreshCountdowns: () => data,
    getTimeSinceUpdate: () => "just now",
    hasResetExpired: () => false,
  } as unknown as UsageStore;
}

describe("StatusBarManager (Codex)", () => {
  afterEach(() => __resetStubState());

  // v3.14.6: settings moved inline into the dashboard, so there is no gear item -
  // only the single usage item. Its priority (103) sits below the Claude monitor's
  // 105 and above GitHub Copilot's ~100.5 slot, so the usage items group together
  // with Copilot to their right ("Copilot last").
  it("creates a single usage item at priority 103 (no gear item)", () => {
    __resetStubState();
    new StatusBarManager(emptyStore, "codex-usage.dashboard");
    expect(createdStatusBarItems).toHaveLength(1);
    expect(createdStatusBarItems[0].priority).toBe(103);
  });

  // v3.14.5 Phase 5.2: compact-mode toggle drops the "Codex Usage: " label.
  it("shows the full label by default and drops it when compactStatusBar is set", () => {
    __resetStubState();
    const mgr = new StatusBarManager(dataStore(42, 10), "codex-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon)\u2002Codex Usage: 42% (current) 10% (week)");

    __setStubConfig("codexUsage", "compactStatusBar", true);
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon)\u200242% (current) 10% (week)");
  });

  // v3.14.6 issue 3: a weekly-only plan (no 5-hour "session" window) must not
  // render a dead "--% (current)"; only the tracked window(s) appear.
  it("omits the untracked 5-hour window from the status bar (weekly-only plan)", () => {
    __resetStubState();
    const mgr = new StatusBarManager(dataStore(UNTRACKED_PERCENT, 91), "codex-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon)\u2002Codex Usage: 91% (week)");
  });

  it("shows a single -- placeholder when there is no data at all", () => {
    __resetStubState();
    const mgr = new StatusBarManager(emptyStore, "codex-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon)\u2002Codex Usage: --");
  });
});
