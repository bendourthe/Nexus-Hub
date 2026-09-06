import { afterEach, describe, expect, it } from "vitest";
import { DashboardPanel, renderDashboard } from "../src/dashboardPanel";
import {
  formatCalendarDate,
  formatPercent,
  formatSharedSpendNote,
  formatSpendAgainstLimit,
  spendFractionOfLimit
} from "../src/formatters";
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
    // Pool labels now live in an SVG bar. The `alt` attribute is what keeps them
    // readable to a screen reader and assertable here - baking label text only into
    // an image would make the hover unreadable to anyone not looking at it.
    expect(hover).toContain('alt="Cursor Models');
    expect(hover).toContain("Other Models");
    expect(hover).toContain("Allowance unavailable; absolute usage only");
    // This fixture carries no pooled figures, so the bar is correctly dropped and
    // only the user's own spend is stated. The two-line organization/personal form
    // is asserted in visual-parity.test.ts against a fixture that has pooled data.
    expect(hover).toContain("$14.25 used by your account");
    expect(hover).toContain("shared limit not reported");
    // The bar lives in a data: URI, so the brand color is percent-encoded there
    // (# becomes %23). Decode ONLY the URI, not the whole hover: the hover also
    // carries an escaped error message containing a literal %, which makes
    // decodeURIComponent throw URIError on the full string.
    const svgSource = /src="data:image\/svg\+xml,([^"]+)"/u.exec(hover)?.[1];
    expect(svgSource).toBeDefined();
    const svg = decodeURIComponent(svgSource!);
    expect(svg).toContain(`fill="${METER_FILL_COLOR}"`);
    // Pill shape, not a square-ended bar: rx is half the bar height.
    expect(svg).toContain('rx="3"');

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

    for (const output of [dashboard, warning]) {
      expect(output).toContain("80%");
      expect(output).toContain("80 requests");
      expect(output).not.toContain("of Not reported");
    }
    // The hover renders its percentage inside the bar image, so it is asserted via
    // the alt text; the absolute figure stays as real text beneath the bar, because
    // a percentage without the underlying number is less information, not more.
    expect(hover).toContain('alt="Cursor Models 80%"');
    expect(hover).toContain("80 requests used");
    expect(hover).not.toContain("of Not reported");
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
    // Renamed to match the sibling monitors' vocabulary.
    expect(html).toContain("Extra Credits");
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

/** A snapshot where BOTH pools have a denominator, so all three bars render. */
function threeBarSnapshot(): FreshUsageSnapshot {
  return {
    ...snapshot(),
    cursorModels: {
      used: { value: 1_000_000, unit: "tokens" },
      limit: { value: 1_000_000, unit: "tokens" },
      percentUsed: 100,
      percentOrigin: "source"
    },
    otherModels: {
      used: { value: 8_500, unit: "tokens" },
      limit: { value: 500_000, unit: "tokens" },
      percentUsed: 1.7,
      percentOrigin: "source"
    }
  };
}

describe("percentage and money formatters", () => {
  it.each([
    [80, "80%"],
    [100, "100%"],
    [1.7, "1.7%"],
    [34.5, "34.5%"],
    [0, "0%"],
    [-5, "0%"]
  ])("formats %s as %s", (input, expected) => {
    expect(formatPercent(input)).toBe(expected);
  });

  it("keeps a nearly-empty pool from rounding up into a used-looking figure", () => {
    // Plain rounding turned 1.7% into "2%", overstating an untouched allowance.
    expect(formatPercent(1.7)).not.toBe("2%");
  });

  it("renders a billing-cycle date in UTC so it cannot shift a day west of UTC", () => {
    expect(formatCalendarDate("2026-09-01T00:00:00Z")).toBe("September 1, 2026");
    expect(formatCalendarDate(null)).toBe("an unreported date");
    expect(formatCalendarDate("not-a-date")).toBe("an unreported date");
  });

  it("refuses a spend fraction when it would be meaningless", () => {
    const spend = { amount: 50, currency: "USD" };
    expect(spendFractionOfLimit(spend, { amount: 200, currency: "USD" })).toBe(25);
    // Mixing currencies is the money equivalent of the unit mismatch the
    // included-usage meters already refuse.
    expect(
      spendFractionOfLimit(spend, { amount: 200, currency: "EUR" })
    ).toBeNull();
    expect(spendFractionOfLimit(spend, { amount: 0, currency: "USD" })).toBeNull();
    expect(spendFractionOfLimit(spend, null)).toBeNull();
    expect(spendFractionOfLimit(null, { amount: 200, currency: "USD" })).toBeNull();
  });

  it("states spend in currency against its limit, never as a token percentage", () => {
    expect(
      formatSpendAgainstLimit(
        { amount: 12.5, currency: "USD" },
        { amount: 200, currency: "USD" }
      )
    ).toBe("$12.50 of $200.00");
    expect(
      formatSpendAgainstLimit({ amount: 12.5, currency: "USD" }, null)
    ).toContain("limit not reported");
    expect(
      formatSpendAgainstLimit(
        { amount: 12.5, currency: "USD" },
        { amount: 200, currency: "EUR" }
      )
    ).toContain("different currency");
    expect(formatSpendAgainstLimit(null, null)).toBe("Not reported");
  });

  it("names the sharing scope and takes the reset date from the payload", () => {
    const note = formatSharedSpendNote("2026-09-01T00:00:00Z");
    expect(note).toContain("shared across your team");
    expect(note).toContain("not a personal allowance");
    expect(note).toContain("September 1, 2026");

    // Proves the date is payload-derived rather than a hardcoded day.
    expect(formatSharedSpendNote("2026-10-15T00:00:00Z")).toContain(
      "October 15, 2026"
    );
  });
});

