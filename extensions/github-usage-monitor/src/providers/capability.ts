import type { BillingOwner } from "../types";
import type { CredentialKind, ProbeRecord } from "./authProbe";

/**
 * Per-target billing-auth capability.
 *
 * Deliberately NOT a global `DEFAULT_AUTH` flag. OAuth-app authorization and SSO
 * enforcement are per-organization settings, so one user can legitimately end up
 * on a VS Code session for their personal account and organization A, and on a
 * pasted PAT for organization B and an enterprise. A single default cannot express
 * that, and picking one would silently mislabel the others.
 *
 * The T022c evidence this encodes (2026-08-06, recorded in
 * `docs/v3/v3.15/development/github-billing-auth-probe.md`):
 *   - OAuth-app tokens ARE accepted by the enhanced billing usage endpoint
 *   - `X-Accepted-OAuth-Scopes` reports `user` for user scope, and
 *     `admin:org, repo` for organization scope
 *   - `repo` ALONE was sufficient for three organizations
 */

export type BlockedReason =
  | "insufficient-scope"
  | "insufficient-role"
  | "enhanced-billing-unavailable"
  | "oauth-app-approval-required"
  | "sso-authorization-required"
  | "token-type-unsupported"
  | "credential-invalid";

/** Whether a `supported` verdict rests on documentation as well as a live 200. */
export type EvidenceClass = "documented-and-probed" | "probed-only";

export type BillingAuthCapability =
  | {
      status: "supported";
      source: CredentialKind;
      evidence: EvidenceClass;
      /** The scopes the successful call actually carried, from `X-OAuth-Scopes`. */
      grantedScopes: readonly string[];
      verifiedAt: string;
    }
  | {
      status: "blocked";
      reason: BlockedReason;
      /** What GitHub said would be accepted, when it said anything. */
      acceptedScopes: readonly string[];
      detail: string;
      observedAt: string;
    }
  | { status: "unknown" };

/**
 * Scope candidates per level, narrowest first, taken from what GitHub itself
 * reported rather than guessed. `repo` leads for organizations because it was
 * empirically sufficient and VS Code's provider requests it routinely; `admin:org`
 * is held back for an explicit escalation.
 */
export const SCOPE_CANDIDATES: Readonly<
  Record<BillingOwner["scope"], readonly string[]>
> = {
user: ["user"],
  organization: ["repo", "admin:org"],
  enterprise: ["manage_billing:enterprise", "admin:enterprise"]
};

/** A stable key for one billing target. Level is included because a user and an
 * organization can share a slug. */
export function capabilityKey(owner: BillingOwner): string {
  return `${owner.scope}:${owner.name.toLowerCase()}`;
}

/**
 * Scopes every session request must carry for this owner.
 *
 * NOT `[candidates[0]]`. v3.16.4 added `repo` to the user-scope list to make private
 * repositories resolvable, and it had no effect whatsoever because this function
 * returned only the first element - so the session kept asking for `user` alone, the
 * private repository kept 404ing, and the drawdown stayed unresolvable. The
 * escalation list is about which scope to ESCALATE to on a 403; it was never the
 * right thing to truncate a base request to.
 */
/**
 * Scopes every session request must carry for this owner.
 *
 * Deliberately NARROW. v3.16.4 briefly requested `repo` alongside `user` so private
 * repositories could be identified - and that was both excessive and harmful:
 * `repo` grants full read/write over every private repository, and widening the
 * request invalidated the existing session, forcing a fresh OAuth round-trip that
 * failed on the URL handler and left the extension unable to sign in at all.
 *
 * It was never needed. `GET /repos/{owner}/{repo}` succeeds without `repo` scope for
 * a PUBLIC repository and returns 404 for a private one, and every repository in an
 * owner's billing belongs to that owner - so the 404 itself identifies the private
 * repositories. See `RepositoryVisibilityCache`.
 */
/**
 * The scopes a session must carry to read everything this monitor reports for a
 * level - distinct from `SCOPE_CANDIDATES`, which is the ESCALATION ladder.
 *
 * Conflating the two is a mistake this file has made in both directions. v3.16.4
 * added a scope to the candidate list expecting the base request to widen, and
 * nothing changed because only the first element was ever requested; the correction
 * then narrowed the base request to a single scope, which silently capped what the
 * monitor could read.
 *
 * `read:org` is here because `GET /orgs/{org}/copilot/billing` documents exactly two
 * acceptable scopes - `manage_billing:copilot` or `read:org` - and `repo` is neither.
 * Verified 2026-08-11: an organization session holding `repo` alone read billing
 * usage and the organization plan perfectly well, and returned nothing for the
 * Copilot subscription, so the AI-credit allowance could never be composed.
 *
 * `read:org` is the narrower of the two acceptable scopes: it reads organization
 * membership and metadata and grants no write of any kind. `manage_billing:copilot`
 * carries "manage" semantics this monitor has no business holding, and `admin:org`
 * stays where it belongs - behind an explicit escalation.
 */
