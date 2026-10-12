import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import * as fs from "node:fs";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { runInNewContext } from "node:vm";
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

describe.each(["copilot-usage-monitor", "cursor-usage-monitor"])(
  "%s runtime discovery",
  (extension) => {
    const script = resolve(__dirname, "../../", extension, "scripts/verify-package-contents.js");

    function loadVerifier(overrides: object): typeof discoverRuntimeFiles {
      const module = { exports: {} as { discoverRuntimeFiles: typeof discoverRuntimeFiles } };
      runInNewContext(fs.readFileSync(script, "utf8"), {
        __dirname: dirname(script),
        module,
        require: (name: string) => name === "node:fs" ? { ...fs, ...overrides } : require_(name)
      }, { timeout: 1000 });
      return module.exports.discoverRuntimeFiles;
    }

    it("reads the checked object when its path is replaced after the file-type check", () => {
      const root = mkdtempSync(join(tmpdir(), "usage-package-race-"));
      const entry = join(root, "extension.js");
      const descriptors = new Map<number, string>();
      let replaced = false;
      function replaceEntry(file: string | undefined): void {
        if (file !== entry || replaced) {
          return;
        }
        replaced = true;
        fs.renameSync(entry, join(root, "checked-original.js"));
        writeFileSync(entry, 'require("./replacement");\n');
      }
      try {
        writeFileSync(entry, 'require("./original");\n');
        writeFileSync(join(root, "original.js"), "module.exports = {};\n");
        writeFileSync(join(root, "replacement.js"), "module.exports = {};\n");
        const discover = loadVerifier({
          statSync: (file: string) => {
            const stat = fs.statSync(file);
            replaceEntry(file);
            return stat;
          },
          openSync: (file: string, flags: fs.OpenMode) => {
            const fd = fs.openSync(file, flags);
            descriptors.set(fd, file);
            return fd;
          },
          fstatSync: (fd: number) => {
            const stat = fs.fstatSync(fd);
            replaceEntry(descriptors.get(fd));
            return stat;
          },
          closeSync: (fd: number) => {
            fs.closeSync(fd);
            descriptors.delete(fd);
          }
        });
        expect(discover(entry, root)).toEqual(["extension.js", "original.js"]);
        expect(replaced).toBe(true);
        expect(fs.readFileSync(entry, "utf8")).toContain("./replacement");
        expect(descriptors.size).toBe(0);
      } finally {
        for (const fd of descriptors.keys()) {
          fs.closeSync(fd);
        }
        rmSync(root, { recursive: true, force: true });
      }
    });

    it("closes an opened module when reading it fails", () => {
      const root = mkdtempSync(join(tmpdir(), "usage-package-read-error-"));
      const entry = join(root, "extension.js");
      const descriptors = new Set<number>();
      const readError = new Error("injected runtime read failure");
      let opened = 0;
      try {
        writeFileSync(entry, "module.exports = {};\n");
        const discover = loadVerifier({
          openSync: (file: string, flags: fs.OpenMode) => {
            const fd = fs.openSync(file, flags);
            descriptors.add(fd);
            opened += 1;
            return fd;
          },
          readFileSync: () => { throw readError; },
          closeSync: (fd: number) => {
            fs.closeSync(fd);
            descriptors.delete(fd);
          }
        });
        expect(() => discover(entry, root)).toThrow(readError);
        expect(opened).toBe(1);
        expect(descriptors.size).toBe(0);
      } finally {
        for (const fd of descriptors) {
          fs.closeSync(fd);
        }
        rmSync(root, { recursive: true, force: true });
      }
    });

    it("rejects a missing or non-regular entry with the module error", () => {
      const root = mkdtempSync(join(tmpdir(), "usage-package-invalid-entry-"));
      try {
        const discover = loadVerifier({});
        expect(() => discover(join(root, "missing.js"), root)).toThrow("runtime module is missing:");
        expect(() => discover(root, root)).toThrow("runtime module is missing:");
      } finally {
        rmSync(root, { recursive: true, force: true });
      }
    });

    it.skipIf(process.platform === "win32")("rejects a FIFO without waiting for a writer", () => {
      const root = mkdtempSync(join(tmpdir(), "usage-package-fifo-"));
      const entry = join(root, "extension.js");
      try {
        expect(spawnSync("mkfifo", [entry]).status).toBe(0);
        const result = spawnSync(process.execPath, ["-e", [
          "try {",
          "require(process.argv[1]).discoverRuntimeFiles(process.argv[2], process.argv[3]);",
          "process.exitCode = 1;",
          "} catch (error) {",
          "if (error.message !== 'runtime module is missing: ' + process.argv[2]) throw error;",
          "console.log(error.message);",
          "}"
        ].join("\n"), script, entry, root], { encoding: "utf8", timeout: 2000 });
        expect(result.error).toBeUndefined();
        expect(result.status, result.stderr).toBe(0);
        expect(result.stdout.trim()).toBe(`runtime module is missing: ${entry}`);
      } finally {
        rmSync(root, { recursive: true, force: true });
      }
    });
  }
);

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
    "secrets.json",
    "out/credentials.json",
    "credential.txt",
    "out/session.token",
    "token.json",
    "id_rsa",
    "keys/id_ed25519.pub",
    "signing.p12",
    "signing.pfx",
    ".npmrc"
  ])("rejects the credential-shaped file %s", (credential) => {
    expect(collectErrors([...CLEAN, credential])).toHaveLength(1);
  });
});
