/**
 * Minimal `vscode` module stub for Vitest, extended from the Codex monitor's.
 *
 * Every surface the extension's modules reference resolves here, and every
 * observable side effect (status-bar items, webview HTML, configuration
 * writes, messages, input boxes, output-channel lines) is recorded so tests,
 * including the leak test, can inspect it. `__resetStubState` clears it all.
 */

export const ConfigurationTarget = { Global: 1, Workspace: 2, WorkspaceFolder: 3 } as const;
export const StatusBarAlignment = { Left: 1, Right: 2 } as const;
export const ViewColumn = { Beside: 2 } as const;
export const ProgressLocation = { Notification: 15 } as const;
export const QuickPickItemKind = { Separator: -1, Default: 0 } as const;
export const ColorThemeKind = { Light: 1, Dark: 2, HighContrast: 3, HighContrastLight: 4 } as const;

interface StubConfiguration {
  get<T>(key: string, defaultValue: T): T;
  get<T>(key: string): T | undefined;
  update(...args: unknown[]): Promise<void>;
}

export const stubConfig: Record<string, Record<string, unknown>> = {};
export const configurationUpdates: Array<{ section: string | undefined; key: string; value: unknown; target: unknown }> = [];
export function __setStubConfig(section: string, key: string, value: unknown): void {
  (stubConfig[section] ??= {})[key] = value;
}

export const createdStatusBarItems: Array<Record<string, unknown>> = [];
export interface StubWebviewPanel {
  webview: {
    html: string;
    postedMessages: unknown[];
    postMessage(message: unknown): Promise<boolean>;
    onDidReceiveMessage(handler: (message: unknown) => void | Promise<void>): { dispose(): void };
    __dispatchMessage(message: unknown): Promise<void>;
  };
  iconPath?: unknown;
  revealCount: number;
  disposed: boolean;
  reveal(): void;
  dispose(): void;
  onDidDispose(handler: () => void): { dispose(): void };
}
export const createdWebviewPanels: StubWebviewPanel[] = [];

/** Every message shown through window.show*Message, in order. */
export const shownMessages: Array<{ level: "info" | "warning" | "error"; message: string }> = [];
/** Lines written to any output channel. */
export const outputLines: string[] = [];
/** Options passed to each showInputBox call, and the queued answers it returns. */
export const inputBoxCalls: Array<Record<string, unknown>> = [];
export const inputBoxAnswers: Array<string | undefined> = [];
/** Commands executed through commands.executeCommand. */
export const executedCommands: Array<{ command: string; args: unknown[] }> = [];

export function __resetStubState(): void {
  createdStatusBarItems.length = 0;
  createdWebviewPanels.length = 0;
  configurationUpdates.length = 0;
  shownMessages.length = 0;
  outputLines.length = 0;
  inputBoxCalls.length = 0;
  inputBoxAnswers.length = 0;
  executedCommands.length = 0;
  for (const k of Object.keys(stubConfig)) {
    delete stubConfig[k];
  }
  authImpl = undefined;
  workspace.workspaceFolders = undefined;
  window.activeColorTheme = { kind: 1 };
}

export const workspace = {
  workspaceFolders: undefined as Array<{ uri: { fsPath: string }; name: string; index: number }> | undefined,
  getConfiguration(section?: string): StubConfiguration {
    return {
      get<T>(key: string, defaultValue?: T): T | undefined {
        const sectionMap = section != null ? stubConfig[section] : undefined;
        if (sectionMap && key in sectionMap) {
          return sectionMap[key] as T;
        }
        return defaultValue;
      },
      async update(key: string, value: unknown, target: unknown): Promise<void> {
        configurationUpdates.push({ section, key, value, target });
        const sectionMap = (stubConfig[section ?? ""] ??= {});
        if (value === undefined) {
          delete sectionMap[key];
        } else {
          sectionMap[key] = value;
        }
      },
    };
  },
  onDidChangeConfiguration(): { dispose(): void } {
    return { dispose() {} };
  },
};

