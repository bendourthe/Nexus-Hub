import { describe, expect, it } from "vitest";
import { buildHoverMarkdown, buildStatusText } from "../src/statusBarManager";
import { renderDashboard } from "../src/dashboardPanel";
import { renderWarning } from "../src/warningView";
import { METER_FILL_COLOR, type UsageState } from "../src/types";
import type { UsageSuggestion } from "../src/recommendations";

/**
 * Visual-parity contract with the sibling Claude and Codex monitors.
 *
 * These exist because the previous pass changed the hover, the dashboard, and the
 * warning panel, and the whole suite stayed green: nothing asserted shape, only
 * wording. A rendering regression that silently reverts to square block-character
 * bars or an off-brand fill would have shipped unnoticed.
 *
 * They assert structural properties (pill radius, brand fill, ring geometry,
 * centering) rather than exact copy, so wording can still change freely.
 */

const now = Date.parse("2026-08-07T12:00:00.000Z");

function snapshot() {
  return {
    fetchedAt: "2026-08-07T11:55:00.000Z",
    source: "credential-api" as const,
    stale: false as const,
    staleReason: null,
    cursorModels: { used: null, limit: null, percentUsed: 1.7, percentOrigin: "source" as const },
    otherModels: { used: null, limit: null, percentUsed: 100, percentOrigin: "source" as const },
    period: { startsAt: "2026-08-03T18:43:07.000Z", resetsAt: "2026-09-03T18:43:07.000Z" },
    onDemand: { enabled: true, personalSpend: { amount: 157.32, currency: "USD" } },
    teamContext: {
      sharedSpendLimit: { amount: 200, currency: "USD" },
      dynamicSpendLimit: true,
      // The pool is drawn PAST its limit with nothing left, while personal spend is
      // far lower. This is the real observed state the rendering must communicate.
      sharedSpendUsed: { amount: 200.86, currency: "USD" },
      sharedSpendRemaining: { amount: 0, currency: "USD" }
    }
  };
}

function fresh(): UsageState {
  return { state: "fresh", data: snapshot() } as unknown as UsageState;
}

function svgOf(hover: string): string {
  const encoded = /src="data:image\/svg\+xml,([^"]+)"/u.exec(hover)?.[1];
  expect(encoded).toBeDefined();
  return decodeURIComponent(encoded!);
}

describe("hover bars", () => {
  it("draws pill-shaped bars in the brand fill", () => {
    const svg = svgOf(buildHoverMarkdown(fresh(), now).value);
    // rx is half the bar height, which is what makes the cap round rather than square.
    expect(svg).toContain('rx="3"');
    expect(svg).toContain(`fill="${METER_FILL_COLOR}"`);
    // A visible track behind the fill, so an almost-empty pool still reads as a bar.
    expect(svg).toContain(`fill="${METER_FILL_COLOR}33"`);
  });

  it("shows one bar per pool plus one for extra usage", () => {
    const hover = buildHoverMarkdown(fresh(), now).value;
    expect(hover.match(/<img /gu)?.length).toBe(3);
  });

  it("labels every bar in alt text, not only inside the image", () => {
    // Text baked into an SVG is invisible to a screen reader and unselectable.
    const hover = buildHoverMarkdown(fresh(), now).value;
    expect(hover).toContain('alt="Cursor Models 1.7%"');
    expect(hover).toContain('alt="Other Models 100%"');
  });

  it("gives each pool its own reset line", () => {
    const hover = buildHoverMarkdown(fresh(), now).value;
    expect(hover.match(/Resets /gu)?.length).toBeGreaterThanOrEqual(3);
  });

  it("states personal spend AND that the shared pool is gone", () => {
    // The whole point of the shared-pool rendering: personal spend of 157.32 against
    // a 200.00 limit looks like 21% headroom, and there is none.
    const hover = buildHoverMarkdown(fresh(), now).value;
    // Two lines, matching the siblings: organization draw first, personal second.
    expect(hover).toContain("$200.86 / $200.00 used this month by the organization");
    expect(hover).toContain("($157.32 used by your account)");
    expect(hover).toContain("none left");
  });

  it("clamps an over-drawn pool instead of overflowing its track", () => {
    const svg = svgOf(buildHoverMarkdown(fresh(), now).value.split("Extra Credits")[0]!);
    const widths = [...svg.matchAll(/width="(\d+)"/gu)].map((m) => Number(m[1]));
    for (const width of widths) {
      expect(width).toBeLessThanOrEqual(360);
    }
  });
});

