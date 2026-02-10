import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  UsageData,
  ApiUsageResponse,
  ApiUsageLimit,
  CredentialsFile,
  OAuthCredentials,
  ClaudeModel,
} from "./types";

const CREDENTIALS_PATH = path.join(os.homedir(), ".claude", ".credentials.json");
const USAGE_API_URL = "https://api.anthropic.com/api/oauth/usage";
const ANTHROPIC_BETA_HEADER = "oauth-2025-04-20";

export type FetchError =
  | "no-credentials-file"
  | "invalid-credentials"
  | "token-expired"
  | "network-error"
  | "api-error"
  | "parse-error";

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
      return { success: false, error: "no-credentials-file" };
    }

    if (this.isTokenExpired(credentials)) {
      return { success: false, error: "token-expired" };
    }

    let response: Response;
    try {
      response = await fetch(USAGE_API_URL, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${credentials.accessToken}`,
          "anthropic-beta": ANTHROPIC_BETA_HEADER,
        },
      });
    } catch {
      return { success: false, error: "network-error" };
    }

    if (!response.ok) {
      return { success: false, error: "api-error" };
    }

    let apiData: ApiUsageResponse;
    try {
      apiData = (await response.json()) as ApiUsageResponse;
    } catch {
      return { success: false, error: "parse-error" };
    }

    return {
      success: true,
      data: this.mapApiResponse(apiData, currentModel ?? "opus-4.6"),
    };
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

  private mapLimit(limit: ApiUsageLimit | null): {
    percent: number;
    resetsIn: string;
  } {
    if (!limit) {
      return { percent: 0, resetsIn: "N/A" };
    }
    return {
      percent: Math.round(limit.utilization),
      resetsIn: this.formatResetTime(limit.resets_at),
    };
  }

  private formatResetTime(isoTimestamp: string | null): string {
    if (!isoTimestamp) {
      return "N/A";
    }

    const resetDate = new Date(isoTimestamp);
    const now = new Date();
    const diffMs = resetDate.getTime() - now.getTime();

    if (diffMs <= 0) {
      return "any moment";
    }

    const diffMinutes = Math.floor(diffMs / 60_000);
    if (diffMinutes < 60) {
      return `${diffMinutes} min`;
    }

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
      const remainingMin = diffMinutes % 60;
      return remainingMin > 0 ? `${diffHours}h ${remainingMin}m` : `${diffHours}h`;
    }

    return resetDate.toLocaleDateString("en-US", {
      weekday: "short",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }

  static getErrorMessage(error: FetchError): string {
    switch (error) {
      case "no-credentials-file":
        return "Claude Code credentials not found. Log in to Claude Code first.";
      case "invalid-credentials":
        return "Claude Code credentials are invalid.";
      case "token-expired":
        return "Claude Code session has expired. Re-authenticate in Claude Code.";
      case "network-error":
        return "Could not reach the Claude API. Check your internet connection.";
      case "api-error":
        return "The Claude API returned an error.";
      case "parse-error":
        return "Could not parse the API response.";
    }
  }
}
