import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { execFileSync } from "child_process";
import { ScopedUsageMetric, UsageData, UsageMetric } from "../types";
import { formatResetTime } from "../usageStore";
import {
  UsageProvider,
  ProviderFetchError,
  ProviderFetchErrorCode,
  ProviderFetchResult,
  CredentialResult,
} from "./types";

/* ------------------------------------------------------------------ */
/*  Anthropic account API shapes (Claude-specific; not part of the    */
/*  normalized model)                                                  */
/* ------------------------------------------------------------------ */

/** Shape returned by https://api.anthropic.com/api/oauth/usage */
interface ApiUsageLimit {
  utilization: number;
  resets_at: string;
}

interface ApiExtraUsage {
  is_enabled: boolean;
  monthly_limit: number;
  used_credits: number;
  utilization: number | null;
}

/**
 * One entry of the self-describing `limits` array the usage endpoint returns
 * alongside the older per-window fields. This is the only stable way to read a
 * model-scoped weekly limit: the flat sibling keys that carry the same numbers
 * are rotating internal codenames (`nimbus_quill`, `tangelo`, `juniper_tide`,
 * ...), so binding to one of those would break the moment it is renamed.
 */
interface ApiLimitEntry {
  /** "session", "weekly_all", or "weekly_scoped". Unknown kinds are ignored. */
  kind: string;
  group?: string;
  percent: number;
  resets_at: string | null;
  scope?: {
    model?: { id: string | null; display_name: string | null } | null;
  } | null;
}

/**
 * Every field is optional because the endpoint is undocumented and has already
 * gained and dropped keys between Claude Code releases; each reader below
 * tolerates an absent value rather than assuming the shape.
 */
export interface ApiUsageResponse {
  five_hour?: ApiUsageLimit | null;
  seven_day?: ApiUsageLimit | null;
  seven_day_oauth_apps?: ApiUsageLimit | null;
  seven_day_opus?: ApiUsageLimit | null;
  seven_day_sonnet?: ApiUsageLimit | null;
  seven_day_cowork?: ApiUsageLimit | null;
  iguana_necktie?: unknown;
  extra_usage?: ApiExtraUsage | null;
  /** Absent on older responses; the flat fields above remain the fallback. */
  limits?: ApiLimitEntry[] | null;
}

interface OAuthCredentials {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  scopes: string[];
  subscriptionType: string | null;
  rateLimitTier: string | null;
}

interface CredentialsFile {
  claudeAiOauth?: OAuthCredentials;
  organizationUuid?: string;
}

const CREDENTIALS_PATH = path.join(os.homedir(), ".claude", ".credentials.json");
// On macOS, Claude Code stores its OAuth credentials in the login Keychain as a
// generic password, NOT in ~/.claude/.credentials.json. Reading the file alone
// therefore reports "credentials not found" on every Mac. The service name has
// been "Claude Code-credentials" across Claude Code releases; we try the bare
// "Claude Code" too as a defensive fallback in case a build differs.
const KEYCHAIN_SERVICES = ["Claude Code-credentials", "Claude Code"];
const IS_MACOS = process.platform === "darwin";
const USAGE_API_URL = "https://api.anthropic.com/api/oauth/usage";
const ANTHROPIC_BETA_HEADER = "oauth-2025-04-20";
const TOKEN_REFRESH_URL = "https://console.anthropic.com/v1/oauth/token";
const CLAUDE_CODE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e";

// Prevents concurrent token refresh attempts (refresh tokens are one-time use)
let tokenRefreshInProgress = false;
// Tracks when we last refreshed the token to prevent runaway refresh loops
let lastTokenRefreshAt = 0;
const TOKEN_REFRESH_COOLDOWN_MS = 30 * 60 * 1_000; // 30 minutes

const SERVER_ERROR_CODES = new Set([500, 502, 503, 504]);
const RETRY_DELAYS_MS = [2_000, 5_000];

/**
 * The Claude usage provider: reads the Claude Code OAuth token (file on
 * Linux/Windows, login Keychain on macOS), refreshes it when expired, fetches
 * account usage from the Anthropic OAuth usage endpoint, and maps it onto the
 * normalized {@link UsageData} model. This is the original `UsageFetcher` logic,
 * unchanged in behavior, now expressed as a {@link UsageProvider}.
 */
