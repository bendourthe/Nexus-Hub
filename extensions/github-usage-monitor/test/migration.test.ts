import { readFileSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import {
  MIGRATED_CONFIG_KEYS,
  MIGRATED_STATE_KEYS,
  MIGRATION_FLAG,
  SETTINGS_ADDED_AFTER_MIGRATION,
  NEW_SECRET_KEY,
  OLD_SECRET_KEY,
  migrateSettings,
  type MigrationContextLike
} from "../src/migration";
import {
  ConfigurationTarget,
  failConfigurationUpdate,
  readUserConfiguration,
  resetVscodeStub,
  setConfiguration,
  setUserConfiguration,
  workspace
} from "./vscode-stub";

/** A `context` whose globalState and secrets are inspectable, plus optional failure injection. */
function fakeContext(options: { secretStoreFails?: boolean } = {}): MigrationContextLike & {
  state: Map<string, unknown>;
  secretValues: Map<string, string>;
} {
  const state = new Map<string, unknown>();
  const secretValues = new Map<string, string>();
  return {
    state,
    secretValues,
    globalState: {
      get<T>(key: string): T | undefined { return state.get(key) as T | undefined; },
      async update(key: string, value: unknown): Promise<void> {
        if (value === undefined) state.delete(key); else state.set(key, value);
      }
    },
    secrets: {
      async get(key: string): Promise<string | undefined> { return secretValues.get(key); },
      async store(key: string, value: string): Promise<void> {
        if (options.secretStoreFails === true) throw new Error("SecretStorage unavailable");
        secretValues.set(key, value);
      },
      async delete(key: string): Promise<void> { secretValues.delete(key); }
    }
  };
}

const rootConfig = (): Parameters<typeof migrateSettings>[1] =>
  workspace.getConfiguration() as unknown as Parameters<typeof migrateSettings>[1];

describe("one-time settings migration", () => {
  beforeEach(() => { resetVscodeStub(); });

  it("covers every contributed setting that predates the migration", () => {
    const manifest = JSON.parse(readFileSync(join(__dirname, "..", "package.json"), "utf8")) as {
      contributes: { configuration: { properties: Record<string, unknown> } };
    };
    const contributed = Object.keys(manifest.contributes.configuration.properties)
      .map((key) => key.replace(/^githubUsageMonitor\./u, ""))
      .sort();
    // Every contributed key is either migrated or explicitly declared as new. A key
    // that is neither would be silently left behind on a future namespace move,
    // which is the defect this guard exists to catch.
    const accounted = [...MIGRATED_CONFIG_KEYS, ...SETTINGS_ADDED_AFTER_MIGRATION].sort();
    expect(accounted).toEqual(contributed);
    // And no migrated key may name a setting that is no longer contributed, which
    // would be a stale entry migrating something that does not exist.
    for (const key of MIGRATED_CONFIG_KEYS) expect(contributed).toContain(key);
    // The two lists must not overlap: a key cannot both predate the migration and
    // have been added after it.
    for (const key of SETTINGS_ADDED_AFTER_MIGRATION) expect(MIGRATED_CONFIG_KEYS).not.toContain(key);
  });

  it("carries every user-set old key across, preserving scope", async () => {
    for (const key of MIGRATED_CONFIG_KEYS) {
      setUserConfiguration(`githubUsage.${key}`, `fixture-${key}`, ConfigurationTarget.Global);
    }
    setUserConfiguration("githubUsage.billingOwner", "workspace-acme", ConfigurationTarget.Workspace);

    const context = fakeContext();
    const result = await migrateSettings(context, rootConfig());

    expect(result.ran).toBe(true);
    expect(result.failures).toEqual([]);
    expect(result.completed).toBe(true);
    for (const key of MIGRATED_CONFIG_KEYS) {
      expect(readUserConfiguration(`githubUsageMonitor.${key}`, ConfigurationTarget.Global)).toBe(`fixture-${key}`);
    }
    // A workspace-set value must land in workspace scope, never be promoted to global.
    expect(readUserConfiguration("githubUsageMonitor.billingOwner", ConfigurationTarget.Workspace)).toBe("workspace-acme");
  });

  it("never copies a value the user left at its default", async () => {
    // Present as an effective value, but not as globalValue or workspaceValue.
    setConfiguration("githubUsage.refreshInterval", 10);

    const context = fakeContext();
    const result = await migrateSettings(context, rootConfig());

    expect(result.migrated).toEqual([]);
    // Writing the default explicitly would pin the user to today's default forever.
    expect(readUserConfiguration("githubUsageMonitor.refreshInterval")).toBeUndefined();
    expect(result.completed).toBe(true);
  });

  it("leaves the old keys readable rather than deleting them", async () => {
    setUserConfiguration("githubUsage.billingOwner", "acme");
    await migrateSettings(fakeContext(), rootConfig());
    expect(readUserConfiguration("githubUsage.billingOwner")).toBe("acme");
  });

  it("is idempotent: a second activation does no work", async () => {
    setUserConfiguration("githubUsage.billingOwner", "acme");
    const context = fakeContext();

    const first = await migrateSettings(context, rootConfig());
    expect(first.ran).toBe(true);
    expect(context.state.get(MIGRATION_FLAG)).toBe(true);

    // Change the source so a re-run would be visible if it happened.
    setUserConfiguration("githubUsage.billingOwner", "second-value");
    const second = await migrateSettings(context, rootConfig());

    expect(second.ran).toBe(false);
    expect(second.migrated).toEqual([]);
    expect(readUserConfiguration("githubUsageMonitor.billingOwner")).toBe("acme");
  });

  it("does not claim completion when a single key fails to write, and retries next activation", async () => {
    setUserConfiguration("githubUsage.billingOwner", "acme");
    setUserConfiguration("githubUsage.refreshInterval", 25);
    failConfigurationUpdate("githubUsageMonitor.refreshInterval");
    const context = fakeContext();

    const first = await migrateSettings(context, rootConfig());

    expect(first.failures).toEqual(["githubUsage.refreshInterval"]);
    expect(first.completed).toBe(false);
    // A half-migrated state that claims completion is the failure mode to avoid.
    expect(context.state.get(MIGRATION_FLAG)).toBeUndefined();

    const second = await migrateSettings(context, rootConfig());
    expect(second.ran).toBe(true);
  });

  it("logs which key failed", async () => {
    setUserConfiguration("githubUsage.billingOwner", "acme");
    failConfigurationUpdate("githubUsageMonitor.billingOwner");
    const lines: string[] = [];

    await migrateSettings(fakeContext(), rootConfig(), (line) => lines.push(line));

    expect(lines.join("\n")).toContain("githubUsage.billingOwner");
  });

  it("re-writes the stored token under the new key and clears the old one", async () => {
    const context = fakeContext();
    context.secretValues.set(OLD_SECRET_KEY, "fixture-token-value-123456789");

    const result = await migrateSettings(context, rootConfig());

    expect(context.secretValues.get(NEW_SECRET_KEY)).toBe("fixture-token-value-123456789");
    expect(context.secretValues.has(OLD_SECRET_KEY)).toBe(false);
    expect(result.completed).toBe(true);
  });

  it("keeps the old token in place when the re-write fails", async () => {
    const context = fakeContext({ secretStoreFails: true });
    context.secretValues.set(OLD_SECRET_KEY, "fixture-token-value-123456789");

    const result = await migrateSettings(context, rootConfig());

    // A stale key name is recoverable next activation; a lost token is not.
    expect(context.secretValues.get(OLD_SECRET_KEY)).toBe("fixture-token-value-123456789");
    expect(result.failures).toContain(OLD_SECRET_KEY);
    expect(context.state.get(MIGRATION_FLAG)).toBeUndefined();
  });

  it("moves the cached snapshot, alert cycle, and capability verdict", async () => {
    const context = fakeContext();
    for (const [oldKey] of MIGRATED_STATE_KEYS) context.state.set(oldKey, { fixture: oldKey });

    await migrateSettings(context, rootConfig());

    for (const [oldKey, newKey] of MIGRATED_STATE_KEYS) {
      expect(context.state.get(newKey)).toEqual({ fixture: oldKey });
      expect(context.state.has(oldKey)).toBe(false);
    }
  });

  it("does nothing and completes cleanly on a fresh install", async () => {
    const context = fakeContext();
    const result = await migrateSettings(context, rootConfig());
    expect(result.migrated).toEqual([]);
    expect(result.completed).toBe(true);
  });
});
