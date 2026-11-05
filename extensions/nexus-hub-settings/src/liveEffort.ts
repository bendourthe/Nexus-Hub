import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as vscode from "vscode";
import { installRoot } from "./cliBridge";
import { effort, type Provider, type ProxyConfig } from "./liveEffortProxy";

const execute = promisify(execFile);
const digest = (value: string | Buffer): string => createHash("sha256").update(value).digest("hex");
const owned = (root: string, file: unknown): file is string => typeof file === "string" && path.relative(root, file) !== "" && !path.relative(root, file).startsWith("..") && !path.isAbsolute(path.relative(root, file));
const exists = async (file: string): Promise<boolean> => { try { return (await fs.stat(file)).isFile(); } catch { return false; } };
export interface LiveEffortSummary { connected: number; applied: number; reloadRequired: boolean; error?: string }
export interface LiveEffortBridge { directory: string; summary(): Promise<LiveEffortSummary> }

async function immutable(file: string, content: Buffer | string): Promise<void> {
  try { await fs.writeFile(file, content, { flag: "wx" }); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") { throw error; }
    if (digest(await fs.readFile(file)) !== digest(content)) { throw new Error("A Nexus live-effort runtime file was changed. Its current contents were preserved."); }
  }
}

/** Immutable runtime files survive extension updates. Existing customized files are never overwritten. */
export async function prepareWindowsRuntime(extension: string, directory: string): Promise<{ launcher: string; script: string }> {
  const script = await fs.readFile(path.join(extension, "out", "liveEffortProxy.js"));
  const source = await fs.readFile(path.join(extension, "media", "effort-launcher.cs"));
  const stream = await fs.readFile(path.join(extension, "out", "nativeStreamProcess.js"));
  const build = path.join(directory, "runtime-" + digest(Buffer.concat([script, source, stream])).slice(0, 20));
  await fs.mkdir(build, { recursive: true });
  const scriptPath = path.join(build, "proxy.js"), sourcePath = path.join(build, "launcher.cs"), launcher = path.join(build, "launcher.exe"), receipt = path.join(build, "launcher.sha256");
  await immutable(scriptPath, script); await immutable(sourcePath, source);
  await immutable(path.join(build, "nativeStreamProcess.js"), stream);
  if (!(await exists(launcher))) {
    const windows = process.env.SystemRoot ?? "C:\\Windows";
    const compiler = [path.join(windows, "Microsoft.NET", "Framework64", "v4.0.30319", "csc.exe"), path.join(windows, "Microsoft.NET", "Framework", "v4.0.30319", "csc.exe")];
    const command = (await Promise.all(compiler.map(async (candidate) => await exists(candidate) ? candidate : null))).find(Boolean);
    if (!command) { throw new Error("The Windows .NET launcher compiler is unavailable."); }
    const temporary = path.join(build, `launcher-${randomUUID()}.exe`);
    try {
      await execute(command, ["/nologo", "/target:exe", "/optimize+", "/r:System.Web.Extensions.dll", `/out:${temporary}`, sourcePath], { windowsHide: true, timeout: 30000, maxBuffer: 1_000_000 });
      try { await fs.copyFile(temporary, launcher, fs.constants.COPYFILE_EXCL); }
      catch (error) { if ((error as NodeJS.ErrnoException).code !== "EEXIST") { throw error; } }
      await immutable(receipt, digest(await fs.readFile(launcher)));
    } finally { await fs.unlink(temporary).catch(() => undefined); }
  }
  // Concurrent editor startup can reach the executable just before its receipt is published.
  for (let attempt = 0; !(await exists(receipt)) && attempt < 20; attempt++) { await new Promise((resolve) => setTimeout(resolve, 50)); }
  if ((await fs.readFile(receipt, "utf8")) !== digest(await fs.readFile(launcher))) { throw new Error("The Nexus live-effort launcher was changed. It was preserved."); }
  return { launcher, script: scriptPath };
}

