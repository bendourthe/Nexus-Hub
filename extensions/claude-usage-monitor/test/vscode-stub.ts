/**
 * Minimal `vscode` module stub for Vitest.
 *
 * The provider modules import `vscode` at module scope, so this stub only needs
 * to be importable and to expose the handful of members those modules reference.
 * The pure functions under test never call into it; it exists so the import
 * graph resolves under plain Node. Extend it as more surface gets unit-tested.
 */

export const ConfigurationTarget = { Global: 1, Workspace: 2, WorkspaceFolder: 3 } as const;

export const StatusBarAlignment = { Left: 1, Right: 2 } as const;

interface StubConfiguration {
  get<T>(key: string, defaultValue: T): T;
  get<T>(key: string): T | undefined;
  update(...args: unknown[]): Promise<void>;
}

// Test-settable configuration (section -> key -> value). `__setStubConfig`
// writes here; `get` reads here first, else returns the caller's default - so
// existing provider tests (which never set anything) still get the default.
export const stubConfig: Record<string, Record<string, unknown>> = {};
export const configurationUpdates: Array<{
  section: string | undefined;
  key: string;
  value: unknown;
  target: unknown;
}> = [];
export function __setStubConfig(section: string, key: string, value: unknown): void {
  (stubConfig[section] ??= {})[key] = value;
}

// Every status-bar item created, in creation order, so tests can assert the
// priorities. `__resetStubState` clears both stores between tests.
export const createdStatusBarItems: Array<Record<string, unknown>> = [];
export const createdWebviewPanels: Array<Record<string, any>> = [];
export function __resetStubState(): void {
  createdStatusBarItems.length = 0;
  createdWebviewPanels.length = 0;
  configurationUpdates.length = 0;
  for (const k of Object.keys(stubConfig)) {
    delete stubConfig[k];
  }
}

export const workspace = {
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
        const sectionKey = section ?? "";
        const sectionMap = (stubConfig[sectionKey] ??= {});
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

export const window = {
  activeColorTheme: { kind: 1 },
  createWebviewPanel(_viewType: string, _title: string, _col?: unknown, _opts?: unknown): Record<string, any> {
    const panel: Record<string, any> = {
      webview: {
        html: "",
        onDidReceiveMessage: () => ({ dispose() {} }),
        postMessage: () => {},
      },
      onDidDispose: () => ({ dispose() {} }),
      reveal() {},
      dispose() {},
      iconPath: undefined,
    };
    createdWebviewPanels.push(panel);
    return panel;
  },
  createStatusBarItem(alignment?: unknown, priority?: number): Record<string, unknown> {
    const item: Record<string, unknown> = {
      alignment,
      priority,
      text: "",
      tooltip: "",
      command: "",
      name: "",
      backgroundColor: undefined,
      show() {},
      hide() {},
      dispose() {},
    };
    createdStatusBarItems.push(item);
    return item;
  },
};

export const ViewColumn = { Active: -1, Beside: -2, One: 1, Two: 2 } as const;

export const ColorThemeKind = { Light: 1, Dark: 2, HighContrast: 3, HighContrastLight: 4 } as const;

/**
 * Minimal `MarkdownString`. The status-bar tooltip is built entirely through
 * this type, so without it the data-path tooltip - including the percent-
 * encoded inline SVG for each bar - could not be asserted at all (v4.10.0 MT-2).
 */
export class MarkdownString {
  public value: string;
  public isTrusted = false;
  public supportThemeIcons = false;
  public supportHtml = false;
  constructor(value = "", supportThemeIcons = false) {
    this.value = value;
    this.supportThemeIcons = supportThemeIcons;
  }
  appendMarkdown(markdown: string): MarkdownString {
    this.value += markdown;
    return this;
  }
}

export class ThemeColor {
  constructor(public readonly id: string) {}
}

export const commands = {
  executeCommand(): Promise<void> {
    return Promise.resolve();
  },
};
