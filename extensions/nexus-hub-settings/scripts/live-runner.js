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
  // A user can click the effort hover only after its initial settings model is rendered.
  const deadline = Date.now() + 30000;
  while (!(await api.getViewModel()).controls.length) {
    if (Date.now() >= deadline) { throw Error("The effort hover did not become ready"); }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  const preferenceFile = path.join(process.env.USERPROFILE, ".nexus-hub", "preferences.json");
  const before = fs.existsSync(preferenceFile) ? fs.readFileSync(preferenceFile, "utf8") : null;
  // Windows URI and filesystem paths can load the same module with different drive-letter casing.
  const prototypes = [...new Set(Object.values(require.cache).filter(entry => entry.filename.toLowerCase() === path.join(ext.extensionPath, "out", "statusBar.js").toLowerCase()).map(entry => entry.exports.SettingsStatusBar.prototype))];
  const previews = [], originals = prototypes.map(prototype => ({prototype, preview: prototype.previewEffort}));
  for (const {prototype, preview} of originals) {
    prototype.previewEffort = function(value) {
      preview.call(this, value);
      if (value) { previews.push({value, text: this.item.text, tooltip: this.item.tooltip.value, beforeSave: (fs.existsSync(preferenceFile) ? fs.readFileSync(preferenceFile, "utf8") : null) === before}); }
    };
  }
  try { await vscode.commands.executeCommand(status.SET_EFFORT_COMMAND, "medium"); }
  finally { for (const {prototype, preview} of originals) {prototype.previewEffort = preview;} }
  if (vscode.workspace.isTrusted) {
    fs.writeFileSync(out + ".preview.json", JSON.stringify(previews));
    assert.equal(previews[0]?.beforeSave, true);
    assert(previews[0].text.includes("(medium)")); assert(previews[0].tooltip.includes("Medium (saving...)"));
    result.steps.immediateEffortPreview = {beforeSave: true, selected: previews[0].value};
    const afterEffort = await api.getViewModel();
    const effortRows = afterEffort.controls.find(control => control.id === "effort").rows;
    for (const tool of ["internal", "claude", "codex"]) {
      const row = effortRows.find(row => row.tool === tool);
      assert.equal(row.value, "medium", `${tool} effort was not saved`);
      assert.equal(row.matchesDefault, true, `${tool} effort did not match the default`);
    }
    result.steps.effortReadback = effortRows.filter(row => ["internal", "claude", "codex"].includes(row.tool)).map(row => ({tool: row.tool, value: row.value, matchesDefault: row.matchesDefault, state: row.state}));
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
    const native = require(path.join(ext.extensionPath, "out", "editorEffort.js"));
    const envKey = "claudeCode.environmentVariables";
    const config = vscode.workspace.getConfiguration();
    const previousEnv = config.inspect(envKey).globalValue;
    await config.update(envKey, [{ name: "CLAUDE_CODE_EFFORT_LEVEL", value: "low" }, { name: "NEXUS_SMOKE_KEEP", value: "unchanged" }], vscode.ConfigurationTarget.Global);
    const backups = [];
    const synchronized = await native.syncEditorEffort([{ control: "effort", tool: "claude", mapped_effort: "max" }], async (key, value) => { backups.push({ key, value }); });
    assert.deepEqual(config.inspect(envKey).globalValue, [{ name: "CLAUDE_CODE_EFFORT_LEVEL", value: "max" }, { name: "NEXUS_SMOKE_KEEP", value: "unchanged" }]);
    assert.equal(backups.length, 1);
    assert.equal(synchronized.issues.length, 0);
    result.steps.nativeEditorEffort = { mapped: "max", unrelatedPreserved: true, backups: backups.length };
    await config.update(envKey, previousEnv, vscode.ConfigurationTarget.Global);
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
