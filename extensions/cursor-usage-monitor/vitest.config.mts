import { defineConfig } from "vitest/config";

export default defineConfig({
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
