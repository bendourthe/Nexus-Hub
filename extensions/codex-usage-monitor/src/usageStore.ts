import * as vscode from "vscode";
import {
  UsageData,
  CreditUsageInfo,
  UsageMetric,
  UrgencyLevel,
  SuggestionState,
  DEFAULT_SUGGESTION_STATE,
} from "./types";

const STORAGE_KEY = "codexUsageData";
const URGENCY_KEY = "codexLastUrgency";
const SUGGESTION_KEY = "codexSuggestionState";

export class UsageStore {
  constructor(private readonly globalState: vscode.Memento) {}

  get(): UsageData | undefined {
    return this.globalState.get<UsageData>(STORAGE_KEY);
  }

  getWithFreshCountdowns(): UsageData | undefined {
    const data = this.get();
    if (!data) {
      return undefined;
    }
    return {
      ...data,
      session: refreshMetricCountdown(data.session),
      weeklyAllModels: refreshMetricCountdown(data.weeklyAllModels),
      ...(data.extraCredits ? { extraCredits: refreshMetricCountdown(data.extraCredits) } : {}),
    };
  }

  async save(data: UsageData): Promise<void> {
    await this.globalState.update(STORAGE_KEY, data);
  }

  async clear(): Promise<void> {
    await this.globalState.update(STORAGE_KEY, undefined);
    await this.globalState.update(URGENCY_KEY, undefined);
    await this.globalState.update(SUGGESTION_KEY, undefined);
  }

  getLastUrgency(): UrgencyLevel | undefined {
    return this.globalState.get<UrgencyLevel>(URGENCY_KEY);
  }

  async saveLastUrgency(level: UrgencyLevel): Promise<void> {
    await this.globalState.update(URGENCY_KEY, level);
  }

  hasResetExpired(): boolean {
    const data = this.get();
    if (!data) {
      return false;
    }
    const now = Date.now();
    const metrics = [data.session, data.weeklyAllModels, data.extraCredits].filter(
      (metric): metric is UsageMetric => metric != null,
    );
    return metrics.some(
      (m) => m.resetsAt != null && m.resetsAt <= now && data.lastUpdated < m.resetsAt
    );
  }

  getTimeSinceUpdate(): string {
    const data = this.get();
    if (!data) {
      return "never";
    }

    const elapsed = Date.now() - data.lastUpdated;
    const minutes = Math.floor(elapsed / 60_000);

    if (minutes < 1) {
      return "just now";
    }
    if (minutes < 60) {
      return `${minutes} min ago`;
    }

    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `${hours}h ago`;
    }

    return `${Math.floor(hours / 24)}d ago`;
  }

  /* ---------------------------------------------------------------- */
  /*  Suggestion notification state                                   */
  /* ---------------------------------------------------------------- */

  getSuggestionState(): SuggestionState {
    return this.globalState.get<SuggestionState>(SUGGESTION_KEY) ?? { ...DEFAULT_SUGGESTION_STATE };
  }

  async saveSuggestionState(state: SuggestionState): Promise<void> {
    await this.globalState.update(SUGGESTION_KEY, state);
  }

}

function refreshMetricCountdown<T extends UsageMetric>(metric: T): T {
  if (metric.resetsAt == null) {
    return metric;
  }
  return { ...metric, resetsIn: formatResetTime(metric.resetsAt) };
}

export function formatResetTime(epochMs: number): string {
  const diffMs = epochMs - Date.now();

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

  // 24h+ away (the weekly limit): show the concrete date and time plus the
  // compact remaining duration, e.g. "Tuesday July 7th at 6:59 AM (3d 4h 15m)".
  const resetDate = new Date(epochMs);
  const weekday = resetDate.toLocaleDateString("en-US", { weekday: "long" });
  const month = resetDate.toLocaleDateString("en-US", { month: "long" });
  const time = resetDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
  const days = Math.floor(diffHours / 24);
  const hours = diffHours % 24;
  const mins = diffMinutes % 60;
  return `${weekday} ${month} ${ordinal(resetDate.getDate())} at ${time} (${days}d ${hours}h ${mins}m)`;
}

/**
 * Prefix a resetsIn value with the right verb form so every surface (dashboard,
 * status-bar tooltip, notifications) reads the same way:
 *   "2h 38m"                        → "Resets in 2h 38m"
 *   "Tuesday July 7th at 7:00 AM…"  → "Resets on Tuesday July 7th at 7:00 AM…"
 *   "August 1"                      → "Resets on August 1"   (monthly credits)
 *   "N/A" / "any moment"            → "Resets N/A" / "Resets any moment"
 */
export function formatResetLabel(resetsIn: string): string {
  if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/.test(resetsIn)) {
    return `Resets on ${resetsIn}`;
  }
  if (resetsIn === "N/A" || resetsIn === "any moment") {
    return `Resets ${resetsIn}`;
  }
  return `Resets in ${resetsIn}`;
}

/**
 * Month-name-first label for the first day of next month, e.g. "August 1".
 * Passed through formatResetLabel it reads "Resets on August 1". Extra credits
 * reset monthly, so this is the reset label for the Extra Credits sections in
 * both the dashboard and the status-bar tooltip.
 */
export function nextMonthlyResetLabel(): string {
  const now = new Date();
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return next.toLocaleDateString("en-US", { month: "long", day: "numeric" });
}

/** Epoch milliseconds for the next calendar-month boundary in UTC. */
export function nextMonthlyResetAt(nowMs = Date.now()): number {
  const now = new Date(nowMs);
  return Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1);
}

/** Format a credit count for compact user-facing amount lines. */
export function formatCreditCount(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

/** Format the shared Extra Credits usage line without deriving a currency conversion. */
export function formatCreditUsageLine(credits: CreditUsageInfo): string {
  const creditText = `${formatCreditCount(credits.usedCredits)} out of ${formatCreditCount(credits.monthlyLimit)} credits used`;
  if (
    credits.usedAmountUsd == null ||
    credits.limitAmountUsd == null ||
    !Number.isFinite(credits.usedAmountUsd) ||
    !Number.isFinite(credits.limitAmountUsd) ||
    credits.usedAmountUsd < 0 ||
    credits.limitAmountUsd < 0
  ) {
    return creditText;
  }

  const usd = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${creditText} (${usd.format(credits.usedAmountUsd)} / ${usd.format(credits.limitAmountUsd)})`;
}

/** 1 → "1st", 2 → "2nd", 7 → "7th", 11 → "11th", 22 → "22nd". */
function ordinal(n: number): string {
  const rem10 = n % 10;
  const rem100 = n % 100;
  if (rem10 === 1 && rem100 !== 11) {
    return `${n}st`;
  }
  if (rem10 === 2 && rem100 !== 12) {
    return `${n}nd`;
  }
  if (rem10 === 3 && rem100 !== 13) {
    return `${n}rd`;
  }
  return `${n}th`;
}
