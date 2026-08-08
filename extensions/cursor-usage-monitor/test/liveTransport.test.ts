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

  it("is recorded as verified in both the code and the fixture", () => {
    // Inverted in Phase 6: the route, the field names, and the money units were
    // confirmed against a live account (HTTP 200). `verified` stays load-bearing in
    // the other direction now - it asserts the claim rests on a recorded probe, so
    // a future contract edit made without one has to flip this deliberately.
    expect(CURSOR_WIRE_CONTRACT.verified).toBe(true);
    const declared = fixture("wire-contract.json");
    const contract = declared.fixtureContract as Record<string, unknown>;
    expect(contract.verified).toBe(true);
    expect(contract.source).toBe("credential-api");
    expect(contract.provenance).toBe("live-probe-verified-names-and-units");
  });

  it("targets the RPC host with a POST, not the web origin with a GET", () => {
    // The original REST assumption is exactly what produced the 405. Pinning both
    // the verb and the host stops a well-meaning "simplification" back to a GET.
    expect(CURSOR_WIRE_CONTRACT.origin).toBe("https://api2.cursor.sh");
    expect(CURSOR_WIRE_CONTRACT.method).toBe("POST");
    expect(CURSOR_WIRE_CONTRACT.route).toBe(
      "/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
    );
    // team_id is optional, so a personal query is an empty body.
    expect(CURSOR_WIRE_CONTRACT.body).toBe("{}");
  });

  it("keeps every field path camelCase, as Connect's JSON codec delivers them", () => {
    // The descriptor says billing_cycle_start; the wire says billingCycleStart.
    // A snake_case path here reads undefined for every field, so it is worth an
    // assertion rather than a comment.
    for (const path of Object.values(CURSOR_WIRE_CONTRACT.fields)) {
      expect(path).not.toMatch(/_/u);
    }
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
    // Per-pool figures arrive as SPEND in cents, and Quantity.unit admits only
    // tokens/requests/percent, so money is deliberately not placed here. The
    // percentage carries the meter.
    expect(snapshot.cursorModels.used).toBeNull();
    expect(snapshot.cursorModels.limit).toBeNull();
    // Taken as delivered, to full precision - not rounded and not recomputed.
    expect(snapshot.cursorModels.percentUsed).toBeCloseTo(23.971111111111114, 10);
    expect(snapshot.cursorModels.percentOrigin).toBe("source");
    expect(snapshot.otherModels.percentUsed).toBe(12);
    // An epoch-millisecond STRING, normalized to ISO. Read as seconds this would
    // land in 1970.
    expect(snapshot.period.resetsAt).toBe(
      new Date(1788374587000).toISOString()
    );
    expect(snapshot.period.startsAt).toBe(
      new Date(1785782587000).toISOString()
    );
  });

  it("converts minor currency units and keeps the limit as team context", () => {
    const result = mapWirePayload(fixture("wire-usage-summary.json"));
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    const envelope = result.value as {
      onDemand: { enabled: boolean; personalSpend: unknown };
      teamContext: {
        sharedSpendLimit: unknown;
        dynamicSpendLimit: unknown;
        sharedSpendUsed: unknown;
        sharedSpendRemaining: unknown;
      };
    };

    expect(envelope.onDemand).toEqual({
      enabled: true,
      // individualUsed 15732 cents -> 157.32 dollars.
      personalSpend: { amount: 157.32, currency: "USD" }
    });
    // The spend limit is the team's shared pool. Recording it as team context is
    // what stops it being rendered as a personal cap.
    expect(envelope.teamContext.sharedSpendLimit).toEqual({
      amount: 200,
      currency: "USD"
    });
    // limitType "team" means the limit is pooled, so from this user's seat it is
    // not a fixed personal cap.
    expect(envelope.teamContext.dynamicSpendLimit).toBe(true);
    // The pool is drawn PAST its limit with nothing left, while personal spend is
    // far lower. That combination is the whole reason these fields are carried:
    // personal spend alone would suggest plenty of headroom that does not exist.
    expect(envelope.teamContext.sharedSpendUsed).toEqual({
      amount: 200.86,
      currency: "USD"
    });
    expect(envelope.teamContext.sharedSpendRemaining).toEqual({
      amount: 0,
      currency: "USD"
    });
  });

  it("rejects a renamed pool rather than coercing it", () => {
    const result = mapWirePayload(fixture("wire-field-drift.json"));
    expect(!result.ok && result.error.code).toBe("json-schema-mismatch");
    expect(!result.ok && result.error.sourceAttempt).toBe("credential-api");
  });

  it("uses the reported percentage and never derives one from spend over limit", () => {
    // The most important assertion in this file. On the probed account
    // (totalSpend / limit) * 100 was 1078.70 while the reported totalPercentUsed was
    // 23.97, because the reported figure uses a base the payload does not expose.
    // The fixture reproduces that discrepancy on purpose, so any refactor that
    // "helpfully" computes the percentage fails here instead of shipping a 1079%
    // meter that pins every threshold alert on a healthy account.
    const payload = fixture("wire-usage-summary.json");
    const plan = payload.planUsage as Record<string, number>;
    const derived = (plan.totalSpend / plan.limit) * 100;
    expect(derived).toBeGreaterThan(1000);
    expect(plan.autoPercentUsed).toBeLessThan(30);

    const result = mapWirePayload(payload);
    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    const envelope = result.value as {
      cursorModels: { percentUsed: number | null };
    };
    expect(envelope.cursorModels.percentUsed).toBeCloseTo(plan.autoPercentUsed, 10);
    expect(envelope.cursorModels.percentUsed).not.toBeCloseTo(derived, 0);
  });

  it("rejects a cycle timestamp that is not an epoch-millisecond string", () => {
    // Read as seconds, a 10-digit value dates the cycle to 1970; a non-numeric
    // string must not silently become an Invalid Date rendered as text.
    for (const bad of ["not-a-number", "", "12", null, {}]) {
      const payload = fixture("wire-usage-summary.json");
      payload.billingCycleEnd = bad;
      expect(!mapWirePayload(payload).ok).toBe(true);
    }
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
    payload.enabled = false;
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
    (payload.planUsage as Record<string, unknown>).autoPercentUsed = 100;
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
    expect(envelope.otherModels.percentUsed).toBe(12);
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
      `${CURSOR_WIRE_CONTRACT.origin}${CURSOR_WIRE_CONTRACT.route}`
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
    // The cached snapshot came from the live mapper, which leaves per-pool absolute
    // usage null because this route reports spend rather than tokens. What matters
    // for degradation is that the cached PERCENTAGE survived with a staleness label.
    expect(state.data.cursorModels.used).toBeNull();
    expect(state.data.cursorModels.percentUsed).toBeCloseTo(23.971111111111114, 10);
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

describe("the real fetch client, not the stub", () => {
  // These exist because every other test in this file passed while the production
  // client still hardcoded `method: "GET"`. A stub that records what it was asked
  // for proves the transport's intent; it cannot prove the client honors it. A
  // POST-only Connect endpoint answers a GET with 405, so the suite was green and
  // production would have been broken.
  // No injected client: this must exercise the default FetchJsonClient.
  const realClient = () => new CursorLiveUsageTransport();

  it("issues the contract's verb and body through global fetch", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const original = globalThis.fetch;
    globalThis.fetch = (async (url: string, init: RequestInit) => {
      calls.push({ url: String(url), init });
      return {
        ok: true,
        status: 200,
        headers: { get: () => null },
        json: async () => ({})
      };
    }) as unknown as typeof fetch;
    try {
      await realClient().fetchUsage("session-value");
    } finally {
      globalThis.fetch = original;
    }

    expect(calls).toHaveLength(1);
    const call = calls[0]!;
    expect(call.url).toBe(
      `${CURSOR_WIRE_CONTRACT.origin}${CURSOR_WIRE_CONTRACT.route}`
    );
    expect(call.init.method).toBe("POST");
    expect(call.init.body).toBe("{}");
  });

  it("sends the session as a bearer header and never in the url", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const original = globalThis.fetch;
    globalThis.fetch = (async (url: string, init: RequestInit) => {
      calls.push({ url: String(url), init });
      return {
        ok: true,
        status: 200,
        headers: { get: () => null },
        json: async () => ({})
      };
    }) as unknown as typeof fetch;
    try {
      await realClient().fetchUsage("super-secret-session");
    } finally {
      globalThis.fetch = original;
    }

    const call = calls[0]!;
    // A credential in a URL reaches history buffers, proxy logs, and error reports.
    expect(call.url).not.toContain("super-secret-session");
    const headers = call.init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer super-secret-session");
    expect(headers["Content-Type"]).toBe("application/json");
  });
});
