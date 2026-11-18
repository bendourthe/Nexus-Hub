/**
 * Live check for "Restore Claude Code and Codex split". Runs ordinary VS Code windows (not a test host, so
 * VS Code's real shutdown and window restore run) in an ISOLATED profile: scratch --user-data-dir,
 * --extensions-dir and home. It copies the real Claude Code and Codex extensions from a vendor directory
 * (read only), installs the packaged Settings .vsix, and adds a small probe extension that drives the layout.
 *
 *   node scripts/restore-split-live.js --vsix <path> --work <new scratch dir> [--vendor <extensions dir>] [--vscode <install dir>]
 *
 * Steps: (1) setup window opens Claude Code and Codex side by side, waits for Settings to remember the split,
 * turns the setting off, merges both tabs into one group, and quits. (2) The profile is copied. (3) Restore window
 * with the setting ON starts from the merged layout. (4) Control window with the setting OFF starts from the same
 * merged layout. Every window is started by this script and ended by its own PID. Writes live-restore-split.json.
 */
const cp = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const PROBE = String.raw`
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const work = process.env.PROBE_WORK, phase = process.env.PROBE_PHASE, t0 = Date.now();
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const classify = (input) => input instanceof vscode.TabInputWebview ? "claude" : input instanceof vscode.TabInputCustom ? "codex" : "other";
const snap = () => vscode.window.tabGroups.all.map((g) => ({ column: g.viewColumn, active: g.isActive, tabs: g.tabs.map((t) => classify(t.input)) }));
const log = (event) => fs.appendFileSync(path.join(work, "log-" + phase + ".jsonl"), JSON.stringify({ ms: Date.now() - t0, event, groups: snap() }) + "\n");
const until = async (test, ms) => { const end = Date.now() + ms; while (Date.now() < end) { if (test()) { return true; } await sleep(200); } return false; };
const both = () => { const kinds = snap().flatMap((g) => g.tabs); return kinds.includes("claude") && kinds.includes("codex"); };
exports.activate = async function () {
  log("probe-activated");
  vscode.window.tabGroups.onDidChangeTabs(() => log("tabs"));
  (async () => {
    try {
      const settings = vscode.extensions.getExtension("nexus-hub.nexus-hub-settings");
      await settings.activate();
      log("settings-active");
      if (phase === "setup") {
        await sleep(4000);
        await vscode.commands.executeCommand("claude-vscode.editor.open");
        await until(() => snap().some((g) => g.tabs.includes("claude")), 20000);
        await sleep(2000);
        await vscode.commands.executeCommand("vscode.openWith", vscode.Uri.parse("openai-codex://route/extension/panel/new"), "chatgpt.conversationEditor", { viewColumn: vscode.ViewColumn.Beside, preview: false });
        await until(() => snap().length === 2 && both(), 20000);
        log("split-built");
        await sleep(6000);
        await vscode.workspace.getConfiguration("nexusHubSettings").update("restoreAgentSplit", false, vscode.ConfigurationTarget.Global);
        await sleep(1000);
        await vscode.commands.executeCommand("workbench.action.moveEditorToPreviousGroup");
        await until(() => snap().length === 1, 10000);
        log("merged");
        await sleep(3000);
      } else {
        await until(() => both(), 30000);
        log("both-present");
        await sleep(Number(process.env.PROBE_WAIT_MS || 12000));
        log("final");
      }
    } catch (error) { log("error " + (error && error.stack || error)); }
    await vscode.commands.executeCommand("workbench.action.quit");
  })();
};
`;

function arg(name) { const at = process.argv.indexOf(`--${name}`); return at >= 0 ? process.argv[at + 1] : undefined; }
const run = (command, args, options) => new Promise((resolve) => cp.execFile(command, args, { windowsHide: true, shell: false, maxBuffer: 16 * 1024 * 1024, encoding: "utf8", ...options }, (error, stdout, stderr) => resolve({ code: error ? (typeof error.code === "number" ? error.code : -1) : 0, stdout: String(stdout), stderr: String(stderr) })));

