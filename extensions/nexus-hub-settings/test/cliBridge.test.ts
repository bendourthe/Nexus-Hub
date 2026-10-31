import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const launched: { command: string; args: string[]; options: Record<string, unknown> }[] = [];

vi.mock("node:child_process", async (importOriginal) => {
  const actual = await importOriginal<typeof import("node:child_process")>();
  return {
    ...actual,
    execFile: ((command: string, args: string[], options: Record<string, unknown>, callback: never) => {
      launched.push({ command, args, options });
      return (actual.execFile as unknown as (...a: unknown[]) => unknown)(command, args, options, callback);
    }) as unknown as typeof actual.execFile,
  };
});

import {
  BridgeError,
  CliBridge,
  INSTALL_COMMAND,
  buildArgs,
  candidateInterpreters,
  installRoot,
} from "../src/cliBridge";

const FAKE_CLI = `
const fs = require("fs");
const args = process.argv.slice(2);
const scenario = process.env.FAKE_SCENARIO || "show";
const home = process.env.FAKE_HOME;
const tokenFile = home ? require("path").join(home, ".nexus-hub", "settings-panel-token.json") : "";
const report = { schema_version: 1, project: null, platform: "windows", tools: {}, records: [] };
if (scenario === "show") { console.log(JSON.stringify({ ...report, argv: args, cwd: process.cwd(), utf8: process.env.PYTHONUTF8 })); }
else if (scenario === "usage") { console.error("nexus-hub settings: unknown control 'x'"); process.exit(2); }
else if (scenario === "refused") { console.error("nexus-hub settings: refused: an agent session is running"); process.exit(3); }
else if (scenario === "nothing") { console.log(JSON.stringify({ schema_version: 1, action: "set", results: [], exit_code: 4 })); process.exit(4); }
else if (scenario === "partial") { console.log(JSON.stringify({ schema_version: 1, action: "set", results: [], exit_code: 1 })); process.exit(1); }
else if (scenario === "badjson") { console.log("not json"); }
else if (scenario === "wrongshape") { console.log(JSON.stringify({ hello: 1 })); }
else if (scenario === "crash") { console.error("Traceback (most recent call last):\\n  boom"); process.exit(1); }
else if (scenario === "weird") { console.error("odd"); process.exit(9); }
else if (scenario === "sleep") { setTimeout(() => {}, 20000); }
else if (scenario === "token") {
  const seen = tokenFile && fs.existsSync(tokenFile) ? JSON.parse(fs.readFileSync(tokenFile, "utf8")) : null;
  console.log(JSON.stringify({ schema_version: 1, action: "set", results: [], exit_code: 0, seen }));
}
else if (scenario === "record") { console.log(JSON.stringify({ schema_version: 1, action: "record-editor-write", exit_code: 0, argv: args })); }
else if (scenario === "record-fail") { console.error("nexus-hub settings: bad payload"); process.exit(2); }
`;

let dirs: string[] = [];

function temp(label: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `nhs-${label}-`));
  dirs.push(dir);
  return dir;
}

function install(scenario: string, extra: Partial<ConstructorParameters<typeof CliBridge>[0]> = {}) {
  const home = temp("home");
  const root = path.join(home, ".nexus-hub");
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.writeFileSync(path.join(root, "scripts", "nexus_hub_cli.py"), FAKE_CLI);
  const bridge = new CliBridge({
    home,
    env: { ...process.env, FAKE_SCENARIO: scenario, FAKE_HOME: home },
    interpreter: { command: process.execPath, args: [] },
    ...extra,
  });
  return { home, root, bridge };
}

beforeEach(() => {
  launched.length = 0;
});

afterEach(() => {
  dirs.forEach((dir) => fs.rmSync(dir, { recursive: true, force: true }));
  dirs = [];
});

