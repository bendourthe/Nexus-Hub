# Session History - GitHub Usage Monitor Accuracy Phase 2: Price-Derived Drawdown

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 2 - Price-derived drawdown
**Environment**: Windows 11, Git Bash, Node with `vitest` 4.1.10
**Outcome**: The drawdown weight is derived per line item from that item's own `pricePerUnit` relative to the standard Linux rate observed in the same payload. There is no multiplier table left to go stale, and exhaustion now renders as exhaustion rather than as a meter stalled below the cap.

## 1. Starting State

- **Starting commit**: `2a667599` (Phase 1: warning-surface parity)
- **Extension version**: 0.3.3
- **Routing decision**: the plan recorded `frontier / high`. Implementation ran on Opus 5, one tier below the recommendation. The delta was surfaced rather than silently accepted; the phase was built with the plan's own degenerate-case enumeration treated as a checklist, which is the mitigation the plan itself names.

## 2. Why the Table Had To Go Rather Than Be Corrected Again

This figure had been revised three times: 1:1, then Windows 2x / macOS 10x, then 1:1 again. Each revision hardcoded a different constant and each was defensible on the evidence available at the time. The pattern, not any one value, was the defect.

GitHub's published multipliers were never an independent taxonomy. `1x / 2x / 10x` are exactly the pre-2026 per-minute price ratios: $0.008, $0.016, $0.080. On 2026-01-01 GitHub cut runner prices to $0.006, $0.010, $0.062, so the same mechanism silently became `1x / 1.67x / 10.33x`. Any hardcoded table is a snapshot of a price list that has already moved once.

`pricePerUnit` is returned on every `/settings/billing/usage` line item and was documented in this repo's own data contract, but the normalizer never parsed it and `lineItemsOf` hardcoded `null`. The fix is to stop storing the derived value and start deriving it.

## 3. What Changed

| File | Change |
|---|---|
| `src/types.ts` | `SkuUsageBreakdown.pricePerUnit: number \| null`, documented as unknown-never-zero. |
| `src/providers/normalizer.ts` | `parseItems` parses `pricePerUnit` through the existing `optionalNumber`, which yields `null` for an absent field. |
| `src/providers/enrich.ts` | `lineItemsOf` passes `row.pricePerUnit ?? null`. `EnrichmentResult.usedWeighting` becomes `appliedWeights` plus `linuxReferenceRate`. |
| `src/providers/drawdown.ts` | `OS_DRAWDOWN_WEIGHTS` deleted. New `PUBLISHED_LINUX_RATE_USD_PER_MINUTE` and `resolveLinuxReferenceRate(items)`. `computeDrawdownMinutes` derives `weight = price / referenceRate`. |
| `src/providers/allowances.ts` | New `isAllowanceExhausted(metric)` predicate. |
| `src/dashboardPanel.ts` | Exhausted metrics render a full bar in the critical style with the true percentage. |
| `src/recommendations.ts` | An exhausted Actions allowance gets consequence-bearing text. |

## 4. The Degenerate Cases, Each Handled Explicitly

The plan enumerated five ways a price-derived weight can go wrong. Each is handled by a named decision rather than by a default:

| Case | Handling | Why not the obvious alternative |
|---|---|---|
| No Linux item in the period | Fall back to `PUBLISHED_LINUX_RATE_USD_PER_MINUTE` and report `source: "published-fallback"` | Falling back to `1.0` would make Windows the implicit baseline and understate by 40% |
| Several Linux rates in one period | Take the **highest** qualifying rate | Larger runners are already excluded, so the standard set's ceiling **is** the 2-core baseline. `min` would pick a sub-2-core variant and inflate every other weight by the ratio between them |
| `pricePerUnit` null or non-positive on a qualifying item | Add to the unresolved set, so the whole figure reads unknown | Contributing zero shrinks the drawdown silently while the meter still looks confident |
| Larger and self-hosted runners | Excluded by `classifySku` **before** weighting | Price-weighting a larger runner is a category error: included minutes cannot be spent on one at all |
| A 0.3.x cached snapshot with no prices | Deserializes to `null`, so the metric reads unknown until the next refresh | Letting `undefined` collapse to `0` renders a confident 0% against a 2,000-minute allowance |

## 5. `usedWeighting` Was Replaced, Not Renamed

The old boolean asked "did any weight differ from 1". Once weights are derived, that question has no stable meaning - a single-rate Linux month and a hardcoded-1 month are indistinguishable through it. `appliedWeights: number[]` survives the change and says strictly more: `[1]` is a single-rate period, `[1, 1.67, 10.33]` names the mix. `linuxReferenceRate` rides alongside so the panel can label which denominator produced them, which Phase 4 consumes.

## 6. Exhaustion Is a Predicate, Not a Fourth State

`AllowanceState` answers "is a percentage derivable at all", and every guard in the codebase reads it that way. Adding an `exhausted` member would have made every existing `allowanceState === "verified"` check silently wrong at exactly the moment the number matters most. `isAllowanceExhausted(metric)` is derived instead.

The bar **width** is clamped to 100% because a 130% width is a layout bug. The **number** is not clamped. The reported symptom was a meter reading 58% while GitHub showed 2,000 of 2,000, and clamping the figure would tell the same kind of lie inverted.

## 7. Verification

| Gate | Result |
|---|---|
| `npm run compile` | Pass |
| `npm test` | 448 tests, 28 files, all pass (up from 439) |
| `npm run test:coverage` | Statements 82.58%, branches 79.16%, lines 85.49% |
| Measured August fixture | 2,595 weighted minutes, above the 2,000 cap, weights `[1, 1.67, 10.33]` |
| Legacy-snapshot regression | Breakdowns without `pricePerUnit` yield `drawdown: null`, `allowanceState: "unknown"` |
| `scripts/reconcile-drawdown.js` | Parses; imports no removed symbol |
| CI | No-op. `vitest run` discovers the new cases in existing files; the path filter already covers them |

## 8. What This Does Not Settle

Price-ratio weighting (1.67x / 10.33x) and the legacy published multipliers (2x / 10x) differ by 0.3%, and no **saturated** month can separate them - a saturated meter reports only "at least the allowance". This release picks the mechanism over the snapshot on the grounds that the mechanism tracks price changes and the snapshot demonstrably does not. Phase 3 encodes that residual uncertainty as a falsifier rather than leaving it as an argument.

## 9. Next Step

Phase 3: the saturation-aware reconciliation ledger, so a fourth revision has to argue with accumulated evidence rather than with the previous author.
