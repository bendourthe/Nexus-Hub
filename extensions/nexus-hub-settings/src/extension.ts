import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";
import { initializeInstallationDefaults } from "./installationDefaults";
import { installLiveEffort } from "./liveEffort";
import { CliBridge, installRoot } from "./cliBridge";
import { ConfirmRequest, SettingsController, UiLike } from "./controller";
import { profileNameFromStorage } from "./editorWrites";
import { syncEditorEffort } from "./editorEffort";
import { SettingsViewProvider } from "./settingsView";
import { COMPACT_COMMAND, EFFORT_LABELS, SET_EFFORT_COMMAND, SettingsStatusBar } from "./statusBar";
import { ViewModel } from "./viewModel";
import { openCodexHistory } from "./codexHistory";
import { requestEffortApply } from "./liveEffortProxy";
import { installNativeUi } from "./vendorUi";
import { readSessionDefaults, SESSION_DEFAULTS_FILE, writeSessionDefault } from "./sessionDefaults";

/** What the live check (and other extensions) can call: the panel's current model, freshly read. */
export interface ExtensionApi {
  getViewModel(): Promise<ViewModel>;
  setFastMode(value: boolean): Promise<ViewModel>;
  setCodexTabs(value: boolean): Promise<ViewModel>;
}

const REFRESH_DELAY_MS = 400;
export const OPEN_COMMAND = "nexusHubSettings.open";

/** The user-level files the panel's state depends on. Project files are watched through the workspace. */
export function watchedFiles(env: NodeJS.ProcessEnv, home: string): string[] {
  const dir = (name: string, fallback: string): string => {
    const value = env[name]?.trim();
    return value ? value : path.join(home, fallback);
  };
  return [
    path.join(dir("CLAUDE_CONFIG_DIR", ".claude"), "settings.json"),
    path.join(dir("CODEX_HOME", ".codex"), "config.toml"),
    path.join(dir("COPILOT_HOME", ".copilot"), "settings.json"),
    path.join(home, ".nexus-hub", "guardrails.json"),
    path.join(home, ".nexus-hub", "preferences.json"),
    path.join(home, ".nexus-hub", "settings-control.json"),
  ];
}

export function vscodeUi(): UiLike {
  return {
    async openCodex(): Promise<void> { await vscode.commands.executeCommand("chatgpt.newCodexPanel"); },
    async confirm(request: ConfirmRequest): Promise<boolean> {
      const choice = await vscode.window.showWarningMessage(request.message, { modal: true, detail: request.detail }, request.confirmLabel);
      return choice === request.confirmLabel;
    },
    async openExternal(url: string): Promise<boolean> {
      return vscode.env.openExternal(vscode.Uri.parse(url));
    },
  };
}

export function firstFolder(): string | undefined {
  const folder = vscode.workspace.workspaceFolders?.[0];
  return folder && folder.uri.scheme === "file" ? folder.uri.fsPath : undefined;
}

/** Only the user's own value counts: a workspace can never choose the interpreter. */
export function userPythonPath(): string | undefined {
  const value = vscode.workspace.getConfiguration("nexusHubSettings").inspect<string>("pythonPath")?.globalValue;
  return typeof value === "string" ? value : undefined;
}

interface RecoveryApi { nexusRestartProvider?(): Promise<unknown>; nexusRefreshTab?(): Promise<unknown> }
async function providerApi(provider: "claude" | "codex"): Promise<RecoveryApi> {
  const extension = vscode.extensions.getExtension(provider === "claude" ? "anthropic.claude-code" : "openai.chatgpt");
  if (!extension) { throw new Error("This extension is not installed in this editor."); }
  return extension.isActive ? extension.exports as RecoveryApi : await extension.activate() as RecoveryApi;
}
export async function refreshCodexTab(): Promise<void> {
  if (!vscode.workspace.isTrusted) { return; }
  try {
    const api = await providerApi("codex");
    if (!api.nexusRefreshTab) { throw new Error("Reload this window once to activate the Codex tab recovery adapter."); }
    await api.nexusRefreshTab();
  } catch (error) { await vscode.window.showWarningMessage(String(error)); }
}
export async function restartProvider(provider: "claude" | "codex"): Promise<void> {
  if (!vscode.workspace.isTrusted) { return; }
  const name = provider === "claude" ? "Claude Code" : "Codex";
  const detail = provider === "codex" ? "Restart only Codex's app-server, then refresh its open tabs with their saved sessions. Running Codex requests may be interrupted. Other extensions keep running." : "Restart only Claude Code session processes. Idle sessions restart now; busy sessions restart at their next idle turn boundary. Other extensions keep running.";
  const choice = await vscode.window.showWarningMessage(`Restart ${name}?`, {modal: true, detail}, "Restart " + name);
  if (choice !== "Restart " + name) { return; }
  try {
    const api = await providerApi(provider);
    if (!api.nexusRestartProvider) { throw new Error("Reload this window once to activate provider-specific recovery. Other extensions were not restarted."); }
    await api.nexusRestartProvider();
  } catch (error) { await vscode.window.showWarningMessage(String(error)); }
}

