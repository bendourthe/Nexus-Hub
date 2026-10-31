/**
 * Live check: install the packaged .vsix into an ISOLATED VS Code (scratch --user-data-dir and
 * --extensions-dir, scratch home, fake tool versions), start it, and compare the panel's view
 * model with `nexus-hub settings show --json` from the same scratch home. Never touches the real
 * VS Code profile, ~/.claude, ~/.codex, ~/.copilot, or ~/.nexus-hub.
 *
 *   node scripts/live-check.js --vsix <path> --work <scratch dir> [--python <absolute path>] [--vscode <install dir>]
 *
 * Windows only for now: it locates Code.exe and its cli.js, and runs the CLI with ELECTRON_RUN_AS_NODE
 * exactly as `code.cmd` does, so no .cmd shim and no console window is involved.
 */
const { execFile } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const REPO = path.resolve(__dirname, "..", "..", "..");
const EXT_ID = "nexus-hub.nexus-hub-settings";

function arg(name) {
  const at = process.argv.indexOf(`--${name}`);
  return at >= 0 ? process.argv[at + 1] : undefined;
}

function run(command, args, options) {
  return new Promise((resolve) => {
    execFile(command, args, { windowsHide: true, shell: false, maxBuffer: 16 * 1024 * 1024, encoding: "utf8", ...options }, (error, stdout, stderr) => {
      resolve({ code: error ? (typeof error.code === "number" ? error.code : -1) : 0, killed: !!(error && error.killed), stdout: String(stdout), stderr: String(stderr) });
    });
  });
}

function findVsCode(explicit) {
  const roots = [explicit, path.join(process.env.LOCALAPPDATA || "", "Programs", "Microsoft VS Code"), path.join(process.env.ProgramFiles || "", "Microsoft VS Code")].filter(Boolean);
  for (const root of roots) {
    const exe = path.join(root, "Code.exe");
    if (!fs.existsSync(exe)) {
      continue;
    }
    const candidates = [root, ...fs.readdirSync(root).map((name) => path.join(root, name))];
    for (const dir of candidates) {
      const cli = path.join(dir, "resources", "app", "out", "cli.js");
      if (fs.existsSync(cli)) {
        return { exe, cli };
      }
    }
  }
  throw new Error("VS Code not found: pass --vscode <install dir containing Code.exe>");
}

function fakeTool(bin, name, output) {
  fs.writeFileSync(path.join(bin, `${name}.cmd`), `@echo off\r\necho ${output}\r\n`);
}

function prepare(work, python) {
  const home = path.join(work, "home");
  const bin = path.join(work, "bin");
  const scripts = path.join(home, ".nexus-hub", "scripts");
  const ws = path.join(work, "workspace");
  for (const dir of [home, bin, scripts, ws, path.join(home, ".claude"), path.join(home, ".codex")]) {
    fs.mkdirSync(dir, { recursive: true });
  }
  for (const name of ["nexus_hub_cli.py", "nexus_process.py"]) {
    fs.copyFileSync(path.join(REPO, "scripts", name), path.join(scripts, name));
  }
  fs.cpSync(path.join(REPO, "scripts", "lib"), path.join(scripts, "lib"), {
    recursive: true,
    filter: (source) => !/(__pycache__|[\\/]integrations$|[\\/]installer$)/.test(source),
  });
  fakeTool(bin, "claude", "2.1.283 (Claude Code)");
  fakeTool(bin, "codex", "codex-cli 0.136.0");
  fs.writeFileSync(path.join(home, ".claude", "settings.json"), '{\n  "model": "opus",\n  "env": { "CLAUDE_CODE_EFFORT_LEVEL": "high" },\n  "permissions": { "allow": ["Bash(git status)"] }\n}\n');
  fs.writeFileSync(path.join(home, ".codex", "config.toml"), '# scratch codex file\nmodel = "gpt-6-astra"\nmodel_reasoning_effort = "medium"\n');
  const system = path.join(process.env.SystemRoot || "C:\\Windows", "System32");
  const base = Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^(CLAUDE|ANTHROPIC|CODEX|COPILOT|NEXUS|AI_AGENT|GITHUB_COPILOT|ELECTRON_RUN_AS_NODE|VSCODE)/i.test(k)));
  const env = { ...base, HOME: home, USERPROFILE: home, NEXUS_HUB_HOME: path.join(home, ".nexus-hub"), PATH: `${bin};${system}`, Path: `${bin};${system}` };
  const devExt = path.join(work, "dev-ext");
  fs.mkdirSync(devExt, { recursive: true });
  fs.writeFileSync(path.join(devExt, "package.json"), JSON.stringify({ name: "live-host", version: "0.0.0", publisher: "nexus-hub", engines: { vscode: "^1.85.0" } }));
  return { home, ws, env, devExt, python };
}

