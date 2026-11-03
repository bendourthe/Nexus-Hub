import { beforeEach, describe, expect, it } from "vitest";
import {
  EditorWriteError,
  applyEditorWrites,
  asciiOnly,
  inspectKey,
  precheckEditorWrites,
  profileNameFromStorage,
  restoreEditorWrites,
} from "../src/editorWrites";
import type { EditorRestore, EditorWrite } from "../src/types";
import { stub } from "./vscode-stub";

const KEY = "chat.tools.global.autoApprove";
const OTHER = "claudeCode.initialPermissionMode";

function write(key = KEY, value: unknown = true): EditorWrite {
  return { tool: "vscode-copilot", write: "vscode-copilot.auto_approve", key, key_path: [key], value, weakens_safety: true, takes_effect: "next" };
}

beforeEach(() => {
  stub.reset();
  stub.defaults[KEY] = false;
  stub.defaults[OTHER] = "default";
});

describe("inspecting a key", () => {
  it("reads every layer and says whether an extension contributes the key", () => {
    stub.user[KEY] = true;
    stub.workspace[KEY] = false;
    expect(inspectKey(KEY)).toMatchObject({ registered: true, globalValue: true, workspaceValue: false, workspaceFolderValue: undefined });
    expect(inspectKey("nobody.contributes.this").registered).toBe(false);
  });
});

describe("checking planned writes before the engine writes anything", () => {
  it("passes a clean set of keys through", () => {
    const result = precheckEditorWrites([write(), write(OTHER, "acceptEdits")]);
    expect(result).toMatchObject({ ok: true, skipped: [] });
    expect(result.ok && result.apply).toHaveLength(2);
  });

  it("aborts the whole change on a workspace value and names the layer and the fix", () => {
    stub.workspace[OTHER] = "default";
    const result = precheckEditorWrites([write(), write(OTHER, "acceptEdits")]);
    expect(result.ok).toBe(false);
    expect(!result.ok && result.message).toContain("overridden-by workspace setting");
    expect(!result.ok && result.key).toBe(OTHER);
    expect(!result.ok && result.message).toContain("the workspace settings");
  });

  it("treats a workspace folder value the same way", () => {
    stub.folder[KEY] = false;
    const result = precheckEditorWrites([write()]);
    expect(!result.ok && result.message).toContain("the workspace folder settings");
  });

  it("skips a key no installed extension contributes instead of letting update() throw", () => {
    delete stub.defaults[OTHER];
    const result = precheckEditorWrites([write(), write(OTHER, "acceptEdits")]);
    expect(result.ok && result.apply.map((w) => w.key)).toEqual([KEY]);
    expect(result.ok && result.skipped[0]?.reason).toContain("not installed or is disabled");
  });
});

describe("applying writes at the user layer and recording each previous value", () => {
  it("writes to the Global layer and records previous present and absent values", async () => {
    stub.user[OTHER] = "default";
    const recorded: unknown[] = [];

    const applied = await applyEditorWrites([write(), write(OTHER, "acceptEdits")], async (w, previous) => void recorded.push([w.key, previous]));

    expect(stub.updates.map((u) => [u.key, u.value, u.target])).toEqual([[KEY, true, 1], [OTHER, "acceptEdits", 1]]);
    expect(recorded).toEqual([[KEY, { present: false }], [OTHER, { present: true, value: "default" }]]);
    expect(applied).toHaveLength(2);
  });

  it("stops at a key VS Code refuses and reports what was already applied for the rollback", async () => {
    stub.failUpdate.add(OTHER);
    const error = await applyEditorWrites([write(), write(OTHER, "acceptEdits")], async () => undefined).catch((e: unknown) => e as EditorWriteError);
    expect(error).toBeInstanceOf(EditorWriteError);
    expect((error as EditorWriteError).message).toContain("VS Code refused to save claudeCode.initialPermissionMode");
    expect((error as EditorWriteError).applied.map((a) => a.write.key)).toEqual([KEY]);
  });

  it("puts a key back at once when recording it fails", async () => {
    stub.user[KEY] = false;
    const error = (await applyEditorWrites([write()], async () => {
      throw new Error("record refused");
    }).catch((e: unknown) => e)) as EditorWriteError;
    expect(error.message).toContain("could not be recorded, so it was put back");
    expect(stub.user[KEY]).toBe(false);
    expect(error.applied).toEqual([]);
  });

  it("removes a key it had added when recording fails and nothing was there before", async () => {
    const error = (await applyEditorWrites([write()], async () => {
      throw "plain text failure";
    }).catch((e: unknown) => e)) as EditorWriteError;
    expect(error.message).toContain("plain text failure");
    expect(KEY in stub.user).toBe(false);
  });
});

