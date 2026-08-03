import type {
  AlertCycleState,
  ProviderError,
  ProviderResult,
  UsageSnapshot,
  UsageState
} from "./types";

const SNAPSHOT_KEY = "githubUsage.snapshot";
const ALERT_CYCLE_KEY = "githubUsage.alertCycle";

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

  public async resolveFetch(
    result: ProviderResult<UsageSnapshot>,
    now = Date.now()
  ): Promise<UsageState> {
    if (result.ok) {
      await this.saveSuccess(result.value);
      return { state: "fresh", data: result.value };
    }
    const cached = this.get(now);
    if (cached !== undefined) {
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
