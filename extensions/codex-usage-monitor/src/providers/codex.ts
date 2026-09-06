import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as vscode from "vscode";
import { CreditUsageInfo, UsageMetric, UsageMetricRow, UNTRACKED_METRIC, isTracked } from "../types";
import { formatResetTime, nextMonthlyResetAt } from "../usageStore";
import {
  UsageProvider,
  UsageModel,
  ProviderFetchError,
  ProviderFetchErrorCode,
  ProviderFetchResult,
  CredentialResult,
  CredentialFailureReason,
} from "./types";

const CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage";
const REQUEST_TIMEOUT_MS = 30_000;

/**
 * The Codex credential extracted from the local Codex-app auth store. Only the
 * two fields the usage endpoint needs are kept; nothing else is retained and the
 * token is never logged.
 */
export interface CodexCredential {
  accessToken: string;
  /**
   * The ChatGPT account id sent as the `chatgpt-account-id` header. Null when
   * absent, or when it is a synthetic `email_`/`local_` placeholder (in which
   * case the header is omitted, matching upstream behavior).
   */
  accountId: string | null;
}

/** Result of locating and parsing the Codex credential, secret carried internally. */
export type CodexCredentialReadResult =
  | { ok: true; credential: CodexCredential }
  | { ok: false; reason: CredentialFailureReason };

/**
 * Inputs to {@link resolveCodexAuthPath}, kept explicit so path resolution is a
 * pure function that unit tests can exercise without touching vscode, the
 * environment, or the real home directory.
 */
export interface CodexAuthPathInputs {
  /** Explicit override from the `codexUsage.authPath` setting. */
  configuredPath?: string;
  /** The `CODEX_HOME` environment variable, when set. */
  codexHome?: string;
  /** The user's home directory. */
  homeDir: string;
}

/**
 * Resolve where the Codex-app credential file lives, most-specific first:
 * an explicit configured path wins; otherwise `CODEX_HOME/auth.json`; otherwise
 * `~/.codex/auth.json`. A leading `~` in the configured path is expanded.
 *
 * The exact on-disk location the ChatGPT Codex app uses is not documented, so
 * this default is a best-effort probe and the configured-path override is the
 * escape hatch (tracked as a known gap for confirmation).
 */
export function resolveCodexAuthPath(inputs: CodexAuthPathInputs): string {
  const configured = inputs.configuredPath?.trim();
  if (configured) {
    if (configured === "~" || configured.startsWith("~/") || configured.startsWith("~\\")) {
      return path.join(inputs.homeDir, configured.slice(1));
    }
    return configured;
  }
  const base = inputs.codexHome?.trim()
    ? inputs.codexHome.trim()
    : path.join(inputs.homeDir, ".codex");
  return path.join(base, "auth.json");
}

/** True for a synthetic account id (`email_`/`local_` prefix) whose header is omitted upstream. */
export function isSyntheticAccountId(accountId: string | null): boolean {
  return accountId != null && (/^email_/.test(accountId) || /^local_/.test(accountId));
}

/**
 * Parse the raw Codex auth-file contents into a {@link CodexCredential}. Returns
 * null on any malformed input. Shape-tolerant: accepts both the nested
 * `{ tokens: { access_token, account_id } }` layout and a flat
 * `{ access_token, account_id }` layout (and their camelCase variants), so the
 * provider is not locked to one on-disk representation. Never throws.
 */
export function parseCodexCredential(raw: string): CodexCredential | null {
  let obj: unknown;
  try {
    obj = JSON.parse(raw);
  } catch {
    return null;
  }
  if (obj == null || typeof obj !== "object") {
    return null;
  }
  const root = obj as Record<string, unknown>;
  const tokens =
    root.tokens != null && typeof root.tokens === "object"
      ? (root.tokens as Record<string, unknown>)
      : {};

  const accessToken = firstString(
    tokens.access_token,
    tokens.accessToken,
    root.access_token,
    root.accessToken,
  );
  if (!accessToken) {
    return null;
  }

  const accountId = firstString(
    tokens.account_id,
    tokens.accountId,
    root.account_id,
    root.accountId,
  );

  return { accessToken, accountId: accountId ?? null };
}

