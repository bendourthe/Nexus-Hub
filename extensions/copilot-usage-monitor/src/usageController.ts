import * as vscode from "vscode";
import type { ProviderFetchError } from "./providers/types";
import { CONFIG_SECTION, UsageData } from "./types";
import { UsageService, UsageFetchResult } from "./usageService";
import { removeUsageState, usageStatePath, writeUsageState } from "./usageStateFile";
import type { UsageStore } from "./usageStore";

/** Failures that say nothing about the figure itself: keep the last good one, marked stale. */
const TRANSIENT_CODES: ReadonlySet<string> = new Set([
  "rate-limited",
  "network-error",
  "api-error",
  "usage-unavailable",
  "parse-error",
]);

/** Personal failures that mean the signed-in account is unavailable. */
const SIGNED_OUT_CODES: ReadonlySet<string> = new Set(["no-credentials", "choose-account", "token-invalid"]);

/**
 * When one half of a fetch fails transiently (429, 5xx, network, an
 * unrecognized body), carry that half's previous figure forward with
 * `stale: true` and its original `fetchedAt`, so the headline does not fall
 * back and the guard does not go silent near a limit. A token rejection,
 * access denial, or sign-out drops the figure instead.
 */
export function retainTransient(next: UsageData, previous: UsageData | undefined): UsageData {
  const merged: UsageData = { ...next };
  if (!merged.organization && merged.organizationError && TRANSIENT_CODES.has(merged.organizationError.code) && previous?.organization) {
    merged.organization = {
      ...previous.organization,
      stale: true,
      fetchedAt: previous.organization.fetchedAt ?? previous.lastUpdated,
    };
  }
  if (!merged.personal && merged.personalError && TRANSIENT_CODES.has(merged.personalError.code) && previous?.personal) {
    merged.personal = {
      ...previous.personal,
      stale: true,
      fetchedAt: previous.personal.fetchedAt ?? previous.lastUpdated,
    };
  }
  return merged;
}

/** The status-bar surface the controller drives (the real StatusBarManager satisfies it). */
export interface StatusSurface {
  refresh(): void;
  setLastError(error: ProviderFetchError | undefined): void;
  applyBackoff(): void;
  resetBackoff(): void;
}

/**
 * One refresh cycle: fetch both halves, cache the result, write the
 * percentages-only state file, and redraw the status bar. Notifications and
 * the dashboard stay in extension.ts; everything here runs under the test stub.
 */
export class UsageController {
  lastFetchError: ProviderFetchError | undefined;
  consecutiveFailures = 0;
  private inFlight: Promise<UsageFetchResult> | undefined;

  constructor(
    private readonly store: UsageStore,
    private readonly service: UsageService,
    private readonly statusBar: StatusSurface,
    private readonly statePath: string = usageStatePath(),
  ) {}

  /** Concurrent callers share one fetch. */
  refresh(nowMs = Date.now()): Promise<UsageFetchResult> {
    this.inFlight ??= this.run(nowMs).finally(() => {
      this.inFlight = undefined;
    });
    return this.inFlight;
  }

  private async run(nowMs: number): Promise<UsageFetchResult> {
    const result = await this.service.fetchAll(nowMs);
    const previous = this.store.get();
    if (result.success) {
      this.consecutiveFailures = 0;
      this.lastFetchError = undefined;
      const data = retainTransient(result.data, previous);
      await this.store.save(data);
      this.writeState(data, nowMs);
    } else {
      this.consecutiveFailures += 1;
      this.lastFetchError = result.error;
      // The account is gone or rejected: a personal figure from it must not
      // keep feeding the guard. A cached organization figure still may.
      if (SIGNED_OUT_CODES.has(result.error.code) && !previous?.organization) {
        this.removeState();
      }
    }
    if (result.rateLimited) {
      this.statusBar.applyBackoff();
    } else if (result.success) {
      this.statusBar.resetBackoff();
    }
    this.statusBar.setLastError(this.lastFetchError);
    this.statusBar.refresh();
    return result;
  }

  /** Write (or remove) the state file for `data`, honoring `copilotUsage.writeUsageState`. */
  writeState(data: UsageData | undefined, nowMs = Date.now()): void {
    if (!this.writingEnabled()) {
      return;
    }
    writeUsageState(data, this.statePath, nowMs);
  }

  private writingEnabled(): boolean {
    return vscode.workspace.getConfiguration(CONFIG_SECTION).get<boolean>("writeUsageState", true) !== false;
  }

  private removeState(): void {
    if (this.writingEnabled()) {
      removeUsageState(this.statePath);
    }
  }

  /** After a disconnect, drop the organization figure and rewrite the file from the personal one. */
  async organizationRemoved(): Promise<void> {
    const data = this.store.get();
    if (data) {
      const { organization: _org, organizationError: _err, ...rest } = data;
      void _org;
      void _err;
      await this.store.save(rest);
      this.writeState(rest);
    } else {
      removeUsageState(this.statePath);
    }
    this.statusBar.refresh();
  }

  /** Clear Data: forget the cache and delete the state file, since no figure remains. */
  async clear(): Promise<void> {
    await this.store.clear();
    removeUsageState(this.statePath);
    this.lastFetchError = undefined;
    this.statusBar.setLastError(undefined);
    this.statusBar.refresh();
  }

  /** The user turned `writeUsageState` off: remove the file the guard would otherwise read. */
  stateWritingDisabled(): void {
    removeUsageState(this.statePath);
  }
}
