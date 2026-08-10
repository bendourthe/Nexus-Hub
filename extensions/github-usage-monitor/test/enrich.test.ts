import { describe, expect, it } from "vitest";
import {
  OS_DRAWDOWN_WEIGHTS,
  computeDrawdownMinutes,
  gigabyteHoursToGigabyteMonths,
  hoursInUtcMonth,
  type UsageLineItem,
  type VisibilityMap
} from "../src/providers/drawdown";
import {
  PLAN_ENTITLEMENTS,
  PRODUCTS_WITHOUT_ALLOWANCE,
  entitlementFor,
  resolvePlan
} from "../src/providers/planEntitlements";
import { enrichSnapshot, storageGigabyteMonths, describeAllowanceProvenance } from "../src/providers/enrich";
import { RepositoryVisibilityCache, fetchAccountPlanName, repositoryNamesIn } from "../src/providers/repositories";
import type { UsageMetric, UsageSnapshot } from "../src/types";

/**
 * Fixtures reproduce the account measured on 2026-08-09, recorded in
 * docs/v3/v3.16/development/github-entitlement-probe.md. Real figures are used
 * rather than round numbers so a regression shows up as a discrepancy against a
 * documented observation rather than against an invented one.
 */

function line(overrides: Partial<UsageLineItem> = {}): UsageLineItem {
  return {
    date: "2026-07-01",
    product: "Actions",
    sku: "Actions Linux",
    unitType: "minutes",
    quantity: 10,
    pricePerUnit: 0.006,
    grossAmount: 0.06,
    discountAmount: 0.06,
    netAmount: 0,
    repositoryName: "Nexus-AI",
    ...overrides
  };
}

const VISIBILITY: VisibilityMap = { "Nexus-AI": "private", "Nexus-Hub": "public" };

describe("drawdown weighting", () => {
  it("weights Windows and macOS above Linux", () => {
    expect(OS_DRAWDOWN_WEIGHTS).toEqual({ linux: 1, windows: 2, macos: 10 });
  });

  it("reproduces the July 2026 measurement that falsified unweighted drawdown", () => {
    // July private usage: 1352.666666667 Linux + 195.6 Windows + 36 macOS. Unweighted
    // that is 1584.27, and GitHub's panel showed 2,000 of 2,000 consumed - saturated,
    // so the true drawdown was at least 2,000. A model predicting 1,584 cannot produce
    // a number that is at least 2,000, which is what killed the unweighted candidate.
    const july = [
      line({ sku: "Actions Linux", quantity: 1352.666666667 }),
      line({ sku: "Actions Windows", quantity: 195.6 }),
      line({ sku: "Actions macOS 3-core", quantity: 36 }),
      line({ sku: "Actions Linux", quantity: 92, repositoryName: "Nexus-Hub" })
    ];
    const result = computeDrawdownMinutes(july, VISIBILITY);
    const unweighted = 1352.666666667 + 195.6 + 36;
    expect(unweighted).toBeLessThan(2000);
    expect(result.minutes).toBeCloseTo(2103.866666667, 6);
    expect(result.minutes).toBeGreaterThan(2000);
    expect(result.usedWeighting).toBe(true);
  });

  it("excludes public-repository usage, which is free and never draws down", () => {
    const result = computeDrawdownMinutes(
      [line({ quantity: 120 }), line({ quantity: 1163, repositoryName: "Nexus-Hub" })],
      VISIBILITY
    );
    expect(result.minutes).toBe(120);
  });

  it("excludes self-hosted and larger runners", () => {
    const result = computeDrawdownMinutes(
      [
        line({ quantity: 100 }),
        line({ sku: "Actions Self Hosted", quantity: 50 }),
        line({ sku: "Actions Linux 16-core", quantity: 25 })
      ],
      VISIBILITY
    );
    expect(result.minutes).toBe(100);
  });

  it("treats an unclassifiable runner as unresolved rather than weighting it as Linux", () => {
    // Weighting an unknown SKU as Linux would understate a macOS runner tenfold.
    const result = computeDrawdownMinutes([line({ sku: "Actions Future Runner", quantity: 60 })], VISIBILITY);
    expect(result.minutes).toBe(0);
    expect(result.unresolvedRepositories).toContain("Actions Future Runner");
  });

  it("returns null when NO repository could be resolved, distinguishing failure from genuine zero", () => {
    const result = computeDrawdownMinutes([line({ quantity: 100 })], {});
    expect(result.minutes).toBeNull();
    expect(result.unresolvedRepositories).toEqual(["Nexus-AI"]);
  });

  it("excludes an individually unresolved repository, understating rather than overstating", () => {
    const result = computeDrawdownMinutes(
      [line({ quantity: 100 }), line({ quantity: 900, repositoryName: "Mystery" })],
      VISIBILITY
    );
    expect(result.minutes).toBe(100);
    expect(result.unresolvedRepositories).toEqual(["Mystery"]);
  });
});

