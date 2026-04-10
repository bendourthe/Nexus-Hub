import * as vscode from "vscode";

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

/**
 * Status bar color for a given urgency level.
 * Either a CSS hex color string (e.g. "#cca700") or "none" to disable highlighting.
 */
export type ColorOption = string;

/** Which usage metric the urgency thresholds are evaluated against. */
export type ThresholdMetric = "highest" | "session" | "weekly" | "sonnet";

/** Default hex colors matching the badge colors in the settings panel. */
export const DEFAULT_URGENCY_COLORS = {
  moderate: "#cca700",
  high:     "#f0643c",
  critical: "#e05555",
} as const;

/**
 * Maps each urgency level to the VS Code standard ThemeColor ID used as the
 * status bar item background.
 * IMPORTANT: VS Code's allowlist for StatusBarItem.backgroundColor contains only two IDs:
 *   "statusBarItem.warningBackground" and "statusBarItem.errorBackground".
 * Both "moderate" and "high" share warningBackground; the correct hex is written
 * dynamically by syncActiveColorToWorkbench() so each level still shows its own color.
 */
export const WORKBENCH_COLOR_KEYS = {
  moderate: "statusBarItem.warningBackground",
  high:     "statusBarItem.warningBackground",  // same key; hex updated per active urgency
  critical: "statusBarItem.errorBackground",
} as const;

export interface ThresholdConfig {
  moderate: number;
  high: number;
  critical: number;
}

export interface ColorConfig {
  moderate: ColorOption;
  high: ColorOption;
  critical: ColorOption;
}

/** Read threshold settings from VS Code configuration, falling back to hardcoded defaults. */
export function getThresholdConfig(): ThresholdConfig {
  const c = vscode.workspace.getConfiguration("claudeUsage");
  return {
    moderate: c.get<number>("thresholds.moderate", URGENCY_THRESHOLDS.moderate),
    high:     c.get<number>("thresholds.high",     URGENCY_THRESHOLDS.high),
    critical: c.get<number>("thresholds.critical", URGENCY_THRESHOLDS.critical),
  };
}

/**
 * Migrate old enum values ("warning", "error") stored by previous versions to hex.
 * Returns the hex string, or "none" as-is, falling back to the provided default.
 */
function migrateColorValue(raw: string | undefined, defaultHex: string): string {
  if (!raw || raw === "warning" || raw === "error") {
    return defaultHex;
  }
  return raw;
}

/** Read color settings from VS Code configuration, migrating legacy enum values. */
export function getColorConfig(): ColorConfig {
  const c = vscode.workspace.getConfiguration("claudeUsage");
  return {
    moderate: migrateColorValue(c.get<string>("colors.moderate"), DEFAULT_URGENCY_COLORS.moderate),
    high:     migrateColorValue(c.get<string>("colors.high"),     DEFAULT_URGENCY_COLORS.high),
    critical: migrateColorValue(c.get<string>("colors.critical"), DEFAULT_URGENCY_COLORS.critical),
  };
}

/** Read which usage metric the thresholds should be evaluated against. */
export function getThresholdMetric(): ThresholdMetric {
  return vscode.workspace
    .getConfiguration("claudeUsage")
    .get<ThresholdMetric>("thresholdMetric", "highest");
}

/**
 * Write user-chosen hex colors into workbench.colorCustomizations for the three
 * standard VS Code status bar ThemeColor IDs, so they take effect immediately.
 * Only writes entries whose value has actually changed; removes entries for "none".
 * Old contributed-color entries (claudeUsageMonitor.*) from a previous build are
 * cleaned up automatically.
 */
export async function syncColorsToWorkbench(colors: ColorConfig): Promise<void> {
  const hexRegex = /^#[0-9a-fA-F]{6}$/i;
  const wbConfig = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(wbConfig.get<Record<string, string>>("colorCustomizations") ?? {}),
  };

  let changed = false;

  // Remove any stale keys from the previous contributed-color implementation
  for (const stale of [
    "claudeUsageMonitor.moderateBackground",
    "claudeUsageMonitor.highBackground",
    "claudeUsageMonitor.criticalBackground",
  ]) {
    if (stale in existing) { delete existing[stale]; changed = true; }
  }

  const levels: Array<keyof typeof WORKBENCH_COLOR_KEYS> = ["moderate", "high", "critical"];
  for (const level of levels) {
    const key = WORKBENCH_COLOR_KEYS[level];
    const hex = colors[level];
    if (hex === "none") {
      if (key in existing) { delete existing[key]; changed = true; }
    } else if (hexRegex.test(hex) && existing[key] !== hex) {
      existing[key] = hex;
      changed = true;
    }
    // Non-hex legacy values ("warning"/"error") are already migrated by getColorConfig();
    // no workbench write needed for them — the theme's default colors will show.
  }

  if (changed) {
    await wbConfig.update(
      "colorCustomizations",
      existing,
      vscode.ConfigurationTarget.Global
    );
  }
}

/**
 * Called on every status bar update to ensure the warningBackground hex reflects the
 * current urgency level.  Moderate and high both use statusBarItem.warningBackground,
 * so we swap the hex value whenever urgency toggles between those two levels.
 * Critical always uses statusBarItem.errorBackground (set by syncColorsToWorkbench).
 */
export async function syncActiveColorToWorkbench(urgency: UrgencyLevel, colors: ColorConfig): Promise<void> {
  const hexRegex = /^#[0-9a-fA-F]{6}$/i;
  const wbConfig = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(wbConfig.get<Record<string, string>>("colorCustomizations") ?? {}),
  };

  const warnKey = "statusBarItem.warningBackground";
  let changed = false;

  if (urgency === "high") {
    const hex = colors.high;
    if (hex === "none") {
      if (warnKey in existing) { delete existing[warnKey]; changed = true; }
    } else if (hexRegex.test(hex) && existing[warnKey] !== hex) {
      existing[warnKey] = hex;
      changed = true;
    }
  } else {
    // moderate, low, or critical: restore warningBackground to moderate's hex
    const hex = colors.moderate;
    if (hex === "none") {
      if (warnKey in existing) { delete existing[warnKey]; changed = true; }
    } else if (hexRegex.test(hex) && existing[warnKey] !== hex) {
      existing[warnKey] = hex;
      changed = true;
    }
  }

  if (changed) {
    await wbConfig.update("colorCustomizations", existing, vscode.ConfigurationTarget.Global);
  }
}

/* ------------------------------------------------------------------ */
/*  Suggestion state                                                   */
/* ------------------------------------------------------------------ */

/**
 * Persisted state tracking which threshold notifications have already been
 * shown to the user in the current usage cycle.
 */
export interface SuggestionState {
  /** Thresholds (50, 75, 90) for which a VS Code notification has been shown. */
  notifiedThresholds: number[];
}

export const DEFAULT_SUGGESTION_STATE: SuggestionState = {
  notifiedThresholds: [],
};
