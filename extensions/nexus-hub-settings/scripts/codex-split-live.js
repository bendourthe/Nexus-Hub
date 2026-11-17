/** Run through --extensionTestsPath in an isolated profile with real Codex installed. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

exports.run = async function run() {
  const vscode = require("vscode");
  const provider = vscode.extensions.getExtension("openai.chatgpt");
  assert(provider, "The private profile must contain the real Codex extension");
  await provider.activate();
  const original = await vscode.workspace.openTextDocument({content: "Keep this editor visible while opening Codex beside it.", language: "plaintext"});
  const editor = await vscode.window.showTextDocument(original, {preview: false});
  const originalColumn = editor.viewColumn;
  const before = vscode.window.tabGroups.all.length;
  const {openCodexPanel} = require(path.join(process.env.NEXUS_SPLIT_SOURCE, "out", "extension.js"));
  const defaults = path.join(process.env.NEXUS_SPLIT_WORK, "session-defaults.json");
  fs.writeFileSync(defaults, JSON.stringify({codexTabs: true}));
  await openCodexPanel(defaults);
  const deadline = Date.now() + 30000;
  let group;
  do {
    group = vscode.window.tabGroups.all.find(g => g.viewColumn !== originalColumn && g.tabs.some(t => t.input instanceof vscode.TabInputCustom && t.input.viewType === "chatgpt.conversationEditor"));
    if (group) { break; }
    await new Promise(resolve => setTimeout(resolve, 100));
  } while (Date.now() < deadline);
  assert(group, "Codex did not open as a custom editor in a separate group");
  const retained = vscode.window.tabGroups.all.find(g => g.viewColumn === originalColumn)?.tabs.some(t => t.input instanceof vscode.TabInputText && t.input.uri.toString() === original.uri.toString());
  assert(retained, "The original editor was displaced");
  assert.equal(vscode.window.tabGroups.all.length, before + 1, "Exactly one new group should be created");
  const existingPanel = vscode.window.createWebviewPanel("nexusSplitOrigin", "Existing editor panel", vscode.ViewColumn.One, {});
  existingPanel.webview.html = "<p>Existing editor panel must stay visible.</p>";
  await openCodexPanel(defaults);
  const customTarget = vscode.window.tabGroups.all.find(g => g.viewColumn !== existingPanel.viewColumn && g.tabs.some(t => t.input instanceof vscode.TabInputCustom && t.input.viewType === "chatgpt.conversationEditor"));
  assert(customTarget && existingPanel.visible, "Opening from a webview must preserve it and show Codex beside it");
  const result = {webviewOrigin: {originalColumn: existingPanel.viewColumn, codexColumn: customTarget.viewColumn, originalVisible: existingPanel.visible}, provider: provider.packageJSON.version, beforeGroups: before, afterGroups: vscode.window.tabGroups.all.length,
    originalColumn, codexColumn: group.viewColumn, originalRetained: retained, customEditor: "chatgpt.conversationEditor"};
  fs.writeFileSync(path.join(process.env.NEXUS_SPLIT_WORK, "result.json"), JSON.stringify(result, null, 2));
};
