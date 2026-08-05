import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";
import { CursorUsageProvider } from "../src/providers/cursor";
import {
  CURSOR_USAGE_ORIGIN,
  CURSOR_WIRE_CONTRACT,
  CursorLiveUsageTransport,
  mapWirePayload,
  readPath,
  type HttpJsonClient,
  type HttpJsonResponse
} from "../src/providers/liveTransport";
import { normalizeSnapshotPayload } from "../src/providers/normalizer";
import { UsageStore, type MementoLike } from "../src/usageStore";
import type { FreshUsageSnapshot, UsageSnapshot } from "../src/types";

const SESSION = "fixture-session-token-abcdef0123456789";

function fixture(name: string): Record<string, unknown> {
  const path = fileURLToPath(
    new URL(`../../../tests/fixtures/cursor-usage/${name}`, import.meta.url)
  );
  return JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
}

class StubClient implements HttpJsonClient {
  public calls: Array<{ url: string; headers: Record<string, string> }> = [];

  public constructor(private readonly responses: HttpJsonResponse[]) {}

  public async getJson(
    url: string,
    headers: Readonly<Record<string, string>>
  ): Promise<HttpJsonResponse> {
    this.calls.push({ url, headers: { ...headers } });
    const next = this.responses.shift();
    if (next === undefined) {
      throw new Error("no scripted response remains");
    }
    return next;
  }
}

class ThrowingClient implements HttpJsonClient {
  public constructor(private readonly error: unknown) {}

  public async getJson(): Promise<HttpJsonResponse> {
    throw this.error;
  }
}

describe("wire contract", () => {
  it("matches the committed fixture exactly", () => {
    const declared = fixture("wire-contract.json");
    expect(declared.version).toBe(CURSOR_WIRE_CONTRACT.version);
    expect(declared.route).toBe(CURSOR_WIRE_CONTRACT.route);
    expect(declared.fields).toEqual(CURSOR_WIRE_CONTRACT.fields);
    expect(declared.units).toEqual(CURSOR_WIRE_CONTRACT.units);
    expect(declared.requiredFields).toEqual(
      CURSOR_WIRE_CONTRACT.requiredFields
    );
  });

  it("is recorded as unverified in both the code and the fixture", () => {
    // Load-bearing: the route is a discovery lead, not a confirmed contract, and
    // nothing in the repository may imply otherwise until the maintainer probes it.
    expect(CURSOR_WIRE_CONTRACT.verified).toBe(false);
    const declared = fixture("wire-contract.json");
    const contract = declared.fixtureContract as Record<string, unknown>;
    expect(contract.verified).toBe(false);
    expect(contract.source).toBe("credential-api");
    expect(contract.provenance).toBe("expected-shape-unverified");
  });

  it("never labels the undocumented route as a public API", () => {
    const declared = fixture("wire-contract.json");
    const contract = declared.fixtureContract as Record<string, unknown>;
    expect(contract.source).toBe("credential-api");

    // The note may discuss the forbidden label; no structural VALUE may carry it.
    const { fixtureContract: _note, ...structure } = declared;
    expect(JSON.stringify(structure)).not.toContain("public-api");
    expect(Object.values(contract)).not.toContain("public-api");
  });

  it("resolves dot-paths and treats a null leaf as absent", () => {
    const payload = { a: { b: { c: 1 }, d: null } };
    expect(readPath(payload, "a.b.c")).toBe(1);
    expect(readPath(payload, "a.d")).toBeUndefined();
    expect(readPath(payload, "a.b.missing")).toBeUndefined();
    expect(readPath(payload, "a.b.c.deeper")).toBeUndefined();
  });
});

