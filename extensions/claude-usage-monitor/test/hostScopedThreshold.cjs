const assert = require("node:assert/strict");
const path = require("node:path");
const vscode = require("vscode");

const fixture = {
  session: { percent: 12, resetsIn: "3h", resetsAt: null },
  weeklyAllModels: { percent: 34, resetsIn: "4d", resetsAt: null },
  weeklyScoped: { percent: 86, resetsIn: "2d", resetsAt: null, label: "Fable" },
  currentModel: "opus",
  lastUpdated: Date.now(),
};

exports.run = async function run() {
  const extension = vscode.extensions.getExtension("nexus-hub.claude-usage-monitor");
  assert.ok(extension, "Claude Usage Monitor is loaded");
  const config = vscode.workspace.getConfiguration("claudeUsage");
  await config.update("autoFetch", false, vscode.ConfigurationTarget.Global);
  await config.update("thresholdMetric", "weeklyScoped", vscode.ConfigurationTarget.Global);
  await extension.activate();

  const expectedEntry = path.join(extension.extensionPath, "out", "extension.js").toLowerCase();
  const runtimeEntry = Object.keys(require.cache).find(key => key.toLowerCase() === expectedEntry);
  assert.ok(runtimeEntry, "active extension module is in the host module cache");
  const fromExtension = modulePath => require(path.join(path.dirname(runtimeEntry), modulePath));
  const { ClaudeUsageProvider } = fromExtension("providers");
  const { WarningViewProvider } = fromExtension("warningView");
  const { StatusBarManager } = fromExtension("statusBarManager");
  const { getActiveUrgency, pickTriggerMetric } = fromExtension("recommendations");
  const { getThresholdMetric } = fromExtension("types");
  assert.equal(getThresholdMetric(), "weeklyScoped", "host reads the scoped setting");
  assert.equal(pickTriggerMetric(fixture).percent, 86, "host selects the scoped value");

  let fetched = fixture;
  let fetches = 0;
  const warnings = [];
  const originalFetch = ClaudeUsageProvider.prototype.fetchUsage;
  const originalShow = WarningViewProvider.prototype.show;
  ClaudeUsageProvider.prototype.fetchUsage = async () => {
    fetches++;
    return { success: true, data: fetched };
  };
  WarningViewProvider.prototype.show = async function (suggestion, urgency) {
    warnings.push({ suggestion, urgency });
    await originalShow.call(this, suggestion, urgency, {});
    for (let attempt = 0; attempt < 20 && !this.view; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    assert.ok(this.view, "warning view resolves in the extension host");
    assert.match(this.view.webview.html, /Weekly \(Fable\)/);
  };

  try {
    await vscode.commands.executeCommand("claude-usage.refresh");
    assert.equal(fetches, 1, "refresh uses the mocked provider");
    assert.equal(warnings.length, 1, "scoped high usage raises a warning");
    assert.equal(warnings[0].suggestion.label, "Weekly (Fable)");
    assert.equal(warnings[0].urgency, "high");

    const store = {
      getWithFreshCountdowns: () => fetched,
      getTimeSinceUpdate: () => "just now",
      hasResetExpired: () => false,
    };
    const status = new StatusBarManager(store, "claude-usage.dashboard");
    status.refresh();
    assert.match(status.statusBarItem.text, /12% \(current\) 34% \(week\)/);
    assert.ok(status.statusBarItem.backgroundColor, "scoped selection highlights the status bar");

    fetched = { ...fixture, session: { ...fixture.session, percent: 98 }, weeklyScoped: undefined };
    await vscode.commands.executeCommand("claude-usage.refresh");
    assert.equal(warnings.length, 1, "missing scoped metric raises no second warning");
    assert.equal(getActiveUrgency(fetched), "low");
    status.refresh();
    assert.equal(status.statusBarItem.backgroundColor, undefined);
    status.dispose();

    await config.update("thresholdMetric", "highest", vscode.ConfigurationTarget.Global);
    fetched = fixture;
    await vscode.commands.executeCommand("claude-usage.refresh");
    assert.equal(warnings.length, 1, "default highest still ignores the scoped bar");
    await config.update("thresholdMetric", "weeklyScoped", vscode.ConfigurationTarget.Global);
    await vscode.commands.executeCommand("claude-usage.refresh");
    assert.equal(warnings.length, 2, "switching back to scoped resets the notified bucket");
    console.log("HOST_SCOPED_THRESHOLD_PASS warnings=2 missing=quiet highest=unchanged switch=reset");
  } finally {
    ClaudeUsageProvider.prototype.fetchUsage = originalFetch;
    WarningViewProvider.prototype.show = originalShow;
  }
};
