type MessageHandler = (message: unknown) => void | Promise<void>;
type CommandHandler = (...args: unknown[]) => unknown | Promise<unknown>;
type ConfigurationHandler = (event: {
  affectsConfiguration(section: string): boolean;
}) => void;

export const ConfigurationTarget = {
  Global: 1,
  Workspace: 2,
  WorkspaceFolder: 3
} as const;
export const StatusBarAlignment = { Left: 1, Right: 2 } as const;
export const ViewColumn = { One: 1, Beside: 2 } as const;

export const configuration = new Map<string, unknown>();
export const configurationUpdates: Array<{
  section: string;
  key: string;
  value: unknown;
  target: unknown;
}> = [];
const configurationUpdateFailures = new Map<string, number>();
export let maximumConcurrentUpdates = 0;
let concurrentUpdates = 0;

export const executedCommands: Array<{
  command: string;
  args: unknown[];
}> = [];
const registeredCommands = new Map<string, CommandHandler>();
const configurationHandlers = new Set<ConfigurationHandler>();
export const informationMessages: string[] = [];
export const warningMessages: string[] = [];
export const warningResponses: Array<string | undefined> = [];
export const informationResponses: Array<string | undefined> = [];
export const inputResponses: Array<string | undefined> = [];
export const openExternalUris: string[] = [];

export class MarkdownString {
  public value: string;
  public isTrusted = false;
  public supportThemeIcons = false;
  public supportHtml = false;

  public constructor(value = "", supportThemeIcons = false) {
    this.value = value;
    this.supportThemeIcons = supportThemeIcons;
  }

  public appendMarkdown(value: string): this {
    this.value += value;
    return this;
  }
}

export class Uri {
  public constructor(private readonly value: string) {}

  public static file(value: string): Uri {
    return new Uri(value);
  }

  public static parse(value: string): Uri {
    return new Uri(value);
  }

  public static joinPath(base: Uri, ...parts: string[]): Uri {
    return new Uri([base.toString(), ...parts].join("/"));
  }

  public toString(): string {
    return this.value;
  }
}

export interface StubStatusBarItem {
  text: string;
  tooltip: unknown;
  command?: string;
  name?: string;
  shown: boolean;
  priority?: number;
  show(): void;
  hide(): void;
  dispose(): void;
}

export const statusItems: StubStatusBarItem[] = [];

export interface StubWebview {
  html: string;
  options: unknown;
  cspSource: string;
  postedMessages: unknown[];
  asWebviewUri(uri: Uri): Uri;
  postMessage(message: unknown): Promise<boolean>;
  onDidReceiveMessage(handler: MessageHandler): { dispose(): void };
  dispatch(message: unknown): Promise<void>;
}

export interface StubWebviewPanel {
  webview: StubWebview;
  revealed: boolean;
  disposed: boolean;
  reveal(): void;
  dispose(): void;
  onDidDispose(handler: () => void): { dispose(): void };
}

export const webviewPanels: StubWebviewPanel[] = [];

function createWebview(): StubWebview {
  let receiver: MessageHandler | undefined;
  return {
    html: "",
    options: {},
    cspSource: "vscode-webview:",
    postedMessages: [],
    asWebviewUri: (uri: Uri) => uri,
    async postMessage(message: unknown): Promise<boolean> {
      this.postedMessages.push(message);
      return true;
    },
    onDidReceiveMessage(handler: MessageHandler) {
      receiver = handler;
      return {
        dispose() {
          receiver = undefined;
        }
      };
    },
    async dispatch(message: unknown): Promise<void> {
      await receiver?.(message);
    }
  };
}

function createPanel(): StubWebviewPanel {
  let disposeHandler: (() => void) | undefined;
  const panel: StubWebviewPanel = {
    webview: createWebview(),
    revealed: false,
    disposed: false,
    reveal() {
      panel.revealed = true;
    },
    dispose() {
      if (!panel.disposed) {
        panel.disposed = true;
        disposeHandler?.();
      }
    },
    onDidDispose(handler: () => void) {
      disposeHandler = handler;
      return {
        dispose() {
          disposeHandler = undefined;
        }
      };
    }
  };
  return panel;
}

