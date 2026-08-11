import type {
  BillingOwner,
  AlertCycleState,
  ProviderError,
  ProviderResult,
  UsageSnapshot,
  UsageState
} from "./types";

const SNAPSHOT_KEY = "githubUsageMonitor.snapshot";
const ALERT_CYCLE_KEY = "githubUsageMonitor.alertCycle";

export interface MementoLike {
  get<T>(key: string): T | undefined;
  update(key: string, value: unknown): Thenable<void>;
}

export class UsageStore {
  public constructor(
    private readonly state: MementoLike,
    private readonly staleAfterMs = 30 * 60_000
  ) {}

  public get(now = Date.now()): UsageSnapshot | undefined {
    const snapshot = this.state.get<UsageSnapshot>(SNAPSHOT_KEY);
    return snapshot === undefined ? undefined : refreshSnapshot(snapshot, now, this.staleAfterMs);
  }

  public async saveSuccess(snapshot: UsageSnapshot): Promise<void> {
    await this.state.update(SNAPSHOT_KEY, {
      ...snapshot,
      source: "api",
      stale: false
    });
    await this.syncAlertCycle(snapshot);
  }

  public async saveManualSnapshot(snapshot: UsageSnapshot): Promise<void> {
    await this.state.update(SNAPSHOT_KEY, {
      ...snapshot,
      source: "manual",
      stale: false
    });
  }

  public async clear(): Promise<void> {
    await this.state.update(SNAPSHOT_KEY, undefined);
    await this.state.update(ALERT_CYCLE_KEY, undefined);
  }

  /**
   * Turns a fetch outcome into display state, falling back to cache on failure.
   *
   * `requestedOwner` is what makes the fallback safe. Without it, a failed fetch for
   * one owner served the cached snapshot of a DIFFERENT one: switching from a
   * personal account to an organization whose billing could not be read re-displayed
   * the personal account's minutes and storage under the new owner's name, labelled
   * only as "last-known-good data". That is not staleness, it is the wrong account's
   * numbers - a correctness problem, and arguably a privacy one on a shared machine.
   *
   * A cached snapshot is now served ONLY when it belongs to the owner just requested.
   */
  public async resolveFetch(
    result: ProviderResult<UsageSnapshot>,
    now = Date.now(),
    requestedOwner?: BillingOwner
  ): Promise<UsageState> {
    if (result.ok) {
      await this.saveSuccess(result.value);
      return { state: "fresh", data: result.value };
    }
    const cached = this.get(now);
    const sameOwner =
      cached !== undefined &&
      (requestedOwner === undefined ||
        (cached.owner.scope === requestedOwner.scope &&
          cached.owner.name.toLowerCase() === requestedOwner.name.toLowerCase()));
    if (cached !== undefined && sameOwner) {
      return {
        state: "stale",
        data: { ...cached, source: "cache", stale: true },
        error: result.error
      };
    }
    return { state: "empty", error: result.error };
  }

  public hasExpiredReset(now = Date.now()): boolean {
    const snapshot = this.state.get<UsageSnapshot>(SNAPSHOT_KEY);
    if (snapshot === undefined) {
      return false;
    }
    return [snapshot.copilot, snapshot.actionsMinutes, snapshot.actionsStorage].some(
      (metric) => metric.reset !== null && metric.reset.at <= now && snapshot.fetchedAt < metric.reset.at
    );
  }

  public getAlertCycle(): AlertCycleState | undefined {
    return this.state.get<AlertCycleState>(ALERT_CYCLE_KEY);
  }

  public async markThresholdNotified(threshold: number): Promise<void> {
    const current = this.getAlertCycle();
    if (current === undefined || current.notifiedThresholds.includes(threshold)) {
      return;
    }
    await this.state.update(ALERT_CYCLE_KEY, {
      ...current,
      notifiedThresholds: [...current.notifiedThresholds, threshold].sort((left, right) => left - right)
    });
  }

  private async syncAlertCycle(snapshot: UsageSnapshot): Promise<void> {
    const cycleId = cycleIdFor(snapshot);
    const current = this.getAlertCycle();
    if (current === undefined) {
      await this.state.update(ALERT_CYCLE_KEY, { cycleId, notifiedThresholds: [] });
      return;
    }
    if (current.cycleId !== cycleId && snapshot.source === "api") {
      await this.state.update(ALERT_CYCLE_KEY, { cycleId, notifiedThresholds: [] });
    }
  }
}

export function refreshSnapshot(
  snapshot: UsageSnapshot,
  now: number,
  staleAfterMs: number
): UsageSnapshot {
  return {
    ...snapshot,
    stale: now - snapshot.fetchedAt >= staleAfterMs
  };
}

/**
 * Absolute reset date and time, matching the sibling monitors.
 *
 * v3.16.3 showed only a countdown ("511h 41m"), which is unreadable at this
 * magnitude - a monthly billing period is three weeks out, and nobody converts 511
 * hours into a date in their head. The siblings show when the period actually ends,
 * so this does too. The countdown remains available for short horizons.
 */
export function formatResetDateTime(resetAt: number, locale?: string): string {
  const date = new Date(resetAt);
  if (!Number.isFinite(resetAt) || Number.isNaN(date.getTime())) return "not reported";
  return new Intl.DateTimeFormat(locale ?? "en-US", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit"
  }).format(date);
}

export function formatResetCountdown(resetAt: number, now = Date.now()): string {
  const remaining = resetAt - now;
  if (remaining <= 0) {
    return "refresh due";
  }
  const minutes = Math.ceil(remaining / 60_000);
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder === 0 ? `${hours}h` : `${hours}h ${remainder}m`;
}

export function describeFallback(error: ProviderError, hasCache: boolean): string {
  return hasCache
    ? `${error.message} Showing last-known-good cached data.`
    : `${error.message} No usage data is available yet.`;
}

function cycleIdFor(snapshot: UsageSnapshot): string {
  return `${snapshot.owner.scope}:${snapshot.owner.name}:${snapshot.periodStart}`;
}
