import type { ProviderFetchError } from "./types";

/**
 * Render a fetch error into a human-readable message. The error is
 * self-describing (it carries its `providerId`), so this single function
 * replaces the old per-fetcher static `getErrorMessage` and lets any consumer
 * (extension host, dashboard webview) resolve a message without holding a
 * provider reference.
 *
 * The Claude branch reproduces the original Anthropic fetcher's messages
 * verbatim so the shipping Claude path is unchanged.
 */
export function describeProviderError(error: ProviderFetchError): string {
  const suffix =
    error.statusCode != null
      ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
      : "";

  if (error.providerId === "codex") {
    return describeCodexError(error, suffix);
  }
  return describeClaudeError(error, suffix);
}

function describeClaudeError(error: ProviderFetchError, suffix: string): string {
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
    case "usage-unavailable":
      return "Usage data is temporarily unavailable.";
  }
}

function describeCodexError(error: ProviderFetchError, suffix: string): string {
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
      return "Codex usage is unavailable right now (the usage endpoint is undocumented and may have changed).";
  }
}
