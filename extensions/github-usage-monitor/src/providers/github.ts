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
  type CopilotEndpoint
} from "./scope";

export const GITHUB_API_VERSION = "2026-03-10";
export const GITHUB_ACCEPT = "application/vnd.github+json";
export const GITHUB_USER_AGENT = "nexus-hub-github-usage-monitor/0.1.0";
export const DEFAULT_TIMEOUT_MS = 10_000;

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

  private async requestJson(
    path: string,
    token: string,
    year: number,
    month: number,
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
      const query = new URLSearchParams({ year: String(year), month: String(month) });
      const response = await this.request(`${this.baseUrl}${path}?${query.toString()}`, {
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
  return {
    code: "service-error",
    statusCode: response.status,
    message: `GitHub billing returned ${response.status}${statusSuffix}.`
  };
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
  const now = Date.now();
  const retryAt = rate.retryAfterMs !== null
    ? now + rate.retryAfterMs
    : rate.resetAt ?? undefined;
  return {
    code: "rate-limited",
    statusCode,
    ...(retryAt === undefined ? {} : { retryAt }),
    message: "GitHub billing is rate limited. Refresh after the reported retry time."
  };
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
