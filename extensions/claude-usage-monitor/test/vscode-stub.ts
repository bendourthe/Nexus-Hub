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
export function __resetStubState(): void {
  createdStatusBarItems.length = 0;
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

export const ColorThemeKind = { Light: 1, Dark: 2, HighContrast: 3, HighContrastLight: 4 } as const;

export class ThemeColor {
  constructor(public readonly id: string) {}
}

export const commands = {
  executeCommand(): Promise<void> {
    return Promise.resolve();
  },
};
