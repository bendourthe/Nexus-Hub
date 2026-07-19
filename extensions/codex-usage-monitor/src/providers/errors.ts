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
      return "Codex credentials not found. Sign in to the Codex app first.";
    case "invalid-credentials":
      return "Codex credentials could not be read. Sign in to the Codex app again.";
    case "token-expired":
      return "Your Codex session has expired. Sign in to the Codex app again.";
    case "token-refresh-failed":
      return "Could not refresh your Codex session. Sign in to the Codex app again.";
    case "token-invalid":
      return `Your Codex session token was rejected${suffix}. Sign in to the Codex app again.`;
    case "rate-limited":
      return "Codex usage endpoint is temporarily unavailable. Showing cached data.";
    case "network-error":
      return "Could not reach the Codex usage endpoint. Check your internet connection.";
    case "api-error":
      return `The Codex usage endpoint returned an error${suffix}.`;
    case "parse-error":
    case "usage-unavailable":
      return "Automated Codex usage isn't available (the ChatGPT usage endpoint is undocumented and may have changed). Open the usage page to read your limits, then use 'Codex Usage: Enter Usage Manually' to enter them.";
  }
}