describe("mapWirePayload", () => {
  it("maps the expected wire shape onto the normalized envelope", () => {
    const result = mapWirePayload(fixture("wire-usage-summary.json"));
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }

    // The envelope must survive the existing normalizer unchanged, which is what
    // keeps the live path on the same typed contract as cache and manual.
    const normalized = normalizeSnapshotPayload(result.value, {
      source: "credential-api",
      fetchedAt: "2026-08-05T12:00:00Z"
    });
    expect(normalized.ok).toBe(true);
    if (!normalized.ok) {
      return;
    }
    const snapshot = normalized.value;
    expect(snapshot.source).toBe("credential-api");
    expect(snapshot.stale).toBe(false);
    expect(snapshot.cursorModels.used).toEqual({
      value: 345000,
      unit: "tokens"
    });
    expect(snapshot.cursorModels.percentUsed).toBe(34.5);
    expect(snapshot.cursorModels.percentOrigin).toBe("source");
    expect(snapshot.otherModels.percentUsed).toBe(1.7);
    expect(snapshot.period.resetsAt).toBe("2026-09-01T00:00:00Z");
  });

  it("converts minor currency units and keeps the limit as team context", () => {
    const result = mapWirePayload(fixture("wire-usage-summary.json"));
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    const envelope = result.value as {
      onDemand: { enabled: boolean; personalSpend: unknown };
      teamContext: { sharedSpendLimit: unknown; dynamicSpendLimit: unknown };
    };

    expect(envelope.onDemand).toEqual({
      enabled: true,
      personalSpend: { amount: 12.5, currency: "USD" }
    });
    // The spend limit is the team's shared pool. Recording it as team context is
    // what stops it being rendered as a personal cap.
    expect(envelope.teamContext.sharedSpendLimit).toEqual({
      amount: 200,
      currency: "USD"
    });
    expect(envelope.teamContext.dynamicSpendLimit).toBe(false);
  });

  it("rejects a renamed pool rather than coercing it", () => {
    const result = mapWirePayload(fixture("wire-field-drift.json"));
    expect(!result.ok && result.error.code).toBe("json-schema-mismatch");
    expect(!result.ok && result.error.sourceAttempt).toBe("credential-api");
  });

  it("rejects a payload that self-declares a different unit", () => {
    const result = mapWirePayload(fixture("wire-unit-drift.json"));
    expect(!result.ok && result.error.code).toBe("unit-mismatch");
  });

  it("rejects a declared money unit that disagrees with the contract", () => {
    const payload = fixture("wire-usage-summary.json");
    (payload.onDemand as Record<string, unknown>).amountUnit = "currency-major";
    expect(!mapWirePayload(payload).ok).toBe(true);
  });

  it.each(CURSOR_WIRE_CONTRACT.requiredFields)(
    "rejects a payload missing %s",
    (field) => {
      const payload = fixture("wire-usage-summary.json");
      const path = CURSOR_WIRE_CONTRACT.fields[field];
      const segments = path.split(".");
      const leaf = segments.pop() ?? "";
      let cursor = payload as Record<string, unknown>;
      for (const segment of segments) {
        cursor = cursor[segment] as Record<string, unknown>;
      }
      delete cursor[leaf];

      const result = mapWirePayload(payload);
      expect(!result.ok && result.error.code).toBe("json-schema-mismatch");
    }
  );

  it.each([null, 42, "text", [], undefined])(
    "rejects a non-object payload",
    (payload) => {
      expect(!mapWirePayload(payload).ok).toBe(true);
    }
  );

  it("omits spend entirely when on-demand is disabled", () => {
    const payload = fixture("wire-usage-summary.json");
    (payload.onDemand as Record<string, unknown>).enabled = false;
    const result = mapWirePayload(payload);
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect((result.value as { onDemand: unknown }).onDemand).toEqual({
      enabled: false,
      personalSpend: null
    });
  });

  it("keeps a pool at 100 percent distinguishable from a near-empty one", () => {
    const payload = fixture("wire-usage-summary.json");
    const pools = payload.includedUsage as Record<
      string,
      Record<string, unknown>
    >;
    (pools.cursorModels ?? {}).percentUsed = 100;
    const result = mapWirePayload(payload);
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    const envelope = result.value as {
      cursorModels: { percentUsed: number };
      otherModels: { percentUsed: number };
    };
    expect(envelope.cursorModels.percentUsed).toBe(100);
    expect(envelope.otherModels.percentUsed).toBe(1.7);
  });
});

