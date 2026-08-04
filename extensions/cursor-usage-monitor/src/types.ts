export type UsageSource =
  | "credential-api"
  | "html-scrape"
  | "cache"
  | "manual";

export type LiveUsageSource = Extract<
  UsageSource,
  "credential-api" | "html-scrape"
>;
export type NonCacheUsageSource = Exclude<UsageSource, "cache">;
export type UsageUnit = "tokens" | "requests" | "percent";
export type PercentOrigin = "source" | "calculated";

export interface Quantity {
  value: number;
  unit: UsageUnit;
}

export interface Money {
  amount: number;
  currency: string;
}

export interface IncludedUsageMeter {
  used: Quantity | null;
  limit: Quantity | null;
  percentUsed: number | null;
  percentOrigin: PercentOrigin | null;
}

export interface UsagePeriod {
  startsAt: string | null;
  resetsAt: string | null;
}

export type OnDemandState =
  | { enabled: true; personalSpend: Money | null }
  | { enabled: false; personalSpend: null }
  | { enabled: null; personalSpend: null };

export interface TeamContext {
  sharedSpendLimit: Money | null;
  dynamicSpendLimit: boolean | null;
}

export type StaleReason =
  | "age-threshold"
  | "fetch-failed"
  | "rate-limited"
  | "authentication-required"
  | "visibility-restricted"
  | "schema-drift"
  | "period-reset-passed"
  | "allowance-unavailable";

interface UsageSnapshotFields {
  period: UsagePeriod;
  cursorModels: IncludedUsageMeter;
  otherModels: IncludedUsageMeter;
  onDemand: OnDemandState;
  teamContext: TeamContext;
  fetchedAt: string;
}

type SourceProvenance =
  | { source: NonCacheUsageSource; cachedFrom?: never }
  | { source: "cache"; cachedFrom: NonCacheUsageSource };

export type FreshUsageSnapshot = UsageSnapshotFields &
  SourceProvenance & { stale: false; staleReason: null };

export type StaleUsageSnapshot = UsageSnapshotFields &
  SourceProvenance & { stale: true; staleReason: StaleReason };

export type UsageSnapshot = FreshUsageSnapshot | StaleUsageSnapshot;

export type ProviderErrorCode =
  | "authorization-required"
  | "missing-credential"
  | "invalid-credential"
  | "session-expired"
  | "dashboard-visibility-restricted"
  | "unsupported-data-path"
  | "endpoint-unavailable"
  | "login-redirect"
  | "client-shell"
  | "html-schema-mismatch"
  | "json-schema-mismatch"
  | "unit-mismatch"
  | "invalid-value"
  | "timeout"
  | "cancelled"
  | "network-error"
  | "rate-limited"
  | "service-error"
  | "credential-adapter-unavailable"
  | "credential-store-error";

export interface ProviderError {
  code: ProviderErrorCode;
  message: string;
  sourceAttempt: LiveUsageSource | null;
  recoverable: boolean;
  statusCode?: number;
  retryAt?: string;
}

export type ProviderResult<T> =
  | { ok: true; value: T }
  | { ok: false; error: ProviderError };

export type UsageState =
  | { state: "fresh"; data: FreshUsageSnapshot }
  | { state: "stale"; data: StaleUsageSnapshot; error: ProviderError }
  | { state: "empty"; error: ProviderError };

export const METER_FILL_COLOR = "#4682B4" as const;
