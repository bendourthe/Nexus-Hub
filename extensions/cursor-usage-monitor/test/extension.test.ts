import { afterEach, describe, expect, it, vi } from "vitest";
import {
  activate,
  COMMAND_IDS,
  CursorUsageRuntime,
  deactivate
} from "../src/extension";
import { buildManualSnapshot, type ManualSnapshotInput } from "../src/manualEntry";
import type { ProviderResult, UsageSnapshot } from "../src/types";
import {
  configuration,
  createExtensionContext,
  executedCommands,
  fireConfigurationChange,
  informationMessages,
  inputResponses,
  openExternalUris,
  registeredCommandIds,
  resetVscodeStub,
  runRegisteredCommand,
  setConfiguration,
  statusItems,
  warningMessages,
  webviewPanels,
  warningResponses
} from "./vscode-stub";

const now = Date.parse("2026-08-04T18:00:00Z");

function manualInput(
  cursorUsed = 80,
  otherUsed = 40
): ManualSnapshotInput {
  return {
    cursorModels: { used: cursorUsed, limit: 100, unit: "requests" },
    otherModels: { used: otherUsed, limit: 100, unit: "requests" },
    onDemandEnabled: true,
    personalSpend: { amount: 12.5, currency: "USD" },
    periodStartsAt: "2026-08-01T00:00:00Z",
    resetsAt: "2026-09-01T00:00:00Z"
  };
}

function snapshot(
  source: "credential-api" | "manual",
  cursorUsed: number
): UsageSnapshot {
  const result = buildManualSnapshot(manualInput(cursorUsed), now);
  if (!result.ok) {
    throw new Error(result.errors.join(" "));
  }
  return { ...result.value, source };
}

function createTimeoutHarness(): {
  setTimeout: (callback: () => void, delay: number) => never;
  clearTimeout: ReturnType<typeof vi.fn>;
  flush(): void;
  pending(): number;
} {
  let nextId = 1;
  const callbacks = new Map<number, () => void>();
  const clearTimeout = vi.fn((handle: unknown) => {
    callbacks.delete(handle as number);
  });
  return {
    setTimeout(callback: () => void): never {
      const id = nextId;
      nextId += 1;
      callbacks.set(id, callback);
      return id as never;
    },
    clearTimeout,
    flush(): void {
      const pending = [...callbacks.values()];
      callbacks.clear();
      for (const callback of pending) {
        callback();
      }
    },
    pending(): number {
      return callbacks.size;
    }
  };
}

afterEach(() => {
  deactivate();
  resetVscodeStub();
  vi.restoreAllMocks();
});

