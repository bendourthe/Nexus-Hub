import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type * as vscode from "vscode";
import { installLiveEffort, prepareWindowsRuntime } from "../src/liveEffort";
import { stub, Uri } from "./vscode-stub";

const extension = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const directories: string[] = [];
beforeEach(() => stub.reset());
afterEach(async () => { vi.unstubAllEnvs(); for (const directory of directories.splice(0)) { await fs.rm(directory, { recursive: true, force: true }); } });

describe.skipIf(process.platform !== "win32")("real Windows protocol launcher", () => {
  async function installation() {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-install-live-")); directories.push(directory); vi.stubEnv("NEXUS_HUB_HOME", directory);
    for (const [id, binary] of [["anthropic.claude-code", "resources/native-binary/claude.exe"], ["openai.chatgpt", "bin/windows-x86_64/codex.exe"]]) {
      const location = path.join(directory, id!, binary!); await fs.mkdir(path.dirname(location), { recursive: true }); await fs.writeFile(location, "native-test-placeholder");
      stub.vendorExtensions.set(id!, { extensionPath: path.join(directory, id!), isActive: true });
    }
    stub.defaults["claudeCode.claudeProcessWrapper"] = ""; stub.defaults["chatgpt.cliExecutable"] = "";
    const saved = new Map<string, unknown>();
    const context = { extensionUri: Uri.file(extension), globalStorageUri: Uri.file(path.join(directory, "profile")), globalState: { get: (key: string) => saved.get(key), update: async (key: string, value: unknown) => { saved.set(key, value); } } } as unknown as vscode.ExtensionContext;
    return { directory, context, saved };
  }
  it("installs only native launch keys and preserves later user customizations", async () => {
    const { context, saved } = await installation(); const bridge = await installLiveEffort(context);
    expect(stub.updates.map((entry) => entry.key)).toEqual(["claudeCode.claudeProcessWrapper", "chatgpt.cliExecutable"]);
    expect(await bridge!.summary()).toMatchObject({ reloadRequired: true, connected: 0 });
    expect(saved.get("live-effort-original:claudeCode.claudeProcessWrapper")).toEqual({ present: false, value: undefined });
    const first = { ...stub.user }; await installLiveEffort(context); expect(stub.user).toEqual(first); expect(stub.updates).toHaveLength(2);
    stub.user["claudeCode.claudeProcessWrapper"] = "C:\\custom\\claude.exe"; stub.user["chatgpt.cliExecutable"] = "C:\\custom\\codex.exe";
    const customized = { ...stub.user }; const again = await installLiveEffort(context);
    expect(stub.user).toEqual(customized); expect((await again!.summary()).error).toContain("preserved");
  }, 45000);
  it("does not count other windows or hide a missing provider behind acknowledged Claude sessions", async () => {
    const { context, directory } = await installation(); const bridge = await installLiveEffort(context);
    await fs.writeFile(path.join(directory, "preferences.json"), '{"default_effort":"medium"}');
    const record = { pid: process.pid, childPid: process.pid, clientPid: process.pid, requested: "medium", applied: true, sessions: 2 };
    await fs.writeFile(path.join(bridge!.directory, `${process.pid}-aaaa.json`), JSON.stringify({ ...record, provider: "claude" }));
    await fs.writeFile(path.join(bridge!.directory, `${process.pid}-bbbb.json`), JSON.stringify({ ...record, provider: "codex", clientPid: process.pid + 1, sessions: 20 }));
    const executable = path.join(directory, "codex.exe"); await fs.copyFile(process.execPath, executable);
    const child = spawn(executable, ["-e", "console.log('ready');process.stdin.resume()"], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
    const finished = new Promise<void>((resolve, reject) => { child.once("error", reject); child.once("close", (code) => code === 0 ? resolve() : reject(new Error("Test native process failed"))); });
    try {
      await new Promise<void>((resolve, reject) => { child.stdout.once("data", () => resolve()); child.once("error", reject); });
      expect(await bridge!.summary()).toMatchObject({ connected: 2, applied: 2, missing: ["Codex"], reloadRequired: true });
    } finally { child.stdin.end(); await finished; }
    await fs.writeFile(path.join(bridge!.directory, `${process.pid}-cccc.json`), JSON.stringify({ ...record, provider: "codex", sessions: 0 }));
    const refreshed = await installLiveEffort(context);
    expect(await refreshed!.summary()).toMatchObject({ connected: 2, applied: 2, missing: [], reloadRequired: false });
  }, 45000);
  it("records the real editor client parent from the Windows launcher", async () => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-live-client-")); directories.push(directory);
    const runtime = await prepareWindowsRuntime(extension, directory); const launcher = path.join(directory, "bridge.exe"); await fs.copyFile(runtime.launcher, launcher);
    await fs.writeFile(path.join(directory, "preferences.json"), '{"default_effort":"medium"}');
    const statusDirectory = path.join(directory, "status");
    await fs.writeFile(path.join(directory, "bridge.json"), JSON.stringify({ provider: "codex", target: process.execPath, runtime: process.execPath, script: runtime.script, preferences: path.join(directory, "preferences.json"), statusDirectory }));
    const child = spawn(launcher, ["-e", "console.log('{}');process.stdin.resume()", "app-server"], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
    const finished = new Promise<void>((resolve, reject) => { child.once("error", reject); child.once("close", (code) => code === 0 ? resolve() : reject(new Error("Launcher failed"))); });
    try {
      await new Promise<void>((resolve, reject) => { child.stdout.once("data", () => resolve()); child.once("error", reject); });
      const files = await fs.readdir(statusDirectory); const state = JSON.parse(await fs.readFile(path.join(statusDirectory, files.find((file) => file.endsWith(".json"))!), "utf8"));
      expect(state.clientPid).toBe(process.pid);
    } finally { child.stdin.end(); await finished; }
  }, 45000);
  it("preserves workspace overrides and custom Claude wrappers while connecting Codex", async () => {
    const { context } = await installation(); stub.user["claudeCode.claudeProcessWrapper"] = "C:\\my-wrapper.exe";
    await installLiveEffort(context); expect(stub.user["claudeCode.claudeProcessWrapper"]).toBe("C:\\my-wrapper.exe"); expect(stub.updates.map((entry) => entry.key)).toEqual(["chatgpt.cliExecutable"]);
    stub.reset(); const next = await installation(); stub.workspace["chatgpt.cliExecutable"] = "C:\\workspace.exe";
    await installLiveEffort(next.context); expect(stub.updates.map((entry) => entry.key)).toEqual(["claudeCode.claudeProcessWrapper"]);
  }, 45000);
  it("fails open for blocked status directories and skips installation in untrusted workspaces", async () => {
    const { context, directory } = await installation(); await fs.writeFile(path.join(directory, "live-effort"), "user file");
    const bridge = await installLiveEffort(context); expect((await bridge!.summary()).error).toBeTruthy(); expect(stub.updates).toEqual([]);
    stub.trusted = false; expect(await installLiveEffort(context)).toBeUndefined();
    expect(await fs.readFile(path.join(directory, "live-effort"), "utf8")).toBe("user file");
  }, 45000);
  it("flushes request traffic while the client keeps stdin open", async () => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-live-flush-")); directories.push(directory);
    const runtime = await prepareWindowsRuntime(extension, directory); const launcher = path.join(directory, "bridge.exe"); await fs.copyFile(runtime.launcher, launcher);
    await fs.writeFile(path.join(directory, "bridge.json"), JSON.stringify({ provider: "codex", target: process.execPath, runtime: process.execPath, script: runtime.script, preferences: path.join(directory, "preferences.json"), statusDirectory: path.join(directory, "status") }));
    await new Promise<void>((resolve, reject) => {
      const child = spawn(launcher, ["-e", "process.stdin.on('data',x=>process.stdout.write(x))"], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
      const timer = setTimeout(() => { child.kill(); reject(new Error("No reply before stdin EOF")); }, 5000);
      let received = false;
      child.on("error", reject); child.stdout.once("data", (value: Buffer) => { expect(value.toString()).toBe("request\n"); received = true; child.stdin.end(); });
      child.once("close", (code) => { clearTimeout(timer); if (received && code === 0) { resolve(); } else { reject(new Error("Launcher exited without replying")); } });
      child.stdin.write("request\n");
    });
  }, 45000);
  it("compiles once, relays UTF-8 streams and preserves quoted arguments and native exit status", async () => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-live-launcher-")); directories.push(directory);
    const runtime = await prepareWindowsRuntime(extension, directory);
    expect(await prepareWindowsRuntime(extension, directory)).toEqual(runtime);
    const profile = path.join(directory, "profile with spaces-ñ"); await fs.mkdir(profile);
    const launcher = path.join(profile, "bridge.exe"); await fs.copyFile(runtime.launcher, launcher);
    await fs.writeFile(path.join(profile, "bridge.json"), JSON.stringify({ provider: "codex", target: process.execPath, runtime: process.execPath, script: runtime.script, preferences: path.join(profile, "preferences.json"), statusDirectory: path.join(profile, "status") }));
    const argumentsToPreserve = ["two words", 'a "quoted" value', "C:\\ends with slash\\", "日本語"];
    const code = "process.stderr.write(JSON.stringify(process.argv.slice(1)));process.stdin.pipe(process.stdout);process.stdin.on('end',()=>{process.exitCode=7})";
    const result = await new Promise<{ code: number | null; stdout: string; stderr: string }>((resolve, reject) => {
      const child = spawn(launcher, ["-e", code, ...argumentsToPreserve], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
      let stdout = "", stderr = "";
      child.stdout.setEncoding("utf8"); child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk: string) => stdout += chunk); child.stderr.on("data", (chunk: string) => stderr += chunk);
      child.on("error", reject); child.on("close", (exit) => resolve({ code: exit, stdout, stderr }));
      child.stdin.end("Nexus 日本語\n");
    });
    expect(result.code).toBe(7); expect(result.stdout).toBe("Nexus 日本語\n"); expect(JSON.parse(result.stderr)).toEqual(argumentsToPreserve);
  }, 45000);

  it("refuses to overwrite a modified runtime file", async () => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-live-preserve-")); directories.push(directory);
    const runtime = await prepareWindowsRuntime(extension, directory);
    await fs.writeFile(runtime.script, "user modification");
    await expect(prepareWindowsRuntime(extension, directory)).rejects.toThrow("preserved");
    expect(await fs.readFile(runtime.script, "utf8")).toBe("user modification");
  }, 45000);
});
