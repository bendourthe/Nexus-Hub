# Session History - GitHub Usage Monitor Accuracy Phase 4: Panel Provenance and Public/Private Split

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 4 - Panel provenance and public/private split
**Environment**: Windows 11, Git Bash, Node with `vitest` 4.1.10
**Outcome**: The panel shows where the Actions minutes went, which of them counted, and what the displayed figure was derived from - both halves of its provenance, as two separate sentences.

## 1. Starting State

- **Starting commit**: `5b070c3b` (Phase 3: reconciliation ledger)
- **Routing decision**: the plan recorded `strong / medium` on the grounds that this is presentation over an already-computed model. Implementation ran on Opus 5, which matches.

## 2. The Existing Breakdown Answered the Wrong Question

`breakdownByRepository` already existed and was unused by the UI, so the obvious move was to render it. It answers "where did the minutes go" - raw totals, list price, discount, net.

The question a user asks when 366 public-repository runs appear on a bill that charges nothing is different: **which of these counted**. A raw-minutes table shows `Nexus-Hub` at 4,200 minutes and `Nexus-AI` at 1,724 and invites exactly the wrong conclusion. So `contributionsByRepository` was added beside it, returning raw **and** weighted minutes per repository, sorted by weighted contribution. The public row sorts to the bottom at zero, which is the answer rendered as a layout.

## 3. What Changed

| File | Change |
|---|---|
| `src/providers/drawdown.ts` | New `RepositoryContribution` and `contributionsByRepository`, applying the same exclusions and the same derived weight as `computeDrawdownMinutes`. |
| `src/types.ts` | New optional `UsageSnapshot.actionsDrawdownDetail` carrying the rows, the reference rate and its source, the unresolved list, and the denominator's provenance sentence. |
| `src/providers/enrich.ts` | Populates that detail. New `describeDrawdownProvenance`, a sibling of `describeAllowanceProvenance`. |
| `src/dashboardPanel.ts` | New collapsible "Actions minutes by repository" section with a 12-row cap, an aggregated tail, an unresolved group, and both provenance sentences. |
| `test/actions-breakdown.test.ts` | New. Nine tests over the measured August month, the 40-repository cap, escaping, and the pre-0.4.0 snapshot. |

## 4. Two Sentences, Not One

`describeAllowanceProvenance` answers where the **denominator** came from - a plan table, or a value the user typed. Since Phase 2 the **numerator** has its own provenance: a reconstruction, weighted by a rate that was either observed in the period or fell back to a published constant.

These are different claims with different reliability. A plan-table denominator is a published figure; a price-derived numerator is an inference from data GitHub returned. Folding them into one sentence is how a provenance line stops being read, so `describeDrawdownProvenance` was added as a sibling and the panel renders both.

The denominator sentence is **resolved at enrichment time and carried on the snapshot**, because it depends on the account's plan name. The panel does not have the plan name and giving it a second channel to obtain one would have been a worse coupling than one extra string on a structure it already renders.

## 5. Decisions Inside the Rendering

| Decision | Reasoning |
|---|---|
| Public rows shown at zero, not filtered | A filtered row leaves the question unanswered, just less visibly |
| 12-row cap with an aggregated "other" row | An account with 100 repositories must not get 100 rows in a sidebar; the tail is **summed**, so the rows still add up |
| Unresolved repositories in their own group | With the existing explanation: a private repository is invisible to a token without the `repo` scope, and those are exactly the ones that draw down |
| Repository names rendered **unhashed** | The user's own data in their own editor. The probe hashes by default because its output is written to be pasted into an issue. The two conventions differ on purpose, and the code says so |
| Every value through `escapeHtml`, CSP unchanged | Tested directly with a hostile repository name |
| `actionsDrawdownDetail` optional | A snapshot cached before 0.4.0 has none; the panel omits the section rather than throwing on the first render after an upgrade |

## 6. Verification

| Gate | Result |
|---|---|
| `npm run compile` | Pass |
| `npm test` | 466 tests, 30 files, all pass (up from 457) |
| `npm run test:coverage` | Statements 83.31%, branches 79.95%, lines 86.08% |
| Measured August render | `Nexus-Hub` public at zero weighted, `Nexus-AI` private with the total, both provenance sentences present |
| 40-repository fixture | Exactly 13 rows inside `table.repo-table`: 12 plus the aggregate |
| Hostile repository name | Rendered escaped; no raw markup reaches the document |
| Pre-0.4.0 snapshot | Section omitted, panel renders |

## 7. Next Step

Phase 5: the Actions-minutes consumption policy document and the decision record, both written against shipped behavior rather than intended behavior.
