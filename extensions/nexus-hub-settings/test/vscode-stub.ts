/**
 * Minimal `vscode` module stub for Vitest.
 *
 * It models only what the panel touches: layered configuration (default, user,
 * workspace, workspace folder) with `inspect` and `update`, modal warning dialogs,
 * file watchers, command and webview-view registration, status-bar items, and
 * `env.openExternal`.
 * `stub.reset()` clears every store between tests.
 */
import * as nodePath from "node:path";

export const ConfigurationTarget = { Global: 1, Workspace: 2, WorkspaceFolder: 3 } as const;

type Listener<T> = (event: T) => unknown;

function emitter<T>(): { event: (listener: Listener<T>) => { dispose(): void }; fire(event: T): void; count(): number; clear(): void } {
  const listeners: Listener<T>[] = [];
  return {
    event(listener) {
      listeners.push(listener);
      return { dispose: () => void listeners.splice(listeners.indexOf(listener), 1) };
    },
    fire(event) {
      [...listeners].forEach((l) => l(event));
    },
    count: () => listeners.length,
    clear: () => void listeners.splice(0, listeners.length),
  };
}

export class Uri {
  constructor(
    readonly scheme: string,
    readonly fsPath: string,
    private readonly text: string,
  ) {}
  static file(fsPath: string): Uri {
    return new Uri("file", fsPath, `file:///${fsPath.replace(/\\/g, "/")}`);
  }
  static parse(text: string): Uri {
    return new Uri(text.split(":")[0] ?? "", text, text);
  }
  static joinPath(base: Uri, ...parts: string[]): Uri {
    return Uri.file(nodePath.join(base.fsPath, ...parts));
  }
  toString(): string {
    return this.text;
  }
}

export const StatusBarAlignment = { Left: 1, Right: 2 } as const;
export const ColorThemeKind = { Light: 1, Dark: 2, HighContrast: 3, HighContrastLight: 4 } as const;

export class MarkdownString {
  supportHtml = false;
  isTrusted: boolean | { enabledCommands: readonly string[] } = false;
  constructor(
    public value = "",
    public supportThemeIcons = false,
  ) {}
}

export interface StatusItem {
  id: string;
  alignment: number;
  priority: number;
  name?: string;
  text: string;
  tooltip?: MarkdownString | string;
  command?: string;
  accessibilityInformation?: { label: string; role?: string };
  shown: boolean;
  disposed: boolean;
  show(): void;
  dispose(): void;
}

export class RelativePattern {
  constructor(
    readonly base: Uri,
    readonly pattern: string,
  ) {}
}

interface Watcher {
  pattern: unknown;
  change: ReturnType<typeof emitter<unknown>>;
  create: ReturnType<typeof emitter<unknown>>;
  remove: ReturnType<typeof emitter<unknown>>;
  disposed: boolean;
}

const configEvents = emitter<{ affectsConfiguration(section: string): boolean }>();
const trustEvents = emitter<void>();

export const stub = {
  defaults: {} as Record<string, unknown>,
  user: {} as Record<string, unknown>,
  workspace: {} as Record<string, unknown>,
  folder: {} as Record<string, unknown>,
  updates: [] as { key: string; value: unknown; target: unknown }[],
  failUpdate: new Set<string>(),
  trusted: true,
  folders: undefined as { uri: Uri }[] | undefined,
  warnings: [] as { message: string; options: unknown; buttons: string[] }[],
  warningAnswer: (buttons: string[]): string | undefined => buttons[0],
  opened: [] as string[],
  watchers: [] as Watcher[],
  providers: [] as { id: string; provider: unknown; options: unknown }[],
  commands: new Map<string, (...args: unknown[]) => unknown>(),
  executed: [] as string[],
  statusItems: [] as StatusItem[],
  vendorExtensions: new Map<string, { extensionPath: string; isActive: boolean; exports?: unknown }>(),
  fireConfig(...sections: string[]): void {
    configEvents.fire({ affectsConfiguration: (section) => sections.includes(section) });
  },
  fireTrust(): void {
    trustEvents.fire(undefined);
  },
  reset(): void {
    this.defaults = {};
    this.user = {};
    this.workspace = {};
    this.folder = {};
    this.updates = [];
    this.failUpdate = new Set();
    this.trusted = true;
    this.folders = undefined;
    this.warnings = [];
    this.warningAnswer = (buttons) => buttons[0];
    this.opened = [];
    this.watchers = [];
    this.providers = [];
    this.commands = new Map();
    this.executed = [];
    this.statusItems = [];
    this.vendorExtensions.clear();
    configEvents.clear();
    trustEvents.clear();
  },
};

