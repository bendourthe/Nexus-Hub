/** Any Claude model ID string, e.g. "claude-sonnet-4-6" or "claude-sonnet-4-6[1m]". */
export type ClaudeModel = string;

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";

export interface UsageMetric {
  percent: number;
  resetsIn: string;
  resetsAt: number | null;
}

export type DataSource = "api" | "manual";

export interface ExtraUsageInfo {
  isEnabled: boolean;
  monthlyLimit: number;
  usedCredits: number;
  utilization: number | null;
}

export interface UsageData {
  session: UsageMetric;
  weeklyAllModels: UsageMetric;
  weeklySonnet: UsageMetric;
  currentModel: ClaudeModel;
  lastUpdated: number;
  dataSource?: DataSource;
  extraUsage?: ExtraUsageInfo;
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
 *   "default"               → "Default (Sonnet)"  (Claude Code's "Default (recommended)", currently Sonnet)
 *   "claude-opus-4-6"       → "Opus"
 *   "claude-haiku-4-5"      → "Haiku"
 *   "claude-opus-5-0"       → "Opus"  (future-proof)
 */
export function formatModelName(modelId: string): string {
  const is1M = /\[1m\]/i.test(modelId);
  const base = modelId.replace(/\[.*?\]/g, "").trim();
  let family: string;
  if (/^default$/i.test(base)) {
    family = "Default (Opus 1M)";
  } else if (/opus/i.test(base)) {
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

/* ------------------------------------------------------------------ */
/*  Auto-Switch types and constants                                   */
/* ------------------------------------------------------------------ */

/** Persisted state tracking what the auto-switcher has changed. */
export interface AutoSwitchState {
  /** Model the user was on before auto-switch kicked in. */
  preAutoModel: string | null;
  /** Whether the current model was set by auto-switch (not by the user). */
  modelAutoSwitched: boolean;
  /** Timestamp of last auto-switch action. */
  lastSwitchAt: number;
  /** Usage thresholds (50, 75, 95) for which a notification has already been shown. */
  notifiedThresholds: number[];
  /** Number of Claude Code terminals that received the /model command on last switch. */
  terminalsSwitched?: number;
  /** The model that auto-switch last targeted (for multi-window propagation). */
  switchedToModel?: string | null;
  /** Epoch ms of last evaluation (for cross-window dedup). */
  lastEvaluatedAt?: number;
}

/** Runtime configuration read from VS Code settings. */
export interface AutoSwitchConfig {
  enabled: boolean;
  model: boolean;
  modelSonnetThreshold: number;
  modelHaikuThreshold: number;
}

export type AutoSwitchActionKind =
  | "model-switched"
  | "model-restored"
  | "usage-advisory";

export interface AutoSwitchAction {
  kind: AutoSwitchActionKind;
  from: string;
  to: string;
  triggerPercent: number;
  /** Human-readable notification/dashboard message for usage-advisory actions. */
  message?: string;
  /** Number of Claude Code terminals that received the /model command. */
  terminalCount?: number;
}

export const DEFAULT_AUTO_SWITCH_STATE: AutoSwitchState = {
  preAutoModel: null,
  modelAutoSwitched: false,
  lastSwitchAt: 0,
  notifiedThresholds: [],
};
