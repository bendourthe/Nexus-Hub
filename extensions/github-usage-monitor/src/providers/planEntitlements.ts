/**
 * Included product usage per GitHub plan.
 *
 * Source: https://docs.github.com/en/billing/reference/product-usage-included
 * Verified: 2026-08-09
 *
 * WHY THIS TABLE EXISTS AT ALL, AND WHAT IT MAY NOT BECOME
 *
 * No documented GitHub endpoint serves an entitlement. Every field of
 * `/settings/billing/usage`, `/usage/summary`, the AI-credit and premium-request
 * endpoints, and the Budgets API was checked on 2026-08-09; none carries an
 * included allowance, quota, or remaining balance. The legacy endpoints that did
 * return `included_minutes` closed down in September 2025. The figures GitHub shows
 * on its own billing page are composed by the web UI from a source the REST API does
 * not expose. Full evidence: docs/v3/v3.16/development/github-entitlement-probe.md
 *
 * So a denominator has to come from somewhere, and the only automatic source is the
 * account's plan name. That makes this table load-bearing, which makes its limits
 * worth stating plainly rather than discovering later:
 *
 *   - A published figure is not a verified account denominator. Data packs,
 *     grandfathered terms, Education benefits, and negotiated agreements are all
 *     invisible to the API, and this table cannot detect its own disagreement with
 *     an account.
 *   - An unrecognized plan returns `null`. It NEVER falls back to Free. Reporting a
 *     2,000-minute allowance to an Enterprise account would be confidently wrong in
 *     the most expensive direction.
 *   - `allowanceSource` for a value from this table is `"plan-table"`, never
 *     `"api"`. Nothing here was served by GitHub as an entitlement.
 *
 * The UI must show the provenance of any value taken from here, and must offer a
 * discoverable override. Both are requirements, not niceties: the account this was
 * developed against carries Education benefits, so its real entitlement may differ
 * from what its plan name implies.
 */

import type { MetricKind } from "../types";

/** `plan.name` as returned by `GET /user`, lowercased. */
export type PlanName = "free" | "pro" | "team" | "enterprise";

export interface PlanEntitlement {
  /** Actions minutes per month. */
  actionsMinutes: number;
  /** Actions artifact storage, in GB. Compare against GB-hours converted to GB-months. */
  actionsStorageGb: number;
}

/**
 * Per-plan included usage.
 *
 * Deliberately covers only what this extension reports. Codespaces, Packages, and
 * Git LFS figures exist on the same source page but are not surfaced here, because
 * a table entry the extension never reads is a maintenance liability that looks
 * authoritative.
 *
 * Note the Codespaces case, which is why `AllowanceState` has a `"none"` value: the
 * source page publishes a literal **None** for GitHub Team, Enterprise Cloud, and
 * Free-for-organizations. "No allowance exists" is a real state, not a missing
 * measurement.
 */
export const PLAN_ENTITLEMENTS: Readonly<Record<PlanName, PlanEntitlement>> = {
  free: { actionsMinutes: 2_000, actionsStorageGb: 0.5 },
  pro: { actionsMinutes: 3_000, actionsStorageGb: 1 },
  team: { actionsMinutes: 3_000, actionsStorageGb: 2 },
  enterprise: { actionsMinutes: 50_000, actionsStorageGb: 50 }
};

/**
 * Products with no included allowance on any plan this extension reports.
 *
 * Copilot Free carries no AI-credit entitlement, which is why a Copilot card showing
 * `0` with no context was the maintainer's original complaint. The honest answer is
 * not a missing number - it is that there is nothing to draw against.
 */
/**
 * Products with NO included allowance - but only on a plan where that is true.
 *
 * Copilot Free carries no AI-credit entitlement, which is what this set was written
 * for. Copilot Business and Enterprise DO include a monthly premium-request
 * allowance per seat, so asserting "no allowance included with your plan" to a
 * Business seat is a false statement, not a cautious one.
 *
 * The figures themselves are not hardcoded here. This extension has already shipped
 * one confidently wrong number, and the per-seat allowance depends on the seat the
 * ORGANIZATION assigned, which no endpoint this monitor calls will confirm. So a
 * Copilot metric on a non-Free plan is reported as UNKNOWN - "not established" -
 * rather than as either a guess or a false zero.
 */
export const PRODUCTS_WITHOUT_ALLOWANCE: ReadonlySet<MetricKind> = new Set<MetricKind>([
  "copilot-ai-credits",
  "copilot-premium-requests"
]);

/**
 * Whether "no allowance exists" is a claim we can honestly make for this owner.
 *
 * Only for a personal account on a Free plan. An organization-scope owner is billed
 * through a Copilot Business or Enterprise subscription whose seat allowance this
 * monitor cannot read, so the honest answer there is "not established".
 */
