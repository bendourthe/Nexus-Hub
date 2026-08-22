import type {
  AcceptedAuthorization,
  BillingOwner,
  ProviderError,
  ProviderResult,
  RateMetadata,
  UsageSnapshot
} from "../types";
import { validateTokenSyntax } from "./auth";
import { normalizeUsageResponses } from "./normalizer";
import {
  billingEndpoint,
  copilotEndpointSuffix,
  permissionError,
  requiredPermission,
  type CopilotEndpoint
} from "./scope";

export const GITHUB_API_VERSION = "2026-03-10";
export const GITHUB_ACCEPT = "application/vnd.github+json";
export const GITHUB_USER_AGENT = "nexus-hub-github-usage-monitor/0.4.0";
export const DEFAULT_TIMEOUT_MS = 10_000;
const MAX_TRANSIENT_ATTEMPTS = 3;
const RETRY_BASE_DELAY_MS = 250;
const RETRY_MAX_DELAY_MS = 2_000;

interface HeadersLike {
  get(name: string): string | null;
}

interface ResponseLike {
  ok: boolean;
  status: number;
  statusText: string;
  headers: HeadersLike;
  json(): Promise<unknown>;
}

export type FetchLike = (
  input: string,
  init: { headers: Record<string, string>; signal: AbortSignal }
) => Promise<ResponseLike>;

export interface FetchUsageOptions {
  owner: BillingOwner;
  token: string;
  copilotEndpoint: CopilotEndpoint;
  now?: number;
  signal?: AbortSignal;
}

export class GitHubBillingClient {
  public constructor(
    private readonly request: FetchLike = fetch as unknown as FetchLike,
    private readonly baseUrl = "https://api.github.com",
    private readonly timeoutMs = DEFAULT_TIMEOUT_MS
  ) {}

  public async validateCredential(
    owner: BillingOwner,
    token: string,
    signal?: AbortSignal
  ): Promise<ProviderResult<void>> {
    const syntaxError = validateTokenSyntax(token);
    if (syntaxError !== null) {
      return failure(syntaxError, emptyRate());
    }
    const now = new Date();
    const path = billingEndpoint(owner, copilotEndpointSuffix("ai-credits"));
    const result = await this.requestJson(path, token, now.getUTCFullYear(), now.getUTCMonth() + 1, signal);
    return result.ok
      ? { ok: true, value: undefined, rate: result.rate }
      : result;
  }

  public async fetchUsage(options: FetchUsageOptions): Promise<ProviderResult<UsageSnapshot>> {
    const syntaxError = validateTokenSyntax(options.token);
    if (syntaxError !== null) {
      return failure(syntaxError, emptyRate());
    }
    if (options.owner.scope === "enterprise" && options.copilotEndpoint === "premium-requests") {
      return failure(
        {
          code: "not-found",
          message: "The approved contract does not expose enterprise legacy premium-request usage."
        },
        emptyRate()
      );
    }

    const requestedAt = options.now ?? Date.now();
    const date = new Date(requestedAt);
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth() + 1;
    const copilotPath = billingEndpoint(options.owner, copilotEndpointSuffix(options.copilotEndpoint));
    const actionsPath = billingEndpoint(options.owner, "usage");

    const copilot = await this.requestJson(copilotPath, options.token, year, month, options.signal);
    if (!copilot.ok) {
      return copilot;
    }
    const actions = await this.requestJson(actionsPath, options.token, year, month, options.signal);
    if (!actions.ok) {
      return actions;
    }

    const normalized = normalizeUsageResponses(copilot.value, actions.value, {
      owner: options.owner,
      copilotEndpoint: options.copilotEndpoint,
      requestedAt,
      year,
      month
    });
    const rate = mergeRate(copilot.rate, actions.rate);
    return normalized.ok
      ? { ok: true, value: normalized.value, rate }
      : { ok: false, error: normalized.error, rate };
  }

  /**
   * A plain authenticated GET with no billing-period query.
   *
   * Added in v3.16.3 Phase 2 for the two non-billing lookups an honest percentage
   * needs: `GET /repos/{owner}/{repo}` for visibility, and `GET /user` for the plan
   * name. Both reuse this client's headers, timeout, and abort handling rather than
   * opening a second HTTP path with its own failure modes.
   *
   * Reads only what it is asked for. The repository call is used for a single
   * boolean (`private`); no file content is requested or returned.
   */
  public async getJson(
    path: string,
    token: string,
    signal?: AbortSignal
  ): Promise<{ ok: true; value: unknown } | { ok: false; status: number }> {
    const result = await this.requestJson(path, token, undefined, undefined, signal);
    return result.ok
      ? { ok: true, value: result.value }
      : { ok: false, status: result.error.statusCode ?? 0 };
  }

