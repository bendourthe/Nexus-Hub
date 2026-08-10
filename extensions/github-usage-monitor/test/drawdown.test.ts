import { describe, expect, it } from "vitest";
import {
  RECONCILIATION_TOLERANCE,
  breakdownByRepository,
  classifySku,
  computeCandidates,
  inventorySkus,
  reconcile,
  type UsageLineItem,
  type VisibilityMap
} from "../src/providers/drawdown";

/**
 * Fixtures reproduce the shape of the real discrepancy this phase exists to fix:
 * gross Actions minutes far exceeding the minutes GitHub counts against the
 * allowance, because public-repository usage is free and never draws down.
 */
function item(overrides: Partial<UsageLineItem> = {}): UsageLineItem {
  return {
    date: "2026-08-01",
    product: "Actions",
    sku: "Actions Linux",
    unitType: "minutes",
    quantity: 10,
    pricePerUnit: 0.008,
    grossAmount: 0.08,
    discountAmount: 0.08,
    netAmount: 0,
    repositoryName: "private-repo",
    ...overrides
  };
}

const VISIBILITY: VisibilityMap = {
  "private-repo": "private",
  "public-repo": "public",
  "unresolved-repo": "unknown"
};

describe("SKU classification", () => {
  it("recognizes each GitHub-hosted standard runner OS", () => {
    expect(classifySku("Actions Linux").os).toBe("linux");
    expect(classifySku("Actions Windows").os).toBe("windows");
    expect(classifySku("Actions macOS").os).toBe("macos");
  });

  it("marks self-hosted runners as not GitHub-hosted", () => {
    const classification = classifySku("Actions Self Hosted");
    expect(classification.githubHosted).toBe(false);
  });

  it("marks larger runners as non-standard, since included minutes cannot be used for them", () => {
    expect(classifySku("Actions Linux 16-core").standard).toBe(false);
    expect(classifySku("Actions Linux 4-core").standard).toBe(false);
    expect(classifySku("Actions Linux Advanced GPU").standard).toBe(false);
  });

  it("keeps the standard macOS runner standard despite its core count", () => {
    // Regression, observed on a real account 2026-08-09: the first rule treated any
    // N-core SKU as a larger runner, which dropped every one of that account's 111
    // macOS minutes out of the private-repository candidates without a trace.
    const classification = classifySku("Actions macOS 3-core");
    expect(classification.os).toBe("macos");
    expect(classification.standard).toBe(true);
    expect(classification.githubHosted).toBe(true);
    expect(classifySku("Actions macOS 4-core").standard).toBe(true);
    // macOS above the standard tier is still a larger runner.
    expect(classifySku("Actions macOS 12-core").standard).toBe(false);
  });

  it("classifies BOTH endpoint vocabularies identically", () => {
    // v3.16.3 NI-3. `/settings/billing/usage` says "Actions Linux";
    // `/usage/summary` says "actions_linux". A rule written against one vocabulary
    // would silently misclassify the other endpoint's items, and a misclassified
    // runner is dropped from the drawdown without a trace.
    const pairs: ReadonlyArray<readonly [string, string]> = [
      ["Actions Linux", "actions_linux"],
      ["Actions Windows", "actions_windows"],
      ["Actions macOS 3-core", "actions_macos"]
    ];
    for (const [usageForm, summaryForm] of pairs) {
      const fromUsage = classifySku(usageForm);
      const fromSummary = classifySku(summaryForm);
      expect(fromSummary.os).toBe(fromUsage.os);
      expect(fromSummary.githubHosted).toBe(fromUsage.githubHosted);
      expect(fromSummary.unrecognized).toBe(false);
    }
    // Storage SKUs are not runners in either vocabulary.
    for (const storage of ["Actions storage", "actions_storage", "Git LFS storage", "git_lfs_storage"]) {
      expect(classifySku(storage).unrecognized).toBe(true);
    }
    // Self-hosted must be recognized whichever separator the endpoint uses.
    for (const selfHosted of ["Actions Self Hosted", "actions_self_hosted", "actions-self-hosted"]) {
      expect(classifySku(selfHosted).githubHosted).toBe(false);
    }
  });

  it("uses the real SKU strings observed on a live account", () => {
    // Ground truth from the 2026-08 probe run, so the rules are pinned to strings
    // GitHub actually emits rather than to strings I guessed at.
    expect(classifySku("Actions Linux")).toMatchObject({ os: "linux", standard: true, githubHosted: true });
    expect(classifySku("Actions Windows")).toMatchObject({ os: "windows", standard: true, githubHosted: true });
    expect(classifySku("Actions macOS 3-core")).toMatchObject({ os: "macos", standard: true, githubHosted: true });
    // Storage SKUs are not runners at all and must not masquerade as one.
    expect(classifySku("Actions storage").unrecognized).toBe(true);
    expect(classifySku("Git LFS storage").unrecognized).toBe(true);
  });

  it("reports an unfamiliar SKU as unrecognized rather than guessing Linux", () => {
    // Guessing Linux is precisely what would make a wrong total look right on a
    // Linux-heavy account, so the default must be unknown.
    const classification = classifySku("Actions Some Future Runner");
    expect(classification.os).toBe("unknown");
    expect(classification.unrecognized).toBe(true);
    expect(classification.githubHosted).toBe("unknown");
  });
});

