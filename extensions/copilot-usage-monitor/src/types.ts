import * as vscode from "vscode";

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";

/** The settings section every `copilotUsage.*` key lives under. */
export const CONFIG_SECTION = "copilotUsage";

/**
 * One limited quota from `copilot_internal/user` `quota_snapshots`. Only a quota
 * GitHub serves as limited (`unlimited` false, `has_quota` true, `entitlement`
 * above 0) becomes a row; see decision file v4.13.7, Copilot usage monitor (1).
 */
export interface QuotaRow {
  /** The `quota_snapshots` key, e.g. `premium_interactions`. */
  id: string;
  /** Display label, e.g. "Premium requests". */
  label: string;
  /** Percent used, 0 to 100, unrounded. */
  percent: number;
  /** The quota GitHub serves (`entitlement`). */
  entitlement: number;
  /** What is left (`remaining`). */
  remaining: number;
}

/** The personal figure, read from the account pinned for this extension. */
export interface PersonalUsage {
  /** Plan name derived from `copilot_plan` / `access_type_sku`, never the login. */
  planLabel: string;
  /** Every qualifying quota, in display order. */
  quotas: QuotaRow[];
  /** The status-bar quota (premium requests, else chat, else completions), or null when none qualifies. */
  primary: QuotaRow | null;
  /** Sum of `credits_used` across quotas; the member view shows this with no percentage. */
  creditsUsed: number;
  /** Monthly reset, epoch ms, from `quota_reset_date_utc` (else `quota_reset_date`). */
  resetsAt: number | null;
  /** When GitHub returned this figure, epoch ms; set by the service. */
  fetchedAt?: number;
  /** True when the latest refresh failed transiently and this is the last good figure. */
  stale?: boolean;
}

/** Per-model used credits, mirroring the organization AI usage page breakdown. */
export interface ModelCredits {
  model: string;
  used: number;
}

/** Why a pool total is labelled approximate. */
export type ApproximateReason = "seat-added" | "pending-cancellation";

/** The organization's shared AI-credit pool; see decision file items (2) and (3). */
export interface OrganizationUsage {
  /** Sum of `discountQuantity` over Copilot AI-credit line items, unrounded. */
  used: number;
  /** Seats x published per-seat rate; 0 when the seat count or plan is unknown. */
  total: number;
  /** Pool percent used, 0 to 100, or null when there is no total to divide by. */
  percent: number | null;
  seats: number;
  planType: "business" | "enterprise" | "unknown";
  /** Credits per seat for `planType` (1,900 Business, 3,900 Enterprise, 0 unknown). */
  creditsPerSeat: number;
  approximate: boolean;
  approximateReasons: ApproximateReason[];
  /** First day of the next calendar month, 00:00:00 UTC, epoch ms. */
  resetsAt: number;
  models: ModelCredits[];
  /** When GitHub returned this figure, epoch ms; set by the service. */
  fetchedAt?: number;
  /** True when the latest refresh failed transiently and this is the last good figure. */
  stale?: boolean;
}

/** A non-fatal failure of one half of the fetch, shown while the other half still renders. */
export interface PartialError {
  code: string;
  statusCode?: number;
}

export type DataSource = "api";

/** Everything the status bar, dashboard, warning view, and state file render from. */
export interface UsageData {
  personal?: PersonalUsage;
  organization?: OrganizationUsage;
  /** The organization half failed while the personal half succeeded. */
  organizationError?: PartialError;
  /** The personal half failed while the organization half succeeded. */
  personalError?: PartialError;
  lastUpdated: number;
  dataSource: DataSource;
}

/** The figure the status bar shows, chosen by {@link headlineOf}. */
export type Headline =
  | {
      kind: "percent";
      source: "organization" | "personal";
      percent: number;
      approximate: boolean;
      resetsAt: number | null;
      label: string;
      stale: boolean;
      fetchedAt: number;
    }
  | { kind: "credits"; creditsUsed: number; label: string }
  | { kind: "none" };

