/**
 * WN-2 (v4.13.7): the dashboard hardening first shipped in the Copilot monitor
 * (extensions/copilot-usage-monitor/test/review-regressions.test.ts), ported
 * here. F1: nonce Content-Security-Policy, delegated listeners instead of
 * inline handlers, validated and escaped setting values, and a validated
 * webview message payload. F6: application-scoped thresholds and colors, and a
 * clamped refresh interval.
 */
import * as fs from "fs";
import * as path from "path";
import { afterEach, describe, expect, it } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { jsonForScript, parseDraft, settingsSectionHtml } from "../src/settingsPanel";
import { StatusBarManager } from "../src/statusBarManager";
import { getColorConfig, getRefreshIntervalMinutes, getThresholdConfig, type UsageData } from "../src/types";
import { UsageStore } from "../src/usageStore";
import { __resetStubState, __setStubConfig, configurationUpdates, createdWebviewPanels } from "./vscode-stub";

const callbacks = { onRefresh() {}, onOpenUsagePage() {} };

function data(): UsageData {
  return {
    session: { percent: 21, resetsIn: "in 3 hours", resetsAt: null },
    weeklyAllModels: { percent: 4, resetsIn: "in 5 days", resetsAt: null },
    currentModel: "claude-opus-4-6[1m]",
    lastUpdated: Date.now(),
    dataSource: "api",
  } as UsageData;
}

function memento() {
  const values = new Map<string, unknown>();
  return {
    get: <T>(key: string, fallback?: T) => (values.has(key) ? (values.get(key) as T) : fallback),
    update: async (key: string, value: unknown) => {
      values.set(key, value);
    },
    keys: () => [...values.keys()],
  };
}

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
});

