import { describe, expect, it } from "vitest";
import { renderDashboard } from "../src/dashboardPanel";
import { contributionsByRepository, type UsageLineItem, type VisibilityMap } from "../src/providers/drawdown";
import { describeDrawdownProvenance, enrichSnapshot } from "../src/providers/enrich";
import type { UsageMetric, UsageSnapshot } from "../src/types";

const now = Date.UTC(2026, 7, 20, 12);

/**
 * The measured August month, reproduced from the 2026-08-19 jobs-API observation:
 * `Nexus-AI` private with 1,457 Linux + 187 Windows + 80 macOS, and `Nexus-Hub`
 * public with the 366 runs that cost nothing. The public row existing but reading
 * zero is the whole point of the section under test.
 */
const RATE = { linux: 0.006, windows: 0.010, macos: 0.062 } as const;
const VISIBILITY: VisibilityMap = { "Nexus-AI": "private", "Nexus-Hub": "public" };

function breakdown(sku: string, quantity: number, repositoryName: string, pricePerUnit: number | null) {
  return {
    product: "Actions", sku, unit: "minutes" as const, grossQuantity: quantity,
    discountQuantity: null, netQuantity: null, grossAmount: null, discountAmount: null,
    netAmount: null, repositoryName, pricePerUnit
  };
}

function metric(kind: UsageMetric["kind"], unit: string, used: number, breakdowns: UsageMetric["breakdowns"]): UsageMetric {
  return {
    kind, unit, used, allowance: null, drawdown: null, drawdownBasis: "unavailable",
    allowanceSource: "unknown", allowanceState: "unknown", percentage: null,
    reset: { at: Date.UTC(2026, 8, 1), kind: "reporting-period", label: "month" },
    breakdowns, grossAmount: null, discountAmount: null, netAmount: null
  };
}

function augustSnapshot(extra: UsageMetric["breakdowns"] = []): UsageSnapshot {
  return {
    owner: { scope: "user", name: "bendourthe" },
    periodStart: Date.UTC(2026, 7, 1), periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: now - 60_000, source: "api", stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 0, []),
    actionsMinutes: metric("actions-minutes", "minutes", 5924, [
      breakdown("Actions Linux", 1457, "Nexus-AI", RATE.linux),
      breakdown("Actions Windows", 187, "Nexus-AI", RATE.windows),
      breakdown("Actions macOS 3-core", 80, "Nexus-AI", RATE.macos),
      breakdown("Actions Linux", 4200, "Nexus-Hub", RATE.linux),
      ...extra
    ]),
    actionsStorage: metric("actions-storage", "gigabyte-hours", 64.5, [])
  };
}

function line(overrides: Partial<UsageLineItem> = {}): UsageLineItem {
  return {
    date: "2026-08-01", product: "Actions", sku: "Actions Linux", unitType: "minutes",
    quantity: 10, pricePerUnit: RATE.linux, grossAmount: null, discountAmount: null,
    netAmount: null, repositoryName: "Nexus-AI", ...overrides
  };
}

describe("per-repository contributions", () => {
  it("shows a public repository contributing zero, rather than hiding it", () => {
    // Filtering the public row out leaves "why did those runs cost nothing"
    // unanswered, just less visibly. It has to be present AND read as zero.
    const rows = contributionsByRepository(
      [
        line({ quantity: 1457, repositoryName: "Nexus-AI" }),
        line({ quantity: 4200, repositoryName: "Nexus-Hub" })
      ],
      VISIBILITY
    );
    const publicRow = rows.find((row) => row.repositoryName === "Nexus-Hub");
    expect(publicRow?.visibility).toBe("public");
    expect(publicRow?.rawMinutes).toBe(4200);
    expect(publicRow?.weightedMinutes).toBe(0);
  });

  it("sorts by weighted contribution, not by raw minutes", () => {
    // Nexus-Hub has nearly three times the raw minutes and none of the cost.
    const rows = contributionsByRepository(
      [
        line({ quantity: 1457, repositoryName: "Nexus-AI" }),
        line({ quantity: 4200, repositoryName: "Nexus-Hub" })
      ],
      VISIBILITY
    );
    expect(rows[0]?.repositoryName).toBe("Nexus-AI");
  });

  it("never counts an excluded runner toward a private repository's contribution", () => {
    const rows = contributionsByRepository(
      [
        line({ quantity: 100, repositoryName: "Nexus-AI" }),
        line({ sku: "Actions Linux 16-core", quantity: 500, repositoryName: "Nexus-AI", pricePerUnit: 0.032 })
      ],
      VISIBILITY
    );
    expect(rows[0]?.rawMinutes).toBe(600);
    expect(rows[0]?.weightedMinutes).toBe(100);
  });
});