describe("argument building", () => {
  it("builds set, reset, and remove-override arguments with the workspace as --project", () => {
    expect(buildArgs({ action: "set", control: "effort", value: "high", tool: "claude", dryRun: true, project: "C:\\w" })).toEqual([
      "settings", "set", "effort", "high", "--tool", "claude", "--dry-run", "--json", "--project=C:\\w",
    ]);
    expect(buildArgs({ action: "set", control: "posture", value: "ask" })).toEqual(["settings", "set", "posture", "ask", "--json"]);
    expect(buildArgs({ action: "reset", control: "model", tool: "codex" })).toEqual(["settings", "reset", "model", "--tool", "codex", "--json"]);
    expect(buildArgs({ action: "reset", control: "model" })).toEqual(["settings", "reset", "model", "--json"]);
    expect(buildArgs({ action: "remove-override", control: "effort", tool: "claude" })).toEqual(["settings", "remove-override", "effort", "--tool", "claude", "--json"]);
  });

  it.each([
    [{ action: "set", control: "Effort", value: "high" }, "invalid control id"],
    [{ action: "set", control: "effort", value: "high", tool: "Claude Code" }, "invalid tool id"],
    [{ action: "set", control: "model", value: "-rf" }, "must be 1 to 200"],
    [{ action: "set", control: "model", value: "" }, "must be 1 to 200"],
    [{ action: "set", control: "model", value: "caf\u00e9" }, "must be 1 to 200"],
    [{ action: "set", control: "model", value: "x".repeat(201) }, "must be 1 to 200"],
    [{ action: "remove-override", control: "effort" }, "needs a tool"],
  ] as const)("refuses an unsafe request %#", (spec, message) => {
    expect(() => buildArgs(spec as never)).toThrow(message);
    try {
      buildArgs(spec as never);
    } catch (error) {
      expect((error as BridgeError).kind).toBe("argument");
    }
  });
});

describe("install root and interpreter discovery", () => {
  it("uses NEXUS_HUB_HOME only when it is absolute", () => {
    expect(installRoot({ NEXUS_HUB_HOME: "C:\\hub" }, "C:\\Users\\a", "win32")).toBe("C:\\hub");
    expect(installRoot({ NEXUS_HUB_HOME: "relative\\hub" }, "C:\\Users\\a", "win32")).toBe("C:\\Users\\a\\.nexus-hub");
    expect(installRoot({}, "/home/a", "linux")).toBe("/home/a/.nexus-hub");
  });

  it("lists fixed absolute locations on POSIX and never a bare command name", () => {
    const found = candidateInterpreters("linux", {}, () => []);
    expect(found.length).toBeGreaterThan(0);
    expect(found.every((c) => path.posix.isAbsolute(c.command))).toBe(true);
  });

  it("lists per-user and machine installs newest first on Windows, then the py launcher", () => {
    const env = { LOCALAPPDATA: "C:\\Users\\a\\AppData\\Local", ProgramFiles: "C:\\Program Files", SystemRoot: "C:\\Windows" };
    const listing: Record<string, string[]> = {
      "C:\\Users\\a\\AppData\\Local\\Programs\\Python": ["Python311", "Python313", "Launcher", "Python39"],
      "C:\\Program Files": ["Python312", "Git"],
      "C:\\Users\\a\\AppData\\Local\\Microsoft\\WindowsApps": ["PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0", "PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0", "python.exe", "Microsoft.WindowsTerminal_8wekyb3d8bbwe"],
    };
    const found = candidateInterpreters("win32", env, (dir) => listing[dir] ?? []);
    expect(found.map((c) => c.command)).toEqual([
      "C:\\Users\\a\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "C:\\Users\\a\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "C:\\Users\\a\\AppData\\Local\\Programs\\Python\\Python39\\python.exe",
      "C:\\Program Files\\Python312\\python.exe",
      "C:\\Users\\a\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\\python.exe",
      "C:\\Users\\a\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\python.exe",
      "C:\\Users\\a\\AppData\\Local\\Programs\\Python\\Launcher\\py.exe",
      "C:\\Windows\\py.exe",
    ]);
    expect(found.at(-1)?.args[0]).toBe("-3");
    expect(candidateInterpreters("win32", {}, () => []).map((c) => c.command)).toEqual(["C:\\Windows\\py.exe"]);
  });

  it("uses the configured interpreter when it is an absolute existing file", () => {
    const configured = process.execPath;
    const bridge = new CliBridge({ pythonPath: () => `  ${configured}  ` });
    expect(bridge.interpreter().command).toBe(configured);
    expect(bridge.interpreter().args).toContain("-B");
  });

  it.each([["python"], ["relative/python"], [path.join(os.tmpdir(), "nhs-missing-python.exe")]])("refuses the configured value %s instead of falling back", (value) => {
    const bridge = new CliBridge({ pythonPath: () => value, listDir: () => [] });
    expect(() => bridge.interpreter()).toThrow("nexusHubSettings.pythonPath");
  });

  it("reports when no interpreter exists anywhere", () => {
    const bridge = new CliBridge({ platform: "win32", env: { SystemRoot: path.join(os.tmpdir(), "nhs-none") }, listDir: () => [] });
    expect(() => bridge.interpreter()).toThrow("no Python 3 interpreter");
    expect(bridge.describe()).toContain("python");
  });

  it("finds an existing standard-location interpreter through discovery", () => {
    const base = temp("py");
    const exe = path.join(base, "Programs", "Python", "Python312", "python.exe");
    fs.mkdirSync(path.dirname(exe), { recursive: true });
    fs.writeFileSync(exe, "");
    const bridge = new CliBridge({ platform: "win32", env: { LOCALAPPDATA: base, SystemRoot: path.join(base, "none") } });
    expect(bridge.interpreter().command).toBe(path.win32.join(base, "Programs", "Python", "Python312", "python.exe"));
  });
});

