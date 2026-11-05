import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OPEN_COMMAND, activate, deactivate, firstFolder, userPythonPath, vscodeUi, watchedFiles } from "../src/extension";
import { Uri, stub } from "./vscode-stub";
import { COMPACT_COMMAND, SET_EFFORT_COMMAND } from "../src/statusBar";
import { SettingsController } from "../src/controller";

let scratch: string;
const savedHub = process.env.NEXUS_HUB_HOME;

function context() {
  return {
    subscriptions: [] as { dispose(): unknown }[],
    extensionUri: Uri.file(path.join(scratch, "ext")),
    globalStorageUri: Uri.file(path.join(scratch, "Code", "User", "globalStorage", "nexus-hub.nexus-hub-settings")),
  };
}

beforeEach(() => {
  stub.reset();
  scratch = fs.mkdtempSync(path.join(os.tmpdir(), "nhs-ext-"));
  process.env.NEXUS_HUB_HOME = path.join(scratch, "no-install");
});

afterEach(() => {
  vi.useRealTimers();
  fs.rmSync(scratch, { recursive: true, force: true });
  if (savedHub === undefined) {
    delete process.env.NEXUS_HUB_HOME;
  } else {
    process.env.NEXUS_HUB_HOME = savedHub;
  }
});

describe("activation", () => {
  it("routes allowlisted hover effort choices through the existing controller", async () => {
    const handle = vi.spyOn(SettingsController.prototype, "handle").mockResolvedValue({} as never);
    try {
      activate(context() as never);
      for (const value of [null, {}, "off", "constructor", "<script>"]) { await stub.commands.get(SET_EFFORT_COMMAND)?.(value); }
      expect(handle).not.toHaveBeenCalled();
      await stub.commands.get(SET_EFFORT_COMMAND)?.("medium");
      expect(handle).toHaveBeenCalledWith({ type: "set", control: "effort", value: "medium", tool: null });
      handle.mockClear();
      stub.trusted = false;
      await stub.commands.get(SET_EFFORT_COMMAND)?.("high");
      expect(handle).not.toHaveBeenCalled();
    } finally { handle.mockRestore(); }
  });
  it("toggles the user compact preference from the hover", async () => {
    stub.defaults["nexusHubSettings.compactStatusBar"] = true;
    activate(context() as never);
    await stub.commands.get(COMPACT_COMMAND)?.();
    expect(stub.user["nexusHubSettings.compactStatusBar"]).toBe(false);
    await stub.commands.get(COMPACT_COMMAND)?.();
    expect(stub.user["nexusHubSettings.compactStatusBar"]).toBe(true);
  });
  it("registers the webview view, the open command, and watchers for every file the state depends on", () => {
    const ctx = context();
    activate(ctx as never);

    expect(stub.providers.map((p) => p.id)).toEqual(["nexusHubSettings.view"]);
    expect(stub.providers[0]?.options).toEqual({ webviewOptions: { retainContextWhenHidden: true } });
    expect(stub.commands.has(OPEN_COMMAND)).toBe(true);
    expect(stub.watchers).toHaveLength(6 + 3);
    expect(ctx.subscriptions.length).toBeGreaterThan(10);
  });

  it("opens the panel by focusing its view", async () => {
    activate(context() as never);
    await stub.commands.get(OPEN_COMMAND)?.();
    expect(stub.executed).toContain("nexusHubSettings.view.focus");
  });

  it("reads the current model on request and shows the install card when Nexus-Hub is missing", async () => {
    const api = activate(context() as never);
    const model = await api.getViewModel();
    expect(model.status).toBe("error");
    expect(model.error?.title).toBe("Nexus-Hub is not installed");
    expect(model.header.profile).toBe("Default");
  });

  it("re-reads after a file or setting change, debounced, and ignores unrelated settings", async () => {
    vi.useFakeTimers();
    const ctx = context();
    activate(ctx as never);

    stub.watchers[0]!.change.fire(undefined);
    stub.watchers[1]!.create.fire(undefined);
    stub.watchers[2]!.remove.fire(undefined);
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(500);
    expect(vi.getTimerCount()).toBe(0);

    stub.fireConfig("editor");
    expect(vi.getTimerCount()).toBe(0);
    stub.fireConfig("claudeCode");
    stub.fireConfig("chat");
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(500);
    stub.fireTrust();
    expect(vi.getTimerCount()).toBe(1);
    ctx.subscriptions.forEach((s) => s.dispose());
    expect(vi.getTimerCount()).toBe(0);
    deactivate();
  });
});

describe("what the panel watches", () => {
  it("covers the four tools' user files and the two Nexus-Hub files, honoring each tool's home override", () => {
    const files = watchedFiles({}, path.join("h"));
    expect(files).toEqual([
      path.join("h", ".claude", "settings.json"),
      path.join("h", ".codex", "config.toml"),
      path.join("h", ".copilot", "settings.json"),
      path.join("h", ".nexus-hub", "guardrails.json"),
      path.join("h", ".nexus-hub", "preferences.json"),
      path.join("h", ".nexus-hub", "settings-control.json"),
    ]);
    const overridden = watchedFiles({ CLAUDE_CONFIG_DIR: path.join("c"), CODEX_HOME: path.join("x"), COPILOT_HOME: "  " }, path.join("h"));
    expect(overridden.slice(0, 3)).toEqual([path.join("c", "settings.json"), path.join("x", "config.toml"), path.join("h", ".copilot", "settings.json")]);
  });
});

describe("host helpers", () => {
  it("takes the project only from a local first folder", () => {
    expect(firstFolder()).toBeUndefined();
    stub.folders = [{ uri: Uri.parse("vscode-remote://ssh/host/folder") }];
    expect(firstFolder()).toBeUndefined();
    stub.folders = [{ uri: Uri.file("C:\\work") }];
    expect(firstFolder()).toBe("C:\\work");
  });

  it("reads the interpreter setting from the user layer only", () => {
    stub.defaults["nexusHubSettings.pythonPath"] = "";
    expect(userPythonPath()).toBeUndefined();
    stub.workspace["nexusHubSettings.pythonPath"] = "C:\\evil\\python.exe";
    expect(userPythonPath()).toBeUndefined();
    stub.user["nexusHubSettings.pythonPath"] = "C:\\Python313\\python.exe";
    expect(userPythonPath()).toBe("C:\\Python313\\python.exe");
  });

  it("opens a modal warning and treats only its confirm button as consent", async () => {
    const ui = vscodeUi();
    stub.warningAnswer = (buttons) => buttons[0];
    expect(await ui.confirm({ message: "m", detail: "d", confirmLabel: "Go" })).toBe(true);
    expect(stub.warnings[0]).toMatchObject({ message: "m", options: { modal: true, detail: "d" }, buttons: ["Go"] });
    stub.warningAnswer = () => undefined;
    expect(await ui.confirm({ message: "m", detail: "d", confirmLabel: "Go" })).toBe(false);
    expect(await ui.openExternal("https://code.claude.com/docs")).toBe(true);
    expect(stub.opened).toEqual(["https://code.claude.com/docs"]);
  });
});