/**
 * Status-bar precedence (plan 2.4): the organization pool percentage when
 * connected, else the personal-plan percentage, else credits used with no
 * percentage. The state file uses the same precedence (plan 2.5).
 */
export function headlineOf(data: UsageData | undefined): Headline {
  if (!data) {
    return { kind: "none" };
  }
  const org = data.organization;
  if (org && org.percent != null) {
    return {
      kind: "percent",
      source: "organization",
      percent: org.percent,
      approximate: org.approximate,
      resetsAt: org.resetsAt,
      label: "Organization pool",
      stale: org.stale === true,
      fetchedAt: org.fetchedAt ?? data.lastUpdated,
    };
  }
  const personal = data.personal;
  if (personal?.primary) {
    return {
      kind: "percent",
      source: "personal",
      percent: personal.primary.percent,
      approximate: false,
      resetsAt: personal.resetsAt,
      label: personal.primary.label,
      stale: personal.stale === true,
      fetchedAt: personal.fetchedAt ?? data.lastUpdated,
    };
  }
  if (personal) {
    return { kind: "credits", creditsUsed: personal.creditsUsed, label: personal.planLabel };
  }
  if (org) {
    return { kind: "credits", creditsUsed: org.used, label: "Organization pool" };
  }
  return { kind: "none" };
}

export interface Recommendation {
  urgency: UrgencyLevel;
  message: string;
  tips: string[];
}

/** Upper boundary for each level. At or above this value, you enter the next level. */
export const URGENCY_THRESHOLDS = {
  moderate: 50,
  high: 75,
  critical: 95,
} as const;

/** Default notification timeout (seconds) before a threshold popup auto-dismisses. */
export const DEFAULT_NOTIFICATION_TIMEOUT_SECONDS = 12;

/** A CSS hex color string (e.g. "#cca700") or "none" to disable highlighting. */
export type ColorOption = string;

/** Default hex colors, identical to the Claude, Codex, and Cursor monitors. */
export const DEFAULT_URGENCY_COLORS = {
  moderate: "#cca700",
  high: "#f0643c",
  critical: "#e05555",
} as const;

/**
 * The progress-bar teal. Chosen for contrast on both theme families: its lowest
 * ratio against the default light and dark editor, sidebar, and hover
 * backgrounds is 3.64:1, above the WCAG 2.2 3:1 minimum for graphical objects
 * (recorded in the v4.13.7 decisions file).
 */
export const BAR_FILL = "#0E8A85";
export const BAR_TRACK = "rgba(14,138,133,0.2)";

/**
 * VS Code's allowlist for StatusBarItem.backgroundColor contains only
 * "statusBarItem.warningBackground" and "statusBarItem.errorBackground", so
 * moderate and high share warningBackground and its hex is swapped per level.
 */
