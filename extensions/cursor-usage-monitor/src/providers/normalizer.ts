import type {
  IncludedUsageMeter,
  LiveUsageSource,
  Money,
  NonCacheUsageSource,
  OnDemandState,
  ProviderError,
  ProviderErrorCode,
  ProviderResult,
  Quantity,
  StaleReason,
  TeamContext,
  UsagePeriod,
  UsageSnapshot,
  UsageSource,
  UsageUnit
} from "../types";

const USAGE_UNITS: ReadonlySet<string> = new Set<UsageUnit>([
  "tokens",
  "requests",
  "percent"
]);
const STALE_REASONS: ReadonlySet<string> = new Set<StaleReason>([
  "age-threshold",
  "fetch-failed",
  "rate-limited",
  "authentication-required",
  "visibility-restricted",
  "schema-drift",
  "period-reset-passed",
  "allowance-unavailable"
]);

export type NormalizationOptions =
  | {
      source: "cache";
      cachedFrom: NonCacheUsageSource;
      fetchedAt?: string;
    }
  | {
      source: NonCacheUsageSource;
      cachedFrom?: never;
      fetchedAt?: string;
    };

export function normalizeSnapshotPayload(
  payload: unknown,
  options: NormalizationOptions
): ProviderResult<UsageSnapshot> {
  const envelope = asRecord(payload);
  if (envelope === null) {
    return failure(
      "json-schema-mismatch",
      "Cursor usage data must be a JSON object.",
      sourceAttempt(options.source)
    );
  }

  const period = parsePeriod(envelope.period, options.source);
  if (!period.ok) {
    return period;
  }
  const cursorModels = parseMeter(
    envelope.cursorModels,
    "Cursor Models",
    options.source
  );
  if (!cursorModels.ok) {
    return cursorModels;
  }
  const otherModels = parseMeter(
    envelope.otherModels,
    "Other Models",
    options.source
  );
  if (!otherModels.ok) {
    return otherModels;
  }
  const onDemand = parseOnDemand(envelope.onDemand, options.source);
  if (!onDemand.ok) {
    return onDemand;
  }
  const teamContext = parseTeamContext(envelope.teamContext, options.source);
  if (!teamContext.ok) {
    return teamContext;
  }

  const freshness = asRecord(envelope.freshness);
  const fetchedAtCandidate =
    options.fetchedAt ??
    freshness?.fetchedAt ??
    (typeof envelope.fetchedAt === "string" ? envelope.fetchedAt : undefined);
  if (!isIsoTimestamp(fetchedAtCandidate)) {
    return failure(
      "invalid-value",
      "Cursor usage data requires a valid fetchedAt timestamp.",
      sourceAttempt(options.source)
    );
  }

  const stale =
    options.source === "credential-api" || options.source === "html-scrape"
      ? false
      : freshness?.stale === true || envelope.stale === true;
  const staleReason = stale
    ? (parseStaleReason(freshness?.staleReason ?? envelope.staleReason) ??
      "age-threshold")
    : null;

  const value = {
    period: period.value,
    cursorModels: cursorModels.value,
    otherModels: otherModels.value,
    onDemand: onDemand.value,
    teamContext: teamContext.value,
    fetchedAt: fetchedAtCandidate,
    ...(options.source === "cache"
      ? { source: "cache" as const, cachedFrom: options.cachedFrom }
      : { source: options.source })
  };
  return stale
    ? {
        ok: true,
        value: {
          ...value,
          stale: true,
          staleReason: staleReason ?? "age-threshold"
        }
      }
    : {
        ok: true,
        value: { ...value, stale: false, staleReason: null }
      };
}

