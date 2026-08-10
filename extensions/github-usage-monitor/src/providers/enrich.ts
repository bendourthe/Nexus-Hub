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
  gigabyteHoursToGigabyteMonths,
  hoursInUtcMonth,
  type UsageLineItem,
  type VisibilityMap
} from "./drawdown";
import { entitlementFor, resolvePlan } from "./planEntitlements";
import { applyAllowances, type AllowanceInputs, type AllowanceMap, type MetricAllowanceInput } from "./allowances";
import type { MetricKind, UsageMetric, UsageSnapshot } from "../types";

/** Storage consumption is reported in GigabyteHours; the entitlement is in GB. */
const GIGABYTE_HOURS = /gigabyte[\s_-]?hours?/iu;

export interface EnrichmentInputs {
  visibility: VisibilityMap;
  /** `plan.name` from `GET /user`, or null when it could not be read. */
  planName: string | null;
  /** Values the user set explicitly, which override the derived denominator. */
  manualAllowances?: AllowanceMap;
}

export interface EnrichmentResult {
  snapshot: UsageSnapshot;
  /** Repositories or SKUs excluded because they could not be classified. */
  unresolved: string[];
  /** True when the Actions drawdown needed a runner-OS weight other than 1. */
  usedWeighting: boolean;
}

/** Rebuilds line items from a metric's retained breakdowns. */
function lineItemsOf(metric: UsageMetric): UsageLineItem[] {
  return metric.breakdowns.map((row) => ({
    date: "",
    product: metric.kind.startsWith("actions") ? "Actions" : "Copilot",
    sku: row.sku,
    unitType: row.unit,
    quantity: row.grossQuantity,
    pricePerUnit: null,
    grossAmount: row.grossAmount,
    discountAmount: row.discountAmount,
    netAmount: row.netAmount,
    repositoryName: row.repositoryName
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

  const minutesResult = computeDrawdownMinutes(lineItemsOf(snapshot.actionsMinutes), inputs.visibility);
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

  const planTable: AllowanceMap = {};
  if (entitlement !== null) {
    planTable["actions-minutes"] = { value: entitlement.actionsMinutes, unit: "minutes" };
    // Declared in GB, matching the unit the converted storage figure is now in.
    planTable["actions-storage"] = { value: entitlement.actionsStorageGb, unit: "gigabytes" };
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

  return {
    snapshot: applyAllowances(converted, inputsForAllowances, drawdowns),
    unresolved: minutesResult.unresolvedRepositories,
    usedWeighting: minutesResult.usedWeighting
  };
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