describe("status bar label toggle", () => {
  it("can render without the 'Cursor Usage: ' prefix", () => {
    // compactStatusBar also abbreviates the pool names, so it cannot serve as a
    // plain "hide the words" switch; this is the dedicated one.
    const withLabel = buildStatusText(fresh(), false);
    expect(withLabel).toContain("Cursor Usage: ");
    const compact = buildStatusText(fresh(), true);
    expect(compact).not.toContain("Cursor Usage: ");
  });
});

describe("dashboard layout", () => {
  it("uses a narrow centered column like the sibling monitors", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    // 500px is the sibling monitors' own column width, matched exactly.
    expect(html).toContain("max-width:500px");
    expect(html).toContain("margin:0 auto");
  });

  it("uses uppercase section labels", () => {
    expect(renderDashboard(fresh(), now, "nonce")).toContain(
      "text-transform:uppercase"
    );
  });

  it("draws pill-shaped bars in the brand fill", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    expect(html).toContain("border-radius:4px");
    expect(html).toContain(METER_FILL_COLOR);
  });

  it("reports both the personal spend and the exhausted shared pool", () => {
    const html = renderDashboard(fresh(), now, "nonce");
    expect(html).toContain("$157.32");
    expect(html).toContain("fully spent");
    expect(html).toContain("$200.00");
  });
});

describe("warning panel", () => {
  const suggestion: UsageSuggestion = {
    severity: "critical",
    label: "Other Models percentage",
    percent: 100,
    message: "Other Models reached 100% of included usage.",
    recommendation: "Pause non-essential runs until the included-usage period resets.",
    meter: { used: null, limit: null, percentUsed: 100, percentOrigin: "source" }
  } as unknown as UsageSuggestion;

  it("carries the siblings' advice, reset, and footer structure", () => {
    const html = renderWarning(suggestion, "local", "'self'", "nonce");
    expect(html).toContain("Ways to extend your usage");
    expect(html).toContain('class="recs"');
    expect(html).toContain('class="reset-box"');
    expect(html).toContain("Source: Cursor Usage Monitor");
    expect(html).toContain('data-command="dashboard"');
    expect(html).toContain('data-command="dismiss"');
  });

  it("draws a ring rather than a bare number", () => {
    const html = renderWarning(suggestion, "local", "'self'", "nonce");
    expect(html).toContain("<svg");
    expect(html).toContain("stroke-dasharray");
    expect(html).toContain(`stroke="${METER_FILL_COLOR}"`);
    expect(html).toContain('role="meter"');
  });

  it("starts the arc at twelve o'clock", () => {
    // Without the rotation an SVG circle starts at 3 o'clock, which reads as though
    // the meter is offset by a quarter turn.
    expect(renderWarning(suggestion, "local", "'self'", "nonce")).toContain(
      "rotate(-90 60 60)"
    );
  });

  it("centers its content", () => {
    const html = renderWarning(suggestion, "local", "'self'", "nonce");
    expect(html).toContain("main{text-align:center}");
    // The brand block is a centred column (logo above a two-line title), and the
    // footer actions sit centred beneath the source line - the siblings' layout.
    expect(html).toContain(".brand{display:flex;flex-direction:column;align-items:center");
    expect(html).toContain(".footer-actions{display:flex;gap:8px;justify-content:center}");
  });

  it("clamps the arc so an over-limit meter cannot wrap past its own start", () => {
    // A second lap would render a high value as a low one.
    const over = { ...suggestion, percent: 250 } as UsageSuggestion;
    const html = renderWarning(over, "local", "'self'", "nonce");
    const arc = Number(/stroke-dasharray="([\d.]+)/u.exec(html)?.[1]);
    const circumference = 2 * Math.PI * 52;
    expect(arc).toBeLessThanOrEqual(circumference + 0.01);
    expect(html).toContain(">100%<");
  });
});
