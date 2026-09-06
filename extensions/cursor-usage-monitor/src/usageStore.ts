import type {
  FreshUsageSnapshot,
  IncludedUsageMeter,
  NonCacheUsageSource,
  ProviderError,
  ProviderResult,
  StaleReason,
  StaleUsageSnapshot,
  UsageSnapshot,
  UsageState
} from "./types";
import { normalizeSnapshotPayload } from "./providers/normalizer";

const SNAPSHOT_KEY = "cursorUsage.snapshot";
const MANUAL_KEY = "cursorUsage.manual";
const DEFAULT_STALE_AFTER_MS = 30 * 60_000;

export interface MementoLike {
  get<T>(key: string): T | undefined;
  update(key: string, value: unknown): Thenable<void>;
}

export class UsageStore {
  private staleAfterMs: number;
  private writeQueue: Promise<void> = Promise.resolve();

  public constructor(
    private readonly state: MementoLike,
    staleAfterMs = DEFAULT_STALE_AFTER_MS
  ) {
    this.staleAfterMs = Math.max(60_000, staleAfterMs);
  }

  public setStaleAfterMs(staleAfterMs: number): void {
    this.staleAfterMs = Math.max(60_000, staleAfterMs);
  }

  public getCache(now = Date.now()): UsageSnapshot | undefined {
    const snapshot = decodeStoredSnapshot(
      this.state.get<unknown>(SNAPSHOT_KEY),
      ["credential-api", "html-scrape"]
    );
    return snapshot === undefined
      ? undefined
      : refreshSnapshot(snapshot, now, this.staleAfterMs, true);
  }

  public getManual(now = Date.now()): UsageSnapshot | undefined {
    const snapshot = decodeStoredSnapshot(
      this.state.get<unknown>(MANUAL_KEY),
      ["manual"]
    );
    return snapshot === undefined
      ? undefined
      : refreshSnapshot(snapshot, now, this.staleAfterMs, false);
  }

  public async saveSuccess(
    snapshot: UsageSnapshot
  ): Promise<FreshUsageSnapshot> {
    if (
      snapshot.source !== "credential-api" &&
      snapshot.source !== "html-scrape"
    ) {
      throw new TypeError("saveSuccess requires a live Cursor usage source.");
    }
    const fresh: FreshUsageSnapshot = {
      ...snapshot,
      stale: false,
      staleReason: null
    };
    return this.serializeWrite(async () => {
      await this.state.update(SNAPSHOT_KEY, fresh);
      return fresh;
    });
  }

  public async saveManual(
    snapshot: UsageSnapshot
  ): Promise<FreshUsageSnapshot> {
    const { cachedFrom: _cachedFrom, ...fields } = snapshot;
    const manual: FreshUsageSnapshot = {
      ...fields,
      source: "manual",
      stale: false,
      staleReason: null
    };
    return this.serializeWrite(async () => {
      await this.state.update(MANUAL_KEY, manual);
      return manual;
    });
  }

  /**
   * Drops only the credential-derived cache, leaving manually entered usage in
   * place. Revoking consent must purge what the session read produced without
   * discarding data the user typed themselves.
   */
  public clearCache(): Promise<void> {
    return this.serializeWrite(async () => {
      const previousSnapshot = this.state.get<unknown>(SNAPSHOT_KEY);
      try {
        await this.state.update(SNAPSHOT_KEY, undefined);
      } catch (error) {
        try {
          await this.state.update(SNAPSHOT_KEY, previousSnapshot);
        } catch {
          // Best effort only: the caller retains and re-renders prior state.
        }
        throw error;
      }
    });
  }

  public clear(): Promise<void> {
    return this.serializeWrite(async () => {
      const previousSnapshot = this.state.get<unknown>(SNAPSHOT_KEY);
      const previousManual = this.state.get<unknown>(MANUAL_KEY);
      try {
        await this.state.update(SNAPSHOT_KEY, undefined);
        await this.state.update(MANUAL_KEY, undefined);
      } catch (error) {
        await this.restoreAfterFailedClear(previousSnapshot, previousManual);
        throw error;
      }
    });
  }

  public async resolveFetch(
    result: ProviderResult<UsageSnapshot>,
    now = Date.now()
  ): Promise<UsageState> {
    if (result.ok) {
      const fresh = await this.saveSuccess(result.value);
      return { state: "fresh", data: fresh };
    }

    const fallback = this.getCache(now) ?? this.getManual(now);
    if (fallback !== undefined) {
      return {
        state: "stale",
        data: applyFailureReason(fallback, result.error),
        error: result.error
      };
    }
    return { state: "empty", error: result.error };
  }

  public hasExpiredReset(now = Date.now()): boolean {
    const snapshot = decodeStoredSnapshot(
      this.state.get<unknown>(SNAPSHOT_KEY),
      ["credential-api", "html-scrape"]
    );
    return snapshot === undefined ? false : resetHasPassed(snapshot, now);
  }

  private serializeWrite<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.writeQueue.then(operation);
    this.writeQueue = result.then(
      () => undefined,
      () => undefined
    );
    return result;
  }

  private async restoreAfterFailedClear(
    snapshot: unknown,
    manual: unknown
  ): Promise<void> {
    try {
      await this.state.update(SNAPSHOT_KEY, snapshot);
      await this.state.update(MANUAL_KEY, manual);
    } catch {
      // Best effort only: callers retain and re-render their prior in-memory state.
    }
  }
}

