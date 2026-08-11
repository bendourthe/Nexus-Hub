import type { BillingScope } from "../types";

/**
 * Keeps `billingScope` and `billingOwner` consistent with the signed-in account.
 *
 * These two settings are only meaningful as a PAIR, and nothing used to enforce
 * that. The failure it caused, observed 2026-08-10: an organization was selected
 * (scope=organization, owner=SupiraMedical), then the VS Code account preference was
 * moved back to the personal account. The owner re-resolved to `bendourthe` while
 * the scope stayed `organization`, so the extension queried
 * `/organizations/bendourthe/settings/billing/usage` - a path that cannot exist,
 * because `bendourthe` is a user. It returned `insufficient-role` forever, which read
 * to the user as "the extension cannot connect".
 *
 * The same coupling broke authentication: organization scope requests a different
 * first OAuth scope than user scope, so a stale scope silently changed which
 * permission the session asked for and triggered a re-consent that failed.
 *
 * This module is pure - no `vscode`, no network - so the rule can be tested directly
 * rather than through an activation harness.
 */

export interface OwnerState {
  scope: BillingScope;
  owner: string;
  /** The account the editor session is currently bound to, if any. */
  login: string | null;
  /** Organizations that account belongs to, when known. */
  organizations?: readonly string[];
}

/**
 * Which kind of correction this is, which decides whether it may be APPLIED.
 *
 * The distinction is about whether a correction can become its own trigger:
 *
 *   - `impossible-pair` and `detected-owner` are self-terminating. Each ends in a
 *     state where no rule fires again, so applying them automatically is safe.
 *   - `account-switch` is NOT. It rewrites the owner toward whichever account was
 *     observed, and the write fires a configuration event that reconciles again. When
 *     two GitHub accounts are signed in, `getSession` answers with either one, so
 *     successive rounds see different logins and the pair never settles - a
 *     notification flickering several times a second, reported repeatedly across
 *     2026-08-11.
 *
 * Three attempts to make that rule's INPUT reliable all failed (message dedupe, then
 * a scoped session request, then a bound-account check). The input is not the
 * problem: a rule that writes configuration must not be driven by an observation the
 * editor is free to answer either way. So this one is offered, never applied.
 */
export type ReconciliationKind = "none" | "impossible-pair" | "account-switch" | "detected-owner";

export interface OwnerReconciliation {
  scope: BillingScope;
  owner: string;
  /** True when the stored pair was inconsistent and has been corrected. */
  changed: boolean;
  /** Why it changed, for the log and for the panel. Empty when nothing changed. */
  reason: string;
  /** What kind of correction this is. Decides apply-vs-offer. */
  kind: ReconciliationKind;
  /** False when applying this automatically could re-trigger reconciliation. */
  safeToApply: boolean;
}

function same(left: string, right: string): boolean {
  return left.trim().toLowerCase() === right.trim().toLowerCase();
}

/**
 * Guards the window in which the owner PAIR is mid-write and must not be judged.
 *
 * The settings store has no transaction: `billingScope` and `billingOwner` are two
 * separate writes, and VS Code fires a configuration-change event after each. Between
 * them the pair is briefly inconsistent, and a reconciliation that runs in that
 * window "corrects" a state the user is halfway through choosing.
 *
 * The failure, observed 2026-08-11: picking organization SupiraMedical wrote
 * `scope = organization` first; the change listener refreshed; `reconcileOwner` saw
 * organization scope against the signed-in user's login, applied its
 * cannot-possibly-be-right rule, and reset the scope to `user`. The second write then
 * stored `SupiraMedical` under `user` scope, which the next pass rewrote to the
 * login. The panel ended up showing a personal Free account while the user had
 * explicitly chosen an organization - the exact "numbers describing something else"
 * class this module was written to prevent, caused by the module itself.
 *
 * A depth counter rather than a boolean, so nested or overlapping writes cannot clear
 * the guard early.
 */
let ownerWriteDepth = 0;

export function beginOwnerWrite(): void {
  ownerWriteDepth += 1;
}

export function endOwnerWrite(): void {
  ownerWriteDepth = Math.max(0, ownerWriteDepth - 1);
}

/** True while a pair write is in progress, so no observer may act on what it sees. */
export function ownerWriteInFlight(): boolean {
  return ownerWriteDepth > 0;
}

/** Test-only reset, so a failed write in one case cannot leak into the next. */
export function resetOwnerWriteGuard(): void {
  ownerWriteDepth = 0;
}

export function reconcileOwner(state: OwnerState): OwnerReconciliation {
  const keep = (): OwnerReconciliation => ({ scope: state.scope, owner: state.owner, changed: false, reason: "", kind: "none", safeToApply: true });
  if (state.login === null) return keep();

  // The state that broke: an organization scope pointing at the signed-in USER.
  // No such organization exists, so this can only ever fail.
  if (state.scope === "organization" && same(state.owner, state.login)) {
    return {
      scope: "user",
      owner: state.login,
      changed: true,
      reason: `Billing scope was 'organization' but the owner '${state.owner}' is your user account, which is not an organization. Switched to user scope.`,
      // Self-terminating: the result is scope=user with owner==login, which no rule
      // matches again.
      kind: "impossible-pair",
      safeToApply: true
    };
  }

  // An account switch under user scope: the owner must follow the account, or the
  // monitor reports the previous account's billing under the new identity.
  if (state.scope === "user" && state.owner !== "" && !same(state.owner, state.login)) {
    return {
      scope: "user",
      owner: state.login,
      changed: true,
      reason: `Signed in as '${state.login}' but billing owner was '${state.owner}'. Update the owner to match the account?`,
      // The oscillating rule. Its output is another observation's input, and the
      // observation is not stable when several accounts are signed in.
      kind: "account-switch",
      safeToApply: false
    };
  }

  // User scope with nothing configured yet: record what the session resolved to,
  // rather than re-detecting it on every fetch.
  if (state.scope === "user" && state.owner.trim() === "") {
    // Self-terminating: once the owner is non-empty this rule cannot match again.
    return { scope: "user", owner: state.login, changed: true, reason: `Detected billing owner '${state.login}' from the signed-in account.`, kind: "detected-owner", safeToApply: true };
  }

  // An organization the signed-in account does not belong to cannot be read. Only
  // acted on when the organization list is actually KNOWN - an unavailable list is
  // not evidence of absence, and guessing here would undo a valid configuration.
  if (state.scope === "organization" && state.organizations !== undefined && state.organizations.length > 0) {
    const member = state.organizations.some((org) => same(org, state.owner));
    if (!member) {
      return {
        scope: "user",
        owner: state.login,
        changed: true,
        reason: `'${state.owner}' is not an organization this account belongs to. Switch to your personal billing?`,
        // Same shape as account-switch: it rewrites the owner from an observation.
        kind: "account-switch",
        safeToApply: false
      };
    }
  }

  return keep();
}
