import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { providerError } from "../src/providers/errors";
import { normalizeSnapshotPayload } from "../src/providers/normalizer";
import type { UsageSnapshot } from "../src/types";
import {
  refreshSnapshot,
  UsageStore,
  type MementoLike
} from "../src/usageStore";

class FakeMemento implements MementoLike {
  public readonly values = new Map<string, unknown>();

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

function snapshot(source: UsageSnapshot["source"] = "credential-api"): UsageSnapshot {
  const path = resolve(
    __dirname,
    "../../../tests/fixtures/cursor-usage/included-usage-healthy.json"
  );
  const payload = JSON.parse(readFileSync(path, "utf8")) as unknown;
  const result = normalizeSnapshotPayload(
    payload,
    source === "cache"
      ? { source, cachedFrom: "credential-api" }
      : { source }
  );
  if (!result.ok) {
    throw new Error("fixture failed to normalize");
  }
  return result.value;
}

describe("UsageStore", () => {
  it("saves live success and returns a normalized cache view", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    expect(store.getCache(Date.parse("2026-08-04T16:10:00Z"))).toMatchObject({
      source: "cache",
      cachedFrom: "credential-api",
      stale: false,
      staleReason: null
    });
  });

  it("resolves success as fresh and persists it", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    const value = snapshot("html-scrape");
    const result = await store.resolveFetch({ ok: true, value });
    expect(result).toEqual({ state: "fresh", data: value });
    expect(state.values.has("cursorUsage.snapshot")).toBe(true);
  });

  it("uses cache before manual fallback and maps auth staleness", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    await store.saveManual(snapshot("manual"));
    const error = providerError("session-expired", "credential-api");
    const result = await store.resolveFetch(
      { ok: false, error },
      Date.parse("2026-08-04T16:10:00Z")
    );
    expect(result.state).toBe("stale");
    expect(result.data).toMatchObject({
      source: "cache",
      stale: true,
      staleReason: "authentication-required"
    });
  });

  it("uses manual data when cache is absent", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveManual(snapshot("manual"));
    const error = providerError("network-error", "html-scrape");
    const result = await store.resolveFetch(
      { ok: false, error },
      Date.parse("2026-08-04T16:10:00Z")
    );
    expect(result.data).toMatchObject({
      source: "manual",
      stale: true,
      staleReason: "fetch-failed"
    });
  });

  it("returns empty when no fallback exists", async () => {
    const store = new UsageStore(new FakeMemento());
    const error = providerError("endpoint-unavailable", "html-scrape");
    expect(await store.resolveFetch({ ok: false, error })).toEqual({
      state: "empty",
      error
    });
  });

  it("rejects corrupt or wrong-source persisted snapshots", () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    state.values.set("cursorUsage.snapshot", {
      source: "credential-api",
      fetchedAt: "not-an-iso-timestamp"
    });
    state.values.set("cursorUsage.manual", snapshot());
    expect(store.getCache()).toBeUndefined();
    expect(store.getManual()).toBeUndefined();
    expect(store.hasExpiredReset()).toBe(false);
  });

  it("marks cache stale at the exact age threshold", async () => {
    const value = snapshot();
    const now = Date.parse(value.fetchedAt) + 5 * 60_000;
    expect(refreshSnapshot(value, now - 1, 5 * 60_000, true).stale).toBe(
      false
    );
    expect(refreshSnapshot(value, now, 5 * 60_000, true)).toMatchObject({
      source: "cache",
      stale: true,
      staleReason: "age-threshold"
    });
  });

  it("suppresses prior-period percentages after reset", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    const resetAt = Date.parse("2026-09-01T00:00:00Z");
    const cached = store.getCache(resetAt);
    expect(cached).toMatchObject({
      source: "cache",
      stale: true,
      staleReason: "period-reset-passed",
      cursorModels: { percentUsed: null, percentOrigin: null },
      otherModels: { percentUsed: null, percentOrigin: null }
    });
    expect(store.hasExpiredReset(resetAt)).toBe(true);
  });

  it("preserves reset-crossing reason over fetch errors", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    const error = providerError("rate-limited", "credential-api");
    const result = await store.resolveFetch(
      { ok: false, error },
      Date.parse("2026-09-01T00:00:00Z")
    );
    expect(result.data?.staleReason).toBe("period-reset-passed");
  });

  it.each([
    ["rate-limited", "rate-limited"],
    ["dashboard-visibility-restricted", "visibility-restricted"],
    ["json-schema-mismatch", "schema-drift"]
  ] as const)("maps %s fallback errors to %s", async (code, reason) => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    const error = providerError(code, "credential-api");
    const result = await store.resolveFetch(
      { ok: false, error },
      Date.parse("2026-08-04T16:10:00Z")
    );
    expect(result.data?.staleReason).toBe(reason);
  });

  it("rejects non-live snapshots passed to saveSuccess", async () => {
    const store = new UsageStore(new FakeMemento());
    await expect(store.saveSuccess(snapshot("cache"))).rejects.toThrow(
      "requires a live Cursor usage source"
    );
  });

  it("clears both normalized cache and manual fallback", async () => {
    const state = new FakeMemento();
    const store = new UsageStore(state);
    await store.saveSuccess(snapshot());
    await store.saveManual(snapshot("manual"));
    await store.clear();
    expect(store.getCache()).toBeUndefined();
    expect(store.getManual()).toBeUndefined();
    expect(store.hasExpiredReset()).toBe(false);
  });
});