describe("candidate reconstructions", () => {
  const items = [
    item({ repositoryName: "private-repo", quantity: 100 }),
    item({ repositoryName: "public-repo", quantity: 880 }),
    item({ repositoryName: "private-repo", sku: "Actions Self Hosted", quantity: 15 }),
    item({ repositoryName: "private-repo", sku: "Actions Linux 16-core", quantity: 8 }),
    item({ repositoryName: "unresolved-repo", quantity: 40 }),
    item({ product: "Actions", sku: "Actions Storage", unitType: "GigabyteHours", quantity: 63.92, discountAmount: 0.2 })
  ];

  it("keeps gross as the control and it overstates, exactly as observed in the wild", () => {
    const candidates = computeCandidates(items, VISIBILITY);
    // Storage is excluded from the minute total because its unit is not minutes.
    expect(candidates.grossMinutes.value).toBe(1043);
  });

  it("excludes public-repository usage from the private candidate", () => {
    const candidates = computeCandidates(items, VISIBILITY);
    // 100 qualifying; the 880 public, 15 self-hosted, 8 larger-runner, and 40
    // unresolved items are all excluded.
    expect(candidates.privateHostedStandardMinutes.value).toBe(100);
  });

  it("excludes a repository whose visibility could not be resolved, understating rather than overstating", () => {
    const candidates = computeCandidates(items, {});
    expect(candidates.privateHostedStandardMinutes.value).toBe(0);
  });

  it("separates the Linux-only subset, which needs no undocumented conversion", () => {
    const withWindows = [...items, item({ repositoryName: "private-repo", sku: "Actions Windows", quantity: 20 })];
    const candidates = computeCandidates(withWindows, VISIBILITY);
    expect(candidates.privateHostedStandardMinutes.value).toBe(120);
    expect(candidates.privateHostedStandardLinuxMinutes.value).toBe(100);
  });

  it("computes the monetary candidates over the right item sets", () => {
    const candidates = computeCandidates(items, VISIBILITY);
    // Actions minutes items only, in dollars.
    expect(candidates.actionsDiscountUsd.unit).toBe("usd");
    expect(candidates.actionsDiscountUsd.value).toBeCloseTo(0.08 * 5, 5);
    // Every product, so storage's discount joins in.
    expect(candidates.allProductsDiscountUsd.value).toBeCloseTo(0.08 * 5 + 0.2, 5);
  });

  it("converts discount dollars back to minutes at each item's own rate", () => {
    const candidates = computeCandidates(items, VISIBILITY);
    expect(candidates.actionsDiscountDerivedMinutes.unit).toBe("minutes");
    expect(candidates.actionsDiscountDerivedMinutes.value).toBeCloseTo(50, 5);
  });

  it("skips an item with no price, rather than dividing by zero", () => {
    const candidates = computeCandidates([item({ pricePerUnit: 0, discountAmount: 5 })], VISIBILITY);
    expect(candidates.actionsDiscountDerivedMinutes.value).toBe(0);
    expect(candidates.actionsDiscountDerivedMinutes.itemCount).toBe(0);
  });

  it("carries a caveat on every candidate, so no figure is presented bare", () => {
    const candidates = computeCandidates(items, VISIBILITY);
    for (const candidate of Object.values(candidates)) {
      expect(candidate.caveat.length).toBeGreaterThan(0);
    }
  });
});

