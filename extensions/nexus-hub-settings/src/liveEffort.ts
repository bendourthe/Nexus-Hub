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
export interface LiveEffortSummary { connected: number; applied: number; reloadRequired: boolean; missing?: string[]; error?: string }
/** `stalled` names providers that started from an incomplete runtime before this activation repaired their launcher. */
export interface LiveEffortBridge { directory: string; stalled: string[]; summary(): Promise<LiveEffortSummary> }

async function immutable(file: string, content: Buffer | string): Promise<void> {
  try { await fs.writeFile(file, content, { flag: "wx" }); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") { throw error; }
    if (digest(await fs.readFile(file)) !== digest(content)) { throw new Error("A Nexus live-effort runtime file was changed. Its current contents were preserved."); }
  }
}

/**
 * The proxy runs outside the extension folder, so it needs every local module it loads.
 * Following `require("./x")` in the compiled output keeps the copy complete when the proxy gains an import.
 */
async function proxyModules(out: string): Promise<Map<string, Buffer>> {
  const modules = new Map<string, Buffer>();
  const pending = ["liveEffortProxy.js"];
  while (pending.length) {
    const name = pending.shift()!;
    if (modules.has(name)) { continue; }
    const content = await fs.readFile(path.join(out, name));
    modules.set(name, content);
    for (const [, local] of content.toString("utf8").matchAll(/require\("\.\/([\w.-]+)"\)/g)) { pending.push(local!.endsWith(".js") ? local! : local + ".js"); }
  }
  return modules;
}

/** Immutable runtime files survive extension updates. Existing customized files are never overwritten. */
export async function prepareWindowsRuntime(extension: string, directory: string): Promise<{ launcher: string; script: string }> {
  const modules = await proxyModules(path.join(extension, "out"));
  const source = await fs.readFile(path.join(extension, "media", "effort-launcher.cs"));
  const build = path.join(directory, "runtime-" + digest(Buffer.concat([source, ...[...modules].flatMap(([name, content]) => [Buffer.from(name), content])])).slice(0, 20));
  await fs.mkdir(build, { recursive: true });
  const scriptPath = path.join(build, "proxy.js"), sourcePath = path.join(build, "launcher.cs"), launcher = path.join(build, "launcher.exe"), receipt = path.join(build, "launcher.sha256");
  await immutable(sourcePath, source);
  for (const [name, content] of modules) { await immutable(name === "liveEffortProxy.js" ? scriptPath : path.join(build, name), content); }
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

/**
 * A provider that started before this activation used the launcher it was configured with then. When that
 * launcher's proxy requires a local module its runtime folder lacks, the provider's process already failed and
 * does not restart itself, so only a window reload connects it. Each runtime is judged by its own imports, so an
 * older build that never needed a newer module is not reported.
 */
export async function startedFromIncompleteRuntime(previousLauncher: unknown, directory: string): Promise<boolean> {
  if (!owned(directory, previousLauncher)) { return false; }
  let script: unknown;
  try { script = (JSON.parse(await fs.readFile(path.join(path.dirname(previousLauncher), "bridge.json"), "utf8")) as { script?: unknown }).script; }
  catch { return false; }
  if (!owned(directory, script)) { return false; }
  const runtime = path.dirname(script), seen = new Set<string>(), pending = [path.basename(script)];
  while (pending.length) {
    const name = pending.shift()!;
    if (seen.has(name)) { continue; }
    seen.add(name);
    let content: string;
    try { content = await fs.readFile(path.join(runtime, name), "utf8"); } catch { return true; }
    for (const [, local] of content.matchAll(/require\("\.\/([\w.-]+)"\)/g)) { pending.push(local!.endsWith(".js") ? local! : local + ".js"); }
  }
  return false;
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
  let inspector: string | undefined, inspectedAt = 0, unbridged: Provider[] = [];
  const stalled: string[] = [];
  try {
    await fs.mkdir(statuses, { recursive: true });
    const runtime = await prepareWindowsRuntime(context.extensionUri.fsPath, directory);
    inspector = runtime.launcher;
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
      if (previous !== executable) {
        if (item.installed!.isActive && await startedFromIncompleteRuntime(previous, directory)) { stalled.push(item.provider === "claude" ? "Claude Code" : "Codex"); }
        await config.update(item.setting, executable, vscode.ConfigurationTarget.Global); reloadRequired ||= !!item.installed!.isActive;
      }
      } catch (error) { setupError ??= error instanceof Error ? error.message : "A native live-effort connection could not be installed."; }
    }
  } catch (error) { setupError = error instanceof Error ? error.message : "The live effort bridge could not be installed."; }
  return {
    directory: statuses,
    stalled,
    async summary(): Promise<LiveEffortSummary> {
      let connected = 0, applied = 0, error = setupError;
      const seen = new Set<Provider>();
      let requested: unknown;
      try { requested = (JSON.parse(await fs.readFile(path.join(hub, "preferences.json"), "utf8")) as { default_effort?: unknown }).default_effort; } catch { /* The settings engine reports an unreadable preference. */ }
      for (const file of await fs.readdir(statuses).catch(() => [])) {
        if (!/^\d+-[a-f0-9-]+\.json$/.test(file)) { continue; }
        try {
          const metadata = await fs.stat(path.join(statuses, file));
          if (!metadata.isFile() || metadata.size > 16384) { continue; }
          const state = JSON.parse(await fs.readFile(path.join(statuses, file), "utf8")) as { pid?: number; childPid?: number; clientPid?: number; provider?: Provider; requested?: unknown; applied?: boolean; sessions?: number; error?: string };
          if (state.clientPid !== process.pid || !available.some((item) => item.provider === state.provider)) { continue; }
          if (!Number.isInteger(state.pid) || !Number.isInteger(state.childPid) || state.pid! <= 0 || state.childPid! <= 0) { continue; }
          process.kill(state.pid!, 0); process.kill(state.childPid!, 0);
          seen.add(state.provider!);
          const count = Number.isInteger(state.sessions) && state.sessions! > 0 && state.sessions! <= 10000 ? state.sessions! : 0;
          connected += count;
          if (effort(requested) && state.requested === requested && state.applied) { applied += count; }
          if (typeof state.error === "string" && state.error) { error = state.error.slice(0, 500); }
        } catch { /* Stale, partial or unreadable status records do not represent connected sessions. */ }
      }
      if (inspector && Date.now() - inspectedAt > 1000) {
        inspectedAt = Date.now();
        try {
          const result = await execute(inspector, ["--nexus-editor-connections", String(process.pid)], { windowsHide: true, timeout: 2000, maxBuffer: 4096 });
          const clients: unknown = JSON.parse(result.stdout);
          if (!Array.isArray(clients)) { throw new Error("Invalid client status"); }
          unbridged = clients.filter((client): client is Provider => client === "claude" || client === "codex");
        } catch { error ??= "The editor's agent connections could not be verified."; }
      }
      const missing = available.filter((item) => unbridged.includes(item.provider)).map((item) => item.provider === "claude" ? "Claude Code" : "Codex");
      return { connected, applied, reloadRequired: missing.length > 0 || (reloadRequired && !seen.size), missing, ...error ? { error } : {} };
    },
  };
}
