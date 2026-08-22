export type BillingScope = "user" | "organization" | "enterprise";

export type BillingOwner =
  | { scope: "user"; name: string }
  | { scope: "organization"; name: string }
  | { scope: "enterprise"; name: string };

export type UsageSource = "api" | "cache" | "manual";
export type CopilotMetricKind = "copilot-ai-credits" | "copilot-premium-requests";
export type MetricKind = CopilotMetricKind | "actions-minutes" | "actions-storage";
/**
 * Where a denominator came from.
 *
 * `"api"` is never produced. The v3.16.3 Phase 2 probe confirmed field by field
 * that no documented GitHub endpoint serves an entitlement, and the value is kept
 * only so a future release can populate it if GitHub ever publishes one. See
 * `docs/v3/v3.16/development/github-entitlement-probe.md`.
 */
export type AllowanceSource = "api" | "plan-table" | "manual" | "unknown";

/**
 * Whether a percentage may be rendered for a metric, and if not, why not.
 *
 * Three states rather than two. GitHub's billing page shows an Included-usage panel
 * for Actions, Git LFS, and Packages, and none at all for Copilot and Codespaces -
 * so "this product has no included allowance" is a real, knowable state, distinct
 * from "an allowance may exist but we could not establish it". Collapsing them
 * leaves a Copilot card showing an unexplained blank where the honest answer is
 * that the plan simply includes nothing to draw against.
 *
 * No state may render `0%` or `100%` for a null allowance. That is the data
 * contract's line 71 and the visual contract's line 39.
 */
export type AllowanceState =
  /** A denominator and a drawdown numerator both exist; a percentage is derivable. */
  | "verified"
  /** This plan includes no allowance for this product. Absolute usage is the truth. */
  | "none"
  /** An allowance may exist but was not established. Absolute usage, with an explanation. */
  | "unknown";

/**
 * How the drawdown numerator was arrived at, so the UI can say so rather than
 * presenting a reconstruction as GitHub's own figure.
 */
export type DrawdownBasis =
  /** Reconstructed from private-repository, GitHub-hosted, standard-runner usage with OS weighting. */
  | "reconstructed"
  /** Consumption as reported, with no drawdown reconstruction applied (storage). */
  | "reported"
  /** Reconstruction was attempted and could not complete; no percentage may be shown. */
  | "unavailable";
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
  /**
   * Present only on the plain `/settings/billing/usage` endpoint. Retained rather
   * than parsed away because it is the ONLY field that can separate free
   * public-repository usage from allowance-consuming private usage - the difference
   * between 1,287 reported minutes and the ~121 GitHub actually counts.
   */
  repositoryName: string | null;
  /**
   * List price per unit for this line item, in USD.
   *
   * Present only on the plain `/settings/billing/usage` endpoint; `/usage/summary`
   * omits it, and a snapshot cached by 0.3.x predates the field entirely. `null`
   * therefore means UNKNOWN and never zero. The distinction is load-bearing: the
   * drawdown derives each item's weight from this value relative to the standard
   * Linux rate, so treating an absent price as 0 would silently drop the item from
   * the drawdown instead of marking the reconstruction incomplete.
   */
  pricePerUnit: number | null;
}

export interface ResetInfo {
  at: number;
  kind: ResetKind;
  label: string;
}

export interface UsageMetric extends MoneyBreakdown {
  kind: MetricKind;
  unit: UsageUnit;
  /** Gross consumption as GitHub reports it. NOT the quantity counted against an allowance. */
  used: number;
  /**
   * The quantity actually counted against the included allowance, when it could be
   * established. This is the numerator of any percentage - never `used`.
   *
   * For Actions minutes it is reconstructed: private-repository, GitHub-hosted,
   * standard-runner minutes, each weighted by its own list price relative to the
   * standard Linux rate observed in the same payload. On the account this was
   * measured against, `used` was 1,287 while the drawdown was about 127.
   */
  drawdown: number | null;
  drawdownBasis: DrawdownBasis;
  allowance: number | null;
  allowanceSource: AllowanceSource;
  allowanceState: AllowanceState;
  /** Derived from `drawdown / allowance`. Null unless `allowanceState` is `"verified"`. */
  percentage: number | null;
  reset: ResetInfo | null;
  breakdowns: SkuUsageBreakdown[];
}

/**
 * What the Actions drawdown was reconstructed FROM, so the panel can show its work.
 *
 * Optional on `UsageSnapshot`: a snapshot cached before 0.4.0 has none, and the
 * panel must render without it rather than throwing on an upgrade.
 */
export interface ActionsDrawdownDetail {
  /** Per-repository contributions, sorted by weighted minutes descending. */
  repositories: Array<{
    repositoryName: string;
    visibility: "public" | "private" | "unknown";
    rawMinutes: number;
    weightedMinutes: number;
  }>;
  /** The standard-Linux denominator every weight was expressed against, in USD per minute. */
  linuxReferenceRate: number;
  /** Whether that rate was observed in this period or fell back to the published constant. */
  linuxRateSource: "observed" | "published-fallback";
  /** Repositories or SKUs excluded because they could not be classified or priced. */
  unresolved: string[];
  /**
   * The DENOMINATOR's provenance sentence, resolved at enrichment time.
   *
   * Carried on the snapshot rather than recomputed in the panel because it depends
   * on the account's plan name, which the panel does not have and should not need
   * a second channel to obtain.
   */
  allowanceProvenance: string;
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
  /** Present from 0.4.0 onward; absent on a snapshot cached by an earlier version. */
  actionsDrawdownDetail?: ActionsDrawdownDetail;
}

export type ProviderErrorCode =
  | "missing-token"
  /**
   * No credential at all: no stored token and no editor session.
   *
   * Distinct from `missing-token`, which means a credential exists but is not
   * accepted for this owner. The two need different UI: one is answered by
   * connecting, the other by fixing a permission. Collapsing them is what made an
   * unconnected install present as a failure rather than as a starting point.
   */
  | "not-connected"
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

/**
 * What GitHub says a denied operation would accept. Captured from the response
 * headers because the REST reference's prose cannot answer it: its token section
 * enumerates fine-grained support only, so OAuth's absence there is not a
 * rejection. These turn a bare 403 into an actionable reason.
 */
export interface AcceptedAuthorization {
  /** `X-Accepted-OAuth-Scopes`: what this operation would accept. */
  acceptedOAuthScopes: string[];
  /** `X-OAuth-Scopes`: what the presented token actually carries. */
  grantedOAuthScopes: string[];
  /** `X-Accepted-GitHub-Permissions`: fine-grained equivalent, when reported. */
  acceptedGitHubPermissions: string | null;
}

export interface ProviderError {
  code: ProviderErrorCode;
  message: string;
  statusCode?: number;
  retryAt?: number;
  requiredPermission?: string;
  accepted?: AcceptedAuthorization;
  requestId?: string;
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
