import type { ProviderFetchError } from "./types";

/**
 * Render a Codex fetch error into a human-readable message, so any consumer
 * (extension host, dashboard webview) can resolve a message without holding a
 * provider reference.
 */
export function describeProviderError(error: ProviderFetchError): string {
  const suffix =
    error.statusCode != null
      ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
      : "";

  switch (error.code) {
    case "no-credentials":
      return "Codex credentials not found (~/.codex/auth.json). Run 'codex' in a terminal to sign in.";
    case "invalid-credentials":
      return "Codex credentials at ~/.codex/auth.json could not be read. Run 'codex' to sign in again.";
    case "token-expired":
      return "Your Codex sign-in has expired. Run 'codex' in a terminal to sign in again.";
    case "token-refresh-failed":
      return "Could not refresh your Codex sign-in. Run 'codex' in a terminal to sign in again.";
    case "token-invalid":
      return `Your Codex token was rejected${suffix}. Run 'codex' in a terminal to sign in again.`;
    case "rate-limited":
      return "Codex usage endpoint is temporarily unavailable. Showing cached data.";
    case "network-error":
      return "Could not reach the Codex usage endpoint. Check your internet connection.";
    case "api-error":
      return `The Codex usage endpoint returned an error${suffix}.`;
    case "parse-error":
    case "usage-unavailable":
      return `The Codex usage endpoint returned an unexpected response${suffix}. Press Retry; if it persists, run 'codex' in a terminal to refresh your sign-in.`;
  }
}
