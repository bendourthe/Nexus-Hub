/**
 * Runs INSIDE a real VS Code extension host (loaded through --extensionTestsPath by live-check.js).
 * It uses the INSTALLED extension (from the .vsix), asks it for the panel's view model, opens the
 * view, and exercises the editor-write module against the real configuration API in the scratch
 * user-data directory. Results go to the file named by NEXUS_LIVE_OUT.
 */
const fs = require("node:fs");
const path = require("node:path");

exports.run = async function run() {
  const vscode = require("vscode");
  const out = process.env.NEXUS_LIVE_OUT;
  const result = { steps: {} };
  const ext = vscode.extensions.getExtension("nexus-hub.nexus-hub-settings");
  if (!ext) {
    throw new Error("nexus-hub.nexus-hub-settings is not installed in this host");
  }
  const api = await ext.activate();
  result.extensionPath = ext.extensionPath;
  result.version = ext.packageJSON.version;
  result.isTrusted = vscode.workspace.isTrusted;
  result.commands = (await vscode.commands.getCommands(true)).filter((c) => c.startsWith("nexusHubSettings."));

  result.model = await api.getViewModel();

  await vscode.commands.executeCommand("nexusHubSettings.open");
  result.steps.openedView = true;

  const assert = require("node:assert/strict");
  const status = require(path.join(ext.extensionPath, "out", "statusBar.js"));
  const readCompact = () => vscode.workspace.getConfiguration("nexusHubSettings").get("compactStatusBar", true);
  const compact = readCompact();
  await vscode.commands.executeCommand(status.COMPACT_COMMAND);
  assert.equal(readCompact(), !compact);
  await vscode.commands.executeCommand(status.COMPACT_COMMAND);
  assert.equal(readCompact(), compact);
  result.steps.compactToggle = true;
  const preferenceFile = path.join(process.env.USERPROFILE, ".nexus-hub", "preferences.json");
  const before = fs.existsSync(preferenceFile) ? fs.readFileSync(preferenceFile, "utf8") : null;
  await vscode.commands.executeCommand(status.SET_EFFORT_COMMAND, "medium");
  if (vscode.workspace.isTrusted) {
    assert.equal(JSON.parse(fs.readFileSync(preferenceFile, "utf8")).default_effort, "medium");
    const readback = await api.getViewModel();
    assert.equal(readback.preferences.effort, "medium");
    result.steps.hoverEffort = { saved: "medium", summary: status.summarize(readback, "nexusHubSettings.open").text };
  } else {
    assert.equal(fs.existsSync(preferenceFile) ? fs.readFileSync(preferenceFile, "utf8") : null, before);
    result.steps.hoverEffort = { readOnly: true, unchanged: true };
  }

  const editor = require(path.join(ext.extensionPath, "out", "editorWrites.js"));
  const key = "chat.tools.global.autoApprove";
  const missing = "claudeCode.initialPermissionMode";
  const layers = editor.inspectKey(key);
  result.steps.registered = { [key]: layers.registered, default: layers.defaultValue, [missing]: editor.inspectKey(missing).registered };
  const write = { tool: "vscode-copilot", write: "vscode-copilot.auto_approve", key, key_path: [key], value: true, weakens_safety: true, takes_effect: "next" };
  const pre = editor.precheckEditorWrites([write, { ...write, key: missing, key_path: [missing] }]);
  result.steps.precheck = { ok: pre.ok, apply: pre.ok ? pre.apply.map((w) => w.key) : [], skipped: pre.ok ? pre.skipped.map((s) => s.write.key) : [] };

  if (vscode.workspace.isTrusted) {
    const recorded = [];
    const applied = await editor.applyEditorWrites(pre.apply, async (w, previous) => void recorded.push({ key: w.key, previous }));
    const settingsFile = process.env.NEXUS_LIVE_USER_SETTINGS;
    result.steps.afterApply = { recorded, userSettings: JSON.parse(fs.readFileSync(settingsFile, "utf8")), value: editor.inspectKey(key).globalValue, applied: applied.length };
    const reports = await editor.restoreEditorWrites(
      [{ tool: "vscode-copilot", write: write.write, key, key_path: [key], restore: { present: false }, was: { present: true, value: true }, profile: null }],
      result.model.header.profile,
    );
    let settings = {};
    try {
      settings = JSON.parse(fs.readFileSync(settingsFile, "utf8"));
    } catch {
      settings = {};
    }
    result.steps.afterRestore = { reports, hasKey: Object.prototype.hasOwnProperty.call(settings, key), value: editor.inspectKey(key).globalValue };
  }

  fs.writeFileSync(out, JSON.stringify(result, null, 2));
};
