export type ClaudeModel = "opus-4.6" | "sonnet-4.5" | "haiku-4.5";

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";

export interface UsageMetric {
  percent: number;
  resetsIn: string;
}

export type DataSource = "api" | "manual";

export interface UsageData {
  session: UsageMetric;
  weeklyAllModels: UsageMetric;
  weeklySonnet: UsageMetric;
  currentModel: ClaudeModel;
  lastUpdated: number;
  dataSource?: DataSource;
}

/** Shape returned by https://api.anthropic.com/api/oauth/usage */
export interface ApiUsageLimit {
  utilization: number;
  resets_at: string;
}

export interface ApiExtraUsage {
  is_enabled: boolean;
  monthly_limit: number;
  used_credits: number;
  utilization: number | null;
}

export interface ApiUsageResponse {
  five_hour: ApiUsageLimit | null;
  seven_day: ApiUsageLimit | null;
  seven_day_oauth_apps: ApiUsageLimit | null;
  seven_day_opus: ApiUsageLimit | null;
  seven_day_sonnet: ApiUsageLimit | null;
  seven_day_cowork: ApiUsageLimit | null;
  iguana_necktie: unknown;
  extra_usage: ApiExtraUsage | null;
}

export interface OAuthCredentials {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  scopes: string[];
  subscriptionType: string | null;
  rateLimitTier: string | null;
}

export interface CredentialsFile {
  claudeAiOauth: OAuthCredentials;
  organizationUuid: string;
}

export interface Recommendation {
  urgency: UrgencyLevel;
  message: string;
  suggestedModel: ClaudeModel | null;
  tips: string[];
}

export interface StatusBarState {
  sessionPercent: number;
  weeklyPercent: number;
  urgency: UrgencyLevel;
  tooltip: string;
}

export const MODEL_DISPLAY_NAMES: Record<ClaudeModel, string> = {
  "opus-4.6": "Opus 4.6",
  "sonnet-4.5": "Sonnet 4.5",
  "haiku-4.5": "Haiku 4.5",
};

/** Upper boundary for each level. At or above this value, you enter the next level. */
export const URGENCY_THRESHOLDS = {
  /** At or above 50% → moderate */
  moderate: 50,
  /** At or above 75% → high */
  high: 75,
  /** At or above 90% → critical */
  critical: 90,
} as const;
