import { afterEach, describe, expect, it } from "vitest";
import { StatusBarManager } from "../src/statusBarManager";
import type { UsageStore } from "../src/usageStore";
import { __resetStubState, __setStubConfig, createdStatusBarItems } from "./vscode-stub";

/**
 * A minimal store whose only used method returns no data. The no-data path is
 * all `refresh()` needs to exercise the priority scheme (constructor) and the
 * compact-label logic (`statusText`), and it avoids the data-path tooltip which
 * needs the host-only `vscode.MarkdownString`.
 */
const emptyStore = {
  getWithFreshCountdowns: () => undefined,
  getTimeSinceUpdate: () => "just now",
  hasResetExpired: () => false,
} as unknown as UsageStore;

describe("StatusBarManager (Claude)", () => {
  afterEach(() => __resetStubState());

  // v3.14.5 Phase 5.1: the cross-extension priority scheme is load-bearing
  // (Claude 103/102 must outrank the Codex monitor's 101/100 so the items read
  // [Claude usage][Claude gear][Codex usage][Codex gear] left-to-right).
  it("creates the usage item at priority 103 and the gear at 102", () => {
    __resetStubState();
    new StatusBarManager(emptyStore, "claude-usage.dashboard", "claude-usage.settings");
    expect(createdStatusBarItems).toHaveLength(2);
    expect(createdStatusBarItems[0].priority).toBe(103); // usage item (created first)
    expect(createdStatusBarItems[1].priority).toBe(102); // gear
  });

  // v3.14.5 Phase 5.2: compact-mode toggle drops the "Claude Usage: " label.
  it("shows the full label by default and drops it when compactStatusBar is set", () => {
    __resetStubState();
    const mgr = new StatusBarManager(emptyStore, "claude-usage.dashboard", "claude-usage.settings");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(claude-icon) Claude Usage: --% (current) --% (week)");

    __setStubConfig("claudeUsage", "compactStatusBar", true);
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(claude-icon) --% (current) --% (week)");
  });
});
