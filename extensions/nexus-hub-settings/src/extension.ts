import { alertProvidersForEditor, ALERT_PROVIDERS, type AlertProvider, USAGE_ALERTS_FILE, readUsageAlerts, writeUsageAlert } from "./usageAlerts";
import { editorCapabilities } from "./editorCapabilities";
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
import { restartNativeProvider } from "./nativeRecovery";
import { installAgentSplit, vscodeSplitHost } from "./agentSplit";
import { readSessionDefaults, SESSION_DEFAULTS_FILE, writeSessionDefault } from "./sessionDefaults";

/** What the live check (and other extensions) can call: the panel's current model, freshly read. */
export interface ExtensionApi {
  getViewModel(): Promise<ViewModel>;
  setFastMode(value: boolean): Promise<ViewModel>;
  setCodexTabs(value: boolean): Promise<ViewModel>;
  setUsageAlert(provider: AlertProvider | "all", enabled: boolean): Promise<ViewModel>;
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

/** The Claude extension includes its own CLI, even when the editor inherited no standalone CLI on PATH. */
export function providerDirectories(): string[] {
  const extension = vscode.extensions.getExtension("anthropic.claude-code");
  if (!extension) { return []; }
  const directory = path.join(extension.extensionPath, "resources", "native-binary");
  return fs.existsSync(path.join(directory, process.platform === "win32" ? "claude.exe" : "claude")) ? [directory] : [];
}

interface RecoveryApi { nexusRestartProvider?(): Promise<unknown>; nexusRefreshTab?(): Promise<unknown> }
/** A vendor build without the Nexus adapter exports nothing, so an empty API is the normal unadapted case. */
async function providerApi(provider: "claude" | "codex"): Promise<RecoveryApi> {
  const extension = vscode.extensions.getExtension(provider === "claude" ? "anthropic.claude-code" : "openai.chatgpt");
  if (!extension) { throw new Error("This extension is not installed in this editor."); }
  const exports = (extension.isActive ? extension.exports : await extension.activate()) as Partial<RecoveryApi> | undefined;
  return exports ?? {};
}
export async function refreshCodexTab(): Promise<void> {
  if (!vscode.workspace.isTrusted) { return; }
  if (!vscode.extensions.getExtension("openai.chatgpt")) { await vscode.window.showWarningMessage("Codex is not installed in this editor."); return; }
  try {
    const api = await providerApi("codex");
    if (typeof api.nexusRefreshTab !== "function") { await restartProvider("codex"); return; }
    await api.nexusRefreshTab();
  } catch (error) { await vscode.window.showWarningMessage(error instanceof Error ? error.message : "Codex could not refresh. Other extensions were not restarted."); }
}
export async function restartProvider(provider: "claude" | "codex"): Promise<void> {
  if (!vscode.workspace.isTrusted) { return; }
  const name = provider === "claude" ? "Claude Code" : "Codex";
  if (!vscode.extensions.getExtension(provider === "claude" ? "anthropic.claude-code" : "openai.chatgpt")) { await vscode.window.showWarningMessage(`${name} is not installed in this editor.`); return; }
  try {
    const api = await providerApi(provider);
    const detail = provider === "codex" ? "Restart only Codex's app-server, then refresh its open tabs with their saved sessions. Running Codex requests may be interrupted. Other extensions keep running." : "Restart only Claude Code session processes. Idle sessions restart now; busy sessions restart at their next idle turn boundary. Other extensions keep running.";
    const choice = await vscode.window.showWarningMessage(`Restart ${name}?`, {modal: true, detail}, "Restart " + name);
    if (choice !== "Restart " + name) { return; }
    if (typeof api.nexusRestartProvider === "function") { await api.nexusRestartProvider(); }
    else { await restartNativeProvider(provider); }
  } catch (error) { await vscode.window.showWarningMessage(error instanceof Error ? error.message : "The selected provider could not restart. Other extensions were not restarted."); }
}

/** A provider whose process failed before its launcher was repaired stays disconnected until the window reloads. */
export async function announceStalledStart(providers: string[]): Promise<void> {
  if (!providers.length) { return; }
  const names = providers.join(" and ");
  const choice = await vscode.window.showWarningMessage(`${names} started before Nexus-Hub repaired ${providers.length > 1 ? "their launchers" : "its launcher"}, so ${providers.length > 1 ? "they cannot" : "it cannot"} connect until this window reloads.`, {}, "Reload Window");
  if (choice === "Reload Window") { await vscode.commands.executeCommand("workbench.action.reloadWindow"); }
}

/** Open the provider's native new-session route beside the current editor. */
export async function openCodexPanel(sessionFile: string): Promise<unknown> {
  if (!vscode.workspace.isTrusted) { return; }
  if (!readSessionDefaults(sessionFile).codexTabs) { return vscode.commands.executeCommand("chatgpt.openSidebar"); }
  return vscode.commands.executeCommand("vscode.openWith", vscode.Uri.parse("openai-codex://route/extension/panel/new"), "chatgpt.conversationEditor", {viewColumn: vscode.ViewColumn.Beside, preserveFocus: false, preview: false});
}

export async function activate(context: vscode.ExtensionContext): Promise<ExtensionApi> {
  const hub = installRoot(process.env, os.homedir());
  if (vscode.workspace.isTrusted && fs.existsSync(path.join(hub, "VERSION"))) { initializeInstallationDefaults(hub); }
  const sessionFile = path.join(hub, SESSION_DEFAULTS_FILE);
  context.subscriptions.push(
    vscode.commands.registerCommand(OPEN_COMMAND, async () => {
      await vscode.commands.executeCommand("workbench.view.extension.nexusHubSettings");
      await vscode.commands.executeCommand(`${SettingsViewProvider.viewType}.focus`);
    }),
    vscode.commands.registerCommand("nexusHubSettings.codexHistory", openCodexHistory),
    vscode.commands.registerCommand("nexusHubSettings.refreshCodexTab", refreshCodexTab),
    vscode.commands.registerCommand("nexusHubSettings.openCodex", () => openCodexPanel(sessionFile)),
  );
  context.subscriptions.push(installAgentSplit(vscodeSplitHost(context.workspaceState)));
  let liveEffort: Awaited<ReturnType<typeof installLiveEffort>>;
  let nativeUi: Awaited<ReturnType<typeof installNativeUi>>;
  const bridge = new CliBridge({ pythonPath: userPythonPath, providerDirectories });
  const controller = new SettingsController({
    restartExtension: restartProvider,
    editorCapabilities: () => editorCapabilities(vscode.env.appName, !!vscode.extensions?.getExtension("anthropic.claude-code") || !!vscode.extensions?.getExtension("openai.chatgpt")),
    usageAlertProviders: () => alertProvidersForEditor(vscode.env.appName),
    usageAlerts: () => readUsageAlerts(path.join(hub, USAGE_ALERTS_FILE)),
    setUsageAlert: async (provider, enabled) => { writeUsageAlert(path.join(hub, USAGE_ALERTS_FILE), provider, enabled, alertProvidersForEditor(vscode.env.appName)); },
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
  watch(new vscode.RelativePattern(vscode.Uri.file(hub), SESSION_DEFAULTS_FILE));
  watch(new vscode.RelativePattern(vscode.Uri.file(hub), USAGE_ALERTS_FILE));
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
      statusBar.previewEffort(value);
      try {
        const model = await controller.handle({ type: "set", control: "effort", value, tool: null });
        await nativeUi?.synchronize();
        if (model.error || model.applicationIssues?.length || model.notice?.level === "error" || model.preferences?.needsAttention) { await vscode.commands.executeCommand(OPEN_COMMAND); }
        return model;
      } finally { statusBar.previewEffort(); }
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

  liveEffort = await installLiveEffort(context);
  if (liveEffort) { watch(new vscode.RelativePattern(vscode.Uri.file(liveEffort.directory), "*.json")); }
  nativeUi = await installNativeUi(context);
  if (!disposed) {
    void announceStalledStart(liveEffort?.stalled ?? []);
    if (!liveEffort?.stalled.length && nativeUi?.summary().reloadRequired) {
      void vscode.window.showWarningMessage("Nexus Hub updated the editor integration. Reload this window to apply the Codex toolbar routing and native controls.", {}, "Reload Window").then(async (choice) => {
        if (choice === "Reload Window") { await vscode.commands.executeCommand("workbench.action.reloadWindow"); }
      });
    }
    schedule();
  }
  await vscode.commands.executeCommand("setContext", "nexusHubSettings.enabled", true);
  context.subscriptions.push({dispose: () => { void Promise.resolve(vscode.commands.executeCommand("setContext", "nexusHubSettings.enabled", false)).catch(() => undefined); }});
  return {
    getViewModel: () => controller.refresh(true),
    setFastMode: (value) => { if (typeof value !== "boolean") { throw new Error("Fast mode must be a boolean."); } return controller.handle({type: "setFastMode", value}); },
    setUsageAlert: (provider, enabled) => { if ((provider !== "all" && !ALERT_PROVIDERS.includes(provider)) || typeof enabled !== "boolean") { throw new Error("Invalid usage-alert preference."); } return controller.handle({type: "setUsageAlert", provider, enabled}); },
    setCodexTabs: (value) => { if (typeof value !== "boolean") { throw new Error("Codex tabs must be a boolean."); } return controller.handle({type: "setCodexTabs", value}); },
  };
}

export function deactivate(): void {
  // Everything registered in `activate` is disposed through context.subscriptions.
}
