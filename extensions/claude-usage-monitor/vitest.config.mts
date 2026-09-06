import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

/**
 * Vitest configuration for the extension's provider unit tests.
 *
 * The provider data layer is VS-Code-independent (it uses fs / os / fetch), but
 * its modules transitively `import * as vscode from "vscode"`, which only
 * resolves inside a real extension host. The alias below points `vscode` at a
 * minimal stub so pure provider logic can be unit-tested under plain Node.
 */
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
  },
  resolve: {
    alias: {
      vscode: fileURLToPath(new URL("./test/vscode-stub.ts", import.meta.url)),
    },
  },
});