export const workspace = {
  getConfiguration(section: string) {
    return {
      get<T>(key: string, defaultValue?: T): T {
        return (
          (configuration.get(`${section}.${key}`) as T | undefined) ??
          (defaultValue as T)
        );
      },
      inspect<T>(key: string): { globalValue?: T } {
        const fullKey = `${section}.${key}`;
        return configuration.has(fullKey)
          ? { globalValue: configuration.get(fullKey) as T }
          : {};
      },
      async update(key: string, value: unknown, target: unknown): Promise<void> {
        concurrentUpdates += 1;
        try {
          maximumConcurrentUpdates = Math.max(
            maximumConcurrentUpdates,
            concurrentUpdates
          );
          await Promise.resolve();
          const fullKey = `${section}.${key}`;
          const remainingFailures =
            configurationUpdateFailures.get(fullKey) ?? 0;
          if (remainingFailures > 0) {
            if (remainingFailures === 1) {
              configurationUpdateFailures.delete(fullKey);
            } else {
              configurationUpdateFailures.set(
                fullKey,
                remainingFailures - 1
              );
            }
            throw new Error("sensitive configuration update detail");
          }
          configurationUpdates.push({ section, key, value, target });
          if (value === undefined) {
            configuration.delete(fullKey);
          } else {
            configuration.set(fullKey, value);
          }
        } finally {
          concurrentUpdates -= 1;
        }
      }
    };
  },
  onDidChangeConfiguration(handler: ConfigurationHandler) {
    configurationHandlers.add(handler);
    return {
      dispose() {
        configurationHandlers.delete(handler);
      }
    };
  }
};

export const commands = {
  registerCommand(command: string, handler: CommandHandler) {
    registeredCommands.set(command, handler);
    return {
      dispose() {
        registeredCommands.delete(command);
      }
    };
  },
  async executeCommand(
    command: string,
    ...args: unknown[]
  ): Promise<unknown> {
    executedCommands.push({ command, args });
    return registeredCommands.get(command)?.(...args);
  }
};

export const webviewProviders: Array<{
  id: string;
  provider: unknown;
}> = [];

/** Mirrors the real enum so a theme-dependent renderer can be exercised. */
export const ColorThemeKind = {
  Light: 1,
  Dark: 2,
  HighContrast: 3,
  HighContrastLight: 4
} as const;

export const window = {
  // The tooltip builder reads this to pick legible text colors. It was absent from
  // this stub, so every test touching the status bar threw on `.kind` the moment
  // the SVG bars landed. The production code guards the read; the stub provides it
  // so the guard is not the only path the suite ever exercises.
  activeColorTheme: { kind: ColorThemeKind.Dark as number },
  createStatusBarItem(_alignment?: unknown, priority?: number): StubStatusBarItem {
    const item: StubStatusBarItem = {
      text: "",
      tooltip: undefined,
      shown: false,
      priority,
      show() {
        item.shown = true;
      },
      hide() {
        item.shown = false;
      },
      dispose() {
        item.shown = false;
      }
    };
    statusItems.push(item);
    return item;
  },
  createWebviewPanel(): StubWebviewPanel {
    const panel = createPanel();
    webviewPanels.push(panel);
    return panel;
  },
  registerWebviewViewProvider(id: string, provider: unknown) {
    webviewProviders.push({ id, provider });
    return {
      dispose() {
        const index = webviewProviders.findIndex(
          (entry) => entry.id === id && entry.provider === provider
        );
        if (index >= 0) {
          webviewProviders.splice(index, 1);
        }
      }
    };
  },
  async showInformationMessage(
    message: string,
    ..._items: unknown[]
  ): Promise<string | undefined> {
    informationMessages.push(message);
    return informationResponses.shift();
  },
  async showWarningMessage(
    message: string,
    ..._items: unknown[]
  ): Promise<string | undefined> {
    warningMessages.push(message);
    return warningResponses.shift();
  },
  async showInputBox(): Promise<string | undefined> {
    return inputResponses.shift();
  }
};

export const env = {
  async openExternal(uri: Uri): Promise<boolean> {
    openExternalUris.push(uri.toString());
    return true;
  }
};

