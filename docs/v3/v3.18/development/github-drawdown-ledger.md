# GitHub Actions Drawdown Reconciliation Ledger

One row per observed month, with the verdict its numbers actually support. This file exists because the Actions drawdown model was revised three times (1:1, then Windows 2x / macOS 10x, then 1:1 again) and each revision argued with the previous author rather than with accumulated evidence. A fourth revision has to argue with this table.

Rows are produced by `extensions/github-usage-monitor/scripts/reconcile-drawdown.js`, which prints a paste-ready row along with the derived Linux reference rate and the per-item weights it produced, so a row can be checked rather than trusted. Verdicts come from `src/providers/reconciliation.ts`, which is pure and testable.

## How to read a verdict

Three verdicts, and the difference between them is the entire point of the file.

- **refutes** - the observation is incompatible with the model. One refutation stands against any number of supporting months.
- **supports** - the observation is compatible with the model **and could have been otherwise**. Both halves are required.
- **non-discriminating** - the observation agrees with the model and with every rival, so it is not evidence for any of them.

A month is non-discriminating for either of two reasons:

1. **Saturation.** A meter pinned at its cap reports only "at least the allowance". Every model predicting at or above the cap produces the identical display, so a saturated month can refute a model that predicts *below* the cap but can never confirm one that predicts above it.
2. **Linux dominance.** Candidate weightings differ only on non-Linux items. When the non-Linux share of predicted drawdown falls below `DISCRIMINATING_NON_LINUX_SHARE` (15%, declared in `reconciliation.ts` with its justification), every candidate lands inside tolerance and the month proves nothing regardless of how well the numbers match.

Treating either case as agreement is how the all-1 table acquired authority it had not earned. The classifier refuses to do it, and the refusal is tested in `test/reconciliation.test.ts`.

## Ledger

The model under test is the one shipped in extension 0.4.0: `weight(item) = item.pricePerUnit / the standard Linux rate observed in the same period`. Predicted values below are that model's output.

| Month | Predicted | Displayed | Saturated | Weighted mix (Linux / Win / macOS) | Non-Linux share | Verdict | Observed |
|---|---|---|---|---|---|---|---|
| 2026-07 | 2,051 | 2,000 | yes | 1,353 / 326 / 372 | 34.0% | non-discriminating | 2026-08-19, jobs API |
| 2026-08 (1-10) | 126.7 | 126.7 | no | 126 / 7 / 0 | 5.3% | non-discriminating | 2026-08-10, billing page |
| 2026-08 (full) | 2,595 | 2,000 | yes | 1,457 / 312 / 826 | 43.8% | non-discriminating | 2026-08-19, jobs API |

### What each row establishes

**2026-07** and **2026-08 (full)** both refute the **unweighted** model. Unweighted, July predicts 1,584 and August predicts 1,724, and a model predicting below a saturated 2,000-minute cap cannot produce a pinned meter. Neither month *confirms* the price-derived model, because both are saturated. They are recorded as non-discriminating with respect to the shipped model and as refutations with respect to its predecessor, which is the honest reading of a lower bound.

**2026-08 (1-10)** is the observation most likely to be misread. It matched the unweighted prediction almost exactly (126.7 against a displayed 126.7) and was cited in `test/enrich.test.ts` as support for counting every runner at face value. It is not support for anything: at a 5.3% non-Linux share, the price-derived model predicts 126.7 as well, and so does the legacy 2x / 10x model. Three candidates, one answer, zero discrimination.

## What would falsify the current model

**An unsaturated month whose non-Linux share exceeds 15% and whose displayed value matches unweighted raw minutes.** That month would show that GitHub counts every runner at face value after all, and the price-derived weighting would be refuted rather than merely re-tuned.

Two weaker falsifiers are also worth recording:

- **An unsaturated, genuinely mixed month whose displayed value sits outside the 1% tolerance in either direction** refutes the model without necessarily endorsing a specific rival.
- **A GitHub billing endpoint that returns the consumed included minutes directly** would make the entire reconstruction unnecessary. The legacy product-specific endpoints that returned `included_minutes` were closed down in September 2025 and now return 404/410; if one returns again, read it instead of reconstructing.

## What this ledger cannot settle

Price-ratio weighting (Windows 1.67x, macOS 10.33x, from the 2026 rates) and the legacy published multipliers (2x, 10x, from the pre-2026 rates) differ by about 0.3% of the weighted total. **No saturated month can separate them**, and every month on this account so far is either saturated or Linux-dominated. The shipped model picks the mechanism over the snapshot on the grounds that the mechanism tracks price changes and a snapshot demonstrably does not, not on the grounds that the data distinguishes them. That is recorded as a known gap rather than as a settled question.

## Adding a row

```bash
cd extensions/github-usage-monitor
npm run compile
node scripts/reconcile-drawdown.js \
  --level user --name <owner> \
  --year 2026 --month 9 \
  --displayed-minutes <from the billing page> \
  --displayed-allowance 2000
```

Repository names are hashed by default; `--reveal-repos` prints them. The `--displayed-*` figures must come from GitHub's billing page for the **same** period the run queried - comparing one month's API data against another month's screenshot produces a mismatch that looks like a formula defect and is not one. That has already happened once.

## Related

- [`docs/policy/github-actions-minute-consumption.md`](../../../policy/github-actions-minute-consumption.md) - when Actions minutes are consumed at all
- [`extensions/github-usage-monitor/src/providers/reconciliation.ts`](../../../../extensions/github-usage-monitor/src/providers/reconciliation.ts) - the classifier and its declared constants
- [`docs/v3/v3.16/development/github-entitlement-probe.md`](../../v3.16/development/github-entitlement-probe.md) - the earlier probe findings this ledger supersedes for weighting questions
