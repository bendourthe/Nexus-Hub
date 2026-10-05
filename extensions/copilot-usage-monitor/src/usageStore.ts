import * as vscode from "vscode";
import { UsageData, UrgencyLevel } from "./types";

const STORAGE_KEY = "copilotUsageData";
const URGENCY_KEY = "copilotLastUrgency";

/**
 * Cached usage in VS Code globalState. The stored model carries plan labels and
 * figures only, never a login, organization name, or token (the providers do not
 * put one into it).
 */
export class UsageStore {
  constructor(private readonly globalState: vscode.Memento) {}

  get(): UsageData | undefined {
    return this.globalState.get<UsageData>(STORAGE_KEY);
  }

  async save(data: UsageData): Promise<void> {
    await this.globalState.update(STORAGE_KEY, data);
  }

  async clear(): Promise<void> {
    await this.globalState.update(STORAGE_KEY, undefined);
    await this.globalState.update(URGENCY_KEY, undefined);
  }

  getLastUrgency(): UrgencyLevel | undefined {
    return this.globalState.get<UrgencyLevel>(URGENCY_KEY);
  }

  async saveLastUrgency(level: UrgencyLevel): Promise<void> {
    await this.globalState.update(URGENCY_KEY, level);
  }

  /** True once a cached monthly reset has passed since the last fetch. */
  hasResetExpired(nowMs = Date.now()): boolean {
    const data = this.get();
    if (!data) {
      return false;
    }
    const resets = [data.personal?.resetsAt, data.organization?.resetsAt].filter(
      (value): value is number => value != null,
    );
    return resets.some((at) => at <= nowMs && data.lastUpdated < at);
  }

  getTimeSinceUpdate(nowMs = Date.now()): string {
    const data = this.get();
    return data ? formatElapsed(nowMs - data.lastUpdated) : "never";
  }
}

export function formatElapsed(elapsedMs: number): string {
  const minutes = Math.floor(elapsedMs / 60_000);
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

/**
 * A percentage for display: a whole number, as the Claude and Codex monitors
 * show it (v4.13.8). 1.3 -> "1", 99.25 -> "99", 100 -> "100". The value itself
 * stays unrounded everywhere it is compared against a threshold.
 */
export function formatPercent(percent: number): string {
  const clamped = Math.min(100, Math.max(0, percent));
  return String(Math.round(clamped));
}

/**
 * A share for a breakdown row: whole numbers like {@link formatPercent}, but a
 * non-zero share that rounds to 0 reads "<1" so small rows stay distinguishable.
 */
export function formatShare(percent: number): string {
  const whole = formatPercent(percent);
  return whole === "0" && percent > 0 ? "<1" : whole;
}

/** "Shared organization pool usage: 172 / 13,300 credits": used and total, both whole. */
export function poolUsageLine(used: number, total: number): string {
  return `Shared organization pool usage: ${formatCreditCount(Math.round(used))} / ${formatCreditCount(total)} credits`;
}

/** Used credits with two decimals, as the organization AI usage page's breakdown shows them. */
export function formatCredits(value: number): string {
  return new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

/** A whole-number credit count, e.g. a pool total of 13,300. */
export function formatCreditCount(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

/** Epoch ms of the first day of the next calendar month, 00:00:00 UTC. */
export function nextMonthlyResetAt(nowMs = Date.now()): number {
  const now = new Date(nowMs);
  return Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1);
}

/** "Resets on November 1" for a monthly reset; "Reset date not reported" when GitHub gave none. */
export function formatResetLabel(resetsAt: number | null): string {
  if (resetsAt == null) {
    return "Reset date not reported";
  }
  const date = new Date(resetsAt).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
  return `Resets on ${date}`;
}