describe("Cursor usage extension lifecycle", () => {
  it("registers the complete command and warning-view surface without live polling", async () => {
    const context = createExtensionContext();
    setConfiguration("cursorUsage.autoFetch", true);

    activate(context as never);
    await Promise.resolve();

    expect(registeredCommandIds()).toEqual(
      expect.arrayContaining(Object.values(COMMAND_IDS))
    );
    expect(statusItems).toHaveLength(1);
    expect(statusItems[0]).toMatchObject({ shown: true });
    expect(statusItems[0]?.text).toContain("--");
    expect(executedCommands).toContainEqual({
      command: "setContext",
      args: ["cursorUsage.warningActive", false]
    });
  });

  it("hydrates cache before manual data and manual before empty", () => {
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.snapshot",
      snapshot("credential-api", 25)
    );
    context.globalState.values.set("cursorUsage.manual", snapshot("manual", 80));

    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now
    });
    runtime.start();
    expect(statusItems[0]?.text).toContain("Cursor 25%");
    runtime.dispose();

    resetVscodeStub();
    const manualOnly = createExtensionContext();
    manualOnly.globalState.values.set(
      "cursorUsage.manual",
      snapshot("manual", 80)
    );
    const manualRuntime = new CursorUsageRuntime(manualOnly as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now
    });
    manualRuntime.start();
    expect(statusItems[0]?.text).toContain("Cursor 80%");
    manualRuntime.dispose();
  });

  it("persists manual entry, evaluates fresh thresholds, and clears all state", async () => {
    const context = createExtensionContext();
    activate(context as never);

    await runRegisteredCommand(COMMAND_IDS.manualEntry, manualInput(80));
    expect(context.globalState.values.get("cursorUsage.manual")).toMatchObject({
      source: "manual",
      cursorModels: { percentUsed: 80 }
    });
    expect(statusItems[0]?.text).toContain("Cursor 80%");
    expect(executedCommands).toContainEqual({
      command: "setContext",
      args: ["cursorUsage.warningActive", true]
    });

    warningResponses.push("Clear");
    await runRegisteredCommand(COMMAND_IDS.clearData);
    expect(context.globalState.values.has("cursorUsage.snapshot")).toBe(false);
    expect(context.globalState.values.has("cursorUsage.manual")).toBe(false);
    expect(statusItems[0]?.text).toContain("--");
    // Dismissing does two things, in this order: clear the context so the view
    // hides, then return the side bar to the Explorer. Without the second step the
    // bar stays parked on an empty container and the dismiss looks like it failed.
    await expectDismissRestoresExplorer(executedCommands);
  });

  it("alerts once per meter severity and only on upward crossings without reset metadata", async () => {
    const context = createExtensionContext();
    activate(context as never);
    const withoutCycle = {
      ...manualInput(80),
      periodStartsAt: null,
      resetsAt: null
    };

    await runRegisteredCommand(COMMAND_IDS.manualEntry, withoutCycle);
    const initialAlerts = executedCommands.filter(
      (entry) => entry.command === "setContext" && entry.args[1] === true
    ).length;
    await runRegisteredCommand(COMMAND_IDS.manualEntry, withoutCycle);
    await runRegisteredCommand(COMMAND_IDS.manualEntry, {
      ...withoutCycle,
      cursorModels: { used: 60, limit: 100, unit: "requests" }
    });
    expect(
      executedCommands.filter(
        (entry) => entry.command === "setContext" && entry.args[1] === true
      )
    ).toHaveLength(initialAlerts);

    await runRegisteredCommand(COMMAND_IDS.manualEntry, {
      ...withoutCycle,
      cursorModels: { used: 99, limit: 100, unit: "requests" }
    });
    expect(
      executedCommands.filter(
        (entry) => entry.command === "setContext" && entry.args[1] === true
      )
    ).toHaveLength(initialAlerts + 1);
  });

  it("starts new fallback cycles and honors raised threshold policies", async () => {
    let currentNow = now;
    const context = createExtensionContext();
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => currentNow
    });
    runtime.start();
    const withoutCycle = {
      ...manualInput(80),
      periodStartsAt: null,
      resetsAt: null
    };

    await runRegisteredCommand(COMMAND_IDS.manualEntry, withoutCycle);
    const firstCycleAlerts = executedCommands.filter(
      (entry) => entry.command === "setContext" && entry.args[1] === true
    ).length;

    currentNow = Date.parse("2026-09-01T18:00:00Z");
    await runRegisteredCommand(COMMAND_IDS.manualEntry, withoutCycle);
    expect(
      executedCommands.filter(
        (entry) =>
          entry.command === "setContext" &&
          entry.args[1] === true
      )
    ).toHaveLength(firstCycleAlerts + 1);

    setConfiguration("cursorUsage.thresholds.moderate", 85);
    setConfiguration("cursorUsage.thresholds.high", 90);
    setConfiguration("cursorUsage.thresholds.critical", 99);
    fireConfigurationChange("cursorUsage.thresholds");
    await Promise.resolve();
    await runRegisteredCommand(COMMAND_IDS.manualEntry, {
      ...withoutCycle,
      cursorModels: { used: 86, limit: 100, unit: "requests" }
    });
    expect(
      executedCommands.filter(
        (entry) =>
          entry.command === "setContext" &&
          entry.args[1] === true
      )
    ).toHaveLength(firstCycleAlerts + 2);
    runtime.dispose();
  });

  it("wires dashboard, settings, recommendation, and transportless refresh commands", async () => {
    const context = createExtensionContext();
    activate(context as never);
    await runRegisteredCommand(COMMAND_IDS.manualEntry, manualInput(80));

    await runRegisteredCommand(COMMAND_IDS.dashboard);
    await runRegisteredCommand(COMMAND_IDS.settings);
    await runRegisteredCommand(COMMAND_IDS.recommend);
    await runRegisteredCommand(COMMAND_IDS.refresh);

    expect(webviewPanels).toHaveLength(2);
    expect(webviewPanels[0]?.webview.html).toContain("Cursor Models");
    expect(webviewPanels[1]?.webview.html).toContain(
      "Cursor Usage Settings"
    );
    // v3.15.12: the refusal notice names the provenance of what is on screen
    // instead of citing HO-5, so the user is told which data they are looking at
    // rather than an internal gap id.
    const notice = informationMessages.at(-1) ?? "";
    expect(notice).toContain("live refresh is unavailable");
    expect(notice).toContain("manually entered usage");
    expect(notice).not.toContain("HO-5");
  });

  it("validates interactive manual JSON without persisting invalid input", async () => {
    const context = createExtensionContext();
    activate(context as never);
    inputResponses.push("{not-json");

    await runRegisteredCommand(COMMAND_IDS.manualEntry);

    expect(warningMessages.at(-1)).toContain("valid JSON");
    expect(context.globalState.values.has("cursorUsage.manual")).toBe(false);
  });

  it("does not alert on stale hydration and updates surfaces on configuration changes", () => {
    const timeouts = createTimeoutHarness();
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.manual",
      snapshot("manual", 80)
    );
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => Date.parse("2026-08-04T20:00:00Z"),
      setTimeout: timeouts.setTimeout,
      clearTimeout: timeouts.clearTimeout
    });
    runtime.start();
    expect(
      executedCommands.filter(
        (entry) =>
          entry.command === "setContext" &&
          entry.args[1] === true
      )
    ).toHaveLength(0);

    setConfiguration("cursorUsage.compactStatusBar", true);
    fireConfigurationChange("cursorUsage.compactStatusBar");
    timeouts.flush();
    expect(statusItems[0]?.text).toContain("C 80%");
    expect(statusItems[0]?.text).not.toContain("Cursor Usage:");

    setConfiguration("cursorUsage.showInStatusBar", false);
    fireConfigurationChange("cursorUsage.showInStatusBar");
    timeouts.flush();
    expect(statusItems[0]?.shown).toBe(false);
    runtime.dispose();
  });

  it("coalesces sequential threshold saves into one final alert evaluation", async () => {
    const timeouts = createTimeoutHarness();
    const context = createExtensionContext();
    context.globalState.values.set("cursorUsage.manual", snapshot("manual", 80));
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now,
      setTimeout: timeouts.setTimeout,
      clearTimeout: timeouts.clearTimeout
    });
    runtime.start();
    await Promise.resolve();
    const alertsBeforeSave = executedCommands.filter(
      (entry) => entry.command === "setContext" && entry.args[1] === true
    ).length;

    for (const [key, value] of [
      ["cursorUsage.thresholds.moderate", 20],
      ["cursorUsage.thresholds.high", 40],
      ["cursorUsage.thresholds.critical", 60]
    ] as const) {
      setConfiguration(key, value);
      fireConfigurationChange(key);
    }

    expect(timeouts.pending()).toBe(1);
    expect(
      executedCommands.filter(
        (entry) => entry.command === "setContext" && entry.args[1] === true
      )
    ).toHaveLength(alertsBeforeSave);

    timeouts.flush();
    await Promise.resolve();
    expect(
      executedCommands.filter(
        (entry) => entry.command === "setContext" && entry.args[1] === true
      )
    ).toHaveLength(alertsBeforeSave + 1);
    runtime.dispose();
  });

  it("evaluates only the restored policy after rollback and cancels pending work on disposal", async () => {
    const timeouts = createTimeoutHarness();
    const context = createExtensionContext();
    context.globalState.values.set("cursorUsage.manual", snapshot("manual", 80));
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now,
      setTimeout: timeouts.setTimeout,
      clearTimeout: timeouts.clearTimeout
    });
    runtime.start();
    await Promise.resolve();
    const alertsBeforeRollback = executedCommands.filter(
      (entry) => entry.command === "setContext" && entry.args[1] === true
    ).length;

    setConfiguration("cursorUsage.thresholds.moderate", 20);
    fireConfigurationChange("cursorUsage.thresholds.moderate");
    setConfiguration("cursorUsage.thresholds.moderate", 50);
    fireConfigurationChange("cursorUsage.thresholds.moderate");

    expect(timeouts.pending()).toBe(1);
    timeouts.flush();
    await Promise.resolve();
    expect(
      executedCommands.filter(
        (entry) => entry.command === "setContext" && entry.args[1] === true
      )
    ).toHaveLength(alertsBeforeRollback);

    setConfiguration("cursorUsage.thresholds.moderate", 25);
    fireConfigurationChange("cursorUsage.thresholds.moderate");
    expect(timeouts.pending()).toBe(1);
    runtime.dispose();
    expect(timeouts.pending()).toBe(0);
    expect(timeouts.clearTimeout).toHaveBeenCalled();
  });

  it("coalesces overlapping refreshes and aborts the active request on disposal", async () => {
    let resolveFetch:
      | ((result: ProviderResult<UsageSnapshot>) => void)
      | undefined;
    let capturedSignal: AbortSignal | undefined;
    const fetch = vi.fn(
      (signal?: AbortSignal) =>
        new Promise<ProviderResult<UsageSnapshot>>((resolve) => {
          capturedSignal = signal;
          resolveFetch = resolve;
        })
    );
    const scheduled: Array<() => void> = [];
    const clearInterval = vi.fn();
    const context = createExtensionContext();
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch },
      liveTransportCapable: true,
      now: () => now,
      setInterval: (callback) => {
        scheduled.push(callback);
        return 1 as never;
      },
      clearInterval
    });
    runtime.start();
    const first = runtime.refresh();
    const second = runtime.refresh();

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(scheduled).toHaveLength(1);
    runtime.dispose();
    expect(capturedSignal?.aborted).toBe(true);
    expect(clearInterval).toHaveBeenCalledWith(1);
    expect(registeredCommandIds()).toEqual([]);
    expect(statusItems[0]?.shown).toBe(false);

    resolveFetch?.({ ok: true, value: snapshot("credential-api", 30) });
    await Promise.all([first, second]);
    expect(context.globalState.values.has("cursorUsage.snapshot")).toBe(false);
  });

  it("persists an authorized injected transport result and refreshes open surfaces", async () => {
    setConfiguration("cursorUsage.autoFetch", false);
    const context = createExtensionContext();
    const runtime = new CursorUsageRuntime(context as never, {
      provider: {
        fetch: vi.fn(async () => ({
          ok: true as const,
          value: snapshot("credential-api", 30)
        }))
      },
      liveTransportCapable: true,
      now: () => now
    });
    runtime.start();

    await runtime.refresh();

    expect(context.globalState.values.get("cursorUsage.snapshot")).toMatchObject({
      source: "credential-api",
      cursorModels: { percentUsed: 30 }
    });
    expect(statusItems[0]?.text).toContain("Cursor 30%");
    expect(informationMessages.at(-1)).toContain("refreshed");
    runtime.dispose();
  });

  it("serializes clear behind in-flight refresh persistence", async () => {
    setConfiguration("cursorUsage.autoFetch", false);
    const context = createExtensionContext();
    let releaseSnapshotWrite: (() => void) | undefined;
    const originalUpdate = context.globalState.update.bind(context.globalState);
    context.globalState.update = vi.fn(async (key: string, value: unknown) => {
      if (key === "cursorUsage.snapshot" && value !== undefined) {
        await new Promise<void>((resolve) => {
          releaseSnapshotWrite = resolve;
        });
      }
      await originalUpdate(key, value);
    });
    const runtime = new CursorUsageRuntime(context as never, {
      provider: {
        fetch: vi.fn(async () => ({
          ok: true as const,
          value: snapshot("credential-api", 80)
        }))
      },
      liveTransportCapable: true,
      now: () => now
    });
    runtime.start();

    const refresh = runtime.refresh();
    await vi.waitFor(() => expect(releaseSnapshotWrite).toBeTypeOf("function"));
    warningResponses.push("Clear");
    const clear = runRegisteredCommand(COMMAND_IDS.clearData);
    await Promise.resolve();
    expect(context.globalState.update).toHaveBeenCalledTimes(1);

    releaseSnapshotWrite?.();
    await Promise.all([refresh, clear]);

    expect(context.globalState.values.has("cursorUsage.snapshot")).toBe(false);
    expect(context.globalState.values.has("cursorUsage.manual")).toBe(false);
    expect(statusItems[0]?.text).toContain("--");
    runtime.dispose();
  });

  it("surfaces fixed safe feedback when refresh persistence fails", async () => {
    setConfiguration("cursorUsage.autoFetch", false);
    const context = createExtensionContext();
    context.globalState.update = vi.fn(async () => {
      throw new Error("sensitive persistence detail");
    });
    const runtime = new CursorUsageRuntime(context as never, {
      provider: {
        fetch: vi.fn(async () => ({
          ok: true as const,
          value: snapshot("credential-api", 80)
        }))
      },
      liveTransportCapable: true,
      now: () => now
    });
    runtime.start();

    await expect(runtime.refresh()).resolves.toBeUndefined();

    expect(statusItems[0]?.text).toContain("--");
    expect(warningMessages.at(-1)).toBe(
      "Cursor Usage: could not save refreshed usage. Existing data remains displayed."
    );
    expect(warningMessages.join(" ")).not.toContain("sensitive");
    runtime.dispose();
  });

  it("keeps prior UI state and surfaces fixed feedback when manual or clear persistence fails", async () => {
    const context = createExtensionContext();
    context.globalState.values.set("cursorUsage.manual", snapshot("manual", 80));
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now
    });
    runtime.start();
    context.globalState.update = vi.fn(async () => {
      throw new Error("sensitive persistence detail");
    });

    await expect(
      runRegisteredCommand(COMMAND_IDS.manualEntry, manualInput(90))
    ).resolves.toBeUndefined();
    expect(warningMessages.at(-1)).toBe(
      "Cursor Usage: could not save manual usage. Existing data remains displayed."
    );
    expect(statusItems[0]?.text).toContain("Cursor 80%");

    warningResponses.push("Clear");
    await expect(
      runRegisteredCommand(COMMAND_IDS.clearData)
    ).resolves.toBeUndefined();
    expect(warningMessages.at(-1)).toBe(
      "Cursor Usage: could not clear stored usage. Existing data remains displayed."
    );
    expect(statusItems[0]?.text).toContain("Cursor 80%");
    expect(warningMessages.join(" ")).not.toContain("sensitive");
    runtime.dispose();
  });

  it("fails soft through manual fallback when an injected transport fails", async () => {
    setConfiguration("cursorUsage.autoFetch", false);
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.manual",
      snapshot("manual", 80)
    );
    const runtime = new CursorUsageRuntime(context as never, {
      provider: {
        fetch: vi.fn(async () => ({
          ok: false as const,
          error: {
            code: "network-error" as const,
            message: "offline",
            sourceAttempt: "html-scrape" as const,
            recoverable: true
          }
        }))
      },
      liveTransportCapable: true,
      now: () => now
    });
    runtime.start();
    await Promise.resolve();
    const alertsBeforeFailure = executedCommands.filter(
      (entry) => entry.args[1] === true
    ).length;

    await runtime.refresh();

    expect(statusItems[0]?.text).toContain("$(warning)");
    expect(informationMessages.at(-1)).toContain("offline");
    expect(
      executedCommands.filter((entry) => entry.args[1] === true)
    ).toHaveLength(alertsBeforeFailure);
    await expectDismissRestoresExplorer(executedCommands);
    runtime.dispose();
  });

  it("opens native settings and the Cursor usage page without exposing credentials", async () => {
    const context = createExtensionContext();
    activate(context as never);

    await runRegisteredCommand(COMMAND_IDS.openNativeSettings);
    await runRegisteredCommand(COMMAND_IDS.openUsagePage);

    expect(executedCommands).toContainEqual({
      command: "workbench.action.openSettings",
      args: ["@ext:nexus-hub.cursor-usage-monitor"]
    });
    expect(openExternalUris).toContain(
      "https://cursor.com/dashboard/usage"
    );
    expect(
      [...configuration.keys()].some((key) => /credential|token|secret/iu.test(key))
    ).toBe(false);
    expect(informationMessages.join(" ")).not.toMatch(
      /credential|token|secret/iu
    );
  });
});

/**
 * Dismissing the warning must clear the context AND return the side bar to the
 * Explorer, in that order. Asserted as "the last clear is immediately followed by
 * the Explorer" rather than by absolute position, because a single action can
 * dismiss more than once (clearing data dismisses, and the resulting state change
 * dismisses again) and pinning `at(-2)` makes the test depend on that count.
 */
async function expectDismissRestoresExplorer(
  commands: ReadonlyArray<{ command: string; args: readonly unknown[] }>
): Promise<void> {
  // The runtime fires dismiss() without awaiting it, and dismiss awaits the
  // setContext before switching views, so the Explorer command lands a microtask
  // after the caller returns. Flush before asserting rather than pinning the
  // assertion to whichever half has completed.
  await new Promise((resolve) => setTimeout(resolve, 0));
  const index = commands.findLastIndex(
    (entry) =>
      entry.command === "setContext" &&
      entry.args[0] === "cursorUsage.warningActive" &&
      entry.args[1] === false
  );
  expect(index).toBeGreaterThan(-1);
  expect(commands[index + 1]).toEqual({
    command: "workbench.view.explorer",
    args: []
  });
}