describe("storage unit conversion", () => {
  it("converts GigabyteHours to GB-months by dividing by the hours in the month", () => {
    expect(gigabyteHoursToGigabyteMonths(720, 720)).toBe(1);
    expect(gigabyteHoursToGigabyteMonths(0, 744)).toBe(0);
  });

  it("reproduces both real observations, one under the allowance and one over", () => {
    // August: 64.567691147 GB-hours over a 744-hour month displayed as "0 GB used"
    // against 0.5 GB included. July: 432.30548267 over the same month length showed
    // as saturated. Both directions matter - a conversion that only matches the small
    // case could be off by a constant factor and never show it.
    expect(gigabyteHoursToGigabyteMonths(64.567691147, 744)).toBeCloseTo(0.0868, 4);
    expect(gigabyteHoursToGigabyteMonths(432.30548267, 744)).toBeCloseTo(0.5811, 4);
    expect(gigabyteHoursToGigabyteMonths(432.30548267, 744)!).toBeGreaterThan(0.5);
  });

  it("counts the hours in each UTC month correctly, including February", () => {
    expect(hoursInUtcMonth(Date.UTC(2026, 7, 15))).toBe(744);
    expect(hoursInUtcMonth(Date.UTC(2026, 5, 15))).toBe(720);
    expect(hoursInUtcMonth(Date.UTC(2026, 1, 15))).toBe(672);
  });

  it("refuses an invalid divisor rather than returning Infinity", () => {
    expect(gigabyteHoursToGigabyteMonths(100, 0)).toBeNull();
    expect(gigabyteHoursToGigabyteMonths(Number.NaN, 744)).toBeNull();
  });
});

describe("plan entitlements", () => {
  it("matches GitHub's published per-plan figures", () => {
    expect(PLAN_ENTITLEMENTS.free).toEqual({ actionsMinutes: 2_000, actionsStorageGb: 0.5 });
    expect(PLAN_ENTITLEMENTS.pro.actionsMinutes).toBe(3_000);
    expect(PLAN_ENTITLEMENTS.enterprise.actionsMinutes).toBe(50_000);
  });

  it("returns null for an unrecognized plan and NEVER falls back to Free", () => {
    // Reporting a 2,000-minute allowance to an Enterprise account would be wrong in
    // the most expensive direction.
    expect(resolvePlan("enterprise_cloud_v2")).toBeNull();
    expect(entitlementFor("enterprise_cloud_v2")).toBeNull();
    expect(entitlementFor(undefined)).toBeNull();
    expect(entitlementFor(42)).toBeNull();
  });

  it("treats Copilot as having no included allowance", () => {
    expect(PRODUCTS_WITHOUT_ALLOWANCE.has("copilot-ai-credits")).toBe(true);
    expect(PRODUCTS_WITHOUT_ALLOWANCE.has("actions-minutes")).toBe(false);
  });
});

function metric(kind: UsageMetric["kind"], unit: string, used: number, breakdowns: UsageMetric["breakdowns"] = []): UsageMetric {
  return {
    kind, unit, used, drawdown: null, drawdownBasis: "unavailable", allowance: null,
    allowanceSource: "unknown", allowanceState: "unknown", percentage: null,
    reset: null, breakdowns, grossAmount: null, discountAmount: null, netAmount: null
  };
}

function snapshotFixture(): UsageSnapshot {
  return {
    owner: { scope: "user", name: "bendourthe" },
    periodStart: Date.UTC(2026, 7, 1),
    periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: Date.UTC(2026, 7, 9),
    source: "api",
    stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 0),
    actionsMinutes: metric("actions-minutes", "minutes", 1287, [
      { product: "Actions", sku: "Actions Linux", unit: "minutes", grossQuantity: 120, discountQuantity: null, netQuantity: null, grossAmount: null, discountAmount: null, netAmount: null, repositoryName: "Nexus-AI" },
      { product: "Actions", sku: "Actions Windows", unit: "minutes", grossQuantity: 4, discountQuantity: null, netQuantity: null, grossAmount: null, discountAmount: null, netAmount: null, repositoryName: "Nexus-AI" },
      { product: "Actions", sku: "Actions Linux", unit: "minutes", grossQuantity: 1163, discountQuantity: null, netQuantity: null, grossAmount: null, discountAmount: null, netAmount: null, repositoryName: "Nexus-Hub" }
    ]),
    actionsStorage: metric("actions-storage", "gigabyte-hours", 64.567691147)
  };
}

