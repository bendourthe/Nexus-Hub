import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { describe, expect, it, vi } from "vitest";
import { CHAT_MODEL_KEY, loadNodeSqlite, readChatModel, stateDatabasePath, type SqliteModule } from "../src/currentModel";
import { UsageService } from "../src/usageService";

type Call = { file: string; options: unknown; sql: string; params: unknown[] };

function fakeSqlite(row: unknown, calls: Call[]): SqliteModule {
  class FakeDatabase {
    constructor(private readonly file: string, private readonly options?: unknown) {}
    prepare(sql: string): { get: (...params: unknown[]) => unknown } {
      return { get: (...params: unknown[]) => (calls.push({ file: this.file, options: this.options, sql, params }), row) };
    }
    close(): void {}
  }
  return { DatabaseSync: FakeDatabase as unknown as SqliteModule["DatabaseSync"] };
}

describe("readChatModel", () => {
  it("opens the database read-only, asks for the one Chat model key, and drops the copilot/ prefix", async () => {
    const calls: Call[] = [];
    expect(await readChatModel("C:/state.vscdb", async () => fakeSqlite({ value: "copilot/claude-opus-5.5" }, calls))).toBe("claude-opus-5.5");
    expect(calls).toEqual([{ file: "C:/state.vscdb", options: { readOnly: true }, sql: "SELECT value FROM ItemTable WHERE key = ? LIMIT 1", params: [CHAT_MODEL_KEY] }]);
  });

  it("keeps another vendor's prefix and decodes a byte value", async () => {
    expect(await readChatModel("db", async () => fakeSqlite({ value: "ollama/qwen3-coder" }, []))).toBe("ollama/qwen3-coder");
    expect(await readChatModel("db", async () => fakeSqlite({ value: new TextEncoder().encode("copilot/gpt-6") }, []))).toBe("gpt-6");
  });

  it.each([
    ["no row", undefined],
    ["markup", { value: "<img src=x>" }],
    ["a JSON blob", { value: '{"model":"x"}' }],
    ["an over-long value", { value: "m".repeat(90) }],
  ])("returns undefined for %s", async (_label, row) => {
    expect(await readChatModel("db", async () => fakeSqlite(row, []))).toBeUndefined();
  });

  it("returns undefined without sqlite or when the open fails", async () => {
    expect(await readChatModel("db", async () => null)).toBeUndefined();
    const throwing = { DatabaseSync: class { constructor() { throw new Error("locked"); } } } as unknown as SqliteModule;
    expect(await readChatModel("db", async () => throwing)).toBeUndefined();
  });

  it("reads a real state database written in VS Code's layout", async () => {
    const sqlite = await loadNodeSqlite();
    if (sqlite === null) return;
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-model-"));
    const file = path.join(dir, "state.vscdb");
    try {
      const writer = new (sqlite.DatabaseSync as unknown as new (f: string) => {
        exec(sql: string): void;
        prepare(sql: string): { run(...params: unknown[]): void };
        close(): void;
      })(file);
      writer.exec("CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)");
      writer.prepare("INSERT INTO ItemTable (key, value) VALUES (?, ?)").run(CHAT_MODEL_KEY, "copilot/claude-opus-5.5");
      writer.close();
      expect(await readChatModel(file)).toBe("claude-opus-5.5");
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  it("finds the database beside the extension's own global storage folder", () => {
    const storage = path.join("C:", "Users", "u", "AppData", "Roaming", "Code", "User", "globalStorage", "nexus-hub.copilot-usage-monitor");
    expect(stateDatabasePath(storage)).toBe(path.join("C:", "Users", "u", "AppData", "Roaming", "Code", "User", "globalStorage", "state.vscdb"));
  });
});

describe("UsageService current model", () => {
  const personal = { fetchUsage: vi.fn(async () => ({ success: true as const, data: { planLabel: "Copilot Free", quotas: [], resetsAt: null } })) };
  const organization = { isActive: () => false, fetchUsage: vi.fn() };

  it("reads the model once per successful fetch and attaches it", async () => {
    const reader = vi.fn(async () => "claude-opus-5.5");
    const result = await new UsageService(personal as never, organization as never, reader).fetchAll(0);
    expect(reader).toHaveBeenCalledOnce();
    expect(result.success && result.data.currentModel).toBe("claude-opus-5.5");
  });

  it("ignores a failing reader and never reads when the fetch failed", async () => {
    const failing = await new UsageService(personal as never, organization as never, async () => { throw new Error("x"); }).fetchAll(0);
    expect(failing.success && failing.data.currentModel).toBeUndefined();
    const reader = vi.fn(async () => "m");
    const down = { fetchUsage: async () => ({ success: false as const, error: { code: "network-error" } }) };
    expect((await new UsageService(down as never, organization as never, reader).fetchAll(0)).success).toBe(false);
    expect(reader).not.toHaveBeenCalled();
  });
});

describe("decision 1b exception is confined to one file", () => {
  it("only currentModel.ts opens the editor state database", () => {
    const srcDir = path.join(__dirname, "..", "src");
    const files = fs.readdirSync(srcDir, { recursive: true }).map(String).filter((f) => f.endsWith(".ts") && !f.endsWith(".d.ts"));
    const openers = files.filter((f) => /node:sqlite|DatabaseSync|state\.vscdb/.test(fs.readFileSync(path.join(srcDir, f), "utf-8")));
    expect(openers).toEqual(["currentModel.ts"]);
  });
});