/** Return the first argument that is a non-empty string, else undefined. */
function firstString(...values: unknown[]): string | undefined {
  for (const v of values) {
    if (typeof v === "string" && v.length > 0) {
      return v;
    }
  }
  return undefined;
}

/**
 * Read and parse the Codex credential at an explicit path. Pure with respect to
 * configuration (the caller resolves the path), so tests can point it at a
 * temp file. Never throws, never logs the token: a missing file yields
 * `missing`; an unreadable or malformed file yields `invalid`.
 */
export function readCodexCredential(authPath: string): CodexCredentialReadResult {
  let raw: string;
  try {
    if (!fs.existsSync(authPath)) {
      return { ok: false, reason: "missing" };
    }
    raw = fs.readFileSync(authPath, "utf-8");
  } catch {
    return { ok: false, reason: "invalid" };
  }
  const credential = parseCodexCredential(raw);
  if (!credential) {
    return { ok: false, reason: "invalid" };
  }
  return { ok: true, credential };
}

/* ------------------------------------------------------------------ */
/*  wham/usage payload mapping                                         */
/*                                                                     */
/*  Schema verified against the live endpoint (2026-07); accessors stay */
/*  defensive (aliases + fallbacks) so a future schema change degrades  */
/*  rather than breaks. The mapper returns null only when NO usable     */
/*  window is present, which the fetcher turns into the fail-soft       */
/*  "usage-unavailable" state.                                          */
/* ------------------------------------------------------------------ */

function asRecord(value: unknown): Record<string, unknown> | null {
  return value != null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function firstNumber(...values: unknown[]): number | undefined {
  for (const v of values) {
    if (typeof v === "number" && Number.isFinite(v)) {
      return v;
    }
    if (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v))) {
      return Number(v);
    }
  }
  return undefined;
}

function firstNonEmptyString(...values: unknown[]): string | undefined {
  for (const v of values) {
    if (typeof v === "string" && v.length > 0) {
      return v;
    }
  }
  return undefined;
}

