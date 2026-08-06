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

export const workspace = {
  getConfiguration(section: string): { get<T>(key: string, defaultValue?: T): T } {
    return { get<T>(key: string, defaultValue?: T): T { return (configuration.get(`${section}.${key}`) as T | undefined) ?? defaultValue as T; } };
  }
};

export interface StubSession { accessToken: string; scopes: string[]; account?: { label?: string } }
/** Sessions handed out by `authentication.getSession`, in order. */
export const sessionResponses: Array<StubSession | undefined> = [];
/** Every getSession call, so a test can assert the options actually passed. */
export const sessionRequests: Array<{ providerId: string; scopes: string[]; options: unknown }> = [];

export const authentication = {
  async getSession(providerId: string, scopes: string[], options: unknown): Promise<StubSession | undefined> {
    sessionRequests.push({ providerId, scopes: [...scopes], options });
    return sessionResponses.shift();
  }
};

function webview() {
  let receiver: ((message: { command?: string }) => void) | undefined;
  return { html: "", options: {}, cspSource: "vscode-webview:", asWebviewUri: (uri: Uri) => uri, onDidReceiveMessage: (callback: (message: { command?: string }) => void) => { receiver = callback; return { dispose() {} }; }, receive: (message: { command?: string }) => receiver?.(message) };
}
function panel() { return { webview: webview(), revealed: false, reveal() { this.revealed = true; }, onDidDispose: () => ({ dispose() {} }) }; }

export const window = {
  createStatusBarItem(): { text: string; tooltip: unknown; command?: string; name?: string; backgroundColor?: unknown; show(): void; hide(): void; dispose(): void } {
    const item = { text: "", tooltip: undefined as unknown, command: undefined as string | undefined, name: undefined as string | undefined, shown: false, show() { this.shown = true; }, hide() { this.shown = false; }, dispose() { this.shown = false; } };
    statusItems.push(item); return item;
  },
  createWebviewPanel() { const created = panel(); webviewPanels.push(created); return created; },
  registerWebviewViewProvider(_id: string, provider: unknown): { dispose(): void } { webviewProviders.push(provider); return { dispose() {} }; },
  async showInputBox(): Promise<string | undefined> { return inputs.shift(); },
  async showInformationMessage(message: string): Promise<string | undefined> { messages.information.push(message); return undefined; },
  async showWarningMessage(message: string): Promise<string | undefined> { messages.warnings.push(message); return undefined; },
  async showErrorMessage(message: string): Promise<string | undefined> { messages.errors.push(message); return undefined; }
};

export function setConfiguration(key: string, value: unknown): void { configuration.set(key, value); }
export function queueInput(value: string | undefined): void { inputs.push(value); }
export async function runCommand(name: string): Promise<unknown> { const command = commandMap.get(name); if (!command) throw new Error(`Command not registered: ${name}`); return command(); }
export function resetVscodeStub(): void { commandMap.clear(); configuration.clear(); inputs.length = 0; messages.information.length = 0; messages.warnings.length = 0; messages.errors.length = 0; statusItems.length = 0; webviewPanels.length = 0; webviewProviders.length = 0; sessionResponses.length = 0; sessionRequests.length = 0; }
