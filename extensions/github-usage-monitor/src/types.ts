export type BillingScope = "user" | "organization" | "enterprise";

export type BillingOwner =
  | { scope: "user"; name: string }
  | { scope: "organization"; name: string }
  | { scope: "enterprise"; name: string };

export type UsageSource = "api" | "cache" | "manual";
export type CopilotMetricKind = "copilot-ai-credits" | "copilot-premium-requests";
export type MetricKind = CopilotMetricKind | "actions-minutes" | "actions-storage";
export type AllowanceSource = "api" | "manual" | "unknown";
export type ResetKind = "quota" | "reporting-period";

export type UsageUnit =
  | "ai-credits"
  | "premium-requests"
  | "minutes"
  | "gigabyte-hours"
  | "gigabytes"
  | string;

export interface MoneyBreakdown {
  grossAmount: number | null;
  discountAmount: number | null;
  netAmount: number | null;
}

export interface SkuUsageBreakdown extends MoneyBreakdown {
  product: string;
  sku: string;
  unit: UsageUnit;
  grossQuantity: number;
  discountQuantity: number | null;
  netQuantity: number | null;
}

export interface ResetInfo {
  at: number;
  kind: ResetKind;
  label: string;
}

export interface UsageMetric extends MoneyBreakdown {
  kind: MetricKind;
  unit: UsageUnit;
  used: number;
  allowance: number | null;
  allowanceSource: AllowanceSource;
  percentage: number | null;
  reset: ResetInfo | null;
  breakdowns: SkuUsageBreakdown[];
}

export interface UsageSnapshot {
  owner: BillingOwner;
  periodStart: number;
  periodEnd: number;
  fetchedAt: number;
  source: UsageSource;
  stale: boolean;
  copilot: UsageMetric;
  actionsMinutes: UsageMetric;
  actionsStorage: UsageMetric;
}

export type ProviderErrorCode =
  | "missing-token"
  | "invalid-token"
  | "invalid-scope"
  | "missing-plan-read"
  | "missing-organization-administration-read"
  | "missing-enterprise-billing-permission"
  | "enhanced-billing-unavailable"
  | "managed-copilot-personal-scope"
  | "not-found"
  | "rate-limited"
  | "timeout"
  | "cancelled"
  | "network-error"
  | "service-error"
  | "schema-mismatch";

export interface RateMetadata {
  remaining: number | null;
  resetAt: number | null;
  retryAfterMs: number | null;
}

export interface ProviderError {
  code: ProviderErrorCode;
  message: string;
  statusCode?: number;
  retryAt?: number;
  requiredPermission?: string;
}

export type ProviderResult<T> =
  | { ok: true; value: T; rate: RateMetadata }
  | { ok: false; error: ProviderError; rate: RateMetadata };

export interface UsageState {
  state: "fresh" | "stale" | "empty";
  data?: UsageSnapshot;
  error?: ProviderError;
}

export interface AlertCycleState {
  cycleId: string;
  notifiedThresholds: number[];
}
