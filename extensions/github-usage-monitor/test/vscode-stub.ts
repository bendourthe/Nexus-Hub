export const configListeners: Array<(event: { affectsConfiguration: (key: string) => boolean }) => void> = [];

type Command = (...args: unknown[]) => unknown;
const commandMap = new Map<string, Command>();
const configuration = new Map<string, unknown>();
const inputs: Array<string | undefined> = [];

export const messages = { information: [] as string[], warnings: [] as string[], errors: [] as string[] };
export const statusItems: Array<{ text: string; tooltip: unknown; command?: string; name?: string; shown: boolean }> = [];
export const webviewPanels: Array<ReturnType<typeof panel>> = [];
export const webviewProviders: unknown[] = [];

export class MarkdownString {
  public value: string;
  public isTrusted = false;
  public supportThemeIcons = false;
  public supportHtml = false;
  public constructor(value = "") { this.value = value; }
  public appendMarkdown(value: string): this { this.value += value; return this; }
  public toString(): string { return this.value; }
}

export class Uri {
  public constructor(private readonly value: string) {}
  public static file(value: string): Uri { return new Uri(value); }
  public static joinPath(base: Uri, ...parts: string[]): Uri { return new Uri([base.toString(), ...parts].join("/")); }
  public toString(): string { return this.value; }
}

export const StatusBarAlignment = { Left: 1, Right: 2 } as const;
export const ViewColumn = { One: 1 } as const;

export const commands = {
  registerCommand(name: string, command: Command): { dispose(): void } { commandMap.set(name, command); return { dispose: () => commandMap.delete(name) }; },
  async executeCommand(name: string, ...args: unknown[]): Promise<unknown> { const command = commandMap.get(name); return command ? command(...args) : undefined; }
};

export const ConfigurationTarget = { Global: 1, Workspace: 2, WorkspaceFolder: 3 } as const;

/**
 * Values a test declared as explicitly user-set, so `inspect()` can distinguish
 * them from a default. Keyed by fully-qualified setting id.
 */
const globalOverrides = new Map<string, unknown>();
const workspaceOverrides = new Map<string, unknown>();
/** Sections whose `update()` must reject, so a partial-migration path is testable. */
const failingUpdates = new Set<string>();
/**
 * Ordered log of configuration access, so a test can assert SEQUENCE and not just
 * outcome. Activation must migrate settings BEFORE anything reads them; a check on
 * the final value alone passes even when the read raced the write.
 */
export const configurationLog: Array<{ op: "get" | "update"; id: string }> = [];

export const workspace = {
  /** Configuration-change events. Tests drive it via `fireConfigChange`. */
  onDidChangeConfiguration: (listener: (event: { affectsConfiguration: (key: string) => boolean }) => void) => {
    configListeners.push(listener);
    return { dispose: () => { configListeners.length = 0; } };
  },
  getConfiguration(section?: string): {
    get<T>(key: string, defaultValue?: T): T;
    inspect<T>(key: string): { globalValue?: T; workspaceValue?: T } | undefined;
    update(key: string, value: unknown, target?: number): Promise<void>;
  } {
    const qualify = (key: string): string => (section === undefined ? key : `${section}.${key}`);
    return {
      get<T>(key: string, defaultValue?: T): T {
        configurationLog.push({ op: "get", id: qualify(key) });
        return (configuration.get(qualify(key)) as T | undefined) ?? defaultValue as T;
      },
      inspect<T>(key: string): { globalValue?: T; workspaceValue?: T } | undefined {
        const id = qualify(key);
        const globalValue = globalOverrides.get(id) as T | undefined;
        const workspaceValue = workspaceOverrides.get(id) as T | undefined;
        if (globalValue === undefined && workspaceValue === undefined && !configuration.has(id)) return undefined;
        return { globalValue, workspaceValue };
      },
      async update(key: string, value: unknown, target = ConfigurationTarget.Global): Promise<void> {
        const id = qualify(key);
        if (failingUpdates.has(id)) throw new Error(`stub refused to write ${id}`);
        configurationLog.push({ op: "update", id });
        (target === ConfigurationTarget.Workspace ? workspaceOverrides : globalOverrides).set(id, value);
        configuration.set(id, value);
      }
    };
  }
};

/** Marks a fully-qualified setting as explicitly set by the user at the given scope. */
export function setUserConfiguration(id: string, value: unknown, target: number = ConfigurationTarget.Global): void {
  (target === ConfigurationTarget.Workspace ? workspaceOverrides : globalOverrides).set(id, value);
  configuration.set(id, value);
}

/** Reads back what `update()` wrote, so a test can assert scope as well as value. */
export function readUserConfiguration(id: string, target: number = ConfigurationTarget.Global): unknown {
  return (target === ConfigurationTarget.Workspace ? workspaceOverrides : globalOverrides).get(id);
}

/** Makes `update()` reject for one setting id, exercising the partial-failure path. */
export function failConfigurationUpdate(id: string): void { failingUpdates.add(id); }

