import type { BillingOwner } from "../types";
import { billingEndpoint } from "./scope";
import {
  GITHUB_ACCEPT,
  GITHUB_API_VERSION,
  GITHUB_USER_AGENT
} from "./github";

/**
 * A bounded, one-read probe that answers T022: which credential classes the
 * enhanced billing endpoints actually accept for a given billing target.
 *
 * Two design rules, both load-bearing:
 *
 * 1. **This module never imports `vscode`.** `probeWithToken` takes a token and a
 *    fetch; `probeVsCodeSession` takes a session provider. That keeps the probe
 *    unit-testable without the editor stub and keeps credential acquisition at the
 *    call site.
 * 2. **`toSanitizedRecord` is the only supported way to serialize a result.** The
 *    raw result deliberately never holds the token, the request headers, or a
 *    success body, and `test/auth-probe.test.ts` asserts that the serialized form
 *    cannot carry them. The recording rules in
 *    `docs/v3/v3.15/development/github-billing-auth-probe.md` are enforced by that
 *    test rather than promised by a comment.
 */

/**
 * `gh-oauth` is a GitHub CLI OAuth-app token (`gho_`). It is tracked separately
 * from `vscode-oauth` because OAuth-app authorization and SSO grants are per-app:
 * a result for one app does NOT transfer to another. What it does answer is the
 * app-independent question of whether the endpoint accepts an OAuth token class at
 * all, which is the question the endpoint reference's fine-grained-only token list
 * cannot settle.
 */
export type CredentialKind =
  | "vscode-oauth"
  | "gh-oauth"
  | "classic-pat"
  | "fine-grained-pat";

export interface ProbeHeadersLike {
  get(name: string): string | null;
}

export interface ProbeResponseLike {
  ok: boolean;
  status: number;
  statusText: string;
  headers: ProbeHeadersLike;
  json(): Promise<unknown>;
}

export type ProbeFetchLike = (
  input: string,
  init: { headers: Record<string, string> }
) => Promise<ProbeResponseLike>;

/** Only the two fields a probe may keep from a failure body. */
export interface ProbeErrorDetail {
  message?: string;
  documentationUrl?: string;
}

export interface ProbeRecord {
  checkedAt: string;
  apiVersion: string;
  level: BillingOwner["scope"];
  endpoint: string;
  credentialKind: CredentialKind;
  requestedScopes: readonly string[];
  /**
   * What the editor reported. Kept separately from `grantedOAuthScopes` because
   * `AuthenticationSession.scopes` reflects what the extension REQUESTED, not what
   * GitHub granted, and conflating the two would make a narrowed consent look like
   * a full grant.
   */
  providerReportedScopes: readonly string[];
  status: number;
  grantedOAuthScopes: readonly string[];
  acceptedOAuthScopes: readonly string[];
  acceptedGitHubPermissions: string | null;
  requestId: string | null;
  error: ProbeErrorDetail | null;
}

export interface SessionLike {
  accessToken: string;
  scopes: readonly string[];
}

export type SessionProvider = (
  providerId: string,
  scopes: readonly string[]
) => Promise<SessionLike | undefined>;

/**
 * Enterprise billing usage documentarily rejects fine-grained PATs and GitHub App
 * tokens, so that combination is refused rather than probed. Probing a
 * known-negative would spend a request and risk recording an ambiguous failure as
 * though it were evidence.
 */
export function isProbeAllowed(
  level: BillingOwner["scope"],
  credentialKind: CredentialKind
): boolean {
  return !(level === "enterprise" && credentialKind === "fine-grained-pat");
}

export function billingUsageProbePath(
  owner: BillingOwner,
  now: Date
): string {
  const query = new URLSearchParams({
    year: String(now.getUTCFullYear()),
    month: String(now.getUTCMonth() + 1)
  });
  return `${billingEndpoint(owner, "usage")}?${query.toString()}`;
}

export function splitScopeHeader(value: string | null): string[] {
  return value === null
    ? []
    : value
        .split(",")
        .map((scope) => scope.trim())
        .filter((scope) => scope.length > 0);
}

export interface ProbeOptions {
  owner: BillingOwner;
  token: string;
  credentialKind: CredentialKind;
  requestedScopes?: readonly string[];
  providerReportedScopes?: readonly string[];
  now?: Date;
  fetch?: ProbeFetchLike;
  baseUrl?: string;
}