export function copilotAllowanceIsKnownAbsent(scope: string, planName: string | null): boolean {
  if (scope !== "user") return false;
  const plan = resolvePlan(planName);
  return plan === "free";
}

/**
 * Included GitHub AI credits per Copilot seat, per month.
 *
 * Source: https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-organizations-and-enterprises
 * Verified: 2026-08-11
 *
 * Unlike Actions minutes, this is not a flat per-plan figure. GitHub pools AI credits
 * at the billing entity: the monthly total is assigned Copilot licenses multiplied by
 * the per-seat figure, and GitHub's own worked example is 100 Business seats sharing
 * 190,000 credits. So a denominator here is COMPOSED, not looked up, which is why it
 * needs more provenance than a plan-table value rather than less.
 *
 * The promotional row is the reason this is a table and not two constants. Existing
 * customers receive a raised allowance from 2026-06-01 through 2026-09-01, and a
 * single hardcoded number is guaranteed to be wrong on one side of that boundary:
 * 3,000 is wrong from September, 1,900 is wrong today. Verified against a live
 * organization on 2026-08-11 - 7 billable Business licenses showing 21,000 included
 * credits, which is exactly 7 x 3,000.
 */
export type CopilotPlanType = "business" | "enterprise";

/** Exclusive end of the promotional window, UTC. From September 1 the standard applies. */
export const AI_CREDIT_PROMOTION_ENDS_UTC = Date.UTC(2026, 8, 1);

export const AI_CREDITS_PER_SEAT: Readonly<
  Record<CopilotPlanType, { standard: number; promotional: number }>
> = {
  business: { standard: 1_900, promotional: 3_000 },
  enterprise: { standard: 3_900, promotional: 7_000 }
};

/**
 * The per-seat figure that applied during a billing period.
 *
 * Resolved against the PERIOD rather than against the current clock, so a snapshot
 * for an earlier month keeps the figure that actually applied to it, and the
 * September transition needs no code change and no release.
 */
export function aiCreditsPerSeat(planType: unknown, periodStartMs: number): number | null {
  if (planType !== "business" && planType !== "enterprise") return null;
  const figures = AI_CREDITS_PER_SEAT[planType];
  return periodStartMs < AI_CREDIT_PROMOTION_ENDS_UTC ? figures.promotional : figures.standard;
}

/**
 * The organization's pooled AI-credit allowance, or null when it cannot be composed.
 *
 * Null on any missing or nonsensical input rather than a partial answer. A seat count
 * that failed to load would otherwise compose into a confidently small denominator,
 * which reads as "you are nearly out" - wrong in the direction that causes a user to
 * change their behavior.
 */
export function aiCreditAllowance(
  planType: unknown,
  seats: unknown,
  periodStartMs: number
): number | null {
  const perSeat = aiCreditsPerSeat(planType, periodStartMs);
  if (perSeat === null) return null;
  if (typeof seats !== "number" || !Number.isInteger(seats) || seats <= 0) return null;
  return perSeat * seats;
}

/** Provenance for a composed AI-credit denominator. A composed number must show its working. */
export function describeAiCreditProvenance(planType: CopilotPlanType, seats: number, perSeat: number): string {
  const plan = planType === "business" ? "Business" : "Enterprise";
  return `${seats} Copilot ${plan} seats x ${perSeat.toLocaleString("en-US")} credits - published figure, not read from your account.`;
}

/**
 * Resolves a `GET /user` `plan.name` to a known plan.
 *
 * Returns `null` for anything unrecognized, including an absent or malformed value.
 * Never guesses, and never defaults to Free.
 */
export function resolvePlan(planName: unknown): PlanName | null {
  if (typeof planName !== "string") return null;
  const normalized = planName.trim().toLowerCase();
  return normalized in PLAN_ENTITLEMENTS ? (normalized as PlanName) : null;
}

/** The entitlement for a plan, or null when the plan could not be resolved. */
export function entitlementFor(planName: unknown): PlanEntitlement | null {
  const plan = resolvePlan(planName);
  return plan === null ? null : PLAN_ENTITLEMENTS[plan];
}

/**
 * Human-readable provenance for a denominator, shown beside the value.
 *
 * The user must be able to see WHERE a number came from before deciding whether to
 * override it. "2,000 min" alone invites the reading that GitHub said so; "2,000 min
 * - published figure for GitHub Free" does not.
 */
export function describeProvenance(plan: PlanName | null): string {
  return plan === null
    ? "Your plan could not be identified, so no allowance is assumed."
    : `Published figure for GitHub ${plan.charAt(0).toUpperCase()}${plan.slice(1)}. Not read from your account - override it if your plan includes a different amount.`;
}