describe("running the command line", () => {
  it("runs with an absolute interpreter, shell false, hidden window, and the install root as cwd", async () => {
    const { root, bridge } = install("show");

    const report = (await bridge.show("C:\\work\\project")) as unknown as { argv: string[]; cwd: string; utf8: string };

    expect(report.argv).toEqual(["settings", "show", "--json", "--project=C:\\work\\project"]);
    expect(fs.realpathSync(report.cwd)).toBe(fs.realpathSync(root));
    expect(report.utf8).toBe("1");
    const call = launched.at(-1);
    expect(path.isAbsolute(call?.command ?? "")).toBe(true);
    expect(call?.options).toMatchObject({ shell: false, windowsHide: true, cwd: root });
    expect(call?.args[0]).toBe(path.join(root, "scripts", "nexus_hub_cli.py"));
  });

  it("never runs a nexus-hub or python plant in the workspace, even with it first on PATH and as cwd", async () => {
    const workspace = temp("workspace");
    const marker = path.join(workspace, "PWNED");
    for (const name of ["nexus-hub.cmd", "nexus-hub.exe", "nexus-hub", "python.cmd", "python.exe", "python", "python3"]) {
      fs.writeFileSync(path.join(workspace, name), `@echo off\r\necho planted> "${marker}"\r\n`, { mode: 0o755 });
    }
    const before = process.cwd();
    const { home, bridge } = install("show");
    const poisoned = new CliBridge({
      home,
      env: { ...process.env, FAKE_SCENARIO: "show", PATH: `${workspace}${path.delimiter}${process.env.PATH ?? ""}`, Path: `${workspace}${path.delimiter}${process.env.PATH ?? ""}` },
      interpreter: { command: process.execPath, args: [] },
    });
    process.chdir(workspace);
    try {
      await poisoned.show(workspace);
      await bridge.show(workspace);
    } finally {
      process.chdir(before);
    }

    expect(fs.existsSync(marker)).toBe(false);
    for (const call of launched) {
      expect(path.resolve(call.command).startsWith(workspace)).toBe(false);
      expect(call.args.some((a) => path.resolve(a).startsWith(workspace) && !a.startsWith("--project="))).toBe(false);
    }
  });

  it("explains a missing install with the command to run", async () => {
    const home = temp("empty");
    const bridge = new CliBridge({ home, platform: "win32", interpreter: { command: process.execPath, args: [] } });

    const error = await bridge.show().catch((e: unknown) => e as BridgeError);

    expect(error).toBeInstanceOf(BridgeError);
    expect((error as BridgeError).kind).toBe("no-install");
    expect((error as BridgeError).fix).toContain(INSTALL_COMMAND.win32);
    expect((error as BridgeError).command).toContain("nexus_hub_cli.py");
  });

  it("reports a posix install hint on other platforms", async () => {
    const home = temp("empty");
    const bridge = new CliBridge({ home, platform: "linux", interpreter: { command: "/usr/bin/python3", args: [] } });
    const error = (await bridge.show().catch((e: unknown) => e)) as BridgeError;
    expect(error.fix).toContain(INSTALL_COMMAND.posix);
  });

  it("times out slow commands and names the command it ran", async () => {
    const { bridge } = install("sleep", { timeoutMs: 300 });
    const error = (await bridge.show().catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe("timeout");
    expect(error.message).toContain("timed out");
    expect(error.command).toContain("nexus_hub_cli.py");
  }, 10_000);

  it("reports an interpreter that cannot start", async () => {
    const { bridge } = install("show", { interpreter: { command: path.join(os.tmpdir(), "nhs-no-such-interpreter"), args: [] } });
    const error = (await bridge.show().catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe("spawn");
  });

  it("surfaces a no-install or no-python failure from the interpreter lookup", async () => {
    const home = temp("nopy");
    fs.mkdirSync(path.join(home, ".nexus-hub", "scripts"), { recursive: true });
    fs.writeFileSync(path.join(home, ".nexus-hub", "scripts", "nexus_hub_cli.py"), FAKE_CLI);
    const bridge = new CliBridge({ home, platform: "linux", pythonPath: () => "relative" });
    const error = (await bridge.show().catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe("no-python");
  });

  it.each([
    ["badjson", "json"],
    ["wrongshape", "json"],
    ["crash", "exit"],
  ])("rejects unusable output (%s)", async (scenario, kind) => {
    const { bridge } = install(scenario);
    const error = (await bridge.show().catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe(kind);
    expect(error.fix.length).toBeGreaterThan(0);
  });

  it("fails a read when the command exits non-zero", async () => {
    const { bridge } = install("usage");
    const error = (await bridge.explain("effort").catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe("exit");
    expect(error.message).toContain("unknown control");
  });

  it("validates the explain shape and control id", async () => {
    const { bridge } = install("wrongshape");
    expect(((await bridge.explain("effort").catch((e: unknown) => e)) as BridgeError).kind).toBe("json");
    await expect(bridge.explain("Not A Control")).rejects.toThrow("invalid control id");
  });
});

describe("actions", () => {
  it("returns the parsed document for exit codes 0, 1, and 4", async () => {
    for (const [scenario, code] of [["show", 0], ["partial", 1], ["nothing", 4]] as const) {
      const { bridge } = install(scenario === "show" ? "token" : scenario);
      const outcome = await bridge.action({ action: "set", control: "effort", value: "high" });
      expect(outcome.exitCode).toBe(code);
      expect(outcome.doc?.exit_code).toBe(code);
    }
  });

  it("returns the command's own message for a usage error and a refusal", async () => {
    expect(await install("usage").bridge.action({ action: "reset", control: "effort" })).toMatchObject({ exitCode: 2, doc: null, message: expect.stringContaining("unknown control") });
    expect(await install("refused").bridge.action({ action: "reset", control: "effort" })).toMatchObject({ exitCode: 3, doc: null, message: expect.stringContaining("refused") });
  });

  it("treats an unknown exit code and an empty crash as failures", async () => {
    expect(((await install("weird").bridge.action({ action: "reset", control: "effort" }).catch((e: unknown) => e)) as BridgeError).kind).toBe("exit");
    expect(((await install("crash").bridge.action({ action: "reset", control: "effort" }).catch((e: unknown) => e)) as BridgeError).message).toContain("no usable JSON");
  });

  it("writes an owner-only one-time token just before a confirmed change and deletes it after", async () => {
    const { home, bridge } = install("token", { now: () => 1_700_000_000_500 });
    const tokenFile = path.join(home, ".nexus-hub", "settings-panel-token.json");

    const outcome = await bridge.action({ action: "set", control: "posture", value: "full-auto", tool: null, token: { action: "set", control: "posture", value: "full-auto", tool: null } });

    const seen = (outcome.doc as unknown as { seen: Record<string, unknown> }).seen;
    expect(seen).toMatchObject({ action: "set", control: "posture", value: "full-auto", tool: null, issued_at: 1_700_000_000.5 });
    expect(String(seen.token)).toMatch(/^[0-9a-f]{64}$/);
    expect(fs.existsSync(tokenFile)).toBe(false);
    if (process.platform !== "win32") {
      expect(fs.statSync(tokenFile.replace(/[^/]+$/, "")).mode & 0o077).toBe(0);
    }
  });

  it("replaces a stale token and removes it even when the command refuses", async () => {
    const { home, bridge } = install("refused");
    const tokenFile = path.join(home, ".nexus-hub", "settings-panel-token.json");
    fs.mkdirSync(path.dirname(tokenFile), { recursive: true });
    fs.writeFileSync(tokenFile, "stale");

    const outcome = await bridge.action({ action: "remove-override", control: "effort", tool: "claude", token: { action: "remove-override", control: "effort", value: null, tool: "claude" } });

    expect(outcome.exitCode).toBe(3);
    expect(fs.existsSync(tokenFile)).toBe(false);
  });

  it("writes no token for a dry run", async () => {
    const { bridge } = install("token");
    const outcome = await bridge.action({ action: "set", control: "posture", value: "full-auto", dryRun: true, token: { action: "set", control: "posture", value: "full-auto", tool: null } });
    expect((outcome.doc as unknown as { seen: unknown }).seen).toBeNull();
  });

  it("records an editor write as one JSON argument and fails when the command refuses it", async () => {
    const ok = install("record");
    await ok.bridge.recordEditorWrite({ write: "w", previous: { present: false }, new: true, profile: "Default" });
    const argv = launched.at(-1)?.args ?? [];
    expect(argv.slice(1, 3)).toEqual(["settings", "record-editor-write"]);
    expect(JSON.parse(argv[3] ?? "")).toEqual({ write: "w", previous: { present: false }, new: true, profile: "Default" });

    const bad = install("record-fail");
    const error = (await bad.bridge.recordEditorWrite({ write: "w", previous: { present: false }, new: true }).catch((e: unknown) => e)) as BridgeError;
    expect(error.kind).toBe("exit");
    expect(error.message).toContain("bad payload");
  });
});
