import { afterEach, describe, expect, it } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import type { UsageData } from "../src/types";
import { __resetStubState, createdWebviewPanels } from "./vscode-stub";

/**
 * Renders the dashboard's weekly sections (v4.10.0 MT-2).
 *
 * The companion to `weeklyBarsRender.test.ts`. The changelog asserts the scoped
 * weekly bar appears "in both the status-bar hover tooltip and the dashboard",
 * and neither surface had ever been rendered by a test. `getHtml()` reads only
 * instance state, so driving the public `show()` against a captured webview is
 * enough to assert the real markup.
 */

const baseData: UsageData = {
  session: { percent: 12, resetsIn: "3h", resetsAt: null },
  weeklyAllModels: { percent: 34, resetsIn: "4d", resetsAt: null },
  currentModel: "opus" as UsageData["currentModel"],
  lastUpdated: Date.now(),
};

function renderDashboard(data: UsageData): string {
  __resetStubState();
  // `show()` caches a singleton across calls; clear it so each test renders fresh.
  (DashboardPanel as unknown as { currentPanel: unknown }).currentPanel = undefined;
  DashboardPanel.show(data, "just now", undefined, {} as never);
  return createdWebviewPanels[0].webview.html as string;
}

describe("dashboard weekly sections", () => {
  afterEach(() => {
    (DashboardPanel as unknown as { currentPanel: unknown }).currentPanel = undefined;
    __resetStubState();
  });

  it("renders a second weekly section labelled from the account", () => {
    const html = renderDashboard({
      ...baseData,
      weeklyScoped: { percent: 56, resetsIn: "4d", resetsAt: null, label: "Fable" },
    });
    expect(html).toContain("<h3>Weekly (All Models)</h3>");
    expect(html).toContain("<h3>Weekly (Fable)</h3>");
    // The all-models heading must survive alongside it, not be replaced.
    expect((html.match(/<h3>Weekly \(/g) ?? []).length).toBe(2);
  });

  it("omits the second weekly section when no scoped limit is reported", () => {
    const html = renderDashboard(baseData);
    expect(html).toContain("<h3>Weekly (All Models)</h3>");
    expect((html.match(/<h3>Weekly \(/g) ?? []).length).toBe(1);
  });

  it("escapes a server-provided label rather than injecting markup", () => {
    const html = renderDashboard({
      ...baseData,
      weeklyScoped: {
        percent: 1,
        resetsIn: "4d",
        resetsAt: null,
        label: '<img src=x onerror=alert(1)>',
      },
    });
    // The dashboard runs with enableScripts: true, so an unescaped label here
    // would be script execution, not just broken layout.
    expect(html).not.toContain("<img src=x onerror");
    expect(html).toContain("&lt;img src=x onerror");
  });
});
