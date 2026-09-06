import { createRequire } from "node:module";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const require_ = createRequire(__filename);
const {
  collectErrors,
  discoverRuntimeFiles,
  packageFilesFromArchiveEntries,
  REQUIRED
} = require_(
  resolve(__dirname, "../scripts/verify-package-contents.js")
) as {
  collectErrors: (files: string[], required?: string[]) => string[];
  discoverRuntimeFiles: (entry: string, root: string) => string[];
  packageFilesFromArchiveEntries: (entries: string[]) => string[];
  REQUIRED: string[];
};

const CLEAN = [...REQUIRED, "out/providers/cursor.js"];

describe("VSIX content verification", () => {
  it("accepts a package carrying every runtime asset", () => {
    expect(collectErrors(CLEAN)).toEqual([]);
  });

  it("names a missing runtime asset", () => {
    const withoutFont = CLEAN.filter((file) => file !== "fonts/cursor-icons.woff2");
    expect(collectErrors(withoutFont)).toEqual([
      "missing required packaged file: fonts/cursor-icons.woff2"
    ]);
  });

  it("requires every local JavaScript module reachable from the runtime entry", () => {
    const root = mkdtempSync(join(tmpdir(), "cursor-usage-package-"));
    try {
      writeFileSync(join(root, "extension.js"), 'require("./dashboard");\n');
      writeFileSync(join(root, "dashboard.js"), 'require("./providers/cursor");\n');
      mkdirSync(join(root, "providers"));
      writeFileSync(join(root, "providers", "cursor.js"), "module.exports = {};\n");

      expect(discoverRuntimeFiles(join(root, "extension.js"), root)).toEqual([
        "dashboard.js",
        "extension.js",
        "providers/cursor.js"
      ]);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  it("fails when a discovered runtime module is absent", () => {
    expect(
      collectErrors(CLEAN, [...REQUIRED, "out/dashboardPanel.js"])
    ).toContain("missing required packaged file: out/dashboardPanel.js");
  });

  it("normalizes files from the generated VSIX extension directory", () => {
    expect(
      packageFilesFromArchiveEntries([
        "[Content_Types].xml",
        "extension.vsixmanifest",
        "extension/",
        "extension/LICENSE.txt",
        "extension/package.json",
        "extension/readme.md",
        "extension/out/extension.js"
      ])
    ).toEqual(["LICENSE", "README.md", "out/extension.js", "package.json"]);
  });

  it.each([
    "coverage/index.html",
    "src/extension.ts",
    "test/assets.test.ts",
    "scripts/generate-icon-font.js",
    "node_modules/vitest/package.json",
    "cursor-usage-monitor-0.1.0.vsix",
    "out/extension.js.map"
  ])("rejects the build-time artifact %s", (artifact) => {
    expect(collectErrors([...CLEAN, artifact])).toHaveLength(1);
  });

  it.each([
    ".env",
    "config/.env.local",
    "auth.json",
    "deploy.pem",
    "signing.key",
    "secret",
    "secrets.json"
  ])("rejects the credential-shaped file %s", (credential) => {
    expect(collectErrors([...CLEAN, credential])).toHaveLength(1);
  });
});