export class ClaudeUsageProvider implements UsageProvider {
  readonly id = "claude" as const;
  readonly displayName = "Claude";

  // Tracks where the active credentials came from so a refreshed token is
  // written back to the same store (file on Linux/Windows, Keychain on macOS).
  private credentialSource: "file" | "keychain" = "file";
  // The Keychain service name that actually held the credentials, so write-back
  // updates the same item. Defaults to the canonical name.
  private keychainService: string = KEYCHAIN_SERVICES[0];

  /** Locate and validate the Claude credential without exposing the token. */
  readCredential(): CredentialResult {
    const credentials = this.readCredentials();
    if (!credentials) {
      return { ok: false, reason: "missing" };
    }
    if (this.isTokenExpired(credentials)) {
      return { ok: false, reason: "expired" };
    }
    return { ok: true };
  }

  private fail(code: ProviderFetchErrorCode, extra?: Partial<ProviderFetchError>): ProviderFetchResult {
    return { success: false, error: { code, ...extra } };
  }

  private readCredentials(): OAuthCredentials | null {
    // 1. The credentials file (Linux/Windows, and any macOS setup that still
    //    uses a file). Preferred when present so behavior is unchanged there.
    const fromFile = this.readCredentialsFromFile();
    if (fromFile) {
      this.credentialSource = "file";
      return fromFile;
    }
    // 2. macOS Keychain fallback. This is the default location Claude Code uses
    //    on macOS, so without this the extension can never find credentials there.
    if (IS_MACOS) {
      const fromKeychain = this.readCredentialsFromKeychain();
      if (fromKeychain) {
        this.credentialSource = "keychain";
        return fromKeychain;
      }
    }
    return null;
  }

  private parseCredentials(raw: string): OAuthCredentials | null {
    try {
      const parsed: CredentialsFile = JSON.parse(raw);
      if (!parsed.claudeAiOauth?.accessToken) {
        return null;
      }
      return parsed.claudeAiOauth;
    } catch {
      return null;
    }
  }

  private readCredentialsFromFile(): OAuthCredentials | null {
    try {
      if (!fs.existsSync(CREDENTIALS_PATH)) {
        return null;
      }
      return this.parseCredentials(fs.readFileSync(CREDENTIALS_PATH, "utf-8"));
    } catch {
      return null;
    }
  }

  private readCredentialsFromKeychain(): OAuthCredentials | null {
    for (const service of KEYCHAIN_SERVICES) {
      const raw = this.readKeychainItem(service);
      if (!raw) {
        continue;
      }
      const parsed = this.parseCredentials(raw);
      if (parsed) {
        this.keychainService = service;
        return parsed;
      }
    }
    return null;
  }

  private readKeychainItem(service: string): string | null {
    try {
      // .toString() before .trim() keeps this valid regardless of which
      // execFileSync overload the resolved @types/node selects (string vs Buffer).
      const raw = execFileSync(
        "security",
        ["find-generic-password", "-s", service, "-w"],
        { encoding: "utf8", timeout: 5_000 }
      )
        .toString()
        .trim();
      return raw || null;
    } catch {
      // No matching Keychain item, or the `security` tool is unavailable.
      return null;
    }
  }

  private isTokenExpired(credentials: OAuthCredentials): boolean {
    return Date.now() >= credentials.expiresAt;
  }

