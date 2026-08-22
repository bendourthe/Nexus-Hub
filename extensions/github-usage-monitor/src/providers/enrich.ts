/**
 * Turns a raw usage snapshot into one carrying drawdown, denominators, and states.
 *
 * This is where the phase's findings meet: the reconstruction (2.3), the
 * plan-derived denominator (2.2), the storage unit conversion (2.4), and the three
 * allowance states (2.5). Kept separate from `extension.ts` so the whole pipeline is
 * unit-testable without a webview or a network.
 */

import {
  computeDrawdownMinutes,
  contributionsByRepository,
  gigabyteHoursToGigabyteMonths,
  hoursInUtcMonth,
  type LinuxReferenceRate,
  type UsageLineItem,
  type VisibilityMap
} from "./drawdown";
import {
  aiCreditAllowance,
  copilotAllowanceIsKnownAbsent,
  entitlementFor,
  resolvePlan,
  type CopilotPlanType
} from "./planEntitlements";

/** Credits are drawn one-for-one; premium requests are metered differently. */
function aiCreditAvailable(kind: MetricKind): kind is "copilot-ai-credits" {
  return kind === "copilot-ai-credits";
}
import { applyAllowances, type AllowanceInputs, type AllowanceMap, type MetricAllowanceInput } from "./allowances";
import type { ActionsDrawdownDetail, MetricKind, UsageMetric, UsageSnapshot } from "../types";

/** Storage consumption is reported in GigabyteHours; the entitlement is in GB. */
const GIGABYTE_HOURS = /gigabyte[\s_-]?hours?/iu;

export interface EnrichmentInputs {
  visibility: VisibilityMap;
  /** `plan.name` for the OWNER being billed, or null when it could not be read. */
  planName: string | null;
  /** Values the user set explicitly, which override the derived denominator. */
  manualAllowances?: AllowanceMap;
  /** The organization's Copilot subscription, when one could be read. */
  copilot?: { planType: CopilotPlanType; seats: number } | null;
}

export interface EnrichmentResult {
  snapshot: UsageSnapshot;
  /** Repositories or SKUs excluded because they could not be classified. */
  unresolved: string[];
  /** The distinct drawdown weights applied, ascending; `[1]` for a single-rate period. */
  appliedWeights: number[];
  /** The standard-Linux denominator those weights were expressed against, and its source. */
  linuxReferenceRate: LinuxReferenceRate;
}

/** Rebuilds line items from a metric's retained breakdowns. */
function lineItemsOf(metric: UsageMetric): UsageLineItem[] {
  return metric.breakdowns.map((row) => ({
    date: "",
    product: metric.kind.startsWith("actions") ? "Actions" : "Copilot",
    sku: row.sku,
    unitType: row.unit,
    quantity: row.grossQuantity,
    // `?? null`: a breakdown persisted by 0.3.x has no such field, and `undefined`
    // is not caught by the `=== null` guard the drawdown uses.
    pricePerUnit: row.pricePerUnit ?? null,
    grossAmount: row.grossAmount,
    discountAmount: row.discountAmount,
    netAmount: row.netAmount,
    // `?? null` for the same reason: a breakdown from 0.1.0 has no such field,
    // and `undefined` is not caught by the `=== null` guard downstream.
    repositoryName: row.repositoryName ?? null
  }));
}

/**
 * Converts a storage metric from GigabyteHours into GB-months so it can be compared
 * against an entitlement expressed in GB.
 *
 * Returns null for any other unit rather than guessing. The unit-matching guard in
 * `allowances.ts` exists precisely to stop a GB figure being compared against a
 * GigabyteHours figure, and this conversion is what lets the comparison happen
 * legitimately instead of by loosening the guard.
 */
export function storageGigabyteMonths(metric: UsageMetric, periodStart: number): number | null {
  if (!GIGABYTE_HOURS.test(metric.unit)) return null;
  return gigabyteHoursToGigabyteMonths(metric.used, hoursInUtcMonth(periodStart));
}

