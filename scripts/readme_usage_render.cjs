/* Render shipped monitor components with isolated sample data and a VS Code API stub. */
"use strict";
const fs = require("node:fs"), path = require("node:path"), Module = require("node:module");
const root = path.resolve(__dirname, ".."), ts = require(path.join(root, "extensions/nexus-hub-settings/node_modules/typescript"));
class MarkdownString {
  constructor(value = "") { this.value = value; }
  appendMarkdown(value) { this.value += value; return this; }
  appendText(value) { this.value += value; return this; }
}
const configuration = { get: (_key, fallback) => fallback, inspect: () => undefined, update: async () => {} };
const vscode = {
  MarkdownString, ThemeColor: class { constructor(id) { this.id = id; } },
  ColorThemeKind: { Light: 1, Dark: 2, HighContrast: 3 }, StatusBarAlignment: { Right: 2 },
  ConfigurationTarget: { Global: 1 },
  workspace: { getConfiguration: () => configuration },
  window: { activeColorTheme: { kind: 2 }, createStatusBarItem: () => ({ show() {}, dispose() {} }) },
};
const originalLoad = Module._load;
Module._load = function (name, ...rest) { return name === "vscode" ? vscode : originalLoad.call(this, name, ...rest); };
require.extensions[".ts"] = function (module, filename) {
  const source = fs.readFileSync(filename, "utf8");
  module._compile(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, filename);
};
const metric = (percent, resetsIn) => ({ percent, resetsIn, resetsAt: null });
const quota = { id: "premium_interactions", label: "Premium requests", percent: 24, entitlement: 300, remaining: 228 };
const samples = {
  claude: { session: metric(28, "2h 18m"), weeklyAllModels: metric(54, "3d 8h"), weeklyScoped: { ...metric(35, "3d 8h"), label: "Sonnet" }, currentModel: "claude-opus-5-5", lastUpdated: Date.now(), dataSource: "api", extraUsage: { isEnabled: false, monthlyLimit: 0, usedCredits: 0, utilization: 0 } },
  codex: { session: metric(16, "3h 12m"), weeklyAllModels: metric(46, "4d 6h"), currentModel: "gpt-6.1-sol", planLabel: "ChatGPT Pro", lastUpdated: Date.now(), dataSource: "api", resets: { available: 1 } },
  copilot: { personal: { planLabel: "Copilot Pro", quotas: [quota], primary: quota, creditsUsed: 72, resetsAt: null }, lastUpdated: Date.now(), dataSource: "api" },
};
async function main() {
  const { marked } = await import(require("node:url").pathToFileURL(path.join(root, "extensions/nexus-hub-settings/node_modules/marked/lib/marked.esm.js")).href);
  const result = {};
  for (const provider of Object.keys(samples)) {
    const folder = path.join(root, `extensions/${provider}-usage-monitor/src`), data = samples[provider];
    const { StatusBarManager } = require(path.join(folder, "statusBarManager.ts"));
    const store = { get: () => data, getWithFreshCountdowns: () => data, getTimeSinceUpdate: () => "just now" };
    const manager = new StatusBarManager(store, provider + ".dashboard");
    manager.refresh();
    const item = manager.statusBarItem;
    const tooltip = marked.parse(item.tooltip.value);
    const { DashboardPanel } = require(path.join(folder, "dashboardPanel.ts"));
    const dashboard = Object.assign(Object.create(DashboardPanel.prototype), { data, timeSince: "just now", fetchError: undefined, orgStatus: "not-connected", panel: { webview: { cspSource: "'self'" } } });
    let html = dashboard.getHtml();
    html = html.replace(/(<script nonce="[^"]+">)/, "$1window.acquireVsCodeApi=()=>({postMessage:()=>{}});");
    result[provider] = { text: item.text, tooltip, dashboard: html };
  }
  const input = JSON.parse(fs.readFileSync(0, "utf8"));
  const { summarize } = require(path.join(root, "extensions/nexus-hub-settings/src/statusBar.ts"));
  result.nexus = {};
  for (const effort of ["medium", "low"]) {
    input.model.controls[0].rows = [{ tool: "internal", state: "in-effect", value: effort, canSet: true }];
    const summary = summarize(input.model, "nexusHubSettings.open", true, false);
    result.nexus[effort] = { text: summary.text, tooltip: marked.parse(summary.tooltip) };
  }
  process.stdout.write(JSON.stringify(result));
}
main().catch(error => { process.stderr.write(error.stack + "\n"); process.exitCode = 1; });
