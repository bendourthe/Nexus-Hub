import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import { CliBridge, Interpreter } from "../src/cliBridge";
import { SettingsController } from "../src/controller";
import type { ShowReport } from "../src/types";
import { VSCODE_AUTO_APPROVE_WARNING, badgeFor } from "../src/viewModel";
import { layers } from "./fixtures";

/**
 * The panel against the REAL command line, in a scratch home with fake tool versions.
 * No mocks of the engine: the controller drives `nexus_hub_cli.py` and the scratch files change.
 * Needs a Python 3.11+ interpreter: set NEXUS_HUB_TEST_PYTHON to its absolute path, or install
 * Python in a standard location (the same search the panel itself uses). It fails, not skips, without one.
 */
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..", "..", "..");
const SCRUBBED = /^(CLAUDE|ANTHROPIC|CODEX|COPILOT|NEXUS|AI_AGENT|GITHUB_COPILOT)/i;

let root: string;
let home: string;
let project: string;
let env: NodeJS.ProcessEnv;
let interpreter: Interpreter;

function findPython(base: NodeJS.ProcessEnv): Interpreter {
  const forced = process.env.NEXUS_HUB_TEST_PYTHON;
  if (forced) {
    return { command: forced, args: ["-B", "-X", "utf8"] };
  }
  try {
    return new CliBridge({ env: base, home: os.homedir() }).interpreter();
  } catch {
    const names = process.platform === "win32" ? ["python.exe", "python3.exe"] : ["python3", "python"];
    for (const dir of (process.env.PATH ?? "").split(path.delimiter)) {
      for (const name of names) {
        const candidate = path.join(dir, name);
        if (dir && !/WindowsApps$/i.test(dir) && fs.existsSync(candidate)) {
          return { command: candidate, args: ["-B", "-X", "utf8"] };
        }
      }
    }
  }
  throw new Error("no Python interpreter for the agreement test: set NEXUS_HUB_TEST_PYTHON to an absolute python path");
}

function fakeTool(bin: string, name: string, output: string): void {
  if (process.platform === "win32") {
    fs.writeFileSync(path.join(bin, `${name}.cmd`), `@echo off\r\necho ${output}\r\n`);
  } else {
    fs.writeFileSync(path.join(bin, name), `#!/bin/sh\necho "${output}"\n`, { mode: 0o755 });
  }
}