function findVsCode(explicit) {
  for (const root of [explicit, path.join(process.env.LOCALAPPDATA || "", "Programs", "Microsoft VS Code"), path.join(process.env.ProgramFiles || "", "Microsoft VS Code")].filter(Boolean)) {
    const exe = path.join(root, "Code.exe");
    if (!fs.existsSync(exe)) { continue; }
    for (const dir of [root, ...fs.readdirSync(root).map((name) => path.join(root, name))]) {
      const cli = path.join(dir, "resources", "app", "out", "cli.js");
      if (fs.existsSync(cli)) { return { exe, cli }; }
    }
  }
  throw new Error("VS Code not found: pass --vscode <install dir containing Code.exe>");
}

const uri = (target) => ({ $mid: 1, path: "/" + target.split(path.sep).join("/"), scheme: "file" });

function buildProfile(work, vendor) {
  const ext = path.join(work, "extensions");
  const registry = JSON.parse(fs.readFileSync(path.join(vendor, "extensions.json"), "utf8")).filter((entry) => /^(anthropic\.claude-code|openai\.chatgpt)$/.test(entry.identifier.id));
  assert.equal(registry.length, 2, "The vendor directory must contain Claude Code and Codex");
  for (const entry of registry) {
    const destination = path.join(ext, entry.relativeLocation);
    fs.cpSync(path.join(vendor, entry.relativeLocation), destination, { recursive: true });
    entry.location = uri(destination);
  }
  const probe = path.join(ext, "probe.layout-probe-0.0.1");
  fs.mkdirSync(probe, { recursive: true });
  fs.writeFileSync(path.join(probe, "package.json"), JSON.stringify({ name: "layout-probe", version: "0.0.1", publisher: "probe", engines: { vscode: "^1.85.0" }, main: "extension.js", activationEvents: ["onStartupFinished"] }));
  fs.writeFileSync(path.join(probe, "extension.js"), PROBE);
  registry.push({ identifier: { id: "probe.layout-probe" }, version: "0.0.1", location: uri(probe), relativeLocation: "probe.layout-probe-0.0.1", metadata: { isApplicationScoped: false, isMachineScoped: false, isBuiltin: false, installedTimestamp: Date.now(), pinned: false, source: "vsix" } });
  fs.writeFileSync(path.join(ext, "extensions.json"), JSON.stringify(registry));
  const home = path.join(work, "home");
  for (const dir of [path.join(work, "workspace"), path.join(work, "user-data", "User"), path.join(home, ".claude"), path.join(home, ".codex")]) { fs.mkdirSync(dir, { recursive: true }); }
  return home;
}

function writeSettings(userData, enabled) {
  fs.writeFileSync(path.join(userData, "User", "settings.json"), JSON.stringify({
    "window.restoreWindows": "preserve", "files.hotExit": "onExitAndWindowClose", "claudeCode.preferredLocation": "panel", "claudeCode.disableLoginPrompt": true,
    "security.workspace.trust.enabled": false, "telemetry.telemetryLevel": "off", "update.mode": "none", "workbench.startupEditor": "none",
    "nexusHubSettings.restoreAgentSplit": enabled,
  }, null, 2));
}