describe("snapshot enrichment", () => {
  it("produces a percentage from the drawdown, not from gross consumption", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: VISIBILITY, planName: "free" });
    // Gross is 1,287 of 2,000 = 64%. The drawdown is 120 Linux + 4 Windows x2 = 128.
    expect(snapshot.actionsMinutes.used).toBe(1287);
    expect(snapshot.actionsMinutes.drawdown).toBe(128);
    expect(snapshot.actionsMinutes.percentage).toBeCloseTo(6.4, 5);
    expect(snapshot.actionsMinutes.allowanceState).toBe("verified");
    expect(snapshot.actionsMinutes.allowanceSource).toBe("plan-table");
  });

  it("converts storage into GB and compares it against the GB entitlement", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: VISIBILITY, planName: "free" });
    expect(snapshot.actionsStorage.unit).toBe("gigabytes");
    expect(snapshot.actionsStorage.used).toBeCloseTo(0.0868, 4);
    expect(snapshot.actionsStorage.allowance).toBe(0.5);
    expect(snapshot.actionsStorage.percentage).toBeCloseTo(17.36, 2);
  });

  it("marks Copilot as having no allowance rather than leaving it blank", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: VISIBILITY, planName: "free" });
    expect(snapshot.copilot.allowanceState).toBe("none");
    expect(snapshot.copilot.percentage).toBeNull();
  });

  it("withholds every percentage when the plan cannot be resolved", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: VISIBILITY, planName: "mystery-plan" });
    expect(snapshot.actionsMinutes.percentage).toBeNull();
    expect(snapshot.actionsMinutes.allowanceState).toBe("unknown");
  });

  it("lets a manual override replace the plan-derived denominator", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), {
      visibility: VISIBILITY,
      planName: "free",
      manualAllowances: { "actions-minutes": { value: 3000, unit: "minutes" } }
    });
    expect(snapshot.actionsMinutes.allowance).toBe(3000);
    expect(snapshot.actionsMinutes.allowanceSource).toBe("manual");
  });

  it("withholds a percentage when visibility could not be resolved at all", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: {}, planName: "free" });
    expect(snapshot.actionsMinutes.drawdown).toBeNull();
    expect(snapshot.actionsMinutes.percentage).toBeNull();
  });

  it("leaves a non-GigabyteHours storage unit unconverted rather than guessing", () => {
    const base = snapshotFixture();
    const odd = { ...base, actionsStorage: metric("actions-storage", "terabytes", 5) };
    expect(storageGigabyteMonths(odd.actionsStorage, odd.periodStart)).toBeNull();
  });

  it("states provenance so a derived figure is not mistaken for GitHub's own", () => {
    const { snapshot } = enrichSnapshot(snapshotFixture(), { visibility: VISIBILITY, planName: "free" });
    expect(describeAllowanceProvenance(snapshot.actionsMinutes, "free")).toContain("not read from your account");
  });
});

