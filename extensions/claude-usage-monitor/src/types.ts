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
  currentModel: ClaudeModel;
  lastUpdated: number;
  dataSource?: DataSource;
  extraUsage?: ExtraUsageInfo;
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
 * Parse any Claude model ID into its bare family name (Fable, Opus, Sonnet, Haiku).
 * Handles short aliases ("sonnet", "opus", "haiku", "default") and full IDs
 * ("claude-fable-5"), stripping any [1m]-style bracket suffix. No "Default" label
 * and no context-window suffix — the dashboard shows only the model family.
 * Examples:
 *   "claude-fable-5[1m]"    → "Fable"
 *   "sonnet[1m]"            → "Sonnet"
 *   "default"               → "Opus"  (Claude Code's default tier)
 *   "claude-opus-4-6"       → "Opus"
 *   "claude-haiku-4-5"      → "Haiku"
 */
export function formatModelName(modelId: string): string {
  const base = modelId.replace(/\[.*?\]/g, "").trim();
  if (/^default$/i.test(base)) {
    return "Opus";
  }
  if (/fable/i.test(base)) {
    return "Fable";
  }
  if (/opus/i.test(base)) {
    return "Opus";
  }
  if (/sonnet/i.test(base)) {
    return "Sonnet";
  }
  if (/haiku/i.test(base)) {
    return "Haiku";
  }
  // Unknown future model: strip prefix and version, capitalize
  const cleaned = base.replace(/^claude-?/i, "").replace(/-\d.*/, "").replace(/-/g, " ").trim();
  return cleaned ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1) : modelId;
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
  /** At or above 95% → critical */
  critical: 95,
} as const;

/** Default notification timeout (seconds) before a threshold popup auto-dismisses. */
export const DEFAULT_NOTIFICATION_TIMEOUT_SECONDS = 12;

/**
 * Status bar color for a given urgency level.
 * Either a CSS hex color string (e.g. "#cca700") or "none" to disable highlighting.
 */
export type ColorOption = string;

/** Which usage metric the urgency thresholds are evaluated against. */
export type ThresholdMetric = "highest" | "session" | "weekly";

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
  const raw = vscode.workspace
    .getConfiguration("claudeUsage")
    .get<string>("thresholdMetric", "highest");
  // Legacy migration: the Weekly (Sonnet) limit is no longer tracked on the
  // Claude Usage page; a persisted "sonnet" selection folds into "weekly".
  if (raw === "sonnet") {
    return "weekly";
  }
  return raw === "session" || raw === "weekly" ? raw : "highest";
}

/**
 * Read the notification auto-dismiss timeout (in milliseconds), clamped to the
 * range advertised in package.json so a corrupt user setting never produces a
 * popup that stays on screen forever or one that disappears before it can be read.
 */
export function getNotificationTimeoutMs(): number {
  const seconds = vscode.workspace
    .getConfiguration("claudeUsage")
    .get<number>("notificationTimeoutSeconds", DEFAULT_NOTIFICATION_TIMEOUT_SECONDS);
  const clamped = Math.max(3, Math.min(60, seconds));
  return clamped * 1000;
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
 * current urgency level. Moderate and high both use statusBarItem.warningBackground,
 * so we swap the hex value whenever urgency toggles between those two levels. Low and
 * critical do not use warningBackground and must not overwrite a color another usage
 * monitor is actively displaying. Critical uses statusBarItem.errorBackground instead.
 */
export async function syncActiveColorToWorkbench(urgency: UrgencyLevel, colors: ColorConfig): Promise<void> {
  if (urgency !== "moderate" && urgency !== "high") {
    return;
  }

  const hexRegex = /^#[0-9a-fA-F]{6}$/i;
  const wbConfig = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(wbConfig.get<Record<string, string>>("colorCustomizations") ?? {}),
  };

  const warnKey = "statusBarItem.warningBackground";
  let changed = false;
  const hex = colors[urgency];
  if (hex === "none") {
    if (warnKey in existing) { delete existing[warnKey]; changed = true; }
  } else if (hexRegex.test(hex) && existing[warnKey] !== hex) {
    existing[warnKey] = hex;
    changed = true;
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
