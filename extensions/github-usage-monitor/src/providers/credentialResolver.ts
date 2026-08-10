import type { BillingOwner, ProviderError } from "../types";
import type { BillingAuthCapability } from "./capability";
import { firstScopeCandidate } from "./capability";
import type { GetSessionLike } from "./sessionBinding";

/**
 * Chooses the credential the DATA PATH uses for one billing target.
 *
 * This module exists because v3.15.12 Phase 4 built the per-target auth model and
 * wired it only to the settings display and the diagnostic command - the refresh
 * path still went straight to SecretStorage, so a user with a perfectly good editor
 * session saw "no token stored". The auth model was complete and inert. This is the
 * wiring that makes it load-bearing.
 *
 * Order, and the reasoning for it:
 *   1. An explicitly stored PAT wins. Supplying one is a deliberate act, and
 *      silently preferring a session over it would override an explicit choice.
 *   2. Otherwise the editor's GitHub session, when the target is not already known
 *      to be blocked. This is what delivers "connected with no setup".
 *   3. Otherwise nothing, with a reason the UI can show.
 *
 * A target recorded as `blocked` is skipped rather than retried on every refresh:
 * re-prompting or re-failing on a timer is how a monitor becomes noise.
 */

export type CredentialSourceKind = "stored-pat" | "editor-session";

export type ResolvedCredential =
  | { ok: true; token: string; source: CredentialSourceKind; scopes: readonly string[] }
  | { ok: false; error: ProviderError };

export interface CredentialResolverDependencies {
  hasStoredToken: () => Promise<boolean>;
  readStoredToken: () => Promise<string | undefined>;
  getSession: GetSessionLike;
  /** The capability already recorded for this target, if any. */
  capability: BillingAuthCapability;
}

export async function resolveCredential(
  dependencies: CredentialResolverDependencies,
  owner: BillingOwner
): Promise<ResolvedCredential> {
  const { hasStoredToken, readStoredToken, getSession, capability } = dependencies;

  if (await hasStoredToken().catch(() => false)) {
    const token = await readStoredToken().catch(() => undefined);
    if (token !== undefined) {
      return { ok: true, token, source: "stored-pat", scopes: [] };
    }
  }

  if (capability.status === "blocked") {
    return {
      ok: false,
      error: {
        code: "missing-token",
        message: `The editor's GitHub session cannot read billing for this owner (${capability.reason}). Run "GitHub Usage Monitor: Diagnose Authorization" for detail, or store a token.`
      }
    };
  }

  // Silent: never raise a sign-in dialog from a background refresh. If no session
  // exists yet the user is told, and connecting stays an explicit action.
  const scopes =
    capability.status === "supported" && capability.grantedScopes.length > 0
      ? capability.grantedScopes
      : firstScopeCandidate(owner);
  const session = await getSession("github", scopes, {
    createIfNone: false,
    silent: true
  }).catch(() => undefined);

  if (session === undefined) {
    return {
      ok: false,
      error: {
        code: "not-connected",
        message:
          'Not connected to GitHub. Run "GitHub Usage Monitor: Log In or Switch Account", or store a token with "GitHub Usage Monitor: Set Token".'
      }
    };
  }
  return {
    ok: true,
    token: session.accessToken,
    source: "editor-session",
    scopes: [...session.scopes]
  };
}

/** Describes the source for a panel or status line, never naming the credential. */
export function describeCredentialSource(source: CredentialSourceKind): string {
  return source === "stored-pat"
    ? "stored token"
    : "the editor's GitHub session";
}
