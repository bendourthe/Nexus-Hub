import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      vscode: fileURLToPath(
        new URL("./test/vscode-stub.ts", import.meta.url)
      )
    }
  },
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json", "clover"],
      include: ["src/**/*.ts"],
      exclude: ["test/**"],
      thresholds: {
        statements: 80,
        branches: 75,
        functions: 75,
        lines: 80
      }
    }
  }
});
