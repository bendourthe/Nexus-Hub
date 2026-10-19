import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { renderDashboard } from "../src/dashboardPanel";
import { COMMAND_IDS, CursorUsageRuntime } from "../src/extension";
import { buildManualSnapshot } from "../src/manualEntry";
import type { UsageSnapshot } from "../src/types";
import {
  createExtensionContext,
  resetVscodeStub,
  runRegisteredCommand,
  webviewPanels
} from "./vscode-stub";
import {
  extractSelectedModel,
  MODEL_SETTINGS_KEY,
  readCursorSelectedModel
} from "../src/providers/currentModel";
import { loadNodeSqlite, type SqliteModuleLike } from "../src/providers/session";

function settingsRow(composer: unknown, extra: Record<string, unknown> = {}): { value: string } {
  return { value: JSON.stringify({ ...extra, aiSettings: { modelConfig: { "cmd-k": { modelName: "default" }, composer } } }) };
}

/** A fake sqlite module that records what was opened and asked for. */
function fakeSqlite(row: unknown, calls: Array<{ path: string; options: unknown; sql: string; params: unknown[] }>): SqliteModuleLike {
  class FakeDatabase {
    public constructor(private readonly path: string, private readonly options?: unknown) {}
    public prepare(sql: string): { get: (...params: unknown[]) => unknown } {
      return {
        get: (...params: unknown[]) => {
          calls.push({ path: this.path, options: this.options, sql, params });
          return row;
        }
      };
    }
    public close(): void {}
  }
  return { DatabaseSync: FakeDatabase as unknown as SqliteModuleLike["DatabaseSync"] };
}

const now = Date.parse("2026-10-19T12:00:00Z");

function snapshot(source: "credential-api" | "manual"): UsageSnapshot {
  const result = buildManualSnapshot(
    {
      cursorModels: { used: 80, limit: 100, unit: "requests" },
      otherModels: { used: 40, limit: 100, unit: "requests" },
      onDemandEnabled: false,
      personalSpend: null,
      periodStartsAt: "2026-10-01T00:00:00Z",
      resetsAt: "2026-11-01T00:00:00Z"
    },
    now
  );
  if (!result.ok) {
    throw new Error(result.errors.join(" "));
  }
  return { ...result.value, source };
}

describe("Current Model on the dashboard", () => {
  it("renders the section after the divider and before Recommendation, escaped", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot("credential-api") }, now, "nonce", "grok-4.7");
    expect(html).toContain('<h3>Current Model</h3>\n      <div class="model-name">grok-4.7</div>');
    expect(html.indexOf("<h3>Current Model</h3>")).toBeLessThan(html.indexOf("<h3>Recommendation</h3>"));
    expect(renderDashboard({ state: "fresh", data: snapshot("credential-api") }, now, "nonce", "a<b")).toContain("a&lt;b");
  });

  it("omits the section when no model was read", () => {
    expect(renderDashboard({ state: "fresh", data: snapshot("manual") }, now, "nonce")).not.toContain("Current Model");
  });

  it("is read after a live fetch and shown on the dashboard, but never for manual data", async () => {
    for (const [source, expected] of [["credential-api", 1], ["manual", 0]] as const) {
      resetVscodeStub();
      const readCurrentModel = vi.fn(async () => "grok-4.7");
      const runtime = new CursorUsageRuntime(createExtensionContext() as never, {
        provider: { fetch: vi.fn(async () => ({ ok: true as const, value: snapshot(source) })) },
        liveTransportCapable: true,
        readCurrentModel,
        now: () => now
      });
      runtime.start();
      await runtime.refresh("automatic");
      await runRegisteredCommand(COMMAND_IDS.dashboard);
      expect(readCurrentModel.mock.calls.length > 0).toBe(expected === 1);
      expect(webviewPanels.at(-1)?.webview.html.includes("grok-4.7")).toBe(expected === 1);
      runtime.dispose();
    }
    resetVscodeStub();
  });
});

describe("extractSelectedModel", () => {
  it("returns the composer model name and nothing else from the record", () => {
    expect(extractSelectedModel(settingsRow({ modelName: "grok-4.7", maxMode: true }, { email: "a@b.c" }))).toBe("grok-4.7");
  });

  it("falls back to the first selected model id", () => {
    expect(extractSelectedModel(settingsRow({ selectedModels: [{ modelId: "claude-4.5-sonnet" }] }))).toBe("claude-4.5-sonnet");
  });

  it("decodes a byte value", () => {
    const row = settingsRow({ modelName: "gpt-5" });
    expect(extractSelectedModel({ value: new TextEncoder().encode(row.value) })).toBe("gpt-5");
  });

  it.each([
    ["no row", undefined],
    ["not JSON", { value: "{nope" }],
    ["no composer", { value: JSON.stringify({ aiSettings: {} }) }],
    ["markup in the name", settingsRow({ modelName: "<img src=x>" })],
    ["an over-long name", settingsRow({ modelName: "m".repeat(80) })]
  ])("returns undefined for %s", (_label, row) => {
    expect(extractSelectedModel(row)).toBeUndefined();
  });
});

describe("readCursorSelectedModel", () => {
  it("opens the database read-only and asks for the one settings key", async () => {
    const calls: Array<{ path: string; options: unknown; sql: string; params: unknown[] }> = [];
    const model = await readCursorSelectedModel("C:/state.vscdb", async () => fakeSqlite(settingsRow({ modelName: "grok-4.7" }), calls));
    expect(model).toBe("grok-4.7");
    expect(calls).toEqual([
      {
        path: "C:/state.vscdb",
        options: { readOnly: true },
        sql: "SELECT value FROM ItemTable WHERE key = ? LIMIT 1",
        params: [MODEL_SETTINGS_KEY]
      }
    ]);
  });

  it("returns undefined without sqlite, without a path, or when the open fails", async () => {
    expect(await readCursorSelectedModel("C:/state.vscdb", async () => null)).toBeUndefined();
    expect(await readCursorSelectedModel("  ", async () => fakeSqlite(settingsRow({ modelName: "x1" }), []))).toBeUndefined();
    const throwing = { DatabaseSync: class { public constructor() { throw new Error("locked"); } } } as unknown as SqliteModuleLike;
    expect(await readCursorSelectedModel("C:/state.vscdb", async () => throwing)).toBeUndefined();
  });

  it("reads a real state database written in Cursor's layout", async () => {
    const sqlite = await loadNodeSqlite();
    if (sqlite === null) {
      return;
    }
    const dir = mkdtempSync(join(tmpdir(), "cursor-model-"));
    const file = join(dir, "state.vscdb");
    try {
      const writer = new (sqlite.DatabaseSync as unknown as new (path: string) => {
        exec(sql: string): void;
        prepare(sql: string): { run(...params: unknown[]): void };
        close(): void;
      })(file);
      writer.exec("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)");
      writer.prepare("INSERT INTO ItemTable (key, value) VALUES (?, ?)").run(MODEL_SETTINGS_KEY, settingsRow({ modelName: "grok-4.7" }).value);
      writer.close();
      expect(await readCursorSelectedModel(file)).toBe("grok-4.7");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