  async fetchUsage(currentModel?: string): Promise<ProviderFetchResult> {
    let credentials = this.readCredentials();
    if (!credentials) {
      return this.fail("no-credentials");
    }

    if (this.isTokenExpired(credentials)) {
      if (tokenRefreshInProgress) {
        return this.fail("token-expired");
      }
      tokenRefreshInProgress = true;
      try {
        const fresh = await this.refreshAccessToken(credentials);
        this.saveCredentials(fresh);
        lastTokenRefreshAt = Date.now();
        credentials = fresh;
      } catch {
        return this.fail("token-refresh-failed");
      } finally {
        tokenRefreshInProgress = false;
      }
    }

    const headers = {
      Authorization: `Bearer ${credentials.accessToken}`,
      "anthropic-beta": ANTHROPIC_BETA_HEADER,
    };

    let response: Response;
    try {
      response = await this.fetchWithRetry(USAGE_API_URL, headers);
    } catch {
      return this.fail("network-error");
    }

    if (!response.ok) {
      if (response.status === 401) {
        return this.fail("token-invalid", {
          statusCode: response.status,
          statusText: response.statusText,
        });
      }
      if (response.status === 429) {
        // Attempt a token refresh to reset the per-token rate limit allocation
        const canRefresh = !tokenRefreshInProgress &&
          Date.now() - lastTokenRefreshAt > TOKEN_REFRESH_COOLDOWN_MS;

        if (canRefresh) {
          tokenRefreshInProgress = true;
          try {
            const fresh = await this.refreshAccessToken(credentials);
            this.saveCredentials(fresh);
            lastTokenRefreshAt = Date.now();
            const newHeaders = {
              Authorization: `Bearer ${fresh.accessToken}`,
              "anthropic-beta": ANTHROPIC_BETA_HEADER,
            };
            let retryResponse: Response;
            try {
              retryResponse = await this.fetchWithRetry(USAGE_API_URL, newHeaders);
            } catch {
              return this.fail("network-error");
            }
            if (retryResponse.ok) {
              let apiData: ApiUsageResponse;
              try {
                apiData = (await retryResponse.json()) as ApiUsageResponse;
              } catch {
                return this.fail("parse-error");
              }
              return { success: true, data: this.mapApiResponse(apiData, currentModel ?? "claude-opus-4-6[1m]") };
            }
            // Retry also failed - fall through to rate-limited
          } catch {
            // Token refresh failed - fall through to rate-limited
          } finally {
            tokenRefreshInProgress = false;
          }
        }

        return this.fail("rate-limited", {
          statusCode: response.status,
          statusText: response.statusText,
        });
      }
      return this.fail("api-error", {
        statusCode: response.status,
        statusText: response.statusText,
      });
    }

    let apiData: ApiUsageResponse;
    try {
      apiData = (await response.json()) as ApiUsageResponse;
    } catch {
      return this.fail("parse-error");
    }

    return {
      success: true,
      data: this.mapApiResponse(apiData, currentModel ?? "claude-opus-4-6[1m]"),
    };
  }

  private async fetchWithRetry(
    url: string,
    headers: Record<string, string>
  ): Promise<Response> {
    let lastResponse: Response | undefined;

    for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30_000);
      let response: Response;
      try {
        response = await fetch(url, { method: "GET", headers, signal: controller.signal });
      } finally {
        clearTimeout(timeoutId);
      }

      if (response.ok) {
        return response;
      }

      const isServerError = SERVER_ERROR_CODES.has(response.status);

      if (!isServerError) {
        return response;
      }

      lastResponse = response;

      if (attempt < RETRY_DELAYS_MS.length) {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAYS_MS[attempt]));
      }
    }

    return lastResponse!;
  }

  private mapApiResponse(
    apiData: ApiUsageResponse,
    currentModel: string
  ): UsageData {
    return mapClaudeUsageResponse(apiData, currentModel);
  }

  private async refreshAccessToken(credentials: OAuthCredentials): Promise<OAuthCredentials> {
    const body = new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: credentials.refreshToken,
      client_id: CLAUDE_CODE_CLIENT_ID,
    });
    const res = await fetch(TOKEN_REFRESH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    if (!res.ok) {
      throw new Error(`Token refresh failed: ${res.status}`);
    }
    const json = await res.json() as { access_token: string; refresh_token: string; expires_in: number };
    return {
      ...credentials,
      accessToken: json.access_token,
      refreshToken: json.refresh_token,
      expiresAt: Date.now() + json.expires_in * 1000,
    };
  }

  private saveCredentials(credentials: OAuthCredentials): void {
    if (this.credentialSource === "keychain") {
      this.saveCredentialsToKeychain(credentials);
      return;
    }
    try {
      const raw = fs.readFileSync(CREDENTIALS_PATH, "utf-8");
      const file: CredentialsFile = JSON.parse(raw);
      file.claudeAiOauth = { ...file.claudeAiOauth, ...credentials };
      fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(file, null, 2), "utf-8");
    } catch {
      // Non-fatal: extension will use the refreshed token for this session only
    }
  }

  private saveCredentialsToKeychain(credentials: OAuthCredentials): void {
    try {
      // Merge into the existing Keychain blob so we preserve any sibling fields
      // Claude Code stores alongside claudeAiOauth.
      let file: CredentialsFile = {};
      const raw = this.readKeychainItem(this.keychainService);
      if (raw) {
        try {
          file = JSON.parse(raw);
        } catch {
          file = {};
        }
      }
      file.claudeAiOauth = { ...file.claudeAiOauth, ...credentials };
      // -U updates the existing generic-password item in place.
      execFileSync(
        "security",
        [
          "add-generic-password",
          "-U",
          "-a",
          os.userInfo().username,
          "-s",
          this.keychainService,
          "-w",
          JSON.stringify(file),
        ],
        { timeout: 5_000 }
      );
    } catch {
      // Non-fatal: extension will use the refreshed token for this session only
    }
  }
}