export const WORKBENCH_COLOR_KEYS = {
  moderate: "statusBarItem.warningBackground",
  high: "statusBarItem.warningBackground",
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

/** A hex color the status bar and the settings form accept. */
export const HEX_COLOR = /^#[0-9a-fA-F]{6}$/;

/** A threshold as stored, or `fallback` unless it is a finite number from 1 to 99. */
export function validThreshold(raw: unknown, fallback: number): number {
  return typeof raw === "number" && Number.isFinite(raw) && raw >= 1 && raw <= 99 ? raw : fallback;
}

/**
 * Read threshold settings, falling back to defaults for anything that is not a
 * number from 1 to 99. Settings can come from a workspace file, so they are
 * validated where they are read.
 */
export function getThresholdConfig(): ThresholdConfig {
  const c = vscode.workspace.getConfiguration(CONFIG_SECTION);
  return {
    moderate: validThreshold(c.get<unknown>("thresholds.moderate"), URGENCY_THRESHOLDS.moderate),
    high: validThreshold(c.get<unknown>("thresholds.high"), URGENCY_THRESHOLDS.high),
    critical: validThreshold(c.get<unknown>("thresholds.critical"), URGENCY_THRESHOLDS.critical),
  };
}

function colorValue(raw: unknown, defaultHex: string): string {
  return typeof raw === "string" && (raw === "none" || HEX_COLOR.test(raw)) ? raw : defaultHex;
}

/** The refresh interval in minutes, clamped to the documented 1 to 120 (10 when unusable), so 0 cannot spin. */
export function getRefreshIntervalMinutes(): number {
  const raw = vscode.workspace.getConfiguration(CONFIG_SECTION).get<unknown>("refreshInterval");
  if (typeof raw !== "number" || !Number.isFinite(raw)) {
    return 10;
  }
  return Math.min(120, Math.max(1, raw));
}

/** Read color settings from VS Code configuration. */
export function getColorConfig(): ColorConfig {
  const c = vscode.workspace.getConfiguration(CONFIG_SECTION);
  return {
    moderate: colorValue(c.get<unknown>("colors.moderate"), DEFAULT_URGENCY_COLORS.moderate),
    high: colorValue(c.get<unknown>("colors.high"), DEFAULT_URGENCY_COLORS.high),
    critical: colorValue(c.get<unknown>("colors.critical"), DEFAULT_URGENCY_COLORS.critical),
  };
}

/** The notification auto-dismiss timeout in milliseconds, clamped to 3 to 60 seconds. */
export function getNotificationTimeoutMs(): number {
  const seconds = vscode.workspace
    .getConfiguration(CONFIG_SECTION)
    .get<number>("notificationTimeoutSeconds", DEFAULT_NOTIFICATION_TIMEOUT_SECONDS);
  return Math.max(3, Math.min(60, seconds)) * 1000;
}


/**
 * Write user-chosen hex colors into workbench.colorCustomizations for the
 * status-bar ThemeColor IDs. Writes only changed entries; removes them for "none".
 */
export async function syncColorsToWorkbench(colors: ColorConfig): Promise<void> {
  const wbConfig = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(wbConfig.get<Record<string, string>>("colorCustomizations") ?? {}),
  };
  // Moderate and high share warningBackground, so resolve each key's final
  // value first (later levels win) and compare once; comparing per level
  // would rewrite the setting on every call.
  const desired = new Map<string, string>();
  const levels: Array<keyof typeof WORKBENCH_COLOR_KEYS> = ["moderate", "high", "critical"];
  for (const level of levels) {
    const hex = colors[level];
    if (hex === "none" || HEX_COLOR.test(hex)) {
      desired.set(WORKBENCH_COLOR_KEYS[level], hex);
    }
  }
  let changed = false;
  for (const [key, hex] of desired) {
    if (hex === "none") {
      if (key in existing) {
        delete existing[key];
        changed = true;
      }
    } else if (existing[key] !== hex) {
      existing[key] = hex;
      changed = true;
    }
  }
  if (changed) {
    await wbConfig.update("colorCustomizations", existing, vscode.ConfigurationTarget.Global);
  }
}

/**
 * Keep warningBackground in step with the active level (moderate and high share
 * it). Low and critical return early so another monitor's color is not overwritten.
 */
export async function syncActiveColorToWorkbench(urgency: UrgencyLevel, colors: ColorConfig): Promise<void> {
  if (urgency !== "moderate" && urgency !== "high") {
    return;
  }
  const wbConfig = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(wbConfig.get<Record<string, string>>("colorCustomizations") ?? {}),
  };
  const warnKey = "statusBarItem.warningBackground";
  let changed = false;
  const hex = colors[urgency];
  if (hex === "none") {
    if (warnKey in existing) {
      delete existing[warnKey];
      changed = true;
    }
  } else if (HEX_COLOR.test(hex) && existing[warnKey] !== hex) {
    existing[warnKey] = hex;
    changed = true;
  }
  if (changed) {
    await wbConfig.update("colorCustomizations", existing, vscode.ConfigurationTarget.Global);
  }
}
