import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { stub } from "./vscode-stub";
import { installNativeUi } from "../src/vendorUi";
import { installVendorUi } from "../src/vendorUiInstall";
vi.mock("../src/vendorUiInstall", () => ({ installVendorUi: vi.fn() }));
let directory: string;
let original: string | undefined;
let subscriptions: { dispose(): unknown }[];
const write = (value: unknown) => fs.writeFile(path.join(directory, "preferences.json"), JSON.stringify({ default_effort: value }));
const setup = () => installNativeUi({ subscriptions } as never);
beforeEach(async () => {
  stub.reset(); subscriptions = [];
  original = process.env.NEXUS_HUB_HOME; directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-ui-")); process.env.NEXUS_HUB_HOME = directory;
  vi.mocked(installVendorUi).mockReset().mockResolvedValue({ changed: false, receipt: "receipt" });
  await write("medium");
});
afterEach(async () => {
  subscriptions.forEach((entry) => entry.dispose());
  await fs.rm(directory, { recursive: true, force: true });
  if (original === undefined) { delete process.env.NEXUS_HUB_HOME; } else { process.env.NEXUS_HUB_HOME = original; }
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