export async function probeWithToken(
  options: ProbeOptions
): Promise<ProbeRecord> {
  const {
    owner,
    token,
    credentialKind,
    requestedScopes = [],
    providerReportedScopes = [],
    now = new Date(),
    fetch: request = fetch as unknown as ProbeFetchLike,
    baseUrl = "https://api.github.com"
  } = options;

  if (!isProbeAllowed(owner.scope, credentialKind)) {
    throw new Error(
      "Enterprise billing usage documentarily rejects fine-grained PATs; do not probe that combination."
    );
  }

  const endpoint = billingUsageProbePath(owner, now);
  const response = await request(`${baseUrl}${endpoint}`, {
    headers: {
      Accept: GITHUB_ACCEPT,
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": GITHUB_API_VERSION,
      "User-Agent": GITHUB_USER_AGENT
    }
  });

  return {
    checkedAt: now.toISOString(),
    apiVersion: GITHUB_API_VERSION,
    level: owner.scope,
    endpoint,
    credentialKind,
    requestedScopes: [...requestedScopes],
    providerReportedScopes: [...providerReportedScopes],
    status: response.status,
    grantedOAuthScopes: splitScopeHeader(response.headers.get("x-oauth-scopes")),
    acceptedOAuthScopes: splitScopeHeader(
      response.headers.get("x-accepted-oauth-scopes")
    ),
    acceptedGitHubPermissions: response.headers.get(
      "x-accepted-github-permissions"
    ),
    requestId: response.headers.get("x-github-request-id"),
    error: await readSafeError(response)
  };
}

/**
 * Acquires a session through the injected provider and probes with it. The session
 * object is never returned, logged, or serialized, because it carries the token.
 */
export async function probeVsCodeSession(
  getSession: SessionProvider,
  options: Omit<ProbeOptions, "token" | "credentialKind" | "providerReportedScopes"> & {
    requestedScopes: readonly string[];
  }
): Promise<ProbeRecord | null> {
  const session = await getSession("github", options.requestedScopes);
  if (session === undefined) {
    return null;
  }
  return probeWithToken({
    ...options,
    token: session.accessToken,
    credentialKind: "vscode-oauth",
    providerReportedScopes: session.scopes
  });
}

/**
 * The only supported serialization. Rebuilt field by field rather than spread, so
 * a field added to `ProbeRecord` cannot reach a report until it is added here
 * deliberately.
 */
export function toSanitizedRecord(record: ProbeRecord): Record<string, unknown> {
  return {
    checkedAt: record.checkedAt,
    apiVersion: record.apiVersion,
    level: record.level,
    endpoint: record.endpoint,
    credentialKind: record.credentialKind,
    requestedScopes: [...record.requestedScopes],
    providerReportedScopes: [...record.providerReportedScopes],
    status: record.status,
    grantedOAuthScopes: [...record.grantedOAuthScopes],
    acceptedOAuthScopes: [...record.acceptedOAuthScopes],
    acceptedGitHubPermissions: record.acceptedGitHubPermissions,
    requestId: record.requestId,
    errorMessage: record.error?.message ?? null,
    errorDocumentationUrl: record.error?.documentationUrl ?? null
  };
}

/** One row of the probe doc's results table, ready to paste. */
export function toMarkdownRow(record: ProbeRecord): string {
  const cells = [
    record.checkedAt.slice(0, 10),
    record.level,
    record.endpoint.split("?")[0] ?? record.endpoint,
    record.credentialKind,
    joinScopes(record.requestedScopes),
    String(record.status),
    joinScopes(record.grantedOAuthScopes),
    joinScopes(record.acceptedOAuthScopes),
    record.acceptedGitHubPermissions ?? "-",
    record.status === 200 ? "supported for this target" : "see interpretation table"
  ];
  return `| ${cells.join(" | ")} |`;
}

function joinScopes(scopes: readonly string[]): string {
  return scopes.length === 0 ? "-" : scopes.join(" ");
}

/**
 * A success body is billing data and is discarded unread. Only `message` and
 * `documentation_url` are kept from a failure body; anything else GitHub returns is
 * dropped rather than filtered later.
 */
async function readSafeError(
  response: ProbeResponseLike
): Promise<ProbeErrorDetail | null> {
  if (response.ok) {
    return null;
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      message: `GitHub returned ${response.status} ${response.statusText}`.trim()
    };
  }
  if (typeof body !== "object" || body === null || Array.isArray(body)) {
    return { message: `GitHub returned ${response.status}` };
  }
  const record = body as Record<string, unknown>;
  const message =
    typeof record.message === "string" ? record.message : undefined;
  const documentationUrl =
    typeof record.documentation_url === "string"
      ? record.documentation_url
      : undefined;
  return {
    ...(message === undefined ? {} : { message }),
    ...(documentationUrl === undefined ? {} : { documentationUrl })
  };
}
