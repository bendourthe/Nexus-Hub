import type { OrganizationUsage, PersonalUsage } from "../types";

/**
 * Fetch error codes. The personal provider uses the first eight; the
 * organization provider adds the three `org-*` codes.
 */
export type ProviderFetchErrorCode =
  | "no-credentials"
  | "choose-account"
  | "token-invalid"
  | "rate-limited"
  | "network-error"
  | "api-error"
  | "parse-error"
  | "usage-unavailable"
  | "org-not-connected"
  | "org-access-denied"
  | "org-token-rejected";

/** A fetch error, rendered into a human-readable message by `describeProviderError`. */
export interface ProviderFetchError {
  code: ProviderFetchErrorCode;
  statusCode?: number;
  statusText?: string;
}

/** The result of a fetch: either data or a typed error. Never thrown. */
export type ProviderFetchResult<T> =
  | { success: true; data: T }
  | { success: false; error: ProviderFetchError };

/** Why a credential lookup failed, without ever exposing the secret itself. */
export type CredentialFailureReason = "missing" | "choose-account";

/** The credential check result. It never carries the token across the interface. */
export type CredentialResult = { ok: true } | { ok: false; reason: CredentialFailureReason };

/**
 * The personal usage provider. `readCredential` checks for a GitHub session
 * without prompting, and `fetchUsage` returns the mapped figure or a typed
 * error. Implementations MUST NOT throw from `fetchUsage`, and the token never
 * leaves `fetchUsage`.
 */
export interface UsageProvider {
  readonly id: "copilot";
  readonly displayName: string;
  readCredential(): Promise<CredentialResult>;
  fetchUsage(): Promise<ProviderFetchResult<PersonalUsage>>;
}

/** The organization pool provider. Inactive while `copilotUsage.organization` is empty. */
export interface OrganizationProvider {
  isActive(): boolean;
  fetchUsage(nowMs?: number): Promise<ProviderFetchResult<OrganizationUsage>>;
}
