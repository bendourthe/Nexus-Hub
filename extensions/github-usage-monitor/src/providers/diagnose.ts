import type { BillingOwner } from "../types";
import type { ProbeRecord } from "./authProbe";
import {
  capabilityFromProbe,
  firstScopeCandidate,
  nextScopeEscalation,
  type BillingAuthCapability
} from "./capability";
import {
  bindingFromSession,
  type GetSessionLike,
  type MonitorBinding
} from "./sessionBinding";

/**
 * The in-editor half of T022c: acquire a VS Code GitHub session, run one bounded
 * billing read with it, and record the resulting capability for that target.
 *
 * This is the only way to answer the question the `gh`-token probe could not.
 * OAuth-app authorization and SSO enforcement are per-app, so a result for the
 * GitHub CLI's app says nothing about whether `GitHub for VS Code` is authorized
 * for a given organization. A session exists only inside the editor, so this has
 * to be a command rather than a script.
 *
 * It is also permanently useful rather than throwaway probe code: it is the
 * "why is my billing panel empty" answer for any user, not just this investigation.
 */

export type ProbeWithTokenLike = (options: {
  owner: BillingOwner;
  token: string;
  credentialKind: "vscode-oauth";
  requestedScopes: readonly string[];
  providerReportedScopes: readonly string[];
}) => Promise<ProbeRecord>;

export interface DiagnoseDependencies {
  getSession: GetSessionLike;
  probeWithToken: ProbeWithTokenLike;
}

export type DiagnoseOutcome =
  | { status: "no-session" }
  | {
      status: "probed";
      binding: MonitorBinding;
      record: ProbeRecord;
      capability: BillingAuthCapability;
      /**
       * A broader scope to offer, and ONLY when GitHub's accepted-scope header
       * says it is required. Null means do not offer one, which is the common case.
       */
      escalation: readonly string[] | null;
    };

/**
 * Runs the diagnosis. Interactive by default because the point is to establish
 * whether a session CAN work, which may require creating one; callers wanting a
 * silent check should use `peekBinding` instead.
 */
export async function diagnoseTarget(
  dependencies: DiagnoseDependencies,
  owner: BillingOwner,
  scopes: readonly string[] = firstScopeCandidate(owner)
): Promise<DiagnoseOutcome> {
  const session = await dependencies.getSession("github", scopes, {
    createIfNone: true
  });
  if (session === undefined) {
    return { status: "no-session" };
  }

  const record = await dependencies.probeWithToken({
    owner,
    token: session.accessToken,
    credentialKind: "vscode-oauth",
    requestedScopes: scopes,
    // Kept distinct from what GitHub reports as granted: the editor reports what
    // was REQUESTED, so trusting it would read a narrowed consent as a full grant.
    providerReportedScopes: session.scopes
  });

  return {
    status: "probed",
    binding: bindingFromSession(session),
    record,
    capability: capabilityFromProbe(record),
    escalation: nextScopeEscalation(owner, record)
  };
}

/**
 * A one-line verdict for a notification. Deliberately names the scope GitHub said
 * it would accept, because "blocked" without that is what sends a user hunting for
 * a broader credential than the situation needs.
 */
export function summarizeOutcome(
  outcome: DiagnoseOutcome,
  owner: BillingOwner
): string {
  if (outcome.status === "no-session") {
    return "No GitHub session was granted, so nothing was checked. The stored token, if any, is unchanged.";
  }
  const target = `${owner.scope} ${owner.name}`;
  if (outcome.capability.status === "supported") {
    return `The editor's GitHub session works for ${target}. Recorded as supported for this target.`;
  }
  if (outcome.capability.status === "blocked") {
    const accepted =
      outcome.capability.acceptedScopes.length === 0
        ? ""
        : ` GitHub reports it would accept: ${outcome.capability.acceptedScopes.join(", ")}.`;
    const offer =
      outcome.escalation === null
        ? ""
        : ` You can retry requesting ${outcome.escalation.join(", ")}.`;
    return `The editor's GitHub session did not work for ${target} (${outcome.capability.reason}).${accepted}${offer}`;
  }
  return `The result for ${target} was inconclusive and has not been recorded as either supported or blocked.`;
}
