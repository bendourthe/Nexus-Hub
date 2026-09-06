import type { ProviderFetchError } from "./types";

/**
 * Render a fetch error into a human-readable message. The messages reproduce the
 * original Anthropic fetcher's wording verbatim so the shipping Claude path is
 * unchanged, and any consumer (extension host, dashboard webview) can resolve a
 * message without holding a provider reference.
 */
export function describeProviderError(error: ProviderFetchError): string {
  const suffix =
    error.statusCode != null
      ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
      : "";

  switch (error.code) {
    case "no-credentials":
      return "Claude Code credentials not found. Log in to Claude Code first.";
    case "invalid-credentials":
      return "Claude Code credentials are invalid.";
    case "token-expired":
      return "Claude Code session has expired. Re-authenticate in Claude Code.";
    case "token-refresh-failed":
      return "Could not refresh the Claude session token. Re-authenticate by running Claude Code.";
    case "token-invalid":
      return `Your Claude session token was rejected by the API${suffix}. Re-authenticate in Claude Code.`;
    case "rate-limited":
      return "Usage API temporarily unavailable. Showing cached data.";
    case "network-error":
      return "Could not reach the Claude API. Check your internet connection.";
    case "api-error":
      return `The Claude API returned an error${suffix}.`;
    case "parse-error":
      return "Could not parse the API response.";
  }
}