async function installAndList(code, vsix, dirs, env) {
  const cliEnv = { ...env, ELECTRON_RUN_AS_NODE: "1" };
  const common = [code.cli, `--user-data-dir=${dirs.ud}`, `--extensions-dir=${dirs.ext}`];
  const installed = await run(code.exe, [...common, "--install-extension", vsix, "--force"], { env: cliEnv, timeout: 180000 });
  const listed = await run(code.exe, [...common, "--list-extensions", "--show-versions"], { env: cliEnv, timeout: 60000 });
  return { installed, listed };
}

async function hostRun(code, dirs, ctx, label, trusted) {
  const out = path.join(dirs.work, `live-${label}.json`);
  fs.rmSync(out, { force: true });
  const userSettings = path.join(dirs.ud, "User", "settings.json");
  const args = [
    `--user-data-dir=${dirs.ud}`, `--extensions-dir=${dirs.ext}`, `--extensionDevelopmentPath=${ctx.devExt}`,
    `--extensionTestsPath=${path.join(__dirname, "live-runner.js")}`, "--disable-gpu", "--disable-updates", "--disable-telemetry",
    "--skip-welcome", "--skip-release-notes", "--no-sandbox", ...(trusted ? ["--disable-workspace-trust"] : []), ctx.ws,
  ];
  const done = await run(code.exe, args, { env: { ...ctx.env, NEXUS_LIVE_OUT: out, NEXUS_LIVE_USER_SETTINGS: userSettings }, timeout: 150000 });
  return { done, out };
}

async function main() {
  const vsix = arg("vsix");
  const work = arg("work");
  if (!vsix || !work) {
    throw new Error("usage: node scripts/live-check.js --vsix <path> --work <scratch dir> [--python <abs path>] [--vscode <dir>]");
  }
  fs.rmSync(work, { recursive: true, force: true });
  fs.mkdirSync(work, { recursive: true });
  const code = findVsCode(arg("vscode"));
  const ctx = prepare(work, arg("python"));
  const dirs = { work, ud: path.join(work, "user-data"), ext: path.join(work, "extensions") };
  const report = { work, steps: {} };

  const install = await installAndList(code, path.resolve(vsix), dirs, ctx.env);
  report.steps.install = { code: install.installed.code, listed: install.listed.stdout.trim().split(/\r?\n/).filter((l) => l.includes("nexus-hub")) };

  const python = ctx.python || arg("python");
  report.steps.cli = null;
  if (python) {
    const cli = await run(python, ["-B", "-X", "utf8", path.join(ctx.home, ".nexus-hub", "scripts", "nexus_hub_cli.py"), "settings", "show", "--json", `--project=${ctx.ws}`], { env: ctx.env, timeout: 60000 });
    report.steps.cli = { code: cli.code };
    report.cliShow = cli.code === 0 ? JSON.parse(cli.stdout) : null;
  }

  for (const [label, trusted] of [["trusted", true], ["untrusted", false]]) {
    const hosted = await hostRun(code, dirs, ctx, label, trusted);
    report.steps[label] = { code: hosted.done.code, killed: hosted.done.killed, stderr: hosted.done.stderr.slice(0, 400) };
    report[label] = fs.existsSync(hosted.out) ? JSON.parse(fs.readFileSync(hosted.out, "utf8")) : null;
  }
  fs.writeFileSync(path.join(work, "live-report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ work, install: report.steps.install, trusted: report.steps.trusted, untrusted: report.steps.untrusted, report: path.join(work, "live-report.json") }));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
