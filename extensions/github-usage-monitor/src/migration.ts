import * as vscode from "vscode";

/**
 * One-time migration from the pre-v0.2.0 `githubUsage.*` namespace to
 * `githubUsageMonitor.*`.
 *
 * v3.16.3 reverted the extension's name to "GitHub Usage Monitor" and moved the
 * command ids, configuration keys, and storage keys with it. A rename without
 * this module would silently reset every threshold, color, owner, and allowance
 * the user had configured: VS Code keys settings by their literal string, so the
 * old values are still on disk but nothing reads them any more.
 *
 * The extension id `nexus-hub.github-usage-monitor` did NOT change in either
 * direction, so an existing install updates in place and this migration runs
 * inside it exactly once.
 */

/** Guards the whole migration. Versioned so a later namespace move can add its own pass. */
export const MIGRATION_FLAG = "githubUsageMonitor.settingsMigrated.v0_2_0";

export const OLD_CONFIG_PREFIX = "githubUsage";
export const NEW_CONFIG_PREFIX = "githubUsageMonitor";

/**
 * Every configuration property the extension contributed under the old prefix.
 *
 * Kept as an explicit list rather than derived at runtime, because a migration
 * must describe the keys that existed WHEN THE OLD VERSION SHIPPED, not the ones
 * that happen to exist today. `migration.test.ts` asserts this list still matches
 * `package.json`, so a newly contributed setting fails loudly instead of being
 * quietly left behind.
 */
export const MIGRATED_CONFIG_KEYS: readonly string[] = [
  "billingScope",
  "billingOwner",
  "copilotMetric",
  "allowances.copilot",
  "allowances.actionsMinutes",
  "allowances.actionsStorage",
  "staleAfterMinutes",
  "autoFetch",
  "refreshInterval",
  "compactStatusBar",
  "alertMetric",
  "thresholds.moderate",
  "thresholds.high",
  "thresholds.critical",
  "notificationTimeoutSeconds",
  "requestTimeoutMs",
  "colors.moderate",
  "colors.high",
  "colors.critical"
];

/** SecretStorage. Losing this forces a full re-authentication, so it is handled most carefully. */
export const OLD_SECRET_KEY = "githubUsage.token";
export const NEW_SECRET_KEY = "githubUsageMonitor.token";

/** globalState caches. Losing these costs only a re-fetch, but there is no reason to pay it. */
export const MIGRATED_STATE_KEYS: readonly (readonly [string, string])[] = [
  ["githubUsage.snapshot", "githubUsageMonitor.snapshot"],
  ["githubUsage.alertCycle", "githubUsageMonitor.alertCycle"],
  ["githubUsage.authCapability", "githubUsageMonitor.authCapability"]
];

/** The `inspect()` and `update()` surface of a root `WorkspaceConfiguration`. */
export interface ConfigurationLike {
  inspect<T>(section: string): { globalValue?: T; workspaceValue?: T } | undefined;
  update(section: string, value: unknown, target: vscode.ConfigurationTarget): Thenable<void>;
}

/** The `context` surface this migration touches. Narrow, so it is unit-testable without a webview harness. */
export interface MigrationContextLike {
  globalState: {
    get<T>(key: string): T | undefined;
    update(key: string, value: unknown): Thenable<void>;
  };
  secrets: {
    get(key: string): Thenable<string | undefined>;
    store(key: string, value: string): Thenable<void>;
    delete(key: string): Thenable<void>;
  };
}

export interface MigrationResult {
  /** False when the flag was already set, i.e. the migration was skipped entirely. */
  ran: boolean;
  /** Old keys whose value was carried across, in the order attempted. */
  migrated: string[];
  /** Old keys that failed to write. A non-empty list means the flag was NOT set. */
  failures: string[];
  /** True only when a full pass completed and the flag was recorded. */
  completed: boolean;
}