export function enrichSnapshot(snapshot: UsageSnapshot, inputs: EnrichmentInputs): EnrichmentResult {
  const plan = resolvePlan(inputs.planName);
  const entitlement = entitlementFor(inputs.planName);

  const actionsItems = lineItemsOf(snapshot.actionsMinutes);
  const minutesResult = computeDrawdownMinutes(actionsItems, inputs.visibility);
  const contributions = contributionsByRepository(actionsItems, inputs.visibility);
  const storageGb = storageGigabyteMonths(snapshot.actionsStorage, snapshot.periodStart);

  const drawdowns: Partial<Record<MetricKind, MetricAllowanceInput>> = {
    "actions-minutes": {
      drawdown: minutesResult.minutes,
      drawdownBasis: minutesResult.minutes === null ? "unavailable" : "reconstructed"
    },
    // Storage carries no public/private exclusion we can measure, so its reported
    // consumption is used as-is, converted into the entitlement's unit. This is
    // stated as `reported` rather than `reconstructed` so the UI does not claim a
    // reconstruction it did not perform.
    "actions-storage": {
      drawdown: storageGb,
      drawdownBasis: storageGb === null ? "unavailable" : "reported"
    }
  };

  // Copilot credits are the one metric where `used` IS the drawdown.
  //
  // The rule that `used` must never be a numerator was written for Actions minutes,
  // where gross consumption includes free public-repository usage the allowance never
  // sees - 1,287 gross against a 121 drawdown on the account that motivated it. AI
  // credits carry no such exclusion: GitHub's own AI usage page renders exactly this
  // figure over the pooled allowance (225.77 of 21,000, observed 2026-08-11). Stated
  // as `reported`, never `reconstructed`, because nothing was reconstructed.
  if (aiCreditAvailable(snapshot.copilot.kind)) {
    drawdowns[snapshot.copilot.kind] = {
      drawdown: Number.isFinite(snapshot.copilot.used) ? snapshot.copilot.used : null,
      drawdownBasis: Number.isFinite(snapshot.copilot.used) ? "reported" : "unavailable"
    };
  }

  const planTable: AllowanceMap = {};
  if (entitlement !== null) {
    planTable["actions-minutes"] = { value: entitlement.actionsMinutes, unit: "minutes" };
    // Declared in GB, matching the unit the converted storage figure is now in.
    planTable["actions-storage"] = { value: entitlement.actionsStorageGb, unit: "gigabytes" };
  }

  // The pooled Copilot credit allowance, composed from seats and the published
  // per-seat figure that applied during THIS period. Composed rather than read, so it
  // is a `plan-table` value and carries that label's caveats.
  const aiCredits =
    inputs.copilot === undefined || inputs.copilot === null
      ? null
      : aiCreditAllowance(inputs.copilot.planType, inputs.copilot.seats, snapshot.periodStart);
  if (aiCredits !== null) {
    planTable["copilot-ai-credits"] = { value: aiCredits, unit: snapshot.copilot.unit };
  }

  const inputsForAllowances: AllowanceInputs = {
    planTable,
    ...(inputs.manualAllowances === undefined ? {} : { manual: inputs.manualAllowances })
  };

  // The storage metric's unit is rewritten to GB before allowances are applied, so
  // the unit-matching guard compares like with like rather than being bypassed.
  const converted: UsageSnapshot =
    storageGb === null
      ? snapshot
      : {
          ...snapshot,
          actionsStorage: { ...snapshot.actionsStorage, unit: "gigabytes", used: storageGb }
        };

  // A Copilot metric may only be reported as "no allowance included" when that is
  // actually knowable - a personal Free account. For an organization seat, the
  // allowance exists but is unreadable, so the honest state is unknown.
  const enriched = applyAllowances(converted, inputsForAllowances, drawdowns);
  const copilotAbsent = copilotAllowanceIsKnownAbsent(snapshot.owner.scope, inputs.planName);
  const copilot: UsageMetric =
    enriched.copilot.allowanceState === "none" && !copilotAbsent
      ? { ...enriched.copilot, allowanceState: "unknown" }
      : enriched.copilot;

  const actionsDrawdownDetail: ActionsDrawdownDetail = {
    repositories: contributions.map((entry) => ({
      repositoryName: entry.repositoryName,
      visibility: entry.visibility,
      rawMinutes: entry.rawMinutes,
      weightedMinutes: entry.weightedMinutes
    })),
    linuxReferenceRate: minutesResult.linuxReferenceRate.rate,
    linuxRateSource: minutesResult.linuxReferenceRate.source,
    unresolved: minutesResult.unresolvedRepositories,
    allowanceProvenance: describeAllowanceProvenance(enriched.actionsMinutes, inputs.planName)
  };

  return {
    snapshot: { ...enriched, copilot, actionsDrawdownDetail },
    unresolved: minutesResult.unresolvedRepositories,
    appliedWeights: minutesResult.appliedWeights,
    linuxReferenceRate: minutesResult.linuxReferenceRate
  };
}

/**
 * Provenance line for the Actions drawdown NUMERATOR.
 *
 * A deliberate sibling of `describeAllowanceProvenance` rather than an extension of
 * it. That function answers where the DENOMINATOR came from (a plan table or a value
 * the user typed). Since 0.4.0 the numerator has its own provenance - a
 * reconstruction, weighted by a rate that was either observed in the period or fell
 * back to a published constant - and folding two different questions into one
 * sentence is how a provenance line stops being read.
 */
export function describeDrawdownProvenance(detail: ActionsDrawdownDetail | undefined): string {
  if (detail === undefined) {
    return "Reconstructed from private-repository, GitHub-hosted, standard-runner minutes. Refresh to see the rate it was weighted by.";
  }
  const rate = `$${detail.linuxReferenceRate} per Linux minute`;
  const source = detail.linuxRateSource === "observed"
    ? `observed in this period (${rate})`
    : `the published standard rate (${rate}), because this period reported no Linux runner to observe one from`;
  return `Reconstructed from private-repository, GitHub-hosted, standard-runner minutes, each weighted by its own list price relative to ${source}. Public-repository and self-hosted runs are free and never count.`;
}

/** Provenance line for a denominator, shown beside the value in the panel. */
export function describeAllowanceProvenance(metric: UsageMetric, planName: string | null): string {
  if (metric.allowanceSource === "manual") return "Set by you in Settings.";
  if (metric.allowanceSource === "plan-table") {
    const plan = resolvePlan(planName);
    return plan === null
      ? "Published figure for your plan."
      : `Published figure for GitHub ${plan.charAt(0).toUpperCase()}${plan.slice(1)} - not read from your account.`;
  }
  return "No allowance established.";
}
