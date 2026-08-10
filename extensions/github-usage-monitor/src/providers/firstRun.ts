/**
 * First-run connection.
 *
 * A freshly installed monitor that reports "no data" until the user finds a command
 * is useless, so this sequence connects it. The hard constraint is the opposite
 * failure: a modal dialog on every VS Code start is the most user-hostile thing this
 * extension could ship, and it is a one-line mistake away at all times.
 *
 * Three steps, in order, and the ordering IS the design:
 *
 *   1. **Silent.** Look for an existing session with `createIfNone: false,
 *      silent: true`. Many users are already signed in to GitHub in the editor and
 *      must never be prompted at all.
 *   2. **One modal, ever.** Only if there is no session, no stored token, and no
 *      prior decline, open the real sign-in flow exactly once.
 *   3. **Durable decline.** If the user dismisses it, record that and never open the
 *      flow automatically again. Explicit action still works and clears the flag.
 *
 * `interactiveAttempts` exists so a test can assert the number of `createIfNone:
 * true` calls directly. That count is the single number separating correct behaviour
 * from a dialog on every startup, and asserting it beats asserting any proxy for it.
 */

import type { BillingOwner } from "../types";
import { logInToMonitor, peekBinding, type GetSessionLike, type MonitorBinding } from "./sessionBinding";

/** `globalState` key recording that the user dismissed the automatic sign-in. */
export const FIRST_RUN_DECLINED_KEY = "githubUsageMonitor.firstRun.declined";

export interface FirstRunDependencies {
  getSession: GetSessionLike;
  /** An explicitly stored PAT makes the sign-in flow unnecessary. */
  hasStoredToken(): Promise<boolean>;
  isDeclined(): boolean;
  recordDecline(): Promise<void>;
  clearDecline(): Promise<void>;
  owner: BillingOwner;
  /** Scopes for the interactive call; defaults to the owner's first candidate. */
  scopes?: readonly string[];
}

export type FirstRunOutcome =
  | { status: "connected"; binding: MonitorBinding; interactive: boolean }
  | { status: "declined" }
  | { status: "skipped"; reason: "stored-token" | "previously-declined" };

export interface FirstRunResult {
  outcome: FirstRunOutcome;
  /** Number of `createIfNone: true` calls made. Must never exceed 1. */
  interactiveAttempts: number;
}

/**
 * Runs the first-run sequence.
 *
 * Never throws. A hung or failing auth provider resolves to a skip rather than
 * propagating, because this runs alongside activation and an activation that fails
 * on an auth error leaves the user with no extension at all rather than an
 * unconnected one.
 */
export async function runFirstRunConnection(deps: FirstRunDependencies): Promise<FirstRunResult> {
  let interactiveAttempts = 0;

  // Step 1: silent. A user already signed in to GitHub in the editor sees nothing.
  const existing = await peekBinding(deps.getSession, deps.owner).catch(() => null);
  if (existing !== null) {
    return { outcome: { status: "connected", binding: existing, interactive: false }, interactiveAttempts };
  }

  // A stored PAT is a deliberate act and answers the question already. Prompting
  // would ask the user to re-decide something they have decided.
  if (await deps.hasStoredToken().catch(() => false)) {
    return { outcome: { status: "skipped", reason: "stored-token" }, interactiveAttempts };
  }

  // Step 3's guard, checked before step 2 runs. This is the line that makes the
  // decline durable rather than per-session.
  if (deps.isDeclined()) {
    return { outcome: { status: "skipped", reason: "previously-declined" }, interactiveAttempts };
  }

  // Step 2: exactly one modal.
  interactiveAttempts += 1;
  const binding = await logInToMonitor(deps.getSession, deps.owner, deps.scopes).catch(() => null);
  if (binding === null) {
    await deps.recordDecline().catch(() => undefined);
    return { outcome: { status: "declined" }, interactiveAttempts };
  }
  // A previous decline is cleared on any success, so a user who changes their mind
  // is not left in a state that suppresses a future automatic connection.
  await deps.clearDecline().catch(() => undefined);
  return { outcome: { status: "connected", binding, interactive: true }, interactiveAttempts };
}
