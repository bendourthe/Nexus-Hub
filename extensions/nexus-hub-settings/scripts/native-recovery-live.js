/** Exercise provider-owned recovery in a disposable VS Code host, with no user credentials or prompts. */
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { execFile } = require("node:child_process");
const assert = require("node:assert/strict");
const EXT = path.resolve(__dirname, "..");
const waitFor = async (read, description) => {
  const deadline = Date.now() + 30000;
  while (!read()) {
    if (Date.now() >= deadline) { throw new Error("Timed out: " + description); }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
};

exports.run = async () => {
  const vscode = require("vscode");
  const report = { extensionHostPid: process.pid };
  const output = path.join(process.env.NEXUS_RECOVERY_WORK, "receipt.json");
  let sentinel;
  try {
    await vscode.extensions.getExtension("nexus-hub.nexus-hub-settings").activate();
    await vscode.extensions.getExtension("openai.chatgpt").activate();
    await vscode.extensions.getExtension("anthropic.claude-code").activate();
    const recovery = require(path.join(EXT, "out/nativeRecovery.js"));
    const effort = require(path.join(EXT, "out/nativeEffort.js"));
    const key = Symbol.for(recovery.RECOVERY_KEY);
    await waitFor(() => globalThis[key]?.codex?.initialized, "native Codex initialization");
    await vscode.commands.executeCommand("chatgpt.newCodexPanel");
    await waitFor(() => globalThis[key]?.codexView?.editorPanels?.size, "native Codex tab");
    await waitFor(() => [...globalThis[key].codexView.editorPanels.values()].some(panel => panel.ready), "Codex tab ready");
    const state = globalThis[key], connection = state.codex;
    const panels = [...state.codexView.editorPanels.keys()];
    const before = connection.proc.pid;
    sentinel = execFile(process.execPath, ["-e", "setInterval(()=>{},1000)"], { env: { ...process.env, ELECTRON_RUN_AS_NODE: "1" }, windowsHide: true, shell: false });
    const sentinelPid = sentinel.pid;
    await recovery.restartNativeProvider("codex");
    const after = connection.proc.pid;
    assert.notEqual(after, before); assert.equal(connection.initialized, true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    assert.equal(connection.proc.pid, after); assert.equal(connection.initialized, true);
    assert(panels.every(panel => state.codexView.editorPanels.has(panel)), "A Codex tab was replaced");
    process.kill(sentinelPid, 0);
    report.codex = { before, after, initialized: connection.initialized, tabsPreserved: panels.length, unrelatedProcessStillRunning: sentinelPid };
    await effort.applyNativeEffort("codex", "high", "native-effort-live-high");
    await new Promise(resolve => setTimeout(resolve, 1000));
    assert.equal(connection.proc.pid, after); assert(panels.every(panel => state.codexView.editorPanels.has(panel)));
    report.codex.effortBroadcastPreservedTabAndBackend = true;
    await vscode.commands.executeCommand("claude-vscode.editor.open");
    await waitFor(() => globalThis[key]?.claude?.size, "native Claude session owner");
    const comms = [...state.claude].map(reference => reference.deref()).filter(Boolean);
    const active = comms.reduce((sum, comm) => sum + comm.channels.size, 0);
    const claude = await recovery.restartNativeProvider("claude");
    assert.equal(claude.sessions, active);
    assert.equal(connection.proc.pid, after); process.kill(sentinelPid, 0);
    report.claude = { registeredOwners: comms.length, sessions: claude.sessions, codexPidUnchanged: after };
    // Exercise the real extension's native flag setter with a controlled channel boundary, without credentials or prompts.
    const comm = comms[0]; assert(comm);
    const channelId = "nexus-effort-integration-channel", flags = {};
    comm.channels.set(channelId, {query: {async applyFlagSettings(settings) {Object.assign(flags, settings);}, async getSettings() {return {applied: {effort: flags.effortLevel, ultracode: flags.ultracode}, effective: {}, sources: []};}}});
    try {
      await vscode.commands.executeCommand("nexusHubSettings.setEffort", "high");
      await waitFor(() => flags.effortLevel === "high", "hover High reaching Claude's native setter");
      await vscode.commands.executeCommand("nexusHubSettings.setEffort", "low");
      await waitFor(() => flags.effortLevel === "low", "hover Low reaching Claude's native setter");
      report.claude.nativeSetterBoundary = {highThenLow: true, controlledChannel: true, realHoverCommand: true};
    } finally {comm.channels.delete(channelId);}
    report.ok = true;
  } catch (error) {
    report.ok = false; report.error = String(error); throw error;
  } finally {
    if (sentinel) { sentinel.kill(); }
    fs.writeFileSync(output, JSON.stringify(report, null, 2));
  }
};

async function main() {
  const work = process.argv[2];
  assert(work && path.isAbsolute(work) && !fs.existsSync(work), "Pass a new absolute scratch path");
  fs.mkdirSync(work, {recursive: true});
  const extensions = path.join(work, "extensions"), home = path.join(work, "home"), hub = path.join(home, ".nexus-hub");
  fs.mkdirSync(extensions); fs.mkdirSync(path.join(hub, "scripts"), {recursive: true});
  const source = path.join(os.homedir(), ".vscode/extensions");
  const installer = require(path.join(EXT, "out/vendorUiInstall.js"));
  for (const [vendor, prefix] of [["codex", "openai.chatgpt-"], ["claude", "anthropic.claude-code-"]]) {
    const dirs = fs.readdirSync(source).filter(name => name.startsWith(prefix)).sort();
    const name = dirs.at(-1); assert(name, prefix + " is not installed");
    const target = path.join(extensions, name);
    fs.cpSync(path.join(source, name), target, {recursive: true});
    await installer.installProviderRecovery(vendor, target, path.join(hub, "native-ui"));
    await installer.installPortableEffort(vendor, target, path.join(hub, "native-ui"));
  }
  const repo = path.resolve(EXT, "../..");
  for (const name of ["nexus_hub_cli.py", "nexus_process.py"]) { fs.copyFileSync(path.join(repo, "scripts", name), path.join(hub, "scripts", name)); }
  fs.cpSync(path.join(repo, "scripts/lib"), path.join(hub, "scripts/lib"), {recursive: true, filter: name => !name.includes("__pycache__")});
  fs.writeFileSync(path.join(hub, "VERSION"), "4.15.1\n");
  const settings = path.join(work, "user-data/User"); fs.mkdirSync(settings, {recursive: true});
  fs.writeFileSync(path.join(settings, "settings.json"), JSON.stringify({"security.workspace.trust.enabled": false, "chatgpt.openOnStartup": false}));
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !/^(NEXUS|CLAUDE|ANTHROPIC|CODEX|OPENAI|COPILOT|VSCODE|ELECTRON|AI_AGENT)/i.test(key)));
  Object.assign(env, {HOME: home, USERPROFILE: home, NEXUS_HUB_HOME: hub, NEXUS_RECOVERY_WORK: work, CODEX_HOME: path.join(home, ".codex"), CLAUDE_CONFIG_DIR: path.join(home, ".claude")});
  const executable = path.join(process.env.LOCALAPPDATA, "Programs/Microsoft VS Code/Code.exe");
  const args = [`--user-data-dir=${path.join(work, "user-data")}`, `--extensions-dir=${extensions}`, `--extensionDevelopmentPath=${EXT}`, `--extensionTestsPath=${__filename}`, "--disable-workspace-trust", "--skip-welcome", "--skip-release-notes", "--disable-updates", "--disable-telemetry", work];
  const child = execFile(executable, args, {env, windowsHide: true, shell: false, maxBuffer: 16 * 1024 * 1024});
  const log = fs.createWriteStream(path.join(work, "host.log")); child.stdout.pipe(log); child.stderr.pipe(log);
  const timer = setTimeout(() => child.kill(), 150000);
  const code = await new Promise(resolve => { child.on("error", () => resolve(-1)); child.on("exit", resolve); }); clearTimeout(timer);
  const report = JSON.parse(fs.readFileSync(path.join(work, "receipt.json"), "utf8"));
  console.log(JSON.stringify({code, work, report})); assert.equal(code, 0); assert.equal(report.ok, true);
}
if (require.main === module) { main().catch(error => { console.error(error); process.exitCode = 1; }); }
