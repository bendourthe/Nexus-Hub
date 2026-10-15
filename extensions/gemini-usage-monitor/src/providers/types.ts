import type { UsageData } from "../types";

/**
 * The normalized usage model the Antigravity provider returns and the entire UI
 * (status bar, tooltip, dashboard, warning view) renders from. It is an alias
 * of the {@link UsageData} shape so the UI consumes provider output unchanged.
 */
export type UsageModel = UsageData;

/**
 * Fetch error codes returned by the Antigravity usage provider.
 * `not-antigravity`, `server-not-found`, and `server-unreachable` come from local
 * language-server discovery; `usage-unavailable` is the fail-soft catch-all for a
 * response with no usable quota window.
 */
export type ProviderFetchErrorCode =
  | "not-antigravity"
  | "server-not-found"
  | "server-unreachable"
  | "rate-limited"
  | "api-error"
  | "usage-unavailable";

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

/**
 * A usage provider: the data-layer seam between Antigravity's local language
 * server and the shared UI. `fetchUsage` returns a normalized {@link UsageModel}
 * or a typed error. Implementations MUST NOT throw from `fetchUsage`.
 */
export interface UsageProvider {
  readonly id: "antigravity";
  readonly displayName: string;
  fetchUsage(forceRefresh?: boolean): Promise<ProviderFetchResult>;
}