describe("per-repository breakdown", () => {
  it("splits minutes, list price, discount, and net by repository and SKU", () => {
    const breakdown = breakdownByRepository(
      [
        item({ repositoryName: "public-repo", sku: "Actions Linux", quantity: 100, grossAmount: 0.6, discountAmount: 0.6, netAmount: 0 }),
        item({ repositoryName: "public-repo", sku: "Actions Windows", quantity: 50, grossAmount: 0.5, discountAmount: 0.5, netAmount: 0 }),
        item({ repositoryName: "private-repo", sku: "Actions Linux", quantity: 20, grossAmount: 0.12, discountAmount: 0.12, netAmount: 0 })
      ],
      VISIBILITY
    );
    expect(breakdown[0]?.repositoryName).toBe("public-repo");
    expect(breakdown[0]?.visibility).toBe("public");
    expect(breakdown[0]?.totalMinutes).toBe(150);
    expect(breakdown[0]?.minutesBySku).toEqual({ "Actions Linux": 100, "Actions Windows": 50 });
    expect(breakdown[0]?.listPriceUsd).toBeCloseTo(1.1, 5);
    expect(breakdown[1]?.visibility).toBe("private");
  });

  it("buckets an item with no repository rather than dropping it", () => {
    const breakdown = breakdownByRepository([item({ repositoryName: null })], VISIBILITY);
    expect(breakdown[0]?.repositoryName).toBe("(no repository reported)");
    expect(breakdown[0]?.visibility).toBe("unknown");
  });
});

describe("SKU inventory", () => {
  it("aggregates distinct product/sku/unit triples with their classification", () => {
    const observations = inventorySkus([
      item({ sku: "Actions Linux", quantity: 10 }),
      item({ sku: "Actions Linux", quantity: 5 }),
      item({ sku: "Actions Windows", quantity: 3 })
    ]);
    expect(observations).toHaveLength(2);
    const linux = observations.find((observation) => observation.sku === "Actions Linux");
    expect(linux?.itemCount).toBe(2);
    expect(linux?.totalQuantity).toBe(15);
    expect(linux?.classification.os).toBe("linux");
  });

  it("flags an unrecognized SKU so a real-world sample can replace the guess", () => {
    const observations = inventorySkus([item({ sku: "Actions Mystery" })]);
    expect(observations[0]?.classification.unrecognized).toBe(true);
  });
});

describe("reconciliation", () => {
  it("declares its tolerance as a constant rather than inline at the comparison", () => {
    expect(RECONCILIATION_TOLERANCE).toBe(0.01);
  });

  it("reconciles a candidate inside the tolerance", () => {
    const verdict = reconcile("privateHostedStandardMinutes", 119.4, 119.7);
    expect(verdict.reconciles).toBe(true);
    expect(verdict.relativeDifference).toBeLessThan(RECONCILIATION_TOLERANCE);
  });

  it("rejects the gross figure against the observed drawdown", () => {
    // The regression fixture for the defect this phase exists to fix: gross 1,003
    // against a 119.7 drawdown is an eightfold overstatement and must never pass.
    const verdict = reconcile("grossMinutes", 1003, 119.7);
    expect(verdict.reconciles).toBe(false);
    expect(verdict.relativeDifference).toBeGreaterThan(7);
  });

  it("treats a zero displayed figure as reconciling only against zero", () => {
    expect(reconcile("privateHostedStandardMinutes", 0, 0).reconciles).toBe(true);
    expect(reconcile("privateHostedStandardMinutes", 5, 0).reconciles).toBe(false);
    expect(reconcile("privateHostedStandardMinutes", 5, 0).relativeDifference).toBeNull();
  });
});
