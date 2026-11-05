import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";
import { CliBridge } from "./cliBridge";
import { ConfirmRequest, SettingsController, UiLike } from "./controller";
import { profileNameFromStorage } from "./editorWrites";
import { syncEditorEffort } from "./editorEffort";
import { SettingsViewProvider } from "./settingsView";
import { COMPACT_COMMAND, EFFORT_LABELS, SET_EFFORT_COMMAND, SettingsStatusBar } from "./statusBar";
import { ViewModel } from "./viewModel";

/** What the live check (and other extensions) can call: the panel's current model, freshly read. */
export interface ExtensionApi {
  getViewModel(): Promise<ViewModel>;
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

export function activate(context: vscode.ExtensionContext): ExtensionApi {
  const bridge = new CliBridge({ pythonPath: userPythonPath });
  const controller = new SettingsController({
    bridge,
    ui: vscodeUi(),
    isTrusted: () => vscode.workspace.isTrusted,
    project: firstFolder,
    profile: () => profileNameFromStorage(context.globalStorageUri.fsPath),
    platform: process.platform === "win32" ? "windows" : process.platform === "darwin" ? "macos" : "linux",
    syncEditorEffort: (records) => syncEditorEffort(records, async (key, previous) => {
      const storageKey = `effort-backup:${key}`;
      if (context.globalState.get(storageKey) === undefined) { await context.globalState.update(storageKey, previous); }
    }),
  });

  let timer: ReturnType<typeof setTimeout> | undefined;
  const schedule = (): void => {
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
  for (const file of watchedFiles(process.env, os.homedir())) {
    watch(new vscode.RelativePattern(vscode.Uri.file(path.dirname(file)), path.basename(file)));
  }
  for (const glob of ["**/.claude/settings*.json", "**/.codex/config.toml", "**/.github/copilot/settings*.json"]) {
    watch(glob);
  }

  // The status bar shows the same model the panel draws. Reading it once at startup fills the
  // status bar before the panel is ever opened; every later refresh reaches it through onChange.
  const statusBar = new SettingsStatusBar(OPEN_COMMAND);
  const statusUpdates = controller.onChange((model) => statusBar.update(model));
  context.subscriptions.push(statusBar, statusUpdates);
  void controller.synchronizeDefaults().catch((error: unknown) => console.error("Nexus Settings synchronization failed", error));

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(SettingsViewProvider.viewType, new SettingsViewProvider(context.extensionUri, controller), {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.commands.registerCommand(OPEN_COMMAND, () => vscode.commands.executeCommand(`${SettingsViewProvider.viewType}.focus`)),
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
    vscode.workspace.onDidGrantWorkspaceTrust(schedule),
  );

  return { getViewModel: () => controller.refresh(true) };
}

export function deactivate(): void {
  // Everything registered in `activate` is disposed through context.subscriptions.
}