describe("F1: the dashboard webview cannot be scripted through settings", () => {
  function hostileDashboard(): string {
    __setStubConfig("claudeUsage", "thresholds.moderate", '50"><img src=x onerror=alert(1)>');
    __setStubConfig("claudeUsage", "colors.high", '#"><svg onload=alert(2)>');
    __setStubConfig("claudeUsage", "colors.critical", "</script><script>alert(3)</script>");
    DashboardPanel.show(data(), "now", undefined, callbacks);
    return createdWebviewPanels[0].webview.html;
  }

  it("renders no injected markup from hostile threshold and color settings", () => {
    const html = hostileDashboard();
    for (const injected of ["onerror=alert(1)", "onload=alert(2)", "<script>alert(3)", "alert("]) {
      expect(html.includes(injected), injected).toBe(false);
    }
  });

  it("serves a nonce Content-Security-Policy whose nonce matches the only script", () => {
    const html = hostileDashboard();
    const csp = html.match(/<meta http-equiv="Content-Security-Policy" content="([^"]+)">/);
    expect(csp).not.toBeNull();
    expect(csp![1]).toContain("default-src 'none'");
    const nonce = csp![1].match(/script-src 'nonce-([^']+)'/)![1];
    // Case-insensitive so <SCRIPT>, <Script> and friends cannot slip past the count.
    const scripts = [...html.matchAll(/<script\b([^>]*)>/gi)].map((m) => m[1]);
    expect(scripts).toEqual([` nonce="${nonce}"`]);
    // Exactly one closing tag in any case, spacing, or attribute variant (</SCRIPT >, </script foo>).
    expect([...html.matchAll(/<\/script\b[^>]*>/gi)]).toHaveLength(1);
  });

  it("contains no inline event handler attributes, with data or without", () => {
    expect(hostileDashboard()).not.toMatch(/\son[a-z]+\s*=/i);
    DashboardPanel.updateIfOpen(undefined, "never", { code: "token-invalid", statusCode: 401 });
    expect(createdWebviewPanels[0].webview.html).not.toMatch(/\son[a-z]+\s*=/i);
  });

  it("validates thresholds and colors where they are read", () => {
    __setStubConfig("claudeUsage", "thresholds.moderate", "50");
    __setStubConfig("claudeUsage", "thresholds.high", 0);
    __setStubConfig("claudeUsage", "thresholds.critical", Number.NaN);
    __setStubConfig("claudeUsage", "colors.moderate", "#12345");
    __setStubConfig("claudeUsage", "colors.high", "none");
    __setStubConfig("claudeUsage", "colors.critical", "#ABCDEF");
    expect(getThresholdConfig()).toEqual({ moderate: 50, high: 75, critical: 95 });
    expect(getColorConfig()).toEqual({ moderate: "#cca700", high: "none", critical: "#ABCDEF" });
  });

  it("validates and escapes values in the markup builder itself, not only on read", () => {
    const hostile = {
      metric: "highest" as const,
      thresholds: { moderate: '50"><img src=x onerror=alert(1)>' as unknown as number, high: 75, critical: 95 },
      colors: { moderate: '#"><svg onload=alert(2)>', high: "#f0643c", critical: "#e05555" },
      compact: false,
    };
    const html = settingsSectionHtml(hostile);
    expect(html).not.toContain("onerror");
    expect(html).not.toContain("onload");
    expect(html).toContain('value="50" class="threshold-slider" data-level="moderate"');
    expect(html).toContain('id="picker-moderate" data-level="moderate" value="#cca700"');
  });

  it("escapes < in JSON embedded in the script", () => {
    expect(jsonForScript({ a: "</script><script>x" })).toBe('{"a":"\\u003c/script>\\u003cscript>x"}');
  });

  const valid = { metric: "weeklyScoped", thresholds: { moderate: 40, high: 70, critical: 90 }, colors: { moderate: "#112233", high: "none", critical: "#AABBCC" }, compact: true };

  it.each([
    [undefined],
    ["draft"],
    [{ ...valid, metric: "monthly" }],
    [{ ...valid, compact: "yes" }],
    [{ ...valid, thresholds: { moderate: "50", high: 75, critical: 95 } }],
    [{ ...valid, thresholds: { moderate: 0, high: 75, critical: 95 } }],
    [{ ...valid, thresholds: { moderate: 50, high: 100, critical: 95 } }],
    [{ ...valid, colors: { moderate: '#"><x', high: "#f0643c", critical: "#e05555" } }],
  ])("rejects a malformed settings draft %#", (draft) => {
    expect(parseDraft(draft)).toBeNull();
  });

  it("accepts a valid draft, including the scoped-model metric", () => {
    expect(parseDraft(valid)).toEqual(valid);
  });

  it("writes nothing for forged or malformed webview messages", async () => {
    DashboardPanel.show(data(), "now", undefined, callbacks);
    const panel = createdWebviewPanels[0];
    for (const message of [null, "save", 42, { command: 1 }, { command: "save" }, { command: "save", draft: { thresholds: "x" } }, { command: "unknown" }]) {
      await panel.webview.__dispatchMessage(message);
    }
    expect(configurationUpdates).toEqual([]);
    expect(panel.webview.postedMessages).toEqual([]);
  });
});

describe("F6: settings scopes and the refresh interval", () => {
  it("scopes thresholds and colors to the application, so a workspace cannot set them", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf-8"));
    const props = pkg.contributes.configuration.properties as Record<string, { scope?: string }>;
    for (const level of ["moderate", "high", "critical"]) {
      expect(props[`claudeUsage.thresholds.${level}`].scope, level).toBe("application");
      expect(props[`claudeUsage.colors.${level}`].scope, level).toBe("application");
    }
  });

  it.each([
    [0, 1],
    [-5, 1],
    [0.5, 1],
    [500, 120],
    [30, 30],
    ["10", 10],
    [Number.NaN, 10],
    [undefined, 10],
  ])("clamps refreshInterval %s to %s minutes", (raw, minutes) => {
    __setStubConfig("claudeUsage", "refreshInterval", raw);
    expect(getRefreshIntervalMinutes()).toBe(minutes);
  });

  it("never schedules a refresh sooner than a minute", () => {
    __setStubConfig("claudeUsage", "refreshInterval", 0);
    const bar = new StatusBarManager(new UsageStore(memento() as never), "x") as unknown as { computeRefreshDelayMs(): number };
    expect(bar.computeRefreshDelayMs()).toBe(60_000);
  });
});
