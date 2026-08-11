import { beforeEach, describe, expect, it } from "vitest";
import {
  evaluateInstallChange,
  initialWatcherState,
  registerUpdateWatcher,
  restartMessage,
  runningIsStale,
  type UpdateWatcherState
} from "../src/updateWatcher";
import { messages, resetVscodeStub, setInstalledExtension, stubExtension } from "./vscode-stub";

/**
 * Cover for the silent-stale-build gap observed 2026-08-10: `--install-extension`
 * reported 0.3.1 installed while the window kept running 0.3.0, so a fix was tested
 * against the build that still contained the bug.
 */

/** Feeds a sequence of observed installed-versions through the watcher. */
function replay(running: string, observations: readonly (string | undefined)[]): {
  prompts: number;
  state: UpdateWatcherState;
} {
  let state = initialWatcherState();
  let prompts = 0;
  for (const observed of observations) {
    const evaluation = evaluateInstallChange(state, running, observed);
    state = evaluation.state;
    if (evaluation.prompt) prompts += 1;
  }
  return { prompts, state };
}

describe("evaluateInstallChange", () => {
  it("stays quiet while the installed version matches the running one", () => {
    expect(replay("0.3.0", ["0.3.0", "0.3.0", "0.3.0"]).prompts).toBe(0);
  });

  it("prompts on a version bump", () => {
    const { prompts, state } = replay("0.3.0", ["0.3.1"]);

    expect(prompts).toBe(1);
    expect(state.prompted).toBe(true);
  });

  it("prompts on a same-version reinstall, which a version check alone would miss", () => {
    // What the Nexus-Hub installers actually do: uninstall, then install --force.
    // The versions match on both sides, so the absence is the only evidence.
    expect(replay("0.3.0", [undefined, "0.3.0"]).prompts).toBe(1);
  });

  it("does not prompt while the extension is merely absent", () => {
    const { prompts, state } = replay("0.3.0", [undefined, undefined]);

    expect(prompts).toBe(0);
    expect(state.seenMissing).toBe(true);
  });

  it("offers the restart exactly once, however many events follow", () => {
    expect(replay("0.3.0", ["0.3.1", "0.3.1", undefined, "0.3.2", "0.3.2"]).prompts).toBe(1);
  });
});

describe("registerUpdateWatcher", () => {
  beforeEach(() => resetVscodeStub());

  /** The minimum of an ExtensionContext this watcher touches. */
  function context(version: string): { subscriptions: Array<{ dispose(): void }>; extension: ReturnType<typeof stubExtension> } {
    return { subscriptions: [], extension: stubExtension("nexus-hub.github-usage-monitor", version) };
  }

  it("offers a restart when a newer build lands underneath the running one", () => {
    const host = context("0.3.0");
    registerUpdateWatcher(host as never, "GitHub Usage Monitor");

    setInstalledExtension("nexus-hub.github-usage-monitor", "0.3.1");

    expect(messages.information).toHaveLength(1);
    expect(messages.information[0]).toContain("still running 0.3.0");
  });

  it("survives the installers' uninstall-then-reinstall at an unchanged version", () => {
    const host = context("0.3.0");
    registerUpdateWatcher(host as never, "GitHub Usage Monitor");

    setInstalledExtension("nexus-hub.github-usage-monitor", undefined);
    expect(messages.information).toHaveLength(0);

    setInstalledExtension("nexus-hub.github-usage-monitor", "0.3.0");
    expect(messages.information).toHaveLength(1);
    expect(messages.information[0]).toContain("reinstalled");
  });

  it("ignores changes to OTHER extensions", () => {
    // Registered first, because that is the real state: this extension is installed
    // while it runs. Without it the assertion would pass down the "absent" path and
    // prove nothing about sibling extensions.
    setInstalledExtension("nexus-hub.github-usage-monitor", "0.3.0");
    const host = context("0.3.0");
    registerUpdateWatcher(host as never, "GitHub Usage Monitor");

    setInstalledExtension("nexus-hub.claude-usage-monitor", "0.9.6");
    setInstalledExtension("nexus-hub.codex-usage-monitor", "0.2.7");

    expect(messages.information).toHaveLength(0);
  });

  it("registers a disposable so the listener does not outlive deactivation", () => {
    const host = context("0.3.0");
    registerUpdateWatcher(host as never, "GitHub Usage Monitor");

    expect(host.subscriptions).toHaveLength(1);
  });
});

describe("runningIsStale", () => {
  beforeEach(() => resetVscodeStub());

  function host(version: string): { subscriptions: Array<{ dispose(): void }>; extension: ReturnType<typeof stubExtension> } {
    return { subscriptions: [], extension: stubExtension("nexus-hub.github-usage-monitor", version) };
  }

  it("detects a window running code an install has superseded", () => {
    // The cross-window loop, confirmed 2026-08-11: reloading ONE window leaves every
    // other window executing its old code, and because global configuration writes
    // reach every window, that old code keeps participating.
    setInstalledExtension("nexus-hub.github-usage-monitor", "0.3.2");

    expect(runningIsStale(host("0.3.1") as never)).toBe(true);
  });

  it("says nothing is stale when the versions agree", () => {
    setInstalledExtension("nexus-hub.github-usage-monitor", "0.3.1");

    expect(runningIsStale(host("0.3.1") as never)).toBe(false);
  });

  it("treats an unreadable registry as up to date, never as stale", () => {
    // Silencing a window on missing evidence would disable a perfectly current one.
    expect(runningIsStale(host("0.3.1") as never)).toBe(false);
  });
});

describe("restartMessage", () => {
  it("names both versions on an update", () => {
    const message = restartMessage("GitHub Usage Monitor", "0.3.0", "0.3.1");

    expect(message).toContain("updated to 0.3.1");
    expect(message).toContain("still running 0.3.0");
  });

  it("says reinstalled rather than updated when the version is unchanged", () => {
    const message = restartMessage("GitHub Usage Monitor", "0.3.0", "0.3.0");

    expect(message).toContain("reinstalled");
    expect(message).not.toContain("updated to");
  });
});
