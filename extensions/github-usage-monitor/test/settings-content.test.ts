import { beforeEach, describe, expect, it } from "vitest";
import {
  EDITABLE_SETTINGS,
  isEditableSetting,
  readSettings,
  settingsScriptJs,
  settingsSectionHtml,
  validateThresholds
} from "../src/settingsPanel";
import { buildHoverMarkdown, buildStatusText, selectStatusMetric, type StatusBarMetric } from "../src/statusBarManager";
import { DashboardPanel } from "../src/dashboardPanel";
import { resetVscodeStub, setConfiguration, webviewPanels } from "./vscode-stub";
import type { UsageMetric, UsageSnapshot } from "../src/types";

function metric(kind: UsageMetric["kind"], unit: string, used: number, percentage: number | null): UsageMetric {
  return {
    kind, unit, used,
    drawdown: percentage === null ? null : used,
    drawdownBasis: percentage === null ? "unavailable" : "reconstructed",
    allowance: percentage === null ? null : 2000,
    allowanceSource: percentage === null ? "unknown" : "plan-table",
    allowanceState: percentage === null ? "unknown" : "verified",
    percentage,
    reset: null, breakdowns: [], grossAmount: null, discountAmount: null, netAmount: null
  };
}

function snapshot(overrides: Partial<UsageSnapshot> = {}): UsageSnapshot {
  return {
    owner: { scope: "user", name: "bendourthe" },
    periodStart: Date.UTC(2026, 7, 1), periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: Date.UTC(2026, 7, 9), source: "api", stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 40, null),
    actionsMinutes: metric("actions-minutes", "minutes", 128, 6.4),
    actionsStorage: metric("actions-storage", "gigabytes", 0.087, 17.4),
    ...overrides
  };
}

describe("status-bar metric selection", () => {
  beforeEach(() => { resetVscodeStub(); });

  it("defaults to Actions minutes", () => {
    // The metric with a real published entitlement for most accounts, and therefore
    // the one most likely to show a meaningful percentage.
    expect(readSettings().statusBarMetric).toBe("actions-minutes");
    expect(buildStatusText(snapshot(), false, false)).toContain("6%");
  });

  it("shows whichever metric the user selected", () => {
    expect(buildStatusText(snapshot(), false, false, false, "actions-minutes")).toContain("6%");
    expect(buildStatusText(snapshot(), false, false, false, "actions-storage")).toContain("17%");
  });

  it("reproduces the pre-change behaviour exactly under `highest`", () => {
    // Regression guard. Before v3.16.3 Phase 5 the status bar unconditionally sorted
    // every metric by percentage and showed the largest; that is now one option
    // rather than the only behaviour, and it must still behave identically.
    const withHigherStorage = snapshot({
      actionsMinutes: metric("actions-minutes", "minutes", 128, 6.4),
      actionsStorage: metric("actions-storage", "gigabytes", 0.4, 81)
    });
    expect(selectStatusMetric(withHigherStorage, "highest")?.kind).toBe("actions-storage");
    expect(buildStatusText(withHigherStorage, false, false, false, "highest")).toContain("81%");
    // And with no percentages at all it falls back to the Copilot amount, as before.
    const noPercentages = snapshot({
      actionsMinutes: metric("actions-minutes", "minutes", 128, null),
      actionsStorage: metric("actions-storage", "gigabytes", 0.087, null)
    });
    expect(buildStatusText(noPercentages, false, false, false, "highest")).toContain("40 ai-credits");
  });

  it("shows an absolute amount, never a fabricated percentage, when the allowance is unknown", () => {
    // Copilot has no plan allowance, so it can only ever show an amount.
    const text = buildStatusText(snapshot(), false, false, false, "copilot");
    expect(text).toContain("40 ai-credits");
    expect(text).not.toContain("%");
  });

  it("never silently substitutes a different metric when the selection is unavailable", () => {
    // A status bar quietly showing a number other than the one the user chose is a
    // correctness bug, not graceful degradation.
    const missing = snapshot({ actionsStorage: undefined as unknown as UsageMetric });
    const text = buildStatusText(missing, false, false, false, "actions-storage");
    expect(text).toContain("n/a");
    expect(text).not.toContain("6%");
    expect(text).not.toContain("40 ai-credits");
  });

  it("explains an unavailable selection in the hover rather than leaving n/a bare", () => {
    setConfiguration("githubUsageMonitor.statusBarMetric", "actions-storage");
    const missing = snapshot({ actionsStorage: undefined as unknown as UsageMetric });
    const hover = buildHoverMarkdown({ state: "fresh", data: missing }).value;
    expect(hover).toContain("does not report");
    expect(hover).toContain("actions-storage");
  });

  it("honours the compact toggle for every selection, including Not connected", () => {
    expect(buildStatusText(snapshot(), false, false, false, "actions-minutes")).toContain("GitHub Usage: ");
    expect(buildStatusText(snapshot(), false, true, false, "actions-minutes")).not.toContain("GitHub Usage: ");
    // The unconnected state used to hard-code the label, ignoring compact mode.
    expect(buildStatusText(undefined, false, true, true)).not.toContain("GitHub Usage: ");
    expect(buildStatusText(undefined, false, false, true)).toContain("GitHub Usage: Not connected");
  });

  it("covers every declared option", () => {
    const options: StatusBarMetric[] = ["actions-minutes", "actions-storage", "copilot", "highest"];
    for (const option of options) {
      expect(() => buildStatusText(snapshot(), false, false, false, option)).not.toThrow();
    }
  });
});

