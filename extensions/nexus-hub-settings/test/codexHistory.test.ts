import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const host = vi.hoisted(() => ({
  trusted: true,
  codex: true as boolean,
  pick: vi.fn(),
  info: vi.fn(),
  execute: vi.fn(),
}));
vi.mock("vscode", () => ({
  workspace: { get isTrusted() { return host.trusted; } },
  extensions: { getExtension: (id: string) => (id === "openai.chatgpt" && host.codex ? {} : undefined) },
  window: { showQuickPick: host.pick, showInformationMessage: host.info },
  commands: { executeCommand: host.execute },
  Uri: { from: (parts: Record<string, string>) => parts },
}));
import { historyEntries, openCodexHistory } from "../src/codexHistory";

const ID_A = "0123abcd-0123-4567-89ab-0123456789ab";
const ID_B = "ffffffff-0000-1111-2222-333333333333";
const row = (id: string, name: unknown, updated: unknown) => JSON.stringify({ id, thread_name: name, updated_at: updated });

describe("historyEntries", () => {
  it("keeps the newest row per session, newest first, and ignores malformed rows", () => {
    const index = [row(ID_A, "First", "2026-11-01T10:00:00Z"), "{not json", row("not-a-uuid", "Bad id", "2026-11-02"), row(ID_B, 7, "2026-11-02"), row(ID_B, "Second", "2026-11-03T09:00:00Z"), row(ID_A, "First\trenamed", "2026-11-04T08:00:00Z")].join("\n");
    expect(historyEntries(index)).toEqual([
      { id: ID_B, label: "Second", description: "2026-11-03" },
      { id: ID_A, label: "First renamed", description: "2026-11-04" },
    ]);
  });
});

describe("openCodexHistory", () => {
  let home: string; let previous: string | undefined;
  beforeEach(async () => {
    host.trusted = true; host.codex = true; host.pick.mockReset(); host.info.mockReset(); host.execute.mockReset();
    previous = process.env.CODEX_HOME; home = await fs.mkdtemp(path.join(os.tmpdir(), "codex-history-")); process.env.CODEX_HOME = home;
  });
  afterEach(async () => {
    await fs.rm(home, { recursive: true, force: true });
    if (previous === undefined) { delete process.env.CODEX_HOME; } else { process.env.CODEX_HOME = previous; }
  });

  it("does nothing in an untrusted workspace or without Codex", async () => {
    host.trusted = false; await openCodexHistory();
    host.trusted = true; host.codex = false; await openCodexHistory();
    expect(host.info).not.toHaveBeenCalled(); expect(host.pick).not.toHaveBeenCalled();
  });
  it("explains that history is unavailable when the index is missing or too large", async () => {
    await openCodexHistory();
    const file = path.join(home, "session_index.jsonl");
    await fs.writeFile(file, ""); await fs.truncate(file, 8_000_001); await openCodexHistory();
    expect(host.info).toHaveBeenCalledTimes(2); expect(host.pick).not.toHaveBeenCalled();
  });
  it("opens the chosen session in a Codex editor tab and nothing when the pick is dismissed", async () => {
    await fs.writeFile(path.join(home, "session_index.jsonl"), row(ID_A, "Fix damage", "2026-11-04T08:00:00Z"));
    host.pick.mockResolvedValueOnce(undefined); await openCodexHistory();
    expect(host.execute).not.toHaveBeenCalled();
    host.pick.mockImplementationOnce(async (items: unknown[]) => items[0]); await openCodexHistory();
    expect(host.execute).toHaveBeenCalledWith("vscode.openWith", { scheme: "openai-codex", authority: "route", path: "/local/" + ID_A }, "chatgpt.conversationEditor", { preview: false });
  });
});