/**
 * What the user is actually looking at. Kept here rather than in the panel so the
 * status bar, dashboard, and runtime notices cannot drift into describing the same
 * snapshot three different ways.
 */
export type UsageProvenance = "live" | "cache" | "manual";

const STALE_REASON_TEXT: Record<StaleReason, string> = {
  "age-threshold": "older than the staleness window",
  "fetch-failed": "the last refresh failed",
  "rate-limited": "Cursor rate limited the refresh",
  "authentication-required": "the Cursor session needs re-authorizing",
  "visibility-restricted": "this account role cannot see spending",
  "schema-drift": "the usage response no longer matches the approved contract",
  "period-reset-passed": "the billing period reset after this data was captured",
  "allowance-unavailable": "the allowance denominator is unavailable"
};

export function snapshotProvenance(snapshot: UsageSnapshot): UsageProvenance {
  if (snapshot.source === "manual") {
    return "manual";
  }
  if (snapshot.source === "cache") {
    return snapshot.cachedFrom === "manual" ? "manual" : "cache";
  }
  return "live";
}

/**
 * Renders provenance and staleness as one phrase. A stale snapshot always says so,
 * which is the guarantee that stale data is never presented as current.
 */
export function describeProvenance(snapshot: UsageSnapshot): string {
  const origin = provenanceText(snapshotProvenance(snapshot));
  return snapshot.stale
    ? `${origin} (stale: ${STALE_REASON_TEXT[snapshot.staleReason]})`
    : origin;
}

function provenanceText(provenance: UsageProvenance): string {
  if (provenance === "live") {
    return "Live Cursor usage";
  }
  return provenance === "manual"
    ? "Manually entered usage"
    : "Cached Cursor usage";
}

export function refreshSnapshot(
  snapshot: UsageSnapshot,
  now: number,
  staleAfterMs: number,
  asCache: boolean
): UsageSnapshot {
  const resetPassed = resetHasPassed(snapshot, now);
  const fetchedAt = Date.parse(snapshot.fetchedAt);
  const stale =
    resetPassed ||
    !Number.isFinite(fetchedAt) ||
    now - fetchedAt >= Math.max(60_000, staleAfterMs);
  const common = {
    period: snapshot.period,
    cursorModels: resetPassed
      ? suppressPercentage(snapshot.cursorModels)
      : snapshot.cursorModels,
    otherModels: resetPassed
      ? suppressPercentage(snapshot.otherModels)
      : snapshot.otherModels,
    onDemand: snapshot.onDemand,
    teamContext: snapshot.teamContext,
    fetchedAt: snapshot.fetchedAt
  };
  const staleReason: StaleReason = resetPassed
    ? "period-reset-passed"
    : "age-threshold";

  if (asCache || snapshot.source === "cache") {
    const cache = {
      ...common,
      source: "cache" as const,
      cachedFrom: cacheOrigin(snapshot)
    };
    return stale
      ? { ...cache, stale: true, staleReason }
      : { ...cache, stale: false, staleReason: null };
  }

  const direct = { ...common, source: snapshot.source };
  return stale
    ? { ...direct, stale: true, staleReason }
    : { ...direct, stale: false, staleReason: null };
}

function applyFailureReason(
  snapshot: UsageSnapshot,
  error: ProviderError
): StaleUsageSnapshot {
  if (snapshot.staleReason === "period-reset-passed") {
    return snapshot;
  }
  return {
    ...snapshot,
    stale: true,
    staleReason: staleReasonFor(error)
  };
}

function staleReasonFor(error: ProviderError): StaleReason {
  if (error.code === "rate-limited") {
    return "rate-limited";
  }
  if (
    error.code === "authorization-required" ||
    error.code === "missing-credential" ||
    error.code === "session-expired"
  ) {
    return "authentication-required";
  }
  if (error.code === "dashboard-visibility-restricted") {
    return "visibility-restricted";
  }
  if (
    error.code === "json-schema-mismatch" ||
    error.code === "html-schema-mismatch" ||
    error.code === "unit-mismatch" ||
    error.code === "invalid-value"
  ) {
    return "schema-drift";
  }
  return "fetch-failed";
}

function resetHasPassed(snapshot: UsageSnapshot, now: number): boolean {
  if (snapshot.period.resetsAt === null) {
    return false;
  }
  const resetAt = Date.parse(snapshot.period.resetsAt);
  const fetchedAt = Date.parse(snapshot.fetchedAt);
  return (
    Number.isFinite(resetAt) &&
    Number.isFinite(fetchedAt) &&
    resetAt <= now &&
    fetchedAt < resetAt
  );
}

function suppressPercentage(meter: IncludedUsageMeter): IncludedUsageMeter {
  return {
    ...meter,
    percentUsed: null,
    percentOrigin: null
  };
}

function cacheOrigin(
  snapshot: UsageSnapshot
): NonCacheUsageSource {
  return snapshot.source === "cache" ? snapshot.cachedFrom : snapshot.source;
}

function decodeStoredSnapshot(
  value: unknown,
  allowedSources: readonly NonCacheUsageSource[]
): UsageSnapshot | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return undefined;
  }
  const source = (value as Record<string, unknown>).source;
  if (
    !isNonCacheUsageSource(source) ||
    !allowedSources.includes(source)
  ) {
    return undefined;
  }
  const result = normalizeSnapshotPayload(value, {
    source
  });
  return result.ok ? result.value : undefined;
}

function isNonCacheUsageSource(value: unknown): value is NonCacheUsageSource {
  return (
    value === "credential-api" ||
    value === "html-scrape" ||
    value === "manual"
  );
}