function message(level: "info" | "warning" | "error") {
  return (text: string): Promise<undefined> => {
    shownMessages.push({ level, message: text });
    return Promise.resolve(undefined);
  };
}

export const window = {
  activeColorTheme: { kind: 1 } as { kind: number },
  createStatusBarItem(alignment?: unknown, priority?: number): Record<string, unknown> {
    const item: Record<string, unknown> = {
      alignment,
      priority,
      text: "",
      tooltip: "",
      command: "",
      name: "",
      backgroundColor: undefined,
      visible: false,
      show() {
        item.visible = true;
      },
      hide() {
        item.visible = false;
      },
      dispose() {},
    };
    createdStatusBarItems.push(item);
    return item;
  },
  createWebviewPanel(): StubWebviewPanel {
    let messageHandler: ((message: unknown) => void | Promise<void>) | undefined;
    let disposeHandler: (() => void) | undefined;
    const panel: StubWebviewPanel = {
      webview: {
        html: "",
        postedMessages: [],
        async postMessage(msg: unknown): Promise<boolean> {
          panel.webview.postedMessages.push(msg);
          return true;
        },
        onDidReceiveMessage(handler: (message: unknown) => void | Promise<void>) {
          messageHandler = handler;
          return { dispose() { messageHandler = undefined; } };
        },
        async __dispatchMessage(msg: unknown): Promise<void> {
          await messageHandler?.(msg);
        },
      },
      revealCount: 0,
      disposed: false,
      reveal() {
        panel.revealCount += 1;
      },
      dispose() {
        if (panel.disposed) {
          return;
        }
        panel.disposed = true;
        disposeHandler?.();
      },
      onDidDispose(handler: () => void) {
        disposeHandler = handler;
        return { dispose() { disposeHandler = undefined; } };
      },
    };
    createdWebviewPanels.push(panel);
    return panel;
  },
  createOutputChannel(_name: string): { appendLine(line: string): void; dispose(): void } {
    return {
      appendLine(line: string) {
        outputLines.push(line);
      },
      dispose() {},
    };
  },
  showInformationMessage: message("info"),
  showWarningMessage: message("warning"),
  showErrorMessage: message("error"),
  async showInputBox(options: Record<string, unknown>): Promise<string | undefined> {
    inputBoxCalls.push(options);
    return inputBoxAnswers.shift();
  },
};

export class ThemeColor {
  constructor(public readonly id: string) {}
}

export class MarkdownString {
  value: string;
  isTrusted = false;
  supportThemeIcons = false;
  supportHtml = false;
  constructor(value = "", supportThemeIcons = false) {
    this.value = value;
    this.supportThemeIcons = supportThemeIcons;
  }
  appendMarkdown(md: string): this {
    this.value += md;
    return this;
  }
}

export const Uri = {
  joinPath(base: { path: string }, ...parts: string[]): { path: string } {
    return { path: [base.path, ...parts].join("/") };
  },
  parse(value: string): { path: string } {
    return { path: value };
  },
};

export const commands = {
  executeCommand(command: string, ...args: unknown[]): Promise<void> {
    executedCommands.push({ command, args });
    return Promise.resolve();
  },
};

/** The authentication implementation `vscode.authentication` delegates to; set by tests. */
interface StubAuthentication {
  getSession(providerId: string, scopes: readonly string[], options: Record<string, unknown>): Promise<unknown>;
  getAccounts?(providerId: string): Promise<readonly unknown[]>;
}
let authImpl: StubAuthentication | undefined;
export function __setAuthentication(impl: StubAuthentication | undefined): void {
  authImpl = impl;
}

export const authentication = {
  getSession(providerId: string, scopes: readonly string[], options: Record<string, unknown>): Promise<unknown> {
    return authImpl ? authImpl.getSession(providerId, scopes, options) : Promise.resolve(undefined);
  },
  getAccounts(providerId: string): Promise<readonly unknown[]> {
    return authImpl?.getAccounts ? authImpl.getAccounts(providerId) : Promise.resolve([]);
  },
  onDidChangeSessions(): { dispose(): void } {
    return { dispose() {} };
  },
};
