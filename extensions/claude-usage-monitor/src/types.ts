/** Any Claude model ID string, e.g. "claude-sonnet-4-6" or "claude-sonnet-4-6[1m]". */
export type ClaudeModel = string;

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";

export interface UsageMetric {
  percent: number;
  resetsIn: string;
  resetsAt: number | null;
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

/**
 * Parse any Claude model ID into a human-readable display name matching Claude Code's UI.
 * Handles short aliases ("sonnet", "opus", "haiku", "default") and full IDs
 * ("claude-sonnet-4-6"), plus the [1m] bracket suffix for extended-context variants.
 * Examples:
 *   "sonnet[1m]"            → "Sonnet (1M context)"
 *   "sonnet"                → "Sonnet"
 *   "default"               → "Opus"
 *   "claude-opus-4-6"       → "Opus"
 *   "claude-haiku-4-5"      → "Haiku"
 *   "claude-opus-5-0"       → "Opus"  (future-proof)
 */
export function formatModelName(modelId: string): string {
  const is1M = /\[1m\]/i.test(modelId);
  const base = modelId.replace(/\[.*?\]/g, "").trim();
  let family: string;
  if (/opus|default/i.test(base)) {
    family = "Opus";
  } else if (/sonnet/i.test(base)) {
    family = "Sonnet";
  } else if (/haiku/i.test(base)) {
    family = "Haiku";
  } else {
    // Unknown future model: strip prefix and version, capitalize
    const cleaned = base.replace(/^claude-?/i, "").replace(/-\d.*/, "").replace(/-/g, " ").trim();
    family = cleaned ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1) : modelId;
  }
  return is1M ? `${family} (1M context)` : family;
}

/** Strip the [1m] or any bracket suffix to get the base model ID. */
export function baseModelId(modelId: string): string {
  return modelId.replace(/\[.*?\]/g, "").trim();
}

/** Returns true if the model ID indicates the 1M extended-context variant. */
export function is1MContext(modelId: string): boolean {
  return /\[1m\]/i.test(modelId);
}

/** Upper boundary for each level. At or above this value, you enter the next level. */
export const URGENCY_THRESHOLDS = {
  /** At or above 50% → moderate */
  moderate: 50,
  /** At or above 75% → high */
  high: 75,
  /** At or above 90% → critical */
  critical: 90,
} as const;