describe("repository lookups", () => {
  const ok = (value: unknown) => Promise.resolve({ ok: true as const, value });

  it("caches visibility so a repeating refresh does not re-request it", async () => {
    let calls = 0;
    const cache = new RepositoryVisibilityCache((path) => { calls += 1; return ok({ private: path.includes("AI") }); });
    await cache.resolve(["Nexus-AI", "Nexus-Hub"], { token: "t", owner: "bendourthe" });
    await cache.resolve(["Nexus-AI", "Nexus-Hub"], { token: "t", owner: "bendourthe" });
    expect(calls).toBe(2);
    expect(cache.snapshot()).toEqual({ "Nexus-AI": "private", "Nexus-Hub": "public" });
  });

  it("bounds the fan-out so a many-repository month cannot exhaust the rate limit", async () => {
    let calls = 0;
    const cache = new RepositoryVisibilityCache(() => { calls += 1; return ok({ private: true }); }, 3);
    const names = Array.from({ length: 20 }, (_, index) => `repo-${index}`);
    const visibility = await cache.resolve(names, { token: "t", owner: "bendourthe" });
    expect(calls).toBe(3);
    expect(Object.keys(visibility)).toHaveLength(3);
  });

  it("does not cache a failed lookup, so one bad refresh is not permanent", async () => {
    let attempt = 0;
    const cache = new RepositoryVisibilityCache(() => {
      attempt += 1;
      return attempt === 1 ? Promise.resolve({ ok: false as const, status: 404 }) : ok({ private: true });
    });
    await cache.resolve(["Nexus-AI"], { token: "t", owner: "bendourthe" });
    expect(cache.get("Nexus-AI")).toBeUndefined();
    await cache.resolve(["Nexus-AI"], { token: "t", owner: "bendourthe" });
    expect(cache.get("Nexus-AI")).toBe("private");
  });

  it("reads only the plan name from the user endpoint", async () => {
    const plan = await fetchAccountPlanName(() => ok({ plan: { name: "free" } }), "t");
    expect(plan).toBe("free");
    expect(await fetchAccountPlanName(() => Promise.resolve({ ok: false as const, status: 403 }), "t")).toBeNull();
    expect(await fetchAccountPlanName(() => ok({}), "t")).toBeNull();
  });

  it("collects distinct repository names, skipping nulls", () => {
    expect(repositoryNamesIn([
      { repositoryName: "a" }, { repositoryName: "a" }, { repositoryName: null }, { repositoryName: "b" }
    ])).toEqual(["a", "b"]);
  });
});

describe("tolerance for snapshots cached by an older version", () => {
  /**
   * The v3.16.3 absence-tolerance class, pinned once for the whole pipeline.
   *
   * It has bitten three times: a NaN drawdown rendered in the panel (Phase 2), a
   * missing metric crashing the hover (Phase 5), and a missing repositoryName
   * slipping past a `!== null` guard before throwing on `.length` (Phase 6). The
   * root cause is always the same - cached state outlives the version that wrote
   * it - so this fixture is deliberately shaped like a 0.1.0 snapshot: no drawdown,
   * no drawdownBasis, no allowanceState, and breakdowns with no repositoryName.
   */
  function legacySnapshot(): UsageSnapshot {
    const legacyMetric = (kind: UsageMetric["kind"], unit: string, used: number): UsageMetric =>
      ({
        kind, unit, used, allowance: null, allowanceSource: "unknown", percentage: null,
        reset: null, grossAmount: null, discountAmount: null, netAmount: null,
        breakdowns: [{ product: "Actions", sku: "Actions Linux", unit, grossQuantity: used, discountQuantity: null, netQuantity: null, grossAmount: null, discountAmount: null, netAmount: null }]
      } as unknown as UsageMetric);
    return {
      owner: { scope: "user", name: "bendourthe" },
      periodStart: Date.UTC(2026, 7, 1), periodEnd: Date.UTC(2026, 8, 1),
      fetchedAt: Date.UTC(2026, 7, 9), source: "cache", stale: true,
      copilot: legacyMetric("copilot-ai-credits", "ai-credits", 40),
      actionsMinutes: legacyMetric("actions-minutes", "minutes", 1287),
      actionsStorage: legacyMetric("actions-storage", "gigabyte-hours", 64.57)
    };
  }

  it("collects no repository names from breakdowns that never had the field", () => {
    // `undefined` passes a `!== null` check and then throws on `.length`.
    expect(() => repositoryNamesIn(legacySnapshot().actionsMinutes.breakdowns)).not.toThrow();
    expect(repositoryNamesIn(legacySnapshot().actionsMinutes.breakdowns)).toEqual([]);
  });

  it("enriches a legacy snapshot without throwing, and withholds every percentage", () => {
    const { snapshot } = enrichSnapshot(legacySnapshot(), { visibility: VISIBILITY, planName: "free" });
    // No repositoryName means nothing can be attributed, so the drawdown is unknown
    // and no bar may render - the safe direction.
    expect(snapshot.actionsMinutes.drawdown).toBeNull();
    expect(snapshot.actionsMinutes.percentage).toBeNull();
    expect(snapshot.actionsMinutes.allowanceState).toBe("unknown");
  });

  it("still converts storage on a legacy snapshot, since that needs no attribution", () => {
    const { snapshot } = enrichSnapshot(legacySnapshot(), { visibility: VISIBILITY, planName: "free" });
    expect(snapshot.actionsStorage.used).toBeCloseTo(0.0868, 4);
    expect(snapshot.actionsStorage.percentage).toBeCloseTo(17.36, 2);
  });
});
