import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as vscode from "vscode";
import { syncEditorEffort } from "../src/editorEffort";
import type { ShowRecord } from "../src/types";
import { stub, Uri } from "./vscode-stub";

const KEY = "claudeCode.environmentVariables";
const VARIABLE = "CLAUDE_CODE_EFFORT_LEVEL";
const record = (fields: Partial<ShowRecord> = {}): ShowRecord => ({
  control: "effort", tool: "claude", surface: "cli", state: "in-effect", value: "ultra", native: "max",
  layer: null, layer_value: null, fix: null, detail: null, caveats: [], writes: [], removable_override: null,
  mapped_effort: "max", ...fields,
});

beforeEach(() => {
  stub.reset();
  stub.defaults[KEY] = [];
});
afterEach(() => { vi.restoreAllMocks(); });

describe("editor effort synchronization", () => {
  it("backs up only existing effort entries before updating and preserves unrelated environment data", async () => {
    const token = { name: "API_TOKEN", value: "private-token" };
    stub.user[KEY] = [token, { name: VARIABLE, value: "low", extra: "preserved" }, { name: VARIABLE, value: "high" }];
    const backups: [string, unknown][] = [];
    const result = await syncEditorEffort([record()], async (key, value) => {
      expect(stub.updates).toHaveLength(0);
      backups.push([key, value]);
    });
    expect(result.issues).toEqual([]);
    expect(result.changed).toHaveLength(1);
    expect(stub.user[KEY]).toEqual([token, { name: VARIABLE, value: "max", extra: "preserved" }, { name: VARIABLE, value: "max" }]);
    expect(backups).toEqual([["editorEffort.claude.user:profile", { entries: [{ index: 1, value: "low" }, { index: 2, value: "high" }], written: "max" }]]);
    expect(JSON.stringify(backups)).not.toContain("private-token");
  });

  it("does not add an editor environment override or rewrite an already matching value", async () => {
    const backup = vi.fn(async () => undefined);
    await syncEditorEffort([record()], backup);
    stub.user[KEY] = [{ name: "OTHER", value: "keep" }];
    await syncEditorEffort([record()], backup);
    stub.user[KEY] = [{ name: VARIABLE, value: "max" }];
    await syncEditorEffort([record()], backup);
    expect(backup).not.toHaveBeenCalled();
    expect(stub.updates).toHaveLength(0);
  });

  it("reconciles existing workspace and folder layers using their actual configuration targets", async () => {
    stub.folders = [{ uri: Uri.file("C:/project") }];
    stub.workspace[KEY] = [{ name: VARIABLE, value: "low" }];
    stub.folder[KEY] = [{ name: VARIABLE, value: "medium" }, { name: "OTHER", value: "keep" }];
    const backup = vi.fn(async () => undefined);
    const result = await syncEditorEffort([record({ mapped_effort: "xhigh" })], backup);
    expect(result.changed).toHaveLength(2);
    expect(stub.updates.map(({ target, value }) => [target, value])).toEqual([
      [2, [{ name: VARIABLE, value: "xhigh" }]],
      [3, [{ name: VARIABLE, value: "xhigh" }, { name: "OTHER", value: "keep" }]],
    ]);
    expect(backup.mock.calls.map((call) => call[0])).toEqual([
      "editorEffort.claude.workspace:file:///C:/project", "editorEffort.claude.folder:file:///C:/project",
    ]);
  });

  it("reconciles every local folder while writing global and workspace effort only once", async () => {
    const first = Uri.file("C:/first");
    const second = Uri.file("C:/second");
    const remote = Uri.parse("vscode-remote://host/project");
    stub.folders = [{ uri: first }, { uri: second }, { uri: remote }];
    stub.user[KEY] = [{ name: VARIABLE, value: "low" }];
    stub.workspace[KEY] = [{ name: VARIABLE, value: "medium" }];
    const folderValues = new Map<string, unknown>([
      [first.toString(), [{ name: VARIABLE, value: "high" }, { name: "TOKEN", value: "first-private" }]],
      [second.toString(), [{ name: VARIABLE, value: "low" }, { name: "TOKEN", value: "second-private" }]],
      [remote.toString(), [{ name: VARIABLE, value: "low" }]],
    ]);
    const writes: { resource: string | undefined; target: unknown }[] = [];
    const original = vscode.workspace.getConfiguration.bind(vscode.workspace);
    vi.spyOn(vscode.workspace, "getConfiguration").mockImplementation((section, resource) => {
      const config = original(section);
      const uri = resource?.toString();
      return {
        ...config,
        inspect: (key: string) => ({ ...config.inspect(key), workspaceFolderValue: uri ? folderValues.get(uri) : undefined }),
        update: async (key: string, value: unknown, target: unknown) => {
          writes.push({ resource: uri, target });
          if (target === vscode.ConfigurationTarget.Global) { stub.user[key] = value; }
          else if (target === vscode.ConfigurationTarget.Workspace) { stub.workspace[key] = value; }
          else if (uri) { folderValues.set(uri, value); }
        },
      } as vscode.WorkspaceConfiguration;
    });
    const backups: [string, unknown][] = [];
    const result = await syncEditorEffort([record()], async (key, value) => { backups.push([key, value]); });
    expect(result.issues).toEqual([]);
    expect(result.changed).toHaveLength(4);
    expect(writes.filter(({ target }) => target === 1)).toHaveLength(1);
    expect(writes.filter(({ target }) => target === 2)).toHaveLength(1);
    expect(writes.filter(({ target }) => target === 3).map(({ resource }) => resource)).toEqual([first.toString(), second.toString()]);
    expect(folderValues.get(first.toString())).toEqual([{ name: VARIABLE, value: "max" }, { name: "TOKEN", value: "first-private" }]);
    expect(folderValues.get(second.toString())).toEqual([{ name: VARIABLE, value: "max" }, { name: "TOKEN", value: "second-private" }]);
    expect(folderValues.get(remote.toString())).toEqual([{ name: VARIABLE, value: "low" }]);
    expect(backups.map(([key]) => key)).toContain("editorEffort.claude.folder:file:///C:/first");
    expect(backups.map(([key]) => key)).toContain("editorEffort.claude.folder:file:///C:/second");
    expect(JSON.stringify(backups)).not.toContain("private");
  });

  it.each(["not-an-array", [{ name: VARIABLE, value: 42 }]])("preserves malformed effort settings %#", async (value) => {
    stub.user[KEY] = value;
    const backup = vi.fn(async () => undefined);
    const result = await syncEditorEffort([record()], backup);
    expect(result.issues.join(" ")).toContain("malformed");
    expect(stub.user[KEY]).toEqual(value);
    expect(backup).not.toHaveBeenCalled();
    expect(stub.updates).toHaveLength(0);
  });

  it("does not write after a backup failure and reports a refused configuration update", async () => {
    stub.user[KEY] = [{ name: VARIABLE, value: "low" }];
    let result = await syncEditorEffort([record()], async () => { throw new Error("backup unavailable"); });
    expect(stub.updates).toHaveLength(0);
    expect(result.issues.join(" ")).toContain("backup unavailable");
    stub.failUpdate.add(KEY);
    result = await syncEditorEffort([record()], async () => undefined);
    expect(result.issues.join(" ")).toContain("stub refused");
    expect(stub.user[KEY]).toEqual([{ name: VARIABLE, value: "low" }]);
  });

  it("preserves a concurrent edit made while the backup is saving", async () => {
    stub.user[KEY] = [{ name: VARIABLE, value: "low" }];
    const changed = [{ name: VARIABLE, value: "medium" }, { name: "USER_EDIT", value: "keep" }];
    const result = await syncEditorEffort([record()], async () => { stub.user[KEY] = changed; });
    expect(result.issues.join(" ")).toContain("changed while saving");
    expect(stub.updates).toHaveLength(0);
    expect(stub.user[KEY]).toEqual(changed);
  });

  it("uses only the engine's validated Claude mapping and skips unregistered settings", async () => {
    stub.user[KEY] = [{ name: VARIABLE, value: "low" }];
    const backup = vi.fn(async () => undefined);
    expect((await syncEditorEffort([record({ mapped_effort: "ultra" })], backup)).issues.join(" ")).toContain("not valid");
    delete stub.defaults[KEY];
    await syncEditorEffort([record()], backup);
    await syncEditorEffort([record({ mapped_effort: undefined })], backup);
    expect(backup).not.toHaveBeenCalled();
    expect(stub.updates).toHaveLength(0);
  });

  it("keeps untrusted workspaces read-only", async () => {
    stub.trusted = false;
    stub.user[KEY] = [{ name: VARIABLE, value: "low" }];
    const backup = vi.fn(async () => undefined);
    expect(await syncEditorEffort([record()], backup)).toEqual({ changed: [], issues: [] });
    expect(backup).not.toHaveBeenCalled();
    expect(stub.updates).toHaveLength(0);
  });

  it("keeps unsupported Copilot compatibility out of synchronization errors", async () => {
    stub.defaults["github.copilot.chat.reasoningEffortOverride"] = null;
    const result = await syncEditorEffort([record({ tool: "vscode-copilot", mapped_effort: undefined })], async () => undefined);
    expect(result.changed).toEqual([]);
    expect(result.issues).toEqual([]);
    expect(stub.updates).toHaveLength(0);
    expect((await syncEditorEffort([record({ tool: "vscode-copilot", state: "tool-not-installed" })], async () => undefined)).issues).toEqual([]);
  });

  it("does not report a Copilot limitation in an editor without Copilot", async () => {
    expect((await syncEditorEffort([record({ tool: "vscode-copilot", mapped_effort: undefined })], async () => undefined)).issues).toEqual([]);
  });
});
