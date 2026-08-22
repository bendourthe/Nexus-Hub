import { describe, expect, it } from "vitest";
import { buildUsageSuggestion } from "../src/recommendations";
import type { UsageMetric, UsageSnapshot } from "../src/types";
import { WarningViewProvider } from "../src/warningView";
import { messages, resetVscodeStub, Uri, webviewPanels, window } from "./vscode-stub";

const now = Date.UTC(2026, 7, 15, 12);

function metric(kind: UsageMetric["kind"], unit: string, used: number, allowance: number | null): UsageMetric {
  return {
    kind, unit, used, allowance,
    drawdown: allowance === null ? null : used,
    drawdownBasis: allowance === null ? "unavailable" : "reported",
    allowanceSource: allowance === null ? "unknown" : "manual",
    allowanceState: allowance === null ? "unknown" : "verified",
    percentage: allowance === null ? null : (used / allowance) * 100,
    reset: { at: Date.UTC(2026, 8, 1), kind: "reporting-period", label: "month" },
    breakdowns: [], grossAmount: 4, discountAmount: 1, netAmount: 3
  };
}

function snapshot(): UsageSnapshot {
  return {
    owner: { scope: "organization", name: "fixture-<org>" },
    periodStart: Date.UTC(2026, 7, 1), periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: now - 120_000, source: "api", stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 60, 100),
    actionsMinutes: metric("actions-minutes", "minutes", 800, 1000),
    actionsStorage: metric("actions-storage", "gigabyte-hours", 25, null)
  };
}

/**
 * A `WebviewView` double that records `show` calls. The real view is registered
 * with `retainContextWhenHidden`, so a view the user dismissed is still resolved
 * on the next alert - which is exactly the state the reported defect occurred in.
 */
function fakeView(): { view: never; shown: boolean[] } {
  const shown: boolean[] = [];
  const created = window.createWebviewPanel();
  const view = {
    webview: created.webview,
    show(preserveFocus?: boolean) { shown.push(preserveFocus === true); }
  };
  return { view: view as never, shown };
}

describe("warning reveal", () => {
  it("reveals the panel on a repeat threshold crossing, not only the first", async () => {
    resetVscodeStub();
    const provider = new WarningViewProvider(Uri.file("fixture"));
    const { view, shown } = fakeView();
    provider.resolveWebviewView(view);
    const suggestion = buildUsageSuggestion(snapshot(), "highest")!;

    await provider.show(suggestion, { onOpenDashboard() {}, onDismiss() {} });
    expect(shown).toHaveLength(1);

    // The user dismisses; the retained view stays resolved from the host's side.
    provider.resolveWebviewView(view);
    await provider.show(suggestion, { onOpenDashboard() {}, onDismiss() {} });
    expect(shown).toHaveLength(2);
    expect(webviewPanels.at(-1)?.webview.html).toContain("High usage");
  });

  it("falls back to focusing the view id on a host without WebviewView.show", async () => {
    resetVscodeStub();
    const provider = new WarningViewProvider(Uri.file("fixture"));
    const created = window.createWebviewPanel();
    provider.resolveWebviewView({ webview: created.webview } as never);
    await expect(
      provider.show(buildUsageSuggestion(snapshot(), "highest")!, { onOpenDashboard() {}, onDismiss() {} })
    ).resolves.toBeUndefined();
  });

  it("raises no native toast from the warning surface", async () => {
    resetVscodeStub();
    const provider = new WarningViewProvider(Uri.file("fixture"));
    const { view } = fakeView();
    provider.resolveWebviewView(view);
    await provider.show(buildUsageSuggestion(snapshot(), "highest")!, { onOpenDashboard() {}, onDismiss() {} });
    expect(messages.warnings).toHaveLength(0);
  });

  it("clears the retained view reference on dismiss so a disposed view is not reused", async () => {
    resetVscodeStub();
    const provider = new WarningViewProvider(Uri.file("fixture"));
    const { view, shown } = fakeView();
    provider.resolveWebviewView(view);
    await provider.show(buildUsageSuggestion(snapshot(), "highest")!, { onOpenDashboard() {}, onDismiss() {} });
    await provider.dismiss();
    // With the reference cleared, the next show takes the focus-command branch
    // rather than calling show() on a view the host may already have disposed.
    await provider.show(buildUsageSuggestion(snapshot(), "highest")!, { onOpenDashboard() {}, onDismiss() {} });
    expect(shown).toHaveLength(1);
  });
});
