import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  UsageData,
  UsageMetric,
  ApiUsageResponse,
  ApiUsageLimit,
  CredentialsFile,
  OAuthCredentials,
} from "./types";
import { formatResetTime } from "./usageStore";

const CREDENTIALS_PATH = path.join(os.homedir(), ".claude", ".credentials.json");
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

export type FetchErrorCode =
  | "no-credentials-file"
  | "invalid-credentials"
  | "token-expired"
  | "token-refresh-failed"
  | "token-invalid"
  | "rate-limited"
  | "network-error"
  | "api-error"
  | "parse-error";

export interface FetchError {
  code: FetchErrorCode;
  statusCode?: number;
  statusText?: string;
}

export type FetchResult =
  | { success: true; data: UsageData }
  | { success: false; error: FetchError };

export class UsageFetcher {
  private readCredentials(): OAuthCredentials | null {
    try {
      if (!fs.existsSync(CREDENTIALS_PATH)) {
        return null;
      }
      const raw = fs.readFileSync(CREDENTIALS_PATH, "utf-8");
      const parsed: CredentialsFile = JSON.parse(raw);
      if (!parsed.claudeAiOauth?.accessToken) {
        return null;
      }
      return parsed.claudeAiOauth;
    } catch {
      return null;
    }
  }

  private isTokenExpired(credentials: OAuthCredentials): boolean {
    return Date.now() >= credentials.expiresAt;
  }

  async fetch(currentModel?: string): Promise<FetchResult> {
    let credentials = this.readCredentials();
    if (!credentials) {
      return { success: false, error: { code: "no-credentials-file" } };
    }

    if (this.isTokenExpired(credentials)) {
      if (tokenRefreshInProgress) {
        return { success: false, error: { code: "token-expired" } };
      }
      tokenRefreshInProgress = true;
      try {
        const fresh = await this.refreshAccessToken(credentials);
        this.saveCredentials(fresh);
        lastTokenRefreshAt = Date.now();
        credentials = fresh;
      } catch {
        return { success: false, error: { code: "token-refresh-failed" } };
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
      return { success: false, error: { code: "network-error" } };
    }

    if (!response.ok) {
      if (response.status === 401) {
        return {
          success: false,
          error: {
            code: "token-invalid",
            statusCode: response.status,
            statusText: response.statusText,
          },
        };
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
              return { success: false, error: { code: "network-error" } };
            }
            if (retryResponse.ok) {
              let apiData: ApiUsageResponse;
              try {
                apiData = (await retryResponse.json()) as ApiUsageResponse;
              } catch {
                return { success: false, error: { code: "parse-error" } };
              }
              return { success: true, data: this.mapApiResponse(apiData, currentModel ?? "claude-opus-4-6[1m]") };
            }
            // Retry also failed — fall through to rate-limited
          } catch {
            // Token refresh failed — fall through to rate-limited
          } finally {
            tokenRefreshInProgress = false;
          }
        }

        return {
          success: false,
          error: {
            code: "rate-limited",
            statusCode: response.status,
            statusText: response.statusText,
          },
        };
      }
      return {
        success: false,
        error: {
          code: "api-error",
          statusCode: response.status,
          statusText: response.statusText,
        },
      };
    }

    let apiData: ApiUsageResponse;
    try {
      apiData = (await response.json()) as ApiUsageResponse;
    } catch {
      return { success: false, error: { code: "parse-error" } };
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
    return {
      session: this.mapLimit(apiData.five_hour),
      weeklyAllModels: this.mapLimit(apiData.seven_day),
      weeklySonnet: this.mapLimit(apiData.seven_day_sonnet),
      currentModel,
      lastUpdated: Date.now(),
      dataSource: "api",
      extraUsage: apiData.extra_usage ? {
        isEnabled: apiData.extra_usage.is_enabled,
        monthlyLimit: apiData.extra_usage.monthly_limit / 100,
        usedCredits: apiData.extra_usage.used_credits / 100,
        utilization: apiData.extra_usage.utilization,
      } : undefined,
    };
  }

  private mapLimit(limit: ApiUsageLimit | null): UsageMetric {
    if (!limit) {
      return { percent: 0, resetsIn: "N/A", resetsAt: null };
    }
    const resetsAt = limit.resets_at ? new Date(limit.resets_at).getTime() : null;
    return {
      percent: Math.round(limit.utilization),
      resetsIn: resetsAt != null ? formatResetTime(resetsAt) : "N/A",
      resetsAt,
    };
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
    try {
      const raw = fs.readFileSync(CREDENTIALS_PATH, "utf-8");
      const file: CredentialsFile = JSON.parse(raw);
      file.claudeAiOauth = { ...file.claudeAiOauth, ...credentials };
      fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(file, null, 2), "utf-8");
    } catch {
      // Non-fatal: extension will use the refreshed token for this session only
    }
  }

  static getErrorMessage(error: FetchError): string {
    const suffix =
      error.statusCode != null
        ? ` (${error.statusCode}${error.statusText ? " " + error.statusText : ""})`
        : "";

    switch (error.code) {
      case "no-credentials-file":
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
}