export async function installLiveEffort(context: vscode.ExtensionContext): Promise<LiveEffortBridge | undefined> {
  const providers: { provider: Provider; extension: string; setting: string; binary: string }[] = [
    { provider: "claude", extension: "anthropic.claude-code", setting: "claudeCode.claudeProcessWrapper", binary: path.join("resources", "native-binary", "claude.exe") },
    { provider: "codex", extension: "openai.chatgpt", setting: "chatgpt.cliExecutable", binary: path.join("bin", "windows-x86_64", "codex.exe") },
  ];
  const available = providers.map((item) => ({ ...item, installed: vscode.extensions?.getExtension(item.extension) })).filter((item) => item.installed);
  if (!available.length || !vscode.workspace.isTrusted || process.platform !== "win32") { return undefined; }
  const hub = installRoot(process.env, os.homedir());
  const directory = path.join(hub, "live-effort");
  const statuses = path.join(directory, "sessions");
  let reloadRequired = false, setupError: string | undefined;
  try {
    await fs.mkdir(statuses, { recursive: true });
    const runtime = await prepareWindowsRuntime(context.extensionUri.fsPath, directory);
    for (const item of available) {
      try {
      const config = vscode.workspace.getConfiguration();
      const layers = config.inspect<unknown>(item.setting);
      if (layers?.workspaceValue !== undefined || layers?.workspaceFolderValue !== undefined) { throw new Error(`A workspace overrides ${item.setting}; its launch setting was preserved.`); }
      const previous = layers?.globalValue;
      if (previous !== undefined && previous !== "" && !owned(directory, previous)) {
        const saved = context.globalState.get<{ present: boolean; value?: unknown }>(`live-effort-original:${item.setting}`);
        if (saved !== undefined) { throw new Error(`A custom ${item.provider} launch setting is configured; it was preserved.`); }
      }
      const backup = `live-effort-original:${item.setting}`;
      if (context.globalState.get(backup) === undefined && !owned(directory, previous)) { await context.globalState.update(backup, { present: previous !== undefined, value: previous }); }
      const original = context.globalState.get<{ present: boolean; value?: unknown }>(backup);
      const native = item.provider === "codex" && typeof original?.value === "string" && original.value.trim() ? original.value : path.join(item.installed!.extensionPath, item.binary);
      if (item.provider === "claude" && typeof original?.value === "string" && original.value.trim()) { throw new Error("A custom Claude process wrapper is already configured; it was preserved."); }
      if (!path.isAbsolute(native) || !(await exists(native))) { throw new Error(`The ${item.provider} native executable is unavailable.`); }
      const configuration: ProxyConfig & { runtime: string; script: string } = { provider: item.provider, target: native, preferences: path.join(hub, "preferences.json"), statusDirectory: statuses, modelsCache: path.join(process.env.CODEX_HOME || path.join(os.homedir(), ".codex"), "models_cache.json"), runtime: process.execPath, script: runtime.script };
      const serialized = JSON.stringify(configuration);
      const profile = digest(context.globalStorageUri.fsPath + serialized).slice(0, 20);
      const launchDirectory = path.join(directory, `${item.provider}-${profile}`);
      await fs.mkdir(launchDirectory, { recursive: true });
      const executable = path.join(launchDirectory, "bridge.exe");
      await immutable(path.join(launchDirectory, "bridge.json"), serialized);
      await immutable(executable, await fs.readFile(runtime.launcher));
      if (previous !== executable) { await config.update(item.setting, executable, vscode.ConfigurationTarget.Global); reloadRequired ||= !!item.installed!.isActive; }
      } catch (error) { setupError ??= error instanceof Error ? error.message : "A native live-effort connection could not be installed."; }
    }
  } catch (error) { setupError = error instanceof Error ? error.message : "The live effort bridge could not be installed."; }
  return {
    directory: statuses,
    async summary(): Promise<LiveEffortSummary> {
      let connected = 0, applied = 0, error = setupError;
      let requested: unknown;
      try { requested = (JSON.parse(await fs.readFile(path.join(hub, "preferences.json"), "utf8")) as { default_effort?: unknown }).default_effort; } catch { /* The settings engine reports an unreadable preference. */ }
      for (const file of await fs.readdir(statuses).catch(() => [])) {
        if (!/^\d+-[a-f0-9-]+\.json$/.test(file)) { continue; }
        try {
          const metadata = await fs.stat(path.join(statuses, file));
          if (!metadata.isFile() || metadata.size > 16384) { continue; }
          const state = JSON.parse(await fs.readFile(path.join(statuses, file), "utf8")) as { pid?: number; childPid?: number; requested?: unknown; applied?: boolean; sessions?: number; error?: string };
          if (!Number.isInteger(state.pid) || !Number.isInteger(state.childPid) || state.pid! <= 0 || state.childPid! <= 0) { continue; }
          process.kill(state.pid!, 0); process.kill(state.childPid!, 0);
          const count = Number.isInteger(state.sessions) && state.sessions! > 0 && state.sessions! <= 10000 ? state.sessions! : 0;
          connected += count;
          if (effort(requested) && state.requested === requested && state.applied) { applied += count; }
          if (typeof state.error === "string" && state.error) { error = state.error.slice(0, 500); }
        } catch { /* Stale, partial or unreadable status records do not represent connected sessions. */ }
      }
      return { connected, applied, reloadRequired, ...error ? { error } : {} };
    },
  };
}
