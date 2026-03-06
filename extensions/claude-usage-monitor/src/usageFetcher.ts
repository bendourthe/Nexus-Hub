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
  ClaudeModel,
} from "./types";
import { formatResetTime } from "./usageStore";

const CREDENTIALS_PATH = path.join(os.homedir(), ".claude", ".credentials.json");
const USAGE_API_URL = "https://api.anthropic.com/api/oauth/usage";
const ANTHROPIC_BETA_HEADER = "oauth-2025-04-20";
const TOKEN_REFRESH_URL = "https://console.anthropic.com/v1/oauth/token";
const CLAUDE_CODE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e";

const SERVER_ERROR_CODES = new Set([500, 502, 503, 504]);
const RETRY_DELAYS_MS = [2_000, 5_000];
const RATE_LIMIT_DELAYS_MS = [10_000, 30_000];
const MAX_RETRY_AFTER_MS = 60_000;

export type FetchErrorCode =
  | "no-credentials-file"
  | "invalid-credentials"
  | "token-expired"
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

  async fetch(currentModel?: ClaudeModel): Promise<FetchResult> {
    const credentials = this.readCredentials();
    if (!credentials) {
      return { success: false, error: { code: "no-credentials-file" } };
    }

    if (this.isTokenExpired(credentials)) {
      return { success: false, error: { code: "token-expired" } };
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

    // On 429, attempt a token refresh and retry once with the new access token.
    // Rate limits on this endpoint are per-access-token (~5 requests per token),
    // so a fresh token resets the budget without requiring the user to do anything.
    if (response.status === 429) {
      const refreshed = await this.refreshAccessToken(credentials);
      if (refreshed) {
        this.saveCredentials(refreshed);
        const retryHeaders = {
          Authorization: `Bearer ${refreshed.accessToken}`,
          "anthropic-beta": ANTHROPIC_BETA_HEADER,
        };
        try {
          response = await fetch(USAGE_API_URL, { method: "GET", headers: retryHeaders });
        } catch {
          return { success: false, error: { code: "network-error" } };
        }
      }
      // If refresh failed or retry still 429, fall through to the error handling below.
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
      data: this.mapApiResponse(apiData, currentModel ?? "opus-4.6"),
    };
  }

  private async fetchWithRetry(
    url: string,
    headers: Record<string, string>
  ): Promise<Response> {
    let lastResponse: Response | undefined;

    for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
      const response = await fetch(url, { method: "GET", headers });

      if (response.ok) {
        return response;
      }

      const isRateLimit = response.status === 429;
      const isServerError = SERVER_ERROR_CODES.has(response.status);

      if (!isRateLimit && !isServerError) {
        return response;
      }

      lastResponse = response;

      if (attempt < RETRY_DELAYS_MS.length) {
        const delayMs = isRateLimit
          ? this.getRetryAfterMs(response) ?? RATE_LIMIT_DELAYS_MS[attempt]
          : RETRY_DELAYS_MS[attempt];
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }

    return lastResponse!;
  }

  private getRetryAfterMs(response: Response): number | undefined {
    const header = response.headers.get("retry-after");
    if (!header) {
      return undefined;
    }
    const seconds = Number(header);
    if (!Number.isFinite(seconds) || seconds <= 0) {
      return undefined;
    }
    return Math.min(seconds * 1_000, MAX_RETRY_AFTER_MS);
  }

  private async refreshAccessToken(
    credentials: OAuthCredentials
  ): Promise<OAuthCredentials | null> {
    try {
      const response = await fetch(TOKEN_REFRESH_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grant_type: "refresh_token",
          refresh_token: credentials.refreshToken,
          client_id: CLAUDE_CODE_CLIENT_ID,
        }),
      });
      if (!response.ok) {
        return null;
      }
      const data = (await response.json()) as {
        access_token: string;
        refresh_token: string;
        expires_in: number;
      };
      if (!data.access_token || !data.refresh_token) {
        return null;
      }
      return {
        ...credentials,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresAt: Date.now() + data.expires_in * 1_000,
      };
    } catch {
      return null;
    }
  }

  private saveCredentials(credentials: OAuthCredentials): void {
    try {
      const raw = fs.readFileSync(CREDENTIALS_PATH, "utf-8");
      const parsed = JSON.parse(raw) as { claudeAiOauth: OAuthCredentials; [key: string]: unknown };
      parsed.claudeAiOauth = {
        ...parsed.claudeAiOauth,
        accessToken: credentials.accessToken,
        refreshToken: credentials.refreshToken,
        expiresAt: credentials.expiresAt,
      };
      fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(parsed, null, 2), "utf-8");
    } catch {
      // Non-fatal: the in-memory token is still valid for this fetch cycle.
    }
  }

  private mapApiResponse(
    apiData: ApiUsageResponse,
    currentModel: ClaudeModel
  ): UsageData {
    return {
      session: this.mapLimit(apiData.five_hour),
      weeklyAllModels: this.mapLimit(apiData.seven_day),
      weeklySonnet: this.mapLimit(apiData.seven_day_sonnet),
      currentModel,
      lastUpdated: Date.now(),
      dataSource: "api",
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
