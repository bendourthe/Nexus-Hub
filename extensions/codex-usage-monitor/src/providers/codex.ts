import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as vscode from "vscode";
import { UsageMetric, UsageMetricRow } from "../types";
import { formatResetTime } from "../usageStore";
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
/*  The endpoint is undocumented, so every accessor below is defensive */
/*  and tolerant of shape variation. The mapper returns null when it   */
/*  cannot find a usable primary window, which the fetcher turns into  */
/*  the fail-soft "usage-unavailable" state.                           */
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
  const absolute = win.reset_at ?? win.resets_at ?? win.resetAt;
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

/** Extract a usage metric from a rate-limit window object, or null when it has no percentage. */
function readWindow(win: unknown, nowMs: number): UsageMetric | null {
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
  return {
    percent: Math.round(percent),
    resetsIn: resetsAt != null ? formatResetTime(resetsAt) : "N/A",
    resetsAt,
  };
}

/** Locate the primary and secondary rate-limit windows across plausible payload shapes. */
function locateWindows(payload: Record<string, unknown>): { primary: unknown; secondary: unknown } {
  const rl = payload.rate_limits ?? payload.rateLimits ?? payload.limits;
  const rlRec = asRecord(rl);
  if (rlRec) {
    return {
      primary: rlRec.primary ?? rlRec.session ?? rlRec.five_hour ?? rlRec["5h"],
      secondary: rlRec.secondary ?? rlRec.weekly ?? rlRec.seven_day ?? rlRec["7d"],
    };
  }
  if (Array.isArray(rl)) {
    return { primary: rl[0], secondary: rl[1] };
  }
  return {
    primary: payload.primary ?? payload.session ?? payload.five_hour,
    secondary: payload.secondary ?? payload.weekly ?? payload.seven_day,
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

/**
 * Map a raw `wham/usage` payload onto the normalized {@link UsageModel}. Returns
 * null when no usable primary window is present, so the fetcher can fail soft.
 * The primary window becomes the session metric and the secondary window the
 * weekly metric, matching what the UI already renders.
 */
export function mapCodexUsageResponse(raw: unknown): UsageModel | null {
  const payload = asRecord(raw);
  if (!payload) {
    return null;
  }
  const now = Date.now();

  const { primary, secondary } = locateWindows(payload);
  const session = readWindow(primary, now);
  if (!session) {
    return null;
  }
  const weekly = readWindow(secondary, now) ?? { percent: 0, resetsIn: "N/A", resetsAt: null };

  const planLabel = formatPlanLabel(
    firstNonEmptyString(payload.plan_type, payload.planType, payload.plan),
  );
  const additionalLimits = readAdditionalLimits(
    payload.additional_rate_limits ?? payload.additionalRateLimits,
    now,
  );
  const creditsSummary = formatCreditsSummary(payload.credits ?? payload.credit_balance);

  return {
    session,
    weeklyAllModels: weekly,
    currentModel: planLabel ?? "Codex",
    lastUpdated: now,
    dataSource: "api",
    planLabel: planLabel ?? "Codex",
    ...(additionalLimits.length > 0 ? { additionalLimits } : {}),
    ...(creditsSummary ? { creditsSummary } : {}),
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