export const BASE_SCOPES: Readonly<
  Record<BillingOwner["scope"], readonly string[]>
> = {
  user: ["user"],
  organization: ["repo", "read:org"],
  enterprise: ["manage_billing:enterprise"]
};

export function firstScopeCandidate(owner: BillingOwner): readonly string[] {
  return BASE_SCOPES[owner.scope];
}

/**
 * The next scope to try, or null. Escalation is permitted **only** when GitHub's
 * accepted-scope header names a candidate the presented credential did not carry.
 * Retrying with a broader scope merely because a narrower one failed is how an
 * extension ends up holding `admin:org` it never needed.
 */
export function nextScopeEscalation(
  owner: BillingOwner,
  record: Pick<ProbeRecord, "acceptedOAuthScopes" | "grantedOAuthScopes">
): readonly string[] | null {
  const accepted = new Set(record.acceptedOAuthScopes);
  if (accepted.size === 0) {
    return null;
  }
  const granted = new Set(record.grantedOAuthScopes);
  // If the credential ALREADY carries an accepted scope and the call still failed,
  // the failure is not scope-shaped: it is a role, SSO, or app-approval problem.
  // Escalating here would request breadth that cannot fix the actual cause, which
  // is precisely the silent-broadening this resolver must not do. Kept consistent
  // with `diagnoseBlockedReason`, which only reports `insufficient-scope` when no
  // accepted scope is granted.
  if ([...accepted].some((scope) => granted.has(scope))) {
    return null;
  }
  const candidate = SCOPE_CANDIDATES[owner.scope].find(
    (scope) => accepted.has(scope) && !granted.has(scope)
  );
  return candidate === undefined ? null : [candidate];
}

/**
 * Turns a failed probe into a named reason.
 *
 * The ordering matters. A `401` is about the credential, never about the token
 * class, so it is checked first and never reported as `token-type-unsupported`.
 * An OAuth-app or SSO refusal is detected from the message before the generic
 * scope reading, because both produce the same status as a scope gap and only the
 * message distinguishes them.
 */
export function diagnoseBlockedReason(record: ProbeRecord): BlockedReason {
  const message = (record.error?.message ?? "").toLowerCase();

  if (record.status === 401) {
    return "credential-invalid";
  }
  if (message.includes("saml") || message.includes("single sign-on")) {
    return "sso-authorization-required";
  }
  if (
    message.includes("oauth app access restrictions") ||
    message.includes("not authorized") ||
    message.includes("third-party application")
  ) {
    return "oauth-app-approval-required";
  }
  if (
    record.acceptedOAuthScopes.length > 0 &&
    !record.acceptedOAuthScopes.some((scope) =>
      record.grantedOAuthScopes.includes(scope)
    )
  ) {
    return "insufficient-scope";
  }
  if (message.includes("integration") || message.includes("token")) {
    return "token-type-unsupported";
  }
  if (record.status === 404) {
    // GitHub uses 404 for insufficient access as well as for a genuinely absent
    // resource. With no scope evidence to lean on, enhanced billing being
    // unavailable for the owner is the more likely of the two.
    return "enhanced-billing-unavailable";
  }
  return "insufficient-role";
}

export function capabilityFromProbe(record: ProbeRecord): BillingAuthCapability {
  if (record.status === 200) {
    return {
      status: "supported",
      source: record.credentialKind,
      // The endpoint reference enumerates fine-grained support only, so an OAuth
      // success is real but undocumented: weaker than a documented contract, and
      // recorded as such rather than promoted.
      evidence:
        record.credentialKind === "classic-pat"
          ? "documented-and-probed"
          : "probed-only",
      grantedScopes: [...record.grantedOAuthScopes],
      verifiedAt: record.checkedAt
    };
  }
  return {
    status: "blocked",
    reason: diagnoseBlockedReason(record),
    acceptedScopes: [...record.acceptedOAuthScopes],
    detail: record.error?.message ?? `GitHub returned ${record.status}.`,
    observedAt: record.checkedAt
  };
}