/* ------------------------------------------------------------------ */
/*  Response mapping (pure, so it can be unit-tested without a host)   */
/* ------------------------------------------------------------------ */

/** The value shown when a window is absent from the payload entirely. */
function emptyMetric(): UsageMetric {
  return { percent: 0, resetsIn: "N/A", resetsAt: null };
}

/** Normalize one percentage plus its ISO reset timestamp into a UsageMetric. */
function toMetric(
  percent: number | null | undefined,
  resetsAtIso: string | null | undefined
): UsageMetric {
  if (typeof percent !== "number" || !Number.isFinite(percent)) {
    return emptyMetric();
  }
  const parsed = resetsAtIso ? new Date(resetsAtIso).getTime() : Number.NaN;
  const resetsAt = Number.isFinite(parsed) ? parsed : null;
  return {
    percent: Math.round(percent),
    resetsIn: resetsAt != null ? formatResetTime(resetsAt) : "N/A",
    resetsAt,
  };
}

/** The pre-`limits` per-window fields, kept as the fallback path. */
function mapLegacyLimit(limit: ApiUsageLimit | null | undefined): UsageMetric {
  return limit ? toMetric(limit.utilization, limit.resets_at) : emptyMetric();
}

function findLimit(limits: ApiLimitEntry[], kind: string): ApiLimitEntry | undefined {
  return limits.find((entry) => entry != null && entry.kind === kind);
}

/**
 * The first model-scoped weekly limit that carries a usable display name.
 * An entry without one is skipped rather than shown under an invented label:
 * the account page names this bar after the model, so an unnamed bar would be
 * a number with no stated meaning.
 */
function mapScopedWeekly(limits: ApiLimitEntry[]): ScopedUsageMetric | undefined {
  for (const entry of limits) {
    if (entry == null || entry.kind !== "weekly_scoped") {
      continue;
    }
    const label = entry.scope?.model?.display_name?.trim();
    if (!label) {
      continue;
    }
    return { ...toMetric(entry.percent, entry.resets_at), label };
  }
  return undefined;
}

/**
 * Map an account usage payload onto the normalized {@link UsageData} model.
 * Prefers the self-describing `limits` array and falls back to the older flat
 * `five_hour` / `seven_day` fields when a response does not carry it.
 */
export function mapClaudeUsageResponse(
  apiData: ApiUsageResponse,
  currentModel: string
): UsageData {
  const limits = Array.isArray(apiData.limits) ? apiData.limits : [];
  const session = findLimit(limits, "session");
  const weeklyAll = findLimit(limits, "weekly_all");
  const extra = apiData.extra_usage;

  return {
    session: session
      ? toMetric(session.percent, session.resets_at)
      : mapLegacyLimit(apiData.five_hour),
    weeklyAllModels: weeklyAll
      ? toMetric(weeklyAll.percent, weeklyAll.resets_at)
      : mapLegacyLimit(apiData.seven_day),
    weeklyScoped: mapScopedWeekly(limits),
    currentModel,
    lastUpdated: Date.now(),
    dataSource: "api",
    extraUsage: extra
      ? {
          isEnabled: extra.is_enabled,
          monthlyLimit: extra.monthly_limit / 100,
          usedCredits: extra.used_credits / 100,
          utilization: extra.utilization,
        }
      : undefined,
  };
}
