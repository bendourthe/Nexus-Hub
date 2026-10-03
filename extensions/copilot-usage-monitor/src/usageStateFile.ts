import * as crypto from "crypto";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { logOnce } from "./log";
import { headlineOf, UsageData } from "./types";

/**
 * The percentages-only file the Nexus-Hub usage-guard hook reads through
 * `catalog/hooks/_usage_probe.py` `read_copilot` (decision file v4.13.7,
 * Copilot usage monitor item (6)). It carries percentages, reset times, the
 * figure's source, and the approximate flag: no login, organization name,
 * account id, email, token, or raw response.
 */
export interface UsageStateWindow {
  name: "monthly";
  percent: number;
  resets_at: string | null;
  source: "personal" | "organization";
}

export interface UsageStateFile {
  schema_version: 1;
  provider: "copilot";
  fetched_at: string;
  approximate: boolean;
  /**
   * Present and true only when the figure is the last good one, kept after a
   * transient fetch failure. `fetched_at` is then that figure's own fetch time,
   * so the probe's 30-minute rule still ages it out. The probe ignores the key.
   */
  stale?: true;
  windows: UsageStateWindow[];
}

/** The probe treats a file older than this as unavailable (`COPILOT_MAX_AGE_SECONDS`). */
export const PROBE_MAX_AGE_MS = 30 * 60_000;

/** `$NEXUS_HOME/state/usage-probe/copilot.json`, else `~/.nexus-hub/state/usage-probe/copilot.json`, as the probe resolves it. */
export function usageStatePath(env: NodeJS.ProcessEnv = process.env, homeDir: string = os.homedir()): string {
  const override = env.NEXUS_HOME?.trim();
  const base = override ? override : path.join(homeDir, ".nexus-hub");
  return path.join(base, "state", "usage-probe", "copilot.json");
}

function isoSeconds(epochMs: number): string {
  return new Date(epochMs).toISOString().replace(/\.\d{3}Z$/, "Z");
}

/**
 * Build the file contents with the status bar's precedence (organization pool,
 * else personal plan). Returns null when no percentage exists, such as a
 * Business or Enterprise member without billing access: then no file is
 * written. Returns "too-old" for a kept (stale) figure older than the probe's
 * 30-minute limit, which is then not rewritten.
 */
export function buildUsageState(data: UsageData | undefined, nowMs = Date.now()): UsageStateFile | null | "too-old" {
  const headline = headlineOf(data);
  if (!data || headline.kind !== "percent") {
    return null;
  }
  if (headline.stale && nowMs - headline.fetchedAt > PROBE_MAX_AGE_MS) {
    return "too-old";
  }
  return {
    schema_version: 1,
    provider: "copilot",
    fetched_at: isoSeconds(headline.fetchedAt),
    approximate: headline.approximate,
    ...(headline.stale ? { stale: true as const } : {}),
    windows: [
      {
        name: "monthly",
        percent: Math.round(Math.min(100, Math.max(0, headline.percent)) * 100) / 100,
        resets_at: headline.resetsAt != null ? isoSeconds(headline.resetsAt) : null,
        source: headline.source,
      },
    ],
  };
}

/** Remove the file if present. Never throws. */
export function removeUsageState(filePath: string = usageStatePath()): void {
  try {
    fs.rmSync(filePath, { force: true });
  } catch {
    logOnce("state-remove-failed", "Could not remove the Copilot usage state file; the usage guard ignores it after 30 minutes.");
  }
}

/** The filesystem calls the writer makes, injectable so the Windows retry is testable. */
export interface StateFileIo {
  rename(from: string, to: string): void;
  platform: NodeJS.Platform;
}

const defaultIo: StateFileIo = { rename: (from, to) => fs.renameSync(from, to), platform: process.platform };

/** Block briefly without an event loop turn (the writer is synchronous). */
function pause(ms: number): void {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/**
 * Rename into place. On Windows a reader or antivirus scan can hold the target
 * open for a moment, which fails the rename with EPERM, EACCES, or EBUSY; one
 * retry after 50 ms covers that.
 */
function renameIntoPlace(from: string, to: string, io: StateFileIo): void {
  try {
    io.rename(from, to);
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (io.platform !== "win32" || (code !== "EPERM" && code !== "EACCES" && code !== "EBUSY")) {
      throw error;
    }
    pause(50);
    io.rename(from, to);
  }
}

/**
 * Write the file atomically: the JSON goes to a temporary sibling that is then
 * renamed over the target, so a reader (or a second VS Code window) sees the
 * old file or the new one, never a partial one. When `data` has no percentage
 * the file is removed instead; a kept figure past the probe's age limit is left
 * as it is. Any failure is logged once and swallowed: the monitor never fails
 * because of this file.
 */
export function writeUsageState(
  data: UsageData | undefined,
  filePath: string = usageStatePath(),
  nowMs = Date.now(),
  io: StateFileIo = defaultIo,
): "written" | "removed" | "skipped" | "failed" {
  const state = buildUsageState(data, nowMs);
  if (state === "too-old") {
    return "skipped";
  }
  if (!state) {
    removeUsageState(filePath);
    return "removed";
  }
  const temp = `${filePath}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.tmp`;
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(temp, JSON.stringify(state, null, 2) + "\n", { encoding: "utf-8", mode: 0o600 });
    renameIntoPlace(temp, filePath, io);
    return "written";
  } catch {
    try {
      fs.rmSync(temp, { force: true });
    } catch {
      // Nothing else to clean up.
    }
    logOnce("state-write-failed", "Could not write the Copilot usage state file; the usage guard stays silent for Copilot.");
    return "failed";
  }
}
