# Decision: Derive Actions drawdown weights from each line item's price

Status: implemented - shipped in extension 0.4.0, then SUPERSEDED the same day when the extension it governed was withdrawn.

> **Superseded 2026-08-22** by [`2026-08-22-withdraw-the-github-usage-monitor.md`](2026-08-22-withdraw-the-github-usage-monitor.md). The mechanism below no longer ships. The record is retained rather than deleted because its analysis remains correct and is part of the evidence base for the withdrawal: the weighting was right, and GitHub's own 2026 pricing page has since confirmed it in writing ("consume available usage based on list price"). What defeated the extension was a different input entirely - the public/private split, which needs repository visibility *at the time of use*, and which no GitHub API reports.

## Problem

The GitHub Usage Monitor reconstructs how many Actions minutes have been drawn from the included allowance, because no GitHub endpoint returns that figure. The reconstruction needs to know how fast a Windows or macOS minute is consumed relative to a Linux minute.

That number was revised three times in three releases:

| Revision | Weights | Basis | Why it was later overturned |
|---|---|---|---|
| Original | Linux 1, Windows 1, macOS 1 | No positive evidence; face value | A saturated July could not be explained by a prediction below the cap |
| v3.16.3 | 1 / 2 / 10 | GitHub's historical published multipliers, plus one saturated July | Visibility was resolved at analysis time and applied retroactively, misclassifying a then-private repository as public and manufacturing the gap the multipliers "explained" |
| v3.16.4 | 1 / 1 / 1 | Two unsaturated observations that matched raw minutes | That window was 97% Linux and could not discriminate between models at all |

Each revision was defensible on the evidence its author had. The pattern, not any single value, was the defect: **every revision hardcoded a snapshot of a price list**.

The legacy multipliers were never an independent taxonomy. `1x / 2x / 10x` are exactly the pre-2026 per-minute price ratios ($0.008, $0.016, $0.080). On 2026-01-01 GitHub cut runner prices to $0.006, $0.010, and $0.062, so the same mechanism silently became `1x / 1.67x / 10.33x`. Any table written before that date was already wrong, and any table written after it will be wrong at the next price change.

Meanwhile `pricePerUnit` is returned on every `/settings/billing/usage` line item, is documented in this repo's own data contract, and was being discarded: the normalizer never parsed it and `lineItemsOf` hardcoded `null`.

## Decision

The drawdown weight for a line item is `item.pricePerUnit / linuxReferenceRate`, where `linuxReferenceRate` is resolved once per period by `resolveLinuxReferenceRate(items)`.

- The reference rate is the **highest** qualifying standard, GitHub-hosted, Linux rate observed in the period. Larger runners are already excluded by `classifySku`, so the standard set's ceiling is the 2-core baseline; selecting by `min` would pick a sub-2-core variant and inflate every other weight by the ratio between them.
- When a period contains no Linux item to observe, the rate falls back to `PUBLISHED_LINUX_RATE_USD_PER_MINUTE` (0.006, verified 2026-08-19) and the result records that it did, so the panel can label the weaker provenance. It does **not** fall back to 1.0, which would make Windows the implicit baseline.
- Public repositories, self-hosted runners, and larger runners are excluded **before** weighting, unchanged. Price-weighting a larger runner is a category error: included minutes cannot be spent on one at all.
- A line item that passes every exclusion but carries a `null` or non-positive price joins the unresolved set, so the whole figure reads unknown. It never contributes zero.
- `OS_DRAWDOWN_WEIGHTS` is deleted as a behavioral input and retained only as a comment recording that the legacy values were price ratios.

Evidence for weighting existing at all: measured 2026-08-19 against a private repository for August 2026 via the Actions jobs API (73 runs, 527 jobs), usage was 1,457 Linux + 187 Windows + 80 macOS minutes. Unweighted that is 1,724, and GitHub's Included-usage panel showed 2,000 of 2,000 consumed. A model predicting 1,724 cannot produce a saturated 2,000-minute meter; price-weighted 2,595 can.

## Alternatives considered

**Keep the unweighted model.** Refuted by measurement. Two saturated months (July 2026 predicting 1,584, August 2026 predicting 1,724) both fall below a pinned 2,000-minute cap, and a model predicting below a saturated cap cannot produce the observed display. This is a genuine falsification, not a preference.

**Reinstate hardcoded 2x / 10x.** Fits the same data - it differs from price ratios by about 0.3% of the weighted total, and no saturated month can separate the two. Rejected because it re-freezes a price list that has already moved once. It would be correct today and wrong at the next price change, which is exactly the failure this decision exists to stop repeating. Choosing the mechanism over the snapshot is a bet on the mechanism's stability, not a claim that the data distinguishes them.

**Show an uncertainty band instead of a figure.** Honest, and unactionable. The meter's purpose is to warn before an allowance runs out; "somewhere between 86% and 130%" cannot drive a threshold crossing. Rejected in favour of a single figure that is labelled as a reconstruction, with its provenance rendered beside it and its residual uncertainty recorded in the ledger.

**Scrape `github.com/settings/billing`.** Would read GitHub's own displayed figure and remove the reconstruction entirely. Not viable: that page requires a browser session cookie, and the extension authenticates with an OAuth Bearer token, so the page is not reachable with the credential it holds. It is also an undocumented surface with no stability contract.

**Wait for a billing endpoint that returns the figure.** The legacy product-specific endpoints returning `included_minutes` were closed down in September 2025 and now return 404/410. There is nothing to wait for. If one returns, reading it should replace this reconstruction outright.

## Consequences

**The displayed percentage rises on accounts using Windows or macOS runners.** A user calibrated against 0.3.3 will see a higher number for the same usage. This is announced in the CHANGELOG leading the entry, because a correct number arriving without explanation is reported as a new bug.

**A snapshot cached by 0.3.x reads as unknown until the next refresh.** Those breakdowns carry no `pricePerUnit`, and letting `undefined` collapse to `0` would derive a zero weight and render a confident 0% against a 2,000-minute allowance. Unknown that self-heals is the safer failure.

**This decision does not grant more than it claims.** The figure is still a reconstruction. GitHub publishes no included-minute multiplier, the allowance itself remains plan-table-derived because no endpoint returns it, and price-ratio weighting cannot be separated from the legacy table by any saturated month.

**The falsifier is written down.** `docs/v3/v3.18/development/github-drawdown-ledger.md` states it: an unsaturated month whose non-Linux share exceeds 15% and whose displayed value matches unweighted raw minutes would refute this decision. `src/providers/reconciliation.ts` classifies each observed month and refuses to count a saturated or Linux-dominated month as support, which is the specific error behind two of the three prior revisions.

## Related

- [`docs/policy/github-actions-minute-consumption.md`](../../../policy/github-actions-minute-consumption.md)
- [`docs/releases/v3/v3.18/development/github-drawdown-ledger.md`](../../../releases/v3/v3.18/development/github-drawdown-ledger.md)
- [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../../releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md)
