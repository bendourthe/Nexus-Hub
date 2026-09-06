import type { UsageData } from "../types";

/**
 * The normalized usage model the provider returns and the entire UI
 * (status bar, tooltip, dashboard, warning view) renders from. It is an alias
 * of the existing {@link UsageData} shape so the UI consumes provider output
 * unchanged.
 */
export type UsageModel = UsageData;

/**
 * Fetch error codes returned by the Claude usage provider. These mirror the
 * original Anthropic fetcher's codes verbatim so the Claude path's messages are
 * unchanged.
 */
export type ProviderFetchErrorCode =
  | "no-credentials"
  | "invalid-credentials"
  | "token-expired"
  | "token-refresh-failed"
  | "token-invalid"
  | "rate-limited"
  | "network-error"
  | "api-error"
  | "parse-error";

/** A fetch error, rendered into a human-readable message by {@link describeProviderError}. */
export interface ProviderFetchError {
  code: ProviderFetchErrorCode;
  statusCode?: number;
  statusText?: string;
}

/** The result of a usage fetch: either normalized data or a typed error. Never thrown. */
export type ProviderFetchResult =
  | { success: true; data: UsageModel }
  | { success: false; error: ProviderFetchError };

/** Why a credential lookup failed, without ever exposing the secret itself. */
export type CredentialFailureReason = "missing" | "invalid" | "expired";

/**
 * The outcome of locating and validating a provider's local credential. It
 * deliberately never carries the raw token across the interface boundary - a
 * provider reads the secret privately inside {@link UsageProvider.fetchUsage}.
 */
export type CredentialResult =
  | { ok: true }
  | { ok: false; reason: CredentialFailureReason };

/**
 * A usage provider: the data-layer seam between a vendor's account API and the
 * shared UI. `readCredential` locates and validates the local auth token
 * (secret-safe), and `fetchUsage` returns a normalized {@link UsageModel} or a
 * typed error. Implementations MUST NOT throw from `fetchUsage`.
 */
export interface UsageProvider {
  readonly id: "claude";
  readonly displayName: string;
  readCredential(): CredentialResult;
  fetchUsage(currentModel?: string): Promise<ProviderFetchResult>;
}