  private async requestJson(
    path: string,
    token: string,
    year: number | undefined,
    month: number | undefined,
    externalSignal?: AbortSignal
  ): Promise<ProviderResult<unknown>> {
    const controller = new AbortController();
    let timedOut = false;
    const abortFromCaller = (): void => controller.abort();
    externalSignal?.addEventListener("abort", abortFromCaller, { once: true });
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.timeoutMs);

    try {
      const query =
        year === undefined || month === undefined
          ? ""
          : `?${new URLSearchParams({ year: String(year), month: String(month) }).toString()}`;
      const startedAt = Date.now();
      for (let attempt = 1; attempt <= MAX_TRANSIENT_ATTEMPTS; attempt += 1) {
        const response = await this.request(`${this.baseUrl}${path}${query}`, {
          headers: {
            Accept: GITHUB_ACCEPT,
            Authorization: `Bearer ${token}`,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": GITHUB_USER_AGENT
          },
          signal: controller.signal
        });
        const rate = readRateMetadata(response.headers);
        if (!response.ok) {
          if (isTransientServerError(response.status) && attempt < MAX_TRANSIENT_ATTEMPTS) {
            const delayMs = transientRetryDelayMs(attempt, rate);
            const remainingMs = this.timeoutMs - (Date.now() - startedAt);
            if (delayMs < remainingMs) {
              await waitForRetry(delayMs, controller.signal);
              continue;
            }
          }
          return failure(
            withAuthorizationDiagnosis(
              classifyHttpError(response, path, rate),
              response.headers
            ),
            rate
          );
        }
        try {
          return { ok: true, value: await response.json(), rate };
        } catch {
          return failure(
            { code: "schema-mismatch", message: "GitHub returned a non-JSON billing response." },
            rate
          );
        }
      }
      throw new Error("GitHub billing retry loop ended unexpectedly.");
    } catch (error: unknown) {
      if (controller.signal.aborted) {
        return failure(
          timedOut
            ? { code: "timeout", message: `GitHub billing request exceeded ${this.timeoutMs} ms.` }
            : { code: "cancelled", message: "GitHub billing request was cancelled." },
          emptyRate()
        );
      }
      return failure(
        {
          code: "network-error",
          message: error instanceof Error ? `Could not reach GitHub billing: ${error.message}` : "Could not reach GitHub billing."
        },
        emptyRate()
      );
    } finally {
      clearTimeout(timer);
      externalSignal?.removeEventListener("abort", abortFromCaller);
    }
  }
}

function isTransientServerError(status: number): boolean {
  return status === 500 || status === 502 || status === 503 || status === 504;
}

function transientRetryDelayMs(attempt: number, rate: RateMetadata): number {
  if (rate.retryAfterMs !== null) return rate.retryAfterMs;
  const ceiling = Math.min(RETRY_MAX_DELAY_MS, RETRY_BASE_DELAY_MS * (2 ** (attempt - 1)));
  return Math.max(1, Math.floor(Math.random() * ceiling));
}

function waitForRetry(delayMs: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new Error("aborted"));
      return;
    }
    const onAbort = (): void => {
      clearTimeout(timer);
      reject(new Error("aborted"));
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }, delayMs);
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

function classifyHttpError(
  response: Pick<ResponseLike, "status" | "statusText" | "headers">,
  path: string,
  rate: RateMetadata
): ProviderError {
  const statusSuffix = response.statusText ? ` ${response.statusText}` : "";
  if (response.status === 401) {
    return {
      code: "invalid-token",
      statusCode: 401,
      message: "GitHub rejected the stored token. Set or rotate the token in SecretStorage."
    };
  }
  if (response.status === 403) {
    if (rate.remaining === 0 || rate.retryAfterMs !== null) {
      return rateLimitError(response.status, rate);
    }
    const owner = ownerFromPath(path);
    const error = owner === null
      ? { code: "invalid-scope" as const, message: "GitHub denied the configured billing scope." }
      : permissionError(owner);
    return { ...error, statusCode: 403 };
  }
  if (response.status === 404) {
    return /\/settings\/billing\/usage$/u.test(path)
      ? {
          code: "enhanced-billing-unavailable",
          statusCode: 404,
          message: "Detailed Actions usage is unavailable for this owner or enhanced billing is not enabled."
        }
      : {
          code: "not-found",
          statusCode: 404,
          message: "GitHub could not find the configured billing owner or endpoint. Verify the scope and authorization."
        };
  }
  if (response.status === 429) {
    return rateLimitError(response.status, rate);
  }
  const retryAt = isTransientServerError(response.status) ? retryAtFromRate(rate) : undefined;
  return {
    code: "service-error",
    statusCode: response.status,
    ...(retryAt === undefined ? {} : { retryAt }),
    message: `GitHub billing returned ${response.status}${statusSuffix}.`
  };
}

