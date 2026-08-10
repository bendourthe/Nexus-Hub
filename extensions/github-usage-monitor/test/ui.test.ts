import { describe, expect, it, vi } from "vitest";
import { scheduleWarningDismissal } from "../src/extension";
import { DashboardPanel, renderDashboard } from "../src/dashboardPanel";
import { buildUsageSuggestion, classifyUrgency, crossedUnnotifiedThreshold, pickTriggerMetric } from "../src/recommendations";
import { renderSettings, SettingsPanel, validateThresholds, type SettingsValues } from "../src/settingsPanel";
import { buildHoverMarkdown, buildStatusText, GITHUB_BAR_FILL, StatusBarManager } from "../src/statusBarManager";
import type { UsageMetric, UsageSnapshot } from "../src/types";
import { renderWarning, WarningViewProvider } from "../src/warningView";
import { resetVscodeStub, statusItems, Uri, webviewPanels } from "./vscode-stub";

const now = Date.UTC(2026, 7, 15, 12);
function metric(kind: UsageMetric["kind"], unit: string, used: number, allowance: number | null): UsageMetric {
  return { kind, unit, used, allowance, drawdown: allowance === null ? null : used, drawdownBasis: allowance === null ? "unavailable" : "reported", allowanceSource: allowance === null ? "unknown" : "manual", allowanceState: allowance === null ? "unknown" : "verified", percentage: allowance === null ? null : used / allowance * 100, reset: { at: Date.UTC(2026, 8, 1), kind: "reporting-period", label: "month" }, breakdowns: [{ product: "Actions <runner>", sku: "linux & standard", unit, grossQuantity: used, discountQuantity: 2, netQuantity: used - 2, repositoryName: "fixture-repo", grossAmount: 4, discountAmount: 1, netAmount: 3 }], grossAmount: 4, discountAmount: 1, netAmount: 3 };
}
function snapshot(): UsageSnapshot {
  return { owner: { scope: "organization", name: "fixture-<org>" }, periodStart: Date.UTC(2026, 7, 1), periodEnd: Date.UTC(2026, 8, 1), fetchedAt: now - 120_000, source: "api", stale: false, copilot: metric("copilot-ai-credits", "ai-credits", 60, 100), actionsMinutes: metric("actions-minutes", "minutes", 800, 1000), actionsStorage: metric("actions-storage", "gigabyte-hours", 25, null) };
}

describe("status bar and hover", () => {
  it("uses the generated glyph, stable ordering, compact mode, and stale signal", () => {
    expect(buildStatusText(snapshot(), false, false)).toBe("$(github-icon)\u2002GitHub Usage: 80%");
    expect(buildStatusText(snapshot(), true, true)).toBe("$(github-icon)\u200280% $(warning)");
    expect(buildStatusText(undefined, false, false)).toContain("--");
  });
  it("renders all sections, purple bars, costs, owner, source, freshness, and absolute unknown limits", () => {
    const hover = buildHoverMarkdown({ state: "fresh", data: snapshot() }, now).value;
    expect(hover).toContain("Copilot"); expect(hover).toContain("Actions minutes"); expect(hover).toContain("Actions storage");
    expect(hover).toContain(GITHUB_BAR_FILL); expect(hover).toContain("Allowance not established"); expect(hover).not.toContain("gigabyte-hours (%)");
    expect(hover).toContain("fixture-&lt;org&gt;"); expect(hover).toContain("Source: api - Fresh"); expect(hover).toContain("net $3.00");
  });
  it("renders empty and stale-error states honestly", () => {
    expect(buildHoverMarkdown({ state: "empty", error: { code: "missing-token", message: "Set <token>" } }).value).toContain("Set &lt;token&gt;");
    const stale = snapshot(); stale.stale = true; stale.source = "cache";
    expect(buildHoverMarkdown({ state: "stale", data: stale, error: { code: "network-error", message: "offline" } }, now).value).toContain("Stale cache");
  });
  it("drives status item loading, display, and disposal", () => {
    resetVscodeStub(); const manager = new StatusBarManager("githubUsageMonitor.dashboard");
    manager.showLoading(); expect(statusItems[0]?.text).toContain("sync~spin");
    manager.show({ state: "fresh", data: snapshot() }); expect(statusItems[0]?.shown).toBe(true); expect(statusItems[0]?.command).toBe("githubUsageMonitor.dashboard");
    manager.dispose(); expect(statusItems[0]?.shown).toBe(false);
  });
});

