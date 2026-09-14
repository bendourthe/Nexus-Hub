import { afterEach, describe, expect, it } from "vitest";
import { StatusBarManager } from "../src/statusBarManager";
import type { UsageData } from "../src/types";
import type { UsageStore } from "../src/usageStore";
import { __resetStubState, createdStatusBarItems } from "./vscode-stub";

/**
 * Renders the status-bar hover tooltip (v4.10.0 MT-2).
 *
 * The 12 pre-existing tests stop at the normalized data model: they prove
 * `mapClaudeUsageResponse` resolves a scoped weekly metric, not that anything
 * draws it. The tooltip is the riskiest surface in the extension precisely
 * because it is the least type-checked - each bar is a hand-built SVG string
 * that is percent-encoded into a data URI, so a malformed tag, an unescaped
 * label or a dropped section is invisible to `tsc` and to every unit test that
 * existed. These tests decode the URI and assert on the markup itself.
 *
 * This does NOT replace loading the extension in a real host: it proves the
 * markup is correct, not that VS Code renders it as intended.
 */

/** Decode every `data:image/svg+xml,...` payload in a tooltip, in order. */
function decodeBars(tooltipValue: string): string[] {
  const out: string[] = [];
  const re = /data:image\/svg\+xml,([^"]+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(tooltipValue)) !== null) {
    out.push(decodeURIComponent(m[1]));
  }
  return out;
}

function storeFor(data: UsageData): UsageStore {
  return {
    getWithFreshCountdowns: () => data,
    getTimeSinceUpdate: () => "just now",
    hasResetExpired: () => false,
  } as unknown as UsageStore;
}

const baseData: UsageData = {
  session: { percent: 12, resetsIn: "3h", resetsAt: null },
  weeklyAllModels: { percent: 34, resetsIn: "4d", resetsAt: null },
  currentModel: "opus" as UsageData["currentModel"],
  lastUpdated: Date.now(),
};

function renderTooltip(data: UsageData): string {
  __resetStubState();
  const mgr = new StatusBarManager(storeFor(data), "claude-usage.dashboard");
  mgr.refresh();
  const tooltip = createdStatusBarItems[0].tooltip as { value: string };
  return tooltip.value;
}

describe("status-bar tooltip weekly bars", () => {
  afterEach(() => __resetStubState());

  it("draws a second weekly bar labelled from the account", () => {
    const value = renderTooltip({
      ...baseData,
      weeklyScoped: { percent: 56, resetsIn: "4d", resetsAt: null, label: "Fable" },
    });
    const bars = decodeBars(value);

    // Current Session, Weekly (All Models), Weekly (Fable). Extra Credits is
    // absent here, so it renders as an N/A line rather than a fourth bar.
    expect(bars).toHaveLength(3);
    expect(bars[1]).toContain("Weekly (All Models)");
    expect(bars[2]).toContain("Weekly (Fable)");
    expect(bars[2]).toContain("56%");
  });

  it("omits the second weekly bar when the account reports no scoped limit", () => {
    const bars = decodeBars(renderTooltip(baseData));
    expect(bars).toHaveLength(2);
    expect(bars.some((b) => b.includes("Weekly (All Models)"))).toBe(true);
    expect(bars.some((b) => /Weekly \((?!All Models)/.test(b))).toBe(false);
  });

  it("escapes a server-provided label instead of injecting raw markup", () => {
    const bars = decodeBars(renderTooltip({
      ...baseData,
      weeklyScoped: {
        percent: 1,
        resetsIn: "4d",
        resetsAt: null,
        label: '</text><script>x</script>',
      },
    }));
    // The label arrives from the usage API, so it is attacker-influenced input
    // reaching an SVG that the tooltip renders as trusted HTML.
    expect(bars[2]).not.toContain("<script>");
    expect(bars[2]).toContain("&lt;/text&gt;");
  });

  it("produces one well-formed svg element per bar", () => {
    const bars = decodeBars(renderTooltip({
      ...baseData,
      weeklyScoped: { percent: 56, resetsIn: "4d", resetsAt: null, label: "Fable" },
    }));
    for (const bar of bars) {
      expect(bar.startsWith("<svg ")).toBe(true);
      expect(bar.endsWith("</svg>")).toBe(true);
      expect((bar.match(/<svg /g) ?? []).length).toBe(1);
    }
  });

  it("clamps the fill width so an out-of-range percent cannot overflow the bar", () => {
    const bars = decodeBars(renderTooltip({
      ...baseData,
      weeklyScoped: { percent: 140, resetsIn: "4d", resetsAt: null, label: "Fable" },
    }));
    const widths = [...bars[2].matchAll(/<rect y="\d+" width="(\d+)"/g)].map((m) => Number(m[1]));
    // Track then fill; the fill must never exceed the 280px track.
    expect(widths).toHaveLength(2);
    expect(widths[1]).toBeLessThanOrEqual(widths[0]);
  });
});
