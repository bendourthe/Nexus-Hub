import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { env, stub } from "./vscode-stub";
import { installNativeUi } from "../src/vendorUi";
import { installVendorUi } from "../src/vendorUiInstall";
vi.mock("../src/vendorUiInstall", () => ({ installVendorUi: vi.fn() }));
let directory: string;
let original: string | undefined;
let subscriptions: { dispose(): unknown }[];
// The native UI bridge is Windows-only; these tests exercise that path with the vendor installer mocked, on every runner.
const platform = Object.getOwnPropertyDescriptor(process, "platform")!;
const setPlatform = (value: NodeJS.Platform) => Object.defineProperty(process, "platform", { ...platform, value });
const write = (value: unknown) => fs.writeFile(path.join(directory, "preferences.json"), JSON.stringify({ default_effort: value }));
const setup = () => installNativeUi({ subscriptions } as never);
beforeEach(async () => {
  stub.reset(); subscriptions = []; setPlatform("win32");
  original = process.env.NEXUS_HUB_HOME; directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-ui-")); process.env.NEXUS_HUB_HOME = directory;
  vi.mocked(installVendorUi).mockReset().mockResolvedValue({ changed: false, receipt: "receipt" });
  await write("medium");
});
afterEach(async () => {
  env.appName = "Visual Studio Code"; env.appRoot = ""; Object.defineProperty(process, "platform", platform);
  subscriptions.forEach((entry) => entry.dispose());
  await fs.rm(directory, { recursive: true, force: true });
  if (original === undefined) { delete process.env.NEXUS_HUB_HOME; } else { process.env.NEXUS_HUB_HOME = original; }
});
it("synchronizes Cursor's built-in Agent without requiring a hosted vendor extension", async () => {
  env.appName = "Cursor"; env.appRoot = "cursor-app";
  const apply = vi.fn().mockResolvedValue({ready: true, updated: 1});
  stub.commands.set("nexusHubSettings.cursor.applyEffort", apply);
  const bridge = (await setup())!;
  expect(installVendorUi).toHaveBeenCalledWith("cursor", "cursor-app", path.join(directory, "native-ui"));
  expect(apply).toHaveBeenLastCalledWith({effort: "medium", revision: "medium:"});
  await write("low"); await bridge.synchronize();
  expect(apply).toHaveBeenLastCalledWith({effort: "low", revision: "low:"});
  expect(bridge.summary()).toEqual({reloadRequired: false, errors: []});
});
it("requires a Cursor restart until its native command is available", async () => {
  env.appName = "Cursor"; env.appRoot = "cursor-app";
  const bridge = (await setup())!;
  expect(bridge.summary().reloadRequired).toBe(true);
  stub.commands.set("nexusHubSettings.cursor.applyEffort", vi.fn());
  await bridge.synchronize(); expect(bridge.summary().reloadRequired).toBe(false);
});
it("updates both active UI owners repeatedly and picks up newly activated vendors", async () => {
  const claude = { extensionPath: "claude", isActive: true, exports: { nexusEffortBridgeVersion: 2, applyNexusEffort: vi.fn() } };
  const codex = { extensionPath: "codex", isActive: false, exports: { nexusEffortBridgeVersion: 2, applyNexusEffort: vi.fn() } };
  stub.vendorExtensions.set("anthropic.claude-code", claude); stub.vendorExtensions.set("openai.chatgpt", codex);
  const bridge = (await setup())!;
  expect(claude.exports.applyNexusEffort).toHaveBeenLastCalledWith("medium", "medium:");
  expect(codex.exports.applyNexusEffort).not.toHaveBeenCalled(); expect(bridge.summary().reloadRequired).toBe(false);
  codex.isActive = true; await write("ultra"); await bridge.synchronize();
  expect(claude.exports.applyNexusEffort).toHaveBeenLastCalledWith("ultra", "ultra:"); expect(codex.exports.applyNexusEffort).toHaveBeenLastCalledWith("ultra", "ultra:");
  await write("low"); await bridge.synchronize(); expect(codex.exports.applyNexusEffort).toHaveBeenLastCalledWith("low", "low:");
  await write("bad"); await bridge.synchronize(); expect(codex.exports.applyNexusEffort).toHaveBeenCalledTimes(2);
});
it("reports a loaded old UI instead of claiming a live update", async () => {
  stub.vendorExtensions.set("openai.chatgpt", { extensionPath: "codex", isActive: true });
  expect((await setup())!.summary().reloadRequired).toBe(true);
});
it("keeps Codex updating when Claude stalls and does not duplicate the pending Claude request", async () => {
  vi.useFakeTimers();
  const claude = vi.fn(() => new Promise(() => {})), codex = vi.fn(async () => {});
  for (const [id, apply] of [["anthropic.claude-code", claude], ["openai.chatgpt", codex]] as const) {
    stub.vendorExtensions.set(id, {extensionPath: id, isActive: true, exports: {nexusEffortBridgeVersion: 3, applyNexusEffort: vi.fn(), applyNexusDefaults: apply}});
  }
  try {
    const starting = setup();
    await vi.advanceTimersByTimeAsync(0);
    expect(codex).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(5000);
    const bridge = (await starting)!;
    expect(bridge.summary().errors).toEqual(["Claude Code: The native effort update failed."]);
    await write("low");
    const updating = bridge.synchronize();
    await vi.advanceTimersByTimeAsync(5000); await updating;
    expect(claude).toHaveBeenCalledTimes(1);
    expect(codex).toHaveBeenLastCalledWith(expect.objectContaining({effort: "low"}));
  } finally {subscriptions.forEach(item => item.dispose()); vi.useRealTimers();}
});
it("preserves an unsupported build and reports its adapter failure", async () => {
  const apply = vi.fn(); stub.vendorExtensions.set("openai.chatgpt", { extensionPath: "codex", isActive: true, exports: { nexusEffortBridgeVersion: 2, applyNexusEffort: apply } });
  vi.mocked(installVendorUi).mockRejectedValueOnce(Error("Build changed and preserved"));
  const bridge = (await setup())!; expect(bridge.summary().errors).toEqual(["Codex: Build changed and preserved"]); expect(apply).not.toHaveBeenCalled();
});
it("does not install adapters in an untrusted workspace or without native vendors", async () => {
  expect(await setup()).toBeUndefined();
  stub.vendorExtensions.set("openai.chatgpt", { extensionPath: "codex", isActive: true }); stub.trusted = false;
  expect(await setup()).toBeUndefined(); expect(installVendorUi).not.toHaveBeenCalled();
});
it.each(["linux", "darwin"] as const)("does not install adapters on %s", async (name) => {
  setPlatform(name); env.appName = "Cursor";
  stub.vendorExtensions.set("openai.chatgpt", { extensionPath: "codex", isActive: true });
  expect(await setup()).toBeUndefined(); expect(installVendorUi).not.toHaveBeenCalled();
});
