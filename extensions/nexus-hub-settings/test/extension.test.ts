import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OPEN_COMMAND, announceStalledStart, refreshCodexTab, restartProvider, activate, deactivate, firstFolder, userPythonPath, providerDirectories, vscodeUi, watchedFiles } from "../src/extension";
import { Uri, stub } from "./vscode-stub";
import { COMPACT_COMMAND, SET_EFFORT_COMMAND, SettingsStatusBar } from "../src/statusBar";
import { SettingsController } from "../src/controller";
import { SESSION_DEFAULTS_FILE, writeSessionDefault } from "../src/sessionDefaults";
import * as nativeUi from "../src/vendorUi";
import * as liveEffort from "../src/liveEffort";

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
  it("finds Claude's bundled CLI without a standalone installation and ignores missing executables", () => {
    expect(providerDirectories()).toEqual([]);
    const directory = path.join(scratch, "claude-extension", "resources", "native-binary");
    fs.mkdirSync(directory, {recursive: true});
    stub.vendorExtensions.set("anthropic.claude-code", {extensionPath: path.join(scratch, "claude-extension"), isActive: false});
    expect(providerDirectories()).toEqual([]);
    fs.writeFileSync(path.join(directory, process.platform === "win32" ? "claude.exe" : "claude"), "fixture");
    expect(providerDirectories()).toEqual([directory]);
  });
  it("starts live adapters when an initially untrusted workspace becomes trusted", async () => {
    const native = vi.spyOn(nativeUi, "installNativeUi").mockResolvedValue(undefined);
    const live = vi.spyOn(liveEffort, "installLiveEffort").mockResolvedValue(undefined);
    const ctx = context();
    try {
      stub.trusted = false;
      await activate(ctx as never);
      expect(native).toHaveBeenCalledTimes(1);
      stub.trusted = true;
      stub.fireTrust();
      await vi.waitFor(() => expect(native).toHaveBeenCalledTimes(2));
      expect(live).toHaveBeenCalledTimes(2);
    } finally {
      ctx.subscriptions.forEach(item => item.dispose());
      native.mockRestore();
      live.mockRestore();
    }
  });
  it("routes the Codex toolbar through the shared tab preference", async () => {
    await activate(context() as never);
    await stub.commands.get("nexusHubSettings.openCodex")?.();
    expect(stub.executed.at(-1)).toBe("vscode.openWith");
    const call = stub.executedCalls.at(-1)!;
    expect(String(call.args[0])).toBe("openai-codex://route/extension/panel/new");
    expect(call.args[1]).toBe("chatgpt.conversationEditor");
    expect(call.args[2]).toEqual({viewColumn: -2, preserveFocus: false, preview: false});
    expect(stub.executed).not.toContain("workbench.action.splitEditor");
    writeSessionDefault(path.join(process.env.NEXUS_HUB_HOME!, SESSION_DEFAULTS_FILE), "codexTabs", false);
    await stub.commands.get("nexusHubSettings.openCodex")?.();
    expect(stub.executed.at(-1)).toBe("chatgpt.openSidebar");
    stub.trusted = false; const count = stub.executed.length;
    await stub.commands.get("nexusHubSettings.openCodex")?.();
    expect(stub.executed).toHaveLength(count);
  });
  it("exposes boolean-only Fast and editor preference actions to other extensions", async () => {
    const handle = vi.spyOn(SettingsController.prototype, "handle").mockResolvedValue({} as never);
    try {
      const api = await activate(context() as never);
      expect(() => api.setFastMode("on" as never)).toThrow("boolean");
      expect(() => api.setCodexTabs(null as never)).toThrow("boolean");
      await api.setFastMode(true); expect(handle).toHaveBeenLastCalledWith({type: "setFastMode", value: true});
      await api.setCodexTabs(false); expect(handle).toHaveBeenLastCalledWith({type: "setCodexTabs", value: false});
    } finally {handle.mockRestore();}
  });
  it("routes allowlisted hover effort choices through the existing controller", async () => {
    const handle = vi.spyOn(SettingsController.prototype, "handle").mockResolvedValue({} as never);
    try {
      await activate(context() as never);
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

  it("previews the hover choice before the slow controller finishes", async () => {
    const preview = vi.spyOn(SettingsStatusBar.prototype, "previewEffort");
    let finish: (value: never) => void = () => undefined;
    const handle = vi.spyOn(SettingsController.prototype, "handle").mockImplementation(() => new Promise(resolve => {finish = resolve;}));
    const ctx = context();
    try {
      await activate(ctx as never);
      const changing = stub.commands.get(SET_EFFORT_COMMAND)?.("low");
      expect(preview).toHaveBeenLastCalledWith("low");
      finish({} as never); await changing;
      expect(preview).toHaveBeenLastCalledWith();
      expect(handle).toHaveBeenCalledWith({type: "set", control: "effort", value: "low", tool: null});
    } finally {preview.mockRestore(); handle.mockRestore(); ctx.subscriptions.forEach(item => item.dispose());}
  });
  it("opens the actual Nexus panel when a hover effort change needs attention", async () => {
    const handle = vi.spyOn(SettingsController.prototype, "handle").mockResolvedValue({applicationIssues: ["Claude Code: expected high, read low."]} as never);
    const ctx = context();
    try {
      await activate(ctx as never);
      await stub.commands.get(SET_EFFORT_COMMAND)?.("high");
      expect(stub.executed).toContain(OPEN_COMMAND);
      expect(stub.executed).toContain("workbench.view.extension.nexusHubSettings");
      expect(stub.executed).toContain("nexusHubSettings.view.focus");
    } finally { handle.mockRestore(); ctx.subscriptions.forEach(item => item.dispose()); }
  });
  it("toggles the user compact preference from the hover", async () => {
    stub.defaults["nexusHubSettings.compactStatusBar"] = true;
    await activate(context() as never);
    await stub.commands.get(COMPACT_COMMAND)?.();
    expect(stub.user["nexusHubSettings.compactStatusBar"]).toBe(false);
    await stub.commands.get(COMPACT_COMMAND)?.();
    expect(stub.user["nexusHubSettings.compactStatusBar"]).toBe(true);
  });
  it("registers the webview view, the open command, and watchers for every file the state depends on", async () => {
    const ctx = context();
    await activate(ctx as never);

    expect(stub.providers.map((p) => p.id)).toEqual(["nexusHubSettings.view"]);
    expect(stub.providers[0]?.options).toEqual({ webviewOptions: { retainContextWhenHidden: true } });
    expect(stub.commands.has(OPEN_COMMAND)).toBe(true);
    expect(stub.watchers).toHaveLength(6 + 3 + 2);
    expect(ctx.subscriptions.length).toBeGreaterThan(10);
  });

  it("opens the panel by focusing its view", async () => {
    await activate(context() as never);
    await stub.commands.get(OPEN_COMMAND)?.();
    expect(stub.executed).toContain("nexusHubSettings.view.focus");
  });

  it("reads the current model on request and shows the install card when Nexus-Hub is missing", async () => {
    const api = await activate(context() as never);
    const model = await api.getViewModel();
    expect(model.status).toBe("error");
    expect(model.error?.title).toBe("Nexus-Hub is not installed");
    expect(model.header.profile).toBe("Default");
  });

  it("re-reads after a file or setting change, debounced, and ignores unrelated settings", async () => {
    vi.useFakeTimers();
    const ctx = context();
    await activate(ctx as never);

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

it("restarts only the selected provider after confirmation and preserves cancellation", async () => {
  const codex = vi.fn().mockResolvedValue({refreshed: 2});
  const claude = vi.fn().mockResolvedValue({sessions: 1});
  stub.vendorExtensions.set("openai.chatgpt", {extensionPath: "", isActive: true, exports: {nexusRestartProvider: codex}});
  stub.vendorExtensions.set("anthropic.claude-code", {extensionPath: "", isActive: true, exports: {nexusRestartProvider: claude}});
  stub.warningAnswer = () => undefined;
  await restartProvider("codex"); expect(codex).not.toHaveBeenCalled();
  stub.warningAnswer = (buttons) => buttons[0];
  await restartProvider("codex"); expect(codex).toHaveBeenCalledTimes(1); expect(claude).not.toHaveBeenCalled();
  await restartProvider("claude"); expect(claude).toHaveBeenCalledTimes(1);
  expect(stub.executed).not.toContain("workbench.action.restartExtensionHost");
  stub.trusted = false; await restartProvider("codex"); expect(codex).toHaveBeenCalledTimes(1);
});

it("routes the restart buttons to registered native lifecycles when provider exports are empty", async () => {
  const connection = {initialized: true, internalNotificationHandlers: new Set(), startCodexProcess: vi.fn(() => ({success: true}))};
  const comm = {channels: new Map([["session", {}]]), restartSessionsWhenIdle: vi.fn()};
  const host = globalThis as typeof globalThis & {[key: symbol]: unknown};
  host[Symbol.for("nexusHub.nativeRecovery.v1")] = {codex: connection, claude: new Set([new WeakRef(comm)])};
  try {
    for (const id of ["openai.chatgpt", "anthropic.claude-code"]) { stub.vendorExtensions.set(id, {extensionPath: "", isActive: true, exports: undefined}); }
    await restartProvider("codex"); expect(connection.startCodexProcess).toHaveBeenCalledTimes(1); expect(comm.restartSessionsWhenIdle).not.toHaveBeenCalled();
    await restartProvider("claude"); expect(comm.restartSessionsWhenIdle).toHaveBeenCalledTimes(1);
    expect(stub.executed).not.toContain("workbench.action.reloadWindow");
    expect(stub.executed).not.toContain("workbench.action.restartExtensionHost");
  } finally { delete host[Symbol.for("nexusHub.nativeRecovery.v1")]; }
});

it("registers the Codex toolbar before slow native adapter setup completes", async () => {
  let release!: (value: undefined) => void;
  const pending = new Promise<undefined>(resolve => { release = resolve; });
  const live = vi.spyOn(liveEffort, "installLiveEffort").mockReturnValue(pending);
  const native = vi.spyOn(nativeUi, "installNativeUi").mockResolvedValue(undefined);
  const ctx = context();
  try {
    const loading = activate(ctx as never);
    expect(stub.commands.has("nexusHubSettings.openCodex")).toBe(true);
    expect(stub.commands.has("nexusHubSettings.refreshCodexTab")).toBe(true);
    expect(stub.providers.map(item => item.id)).toContain("nexusHubSettings.view");
    await stub.commands.get(OPEN_COMMAND)?.();
    expect(stub.executed).toContain("workbench.view.extension.nexusHubSettings");
    await stub.commands.get("nexusHubSettings.openCodex")?.();
    expect(stub.executed).toContain("vscode.openWith");
    release(undefined); await loading;
  } finally { release(undefined); ctx.subscriptions.forEach(item => item.dispose()); live.mockRestore(); native.mockRestore(); }
});

it("refreshes Codex tabs through its recovery adapter and explains every unavailable state", async () => {
  stub.trusted = false; await refreshCodexTab(); expect(stub.warnings).toEqual([]);
  stub.trusted = true; await refreshCodexTab();
  expect(stub.warnings.at(-1)?.message).toContain("not installed");
  const refresh = vi.fn().mockResolvedValue(undefined); const activateCodex = vi.fn().mockResolvedValue({});
  stub.vendorExtensions.set("openai.chatgpt", {extensionPath: "", isActive: false, activate: activateCodex} as never);
  await refreshCodexTab(); expect(activateCodex).toHaveBeenCalled(); expect(stub.warnings.at(-1)?.message).toContain("native recovery is not connected");
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
  stub.vendorExtensions.set("openai.chatgpt", {extensionPath: "", isActive: true, exports: {nexusRefreshTab: refresh}});
  const before = stub.warnings.length; await refreshCodexTab();
  expect(refresh).toHaveBeenCalledTimes(1); expect(stub.warnings).toHaveLength(before);
});

it("leaves all extensions running when the user cancels the selected-provider restart", async () => {
  stub.vendorExtensions.set("anthropic.claude-code", {extensionPath: "", isActive: true, exports: {}});
  stub.warningAnswer = () => undefined;
  await restartProvider("claude");
  expect(stub.warnings.at(-1)?.buttons).toEqual(["Restart Claude Code"]);
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
});

it("explains an unadapted vendor build that exports nothing instead of throwing a TypeError", async () => {
  stub.warningAnswer = (buttons) => buttons[0];
  stub.vendorExtensions.set("openai.chatgpt", {extensionPath: "", isActive: true, exports: undefined, packageJSON: {version: "26.1111.21308"}} as never);
  await restartProvider("codex");
  const restart = stub.warnings.at(-1)?.message ?? "";
  expect(restart).not.toContain("TypeError");
  expect(restart).toContain("native recovery is not connected");
  expect(restart).not.toContain("26.1111.21308");
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
  await refreshCodexTab();
  expect(stub.warnings.at(-1)?.message ?? "").not.toContain("TypeError");
});

it.each(["claude", "codex"] as const)("reports %s activation failure without offering a window reload", async (provider) => {
  stub.vendorExtensions.set(provider === "claude" ? "anthropic.claude-code" : "openai.chatgpt", {extensionPath: "", isActive: false, activate: vi.fn().mockRejectedValue(new Error("startup failed"))} as never);
  await restartProvider(provider);
  expect(stub.warnings.at(-1)?.message).toBe("startup failed");
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
});

it("reports a targeted recovery failure without restarting unrelated extensions", async () => {
  stub.vendorExtensions.set("openai.chatgpt", {extensionPath: "", isActive: true, exports: {nexusRestartProvider: vi.fn().mockRejectedValue(new Error("failed"))}});
  await restartProvider("codex");
  expect(stub.warnings.at(-1)?.message).toBe("failed");
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
});

it("offers one window reload when a provider started before its launcher was repaired", async () => {
  await announceStalledStart([]);
  expect(stub.warnings).toEqual([]);
  stub.warningAnswer = (buttons) => buttons[0];
  await announceStalledStart(["Codex"]);
  expect(stub.warnings.at(-1)).toMatchObject({ message: expect.stringContaining("Codex started before Nexus-Hub repaired its launcher"), buttons: ["Reload Window"] });
  expect(stub.executed).toContain("workbench.action.reloadWindow");
  stub.executed.length = 0; stub.warningAnswer = () => undefined;
  await announceStalledStart(["Claude Code", "Codex"]);
  expect(stub.warnings.at(-1)?.message).toContain("Claude Code and Codex started before Nexus-Hub repaired their launchers");
  expect(stub.executed).not.toContain("workbench.action.reloadWindow");
});

it("rejects usage-alert preferences outside the allowlist", async () => {
  const api = await activate(context() as never);
  expect(() => api.setUsageAlert("gemini-pro" as never, true)).toThrow("Invalid usage-alert preference");
  expect(() => api.setUsageAlert("all", "yes" as never)).toThrow("Invalid usage-alert preference");
});