/** Resolve a reset instant (epoch ms) from a window's absolute or relative reset fields. */
function resolveResetsAt(win: Record<string, unknown>, nowMs: number): number | null {
  const absolute =
    win.reset_at ??
    win.resets_at ??
    win.resetAt ??
    win.credit_reset_at ??
    win.creditResetAt ??
    win.monthly_reset_at ??
    win.monthlyResetAt ??
    win.period_end ??
    win.periodEnd;
  if (typeof absolute === "string" && absolute.length > 0) {
    const parsed = Date.parse(absolute);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  if (typeof absolute === "number" && Number.isFinite(absolute)) {
    // Values below ~1e12 are epoch seconds; at or above are already milliseconds.
    return absolute < 1e12 ? Math.round(absolute * 1000) : Math.round(absolute);
  }
  const afterSeconds = firstNumber(
    win.reset_after_seconds,
    win.resets_in_seconds,
    win.resetAfterSeconds,
    win.seconds_until_reset,
  );
  if (afterSeconds != null) {
    return nowMs + afterSeconds * 1000;
  }
  return null;
}

/** A parsed window plus its declared duration, used to classify it as the 5-hour or weekly bucket. */
type RawWindow = UsageMetric & { windowSeconds: number | null };

/** Extract a usage metric (and its window duration) from a rate-limit window object, or null when it has no percentage. */
function readWindow(win: unknown, nowMs: number): RawWindow | null {
  const rec = asRecord(win);
  if (!rec) {
    return null;
  }
  const percent = firstNumber(
    rec.used_percent,
    rec.usedPercent,
    rec.utilization,
    rec.percent_used,
    rec.percent,
  );
  if (percent == null) {
    return null;
  }
  const resetsAt = resolveResetsAt(rec, nowMs);
  // The window's own length (verified field `limit_window_seconds`), used to tell
  // a 5-hour "session" window from a 7-day "weekly" one regardless of position.
  const windowSeconds = firstNumber(rec.limit_window_seconds, rec.window_seconds, rec.limitWindowSeconds) ?? null;
  return {
    percent: Math.round(percent),
    resetsIn: resetsAt != null ? formatResetTime(resetsAt) : "N/A",
    resetsAt,
    windowSeconds,
  };
}

/**
 * Locate the two rate-limit windows across the payload shapes. Verified against
 * the live `wham/usage` endpoint (2026-07): the windows are nested under
 * `rate_limit` (SINGULAR) as `primary_window` / `secondary_window`, where a
 * window may be null (e.g. a plan with only a weekly window has a weekly
 * `primary_window` and a null `secondary_window`). Older/alternative shapes
 * (`rate_limits` plural, top-level, five_hour_limit/weekly_limit aliases, an
 * array) are kept as fallbacks so a schema change degrades rather than breaks.
 * The returned windows are position-tagged only; `mapCodexUsageResponse`
 * classifies each as the 5-hour or weekly bucket by its actual duration.
 */
function locateWindows(payload: Record<string, unknown>): { primary: unknown; secondary: unknown } {
  const rl = payload.rate_limit ?? payload.rate_limits ?? payload.rateLimits ?? payload.limits;
  const rlRec = asRecord(rl);
  if (rlRec) {
    return {
      primary: rlRec.primary_window ?? rlRec.primary ?? rlRec.session ?? rlRec.five_hour ?? rlRec.five_hour_limit ?? rlRec["5h"],
      secondary: rlRec.secondary_window ?? rlRec.secondary ?? rlRec.weekly ?? rlRec.weekly_limit ?? rlRec.seven_day ?? rlRec["7d"],
    };
  }
  if (Array.isArray(rl)) {
    return { primary: rl[0], secondary: rl[1] };
  }
  return {
    primary: payload.primary_window ?? payload.primary ?? payload.session ?? payload.five_hour ?? payload.five_hour_limit,
    secondary: payload.secondary_window ?? payload.secondary ?? payload.weekly ?? payload.weekly_limit ?? payload.seven_day,
  };
}

/** Title-case a plan token: "chatgpt_plus" -> "ChatGPT Plus", "pro" -> "Pro". */
function formatPlanLabel(plan: string | undefined): string | undefined {
  if (!plan) {
    return undefined;
  }
  return plan
    .replace(/[_-]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((w) => (w.toLowerCase() === "chatgpt" ? "ChatGPT" : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(" ");
}

/** Map an `additional_rate_limits` array into dashboard rows, skipping unusable entries. */
function readAdditionalLimits(raw: unknown, nowMs: number): UsageMetricRow[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  const rows: UsageMetricRow[] = [];
  for (const entry of raw) {
    const rec = asRecord(entry);
    if (!rec) {
      continue;
    }
    const metric = readWindow(rec, nowMs);
    if (!metric) {
      continue;
    }
    const label = firstNonEmptyString(rec.name, rec.label, rec.window, rec.title) ?? "Additional limit";
    rows.push({ label, percent: metric.percent, resetsIn: metric.resetsIn, resetsAt: metric.resetsAt });
  }
  return rows;
}

/** Build a short credits summary line from the payload's credits block, if any. */
function formatCreditsSummary(raw: unknown): string | undefined {
  const rec = asRecord(raw);
  if (!rec) {
    return undefined;
  }
  if (rec.unlimited === true) {
    return "Credits: unlimited";
  }
  const balance = firstNumber(rec.balance, rec.remaining, rec.amount);
  if (balance != null) {
    return `Credits: ${balance} remaining`;
  }
  if (rec.has_credits === true || rec.hasCredits === true) {
    return "Credits: available";
  }
  return undefined;
}

/** Parse a detailed monthly workspace credit limit from supported payload aliases. */
function readExtraCredits(payload: Record<string, unknown>, nowMs: number): CreditUsageInfo | undefined {
  const credits = asRecord(payload.credits ?? payload.credit_balance);
  const spendControl = asRecord(payload.spend_control ?? payload.spendControl);
  const candidates: unknown[] = [
    spendControl?.individual_limit,
    spendControl?.individualLimit,
    payload.workspace_monthly_credit_limit,
    payload.workspaceMonthlyCreditLimit,
    payload.monthly_credit_limit,
    payload.monthlyCreditLimit,
    payload.workspace_credit_limit,
    payload.workspaceCreditLimit,
    payload.extra_credits,
    payload.extraCredits,
    credits?.workspace_monthly_credit_limit,
    credits?.workspaceMonthlyCreditLimit,
    credits?.monthly_credit_limit,
    credits?.monthlyCreditLimit,
    credits,
    payload,
  ];

  for (const candidate of candidates) {
    const rec = asRecord(candidate);
    if (!rec) {
      continue;
    }

    const monthlyLimit = firstNumber(
      rec.monthly_limit,
      rec.monthlyLimit,
      rec.workspace_monthly_credit_limit,
      rec.workspaceMonthlyCreditLimit,
      rec.credit_limit,
      rec.creditLimit,
      rec.total_credits,
      rec.totalCredits,
      rec.limit,
      rec.total,
    );
    if (monthlyLimit == null || monthlyLimit <= 0) {
      continue;
    }

    const directPercent = firstNumber(rec.used_percent, rec.usedPercent, rec.utilization, rec.percent);
    const remaining = firstNumber(rec.balance, rec.remaining, rec.remaining_credits, rec.remainingCredits);
    let usedCredits = firstNumber(
      rec.used_credits,
      rec.usedCredits,
      rec.credits_used,
      rec.creditsUsed,
      rec.credit_usage,
      rec.creditUsage,
      rec.used,
      rec.consumed,
    );
    if (usedCredits == null && remaining != null) {
      usedCredits = monthlyLimit - remaining;
    }
    if (usedCredits == null && directPercent != null) {
      usedCredits = monthlyLimit * directPercent / 100;
    }
    if (usedCredits == null) {
      continue;
    }

    const normalizedUsed = Math.max(0, usedCredits);
    const percent = Math.round(
      Math.min(100, Math.max(0, directPercent ?? normalizedUsed / monthlyLimit * 100)),
    );
    const usedAmountUsd = firstNumber(
      rec.used_usd,
      rec.usedUsd,
      rec.used_amount_usd,
      rec.usedAmountUsd,
      rec.used_dollars,
      rec.usedDollars,
    );
    const limitAmountUsd = firstNumber(
      rec.limit_usd,
      rec.limitUsd,
      rec.limit_amount_usd,
      rec.limitAmountUsd,
      rec.limit_dollars,
      rec.limitDollars,
    );
    const resetsAt = resolveResetsAt(rec, nowMs) ?? nextMonthlyResetAt(nowMs);
    return {
      usedCredits: normalizedUsed,
      monthlyLimit,
      percent,
      resetsIn: formatResetTime(resetsAt),
      resetsAt,
      ...(usedAmountUsd != null && usedAmountUsd >= 0 && limitAmountUsd != null && limitAmountUsd >= 0
        ? { usedAmountUsd, limitAmountUsd }
        : {}),
    };
  }

  return undefined;
}

/**
 * Map a raw `wham/usage` payload onto the normalized {@link UsageModel}. Verified
 * against the live endpoint (2026-07): the two windows are nested under
 * `rate_limit` (singular) as `primary_window` / `secondary_window`, each carrying
 * `used_percent`, `limit_window_seconds`, and `reset_at` (epoch seconds); either
 * may be null. Each present window is bucketed as the 5-hour "session" or the
 * weekly metric by its own duration, so a weekly-only plan maps correctly.
 * Returns null only when NEITHER window is usable, so the fetcher can fail soft.
 */
export function mapCodexUsageResponse(raw: unknown): UsageModel | null {
  const payload = asRecord(raw);
  if (!payload) {
    return null;
  }
  const now = Date.now();

  const { primary, secondary } = locateWindows(payload);
  const pWin = readWindow(primary, now);
  const sWin = readWindow(secondary, now);

  // Classify each present window as the 5-hour "session" bucket or the weekly
  // bucket by its own declared duration, so a plan that exposes only a weekly
  // window (its single window is 7 days = 604800s) maps to weekly rather than
  // being mislabeled "current session". Windows are optional; an absent one is
  // the untracked sentinel the UI hides. Fall back to position (primary=session,
  // secondary=weekly) only when a window omits its length.
  const SESSION_MAX_SECONDS = 6 * 3600; // longer than a 5-hour window => weekly
  let session: UsageMetric = UNTRACKED_METRIC;
  let weekly: UsageMetric = UNTRACKED_METRIC;
  const assign = (w: RawWindow | null, isPrimaryPosition: boolean): void => {
    if (!w) {
      return;
    }
    const metric: UsageMetric = { percent: w.percent, resetsIn: w.resetsIn, resetsAt: w.resetsAt };
    const isWeekly = w.windowSeconds != null ? w.windowSeconds > SESSION_MAX_SECONDS : !isPrimaryPosition;
    if (isWeekly) {
      weekly = metric;
    } else {
      session = metric;
    }
  };
  assign(pWin, true);
  assign(sWin, false);
  if (!isTracked(session) && !isTracked(weekly)) {
    return null;
  }

  const planLabel = formatPlanLabel(
    firstNonEmptyString(payload.plan_type, payload.planType, payload.plan),
  );
  const additionalLimits = readAdditionalLimits(
    payload.additional_rate_limits ?? payload.additionalRateLimits,
    now,
  );
  const creditsSummary = formatCreditsSummary(payload.credits ?? payload.credit_balance);
  const extraCredits = readExtraCredits(payload, now);

  return {
    session,
    weeklyAllModels: weekly,
    currentModel: planLabel ?? "Codex",
    lastUpdated: now,
    dataSource: "api",
    planLabel: planLabel ?? "Codex",
    ...(additionalLimits.length > 0 ? { additionalLimits } : {}),
    ...(creditsSummary ? { creditsSummary } : {}),
    ...(extraCredits ? { extraCredits } : {}),
  };
}

/**
 * The Codex usage provider: reads the local Codex-app OAuth token and fetches
 * ChatGPT account usage from the undocumented `wham/usage` endpoint, mapping it
 * onto the normalized model. Fail-soft throughout: a missing credential, an
 * unreachable endpoint, or an unrecognized payload yields a typed error, never
 * an exception.
 */
export class CodexUsageProvider implements UsageProvider {
  readonly id = "codex" as const;
  readonly displayName = "Codex";

  /** Resolve the auth-file path from settings, `CODEX_HOME`, and the home dir. */
  private resolveAuthPath(): string {
    const configuredPath = vscode.workspace
      .getConfiguration("codexUsage")
      .get<string>("authPath", "");
    return resolveCodexAuthPath({
      configuredPath,
      codexHome: process.env.CODEX_HOME,
      homeDir: os.homedir(),
    });
  }

  /** Read the internal credential (token carried privately for the fetch). */
  private readCodexCredential(): CodexCredentialReadResult {
    return readCodexCredential(this.resolveAuthPath());
  }

  /** Locate and validate the Codex credential without exposing the token. */
  readCredential(): CredentialResult {
    const result = this.readCodexCredential();
    return result.ok ? { ok: true } : { ok: false, reason: result.reason };
  }

  private fail(code: ProviderFetchErrorCode, extra?: Partial<ProviderFetchError>): ProviderFetchResult {
    return { success: false, error: { code, ...extra } };
  }

  async fetchUsage(_currentModel?: string): Promise<ProviderFetchResult> {
    // Codex usage is account-wide; there is no per-model dimension to pass.
    void _currentModel;

    const read = this.readCodexCredential();
    if (!read.ok) {
      return this.fail(read.reason === "missing" ? "no-credentials" : "invalid-credentials");
    }
    const { accessToken, accountId } = read.credential;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
    };
    // Omit the account-id header for a synthetic (email_/local_) id, matching upstream behavior.
    if (accountId && !isSyntheticAccountId(accountId)) {
      headers["chatgpt-account-id"] = accountId;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch(CODEX_USAGE_URL, { method: "GET", headers, signal: controller.signal });
    } catch {
      // Network failure or timeout (abort). Fail soft.
      return this.fail("network-error");
    } finally {
      clearTimeout(timeoutId);
    }

    if (!response.ok) {
      if (response.status === 401) {
        return this.fail("token-invalid", { statusCode: response.status, statusText: response.statusText });
      }
      if (response.status === 429) {
        return this.fail("rate-limited", { statusCode: response.status, statusText: response.statusText });
      }
      // Any other HTTP status on this undocumented endpoint -> fail soft.
      return this.fail("usage-unavailable", { statusCode: response.status, statusText: response.statusText });
    }

    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      return this.fail("usage-unavailable");
    }

    const model = mapCodexUsageResponse(raw);
    if (!model) {
      return this.fail("usage-unavailable");
    }
    return { success: true, data: model };
  }
}
