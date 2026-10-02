import type { ProviderFetchError } from "./types";

/** The message shown when an organization endpoint answers 403 or 404 (plan 2.3). */
export const ORG_ACCESS_MESSAGE =
  "This needs a read-only token from an organization owner or billing manager.";

/**
 * Render a fetch error into a message for the dashboard and notifications. The
 * message is built from the code and HTTP status only, so it can never carry a
 * token, login, or organization name.
 */
export function describeProviderError(error: ProviderFetchError): string {
  const suffix =
    error.statusCode != null
      ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
      : "";

  switch (error.code) {
    case "no-credentials":
      return "No GitHub account is signed in to VS Code. Select Sign in to GitHub to see your Copilot usage.";
    case "choose-account":
      return "Several GitHub accounts are signed in. Select Choose GitHub account to pick the one whose Copilot usage to show.";
    case "token-invalid":
      return `GitHub rejected the VS Code sign-in${suffix}. Select Sign in to GitHub to sign in again.`;
    case "rate-limited":
      return "GitHub is rate-limiting usage requests. Showing cached data until the next refresh.";
    case "network-error":
      return "Could not reach api.github.com. Check your internet connection.";
    case "api-error":
      return `GitHub returned an error${suffix}. Press Retry in a moment.`;
    case "parse-error":
    case "usage-unavailable":
      return `GitHub returned a Copilot usage response this monitor does not recognize${suffix}. Press Retry; if it persists, the undocumented endpoint may have changed.`;
    case "org-not-connected":
      return "The organization is set but no token is stored. Run Copilot Usage: Connect Organization.";
    case "org-access-denied":
      return ORG_ACCESS_MESSAGE;
    case "org-token-rejected":
      return "The organization token was rejected or has expired, so it was removed. Select Reconnect to add a new one.";
  }
}
