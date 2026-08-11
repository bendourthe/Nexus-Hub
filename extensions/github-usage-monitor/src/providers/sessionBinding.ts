import type { BillingOwner } from "../types";
import { firstScopeCandidate, sessionFingerprint } from "./capability";

/**
 * Binding between this extension and a GitHub identity.
 *
 * The design rule that matters here is what this module is NOT given. Logging out
 * of the monitor must never sign the user out of VS Code's GitHub session, because
 * that session is shared with Copilot and with every other extension. Rather than
 * documenting that as a caution, the dependency type below simply has no
 * revoke/sign-out member: `logOutOfMonitor` structurally cannot end a session, and
 * a test asserts the injected surface stays that narrow.
 */

/** What a session exposes to this extension. Read-only by construction. */
export interface GitHubSessionLike {
  accessToken: string;
  scopes: readonly string[];
  account?: { label?: string };
}

export interface GetSessionOptions {
  createIfNone?: boolean;
  silent?: boolean;
  clearSessionPreference?: boolean;
  /**
   * The account to get a session FOR.
   *
   * Without it a scope list is all that identifies the request, and a scope list is a
   * permission grant rather than an identity - so an editor with two GitHub accounts
   * signed in answers with either one. See the pinning comment in `extension.ts`.
   */
  account?: { readonly id: string; readonly label: string };
}

/**
 * The ONLY session capability injected. Note the absence of any sign-out, revoke,
 * or delete member: that omission is the guarantee.
 */
export type GetSessionLike = (
  providerId: string,
  scopes: readonly string[],
  options: GetSessionOptions
) => Promise<GitHubSessionLike | undefined>;

export interface MonitorBinding {
  accountLabel: string | null;
  scopes: readonly string[];
  fingerprint: string;
}

export function bindingFromSession(session: GitHubSessionLike): MonitorBinding {
  const accountLabel = session.account?.label ?? null;
  return {
    accountLabel,
    scopes: [...session.scopes],
    fingerprint: sessionFingerprint(accountLabel ?? undefined, session.scopes)
  };
}

/**
 * Looks for an existing session WITHOUT prompting. Activation must never raise a
 * consent dialog on its own: the user opens an editor, not an auth flow.
 */
export async function peekBinding(
  getSession: GetSessionLike,
  owner: BillingOwner
): Promise<MonitorBinding | null> {
  const session = await getSession("github", firstScopeCandidate(owner), {
    createIfNone: false,
    silent: true
  });
  return session === undefined ? null : bindingFromSession(session);
}

/**
 * Interactive sign-in that reaches GitHub's account picker.
 *
 * `clearSessionPreference` is what makes the picker appear rather than silently
 * reusing the previously chosen account, which is the entire point: the billing
 * account may deliberately differ from the Copilot account.
 */
export async function logInToMonitor(
  getSession: GetSessionLike,
  owner: BillingOwner,
  scopes: readonly string[] = firstScopeCandidate(owner)
): Promise<MonitorBinding | null> {
  const session = await getSession("github", scopes, {
    createIfNone: true,
    clearSessionPreference: true
  });
  return session === undefined ? null : bindingFromSession(session);
}

/** Everything log-out is permitted to clear. All of it belongs to this extension. */
export interface MonitorOwnedState {
  clearToken(): Promise<void>;
  clearCapabilities(): Promise<void>;
  clearSessionPreference(): Promise<void>;
}

export interface LogOutResult {
  clearedToken: boolean;
  clearedCapabilities: boolean;
  clearedPreference: boolean;
}

/**
 * Clears only this extension's binding.
 *
 * Deliberately takes `MonitorOwnedState` and NOT a session provider, so there is
 * no reachable path from here to VS Code's session. Copilot's sign-in, and every
 * other extension's, is unaffected because nothing here can touch it.
 *
 * Each step is attempted independently: a failure to clear one piece must not
 * leave the others behind, since a partial log-out that kept the token would be
 * worse than a loud failure.
 */
export async function logOutOfMonitor(
  owned: MonitorOwnedState
): Promise<LogOutResult> {
  const result: LogOutResult = {
    clearedToken: false,
    clearedCapabilities: false,
    clearedPreference: false
  };
  try {
    await owned.clearToken();
    result.clearedToken = true;
  } catch {
    // Reported, not thrown: the remaining steps still run.
  }
  try {
    await owned.clearCapabilities();
    result.clearedCapabilities = true;
  } catch {
    // As above.
  }
  try {
    await owned.clearSessionPreference();
    result.clearedPreference = true;
  } catch {
    // As above.
  }
  return result;
}

export function isCompleteLogOut(result: LogOutResult): boolean {
  return (
    result.clearedToken && result.clearedCapabilities && result.clearedPreference
  );
}

/**
 * How the bound identity is shown. Always names the account, because the whole
 * point is that it may differ from the Copilot account, and "signed in" without a
 * name is what leaves a user reporting the wrong account's numbers.
 */
export function describeBinding(binding: MonitorBinding | null): string {
  if (binding === null) {
    return "Not connected. This monitor uses its own GitHub binding, which may differ from the account Copilot uses.";
  }
  const account = binding.accountLabel ?? "an unnamed account";
  const scopes =
    binding.scopes.length === 0 ? "no scopes" : binding.scopes.join(", ");
  return `Bound to ${account} (requested ${scopes}). This is independent of the account Copilot uses.`;
}
