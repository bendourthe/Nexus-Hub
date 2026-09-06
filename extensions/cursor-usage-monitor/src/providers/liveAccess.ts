import type { ProviderResult } from "../types";
import type { CursorCredentialStore } from "./auth";
import { type ConsentGate, consentRequiredError } from "./consent";
import type { CursorSessionAdapter } from "./session";

/**
 * The credential source and the capability rule live here rather than in
 * `extension.ts` so both can be asserted directly. The two invariants they carry -
 * a refusal never reaches the state database, and consent is requested only when
 * it could be acted on - are the phase's security contract, not activation glue.
 */

export type CredentialSource = Pick<CursorCredentialStore, "withCredential">;

export interface LiveAccessDependencies {
  secrets: Pick<CursorCredentialStore, "hasCredential" | "withCredential">;
  consent: Pick<ConsentGate, "isGranted" | "ensure">;
  adapter: Pick<CursorSessionAdapter, "capability" | "withSession">;
}

/**
 * Prefers an explicitly supplied SecretStorage credential, then the consent-gated
 * session. Consent is re-checked on every call rather than captured once, so a
 * revocation takes effect immediately instead of at the next activation.
 */
export function createCredentialSource(
  dependencies: LiveAccessDependencies
): CredentialSource {
  const { secrets, consent, adapter } = dependencies;
  return {
    async withCredential<T>(
      operation: (credential: string) => Promise<ProviderResult<T>>
    ): Promise<ProviderResult<T>> {
      const stored = await secrets.hasCredential();
      if (stored.ok && stored.value) {
        return secrets.withCredential(operation);
      }
      if (!consent.isGranted()) {
        // Returns before the adapter is touched. This ordering is the guarantee
        // that a declined prompt never results in a state-database read.
        return { ok: false, error: consentRequiredError() };
      }
      return adapter.withSession(operation);
    }
  };
}

/**
 * Consent is requested only when acting on it is actually possible. Asking for
 * permission the extension could not use anyway would be a prompt with no payoff.
 */
export async function resolveLiveCapability(
  dependencies: LiveAccessDependencies
): Promise<boolean> {
  const { secrets, consent, adapter } = dependencies;
  const stored = await secrets.hasCredential();
  if (stored.ok && stored.value) {
    // Supplying a credential explicitly is itself the opt-in; no prompt is due.
    return true;
  }
  const capability = await adapter.capability();
  if (!capability.available) {
    return false;
  }
  const status = await consent.ensure();
  return status.state === "granted";
}