export function normalizeHtmlUsage(
  spendingHtml: string,
  usageHtml: string,
  fetchedAt: string
): ProviderResult<UsageSnapshot> {
  if (!isIsoTimestamp(fetchedAt)) {
    return failure(
      "invalid-value",
      "Cursor HTML normalization requires a valid fetchedAt timestamp.",
      "html-scrape"
    );
  }

  const spending = extractVisibleText(spendingHtml);
  const usage = extractVisibleText(usageHtml);
  if (looksLikeLogin(spending) || looksLikeLogin(usage)) {
    return failure(
      "login-redirect",
      "Cursor returned a sign-in page instead of usage data.",
      "html-scrape"
    );
  }
  if (!hasSpendingAnchors(spending) || !hasUsageAnchors(usage)) {
    return failure(
      spending.length < 40 || usage.length < 40
        ? "client-shell"
        : "html-schema-mismatch",
      "Cursor dashboard HTML is missing required semantic usage sections.",
      "html-scrape"
    );
  }

  const cursorPercent = parsePercent(spending, "Cursor Models");
  const otherPercent = parsePercent(spending, "Other Models");
  const cursorUsed = parseTokenTotal(usage, "Cursor Models");
  const otherUsed = parseTokenTotal(usage, "Other Models");
  if (
    cursorPercent === null ||
    otherPercent === null ||
    cursorUsed === null ||
    otherUsed === null
  ) {
    return failure(
      "html-schema-mismatch",
      "Cursor dashboard HTML has invalid pool percentages or token values.",
      "html-scrape"
    );
  }

  const period = parseHtmlPeriod(usage, spending);
  if (period === null) {
    return failure(
      "html-schema-mismatch",
      "Cursor dashboard HTML has no valid billing cycle.",
      "html-scrape"
    );
  }
  const onDemand = parseHtmlOnDemand(spending);
  if (onDemand === null) {
    return failure(
      "html-schema-mismatch",
      "Cursor dashboard HTML has invalid on-demand usage.",
      "html-scrape"
    );
  }

  return {
    ok: true,
    value: {
      period,
      cursorModels: sourcePercentMeter(cursorUsed, cursorPercent),
      otherModels: sourcePercentMeter(otherUsed, otherPercent),
      onDemand: onDemand.state,
      teamContext: onDemand.teamContext,
      source: "html-scrape",
      fetchedAt,
      stale: false,
      staleReason: null
    }
  };
}

export function extractVisibleText(html: string): string {
  let output = "";
  let index = 0;
  let skippedElement: "script" | "style" | null = null;

  while (index < html.length) {
    if (html.startsWith("<!--", index)) {
      const commentEnd = html.indexOf("-->", index + 4);
      index = commentEnd === -1 ? html.length : commentEnd + 3;
      continue;
    }

    if (html[index] === "<") {
      const tagEnd = html.indexOf(">", index + 1);
      if (tagEnd === -1) {
        break;
      }
      const rawTag = html.slice(index + 1, tagEnd).trim().toLowerCase();
      const closing = rawTag.startsWith("/");
      const tagName = rawTag
        .replace(/^\/\s*/u, "")
        .split(/[\s/>]/u, 1)[0];
      if ((tagName === "script" || tagName === "style") && !closing) {
        skippedElement = tagName;
      } else if (closing && tagName === skippedElement) {
        skippedElement = null;
      }
      if (skippedElement === null) {
        output += " ";
      }
      index = tagEnd + 1;
      continue;
    }

    if (skippedElement === null) {
      output += html[index];
    }
    index += 1;
  }

  return decodeHtmlEntities(output).replace(/\s+/gu, " ").trim();
}

