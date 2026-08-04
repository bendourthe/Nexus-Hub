import { afterEach, describe, expect, it } from "vitest";
import { DashboardPanel, renderDashboard } from "../src/dashboardPanel";
import { buildUsageSuggestion } from "../src/recommendations";
import {
  buildHoverMarkdown,
  buildStatusText,
  StatusBarManager
} from "../src/statusBarManager";
import {
  METER_FILL_COLOR,
  type FreshUsageSnapshot,
  type ProviderError,
  type UsageState
} from "../src/types";
import {
  renderWarning,
  WarningViewProvider
} from "../src/warningView";
import {
  createWebviewView,
  executedCommands,
  resetVscodeStub,
  statusItems,
  Uri,
  webviewPanels
} from "./vscode-stub";

const now = Date.parse("2026-08-04T18:00:00Z");
const error: ProviderError = {
  code: "network-error",
  message: "offline <retry>",
  sourceAttempt: "html-scrape",
  recoverable: true
};

function snapshot(): FreshUsageSnapshot {
  return {
    source: "manual",
    period: {
      startsAt: "2026-08-01T00:00:00Z",
      resetsAt: "2026-09-01T00:00:00Z"
    },
    cursorModels: {
      used: { value: 80, unit: "requests" },
      limit: { value: 100, unit: "requests" },
      percentUsed: 80,
      percentOrigin: "calculated"
    },
    otherModels: {
      used: { value: 2500, unit: "tokens" },
      limit: null,
      percentUsed: null,
      percentOrigin: null
    },
    onDemand: {
      enabled: true,
      personalSpend: { amount: 14.25, currency: "USD" }
    },
    teamContext: {
      sharedSpendLimit: { amount: 500, currency: "USD" },
      dynamicSpendLimit: true
    },
    fetchedAt: "2026-08-04T17:58:00Z",
    stale: false,
    staleReason: null
  };
}

function fresh(): UsageState {
  return { state: "fresh", data: snapshot() };
}

afterEach(() => resetVscodeStub());

describe("status bar and hover", () => {
  it("renders separate full and compact meters without inventing percentages", () => {
    expect(buildStatusText(fresh(), false)).toBe(
      "$(cursor-icon)\u2002Cursor Usage: Cursor 80% \u00b7 Other 2,500 tokens"
    );
    expect(buildStatusText(fresh(), true)).toBe(
      "$(cursor-icon)\u2002C 80% \u00b7 O 2,500 tokens"
    );
    expect(buildStatusText({ state: "empty", error }, false)).toContain("--");
  });

  it("shows personal meters, on-demand, shared context, source, and escaped errors", () => {
    const hover = buildHoverMarkdown(fresh(), now).value;
    expect(hover).toContain("Cursor Models");
    expect(hover).toContain("Other Models");
    expect(hover).toContain("Allowance unavailable; absolute usage only");
    expect(hover).toContain("Personal spend $14.25");
    expect(hover).toContain("Shared team context");
    expect(hover).toContain("not a personal allowance");
    expect(hover).toContain(METER_FILL_COLOR);

    const empty = buildHoverMarkdown({ state: "empty", error }, now).value;
    expect(empty).toContain("offline &lt;retry&gt;");
  });

  it("separates source percentages from absolute usage when no limit is reported", () => {
    const data = snapshot();
    data.cursorModels = {
      used: { value: 80, unit: "requests" },
      limit: null,
      percentUsed: 80,
      percentOrigin: "source"
    };
    const state: UsageState = { state: "fresh", data };
    const hover = buildHoverMarkdown(state, now).value;
    const dashboard = renderDashboard(state, now, "nonce");
    const suggestion = buildUsageSuggestion(state, "cursorModels");
    if (suggestion === null) {
      throw new Error("expected threshold suggestion");
    }
    const warning = renderWarning(suggestion, "local", "'self'", "nonce");

    for (const output of [hover, dashboard, warning]) {
      expect(output).toContain("80%");
      expect(output).toContain("80 requests");
      expect(output).not.toContain("of Not reported");
    }
    expect(hover).toContain("Absolute usage: 80 requests");
    expect(warning).toContain("Absolute usage: 80 requests");
  });

  it("drives the native status item lifecycle", () => {
    const manager = new StatusBarManager("cursor-usage.dashboard");
    expect(statusItems[0]?.priority).toBe(102);
    manager.showLoading();
    expect(statusItems[0]?.text).toContain("sync~spin");
    manager.show(fresh());
    expect(statusItems[0]).toMatchObject({
      shown: true,
      command: "cursor-usage.dashboard",
      name: "Cursor Usage Monitor"
    });
    manager.hide();
    expect(statusItems[0]?.shown).toBe(false);
    manager.dispose();
  });
});