describe("restoring on reset", () => {
  const restore = (over: Partial<EditorRestore> = {}): EditorRestore => ({
    tool: "vscode-copilot", write: "vscode-copilot.auto_approve", key: KEY, key_path: [KEY],
    restore: { present: false }, was: { present: true, value: true }, profile: null, ...over,
  });

  it("restores a key that still holds what Nexus-Hub wrote, and removes one that was absent before", async () => {
    stub.user[KEY] = true;
    const reports = await restoreEditorWrites([restore()], "Default");
    expect(reports).toEqual([{ key: KEY, status: "restored", detail: `${KEY} restored` }]);
    expect(KEY in stub.user).toBe(false);

    stub.user[OTHER] = "acceptEdits";
    await restoreEditorWrites([restore({ key: OTHER, key_path: [OTHER], restore: { present: true, value: "default" }, was: { present: true, value: "acceptEdits" } })], "Default");
    expect(stub.user[OTHER]).toBe("default");
  });

  it("leaves a key the user changed since, and says so", async () => {
    stub.user[KEY] = false;
    const [report] = await restoreEditorWrites([restore()], "Default");
    expect(report).toMatchObject({ status: "left" });
    expect(stub.user[KEY]).toBe(false);
  });

  it("treats a missing key as unchanged only when Nexus-Hub also wrote nothing", async () => {
    const [report] = await restoreEditorWrites([restore({ was: { present: false } })], "Default");
    expect(report?.status).toBe("restored");
  });

  it("skips a key written in another profile, an unregistered key, and a refused update", async () => {
    stub.user[KEY] = true;
    expect((await restoreEditorWrites([restore({ profile: "Work" })], "Default"))[0]).toMatchObject({ status: "skipped", detail: expect.stringContaining('profile "Work"') });
    expect((await restoreEditorWrites([restore({ profile: "Work" })], "Work"))[0]?.status).toBe("restored");
    delete stub.defaults[KEY];
    expect((await restoreEditorWrites([restore()], "Default"))[0]).toMatchObject({ status: "skipped", detail: expect.stringContaining("not registered") });
    stub.defaults[KEY] = false;
    stub.user[KEY] = true;
    stub.failUpdate.add(KEY);
    expect((await restoreEditorWrites([restore()], "Default"))[0]).toMatchObject({ status: "skipped", detail: expect.stringContaining("refused to restore") });
  });

  it("describes a non-Error failure", async () => {
    stub.user[KEY] = true;
    stub.failUpdate.add(KEY);
    const [report] = await restoreEditorWrites([restore()], "Default");
    expect(report?.detail).toContain("stub refused");
  });
});

describe("the active profile name", () => {
  const storage = JSON.stringify({ userDataProfiles: [{ location: "-6f2a1", name: "Work \u00e9" }] });

  it("is Default for the default profile and the profile's name for a named one", () => {
    expect(profileNameFromStorage("C:\\Users\\a\\AppData\\Roaming\\Code\\User\\globalStorage\\nexus-hub.nexus-hub-settings")).toBe("Default");
    const named = "C:\\Users\\a\\AppData\\Roaming\\Code\\User\\profiles\\-6f2a1\\globalStorage\\nexus-hub.nexus-hub-settings";
    expect(profileNameFromStorage(named, () => storage)).toBe("Work ?");
    expect(profileNameFromStorage("/home/a/.config/Code/User/profiles/-6f2a1/globalStorage/x", () => storage)).toBe("Work ?");
  });

  it("falls back to the profile id when the list cannot be read or has no entry", () => {
    const named = "/home/a/.config/Code/User/profiles/abc123/globalStorage/x";
    expect(profileNameFromStorage(named, () => { throw new Error("no file"); })).toBe("abc123");
    expect(profileNameFromStorage(named, () => storage)).toBe("abc123");
    expect(profileNameFromStorage(named, () => "{}")).toBe("abc123");
  });

  it("keeps recorded names printable ASCII and at most 100 characters", () => {
    expect(asciiOnly("caf\u00e9 ok")).toBe("caf? ok");
    expect(asciiOnly("x".repeat(150))).toHaveLength(100);
  });
});