function parseMeter(
  value: unknown,
  label: string,
  source: UsageSource
): ProviderResult<IncludedUsageMeter> {
  const meter = asRecord(value);
  if (meter === null) {
    return failure(
      "json-schema-mismatch",
      `${label} usage must be an object.`,
      sourceAttempt(source)
    );
  }
  const used = parseNullableQuantity(meter.used);
  const limit = parseNullableQuantity(meter.limit);
  if (!used.ok || !limit.ok) {
    return failure(
      "invalid-value",
      `${label} has an invalid quantity.`,
      sourceAttempt(source)
    );
  }
  if (
    used.value !== null &&
    limit.value !== null &&
    used.value.unit !== limit.value.unit
  ) {
    return failure(
      "unit-mismatch",
      `${label} numerator and denominator use different units.`,
      sourceAttempt(source)
    );
  }

  const suppliedPercent = optionalNonNegativeNumber(meter.percentUsed);
  if (meter.percentUsed !== null && suppliedPercent === null) {
    return failure(
      "invalid-value",
      `${label} has an invalid percentage.`,
      sourceAttempt(source)
    );
  }
  if (suppliedPercent !== null) {
    return {
      ok: true,
      value: {
        used: used.value,
        limit: limit.value,
        percentUsed: suppliedPercent,
        percentOrigin: "source"
      }
    };
  }

  const calculated =
    used.value !== null &&
    limit.value !== null &&
    limit.value.value > 0 &&
    used.value.unit === limit.value.unit
      ? (used.value.value / limit.value.value) * 100
      : null;
  return {
    ok: true,
    value: {
      used: used.value,
      limit: limit.value,
      percentUsed: calculated,
      percentOrigin: calculated === null ? null : "calculated"
    }
  };
}

function parsePeriod(
  value: unknown,
  source: UsageSource
): ProviderResult<UsagePeriod> {
  const period = asRecord(value);
  if (period === null) {
    return failure(
      "json-schema-mismatch",
      "Cursor usage period must be an object.",
      sourceAttempt(source)
    );
  }
  const startsAt = nullableIsoTimestamp(period.startsAt);
  const resetsAt = nullableIsoTimestamp(period.resetsAt);
  if (!startsAt.ok || !resetsAt.ok) {
    return failure(
      "invalid-value",
      "Cursor usage period has an invalid timestamp.",
      sourceAttempt(source)
    );
  }
  return {
    ok: true,
    value: { startsAt: startsAt.value, resetsAt: resetsAt.value }
  };
}

function parseOnDemand(
  value: unknown,
  source: UsageSource
): ProviderResult<OnDemandState> {
  const onDemand = asRecord(value);
  if (
    onDemand === null ||
    !(
      typeof onDemand.enabled === "boolean" ||
      onDemand.enabled === null
    )
  ) {
    return failure(
      "json-schema-mismatch",
      "Cursor on-demand state is invalid.",
      sourceAttempt(source)
    );
  }
  const personalSpend = parseNullableMoney(onDemand.personalSpend);
  if (!personalSpend.ok) {
    return failure(
      "invalid-value",
      "Cursor personal on-demand spend is invalid.",
      sourceAttempt(source)
    );
  }
  if (onDemand.enabled !== true && personalSpend.value !== null) {
    return failure(
      "invalid-value",
      "Cursor on-demand spend requires an enabled state.",
      sourceAttempt(source)
    );
  }
  if (onDemand.enabled === true) {
    return {
      ok: true,
      value: { enabled: true, personalSpend: personalSpend.value }
    };
  }
  return {
    ok: true,
    value: {
      enabled: onDemand.enabled,
      personalSpend: null
    }
  };
}