/**
 * Carries every user-set value from the old namespace to the new one, exactly once.
 *
 * Only `globalValue` and `workspaceValue` are copied. A `defaultValue` is
 * deliberately never written: writing a default explicitly would pin the user to
 * today's default forever, so that a later release changing the default would
 * silently not reach them.
 *
 * The old configuration keys are NOT deleted in this release. A user who
 * downgrades should still find their settings, and a deletion that races a failed
 * write loses the data outright. Deletion is recorded as a v3.17.0 follow-up.
 */
export async function migrateSettings(
  context: MigrationContextLike,
  config: ConfigurationLike,
  log: (line: string) => void = () => undefined
): Promise<MigrationResult> {
  if (context.globalState.get<boolean>(MIGRATION_FLAG) === true) {
    return { ran: false, migrated: [], failures: [], completed: false };
  }

  const migrated: string[] = [];
  const failures: string[] = [];

  for (const key of MIGRATED_CONFIG_KEYS) {
    const oldKey = `${OLD_CONFIG_PREFIX}.${key}`;
    const newKey = `${NEW_CONFIG_PREFIX}.${key}`;
    const existing = config.inspect<unknown>(oldKey);
    if (existing === undefined) continue;
    // Scope is preserved rather than collapsed: a value the user set for one
    // workspace must not silently become their global default.
    for (const [value, target] of [
      [existing.globalValue, vscode.ConfigurationTarget.Global],
      [existing.workspaceValue, vscode.ConfigurationTarget.Workspace]
    ] as const) {
      if (value === undefined) continue;
      try {
        await config.update(newKey, value, target);
        migrated.push(oldKey);
      } catch (error) {
        failures.push(oldKey);
        log(`Settings migration failed for ${oldKey}: ${describeError(error)}`);
      }
    }
  }

  for (const [oldKey, newKey] of MIGRATED_STATE_KEYS) {
    try {
      const value = context.globalState.get<unknown>(oldKey);
      if (value === undefined) continue;
      await context.globalState.update(newKey, value);
      await context.globalState.update(oldKey, undefined);
      migrated.push(oldKey);
    } catch (error) {
      failures.push(oldKey);
      log(`Cached-state migration failed for ${oldKey}: ${describeError(error)}`);
    }
  }

  await migrateToken(context, migrated, failures, log);

  // A half-migrated state that claims completion is the failure mode to avoid:
  // the flag is recorded only after a clean pass, so the next activation retries.
  const completed = failures.length === 0;
  if (completed) await context.globalState.update(MIGRATION_FLAG, true);
  return { ran: true, migrated, failures, completed };
}

/**
 * Re-writes the stored token under the new key, then clears the old one.
 *
 * Written before deleted, deliberately. If the write fails the old key is left
 * exactly where it is: a stale key name is recoverable on the next activation,
 * while a lost token forces the user through a full re-authentication.
 */
async function migrateToken(
  context: MigrationContextLike,
  migrated: string[],
  failures: string[],
  log: (line: string) => void
): Promise<void> {
  let token: string | undefined;
  try {
    token = await context.secrets.get(OLD_SECRET_KEY);
  } catch (error) {
    failures.push(OLD_SECRET_KEY);
    log(`Token migration could not read ${OLD_SECRET_KEY}: ${describeError(error)}`);
    return;
  }
  if (token === undefined) return;
  try {
    await context.secrets.store(NEW_SECRET_KEY, token);
  } catch (error) {
    failures.push(OLD_SECRET_KEY);
    log(`Token migration could not write ${NEW_SECRET_KEY}; the old token is left in place: ${describeError(error)}`);
    return;
  }
  migrated.push(OLD_SECRET_KEY);
  try {
    await context.secrets.delete(OLD_SECRET_KEY);
  } catch (error) {
    // The token is already safe under the new key, so this is cosmetic. It must
    // not fail the pass and force a pointless retry of an already-done migration.
    log(`Token migration left the superseded ${OLD_SECRET_KEY} in place: ${describeError(error)}`);
  }
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
