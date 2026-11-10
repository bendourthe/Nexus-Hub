import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as vscode from "vscode";
import { WarningViewProvider, WARNING_ACTIVE_CONTEXT } from "../src/warningView";

describe("warning expiry", () => {
  const savedHome = process.env.NEXUS_HUB_HOME;
  let home: string;
  beforeEach(() => { vi.useFakeTimers(); home = fs.mkdtempSync(path.join(os.tmpdir(), "usage-alerts-")); process.env.NEXUS_HUB_HOME = home; });
  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
    fs.rmSync(home, {recursive: true, force: true});
    if (savedHome === undefined) { delete process.env.NEXUS_HUB_HOME; } else { process.env.NEXUS_HUB_HOME = savedHome; }
  });

  const suggestion = {
    percent: 75, label: "Usage", message: "Usage at 75%",
    resetsIn: "Resets in 1h", resetLabel: "Resets in 1h",
    effortAdvice: "Batch requests", advice: "Batch requests",
    recommendation: "Batch requests", severity: "high", key: "cursorModels",
    meter: { used: 75, limit: 100, percentUsed: 75 }, bucket: 75,
  } as never;

  function setup() {
    const command = vi.spyOn(vscode.commands, "executeCommand");
    const provider = new WarningViewProvider(vscode.Uri.file("extension"));
    const callbacks = { onOpenDashboard: vi.fn(), onDismiss: vi.fn(), onOpenAttribution: vi.fn() };
    const show = () => provider.show(suggestion, callbacks);
    return { provider, command, callbacks, show };
  }

  it("keeps the alert for 9 seconds and dismisses it after ten seconds", async () => {
    const { command, show } = setup();
    await show();
    command.mockClear();
    await vi.advanceTimersByTimeAsync(9_999);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
    await vi.advanceTimersByTimeAsync(1);
    expect(command).toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
  });

  it("gives a replacement alert its own full ten seconds", async () => {
    const { command, show } = setup();
    await show();
    await vi.advanceTimersByTimeAsync(5_000);
    await show();
    command.mockClear();
    await vi.advanceTimersByTimeAsync(5_000);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
    await vi.advanceTimersByTimeAsync(5_000);
    expect(command).toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
  });

  it("cancels expiry when the user dismisses the alert", async () => {
    const { provider, command, show } = setup();
    let receive: (message: { command: string }) => void = () => {};
    provider.resolveWebviewView({
      webview: { html: "", options: {}, cspSource: "local:",
        asWebviewUri: (uri: vscode.Uri) => uri,
        onDidReceiveMessage: (handler: typeof receive) => { receive = handler; } },
      onDidDispose: () => {}, show: () => {},
    } as never);
    await show();
    receive({ command: "dismiss" });
    await Promise.resolve();
    command.mockClear();
    await vi.advanceTimersByTimeAsync(10_000);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
  });
  it("suppresses only disabled warning panels and permits re-enabling", async () => {
    const {command, show} = setup();
    fs.writeFileSync(path.join(home, "usage-alerts.json"), JSON.stringify({cursor: false}));
    await show(); expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, true);
    fs.writeFileSync(path.join(home, "usage-alerts.json"), JSON.stringify({cursor: true}));
    await show(); expect(command).toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, true);
  });
  it("closes a visible warning when shared preferences disable it", async () => {
    vi.useRealTimers();
    const {provider, command, show} = setup(); const subscription = provider.watchAlerts();
    await show(); command.mockClear();
    // fs.watchFile takes its first baseline asynchronously, so a write that lands before it is not a change.
    // Rewrite with a new value on each retry until a later poll observes one.
    let attempt = 0;
    try { await vi.waitFor(() => { fs.writeFileSync(path.join(home, "usage-alerts.json"), JSON.stringify({cursor: false, attempt: attempt++})); expect(command).toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false); }, {timeout: 4000, interval: 250}); }
    finally { subscription.dispose(); vi.useFakeTimers(); }
  });

});
