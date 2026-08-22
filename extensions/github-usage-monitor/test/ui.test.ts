import { describe, expect, it, vi } from "vitest";
import { DashboardPanel, renderDashboard } from "../src/dashboardPanel";
import { buildUsageSuggestion, classifyUrgency, crossedUnnotifiedThreshold, pickTriggerMetric } from "../src/recommendations";
import { settingsSectionHtml, validateThresholds, type SettingsValues } from "../src/settingsPanel";
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
    expect(buildStatusText(snapshot(), false, false)).toBe("$(github-icon)\u2002GitHub Usage: 80% (actions minutes)");
    // Compact drops the "GitHub Usage: " label but keeps the metric name: the point
    // of compact is to save width, not to make the number ambiguous between three
    // metrics that can each occupy this slot.
    expect(buildStatusText(snapshot(), true, true)).toBe("$(github-icon)\u200280% (actions minutes) $(warning)");
    expect(buildStatusText(undefined, false, false)).toContain("--");
  });
  it("renders all sections, purple bars, costs, owner, source, freshness, and absolute unknown limits", () => {
    const hover = buildHoverMarkdown({ state: "fresh", data: snapshot() }, now).value;
    expect(hover).toContain("Copilot"); expect(hover).toContain("Actions minutes"); expect(hover).toContain("Actions storage");
    expect(decodeURIComponent(hover)).toContain(GITHUB_BAR_FILL); expect(hover).toContain("Allowance not established"); expect(hover).not.toContain("gigabyte-hours (%)");
    expect(hover).toContain("fixture-&lt;org&gt;"); expect(hover).toContain("Source: api - Fresh");
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
  it("uses semantic meters, theme tokens, escaped detail, and the absolute treatment", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain('role="meter"'); expect(html).toContain(GITHUB_BAR_FILL); expect(html).toContain("var(--vscode-editor-background)");
    expect(html).toContain("linux &amp; standard"); expect(html).not.toContain("fixture-<org>"); expect(html).toContain("Absolute usage; no percentage available");
    expect(html).toContain("default-src 'none'"); expect(html).toContain("focus-visible"); expect(html).toContain("prefers-reduced-motion");
  });

  it("renders exactly three action-row controls, in order", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    const row = html.slice(html.indexOf('<div class="actions">'));
    const buttons = [...row.matchAll(/<button[^>]*>/gu)].slice(0, 3).map((match) => match[0]);
    expect(buttons).toHaveLength(3);
    // Refresh Now is primary (no .secondary), the billing page is secondary, and
    // the gear is the icon button. The order is asserted because the row's shape is
    // the maintainer-facing part of this phase.
    expect(buttons[0]).toContain('data-command="refresh"');
    expect(buttons[0]).not.toContain("secondary");
    expect(buttons[1]).toContain('data-command="openBillingPage"');
    expect(buttons[1]).toContain("secondary");
    expect(buttons[2]).toContain("icon-btn");
    expect(buttons[2]).toContain('aria-expanded="false"');
    expect(html).toContain("Refresh Now");
    expect(html).toContain("Open GitHub Billing Page");
  });

  it("embeds the settings section hidden, with the controls the panel still offers", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain('<section id="settings-section" hidden');
    // v3.16.4 cut the Account group down to a name plus Connect and Log out, and
    // removed the allowance override (allowances are derived now). The token,
    // diagnose, and native-settings commands stay REGISTERED and reachable from the
    // Command Palette; they simply no longer occupy space in the panel.
    for (const command of ["logIn", "logOut"]) {
      expect(html).toContain(`data-command="${command}"`);
    }
    // Refresh, Allowance, and Danger zone were removed from the panel in v3.16.4.
    // Their settings keep working and Clear Data stays in the Command Palette.
    expect(html).not.toContain("Danger zone");
  });

  it("runs the settings script under the dashboard's single nonce, not a second block", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain("function toggleSettings()");
    // One script element only. A second inline block would need its own nonce and
    // would change the Content-Security-Policy shape.
    expect([...html.matchAll(/<script/gu)]).toHaveLength(1);
    // acquireVsCodeApi throws if called twice, so the settings script must reuse
    // the dashboard's handle rather than acquiring its own.
    expect([...html.matchAll(/acquireVsCodeApi\(\)/gu)]).toHaveLength(1);
  });

  it("styles the meter as a neutral track with a teal fill and a label beside it", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain("rgba(128,128,128,0.2)");
    expect(html).toContain(`background:${GITHUB_BAR_FILL};border-radius:4px`);
    expect(html).toContain('<span class="bar-pct">80%</span>');
    // The width transition must not animate for a user who asked for reduced motion.
    expect(html).toContain("prefers-reduced-motion:reduce){.bar-fill{transition:none}}");
  });

  it("keeps the accessible meter attributes through the restyle", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    expect(html).toContain('role="meter"');
    expect(html).toContain('aria-valuenow="80"');
    expect(html).toContain('aria-label="Actions minutes usage"');
  });

  it("renders no meter for a null-percentage metric, keeping the bordered treatment", () => {
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now);
    // Two metrics have a percentage, one does not; so exactly two meters.
    expect([...html.matchAll(/role="meter"/gu)]).toHaveLength(2);
    expect(html).toContain('class="absolute"');
  });
  it("renders actionable empty and stale states", () => {
    expect(renderDashboard({ state: "empty", error: { code: "invalid-token", message: "invalid" } })).toContain("No billing data available");
    expect(renderDashboard({ state: "stale", data: snapshot(), error: { code: "network-error", message: "offline" } })).toContain("Showing last-known-good data");
  });
  it("validates ordered thresholds and never renders a token field", () => {
    expect(validateThresholds({ moderate: 50, high: 75, critical: 95 })).toBeNull();
    expect(validateThresholds({ moderate: 75, high: 50, critical: 95 })).toContain("increase");
    expect(validateThresholds({ moderate: 0, high: 75, critical: 95 })).toContain("1 to 100");
    const values: SettingsValues = { billingScope: "organization", billingOwner: "fixture-<org>", copilotMetric: "ai-credits", copilotAllowance: null, actionsMinutesAllowance: 1000, actionsStorageAllowance: null, refreshInterval: 10, compactStatusBar: false, alertMetric: "highest", moderate: 50, high: 75, critical: 95, moderateColor: "#cca700", highColor: "#f0643c", criticalColor: "#e05555" };
    const html = settingsSectionHtml(values);
    // The owner name no longer appears here: the Account group moved out of Settings
    // to the panel header on 2026-08-11, so that "who am I" and "change who I am"
    // are one control rather than two places. Escaping is still asserted, on the
    // header that now renders it.
    expect(html).not.toContain("fixture-&lt;org&gt;"); expect(html).not.toContain('type="password"');
    expect(renderDashboard({ state: "fresh", data: snapshot() }, now, { binding: { accountLabel: "octo<cat>", scopes: [], fingerprint: "f" }, capability: { status: "unknown" }, hasStoredToken: false })).toContain("octo&lt;cat&gt;");
    // The token and native-settings buttons were removed from the panel in v3.16.4;
    // their commands remain registered and reachable from the Command Palette.
    expect(html).not.toContain("Set token");
  });
  it("puts every account control in the header, and none in Settings", () => {
    // Moved 2026-08-11. "Who am I" and "change who I am" answer the same question,
    // and splitting them across a header and a collapsed pane meant the control was
    // hidden behind a gear while the answer was not.
    const auth = { binding: { accountLabel: "benjamin-dourthe", scopes: [], fingerprint: "f" }, capability: { status: "unknown" as const }, hasStoredToken: false };
    const html = renderDashboard({ state: "fresh", data: snapshot() }, now, auth);

    // Both identities named, each with its own label - not "name (scope)".
    expect(html).toContain("benjamin-dourthe");
    expect(html).toContain("Organization");
    expect(html).toContain("fixture-&lt;org&gt;");
    // Switch and Log out live in the header.
    expect(html).toContain('class="acct-btn" data-command="logIn"');
    expect(html).toContain('class="acct-btn" data-command="logOut"');
    // And the word the REST API uses is gone from the panel chrome.
    expect(html).not.toContain("Owner:");
  });

  it("offers Log in, not Switch, when nothing is bound", () => {
    const html = renderDashboard({ state: "empty" }, now);

    expect(html).toContain('data-command="logIn"');
    expect(html).not.toContain('data-command="logOut"');
  });

  it("names the user and the organization separately in the hover", () => {
    // "Owner: SupiraMedical (organization)" reads as "the person who owns this",
    // which is the wrong idea when the signed-in user and the billed organization
    // are different identities - the normal case for a work account.
    const hover = buildHoverMarkdown({ state: "fresh", data: snapshot() }, now, "benjamin-dourthe").value;

    expect(hover).toContain("User: benjamin-dourthe");
    expect(hover).toContain("Organization: fixture-&lt;org&gt;");
    expect(hover).not.toContain("Owner:");
  });

  it("omits the user line when no account label is known", () => {
    const hover = buildHoverMarkdown({ state: "fresh", data: snapshot() }, now).value;

    expect(hover).not.toContain("User:");
    expect(hover).toContain("Organization: fixture-&lt;org&gt;");
  });

  it("calls a personal billing owner personal, not 'user'", () => {
    const personal: UsageSnapshot = { ...snapshot(), owner: { scope: "user", name: "benjamin-dourthe" } };
    const hover = buildHoverMarkdown({ state: "fresh", data: personal }, now, "benjamin-dourthe").value;

    expect(hover).toContain("Personal account: benjamin-dourthe");
  });

  it("creates exactly ONE webview and reuses it", () => {
    // The second panel is gone. v3.16.3 Phase 4 folded settings into this document,
    // so any additional createWebviewPanel call is a regression.
    resetVscodeStub();
    const dashboard = new DashboardPanel();
    dashboard.show({ state: "fresh", data: snapshot() });
    dashboard.show({ state: "empty" });
    expect(webviewPanels).toHaveLength(1);
    expect(webviewPanels[0]?.revealed).toBe(true);
    expect(webviewPanels[0]?.webview.html).toContain("No billing data");
    // The settings section travels with the dashboard, including on an empty state,
    // so the gear is never a control that does nothing.
    expect(webviewPanels[0]?.webview.html).toContain('id="settings-section"');
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
});
