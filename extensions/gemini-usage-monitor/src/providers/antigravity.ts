import * as vscode from "vscode";
import { UsageMetric, UsageMetricRow, UNTRACKED_METRIC, isTracked } from "../types";
import { formatResetTime } from "../usageStore";
import { UsageProvider, UsageModel, ProviderFetchError, ProviderFetchErrorCode, ProviderFetchResult } from "./types";
import {
  QUOTA_SUMMARY_METHOD,
  USER_STATUS_METHOD,
  ServerEndpoint,
  discoverEndpoint,
  postRpc,
  readServerCa,
} from "./languageServer";

/* ------------------------------------------------------------------ */
/*  RetrieveUserQuotaSummary mapping                                   */
/*                                                                     */
/*  Shape recorded from a live Antigravity IDE 2.5.5 response          */
/*  (2026-10-14): response.groups[] of { displayName, description,     */
/*  buckets[] }, each bucket { window: "weekly" | "5h", displayName,   */
/*  remainingFraction (0..1, omitted when exhausted), resetTime (ISO), */
/*  disabled? }. Antigravity shows REMAINING; every Nexus-Hub monitor  */
/*  shows USED, so the fraction is inverted here.                      */
/* ------------------------------------------------------------------ */

function asRecord(value: unknown): Record<string, unknown> | null {
  return value != null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function str(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

/** Which window a bucket measures, by its `window` id first and its label second. */
export function bucketWindow(bucket: Record<string, unknown>): "session" | "weekly" | null {
  const id = (str(bucket.window) ?? "").toLowerCase();
  if (id === "5h" || id.includes("hour")) {
    return "session";
  }
  if (id.includes("week")) {
    return "weekly";
  }
  const label = (str(bucket.displayName) ?? "").toLowerCase();
  if (/five.?hour|5.?h/.test(label)) {
    return "session";
  }
  return /week/.test(label) ? "weekly" : null;
}

/**
 * Convert one bucket into a USED-percent metric. A disabled bucket is untracked
 * (the panel hides its figure). A missing `remainingFraction` is read as 0
 * remaining, which is how Antigravity's own panel renders it ("0%").
 */
export function readBucket(bucket: Record<string, unknown>): UsageMetric {
  if (bucket.disabled === true) {
    return UNTRACKED_METRIC;
  }
  const raw = bucket.remainingFraction;
  const remaining = typeof raw === "number" && Number.isFinite(raw) ? Math.min(1, Math.max(0, raw)) : 0;
  const parsed = typeof bucket.resetTime === "string" ? Date.parse(bucket.resetTime) : NaN;
  const resetsAt = Number.isNaN(parsed) ? null : parsed;
  return {
    percent: Math.round((1 - remaining) * 100),
    resetsIn: resetsAt != null ? formatResetTime(resetsAt) : "N/A",
    resetsAt,
  };
}

interface QuotaGroup {
  name: string;
  session: UsageMetric;
  weekly: UsageMetric;
  /** Buckets whose window could not be classified, kept under their own label. */
  other: UsageMetricRow[];
}

function hasFraction(bucket: Record<string, unknown>): boolean {
  return typeof bucket.remainingFraction === "number" && Number.isFinite(bucket.remainingFraction);
}

function readGroup(rec: Record<string, unknown>, buckets: unknown[]): QuotaGroup {
  const group: QuotaGroup = { name: str(rec.displayName) ?? "Models", session: UNTRACKED_METRIC, weekly: UNTRACKED_METRIC, other: [] };
  let sessionServed = false;
  for (const b of buckets) {
    const bucket = asRecord(b);
    if (!bucket) {
      continue;
    }
    const which = bucketWindow(bucket);
    if (which) {
      group[which] = readBucket(bucket);
      if (which === "session") {
        sessionServed = hasFraction(bucket);
      }
      continue;
    }
    const label = str(bucket.displayName);
    if (label && bucket.disabled !== true && hasFraction(bucket)) {
      group.other.push({ label, ...readBucket(bucket) });
    }
  }
  // Antigravity leaves the five-hour figure blank while the weekly limit is spent
  // ("the 5-hour limit does not currently apply"); that is not 100% used.
  if (!sessionServed && isTracked(group.session) && isTracked(group.weekly) && group.weekly.percent >= 100) {
    group.session = UNTRACKED_METRIC;
  }
  return group;
}

function readGroups(summary: unknown): QuotaGroup[] {
  const root = asRecord(summary);
  const response = asRecord(root?.response) ?? root;
  const groups = response?.groups;
  if (!Array.isArray(groups)) {
    return [];
  }
  const out: QuotaGroup[] = [];
  for (const g of groups) {
    const rec = asRecord(g);
    if (!rec || !Array.isArray(rec.buckets)) {
      continue;
    }
    const group = readGroup(rec, rec.buckets);
    if (isTracked(group.session) || isTracked(group.weekly) || group.other.length > 0) {
      out.push(group);
    }
  }
  return out;
}

/**
 * The headline group: the panel's own "Gemini Models" first, so a narrower
 * group such as "Gemini 4 Argon" never takes over the status bar by order alone.
 */
export function pickPrimaryGroup<T extends { name: string; session: UsageMetric; weekly: UsageMetric }>(groups: T[]): T {
  return (
    groups.find((g) => /^gemini models$/i.test(g.name.trim())) ??
    groups.find((g) => /gemini/i.test(g.name) && isTracked(g.session) && isTracked(g.weekly)) ??
    groups.find((g) => /gemini/i.test(g.name)) ??
    groups[0]
  );
}

/** "Claude and GPT models" -> "Claude and GPT Models", matching the panel's own "Gemini Models". */
function titleGroup(name: string): string {
  return name.replace(/\bmodels\b/, "Models");
}

/** Read the plan label ("Google AI Pro") from a GetUserStatus response, if present. */
export function readPlanLabel(userStatus: unknown): string | undefined {
  const status = asRecord(asRecord(userStatus)?.userStatus);
  return str(asRecord(status?.userTier)?.description);
}

/**
 * Map a quota summary (and optional user status) onto the shared usage model.
 * The Gemini group becomes the headline session/weekly pair; every other group
 * becomes extra rows, which the alert logic also evaluates. Returns null when no
 * group carries a usable window.
 */
export function mapQuotaSummary(summary: unknown, userStatus?: unknown, now = Date.now()): UsageModel | null {
  const groups = readGroups(summary);
  if (groups.length === 0) {
    return null;
  }
  const primary = pickPrimaryGroup(groups);
  const additionalLimits: UsageMetricRow[] = [];
  for (const g of groups) {
    const name = titleGroup(g.name);
    if (g !== primary) {
      if (isTracked(g.session)) {
        additionalLimits.push({ label: `${name}: Current Session`, ...g.session });
      }
      if (isTracked(g.weekly)) {
        additionalLimits.push({ label: `${name}: Weekly`, ...g.weekly });
      }
    }
    for (const row of g.other) {
      additionalLimits.push({ ...row, label: `${name}: ${row.label}` });
    }
  }
  const planLabel = readPlanLabel(userStatus) ?? "Antigravity";
  return {
    session: primary.session,
    weeklyAllModels: primary.weekly,
    currentModel: titleGroup(primary.name),
    lastUpdated: now,
    dataSource: "api",
    planLabel,
    ...(additionalLimits.length > 0 ? { additionalLimits } : {}),
  };
}

/**
 * The Antigravity usage provider: asks the running Antigravity language server,
 * over loopback, for the same quota summary its Models & Usage panel shows. The
 * discovered endpoint is cached and rediscovered after any failure (the server
 * picks new random ports when it restarts). Fail-soft: never throws.
 */
export class AntigravityUsageProvider implements UsageProvider {
  readonly id = "antigravity" as const;
  readonly displayName = "Antigravity";
  private endpoint: ServerEndpoint | undefined;

  constructor(private readonly appRoot: string = vscode.env.appRoot) {}

  private fail(code: ProviderFetchErrorCode, extra?: Partial<ProviderFetchError>): { success: false; error: ProviderFetchError } {
    return { success: false, error: { code, ...extra } };
  }

  async fetchUsage(forceRefresh = false): Promise<ProviderFetchResult> {
    const raw = await this.fetchRawUsage(forceRefresh);
    if (!raw.success) {
      return raw;
    }
    const model = mapQuotaSummary(raw.raw.summary, raw.raw.userStatus);
    return model ? { success: true, data: model } : this.fail("usage-unavailable");
  }

  /**
   * The quota summary plus the user status, unmapped. Shared by {@link fetchUsage}
   * and the opt-in "Save Raw Usage Response" command so both send the same calls.
   * `forceRefresh` asks the server to re-read Google's quota service, exactly as
   * the refresh arrow in Antigravity's own panel does.
   */
  async fetchRawUsage(
    forceRefresh = false,
  ): Promise<{ success: true; raw: { summary: unknown; userStatus: unknown } } | { success: false; error: ProviderFetchError }> {
    for (let attempt = 0; attempt < 2; attempt++) {
      if (!this.endpoint) {
        const found = await discoverEndpoint(this.appRoot);
        if (!found.ok) {
          return this.fail(found.reason);
        }
        this.endpoint = found.endpoint;
      }
      const ca = this.endpoint.scheme === "https" ? readServerCa(this.appRoot) : undefined;
      const summary = await postRpc(this.endpoint, QUOTA_SUMMARY_METHOD, { forceRefresh }, ca);
      if (summary?.status === 200 && summary.body != null) {
        const status = await postRpc(this.endpoint, USER_STATUS_METHOD, {}, ca);
        return { success: true, raw: { summary: summary.body, userStatus: status?.status === 200 ? status.body : undefined } };
      }
      // The server restarted (new port/token) or rejected the call: rediscover once.
      this.endpoint = undefined;
      if (summary && summary.status !== 200 && attempt === 1) {
        return this.fail("api-error", { statusCode: summary.status });
      }
    }
    return this.fail("server-unreachable");
  }
}