/** What `GET /user/memberships/orgs/{org}` returned, or the status that replaced it. */
export type MembershipLookup =
  | { ok: true; value: unknown }
  | { ok: false; status: number };

/** The path whose answer separates the two causes of an organization billing 404. */
export function membershipPath(owner: BillingOwner): string {
  return `/user/memberships/orgs/${encodeURIComponent(owner.name)}`;
}

/**
 * Separates the two very different failures GitHub reports identically.
 *
 * `GET /organizations/{org}/settings/billing/...` returns 404 both when the caller
 * lacks the owner or billing-manager role AND when the organization is not on the
 * enhanced billing platform - and the scope headers cannot tell them apart, because
 * in the observed case (2026-08-10, SupiraMedical) the credential already carried an
 * accepted scope. The resulting "could not find the owner or endpoint. Verify the
 * scope" told the user to check the one thing that was already correct.
 *
 * Membership role is the discriminator: GitHub reports `admin` for an organization
 * owner, `billing_manager` for a billing manager, and `member` for everyone else. A
 * role that CAN read billing means the 404 is about the platform; a role that cannot
 * means the 404 is about permission. Pure so both branches are unit-testable without
 * a network.
 */
export function explainOrganizationNotFound(
  owner: BillingOwner,
  lookup: MembershipLookup,
  fallback: ProviderError
): ProviderError {
  if (!lookup.ok) {
    // 403 here is GitHub refusing to describe the membership at all, which is what
    // an OAuth-app restriction or an unauthorized SAML session looks like.
    if (lookup.status === 403) {
      return {
        ...fallback,
        message: `'${owner.name}' did not let this credential read your membership, which usually means the organization restricts OAuth apps or requires SAML single sign-on authorization. Approve the editor's GitHub app for '${owner.name}', or authorize the session for its SSO, then refresh.`
      };
    }
    return fallback;
  }

  // `typeof null === "object"`, so the null guard is explicit rather than implied.
  const record =
    typeof lookup.value === "object" && lookup.value !== null
      ? (lookup.value as { role?: unknown; state?: unknown })
      : {};
  const role = typeof record.role === "string" ? record.role.toLowerCase() : "";
  const state = typeof record.state === "string" ? record.state.toLowerCase() : "";

  if (state === "pending") {
    return {
      ...fallback,
      message: `Your membership of '${owner.name}' is still a pending invitation, so its billing is not readable yet. Accept the invitation, then refresh.`
    };
  }
  if (role === "admin" || role === "billing_manager") {
    return {
      ...fallback,
      code: "enhanced-billing-unavailable",
      message: `You hold the ${role === "admin" ? "organization owner" : "billing manager"} role on '${owner.name}', so this is not a permission problem: GitHub returned no billing endpoint for it. That organization is not on GitHub's enhanced billing platform, which is the only platform exposing per-product usage through the API. Check its billing page for the authoritative figures.`
    };
  }
  if (role === "member") {
    return {
      ...fallback,
      // The existing code for exactly this state, already produced by `permissionError`
      // on the 403 path. Reused rather than adding a synonym to the error union.
      code: "missing-organization-administration-read",
      requiredPermission: requiredPermission(owner),
      message: `You are a member of '${owner.name}' but not an organization owner or billing manager, and only those roles can read organization billing. Ask an owner for the billing manager role, or point this monitor at an owner you can bill for.`
    };
  }
  return fallback;
}

/**
 * Attaches GitHub's own account of what the operation would have accepted, and
 * appends it to the message when it is actionable.
 *
 * Without this a permission failure reads only "the token needs X", which is the
 * extension's guess from the configured scope. `X-Accepted-OAuth-Scopes` is
 * GitHub's answer for the credential actually presented, and it is the documented
 * way to discover what an operation accepts. A user who granted `read:org` where
 * `admin:org` was required now gets told exactly that.
 */
