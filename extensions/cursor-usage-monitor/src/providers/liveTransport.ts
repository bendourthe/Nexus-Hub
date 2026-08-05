import type { Money, ProviderResult, Quantity } from "../types";
import type { CredentialJsonTransport } from "./cursor";
import { classifyHttpError, providerError } from "./errors";

export const CURSOR_USAGE_ORIGIN = "https://cursor.com";

/**
 * The wire shape this transport REQUIRES of the undocumented JSON route.
 *
 * Every entry is a dot-path into the raw payload, so correcting the contract after
 * the bounded probe in `cursor-usage-auth-probe.md` is a string edit in this one
 * table rather than a change to the mapping code. `verified: false` is load-bearing:
 * it records that the names below are the shape derived from
 * `cursor-usage-data-contract.md`, not a shape confirmed against a live account.
 *
 * The route is `credential-api`. It is not a documented Cursor API and must never
 * be described as one.
 */
export const CURSOR_WIRE_CONTRACT = {
  version: "wire/v1-unverified",
  verified: false,
  route: "/api/usage-summary",
  fields: {
    periodStart: "billingCycle.start",
    periodEnd: "billingCycle.end",
    cursorModelsUsed: "includedUsage.cursorModels.usedTokens",
    cursorModelsLimit: "includedUsage.cursorModels.limitTokens",
    cursorModelsPercent: "includedUsage.cursorModels.percentUsed",
    otherModelsUsed: "includedUsage.otherModels.usedTokens",
    otherModelsLimit: "includedUsage.otherModels.limitTokens",
    otherModelsPercent: "includedUsage.otherModels.percentUsed",
    onDemandEnabled: "onDemand.enabled",
    onDemandSpend: "onDemand.spendCents",
    onDemandSharedLimit: "onDemand.spendLimitCents",
    onDemandCurrency: "onDemand.currency",
    onDemandDynamicLimit: "onDemand.dynamicLimit"
  },
  /**
   * A field whose absence means the route no longer reports what the panel claims
   * to show. Anything outside this list may be null or missing without rejecting
   * the payload.
   */
  requiredFields: [
    "periodEnd",
    "cursorModelsUsed",
    "cursorModelsLimit",
    "otherModelsUsed",
    "otherModelsLimit",
    "onDemandEnabled"
  ],
  units: {
    includedUsage: "tokens",
    money: "currency-minor",
    /** Optional self-declared units. When present they must agree with the above. */
    includedUsageDeclaredAt: "includedUsage.unit",
    moneyDeclaredAt: "onDemand.amountUnit"
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
  getJson(
    url: string,
    headers: Readonly<Record<string, string>>,
    signal?: AbortSignal
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
    this.origin = dependencies.origin ?? CURSOR_USAGE_ORIGIN;
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
          Accept: "application/json"
        },
        signal
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

  const declaredUsageUnit = readPath(
    payload,
    CURSOR_WIRE_CONTRACT.units.includedUsageDeclaredAt
  );
  if (
    declaredUsageUnit !== undefined &&
    declaredUsageUnit !== CURSOR_WIRE_CONTRACT.units.includedUsage
  ) {
    return unitMismatch();
  }
  const declaredMoneyUnit = readPath(
    payload,
    CURSOR_WIRE_CONTRACT.units.moneyDeclaredAt
  );
  if (
    declaredMoneyUnit !== undefined &&
    declaredMoneyUnit !== CURSOR_WIRE_CONTRACT.units.money
  ) {
    return unitMismatch();
  }

  for (const field of CURSOR_WIRE_CONTRACT.requiredFields) {
    if (readField(payload, field) === undefined) {
      return schemaMismatch();
    }
  }

  const cursorModels = mapMeter(payload, "cursorModels");
  const otherModels = mapMeter(payload, "otherModels");
  if (cursorModels === null || otherModels === null) {
    return schemaMismatch();
  }

  const periodEnd = optionalString(readField(payload, "periodEnd"));
  if (periodEnd === null) {
    return schemaMismatch();
  }
  const enabled = readField(payload, "onDemandEnabled");
  if (typeof enabled !== "boolean") {
    return schemaMismatch();
  }

  const currency =
    optionalString(readField(payload, "onDemandCurrency")) ?? DEFAULT_CURRENCY;
  const personalSpend = enabled
    ? minorUnitsToMoney(readField(payload, "onDemandSpend"), currency)
    : null;
  if (enabled && personalSpend === null) {
    return schemaMismatch();
  }
  const dynamicLimit = readField(payload, "onDemandDynamicLimit");

  return {
    ok: true,
    value: {
      period: {
        startsAt: optionalString(readField(payload, "periodStart")),
        resetsAt: periodEnd
      },
      cursorModels,
      otherModels,
      onDemand: enabled
        ? { enabled: true, personalSpend }
        : { enabled: false, personalSpend: null },
      teamContext: {
        // The spend limit is the team's shared pool, so it is recorded as team
        // context and never as a personal cap.
        sharedSpendLimit: minorUnitsToMoney(
          readField(payload, "onDemandSharedLimit"),
          currency
        ),
        dynamicSpendLimit:
          typeof dynamicLimit === "boolean" ? dynamicLimit : null
      }
    }
  };
}

function mapMeter(
  payload: Record<string, unknown>,
  pool: "cursorModels" | "otherModels"
): {
  used: Quantity | null;
  limit: Quantity | null;
  percentUsed: number | null;
} | null {
  const used = tokenQuantity(
    readField(payload, `${pool}Used` as WireFieldName)
  );
  const limit = tokenQuantity(
    readField(payload, `${pool}Limit` as WireFieldName)
  );
  if (used === null || limit === null) {
    return null;
  }
  const percent = readField(payload, `${pool}Percent` as WireFieldName);
  return {
    used,
    limit,
    percentUsed: nonNegativeNumber(percent)
  };
}

function tokenQuantity(value: unknown): Quantity | null {
  const amount = nonNegativeNumber(value);
  return amount === null
    ? null
    : { value: amount, unit: CURSOR_WIRE_CONTRACT.units.includedUsage };
}

function minorUnitsToMoney(value: unknown, currency: string): Money | null {
  const minor = nonNegativeNumber(value);
  if (minor === null || !/^[A-Z]{3}$/u.test(currency)) {
    return null;
  }
  return {
    amount: minor / MONEY_MINOR_UNITS_PER_MAJOR,
    currency
  };
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
    signal?: AbortSignal
  ): Promise<HttpJsonResponse> {
    const response = await fetch(url, {
      method: "GET",
      headers: { ...headers },
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
