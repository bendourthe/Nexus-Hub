import type {
  AllowanceSource,
  AllowanceState,
  MetricKind,
  UsageMetric,
  UsageSnapshot,
  UsageUnit
} from "../types";
import { PRODUCTS_WITHOUT_ALLOWANCE } from "./planEntitlements";

export interface AllowanceValue {
  value: number;
  unit: UsageUnit;
}

export type AllowanceMap = Partial<Record<MetricKind, AllowanceValue>>;

export interface AllowanceInputs {
  /**
   * NEVER POPULATED, and a test asserts it stays that way.
   *
   * The v3.16.3 Phase 2 probe checked every documented endpoint field by field:
   * `/settings/billing/usage`, `/usage/summary`, the AI-credit and premium-request
   * endpoints, and the Budgets API. None serves an entitlement, quota, or remaining
   * balance, and `/usage/summary` reports `discountQuantity == grossQuantity` on
   * every row, so it does not serve the drawdown either. The legacy endpoints that
   * did return `included_minutes` closed down in September 2025.
   *
   * The field is retained because it is exactly the shape a future GitHub
   * entitlement field would fill, and re-adding it later would be a wider change
   * than leaving it. Populating it from a static table would be a lie about
   * provenance - use `planTable` for that.
   */
  api?: AllowanceMap;
  /** Derived from `GET /user`'s `plan.name` against GitHub's published table. */
  planTable?: AllowanceMap;
  /** Set explicitly by the user, overriding the derived value. */
  manual?: AllowanceMap;
}

export interface MetricAllowanceInput {
  /** Quantity counted against the allowance. Null when it could not be reconstructed. */
  drawdown: number | null;
  drawdownBasis: UsageMetric["drawdownBasis"];
}

export function applyAllowances(
  snapshot: UsageSnapshot,
  inputs: AllowanceInputs,
  drawdowns: Partial<Record<MetricKind, MetricAllowanceInput>> = {}
): UsageSnapshot {
  const forMetric = (metric: UsageMetric): UsageMetric =>
    applyMetricAllowance(metric, inputs, drawdowns[metric.kind]);
  return {
    ...snapshot,
    copilot: forMetric(snapshot.copilot),
    actionsMinutes: forMetric(snapshot.actionsMinutes),
    actionsStorage: forMetric(snapshot.actionsStorage)
  };
}

/**
 * Resolves one metric to a denominator, a numerator, and a state.
 *
 * Precedence for the denominator is manual, then the plan table, then the API field
 * that is never populated. Manual wins because it is the only source that can be
 * right when the published figure is wrong for an account - data packs, Education
 * benefits, and negotiated terms are all invisible to the API.
 *
 * A percentage is produced ONLY when a denominator and a drawdown numerator both
 * exist. `used` is never the numerator: it is gross consumption, which includes
 * free public-repository usage. On the account this was measured against, `used`
 * was 1,287 minutes where the drawdown was about 121 - dividing `used` by the
 * allowance would render 64% where the truth is 6%.
 */
export function applyMetricAllowance(
  metric: UsageMetric,
  inputs: AllowanceInputs,
  drawdownInput?: MetricAllowanceInput
): UsageMetric {
  const manual = validMatchingAllowance(metric, inputs.manual?.[metric.kind]);
  const planTable = validMatchingAllowance(metric, inputs.planTable?.[metric.kind]);
  const api = validMatchingAllowance(metric, inputs.api?.[metric.kind]);

  const allowance = manual ?? planTable ?? api;
  const allowanceSource: AllowanceSource =
    manual !== null ? "manual" : planTable !== null ? "plan-table" : api !== null ? "api" : "unknown";

  const drawdown = drawdownInput?.drawdown ?? null;
  const drawdownBasis = drawdownInput?.drawdownBasis ?? "unavailable";

  const allowanceState: AllowanceState = PRODUCTS_WITHOUT_ALLOWANCE.has(metric.kind)
    ? "none"
    : allowance !== null && drawdown !== null
      ? "verified"
      : "unknown";

  return {
    ...metric,
    drawdown,
    drawdownBasis,
    allowance: allowanceState === "none" ? null : allowance,
    allowanceSource: allowanceState === "none" ? "unknown" : allowanceSource,
    allowanceState,
    // Guarded on the state rather than on the allowance alone, so a `none` metric
    // can never render a percentage even if a stale allowance is present.
    percentage:
      allowanceState === "verified" && allowance !== null && drawdown !== null && allowance > 0
        ? (drawdown / allowance) * 100
        : null
  };
}

/**
 * A candidate allowance is usable only when its unit matches the metric's exactly.
 *
 * The check is doing its job and is deliberately kept. Storage was the case that
 * made it look broken: GitHub's billing page expresses the entitlement in GB while
 * the usage API reports consumption in GigabyteHours, so a user entering `0.5` was
 * silently refused. The fix is to convert the CONSUMPTION into GB before it reaches
 * here - see `gigabyteHoursToGigabyteMonths` - not to loosen the guard and start
 * comparing quantities of different dimensions.
 */
function validMatchingAllowance(metric: UsageMetric, candidate: AllowanceValue | undefined): number | null {
  if (
    candidate === undefined ||
    candidate.unit.toLowerCase() !== metric.unit.toLowerCase() ||
    !Number.isFinite(candidate.value) ||
    candidate.value <= 0
  ) {
    return null;
  }
  return candidate.value;
}

/**
 * The sentence shown beside a metric that has no bar, explaining which of the two
 * absences it is.
 *
 * An explained absence is a good UI; an unexplained blank is the bug being fixed.
 */
export function explainMissingPercentage(metric: UsageMetric): string {
  if (metric.allowanceState === "none") {
    return "Your plan includes no allowance for this product, so this is your total usage rather than a share of a limit.";
  }
  if (metric.allowance === null) {
    return "No allowance is known for this metric, so only absolute usage is shown. Set one in Settings to see a percentage.";
  }
  return "GitHub does not report how much of this allowance you have consumed, and it could not be reconstructed for this period, so only absolute usage is shown.";
}