describe("panel rendering of the split", () => {
  it("renders the measured August month with both halves of the provenance", () => {
    const { snapshot } = enrichSnapshot(augustSnapshot(), { visibility: VISIBILITY, planName: "free" });
    const html = renderDashboard({ state: "fresh", data: snapshot }, now);

    expect(html).toContain("Actions minutes by repository");
    expect(html).toContain("Nexus-AI");
    expect(html).toContain("Nexus-Hub");
    expect(html).toContain("public");
    expect(html).toContain("private");
    // The numerator's provenance names the derived rate and its source.
    expect(html).toContain("weighted by its own list price");
    expect(html).toContain("observed in this period");
    // The denominator's provenance is a separate sentence, not folded into it.
    expect(html).toContain("Published figure for GitHub Free");
  });

  it("caps the row list and aggregates the tail rather than dropping it", () => {
    const many = Array.from({ length: 40 }, (_, index) =>
      breakdown("Actions Linux", 10 + index, `repo-${index}`, RATE.linux)
    );
    const visibility: VisibilityMap = { ...VISIBILITY };
    for (let index = 0; index < 40; index += 1) visibility[`repo-${index}`] = "private";

    const { snapshot } = enrichSnapshot(augustSnapshot(many), { visibility, planName: "free" });
    const html = renderDashboard({ state: "fresh", data: snapshot }, now);

    expect(html).toMatch(/other \(\d+ repositories\)/);
    // 12 capped rows plus the aggregate, never 44 rows in a sidebar. Scoped to the
    // repository table: the billing-detail section renders its own rows.
    const table = /<table class="repo-table">[\s\S]*?<\/table>/.exec(html)?.[0] ?? "";
    const rowCount = (table.match(/<tr><td>/g) ?? []).length;
    expect(rowCount).toBe(13);
  });

  it("escapes a repository name rather than letting it reach the DOM as markup", () => {
    const hostile = [breakdown("Actions Linux", 5, '<img src=x onerror="alert(1)">', RATE.linux)];
    const visibility: VisibilityMap = { ...VISIBILITY, '<img src=x onerror="alert(1)">': "private" };
    const { snapshot } = enrichSnapshot(augustSnapshot(hostile), { visibility, planName: "free" });
    const html = renderDashboard({ state: "fresh", data: snapshot }, now);
    expect(html).not.toContain("<img src=x");
    expect(html).toContain("&lt;img");
  });

  it("renders without the section on a snapshot cached before 0.4.0", () => {
    // `actionsDrawdownDetail` is optional precisely so an upgrade does not throw on
    // the first render against a snapshot that predates the field.
    const legacy = augustSnapshot();
    const html = renderDashboard({ state: "fresh", data: legacy }, now);
    expect(html).not.toContain("Actions minutes by repository");
    expect(html).toContain("GitHub");
  });
});

describe("numerator provenance", () => {
  it("says when the rate was a published fallback and why", () => {
    const text = describeDrawdownProvenance({
      repositories: [], linuxReferenceRate: 0.006, linuxRateSource: "published-fallback",
      unresolved: [], allowanceProvenance: "Published figure for GitHub Free."
    });
    expect(text).toContain("published standard rate");
    expect(text).toContain("no Linux runner to observe one from");
  });

  it("degrades to a plain sentence when no detail was persisted", () => {
    expect(describeDrawdownProvenance(undefined)).toContain("Reconstructed from private-repository");
  });
});
