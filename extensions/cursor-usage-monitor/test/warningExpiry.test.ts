import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as vscode from "vscode";
import { WarningViewProvider, WARNING_ACTIVE_CONTEXT } from "../src/warningView";

describe("warning expiry", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
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

  it("keeps the alert for 59 seconds and dismisses it after one minute", async () => {
    const { command, show } = setup();
    await show();
    command.mockClear();
    await vi.advanceTimersByTimeAsync(59_999);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
    await vi.advanceTimersByTimeAsync(1);
    expect(command).toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
  });

  it("gives a replacement alert its own full minute", async () => {
    const { command, show } = setup();
    await show();
    await vi.advanceTimersByTimeAsync(30_000);
    await show();
    command.mockClear();
    await vi.advanceTimersByTimeAsync(30_000);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
    await vi.advanceTimersByTimeAsync(30_000);
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
    await vi.advanceTimersByTimeAsync(60_000);
    expect(command).not.toHaveBeenCalledWith("setContext", WARNING_ACTIVE_CONTEXT, false);
  });
});