export async function activate(context: vscode.ExtensionContext): Promise<ExtensionApi> {
  const hub = installRoot(process.env, os.homedir());
  if (vscode.workspace.isTrusted && fs.existsSync(path.join(hub, "VERSION"))) { initializeInstallationDefaults(hub); }
  const sessionFile = path.join(hub, SESSION_DEFAULTS_FILE);
  context.subscriptions.push(
    vscode.commands.registerCommand(OPEN_COMMAND, () => vscode.commands.executeCommand(`${SettingsViewProvider.viewType}.focus`)),
    vscode.commands.registerCommand("nexusHubSettings.codexHistory", openCodexHistory),
    vscode.commands.registerCommand("nexusHubSettings.refreshCodexTab", refreshCodexTab),
    vscode.commands.registerCommand("nexusHubSettings.openCodex", () => {
      if (!vscode.workspace.isTrusted) { return; }
      return vscode.commands.executeCommand(readSessionDefaults(sessionFile).codexTabs ? "chatgpt.newCodexPanel" : "chatgpt.openSidebar");
    }),
  );
  let liveEffort = await installLiveEffort(context);
  let nativeUi = await installNativeUi(context);
  const bridge = new CliBridge({ pythonPath: userPythonPath });
  const controller = new SettingsController({
    restartExtension: restartProvider,
    sessionDefaults: () => readSessionDefaults(sessionFile),
    setFastMode: async (value) => { writeSessionDefault(sessionFile, "fastMode", value); await nativeUi?.synchronize(); },
    setCodexTabs: async (value) => { writeSessionDefault(sessionFile, "codexTabs", value); },
    hubVersion: () => { try { return fs.readFileSync(path.join(hub, "VERSION"), "utf8").trim().slice(0, 40); } catch { return "Unknown"; } },
    applyAll: async () => { requestEffortApply(path.join(hub, "preferences.json")); writeSessionDefault(sessionFile, "applyAll"); await nativeUi?.synchronize(); },
    upgrade: async () => {
      const interpreter = bridge.interpreter();
      const args = [...interpreter.args, path.join(hub, "scripts", "nexus_hub_cli.py"), "upgrade"];
      const quote = (part: string): string => "'" + part.replace(/'/g, "''") + "'";
      const windows = process.platform === "win32";
      const terminal = vscode.window.createTerminal({
        name: "Nexus Hub Upgrade", cwd: hub,
        shellPath: windows ? path.join(process.env.SystemRoot || "C:\\Windows", "System32", "WindowsPowerShell", "v1.0", "powershell.exe") : interpreter.command,
        shellArgs: windows ? ["-NoLogo", "-NoProfile", "-NoExit", "-Command", "& " + [interpreter.command, ...args].map(quote).join(" ")] : args,
      });
      terminal.show();
    },
    bridge,
    liveEffort: async () => liveEffort?.summary(),
    uiEffort: () => nativeUi?.summary(),
    ui: vscodeUi(),
    isTrusted: () => vscode.workspace.isTrusted,
    project: firstFolder,
    profile: () => profileNameFromStorage(context.globalStorageUri.fsPath),
    platform: process.platform === "win32" ? "windows" : process.platform === "darwin" ? "macos" : "linux",
    codexAvailable: () => !!vscode.extensions?.getExtension("openai.chatgpt"),
    syncEditorEffort: (records) => syncEditorEffort(records, async (key, previous) => {
      const storageKey = `effort-backup:${key}`;
      if (context.globalState.get(storageKey) === undefined) { await context.globalState.update(storageKey, previous); }
    }),
  });

  let timer: ReturnType<typeof setTimeout> | undefined;
  let disposed = false;
  context.subscriptions.push({dispose: () => { disposed = true; }});
  const schedule = (): void => {
    if (disposed) { return; }
    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => void controller.synchronizeDefaults().catch((error: unknown) => console.error("Nexus Settings synchronization failed", error)), REFRESH_DELAY_MS);
  };
  context.subscriptions.push({ dispose: () => timer && clearTimeout(timer) });

  const watch = (pattern: vscode.GlobPattern): void => {
    const watcher = vscode.workspace.createFileSystemWatcher(pattern);
    context.subscriptions.push(watcher, watcher.onDidChange(schedule), watcher.onDidCreate(schedule), watcher.onDidDelete(schedule));
  };
  if (liveEffort) { watch(new vscode.RelativePattern(vscode.Uri.file(liveEffort.directory), "*.json")); }
  watch(new vscode.RelativePattern(vscode.Uri.file(hub), SESSION_DEFAULTS_FILE));
  for (const file of watchedFiles(process.env, os.homedir())) {
    watch(new vscode.RelativePattern(vscode.Uri.file(path.dirname(file)), path.basename(file)));
  }
  for (const glob of ["**/.claude/settings*.json", "**/.codex/config.toml", "**/.github/copilot/settings*.json"]) {
    watch(glob);
  }

  // The status bar shows the same model the panel draws. Reading it once at startup fills the
  // status bar before the panel is ever opened; every later refresh reaches it through onChange.
  const statusBar = new SettingsStatusBar(OPEN_COMMAND);
  const statusUpdates = controller.onChange((model) => { statusBar.update(model); void nativeUi?.synchronize(); });
  context.subscriptions.push(statusBar, statusUpdates);
  void controller.synchronizeDefaults().catch((error: unknown) => console.error("Nexus Settings synchronization failed", error));

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(SettingsViewProvider.viewType, new SettingsViewProvider(context.extensionUri, controller), {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.commands.registerCommand("nexusHubSettings.newCodexAgent", () => controller.handle({ type: "newCodex" })),
    vscode.commands.registerCommand("nexusHubSettings.applyAll", () => controller.handle({ type: "applyAll" })),
    vscode.commands.registerCommand("nexusHubSettings.upgrade", () => controller.handle({ type: "upgrade" })),
    vscode.commands.registerCommand(SET_EFFORT_COMMAND, async (value: unknown) => {
      if (!vscode.workspace.isTrusted || typeof value !== "string" || !Object.hasOwn(EFFORT_LABELS, value)) { return; }
      return controller.handle({ type: "set", control: "effort", value, tool: null });
    }),
    vscode.commands.registerCommand(COMPACT_COMMAND, async () => {
      const config = vscode.workspace.getConfiguration("nexusHubSettings");
      await config.update("compactStatusBar", !config.get<boolean>("compactStatusBar", true), vscode.ConfigurationTarget.Global);
    }),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (["claudeCode", "chat", "nexusHubSettings"].some((section) => event.affectsConfiguration(section))) {
        schedule();
      }
    }),
    vscode.workspace.onDidGrantWorkspaceTrust(async () => {
      if (fs.existsSync(path.join(hub, "VERSION"))) { initializeInstallationDefaults(hub); }
      schedule();
      const firstSubscription = context.subscriptions.length;
      if (!liveEffort) {
        liveEffort = await installLiveEffort(context);
        if (liveEffort) { watch(new vscode.RelativePattern(vscode.Uri.file(liveEffort.directory), "*.json")); }
      }
      if (disposed) { context.subscriptions.slice(firstSubscription).forEach(item => item.dispose()); return; }
      nativeUi ??= await installNativeUi(context);
      if (disposed) { context.subscriptions.slice(firstSubscription).forEach(item => item.dispose()); return; }
      schedule();
    }),
  );

  await vscode.commands.executeCommand("setContext", "nexusHubSettings.enabled", true);
  context.subscriptions.push({dispose: () => { void Promise.resolve(vscode.commands.executeCommand("setContext", "nexusHubSettings.enabled", false)).catch(() => undefined); }});
  return {
    getViewModel: () => controller.refresh(true),
    setFastMode: (value) => { if (typeof value !== "boolean") { throw new Error("Fast mode must be a boolean."); } return controller.handle({type: "setFastMode", value}); },
    setCodexTabs: (value) => { if (typeof value !== "boolean") { throw new Error("Codex tabs must be a boolean."); } return controller.handle({type: "setCodexTabs", value}); },
  };
}

export function deactivate(): void {
  // Everything registered in `activate` is disposed through context.subscriptions.
}