describe("editable settings section", () => {
  beforeEach(() => { resetVscodeStub(); });

  it("renders an editable control for every editable setting", () => {
    const html = settingsSectionHtml(readSettings());
    for (const key of Object.keys(EDITABLE_SETTINGS)) {
      expect(html).toContain(`data-setting="${key}"`);
    }
  });

  it("renders the status-bar metric selector with Actions minutes selected by default", () => {
    const html = settingsSectionHtml(readSettings());
    expect(html).toContain('data-setting="statusBarMetric"');
    expect(html).toContain('<option value="actions-minutes" selected>');
  });

  it("renders the compact toggle as a checkbox, not a read-only value", () => {
    const html = settingsSectionHtml(readSettings());
    expect(html).toContain('data-setting="compactStatusBar"');
    expect(html).toContain('type="checkbox"');
  });

  it("drops the panel buttons the maintainer asked to remove, without unregistering them", () => {
    // v3.16.4 simplified the Account group to a name plus Connect and Log out, and
    // removed the allowance override entirely (allowances are derived now). The
    // commands remain registered in package.json and extension.ts, so the Command
    // Palette still reaches them - the panel got shorter, the capability did not.
    const html = settingsSectionHtml(readSettings());
    for (const removed of ["openNativeSettings", "manualEntry", "setToken", "rotateToken", "validateToken", "clearToken", "diagnoseAuth"]) {
      expect(html).not.toContain(`data-command="${removed}"`);
    }
    // logIn / logOut are no longer here either. As of 2026-08-11 every account
    // control lives in the panel header, so this section is settings only.
    expect(html).not.toContain('data-command="logIn"');
    expect(html).not.toContain('data-command="logOut"');
  });

  it("validates thresholds inline, beside the field rather than as a notification", () => {
    const html = settingsSectionHtml(readSettings());
    expect(html).toContain('id="err-thresholds.moderate"');
    expect(html).toContain('role="alert"');
    // The ordering check runs in the webview so the message lands next to the
    // offending field; an invalid draft is never posted.
    const script = settingsScriptJs();
    expect(script).toContain("thresholdOrderError");
    expect(script).toContain("must increase from moderate to high to critical");
    expect(script).toContain("if(error)return;");
  });
});

describe("setting write-back guard", () => {
  it("accepts only declared keys, with the declared type", () => {
    expect(isEditableSetting("thresholds.high", 75)).toBe(true);
    expect(isEditableSetting("compactStatusBar", true)).toBe(true);
    expect(isEditableSetting("statusBarMetric", "copilot")).toBe(true);
    // Wrong type for a declared key.
    expect(isEditableSetting("thresholds.high", "75")).toBe(false);
    expect(isEditableSetting("compactStatusBar", "yes")).toBe(false);
    expect(isEditableSetting("thresholds.high", Number.NaN)).toBe(false);
  });

  it("rejects any key outside the editable set", () => {
    // A webview is a browser context. Without this gate a crafted message could
    // write ANY VS Code setting, which is far wider than this panel needs.
    expect(isEditableSetting("billingOwner", "attacker")).toBe(false);
    expect(isEditableSetting("allowances.actionsMinutes", 1)).toBe(false);
    expect(isEditableSetting("http.proxy", "http://evil")).toBe(false);
    expect(isEditableSetting(42, "x")).toBe(false);
    expect(isEditableSetting(undefined, "x")).toBe(false);
  });

  it("still rejects an out-of-order threshold set", () => {
    // The panel checks this too, but its check is a convenience for the user and
    // never a guarantee for the extension.
    expect(validateThresholds({ moderate: 80, high: 50, critical: 95 })).toContain("increase");
    expect(validateThresholds({ moderate: 50, high: 75, critical: 95 })).toBeNull();
  });

  it("routes an updateSetting message to the handler instead of executing a command", () => {
    resetVscodeStub();
    const received: Array<{ key: unknown; value: unknown }> = [];
    const dashboard = new DashboardPanel((key, value) => received.push({ key, value }));
    dashboard.show({ state: "empty" });

    webviewPanels[0]?.webview.receive({ command: "updateSetting", key: "thresholds.high", value: 70 } as never);
    expect(received).toEqual([{ key: "thresholds.high", value: 70 }]);
  });

  it("still routes an ordinary command message through executeCommand", () => {
    resetVscodeStub();
    const received: unknown[] = [];
    const dashboard = new DashboardPanel((key) => received.push(key));
    dashboard.show({ state: "empty" });

    webviewPanels[0]?.webview.receive({ command: "refresh" });
    // The command path must not be swallowed by the settings handler.
    expect(received).toEqual([]);
  });
});