describe("dashboard and settings", () => {
  it("uses semantic meters, theme tokens, escaped detail, controls, and absolute treatment", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain('role="meter"'); expect(html).toContain(GITHUB_BAR_FILL); expect(html).toContain("var(--vscode-editor-background)");
    expect(html).toContain("Actions &lt;runner&gt;"); expect(html).not.toContain("fixture-<org>"); expect(html).toContain("Absolute usage; no percentage available");
    for (const command of ["refresh", "manualEntry", "settings", "clearData"]) expect(html).toContain(`data-command="${command}"`);
    expect(html).toContain("default-src 'none'"); expect(html).toContain("focus-visible"); expect(html).toContain("prefers-reduced-motion");
  });
  it("renders actionable empty and stale states", () => {
    expect(renderDashboard({ state: "empty", error: { code: "invalid-token", message: "invalid" } })).toContain("No billing data available");
    expect(renderDashboard({ state: "stale", data: snapshot(), error: { code: "network-error", message: "offline" } })).toContain("Last-known-good data");
  });
  it("validates ordered thresholds and never renders a token field", () => {
    expect(validateThresholds({ moderate: 50, high: 75, critical: 95 })).toBeNull();
    expect(validateThresholds({ moderate: 75, high: 50, critical: 95 })).toContain("increase");
    expect(validateThresholds({ moderate: 0, high: 75, critical: 95 })).toContain("1 to 100");
    const values: SettingsValues = { billingScope: "organization", billingOwner: "fixture-<org>", copilotMetric: "ai-credits", copilotAllowance: null, actionsMinutesAllowance: 1000, actionsStorageAllowance: null, refreshInterval: 10, compactStatusBar: false, alertMetric: "highest", moderate: 50, high: 75, critical: 95, notificationTimeoutSeconds: 12, moderateColor: "#cca700", highColor: "#f0643c", criticalColor: "#e05555" };
    const html = renderSettings(values);
    expect(html).toContain("SecretStorage"); expect(html).toContain("fixture-&lt;org&gt;"); expect(html).not.toContain('type="password"');
    expect(html).toContain("Set token"); expect(html).toContain("Edit settings"); expect(html).toContain("focus-visible");
  });
  it("creates and reuses dashboard and settings panels", () => {
    resetVscodeStub(); const dashboard = new DashboardPanel(); dashboard.show({ state: "fresh", data: snapshot() }); dashboard.show({ state: "empty" });
    expect(webviewPanels).toHaveLength(1); expect(webviewPanels[0]?.revealed).toBe(true); expect(webviewPanels[0]?.webview.html).toContain("No billing data");
    const settings = new SettingsPanel(); settings.show(); settings.show(); expect(webviewPanels).toHaveLength(2); expect(webviewPanels[1]?.webview.html).toContain("GitHub Usage Monitor Settings");
  });
});

describe("recommendations and warning view", () => {
  it("selects the highest or configured valid metric and ignores unknown denominators", () => {
    expect(pickTriggerMetric(snapshot(), "highest")?.kind).toBe("actions-minutes");
    expect(pickTriggerMetric(snapshot(), "actions-storage")).toBeNull();
    expect(classifyUrgency(49)).toBe("low"); expect(classifyUrgency(75)).toBe("high"); expect(classifyUrgency(95)).toBe("critical");
  });
  it("builds one bucketed suggestion and deduplicates it", () => {
    const suggestion = buildUsageSuggestion(snapshot(), "highest");
    expect(suggestion).toMatchObject({ bucket: 75, urgency: "high", percent: 80 });
    expect(crossedUnnotifiedThreshold(suggestion, [])).toBe(true);
    expect(crossedUnnotifiedThreshold(suggestion, [75])).toBe(false);
  });
  it("renders branded, non-color-only warning content and actions without external loads", () => {
    const suggestion = buildUsageSuggestion(snapshot(), "highest")!;
    const html = renderWarning(suggestion, "vscode-resource:/github-gradient.png", now, "vscode-resource:");
    expect(html).toContain("GitHub"); expect(html).toContain("High usage"); expect(html).toContain("&#9650;");
    expect(html).toContain("Open dashboard"); expect(html).toContain("Dismiss"); expect(html).toContain("Free icon from Streamline");
    expect(html).toContain("default-src 'none'"); expect(html).not.toContain("img-src https:");
  });
  it("resolves, refreshes, and dismisses the warning provider", async () => {
    resetVscodeStub(); const provider = new WarningViewProvider(Uri.file("fixture"));
    const view = { webview: webviewPanels.length === 0 ? (await import("./vscode-stub")).window.createWebviewPanel().webview : webviewPanels[0]!.webview } as never;
    provider.resolveWebviewView(view); let dismissed = false;
    await provider.show(buildUsageSuggestion(snapshot(), "highest")!, { onOpenDashboard() {}, onDismiss() { dismissed = true; } });
    expect(webviewPanels[0]?.webview.html).toContain("High usage");
    await provider.dismiss(); expect(dismissed).toBe(true);
  });
  it("auto-dismisses after the configured timeout", () => {
    vi.useFakeTimers(); const dismiss = vi.fn(); scheduleWarningDismissal(3_000, dismiss);
    vi.advanceTimersByTime(2_999); expect(dismiss).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1); expect(dismiss).toHaveBeenCalledOnce(); vi.useRealTimers();
  });
});
