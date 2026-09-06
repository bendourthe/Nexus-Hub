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

  // v3.14.6: settings moved inline into the dashboard, so there is no gear item -
  // only the single usage item. Its priority (105) sits above the Codex monitor's
  // 103 and above GitHub Copilot's ~100.5 slot, so the usage items group together
  // with Copilot to their right ("Copilot last").
  it("creates a single usage item at priority 105 (no gear item)", () => {
    __resetStubState();
    new StatusBarManager(emptyStore, "claude-usage.dashboard");
    expect(createdStatusBarItems).toHaveLength(1);
    expect(createdStatusBarItems[0].priority).toBe(105);
  });

  // v3.14.5 Phase 5.2: compact-mode toggle drops the "Claude Usage: " label.
  it("shows the full label by default and drops it when compactStatusBar is set", () => {
    __resetStubState();
    const mgr = new StatusBarManager(emptyStore, "claude-usage.dashboard");

    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(claude-icon)\u2002Claude Usage: --% (current) --% (week)");

    __setStubConfig("claudeUsage", "compactStatusBar", true);
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(claude-icon)\u2002--% (current) --% (week)");
  });
});