export const workspace = {
  getConfiguration(section?: string) {
    const full = (key: string): string => (section ? `${section}.${key}` : key);
    return {
      get<T>(key: string, fallback?: T): T | undefined {
        const name = full(key);
        return (name in stub.user ? stub.user[name] : name in stub.defaults ? stub.defaults[name] : fallback) as T | undefined;
      },
      inspect<T>(key: string) {
        const name = full(key);
        return {
          key: name,
          defaultValue: stub.defaults[name] as T | undefined,
          globalValue: stub.user[name] as T | undefined,
          workspaceValue: stub.workspace[name] as T | undefined,
          workspaceFolderValue: stub.folder[name] as T | undefined,
        };
      },
      async update(key: string, value: unknown, target: unknown): Promise<void> {
        const name = full(key);
        if (stub.failUpdate.has(name)) {
          throw new Error(`stub refused to update ${name}`);
        }
        if (!(name in stub.defaults)) {
          throw new Error(`${name} is not a registered configuration`);
        }
        stub.updates.push({ key: name, value, target });
        if (value === undefined) {
          delete stub.user[name];
        } else {
          stub.user[name] = value;
        }
      },
    };
  },
  get isTrusted(): boolean {
    return stub.trusted;
  },
  get workspaceFolders() {
    return stub.folders;
  },
  createFileSystemWatcher(pattern: unknown) {
    const watcher: Watcher = { pattern, change: emitter(), create: emitter(), remove: emitter(), disposed: false };
    stub.watchers.push(watcher);
    return {
      onDidChange: watcher.change.event,
      onDidCreate: watcher.create.event,
      onDidDelete: watcher.remove.event,
      dispose: () => {
        watcher.disposed = true;
      },
    };
  },
  onDidChangeConfiguration: configEvents.event,
  onDidGrantWorkspaceTrust: trustEvents.event,
};

export const window = {
  async showWarningMessage(message: string, options: unknown, ...buttons: string[]): Promise<string | undefined> {
    stub.warnings.push({ message, options, buttons });
    return stub.warningAnswer(buttons);
  },
  createStatusBarItem(id: string, alignment: number, priority: number): StatusItem {
    const item: StatusItem = {
      id,
      alignment,
      priority,
      text: "",
      shown: false,
      disposed: false,
      show() {
        item.shown = true;
      },
      dispose() {
        item.disposed = true;
      },
    };
    stub.statusItems.push(item);
    return item;
  },
  registerWebviewViewProvider(id: string, provider: unknown, options: unknown) {
    stub.providers.push({ id, provider, options });
    return { dispose() {} };
  },
};

export const commands = {
  registerCommand(id: string, handler: (...args: unknown[]) => unknown) {
    stub.commands.set(id, handler);
    return { dispose: () => void stub.commands.delete(id) };
  },
  async executeCommand(id: string, ...args: unknown[]): Promise<unknown> {
    stub.executed.push(id);
    return stub.commands.get(id)?.(...args);
  },
};

export const env = {
  async openExternal(uri: Uri): Promise<boolean> {
    stub.opened.push(uri.toString());
    return true;
  },
};

export const extensions = { getExtension: (id: string) => stub.vendorExtensions.get(id) };
