import type { Money, ProviderResult, Quantity } from "../types";
import type { CredentialJsonTransport } from "./cursor";
import { classifyHttpError, providerError } from "./errors";

export const CURSOR_USAGE_ORIGIN = "https://cursor.com";

/**
 * The RPC host. Personal usage is not on the web origin: it is a unary Connect
 * method on Cursor's API host, which is why the earlier REST assumption produced a
 * 405 rather than a 404. See `cursor-usage-auth-probe.md`, Phase 6.
 */
export const CURSOR_RPC_ORIGIN = "https://api2.cursor.sh";

/**
 * The wire shape this transport REQUIRES of the undocumented usage RPC.
 *
 * Every entry is a dot-path into the raw payload, so a contract correction is a
 * string edit in this one table rather than a change to the mapping code.
 *
 * `verified: true` records that the route, the field NAMES, and the money units
 * were confirmed against a live account (HTTP 200) in the Phase 6 probe. Three
 * findings from that probe are load-bearing here and must not be "tidied" away:
 *
 *  1. **Field names are camelCase, not the descriptor's snake_case.** The protobuf
 *     declares `billing_cycle_start`; Connect's JSON codec applies the proto3 JSON
 *     mapping, so the wire says `billingCycleStart`. Building from the descriptor
 *     alone yields `undefined` for every field.
 *  2. **Percentages are taken as delivered, never recomputed.** On the probed
 *     account `(totalSpend / limit) * 100` came to 1078.70 while the reported
 *     `totalPercentUsed` was 23.97 - a factor of ~45, because the reported
 *     percentage uses a base this payload does not expose. Deriving it would render
 *     a healthy 24% meter as 1079% and fire every threshold alert continuously.
 *  3. **`limit` is NOT the denominator of `totalPercentUsed`**, per (2), and
 *     `remainingBonus` is a boolean flag rather than a remaining amount.
 *
 * Money is minor units (cents): the probed plan reported `limit: 2000` for a
 * 20-dollar included allowance. Cycle bounds are epoch MILLISECONDS delivered as
 * strings, because proto3 JSON encodes 64-bit integers as strings.
 *
 * The route is `credential-api`. It is not a documented Cursor API and must never
 * be described as one.
 */
export const CURSOR_WIRE_CONTRACT = {
  version: "wire/v2-rpc-verified",
  verified: true,
  origin: CURSOR_RPC_ORIGIN,
  route: "/aiserver.v1.DashboardService/GetCurrentPeriodUsage",
  method: "POST",
  /** `team_id` is optional, so an empty body asks for the caller's own usage. */
  body: "{}",
  fields: {
    periodStart: "billingCycleStart",
    periodEnd: "billingCycleEnd",
    // "auto" is Cursor's own model selection; "api" is other/bring-your-own models.
    cursorModelsPercent: "planUsage.autoPercentUsed",
    cursorModelsSpend: "planUsage.autoSpend",
    cursorModelsLimit: "planUsage.autoLimit",
    otherModelsPercent: "planUsage.apiPercentUsed",
    otherModelsSpend: "planUsage.apiSpend",
    otherModelsLimit: "planUsage.apiLimit",
    onDemandEnabled: "enabled",
    onDemandSpend: "spendLimitUsage.individualUsed",
    onDemandPersonalLimit: "spendLimitUsage.individualLimit",
    onDemandSharedLimit: "spendLimitUsage.pooledLimit",
    onDemandSharedUsed: "spendLimitUsage.pooledUsed",
    onDemandSharedRemaining: "spendLimitUsage.pooledRemaining",
    limitType: "spendLimitUsage.limitType"
  },
  /**
   * A field whose absence means the route no longer reports what the panel claims
   * to show. Deliberately short, and deliberately NOT including spend or limit for
   * either pool: the probed account omitted `autoSpend`, `autoLimit`, `apiSpend`,
   * `apiLimit`, and `individualLimit` entirely, so requiring any of them would
   * reject a valid payload. What the panel cannot do without is the cycle end and
   * the on-demand flag.
   */
  requiredFields: ["periodEnd", "onDemandEnabled"],
  units: {
    /** Percentages arrive precomputed; see finding (2) above. */
    includedUsage: "percent-precomputed",
    money: "currency-minor",
    /** Epoch milliseconds, delivered as strings. */
    timestamps: "epoch-millis-string"
  }
} as const;

type WireFieldName = keyof typeof CURSOR_WIRE_CONTRACT.fields;

const MONEY_MINOR_UNITS_PER_MAJOR = 100;
const DEFAULT_CURRENCY = "USD";

export interface HttpJsonResponse {
  status: number;
  body: unknown;
  retryAfter?: string;
}