describe("dashboard", () => {
  it("renders accessible fixed-color and absolute-only personal meters", () => {
    const html = renderDashboard(fresh(), now, "test-nonce");
    expect(html).toContain("Cursor Models");
    expect(html).toContain("Other Models");
    expect(html).toContain('role="meter"');
    expect(html).toContain("Allowance unavailable - absolute usage only");
    expect(html).toContain("Personal on-demand");
    expect(html).toContain("Shared team context");
    expect(html).toContain("not a personal allowance");
    expect(html).toContain(METER_FILL_COLOR);
    expect(html).toContain("@media(forced-colors:active)");
    expect(html).toContain("@media(prefers-reduced-motion:reduce)");
    expect(html).toContain(":focus-visible");
  });

  it("uses nonce-only local CSP and event listeners", () => {
    const html = renderDashboard(fresh(), now, "strict-nonce");
    expect(html).toContain(
      "style-src 'nonce-strict-nonce'; script-src 'nonce-strict-nonce'"
    );
    expect(html).not.toContain("'unsafe-inline'");
    expect(html).not.toContain("onclick=");
    expect(html).not.toContain("style=");
    expect(html).toContain("addEventListener");
  });

  it("escapes empty and stale errors", () => {
    expect(
      renderDashboard({ state: "empty", error }, now, "nonce")
    ).toContain("offline &lt;retry&gt;");
    const stale: UsageState = {
      state: "stale",
      data: {
        ...snapshot(),
        stale: true,
        staleReason: "fetch-failed"
      },
      error
    };
    const html = renderDashboard(stale, now, "nonce");
    expect(html).toContain("Stale usage snapshot");
    expect(html).toContain("not used for alerts");
  });

  it("reuses one panel and forwards only known commands", async () => {
    const dashboard = new DashboardPanel();
    dashboard.show(fresh());
    dashboard.show({ state: "empty", error });
    expect(webviewPanels).toHaveLength(1);
    expect(webviewPanels[0]?.revealed).toBe(true);
    await webviewPanels[0]?.webview.dispatch({ command: "refresh" });
    await webviewPanels[0]?.webview.dispatch({ command: "unknown" });
    expect(executedCommands).toEqual([
      { command: "cursor-usage.refresh", args: [] }
    ]);
    dashboard.dispose();
  });
});

describe("warning view", () => {
  it("renders explicit severity, the native logo, attribution, and local CSP", () => {
    const suggestion = buildUsageSuggestion(fresh(), "highest");
    if (suggestion === null) {
      throw new Error("expected threshold suggestion");
    }
    const html = renderWarning(
      suggestion,
      "vscode-webview:/icons/cursor-ai-48.png",
      "vscode-webview:",
      "warning-nonce"
    );
    expect(html).toContain("High usage warning");
    expect(html).toContain("&#9650;");
    expect(html).toContain('width="48" height="48"');
    expect(html).toContain("Icon");
    expect(html).toContain("Icons8");
    expect(html).toContain("data-command=\"attribution\"");
    expect(html).toContain(
      'href="https://icons8.com/icon/DiGZkjCzyZXn/cursor-ai"'
    );
    expect(html).toContain("img-src vscode-webview:");
    expect(html).not.toContain("img-src https:");
    expect(html).not.toContain("'unsafe-inline'");
    expect(html).not.toContain("onclick=");
    expect(html).toContain("@media(forced-colors:active)");
  });

  it("resolves local resources and dispatches warning actions", async () => {
    const suggestion = buildUsageSuggestion(fresh(), "highest");
    if (suggestion === null) {
      throw new Error("expected threshold suggestion");
    }
    let dashboardOpened = 0;
    let dismissed = 0;
    let attributionOpened = 0;
    const provider = new WarningViewProvider(Uri.file("extension"));
    const view = createWebviewView();
    provider.resolveWebviewView(view as never);
    await provider.show(suggestion, {
      onOpenDashboard: () => {
        dashboardOpened += 1;
      },
      onDismiss: () => {
        dismissed += 1;
      },
      onOpenAttribution: () => {
        attributionOpened += 1;
      }
    });
    expect(view.webview.html).toContain(
      "extension/icons/cursor-ai-48.png"
    );
    await view.webview.dispatch({ command: "dashboard" });
    await view.webview.dispatch({ command: "attribution" });
    await view.webview.dispatch({ command: "dismiss" });
    expect({ dashboardOpened, dismissed, attributionOpened }).toEqual({
      dashboardOpened: 1,
      dismissed: 1,
      attributionOpened: 1
    });
    expect(executedCommands).toEqual(
      expect.arrayContaining([
        {
          command: "setContext",
          args: ["cursorUsage.warningActive", true]
        },
        {
          command: "setContext",
          args: ["cursorUsage.warningActive", false]
        }
      ])
    );
  });

  it("renders a safe empty warning view", () => {
    expect(renderWarning(undefined, "local", "'self'", "nonce")).toContain(
      "No active Cursor usage warning"
    );
  });
});
