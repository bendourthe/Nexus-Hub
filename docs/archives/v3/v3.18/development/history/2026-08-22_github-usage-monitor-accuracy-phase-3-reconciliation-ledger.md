# Session History - GitHub Usage Monitor Accuracy Phase 3: Self-Validating Reconciliation Ledger

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 3 - Self-validating reconciliation ledger
**Environment**: Windows 11, Git Bash, Node with `vitest` 4.1.10
**Outcome**: Monthly evidence is classified by a pure, tested function that refuses to treat a saturated meter or a Linux-dominated month as agreement. Three months are recorded in a committed ledger with the falsifier that would overturn the shipped model stated up front.

## 1. Starting State

- **Starting commit**: `c19970ab` (Phase 2: price-derived drawdown)
- **Routing decision**: the plan recorded `frontier / high` and flagged this as "the phase most likely to be reasoned about incorrectly". Implementation ran on Opus 5. The mitigation applied was structural rather than model-tier: the ordering of the classifier's tests was fixed before any of them were written, so the trap is closed by construction rather than by care.

## 2. The Trap This Phase Exists To Close

Two prior revisions fell into the same mistake from opposite directions.

A **saturated** meter reports only "at least the allowance". Every model predicting at or above the cap produces the identical display. So a saturated month can refute a model that predicts *below* the cap, and can never confirm one that predicts above it. The 2x / 10x revision read a saturated July as confirmation.

A **Linux-dominated** month agrees with every candidate, because candidate weightings differ only on non-Linux items. The revert to all-1 read a 97%-Linux window as confirmation.

Both readings are structurally invalid, and both looked like careful empiricism at the time.

## 3. What Changed

| File | Change |
|---|---|
| `src/providers/reconciliation.ts` | New. Pure classifier over `{month, displayedValue, displayedIsSaturated, allowance, predicted, mixByOs}`. Exports `OBSERVATION_TOLERANCE`, `DISCRIMINATING_NON_LINUX_SHARE`, `classifyObservation`, `nonLinuxShare`, `summarize`. No network, no `vscode`, no configuration. |
| `test/reconciliation.test.ts` | New. Nine tests, each pinned to a real month rather than an invented one. |
| `scripts/reconcile-drawdown.js` | Prints the derived Linux reference rate, its source, every per-SKU weight, and one paste-ready ledger row classified by the new module. |
| `docs/v3/v3.18/development/github-drawdown-ledger.md` | New. Three seeded months, the reading rules, and the falsifier. |

## 4. Both Constants Were Declared Before Any Comparison

Following the `RECONCILIATION_TOLERANCE` precedent already in `drawdown.ts`:

- **`OBSERVATION_TOLERANCE = 0.01`.** Carried over unchanged: GitHub displays one decimal on a three-digit minute figure, so display rounding alone is roughly 0.4%, and per-job minute rounding covers the rest. Every structurally wrong candidate differs by tens of percent.
- **`DISCRIMINATING_NON_LINUX_SHARE = 0.15`.** New. Candidate weightings differ only on non-Linux items, so a month's discriminating power is bounded by the non-Linux share times the spread between candidates. At 15% the unweighted model is off by more than the tolerance and is testable; below it, the month agrees with everything.

The Aug 1-10 window sits at roughly 5%. It was cited as support for the unweighted model. Under the declared bar it is not support for anything.

## 5. The Test Ordering Is the Mechanism

`classifyObservation` runs its checks in a fixed order, and the order is load-bearing:

1. **Saturated?** Predicting below the cap is refutation. Predicting at or above it is `non-discriminating`, never `supports`.
2. **Too Linux-dominated?** `non-discriminating`, **before** the tolerance comparison runs, precisely so a good numeric match cannot be mistaken for evidence.
3. Only then does an unsaturated, genuinely mixed month get compared on the numbers.

`summarize` completes the shape: one `refutes` is decisive, and an absence of refutation yields `supported` only if at least one month actually discriminated. Otherwise the standing verdict is `untested` - the honest and common state for a Linux-dominated account, and the state a table acquires false authority by mislabelling as "supported".

## 6. The Ledger Records Three Months, and None of Them Confirm the Shipped Model

| Month | Verdict for the shipped model | What it does establish |
|---|---|---|
| 2026-07 (saturated) | non-discriminating | Refutes the **unweighted** model: 1,584 predicted below a pinned 2,000 cap |
| 2026-08 1-10 (unsaturated, 5.3% non-Linux) | non-discriminating | Nothing. Three candidates, one answer |
| 2026-08 full (saturated) | non-discriminating | Refutes the **unweighted** model: 1,724 below a pinned 2,000 cap |

That is the accurate state of the evidence and the ledger says so plainly. The price-derived model is adopted because the mechanism tracks price changes and a hardcoded snapshot demonstrably does not, **not** because the data distinguishes it from the legacy 2x / 10x table. The two differ by 0.3%, and no saturated month can separate them.

## 7. Verification

| Gate | Result |
|---|---|
| `npm run compile` | Pass |
| `npm test` | 457 tests, 29 files, all pass (up from 448) |
| `node --check scripts/reconcile-drawdown.js` | Parses |
| Classifier loaded from compiled JS | Returns `non-discriminating` for the measured August, with its reason |
| Repository hashing | On by default; `--reveal-repos` remains opt-in |
| Path reconciliation | The plan named `docs/v3/v3.17/...` from its pre-retarget life; written to `docs/v3/v3.18/...` per the plan header's own instruction |

## 8. Next Step

Phase 4: surface the public/private split and the numerator's provenance in the panel, so a user can see why 366 public-repository runs cost nothing.