function sha(file: string): string {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

beforeAll(() => {
  root = fs.mkdtempSync(path.join(os.tmpdir(), "nhs-agree-"));
  home = path.join(root, "home");
  project = path.join(root, "project");
  const bin = path.join(root, "bin");
  const scripts = path.join(home, ".nexus-hub", "scripts");
  for (const dir of [home, project, bin, scripts]) {
    fs.mkdirSync(dir, { recursive: true });
  }
  for (const name of ["nexus_hub_cli.py", "nexus_process.py"]) {
    fs.copyFileSync(path.join(repo, "scripts", name), path.join(scripts, name));
  }
  fs.cpSync(path.join(repo, "scripts", "lib"), path.join(scripts, "lib"), {
    recursive: true,
    filter: (source) => !/(__pycache__|[\\/]integrations$|[\\/]installer$)/.test(source),
  });
  fakeTool(bin, "claude", "2.1.283 (Claude Code)");
  fakeTool(bin, "codex", "codex-cli 0.136.0");
  const base = Object.fromEntries(Object.entries(process.env).filter(([key]) => !SCRUBBED.test(key)));
  const system = process.platform === "win32" ? path.join(process.env.SystemRoot ?? "C:\\Windows", "System32") : "/usr/bin:/bin";
  env = { ...base, HOME: home, USERPROFILE: home, PATH: `${bin}${path.delimiter}${system}`, Path: `${bin}${path.delimiter}${system}`, NEXUS_HUB_HOME: path.join(home, ".nexus-hub") };
  interpreter = findPython(process.env);
  fs.mkdirSync(path.join(home, ".claude"), { recursive: true });
  fs.mkdirSync(path.join(home, ".codex"), { recursive: true });
  fs.writeFileSync(
    path.join(home, ".claude", "settings.json"),
    '{\n  "model": "opus",\n  "env": { "CLAUDE_CODE_EFFORT_LEVEL": "high" },\n  "permissions": { "allow": ["Bash(git status)"] }\n}\n',
  );
  fs.writeFileSync(path.join(home, ".codex", "config.toml"), '# my codex file\nmodel = "gpt-6-astra"\nmodel_reasoning_effort = "medium"\n');
});

afterAll(() => {
  fs.rmSync(root, { recursive: true, force: true });
});

function build(extraEnv: NodeJS.ProcessEnv = {}, answer = true) {
  const bridge = new CliBridge({ home, env: { ...env, ...extraEnv }, interpreter, timeoutMs: 30_000 });
  const confirm = vi.fn(async () => answer);
  const controller = new SettingsController({
    bridge,
    ui: { confirm, openExternal: async () => true },
    inspect: (key) => layers(key, { registered: false }),
    isTrusted: () => true,
    project: () => project,
    profile: () => "Default",
    platform: "windows",
  });
  return { bridge, confirm, controller };
}

const claudeFile = (): string => path.join(home, ".claude", "settings.json");
const record = (): string => path.join(home, ".nexus-hub", "settings-control.json");

describe("the panel agrees with `nexus-hub settings show --json`", () => {
  it("draws exactly the engine's records, one row each, with the same state, value, layer, and fix", async () => {
    const { bridge, controller } = build();
    const raw = await bridge.run(["settings", "show", "--json", `--project=${project}`]);
    expect(raw.exitCode).toBe(0);
    const cli = JSON.parse(raw.stdout) as ShowReport;

    const model = await controller.refresh(true);

    expect(model.status).toBe("ready");
    const rows = model.controls.flatMap((control) => control.rows.map((row) => ({ control: control.id, row })));
    expect(rows).toHaveLength(cli.records.length);
    for (const entry of cli.records) {
      const match = rows.find((r) => r.control === entry.control && r.row.tool === entry.tool && r.row.surface === entry.surface);
      expect(match, `${entry.control}/${entry.tool}/${entry.surface}`).toBeDefined();
      expect(match!.row.state).toBe(entry.state);
      expect(match!.row.badge).toEqual(badgeFor(entry.state, entry.detail, entry.layer));
      expect(match!.row.value).toBe(entry.value);
      expect(match!.row.fix).toBe(entry.fix);
      expect(match!.row.layerValue).toBe(entry.layer_value);
      expect(match!.row.removable !== null).toBe(entry.removable_override !== null);
    }
    expect(model.controls.map((c) => c.id)).toEqual(["effort", "model", "posture", "attribution", "git_guardrails"]);
    expect(model.outcome.rows.length).toBeGreaterThan(0);
  }, 90_000);
});

describe("changes made through the panel reach the real files and reverse exactly", () => {
  it("sets effort, removes the legacy override after confirmation, and resets to identical files", async () => {
    const { controller, confirm } = build();
    const before = { claude: sha(claudeFile()), codex: sha(path.join(home, ".codex", "config.toml")) };
    await controller.refresh(true);
    const state = () => controller.current().controls.find((c) => c.id === "effort")!.rows.find((r) => r.tool === "claude")!;
    expect(state().state).toBe("overridden-by");
    expect(state().removable).not.toBeNull();

    await controller.handle({ type: "set", control: "effort", value: "medium", tool: "claude" });
    const written = JSON.parse(fs.readFileSync(claudeFile(), "utf8")) as { effortLevel?: string; modelSettings?: Record<string, { effortLevel: string }>; permissions: { allow: string[] } };
    expect(written.effortLevel).toBe("medium");
    expect(Object.keys(written.modelSettings ?? {}).length).toBeGreaterThan(0);
    expect(written.permissions.allow).toEqual(["Bash(git status)"]);
    expect(state().state).toBe("overridden-by");
    expect(confirm).not.toHaveBeenCalled();

    const removed = await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" });
    expect(removed.notice).toMatchObject({ level: "info" });
    expect(confirm).toHaveBeenCalledTimes(1);
    expect(JSON.parse(fs.readFileSync(claudeFile(), "utf8")).env?.CLAUDE_CODE_EFFORT_LEVEL).toBeUndefined();
    expect(state()).toMatchObject({ state: "in-effect", value: "medium" });
    expect(fs.existsSync(path.join(home, ".nexus-hub", "settings-panel-token.json"))).toBe(false);

    await controller.handle({ type: "reset", control: "effort", tool: null });
    await controller.handle({ type: "reset", control: "effort", tool: null });

    expect(sha(claudeFile())).toBe(before.claude);
    expect(sha(path.join(home, ".codex", "config.toml"))).toBe(before.codex);
    expect(state().state).toBe("overridden-by");
  }, 120_000);

  it("asks before lowering a safety barrier, writes nothing when cancelled, and consumes the one-time token when confirmed", async () => {
    const start = sha(claudeFile());
    const cancelled = build({}, false);
    await cancelled.controller.refresh(true);
    const none = await cancelled.controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });
    expect(none.notice?.text).toBe("Cancelled. Nothing was written.");
    expect(sha(claudeFile())).toBe(start);
    const request = cancelled.confirm.mock.calls[0]![0] as { detail: string };
    expect(request.detail).toContain("permissions.defaultMode");
    expect(request.detail).toContain("Still prompts or blocks (Claude Code):");
    expect(request.detail).toContain(VSCODE_AUTO_APPROVE_WARNING);

    const confirmed = build({}, true);
    await confirmed.controller.refresh(true);
    await confirmed.controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });
    const after = JSON.parse(fs.readFileSync(claudeFile(), "utf8")) as { permissions: { defaultMode?: string } };
    expect(after.permissions.defaultMode).toBe("bypassPermissions");
    expect(fs.existsSync(path.join(home, ".nexus-hub", "settings-panel-token.json"))).toBe(false);

    await confirmed.controller.handle({ type: "reset", control: "posture", tool: null });
    expect(sha(claudeFile())).toBe(start);
  }, 120_000);

  it("is refused under an agent-session marker even after a person confirmed, and writes nothing", async () => {
    const start = sha(claudeFile());
    const { controller, confirm } = build({ CLAUDECODE: "1" });
    await controller.refresh(true);

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(model.notice).toMatchObject({ level: "error", text: expect.stringContaining("CLAUDECODE is set") });
    expect(confirm).toHaveBeenCalledTimes(1);
    expect(sha(claudeFile())).toBe(start);
    expect(fs.existsSync(path.join(home, ".nexus-hub", "settings-panel-token.json"))).toBe(false);
  }, 90_000);

  it("keeps the ownership record readable by the installers after a panel write", async () => {
    const { bridge, controller } = build();
    await controller.refresh(true);
    await controller.handle({ type: "set", control: "effort", value: "low", tool: "claude" });
    expect(fs.existsSync(record())).toBe(true);

    const owned = await bridge.run(["settings", "owned-keys", "--json", `--home=${home}`]);
    expect(owned.exitCode).toBe(0);
    expect(JSON.stringify(JSON.parse(owned.stdout))).toContain("effortLevel");

    await controller.handle({ type: "reset", control: "effort", tool: null });
  }, 90_000);

  it("records a VS Code write through the real command and returns its restore on reset", async () => {
    const { bridge, controller } = build();
    const payload = { write: "vscode-copilot.auto_approve", previous: { present: false }, new: true, profile: "Default" };
    const refused = await bridge.recordEditorWrite(payload).catch((e: unknown) => e as Error);
    // Not admitted in the shipped catalog (no manual proof yet), so the engine refuses to record it.
    expect(refused).toBeInstanceOf(Error);
    expect((refused as Error).message).toContain("not settable");
    await controller.refresh(true);
    expect(controller.current().controls.find((c) => c.id === "posture")!.rows.find((r) => r.tool === "vscode-copilot")!.state).toBe("not-settable");
  }, 90_000);
});
