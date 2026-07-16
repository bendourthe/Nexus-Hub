/**
 * Minimal `vscode` module stub for Vitest.
 *
 * The provider modules import `vscode` at module scope, so this stub only needs
 * to be importable and to expose the handful of members those modules reference.
 * The pure functions under test never call into it; it exists so the import
 * graph resolves under plain Node. Extend it as more surface gets unit-tested.
 */

export const ConfigurationTarget = { Global: 1, Workspace: 2, WorkspaceFolder: 3 } as const;

interface StubConfiguration {
  get<T>(key: string, defaultValue: T): T;
  get<T>(key: string): T | undefined;
  update(...args: unknown[]): Promise<void>;
}

export const workspace = {
  getConfiguration(_section?: string): StubConfiguration {
    return {
      get<T>(_key: string, defaultValue?: T): T | undefined {
        return defaultValue;
      },
      async update(): Promise<void> {
        /* no-op in tests */
      },
    };
  },
  onDidChangeConfiguration(): { dispose(): void } {
    return { dispose() {} };
  },
};

export const window = {
  activeColorTheme: { kind: 1 },
  createStatusBarItem() {
    return { show() {}, hide() {}, dispose() {} };
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
