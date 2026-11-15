import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

/**
 * Vitest configuration for the settings panel's unit tests.
 *
 * The extension modules import `vscode`, which only resolves inside a real
 * extension host. The alias points it at a stub that models the pieces the panel
 * touches (configuration layers, modal dialogs, webview views). The webview
 * script is tested against a DOM per file with the `@vitest-environment` docblock.
 */
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json", "clover"],
      include: ["src/**/*.ts", "media/panel.js"],
      // The live-effort launcher compiles and runs real Windows executables; its tests run only on
      // Windows (developer machines; a hosted Windows CI leg is v4.15 known gap MT-8). Elsewhere it is not executable.
      exclude: process.platform === "win32" ? [] : ["src/liveEffort.ts"],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
  resolve: {
    alias: {
      vscode: fileURLToPath(new URL("./test/vscode-stub.ts", import.meta.url)),
    },
  },
});