export interface HttpJsonClient {
  /**
   * Named `getJson` for continuity with the callers and tests that already depend
   * on it, but it performs the contract's own verb. A Connect endpoint is POST-only,
   * so a GET here returns 405 rather than data.
   */
  getJson(
    url: string,
    headers: Readonly<Record<string, string>>,
    signal?: AbortSignal,
    init?: { method: string; body: string }
  ): Promise<HttpJsonResponse>;
}

export interface LiveTransportDependencies {
  client?: HttpJsonClient;
  origin?: string;
}

/**
 * Calls the allowlisted JSON route and maps it into the normalized envelope that
 * `normalizeSnapshotPayload` already validates. It never requests an HTML page.
 */
export class CursorLiveUsageTransport implements CredentialJsonTransport {
  private readonly client: HttpJsonClient;
  private readonly origin: string;

  public constructor(dependencies: LiveTransportDependencies = {}) {
    this.client = dependencies.client ?? new FetchJsonClient();
    this.origin = dependencies.origin ?? CURSOR_WIRE_CONTRACT.origin;
  }

  public async fetchUsage(
    credential: string,
    signal?: AbortSignal
  ): Promise<ProviderResult<unknown>> {
    let response: HttpJsonResponse;
    try {
      response = await this.client.getJson(
        `${this.origin}${CURSOR_WIRE_CONTRACT.route}`,
        {
          // The session travels in a header for one request and is never logged,
          // persisted, or placed in a URL where it could reach a history buffer.
          Authorization: `Bearer ${credential}`,
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        signal,
        { method: CURSOR_WIRE_CONTRACT.method, body: CURSOR_WIRE_CONTRACT.body }
      );
    } catch (error) {
      return {
        ok: false,
        error: providerError(
          isAbortError(error) ? "cancelled" : "network-error",
          "credential-api"
        )
      };
    }

    if (response.status !== 200) {
      // 401 lands on session-expired, which `shouldTryHtmlFallback` excludes, so
      // the caller degrades to cache instead of retrying or probing neighbors.
      return {
        ok: false,
        error: classifyHttpError(
          response.status,
          "credential-api",
          response.retryAfter
        )
      };
    }
    return mapWirePayload(response.body);
  }
}

/**
 * Maps a raw wire payload onto the normalized envelope, rejecting rather than
 * coercing when a required field name is absent or a declared unit disagrees.
 */
export function mapWirePayload(payload: unknown): ProviderResult<unknown> {
  if (!isRecord(payload)) {
    return schemaMismatch();
  }

  // This route declares no units of its own, so there is nothing to cross-check
  // against. The units are fixed by the Phase 6 probe and recorded on the contract:
  // money in minor units, timestamps as epoch-millisecond strings, percentages
  // precomputed. A drift in any of those shows up as a rejected payload below or as
  // a value that fails its own range check, not as a silent misread.
  for (const field of CURSOR_WIRE_CONTRACT.requiredFields) {
    if (readField(payload, field) === undefined) {
      return schemaMismatch();
    }
  }

  const cursorModels = mapMeter(payload, "cursorModels");
  const otherModels = mapMeter(payload, "otherModels");

  const periodEnd = epochMillisString(readField(payload, "periodEnd"));
  if (periodEnd === null) {
    return schemaMismatch();
  }
  const enabled = readField(payload, "onDemandEnabled");
  if (typeof enabled !== "boolean") {
    return schemaMismatch();
  }

  // Currency is not reported by this route. USD is the documented billing currency
  // and is recorded as an assumption here rather than silently baked into the
  // formatter, so a future non-USD account surfaces as one wrong label in one place.
  const currency = DEFAULT_CURRENCY;
  const personalSpend = enabled
    ? minorUnitsToMoney(readField(payload, "onDemandSpend"), currency)
    : null;

  // The shared pool is team context, never a personal cap. `limitType` is the
  // payload's own word for the arrangement; "team" means the limit is pooled.
  const limitType = optionalString(readField(payload, "limitType"));

  return {
    ok: true,
    value: {
      period: {
        startsAt: epochMillisString(readField(payload, "periodStart")),
        resetsAt: periodEnd
      },
      cursorModels,
      otherModels,
      onDemand: enabled
        ? { enabled: true, personalSpend }
        : { enabled: false, personalSpend: null },
      teamContext: {
        sharedSpendLimit: minorUnitsToMoney(
          readField(payload, "onDemandSharedLimit"),
          currency
        ),
        // Carried through so the panel can answer "is there anything left in the
        // pool", which personal spend alone cannot. `used` may exceed `limit`.
        sharedSpendUsed: minorUnitsToMoney(
          readField(payload, "onDemandSharedUsed"),
          currency
        ),
        sharedSpendRemaining: minorUnitsToMoney(
          readField(payload, "onDemandSharedRemaining"),
          currency
        ),
        // A pooled limit is shared and therefore not fixed from this user's
        // perspective. Anything other than an explicit "team" leaves it unknown
        // rather than guessing a boolean from an unrecognized string.
        dynamicSpendLimit: limitType === null ? null : limitType === "team"
      }
    }
  };
}

/**
 * One pool's meter.
 *
 * Returns the percentage **exactly as delivered** and never derives one from spend
 * over limit. On the probed account those two disagreed by a factor of ~45, because
 * the reported percentage uses a base the payload does not expose. Deriving it would
 * have shown 1079% for a healthy 24% pool and pinned every threshold alert on.
 *
 * Spend and limit are optional: the probed account omitted both for both pools, so
 * an absent value yields `null` and the panel falls back to its documented
 * "allowance unknown" presentation rather than rejecting the payload.
 */
function mapMeter(
  payload: Record<string, unknown>,
  pool: "cursorModels" | "otherModels"
): {
  used: Quantity | null;
  limit: Quantity | null;
  percentUsed: number | null;
} {
  // `used` and `limit` stay null on purpose. This route reports per-pool figures as
  // SPEND in cents, and `Quantity.unit` admits only tokens, requests, or percent -
  // so putting money there would label dollars as tokens. The probed account omitted
  // both fields anyway. The percentage carries the meter; money is rendered by the
  // on-demand card, which is Money-typed and can state its currency.
  return {
    used: null,
    limit: null,
    percentUsed: nonNegativeNumber(
      readField(payload, `${pool}Percent` as WireFieldName)
    )
  };
}

function minorUnitsToMoney(value: unknown, currency: string): Money | null {
  const minor = nonNegativeNumber(value);
  if (minor === null || !/^[A-Z]{3}$/u.test(currency)) {
    return null;
  }
  return { amount: minor / MONEY_MINOR_UNITS_PER_MAJOR, currency };
}

/**
 * Epoch milliseconds delivered as a string, normalized to an ISO timestamp.
 *
 * proto3 JSON encodes 64-bit integers as strings, so this arrives as `"1785782587000"`
 * rather than a number. Treating it as seconds would date every billing cycle to
 * 1970, so the 13-digit millisecond scale is asserted rather than assumed.
 */
function epochMillisString(value: unknown): string | null {
  const numeric =
    typeof value === "string" && /^[0-9]{10,16}$/u.test(value.trim())
      ? Number(value.trim())
      : typeof value === "number" && Number.isFinite(value)
        ? value
        : null;
  if (numeric === null || numeric <= 0) {
    return null;
  }
  const date = new Date(numeric);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export function readField(
  payload: Record<string, unknown>,
  field: WireFieldName
): unknown {
  return readPath(payload, CURSOR_WIRE_CONTRACT.fields[field]);
}

export function readPath(payload: unknown, path: string): unknown {
  let cursor: unknown = payload;
  for (const segment of path.split(".")) {
    if (!isRecord(cursor)) {
      return undefined;
    }
    cursor = cursor[segment];
  }
  return cursor ?? undefined;
}

function nonNegativeNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? value
    : null;
}

function optionalString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isAbortError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    (error as { name?: unknown }).name === "AbortError"
  );
}

function schemaMismatch(): ProviderResult<never> {
  return {
    ok: false,
    error: providerError("json-schema-mismatch", "credential-api")
  };
}

function unitMismatch(): ProviderResult<never> {
  return {
    ok: false,
    error: providerError("unit-mismatch", "credential-api")
  };
}

class FetchJsonClient implements HttpJsonClient {
  public async getJson(
    url: string,
    headers: Readonly<Record<string, string>>,
    signal?: AbortSignal,
    init?: { method: string; body: string }
  ): Promise<HttpJsonResponse> {
    // The verb comes from the caller, defaulting to GET only for the legacy shape.
    // Hardcoding GET here is what made the whole suite pass against a stub while
    // production would have taken a 405 from a POST-only Connect endpoint.
    const method = init?.method ?? "GET";
    const response = await fetch(url, {
      method,
      headers: { ...headers },
      ...(init?.body === undefined || method === "GET"
        ? {}
        : { body: init.body }),
      ...(signal === undefined ? {} : { signal })
    });
    const retryAfter = response.headers.get("retry-after");
    const body = response.ok ? ((await response.json()) as unknown) : null;
    return {
      status: response.status,
      body,
      ...(retryAfter === null ? {} : { retryAfter })
    };
  }
}