function window(code, work, userData, home, phase, extra) {
  return new Promise((resolve) => {
    const base = Object.fromEntries(Object.entries(process.env).filter(([key]) => !/^(ELECTRON_RUN_AS_NODE|VSCODE|CLAUDE|ANTHROPIC|CODEX|COPILOT|NEXUS)/i.test(key)));
    const env = { ...base, HOME: home, USERPROFILE: home, NEXUS_HUB_HOME: path.join(home, ".nexus-hub"), PROBE_WORK: work, PROBE_PHASE: phase, ...extra };
    const args = [`--user-data-dir=${userData}`, `--extensions-dir=${path.join(work, "extensions")}`, "--disable-gpu", "--disable-updates", "--skip-welcome", "--skip-release-notes", "--no-sandbox", "--disable-workspace-trust", path.join(work, "workspace")];
    const child = cp.spawn(code.exe, args, { env, windowsHide: true, stdio: "ignore" });
    let killed = false;
    const timer = setTimeout(() => { killed = true; cp.spawnSync("taskkill", ["/T", "/F", "/PID", String(child.pid)], { windowsHide: true }); }, 150000);
    child.on("exit", (exitCode) => { clearTimeout(timer); resolve({ exitCode, killed }); });
  });
}

function readLog(work, phase) {
  const file = path.join(work, `log-${phase}.jsonl`);
  return fs.existsSync(file) ? fs.readFileSync(file, "utf8").trim().split("\n").map((line) => JSON.parse(line)) : [];
}
const last = (entries, event) => entries.filter((entry) => entry.event === event).at(-1)?.groups;
const shape = (groups) => (groups || []).map((group) => group.tabs.join("+"));

async function main() {
  const vsix = arg("vsix"), work = arg("work");
  if (!vsix || !work) { throw new Error("usage: node scripts/restore-split-live.js --vsix <path> --work <new scratch dir> [--vendor <dir>] [--vscode <dir>]"); }
  if (!path.isAbsolute(work) || fs.existsSync(work)) { throw new Error("--work must name a new absolute scratch directory"); }
  const vendor = arg("vendor") || path.join(process.env.USERPROFILE || "", ".vscode", "extensions");
  const code = findVsCode(arg("vscode"));
  fs.mkdirSync(work, { recursive: true });
  const home = buildProfile(work, vendor);
  const userData = path.join(work, "user-data");
  writeSettings(userData, true);
  const common = [code.cli, `--user-data-dir=${userData}`, `--extensions-dir=${path.join(work, "extensions")}`];
  const installed = await run(code.exe, [...common, "--install-extension", path.resolve(vsix), "--force"], { env: { ...process.env, ELECTRON_RUN_AS_NODE: "1", HOME: home, USERPROFILE: home }, timeout: 180000 });
  assert.equal(installed.code, 0, installed.stderr);

  const report = { work, steps: {} };
  report.steps.setup = await window(code, work, userData, home, "setup", {});
  const setup = readLog(work, "setup");
  report.setup = { split: shape(last(setup, "split-built")), merged: shape(last(setup, "merged")) };
  assert.deepEqual(report.setup.split, ["claude", "codex"], "setup did not build the split");
  assert.deepEqual(report.setup.merged, ["claude+codex"], "setup did not merge the tabs");

  const controlData = path.join(work, "user-data-control");
  fs.cpSync(userData, controlData, { recursive: true });
  writeSettings(userData, true);
  writeSettings(controlData, false);
  report.steps.restore = await window(code, work, userData, home, "restore", {});
  report.steps.control = await window(code, work, controlData, home, "control", {});
  const restore = readLog(work, "restore"), control = readLog(work, "control");
  report.restoreStart = shape(last(restore, "both-present"));
  report.restoreFinal = shape(last(restore, "final"));
  report.controlStart = shape(last(control, "both-present"));
  report.controlFinal = shape(last(control, "final"));
  fs.writeFileSync(path.join(work, "live-restore-split.json"), JSON.stringify(report, null, 2));
  for (const step of ["setup", "restore", "control"]) { assert.equal(report.steps[step].exitCode, 0, `${step} window exited ${report.steps[step].exitCode}`); assert.equal(report.steps[step].killed, false); }
  assert.deepEqual(report.controlFinal, ["claude+codex"], "With the setting off the merged layout must be left alone");
  assert.deepEqual(report.restoreFinal, ["claude", "codex"], "With the setting on the split must be restored");
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => { console.error(error.stack || error); process.exit(1); });