export class FakeMemento {
  public readonly values = new Map<string, unknown>();

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

export function createExtensionContext(): {
  globalState: FakeMemento;
  secrets: {
    get(key: string): Promise<string | undefined>;
    store(key: string, value: string): Promise<void>;
    delete(key: string): Promise<void>;
  };
  extensionUri: Uri;
  subscriptions: Array<{ dispose(): unknown }>;
} {
  const secretValues = new Map<string, string>();
  return {
    globalState: new FakeMemento(),
    secrets: {
      async get(key: string) {
        return secretValues.get(key);
      },
      async store(key: string, value: string) {
        secretValues.set(key, value);
      },
      async delete(key: string) {
        secretValues.delete(key);
      }
    },
    extensionUri: Uri.file("extension"),
    subscriptions: [],
    // The identity the update watcher reads. Present because activation registers
    // that watcher first, so a context without it is not a usable stub.
    extension: { id: "nexus-hub.cursor-usage-monitor", packageJSON: { version: "0.0.0-test" } }
  };
}

/**
 * The installed-extension registry, mirroring `vscode.extensions`.
 *
 * `getExtension` returning undefined is the state the update watcher reads as an
 * uninstall in progress, which is what the Nexus-Hub installers produce when they
 * uninstall before reinstalling.
 */
export const extensionRegistry = new Map<string, { id: string; packageJSON: { version: string } }>();
const extensionChangeListeners: Array<() => void> = [];

export const extensions = {
  getExtension(id: string): { id: string; packageJSON: { version: string } } | undefined {
    return extensionRegistry.get(id);
  },
  onDidChange(listener: () => void): { dispose(): void } {
    extensionChangeListeners.push(listener);
    return { dispose() { /* no-op */ } };
  }
};

/** Installs (or, with an undefined version, uninstalls) an extension and notifies. */
export function setInstalledExtension(id: string, version: string | undefined): void {
  if (version === undefined) extensionRegistry.delete(id);
  else extensionRegistry.set(id, { id, packageJSON: { version } });
  for (const listener of [...extensionChangeListeners]) listener();
}

/** Clears the registry and its listeners between tests. */
export function resetExtensionRegistry(): void {
  extensionRegistry.clear();
  extensionChangeListeners.length = 0;
}

export function createWebviewView(): {
  webview: StubWebview;
  shown: boolean;
  show(preserveFocus?: boolean): void;
  onDidDispose(handler: () => void): { dispose(): void };
  dispose(): void;
} {
  let disposeHandler: (() => void) | undefined;
  const view = {
    webview: createWebview(),
    shown: false,
    show(_preserveFocus?: boolean) {
      view.shown = true;
    },
    onDidDispose(handler: () => void) {
      disposeHandler = handler;
      return {
        dispose() {
          disposeHandler = undefined;
        }
      };
    },
    dispose() {
      disposeHandler?.();
    }
  };
  return view;
}

export function setConfiguration(key: string, value: unknown): void {
  configuration.set(key, value);
}

export function failConfigurationUpdate(key: string, times = 1): void {
  configurationUpdateFailures.set(key, times);
}

export function fireConfigurationChange(section: string): void {
  const event = {
    affectsConfiguration(candidate: string): boolean {
      return (
        candidate === section ||
        candidate.startsWith(`${section}.`) ||
        section.startsWith(`${candidate}.`)
      );
    }
  };
  for (const handler of [...configurationHandlers]) {
    handler(event);
  }
}

export function registeredCommandIds(): string[] {
  return [...registeredCommands.keys()];
}

export async function runRegisteredCommand(
  command: string,
  ...args: unknown[]
): Promise<unknown> {
  const handler = registeredCommands.get(command);
  if (handler === undefined) {
    throw new Error(`Command is not registered: ${command}`);
  }
  return handler(...args);
}

export function resetVscodeStub(): void {
  configuration.clear();
  configurationUpdateFailures.clear();
  configurationUpdates.length = 0;
  executedCommands.length = 0;
  registeredCommands.clear();
  configurationHandlers.clear();
  informationMessages.length = 0;
  warningMessages.length = 0;
  warningResponses.length = 0;
  informationResponses.length = 0;
  inputResponses.length = 0;
  openExternalUris.length = 0;
  statusItems.length = 0;
  webviewPanels.length = 0;
  webviewProviders.length = 0;
  concurrentUpdates = 0;
  maximumConcurrentUpdates = 0;
}