describe("CursorLiveUsageTransport", () => {
  it("requests only the allowlisted JSON route and never an HTML page", async () => {
    const client = new StubClient([
      { status: 200, body: fixture("wire-usage-summary.json") }
    ]);
    const transport = new CursorLiveUsageTransport({ client });

    const result = await transport.fetchUsage(SESSION);
    expect(result.ok).toBe(true);
    expect(client.calls).toHaveLength(1);
    const call = client.calls[0];
    expect(call?.url).toBe(
      `${CURSOR_USAGE_ORIGIN}${CURSOR_WIRE_CONTRACT.route}`
    );
    expect(call?.url).not.toContain("/dashboard");
    expect(call?.headers.Accept).toBe("application/json");
  });

  it("carries the session in a header and never in the URL", async () => {
    const client = new StubClient([
      { status: 200, body: fixture("wire-usage-summary.json") }
    ]);
    await new CursorLiveUsageTransport({ client }).fetchUsage(SESSION);

    const call = client.calls[0];
    expect(call?.headers.Authorization).toBe(`Bearer ${SESSION}`);
    expect(call?.url).not.toContain(SESSION);
  });

  it("treats a 401 as an expired session and issues exactly one request", async () => {
    const client = new StubClient([{ status: 401, body: null }]);
    const result = await new CursorLiveUsageTransport({ client }).fetchUsage(
      SESSION
    );

    expect(!result.ok && result.error.code).toBe("session-expired");
    // No retry loop and no neighboring-endpoint probe.
    expect(client.calls).toHaveLength(1);
  });

  it.each([
    [403, "dashboard-visibility-restricted"],
    [404, "endpoint-unavailable"],
    [429, "rate-limited"],
    [500, "service-error"],
    [418, "network-error"]
  ])("classifies status %i", async (status, code) => {
    const client = new StubClient([{ status, body: null }]);
    const result = await new CursorLiveUsageTransport({ client }).fetchUsage(
      SESSION
    );
    expect(!result.ok && result.error.code).toBe(code);
    expect(client.calls).toHaveLength(1);
  });

  it("preserves retry metadata without retrying", async () => {
    const client = new StubClient([
      { status: 429, body: null, retryAfter: "2026-08-05T13:00:00Z" }
    ]);
    const result = await new CursorLiveUsageTransport({ client }).fetchUsage(
      SESSION
    );
    expect(!result.ok && result.error.retryAt).toBe("2026-08-05T13:00:00Z");
  });

  it("maps an abort to cancelled and any other throw to a network error", async () => {
    const abort = Object.assign(new Error("aborted"), { name: "AbortError" });
    const cancelled = await new CursorLiveUsageTransport({
      client: new ThrowingClient(abort)
    }).fetchUsage(SESSION);
    expect(!cancelled.ok && cancelled.error.code).toBe("cancelled");

    const failed = await new CursorLiveUsageTransport({
      client: new ThrowingClient(new Error("socket closed"))
    }).fetchUsage(SESSION);
    expect(!failed.ok && failed.error.code).toBe("network-error");
  });

  it("keeps the session out of every error it returns", async () => {
    for (const status of [401, 403, 429, 500]) {
      const client = new StubClient([{ status, body: null }]);
      const result = await new CursorLiveUsageTransport({ client }).fetchUsage(
        SESSION
      );
      expect(JSON.stringify(result)).not.toContain(SESSION);
    }
  });
});

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