function parseTeamContext(
  value: unknown,
  source: UsageSource
): ProviderResult<TeamContext> {
  if (value === undefined) {
    return {
      ok: true,
      value: {
        sharedSpendLimit: null,
        dynamicSpendLimit: null,
        sharedSpendUsed: null,
        sharedSpendRemaining: null
      }
    };
  }
  const teamContext = asRecord(value);
  if (
    teamContext === null ||
    !(
      typeof teamContext.dynamicSpendLimit === "boolean" ||
      teamContext.dynamicSpendLimit === null
    )
  ) {
    return failure(
      "json-schema-mismatch",
      "Cursor team context is invalid.",
      sourceAttempt(source)
    );
  }
  const sharedSpendLimit = parseNullableMoney(teamContext.sharedSpendLimit);
  if (!sharedSpendLimit.ok) {
    return failure(
      "invalid-value",
      "Cursor shared team spend limit is invalid.",
      sourceAttempt(source)
    );
  }
  // ABSENT is not INVALID. These two fields were added after the first release, so
  // every snapshot already cached on a user's machine lacks them. Requiring them
  // would reject the whole cache on upgrade and blank the panel until the next
  // successful fetch - a self-inflicted outage for a purely additive field. `null`
  // and "not present" both mean "not reported".
  const sharedSpendUsed = parseNullableMoney(
    teamContext.sharedSpendUsed ?? null
  );
  const sharedSpendRemaining = parseNullableMoney(
    teamContext.sharedSpendRemaining ?? null
  );
  if (!sharedSpendUsed.ok || !sharedSpendRemaining.ok) {
    return failure(
      "invalid-value",
      "Cursor shared team spend usage is invalid.",
      sourceAttempt(source)
    );
  }
  return {
    ok: true,
    value: {
      sharedSpendLimit: sharedSpendLimit.value,
      dynamicSpendLimit: teamContext.dynamicSpendLimit,
      sharedSpendUsed: sharedSpendUsed.value,
      sharedSpendRemaining: sharedSpendRemaining.value
    }
  };
}

function parseNullableQuantity(
  value: unknown
): { ok: true; value: Quantity | null } | { ok: false } {
  if (value === null) {
    return { ok: true, value: null };
  }
  const quantity = asRecord(value);
  const quantityValue = optionalNonNegativeNumber(quantity?.value);
  if (
    quantity === null ||
    quantityValue === null ||
    !isUsageUnit(quantity.unit)
  ) {
    return { ok: false };
  }
  return {
    ok: true,
    value: {
      value: quantityValue,
      unit: quantity.unit
    }
  };
}

function parseNullableMoney(
  value: unknown
): { ok: true; value: Money | null } | { ok: false } {
  if (value === null) {
    return { ok: true, value: null };
  }
  const money = asRecord(value);
  const amount = optionalNonNegativeNumber(money?.amount);
  if (
    money === null ||
    amount === null ||
    typeof money.currency !== "string" ||
    !/^[A-Z]{3}$/u.test(money.currency)
  ) {
    return { ok: false };
  }
  return {
    ok: true,
    value: { amount, currency: money.currency }
  };
}

function parseHtmlPeriod(usage: string, spending: string): UsagePeriod | null {
  const cycle = usage.match(
    /Billing cycle:\s+([A-Za-z]+ \d{1,2}, \d{4})\s+to\s+([A-Za-z]+ \d{1,2}, \d{4})/iu
  );
  if (cycle !== null) {
    const startsAt = calendarDateToIso(cycle[1]);
    const resetsAt = calendarDateToIso(cycle[2]);
    return startsAt === null || resetsAt === null
      ? null
      : { startsAt, resetsAt };
  }
  const reset = spending.match(/Resets\s+([A-Za-z]+ \d{1,2}, \d{4})/iu);
  const resetsAt = calendarDateToIso(reset?.[1]);
  return resetsAt === null ? null : { startsAt: null, resetsAt };
}

function parseHtmlOnDemand(
  text: string
): { state: OnDemandState; teamContext: TeamContext } | null {
  const status = text.match(/Status:\s+(Enabled|Disabled)/iu)?.[1]?.toLowerCase();
  if (status === undefined) {
    return null;
  }
  const personalSpend =
    status === "enabled" ? parseMoneyText(text, "Personal spend") : null;
  if (status === "enabled" && personalSpend === null) {
    return null;
  }
  const state: OnDemandState =
    status === "enabled"
      ? { enabled: true, personalSpend }
      : { enabled: false, personalSpend: null };
  return {
    state,
    teamContext: {
      sharedSpendLimit: parseMoneyText(text, "Team spend limit"),
      dynamicSpendLimit: null,
      sharedSpendUsed: null,
      sharedSpendRemaining: null
    }
  };
}

