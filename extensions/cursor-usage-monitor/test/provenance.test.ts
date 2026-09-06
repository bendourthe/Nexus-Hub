import { describe, expect, it, vi } from "vitest";
import { COMMAND_IDS, CursorUsageRuntime } from "../src/extension";
import { buildManualSnapshot, type ManualSnapshotInput } from "../src/manualEntry";
import type { UsageSnapshot } from "../src/types";
import {
  describeProvenance,
  snapshotProvenance,
  UsageStore,
  type MementoLike
} from "../src/usageStore";
import {
  createExtensionContext,
  informationMessages,
  registeredCommandIds,
  resetVscodeStub,
  runRegisteredCommand,
  warningMessages,
  warningResponses
} from "./vscode-stub";

const now = Date.parse("2026-08-05T12:00:00Z");

class FakeMemento implements MementoLike {
  public readonly values = new Map<string, unknown>();
  public failUpdate = false;

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (this.failUpdate) {
      throw new Error("state unavailable");
    }
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

function manualInput(): ManualSnapshotInput {
  return {
    cursorModels: { used: 80, limit: 100, unit: "requests" },
    otherModels: { used: 40, limit: 100, unit: "requests" },
    onDemandEnabled: false,
    personalSpend: null,
    periodStartsAt: "2026-08-01T00:00:00Z",
    resetsAt: "2026-09-01T00:00:00Z"
  };
}

function snapshot(source: "credential-api" | "manual"): UsageSnapshot {
  const result = buildManualSnapshot(manualInput(), now);
  if (!result.ok) {
    throw new Error(result.errors.join(" "));
  }
  return { ...result.value, source };
}

describe("snapshotProvenance", () => {
  it("reports live, cache, and manual distinctly", () => {
    expect(snapshotProvenance(snapshot("credential-api"))).toBe("live");
    expect(snapshotProvenance(snapshot("manual"))).toBe("manual");
    expect(
      snapshotProvenance({
        ...snapshot("credential-api"),
        source: "cache",
        cachedFrom: "credential-api"
      })
    ).toBe("cache");
  });

  it("keeps cached manual data described as manual, not as cached live data", () => {
    // Otherwise a user who typed their numbers would be told they came from Cursor.
    expect(
      snapshotProvenance({
        ...snapshot("manual"),
        source: "cache",
        cachedFrom: "manual"
      })
    ).toBe("manual");
  });
});

describe("describeProvenance", () => {
  it("names the origin without a staleness clause when fresh", () => {
    expect(describeProvenance(snapshot("credential-api"))).toBe(
      "Live Cursor usage"
    );
    expect(describeProvenance(snapshot("manual"))).toBe(
      "Manually entered usage"
    );
  });

  it("always states staleness and its reason when stale", () => {
    const stale = describeProvenance({
      ...snapshot("credential-api"),
      source: "cache",
      cachedFrom: "credential-api",
      stale: true,
      staleReason: "authentication-required"
    });
    expect(stale).toContain("Cached Cursor usage");
    expect(stale).toContain("stale");
    expect(stale).toContain("re-authorizing");
  });

  it("covers every stale reason with readable text", () => {
    const reasons = [
      "age-threshold",
      "fetch-failed",
      "rate-limited",
      "authentication-required",
      "visibility-restricted",
      "schema-drift",
      "period-reset-passed",
      "allowance-unavailable"
    ] as const;
    for (const staleReason of reasons) {
      const text = describeProvenance({
        ...snapshot("credential-api"),
        stale: true,
        staleReason
      });
      expect(text).toContain("stale:");
      expect(text).not.toContain("undefined");
    }
  });
});

describe("UsageStore.clearCache", () => {
  it("drops credential-derived cache and keeps manual data", async () => {
    const memento = new FakeMemento();
    const store = new UsageStore(memento, 30 * 60_000);
    await store.saveSuccess(snapshot("credential-api"));
    await store.saveManual(snapshot("manual"));

    await store.clearCache();

    expect(store.getCache(now)).toBeUndefined();
    expect(store.getManual(now)).toBeDefined();
  });

  it("restores the previous cache when the write fails", async () => {
    const memento = new FakeMemento();
    const store = new UsageStore(memento, 30 * 60_000);
    await store.saveSuccess(snapshot("credential-api"));

    memento.failUpdate = true;
    await expect(store.clearCache()).rejects.toThrow();
    memento.failUpdate = false;
    expect(memento.values.has("cursorUsage.snapshot")).toBe(true);
  });
});

describe("revoke consent command", () => {
  it("is registered on the command surface", () => {
    resetVscodeStub();
    const context = createExtensionContext();
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: false,
      now: () => now
    });
    runtime.start();
    expect(registeredCommandIds()).toContain(COMMAND_IDS.revokeConsent);
    runtime.dispose();
    resetVscodeStub();
  });

