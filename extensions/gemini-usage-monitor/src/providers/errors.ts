import type { ProviderFetchError } from "./types";

/**
 * Render an Antigravity fetch error into a human-readable message, so any
 * consumer (extension host, dashboard webview) can resolve a message without
 * holding a provider reference.
 */
export function describeProviderError(error: ProviderFetchError): string {
  const suffix =
    error.statusCode != null
      ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
      : "";

  switch (error.code) {
    case "not-antigravity":
      return "This monitor reads usage from the Antigravity IDE and only works inside Antigravity.";
    case "server-not-found":
      return "Antigravity's language server is not running yet. Sign in to Antigravity and wait for the agent panel to load, then press Retry.";
    case "server-unreachable":
      return "Could not reach Antigravity's local language server. Press Retry; if it persists, run 'Antigravity: Restart Language Server'.";
    case "rate-limited":
      return "Antigravity's quota service is temporarily unavailable. Showing cached data.";
    case "api-error":
      return `Antigravity's language server returned an error${suffix}. Press Retry; if it persists, sign in to Antigravity again.`;
    case "usage-unavailable":
      return `Antigravity returned no usable quota data${suffix}. Open Settings > Models in Antigravity to check that your plan reports usage.`;
  }
}