export interface StubSession { accessToken: string; scopes: string[]; account?: { label?: string } }
/** Sessions handed out by `authentication.getSession`, in order. */
export const sessionResponses: Array<StubSession | undefined> = [];
/** Every getSession call, so a test can assert the options actually passed. */
export const sessionRequests: Array<{ providerId: string; scopes: string[]; options: unknown }> = [];

/** Accounts the provider knows about, for the account-pinned session request. */
export const authenticationAccounts: Array<{ id: string; label: string }> = [];

export const authentication = {
  async getSession(providerId: string, scopes: string[], options: unknown): Promise<StubSession | undefined> {
    sessionRequests.push({ providerId, scopes: [...scopes], options });
    return sessionResponses.shift();
  },
  async getAccounts(_providerId: string): Promise<ReadonlyArray<{ id: string; label: string }>> {
    return [...authenticationAccounts];
  }
};

function webview() {
  let receiver: ((message: { command?: string }) => void) | undefined;
  return { html: "", options: {}, cspSource: "vscode-webview:", asWebviewUri: (uri: Uri) => uri, onDidReceiveMessage: (callback: (message: { command?: string }) => void) => { receiver = callback; return { dispose() {} }; }, receive: (message: { command?: string }) => receiver?.(message) };
}
function panel() { return { webview: webview(), revealed: false, reveal() { this.revealed = true; }, onDidDispose: () => ({ dispose() {} }) }; }

export const window = {
  activeColorTheme: { kind: 2 },
  createStatusBarItem(): { text: string; tooltip: unknown; command?: string; name?: string; backgroundColor?: unknown; show(): void; hide(): void; dispose(): void } {
    const item = { text: "", tooltip: undefined as unknown, command: undefined as string | undefined, name: undefined as string | undefined, shown: false, show() { this.shown = true; }, hide() { this.shown = false; }, dispose() { this.shown = false; } };
    statusItems.push(item); return item;
  },
  createWebviewPanel() { const created = panel(); webviewPanels.push(created); return created; },
  registerWebviewViewProvider(_id: string, provider: unknown): { dispose(): void } { webviewProviders.push(provider); return { dispose() {} }; },
  async showInputBox(): Promise<string | undefined> { return inputs.shift(); },
  async showInformationMessage(message: string): Promise<string | undefined> { messages.information.push(message); return undefined; },
  async showWarningMessage(message: string): Promise<string | undefined> { messages.warnings.push(message); return undefined; },
  async showErrorMessage(message: string): Promise<string | undefined> { messages.errors.push(message); return undefined; },
  createOutputChannel(name: string): { name: string; appendLine(line: string): void; show(preserve?: boolean): void; dispose(): void } {
    const channel = { name, appendLine(line: string) { outputLines.push(line); }, show() { /* no-op */ }, dispose() { /* no-op */ } };
    return channel;
  }
};

/** Everything written to the diagnostics output channel, for leak assertions. */
export const outputLines: string[] = [];

/**
 * The installed-extension registry, so the update watcher can be exercised.
 *
 * Mirrors `vscode.extensions`: `getExtension` returns undefined for an extension
 * that is not installed, which is the state the watcher reads as "uninstall in
 * progress" during the installers' uninstall-then-reinstall sequence.
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

/** The `context.extension` every activation needs. Version is the RUNNING one. */
export function stubExtension(id = "nexus-hub.github-usage-monitor", version = "0.0.0-test"): { id: string; packageJSON: { version: string } } {
  return { id, packageJSON: { version } };
}

export function setConfiguration(key: string, value: unknown): void { configuration.set(key, value); }
export function queueInput(value: string | undefined): void { inputs.push(value); }
export async function runCommand(name: string): Promise<unknown> { const command = commandMap.get(name); if (!command) throw new Error(`Command not registered: ${name}`); return command(); }
export function resetVscodeStub(): void { commandMap.clear(); configuration.clear(); globalOverrides.clear(); workspaceOverrides.clear(); failingUpdates.clear(); configurationLog.length = 0; inputs.length = 0; messages.information.length = 0; messages.warnings.length = 0; messages.errors.length = 0; statusItems.length = 0; webviewPanels.length = 0; webviewProviders.length = 0; sessionResponses.length = 0; sessionRequests.length = 0; outputLines.length = 0; extensionRegistry.clear(); extensionChangeListeners.length = 0; authenticationAccounts.length = 0; }

/** Mirrors VS Code's enum: Light=1, Dark=2, HighContrast=3, HighContrastLight=4. */
export const ColorThemeKind = { Light: 1, Dark: 2, HighContrast: 3, HighContrastLight: 4 } as const;

/** Fires a configuration-change event at every registered listener. */
export function fireConfigChange(changedKeys: readonly string[]): void {
  for (const listener of configListeners) {
    listener({ affectsConfiguration: (key: string) => changedKeys.includes(key) });
  }
}