  it("clears the consent decision and the live cache in one action", async () => {
    resetVscodeStub();
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.snapshot",
      snapshot("credential-api")
    );
    context.globalState.values.set("cursorUsage.manual", snapshot("manual"));
    context.globalState.values.set("cursorUsage.liveTransportConsent", {
      decision: "granted",
      scope: "state-db-allowlisted-key+usage-json/v1",
      decidedAt: "2026-08-05T00:00:00Z"
    });

    const revokeLiveConsent = vi.fn(async () => {
      await context.globalState.update(
        "cursorUsage.liveTransportConsent",
        undefined
      );
    });
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: true,
      revokeLiveConsent,
      now: () => now
    });
    runtime.start();

    warningResponses.push("Revoke");
    await runRegisteredCommand(COMMAND_IDS.revokeConsent);

    expect(revokeLiveConsent).toHaveBeenCalledOnce();
    expect(context.globalState.values.has("cursorUsage.snapshot")).toBe(false);
    expect(
      context.globalState.values.has("cursorUsage.liveTransportConsent")
    ).toBe(false);
    // Manually entered usage is the user's own and is deliberately preserved.
    expect(context.globalState.values.has("cursorUsage.manual")).toBe(true);
    expect(informationMessages.at(-1)).toContain("revoked");
    runtime.dispose();
    resetVscodeStub();
  });

  it("does nothing when the confirmation is declined", async () => {
    resetVscodeStub();
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.snapshot",
      snapshot("credential-api")
    );
    const revokeLiveConsent = vi.fn(async () => undefined);
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: true,
      revokeLiveConsent,
      now: () => now
    });
    runtime.start();

    warningResponses.push(undefined);
    await runRegisteredCommand(COMMAND_IDS.revokeConsent);

    expect(revokeLiveConsent).not.toHaveBeenCalled();
    expect(context.globalState.values.has("cursorUsage.snapshot")).toBe(true);
    runtime.dispose();
    resetVscodeStub();
  });

  it("keeps data displayed when the purge cannot be persisted", async () => {
    resetVscodeStub();
    const context = createExtensionContext();
    context.globalState.values.set(
      "cursorUsage.snapshot",
      snapshot("credential-api")
    );
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch: vi.fn() },
      liveTransportCapable: true,
      revokeLiveConsent: async () => {
        throw new Error("consent state unavailable");
      },
      now: () => now
    });
    runtime.start();

    warningResponses.push("Revoke");
    await runRegisteredCommand(COMMAND_IDS.revokeConsent);

    expect(warningMessages.at(-1)).toContain("could not fully revoke");
    runtime.dispose();
    resetVscodeStub();
  });
});

describe("capability thunk", () => {
  it("starts polling only once capability flips to true", async () => {
    resetVscodeStub();
    const context = createExtensionContext();
    let capable = false;
    const fetch = vi.fn(async () => ({
      ok: false as const,
      error: {
        code: "session-expired" as const,
        message: "expired",
        sourceAttempt: "credential-api" as const,
        recoverable: true
      }
    }));

    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch },
      liveTransportCapable: () => capable,
      now: () => now
    });
    runtime.start();
    await Promise.resolve();
    expect(fetch).not.toHaveBeenCalled();

    capable = true;
    runtime.capabilityChanged();
    await Promise.resolve();
    await Promise.resolve();
    expect(fetch).toHaveBeenCalled();

    runtime.dispose();
    resetVscodeStub();
  });

  it("ignores a capability change before start and after dispose", () => {
    resetVscodeStub();
    const context = createExtensionContext();
    const fetch = vi.fn();
    const runtime = new CursorUsageRuntime(context as never, {
      provider: { fetch },
      liveTransportCapable: () => true,
      now: () => now
    });

    runtime.capabilityChanged();
    expect(fetch).not.toHaveBeenCalled();

    runtime.start();
    runtime.dispose();
    runtime.capabilityChanged();
    resetVscodeStub();
  });
});