const BLOCKED_GUIDANCE: Readonly<Record<BlockedReason, string>> = {
  "insufficient-scope":
    "The credential is missing a scope this billing endpoint requires.",
  // The commonest cause is NOT a missing permission that can be granted. An
  // enterprise-managed or corporate account usually cannot read its own USER-scope
  // billing at all, because the enterprise owns that billing relationship - so the
  // useful advice is to change the scope, not to hunt for a broader credential.
  "insufficient-role":
    "The account is signed in but cannot read billing for this owner. If this is a work or enterprise-managed account, its billing usually belongs to the organization or enterprise rather than to the user - set githubUsageMonitor.billingScope to 'organization' or 'enterprise' and githubUsageMonitor.billingOwner to that slug. If it is a personal account, you need the billing manager role on this owner.",
  "enhanced-billing-unavailable":
    "Enhanced billing is not enabled for this owner, or the owner name is wrong.",
  "oauth-app-approval-required":
    "This organization restricts OAuth apps, so the editor's GitHub app must be approved first.",
  "sso-authorization-required":
    "The credential must be authorized for this organization's SAML single sign-on.",
  "token-type-unsupported":
    "This billing endpoint does not accept this class of token.",
  "credential-invalid":
    "The credential is invalid, revoked, or expired. This says nothing about which token classes are supported."
};

/**
 * A human-facing explanation. Every blocked target explains itself, because a
 * target that merely looks broken is what drives a user to paste a broader
 * credential than the situation needs.
 */
export function describeCapability(
  capability: BillingAuthCapability
): string {
  if (capability.status === "unknown") {
    return "Not yet checked for this billing owner.";
  }
  if (capability.status === "supported") {
    const scopes =
      capability.grantedScopes.length === 0
        ? "no OAuth scopes"
        : capability.grantedScopes.join(", ");
    const strength =
      capability.evidence === "documented-and-probed"
        ? "documented and verified"
        : "verified against this owner, though GitHub does not document it";
    return `Connected via ${capability.source} (${strength}); credential carries ${scopes}.`;
  }
  const suffix =
    capability.acceptedScopes.length === 0
      ? ""
      : ` GitHub reports it would accept: ${capability.acceptedScopes.join(", ")}.`;
  return `${BLOCKED_GUIDANCE[capability.reason]}${suffix}`;
}

export interface CapabilityStateLike {
  get<T>(key: string): T | undefined;
  update(key: string, value: unknown): Thenable<void>;
}

const STORE_KEY = "githubUsageMonitor.authCapability";

interface StoredCapability {
  /** Ties the verdict to the session that produced it. */
  sessionFingerprint: string;
  capability: BillingAuthCapability;
}

/**
 * Remembers a per-target verdict so a verified target is not re-probed on every
 * refresh, and forgets it when the session changes.
 */
export class CapabilityStore {
  public constructor(private readonly state: CapabilityStateLike) {}

  public get(
    owner: BillingOwner,
    sessionFingerprint: string
  ): BillingAuthCapability {
    const all = this.readAll();
    const stored = all[capabilityKey(owner)];
    if (stored === undefined) {
      return { status: "unknown" };
    }
    // A changed session invalidates the verdict rather than inheriting it: the new
    // session may hold different scopes or belong to a different account.
    return stored.sessionFingerprint === sessionFingerprint
      ? stored.capability
      : { status: "unknown" };
  }

  public async remember(
    owner: BillingOwner,
    sessionFingerprint: string,
    capability: BillingAuthCapability
  ): Promise<void> {
    const all = this.readAll();
    all[capabilityKey(owner)] = { sessionFingerprint, capability };
    await this.state.update(STORE_KEY, all);
  }

  public async forget(owner: BillingOwner): Promise<void> {
    const all = this.readAll();
    delete all[capabilityKey(owner)];
    await this.state.update(STORE_KEY, all);
  }

  public async clear(): Promise<void> {
    await this.state.update(STORE_KEY, undefined);
  }

  private readAll(): Record<string, StoredCapability> {
    const raw = this.state.get<unknown>(STORE_KEY);
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
      return {};
    }
    return { ...(raw as Record<string, StoredCapability>) };
  }
}

/**
 * A non-secret fingerprint identifying a session, for cache invalidation. Built
 * from the account label and granted scopes, never from the token: a fingerprint
 * that hashed the token would put a credential-derived value in global state.
 */
export function sessionFingerprint(
  accountLabel: string | undefined,
  scopes: readonly string[]
): string {
  return `${accountLabel ?? "none"}|${[...scopes].sort().join(",")}`;
}
