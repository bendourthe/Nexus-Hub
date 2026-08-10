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
export const PRODUCTS_WITHOUT_ALLOWANCE: ReadonlySet<MetricKind> = new Set<MetricKind>([
  "copilot-ai-credits",
  "copilot-premium-requests"
]);

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
