import { afterEach, describe, expect, it, vi } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import type { DraftState } from "../src/settingsPanel";
import { UNTRACKED_PERCENT, type UsageData } from "../src/types";
import {
  __resetStubState,
  createdWebviewPanels,
  type StubWebviewPanel,
} from "./vscode-stub";

function usageData(overrides: Partial<UsageData> = {}): UsageData {
  return {
    session: { percent: UNTRACKED_PERCENT, resetsIn: "N/A", resetsAt: null },
    weeklyAllModels: { percent: 10, resetsIn: "in 4 days", resetsAt: null },
    currentModel: "Codex",
    lastUpdated: Date.now(),
    dataSource: "api",
    planLabel: "ChatGPT Plus",
    ...overrides,
  };
}

function renderDashboard(data: UsageData): string {
  const renderable = Object.create(DashboardPanel.prototype) as {
    data: UsageData;
    timeSince: string;
    fetchError: undefined;
    getHtml(): string;
  };
  renderable.data = data;
  renderable.timeSince = "just now";
  renderable.fetchError = undefined;
  return renderable.getHtml();
}

describe("DashboardPanel", () => {
  afterEach(() => {
    for (const panel of createdWebviewPanels) {
      panel.dispose();
    }
    __resetStubState();
  });

  it("renders Extra Credits as a second progress bar after Weekly", () => {
    const html = renderDashboard(usageData({
      extraCredits: {
        usedCredits: 836.88,
        monthlyLimit: 5_000,
        percent: 17,
        resetsIn: "August 31, 2026 5:00 PM",
        resetsAt: Date.UTC(2026, 8, 1),
        usedAmountUsd: 33.4752,
        limitAmountUsd: 200,
      },
    }));

    expect(html).toContain("<h3>Weekly</h3>");
    expect(html).toContain("<h3>Extra Credits</h3>");
    expect(html).toContain('style="width: 17%;"');
    expect(html).toContain("837 out of 5,000 credits used ($33.48 / $200.00)");
    expect(html.indexOf("837 out of 5,000 credits used")).toBeLessThan(html.indexOf("Resets on August 31, 2026 5:00 PM"));
    expect(html).not.toContain("credits used &middot;");
    expect(html.indexOf("<h3>Weekly</h3>")).toBeLessThan(html.indexOf("<h3>Extra Credits</h3>"));
  });

  it("reuses the singleton panel and supports update, reveal, and action messages", async () => {
    const onRefresh = vi.fn();
    const onOpenUsagePage = vi.fn();
    const callbacks = { onRefresh, onOpenUsagePage };
    const instance = DashboardPanel.show(usageData(), "just now", undefined, callbacks);
    const panel = createdWebviewPanels[0] as StubWebviewPanel;

    expect(createdWebviewPanels).toHaveLength(1);
    expect(panel.webview.html).toContain("Codex Usage Dashboard");

    const reused = DashboardPanel.show(
      usageData({ creditsSummary: "Credits: 125 remaining", planLabel: "Team" }),
      "2 min ago",
      undefined,
      callbacks,
    );
    expect(reused).toBe(instance);
    expect(panel.revealCount).toBe(1);
    expect(panel.webview.html).toContain("Credits: 125 remaining");

    instance.update(usageData({ weeklyAllModels: { percent: 55, resetsIn: "2d", resetsAt: null } }), "3 min ago");
    expect(panel.webview.html).toContain('style="width: 55%;"');
    DashboardPanel.updateIfOpen(usageData({ planLabel: "Enterprise" }), "4 min ago", undefined);
    expect(panel.webview.html).toContain("Enterprise");

    DashboardPanel.revealSettings();
    await panel.webview.__dispatchMessage({ command: "refresh" });
    await panel.webview.__dispatchMessage({ command: "openUsagePage" });
    expect(panel.webview.postedMessages).toContainEqual({ command: "openSettings" });
    expect(panel.webview.postedMessages).toContainEqual({ command: "setLoading" });
    expect(onRefresh).toHaveBeenCalledOnce();
    expect(onOpenUsagePage).toHaveBeenCalledOnce();

    const draft: DraftState = {
      metric: "weekly",
      thresholds: { moderate: 40, high: 70, critical: 90 },
      colors: { moderate: "#112233", high: "#445566", critical: "none" },
      compact: true,
    };
    await panel.webview.__dispatchMessage({ command: "save", draft });
    await panel.webview.__dispatchMessage({ command: "reset" });
    expect(panel.webview.postedMessages.filter((message) =>
      (message as { command?: string }).command === "loadSettings"
    )).toHaveLength(2);
  });

  it("renders actionable and rate-limited empty states without alarming cached-data users", () => {
    const callbacks = { onRefresh: vi.fn(), onOpenUsagePage: vi.fn() };
    const instance = DashboardPanel.show(undefined, "never", { code: "rate-limited" }, callbacks);
    const panel = createdWebviewPanels[0];
    expect(panel.webview.html).toContain("The usage API is rate-limiting right now");
    expect(panel.webview.html).toContain("No Usage Data");

    instance.update(undefined, "never", { code: "api-error", statusCode: 503, statusText: "Unavailable" });
    expect(panel.webview.html).toContain('class="error-banner"');
    expect(panel.webview.html).toContain("503 Unavailable");

    instance.update(usageData(), "just now", { code: "rate-limited" });
    expect(panel.webview.html).not.toContain('<div class="error-banner">');
  });

  it("renders additional limits, escapes labels, and distinguishes manual data", () => {
    const html = renderDashboard(usageData({
      dataSource: "manual",
      planLabel: "Team <Admin>",
      additionalLimits: [{
        label: "Review & Work",
        percent: 25,
        resetsIn: "2h",
        resetsAt: Date.UTC(2026, 7, 3),
      }],
      creditsSummary: "Credits: unlimited",
    }));

    expect(html).toContain("Review &amp; Work");
    expect(html).toContain("Team &lt;Admin&gt;");
    expect(html).toContain("Credits: unlimited");
    expect(html).toContain("Manually entered just now");
    expect(html).toContain(`data-resets-at="${Date.UTC(2026, 7, 3)}"`);
  });
});
