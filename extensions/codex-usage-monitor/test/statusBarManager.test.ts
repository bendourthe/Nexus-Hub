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

describe("StatusBarManager (Codex)", () => {
  afterEach(() => __resetStubState());

  // v3.14.5 Phase 5.1: the cross-extension priority scheme is load-bearing
  // (Codex 101/100 must sit below the Claude monitor's 103/102). Lock it so a
  // future edit cannot silently reintroduce the collision the two extensions had.
  it("creates the usage item at priority 101 and the gear at 100", () => {
    __resetStubState();
    new StatusBarManager(emptyStore, "codex-usage.dashboard", "codex-usage.settings");
    expect(createdStatusBarItems).toHaveLength(2);
    expect(createdStatusBarItems[0].priority).toBe(101); // usage item (created first)
    expect(createdStatusBarItems[1].priority).toBe(100); // gear
  });

  // v3.14.5 Phase 5.2: compact-mode toggle drops the "Codex Usage: " label.
  it("shows the full label by default and drops it when compactStatusBar is set", () => {
    __resetStubState();
    const mgr = new StatusBarManager(emptyStore, "codex-usage.dashboard", "codex-usage.settings");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon) Codex Usage: --% (current) --% (week)");

    __setStubConfig("codexUsage", "compactStatusBar", true);
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(codex-icon) --% (current) --% (week)");
  });
});