export function withAuthorizationDiagnosis(
  error: ProviderError,
  headers: HeadersLike
): ProviderError {
  const accepted = readAcceptedAuthorization(headers);
  const requestId = headers.get("x-github-request-id");
  if (accepted === null && requestId === null) {
    return error;
  }

  const suffix =
    accepted === null || accepted.acceptedOAuthScopes.length === 0
      ? ""
      : ` GitHub reports this operation accepts OAuth scopes: ${accepted.acceptedOAuthScopes.join(", ")}; the credential presented ${
          accepted.grantedOAuthScopes.length === 0
            ? "no OAuth scopes"
            : accepted.grantedOAuthScopes.join(", ")
        }.`;

  return {
    ...error,
    message: `${error.message}${suffix}`,
    ...(accepted === null ? {} : { accepted }),
    ...(requestId === null ? {} : { requestId })
  };
}

function readAcceptedAuthorization(
  headers: HeadersLike
): AcceptedAuthorization | null {
  const acceptedOAuth = headers.get("x-accepted-oauth-scopes");
  const grantedOAuth = headers.get("x-oauth-scopes");
  const acceptedPermissions = headers.get("x-accepted-github-permissions");
  if (
    acceptedOAuth === null &&
    grantedOAuth === null &&
    acceptedPermissions === null
  ) {
    return null;
  }
  return {
    acceptedOAuthScopes: splitHeaderList(acceptedOAuth),
    grantedOAuthScopes: splitHeaderList(grantedOAuth),
    acceptedGitHubPermissions: acceptedPermissions
  };
}

function splitHeaderList(value: string | null): string[] {
  return value === null
    ? []
    : value
        .split(",")
        .map((entry) => entry.trim())
        .filter((entry) => entry.length > 0);
}

function readRateMetadata(headers: HeadersLike): RateMetadata {
  const remaining = parseFinite(headers.get("x-ratelimit-remaining"));
  const resetSeconds = parseFinite(headers.get("x-ratelimit-reset"));
  const retrySeconds = parseFinite(headers.get("retry-after"));
  return {
    remaining,
    resetAt: resetSeconds === null ? null : resetSeconds * 1000,
    retryAfterMs: retrySeconds === null ? null : retrySeconds * 1000
  };
}

function rateLimitError(statusCode: number, rate: RateMetadata): ProviderError {
  const retryAt = retryAtFromRate(rate);
  return {
    code: "rate-limited",
    statusCode,
    ...(retryAt === undefined ? {} : { retryAt }),
    message: "GitHub billing is rate limited. Refresh after the reported retry time."
  };
}

function retryAtFromRate(rate: RateMetadata): number | undefined {
  return rate.retryAfterMs !== null
    ? Date.now() + rate.retryAfterMs
    : rate.resetAt ?? undefined;
}

function ownerFromPath(path: string): BillingOwner | null {
  const match = /^\/(users|organizations|enterprises)\/([^/]+)\/settings\/billing\//u.exec(path);
  if (match === null || match[1] === undefined || match[2] === undefined) {
    return null;
  }
  const scopes = {
    users: "user",
    organizations: "organization",
    enterprises: "enterprise"
  } as const;
  const scope = scopes[match[1] as keyof typeof scopes];
  return { scope, name: decodeURIComponent(match[2]) } as BillingOwner;
}

function parseFinite(value: string | null): number | null {
  if (value === null || value.trim() === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mergeRate(first: RateMetadata, second: RateMetadata): RateMetadata {
  return {
    remaining: minNullable(first.remaining, second.remaining),
    resetAt: maxNullable(first.resetAt, second.resetAt),
    retryAfterMs: maxNullable(first.retryAfterMs, second.retryAfterMs)
  };
}

function minNullable(first: number | null, second: number | null): number | null {
  if (first === null) {
    return second;
  }
  if (second === null) {
    return first;
  }
  return Math.min(first, second);
}

function maxNullable(first: number | null, second: number | null): number | null {
  if (first === null) {
    return second;
  }
  if (second === null) {
    return first;
  }
  return Math.max(first, second);
}

function emptyRate(): RateMetadata {
  return { remaining: null, resetAt: null, retryAfterMs: null };
}

function failure<T>(error: ProviderError, rate: RateMetadata): ProviderResult<T> {
  return { ok: false, error, rate };
}
