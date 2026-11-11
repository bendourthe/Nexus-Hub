import * as fs from "node:fs";
import { createRequire } from "node:module";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { SettingsViewProvider } from "../src/settingsView";
import { SOURCE_HOSTS } from "../src/viewModel";

const here = path.dirname(fileURLToPath(import.meta.url));
const ext = path.resolve(here, "..");
const repo = path.resolve(ext, "..", "..");
const require = createRequire(import.meta.url);
const manifest = JSON.parse(fs.readFileSync(path.join(ext, "package.json"), "utf8")) as Record<string, any>;
const verify = require("../scripts/verify-package-contents.js") as {
  collectErrors(files: string[], required: string[]): string[];
  STATIC_REQUIRED: string[];
};

function sources(dir: string, suffix = ".ts"): string[] {
  return fs.readdirSync(dir).filter((name) => name.endsWith(suffix)).map((name) => path.join(dir, name));
}

describe("manifest", () => {
  it("matches the plan: publisher, engines, activation, command, and an activity-bar view", () => {
    expect(manifest.publisher).toBe("nexus-hub");
    expect(manifest.engines).toEqual({ vscode: "^1.85.0", node: ">=22.0.0" });
    expect(manifest.activationEvents).toEqual(["*", "onCommand:nexusHubSettings.openCodex"]);
    expect(manifest.contributes.commands).toEqual(expect.arrayContaining([{ command: "nexusHubSettings.newCodexAgent", title: "New Codex Agent", category: "Nexus Hub" }, { command: "nexusHubSettings.open", title: "Open Settings", category: "Nexus Hub" }]));
    expect(manifest.contributes.viewsContainers.activitybar).toHaveLength(1);
    const view = manifest.contributes.views[manifest.contributes.viewsContainers.activitybar[0].id][0];
    expect(view).toMatchObject({ id: SettingsViewProvider.viewType, type: "webview" });
  });

  it("supports untrusted workspaces only in a limited, read-only way, and runs on the UI side", () => {
    expect(manifest.capabilities.untrustedWorkspaces.supported).toBe("limited");
    expect(manifest.capabilities.untrustedWorkspaces.description).toMatch(/cannot change anything/);
    expect(manifest.capabilities.virtualWorkspaces.supported).toBe(false);
    expect(manifest.extensionKind).toEqual(["ui"]);
  });

  it("lets only the user choose the interpreter, never a workspace", () => {
    const setting = manifest.contributes.configuration.properties["nexusHubSettings.pythonPath"];
    expect(setting.scope).toBe("machine");
    expect(setting.default).toBe("");
  });

  it("has the build scripts the stability gate runs and exact dependency versions", () => {
    for (const name of ["compile", "test", "test:coverage", "package", "verify:package"]) {
      expect(manifest.scripts[name]).toBeTruthy();
    }
    expect(manifest.scripts.package).toBe("vsce package --no-dependencies");
    for (const [name, version] of Object.entries(manifest.devDependencies as Record<string, string>)) {
      expect(version, name).toMatch(/^\d+\.\d+\.\d+$/);
    }
  });

  it("uses the original Nexus mark consistently on every Settings surface", () => {
    const logo = fs.readFileSync(path.join(repo, "assets", "nexus-hub-favicon", "android-chrome-512x512.png"));
    const settingsIcon = fs.readFileSync(path.join(ext, manifest.icon));
    expect(settingsIcon.equals(logo)).toBe(true);
    expect(fs.readFileSync(path.join(ext, "media", "logo.png")).equals(settingsIcon)).toBe(true);
    expect(settingsIcon.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
    expect(settingsIcon.readUInt32BE(16)).toBe(512);
    expect(settingsIcon.readUInt32BE(20)).toBe(512);
    expect(settingsIcon[25]).toBe(6); // RGBA supports a transparent background.
    const sidebar = fs.readFileSync(path.join(ext, "media", "icon.svg"), "utf8");
    const statusBar = fs.readFileSync(path.join(ext, "icons", "nexus-hub.svg"), "utf8");
    expect(statusBar).toBe(sidebar);
  });

  it("keeps developer files out of the package", () => {
    const ignore = fs.readFileSync(path.join(ext, ".vscodeignore"), "utf8").split(/\r?\n/);
    for (const entry of ["src/**", "test/**", "scripts/**", "node_modules/**", "**/*.map"]) {
      expect(ignore).toContain(entry);
    }
  });
});

describe("package content check", () => {
  it("requires the runtime files and rejects developer and credential files", () => {
    const required = [...verify.STATIC_REQUIRED, "out/extension.js"];
    expect(verify.collectErrors(required, required)).toEqual([]);
    expect(verify.collectErrors(["package.json"], required)[0]).toContain("missing required packaged file");
    for (const bad of ["src/cliBridge.ts", "test/x.test.ts", "coverage/index.html", "out/extension.js.map", "x.vsix", ".env", "auth.json", "a/secrets.txt", "id.pem", ".npmrc"]) {
      expect(verify.collectErrors([...required, bad], required).some((e) => e.includes("forbidden file")), bad).toBe(true);
    }
  });
});

describe("catalog sources", () => {
  it("only reports source links on hosts the panel is allowed to open", () => {
    const catalog = JSON.parse(fs.readFileSync(path.join(repo, "scripts", "lib", "settings_control", "catalog.json"), "utf8")) as unknown;
    const hosts = new Set<string>();
    const walk = (node: unknown): void => {
      if (Array.isArray(node)) {
        node.forEach(walk);
      } else if (node && typeof node === "object") {
        for (const [key, value] of Object.entries(node)) {
          if (key === "url" && typeof value === "string") {
            hosts.add(new URL(value).hostname);
          } else {
            walk(value);
          }
        }
      }
    };
    walk(catalog);
    expect(hosts.size).toBeGreaterThan(0);
    for (const host of hosts) {
      expect(SOURCE_HOSTS, host).toContain(host);
    }
  });
});

describe("process launches", () => {
  it("starts every child process windowless, without a shell, and never detached", () => {
    const files = [...sources(path.join(ext, "src")), ...sources(path.join(ext, "scripts"), ".js")];
    let launches = 0;
    for (const file of files) {
      const text = fs.readFileSync(file, "utf8");
      const streamingPolicy = path.basename(file) === "nativeStreamProcess.ts";
      if (streamingPolicy) {
        expect(text.match(/\bspawn\s*\(/g)).toHaveLength(1);
        expect(text).toContain("windowsHide: true");
        expect(text).toContain("shell: false");
        expect(text).toContain('stdio: ["pipe", "pipe", "pipe"]');
      } else { expect(text, file).not.toMatch(/(?<![.\w])(spawn|spawnSync|exec|execSync|fork)\s*\(/); }
      for (const imported of text.matchAll(/import\s*\{([^}]*)\}\s*from\s*["']node:child_process["']/g)) {
        const names = (imported[1] ?? "").split(",").map((n) => n.trim()).filter(Boolean);
        expect(names.every((n) => n === "execFile" || n === "execFileSync" || (streamingPolicy && n === "spawn")), `${file} imports ${names.join(",")}`).toBe(true);
      }
      expect(text, file).not.toMatch(/import\s+\*\s+as\s+\w+\s+from\s*["']node:child_process["']/);
      expect(text, file).not.toMatch(/shell:\s*true|detached:\s*true|DETACHED_PROCESS|CREATE_NEW_CONSOLE/);
      for (const match of text.matchAll(/\b(execFile|execFileSync)\s*\(/g)) {
        launches += 1;
        const call = text.slice(match.index, match.index + 600);
        expect(call, `${file}: ${match[0]}`).toContain("windowsHide: true");
      }
    }
    expect(launches).toBeGreaterThan(0);
  });

  it("never reads the interpreter or the command line from PATH or a workspace", () => {
    const bridge = fs.readFileSync(path.join(ext, "src", "cliBridge.ts"), "utf8");
    expect(bridge).not.toMatch(/process\.env\.PATH|env\.PATH|which\(|workspaceFolders|process\.cwd\(/);
    expect(bridge).toContain("shell: false");
  });
});