async function seedLiveCache(
  store: UsageStore,
  fetchedAt: string
): Promise<FreshUsageSnapshot> {
  const mapped = mapWirePayload(fixture("wire-usage-summary.json"));
  if (!mapped.ok) {
    throw new Error("fixture must map cleanly");
  }
  const normalized = normalizeSnapshotPayload(mapped.value, {
    source: "credential-api",
    fetchedAt
  });
  if (!normalized.ok) {
    throw new Error("fixture must normalize cleanly");
  }
  return store.saveSuccess(normalized.value as UsageSnapshot);
}

describe("degradation", () => {
  const fetchedAt = "2026-08-05T12:00:00Z";
  const now = Date.parse("2026-08-05T12:05:00Z");

  it("demotes a live failure to the prior cache with an explicit staleness label", async () => {
    const store = new UsageStore(new FakeMemento(), 30 * 60_000);
    await seedLiveCache(store, fetchedAt);

    const client = new StubClient([{ status: 401, body: null }]);
    const provider = new CursorUsageProvider({
      credentials: {
        withCredential: async (operation) => operation(SESSION)
      },
      jsonTransport: new CursorLiveUsageTransport({ client }),
      now: () => new Date(now)
    });

    const state = await store.resolveFetch(await provider.fetch(), now);
    expect(state.state).toBe("stale");
    if (state.state !== "stale") {
      return;
    }
    // The prior numbers survive, and they are labelled rather than presented as
    // current. Blanking or silently reusing them would both be wrong.
    expect(state.data.cursorModels.used).toEqual({
      value: 345000,
      unit: "tokens"
    });
    expect(state.data.stale).toBe(true);
    expect(state.data.staleReason).toBe("authentication-required");
    expect(state.data.source).toBe("cache");
    expect(state.data.cachedFrom).toBe("credential-api");
  });

  it("labels a schema drift as drift rather than a generic failure", async () => {
    const store = new UsageStore(new FakeMemento(), 30 * 60_000);
    await seedLiveCache(store, fetchedAt);

    const client = new StubClient([
      { status: 200, body: fixture("wire-field-drift.json") }
    ]);
    const provider = new CursorUsageProvider({
      credentials: {
        withCredential: async (operation) => operation(SESSION)
      },
      jsonTransport: new CursorLiveUsageTransport({ client }),
      now: () => new Date(now)
    });

    const state = await store.resolveFetch(await provider.fetch(), now);
    expect(state.state).toBe("stale");
    if (state.state !== "stale") {
      return;
    }
    expect(state.data.staleReason).toBe("schema-drift");
  });

  it("reports empty rather than inventing numbers when no cache exists", async () => {
    const store = new UsageStore(new FakeMemento(), 30 * 60_000);
    const client = new StubClient([{ status: 500, body: null }]);
    const provider = new CursorUsageProvider({
      credentials: {
        withCredential: async (operation) => operation(SESSION)
      },
      jsonTransport: new CursorLiveUsageTransport({ client })
    });

    const state = await store.resolveFetch(await provider.fetch(), now);
    expect(state.state).toBe("empty");
  });

  it("refuses without a transport call when consent is absent", async () => {
    const client = new StubClient([]);
    const provider = new CursorUsageProvider({
      credentials: {
        withCredential: async () => ({
          ok: false,
          error: {
            code: "authorization-required",
            message: "consent required",
            sourceAttempt: "credential-api",
            recoverable: true
          }
        })
      },
      jsonTransport: new CursorLiveUsageTransport({ client })
    });

    const result = await provider.fetch();
    expect(result.ok).toBe(false);
    expect(client.calls).toHaveLength(0);
  });

  it("keeps the fetch spy honest about how often the network is touched", async () => {
    const fetchUsage = vi.fn(async () => ({
      ok: false as const,
      error: {
        code: "session-expired" as const,
        message: "expired",
        sourceAttempt: "credential-api" as const,
        recoverable: true
      }
    }));
    const provider = new CursorUsageProvider({
      credentials: {
        withCredential: async (operation) => operation(SESSION)
      },
      jsonTransport: { fetchUsage }
    });

    await provider.fetch();
    expect(fetchUsage).toHaveBeenCalledTimes(1);
  });
});