describe("dashboard on-demand bar", () => {
  it("renders three bars: both included pools plus on-demand spend", () => {
    const html = renderDashboard(
      { state: "fresh", data: threeBarSnapshot() },
      now,
      "nonce"
    );
    expect(html.match(/role="meter"/gu)).toHaveLength(3);
    expect(html).toContain("Cursor Models");
    expect(html).toContain("Other Models");
    expect(html).toContain(
      'aria-label="On-demand spend against the shared team limit"'
    );
  });

  it("keeps a full pool visually distinguishable from a nearly-empty one", () => {
    const html = renderDashboard(
      { state: "fresh", data: threeBarSnapshot() },
      now,
      "nonce"
    );
    // Widths differ by two orders of magnitude, and the labels keep the precision.
    expect(html).toContain("fill fill-100");
    expect(html).toContain("fill fill-2");
    expect(html).toContain(">100%<");
    expect(html).toContain(">1.7%<");
  });

  it("states on-demand spend as currency against its limit, not a token percentage", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    expect(html).toContain("$14.25 of $500.00");
    // The bar's own value text leads with currency; the percentage is geometry
    // only, and carries the same one-decimal precision as the included pools.
    expect(html).toContain("2.9% of the limit shared across your team");
    expect(html).not.toContain("$14.25 tokens");
  });

  it("annotates the on-demand bar with sharing scope and the payload reset date", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    expect(html).toContain("shared across your team");
    expect(html).toContain("not a personal allowance");
    expect(html).toContain("September 1, 2026");
  });

  it("never presents the shared pool as a personal cap", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    // The guarantee is semantic, not a heading: the sharing scope must be stated
    // and the pool must never be framed as this user's own cap. The separate
    // "Shared team context" block folded into Extra Credits, matching the siblings.
    expect(html).toContain("Shared limit");
    expect(html).toContain("shared across your team");
    expect(html).toContain("not a personal allowance");
    expect(html).not.toMatch(/personal (cap|limit|allowance of)/iu);
    // The shared amount is never divided down into a per-member figure.
    expect(html).not.toContain("per member");
  });

  it("drops the bar rather than inventing a denominator when the limit is absent", () => {
    const data = snapshot();
    data.teamContext = { sharedSpendLimit: null, dynamicSpendLimit: null };
    const html = renderDashboard({ state: "fresh", data }, now, "nonce");

    expect(html).toContain("Shared spend limit unavailable - spend only");
    expect(html).toContain("limit not reported");
    expect(html).not.toContain(
      'aria-label="On-demand spend against the shared team limit"'
    );
  });

  it("drops the bar when spend and limit use different currencies", () => {
    const data = snapshot();
    data.teamContext = {
      sharedSpendLimit: { amount: 500, currency: "EUR" },
      dynamicSpendLimit: false
    };
    const html = renderDashboard({ state: "fresh", data }, now, "nonce");
    expect(html).toContain("different currency");
    expect(html).toContain("Shared spend limit unavailable - spend only");
  });

  it("clamps an over-limit bar and says so instead of overflowing", () => {
    const data = snapshot();
    data.onDemand = {
      enabled: true,
      personalSpend: { amount: 750, currency: "USD" }
    };
    const html = renderDashboard({ state: "fresh", data }, now, "nonce");

    expect(html).toContain("fill fill-100");
    expect(html).toContain("Over the shared limit");
    expect(html).toContain("$750.00 of $500.00");
    expect(html).not.toContain("fill-150");
  });

  it("renders no on-demand bar when on-demand is disabled or unknown", () => {
    for (const onDemand of [
      { enabled: false as const, personalSpend: null },
      { enabled: null as const, personalSpend: null }
    ]) {
      const data = { ...snapshot(), onDemand };
      const html = renderDashboard({ state: "fresh", data }, now, "nonce");
      expect(html).not.toContain(
        'aria-label="On-demand spend against the shared team limit"'
      );
      expect(html).toContain("Not applicable");
      expect(html.match(/role="meter"/gu)).toHaveLength(1);
    }
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
