import { afterEach, describe, expect, it, vi } from "vitest";
import { WarningViewProvider, WARNING_ACTIVE_CONTEXT, WARNING_VIEW_ID } from "../src/warningView";
import type { UsageSuggestion } from "../src/recommendations";
import { __resetStubState, executedCommands } from "./vscode-stub";

function fakeView() {
  let handler: ((m: { command: string }) => void) | undefined;
  let disposeHandler: (() => void) | undefined;
  const view = {
    shown: 0,
    webview: {
      html: "",
      options: {},
      cspSource: "vscode-resource:",
      onDidReceiveMessage(h: (m: { command: string }) => void) {
        handler = h;
      },
    },
    onDidDispose(h: () => void) {
      disposeHandler = h;
    },
    show() {
      view.shown += 1;
    },
    send: (command: string) => handler?.({ command }),
    dispose: () => disposeHandler?.(),
  };
  return view;
}

const suggestion: UsageSuggestion = {
  bucket: 95,
  message: "Organization pool at 99.25%.",
  percent: 99.2481,
  label: "Organization pool",
  resetLabel: "Resets on November 1",
  advice: "Pause non-essential Copilot work, or ask an owner about additional usage",
};

describe("WarningViewProvider", () => {
  afterEach(() => __resetStubState());

  it("uses Copilot ids and renders the ring, advice, reset, and logo", async () => {
    expect(WARNING_VIEW_ID).toBe("copilotUsageWarningView");
    expect(WARNING_ACTIVE_CONTEXT).toBe("copilotUsage.warningActive");
    const provider = new WarningViewProvider();
    const view = fakeView();
    provider.resolveWebviewView(view as never);
    expect(view.webview.html).toContain("No active usage warning.");

    const onOpenDashboard = vi.fn();
    await provider.show(suggestion, "critical", { onOpenDashboard });
    expect(executedCommands[0]).toEqual({ command: "setContext", args: [WARNING_ACTIVE_CONTEXT, true] });
    expect(view.shown).toBe(1);
    const html = view.webview.html;
    expect(html).toContain('<div class="ring-pct">99%</div>');
    expect(html).toContain("Organization pool");
    expect(html).toContain("Pause non-essential Copilot work, or ask an owner about additional usage");
    expect(html).toContain("Usage will reset on November 1.");
    expect(html).toContain('<div class="brand-name">Copilot</div>');
    expect(html).toContain("data:image/png;base64,");

    view.send("openDashboard");
    expect(onOpenDashboard).toHaveBeenCalledOnce();
    view.send("cancel");
    await Promise.resolve();
    expect(executedCommands.at(-1)).toEqual({ command: "setContext", args: [WARNING_ACTIVE_CONTEXT, false] });
  });

  it("focuses the view when it is not resolved yet, and keeps an unreported reset as is", async () => {
    const provider = new WarningViewProvider();
    await provider.show({ ...suggestion, resetLabel: "Reset date not reported" }, "high", { onOpenDashboard: () => {} });
    expect(executedCommands.at(-1)).toEqual({ command: `${WARNING_VIEW_ID}.focus`, args: [] });
    const view = fakeView();
    provider.resolveWebviewView(view as never);
    expect(view.webview.html).toContain("Reset date not reported.");
    view.dispose();
  });
});