function parseMoneyText(text: string, label: string): Money | null {
  const match = text.match(
    new RegExp(`${escapeRegExp(label)}:\\s+([A-Z]{3})\\s+([0-9]+(?:\\.[0-9]+)?)`, "iu")
  );
  if (match?.[1] === undefined || match[2] === undefined) {
    return null;
  }
  const amount = Number(match[2]);
  return Number.isFinite(amount) ? { amount, currency: match[1] } : null;
}

function parsePercent(text: string, label: string): number | null {
  const match = text.match(
    new RegExp(
      `${escapeRegExp(label)}\\s+([0-9]+(?:\\.[0-9]+)?)%\\s+used`,
      "iu"
    )
  );
  const value = match?.[1] === undefined ? Number.NaN : Number(match[1]);
  return Number.isFinite(value) && value >= 0 ? value : null;
}

function parseTokenTotal(text: string, label: string): Quantity | null {
  const match = text.match(
    new RegExp(
      `${escapeRegExp(label)}\\s+([0-9]+(?:\\.[0-9]+)?)\\s+([0-9]+(?:\\.[0-9]+)?)`,
      "iu"
    )
  );
  if (match?.[1] === undefined || match[2] === undefined) {
    return null;
  }
  const input = Number(match[1]);
  const output = Number(match[2]);
  return Number.isFinite(input) && Number.isFinite(output)
    ? { value: input + output, unit: "tokens" }
    : null;
}

function sourcePercentMeter(
  used: Quantity,
  percentUsed: number
): IncludedUsageMeter {
  return {
    used,
    limit: null,
    percentUsed,
    percentOrigin: "source"
  };
}

function looksLikeLogin(text: string): boolean {
  return /\b(sign in|log in|authentication required)\b/iu.test(text);
}

function hasSpendingAnchors(text: string): boolean {
  return [
    "Spending",
    "Included Usage",
    "Cursor Models",
    "Other Models",
    "On-Demand Usage"
  ].every((anchor) => text.includes(anchor));
}

function hasUsageAnchors(text: string): boolean {
  return ["Usage", "Billing cycle", "Input tokens", "Output tokens"].every(
    (anchor) => text.includes(anchor)
  );
}

function calendarDateToIso(value: string | undefined): string | null {
  if (value === undefined) {
    return null;
  }
  const timestamp = Date.parse(`${value} 00:00:00 UTC`);
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : null;
}

function nullableIsoTimestamp(
  value: unknown
): { ok: true; value: string | null } | { ok: false } {
  if (value === null) {
    return { ok: true, value: null };
  }
  return isIsoTimestamp(value) ? { ok: true, value } : { ok: false };
}

function isIsoTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/u.test(
      value
    ) &&
    Number.isFinite(Date.parse(value))
  );
}

function optionalNonNegativeNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? value
    : null;
}

function isUsageUnit(value: unknown): value is UsageUnit {
  return typeof value === "string" && USAGE_UNITS.has(value);
}

function parseStaleReason(value: unknown): StaleReason | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase().replace(/[\s_]+/gu, "-");
  return isStaleReason(normalized) ? normalized : null;
}

function isStaleReason(value: string): value is StaleReason {
  return STALE_REASONS.has(value);
}

function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&nbsp;/giu, " ")
    .replace(/&amp;/giu, "&")
    .replace(/&lt;/giu, "<")
    .replace(/&gt;/giu, ">")
    .replace(/&quot;/giu, '"')
    .replace(/&#39;/giu, "'");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function sourceAttempt(source: UsageSource): LiveUsageSource | null {
  return source === "credential-api" || source === "html-scrape"
    ? source
    : null;
}

function failure<T>(
  code: ProviderErrorCode,
  message: string,
  sourceAttemptValue: LiveUsageSource | null,
  details: Partial<Pick<ProviderError, "statusCode" | "retryAt">> = {}
): ProviderResult<T> {
  return {
    ok: false,
    error: {
      code,
      message,
      sourceAttempt: sourceAttemptValue,
      recoverable: ![
        "invalid-value",
        "unit-mismatch",
        "json-schema-mismatch",
        "html-schema-mismatch"
      ].includes(code),
      ...details
    }
  };
}
