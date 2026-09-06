# Session History - v3.16.3 Phase 2: Allowance and drawdown truth

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.3-github-usage-monitor-ux.md](../../plans/v3.16.3-github-usage-monitor-ux.md)
**Phase**: 2 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO. Percentages ship, weighted and labelled.

## Goal

Determine whether a correct percentage is derivable at all from documented GitHub data, ship bars only where it is, and explain the absence everywhere else.

## What the phase actually established

The plan's framing assumed the answer would be either "reconstruction reconciles" or "reconstruction is impossible". It was neither. A reconstruction exists and survives every test the available data can apply, but it depends on constants GitHub has withdrawn from its documentation.

Getting there required live measurement against a real account, because every question that mattered turned out to be unanswerable from documentation alone.

### 2.1 - Re-verification, and four corrections to the plan

Full evidence in [github-entitlement-probe.md](../github-entitlement-probe.md).

Confirmed: **no documented endpoint serves an entitlement.** Every field of `/settings/billing/usage`, `/usage/summary`, the AI-credit and premium-request endpoints, and the Budgets API was checked. `consumed_amount` on Budgets is spend against a user-defined budget, not usage against an allowance - checked and rejected explicitly so a future contributor does not re-check it.

Also confirmed, and new: **no endpoint serves the drawdown either.** `/usage/summary` reports `discountQuantity == grossQuantity` on every row. GitHub discounts 100% of usage and never separates the free public-repository portion from the allowance-consuming portion. Reconstruction is the only route, which is what made its verifiability decisive.

Four corrections to the plan's own text:

1. **The field inventory was wrong.** `/settings/billing/usage` returns `quantity` with money-only discount and net; the `grossQuantity` / `discountQuantity` / `netQuantity` triplet exists only on `/usage/summary`, which carries no `repositoryName`. The two fields a reconstruction needs sit on different endpoints.
2. **The exclusion set is three deep, not one.** GitHub's report reference defines `discount_amount` as covering included usage **and** public-repository usage **and** self-hosted runners; separately, included minutes cannot be used for larger runners.
3. **The 10 GB Git LFS figure is not anomalous.** The plan cited it as evidence that plan tables are unreliable. GitHub currently publishes 10 GB storage and 10 GB bandwidth for Free - it matches exactly. The conclusion survives on other grounds (unresolvable plans, invisible data packs, Codespaces publishing a literal **None**), but the cited evidence was mistaken.
4. **A documented storage conversion exists.** The plan predicted none and expected an unsupported state. GitHub states outright that GB-Hours convert to GB-Months by dividing by the hours in the month.

### 2.2 - Denominator, auto-derived with a discoverable override

[`planEntitlements.ts`](../../../../extensions/github-usage-monitor/src/providers/planEntitlements.ts) carries GitHub's published per-plan figures with source URL and verification date. `GET /user` supplies `plan.name`; an unrecognized plan returns `null` and **never** falls back to Free, because reporting 2,000 minutes to an Enterprise account would be wrong in the most expensive direction.

The design changed mid-phase after a maintainer correction. An earlier draft had removed manual entry entirely, having conflated Phase 3's automatic-connection requirement with a ban on allowance settings. Those are different concerns, and collapsing them made the static table load-bearing in a design with no way to ever be right for an account whose real entitlement differs. The shipped shape: derive automatically so the common case needs no typing, show provenance beside the value ("published figure for your plan, not read from your account"), and keep the `githubUsageMonitor.allowances.*` settings as a discoverable override.

### 2.3 - Drawdown reconstruction, and the candidate that had to die

This is the phase's substance. `scripts/reconcile-drawdown.js` computes several candidate reconstructions side by side against a real account and selects none of them; the pure computation lives in [`drawdown.ts`](../../../../extensions/github-usage-monitor/src/providers/drawdown.ts) so the measurement uses the same code the product does.

Measured on account `bendourthe`:

| Month | Private raw | Unweighted | Weighted (2x/10x) | GitHub displayed |
|---|---|---|---|---|
| 2026-05 | 4,048 | 4,048 | 5,534 | saturated at 2,000 |
| 2026-07 | 1,584 | 1,584 | 2,104 | **2,000 of 2,000, saturated** |
| 2026-08 | 124 | 124 | 128 | ~121 (month in progress) |

**July falsified the unweighted model.** A saturated bar means the true drawdown was at least 2,000; a model predicting 1,584 cannot produce that. Non-Linux minutes draw down faster, even though GitHub withdrew the page stating so.

The two surviving weightings - historical published (2x / 10x) and current list-price ratios (1.67x / 10.33x) - predict 2,104 and 2,051 for July, both above the cap, and 1,473 versus 1,469 for April. This account cannot separate them. Shipped with the historical values, chosen with the maintainer because GitHub once stated them outright where a price ratio never was, and the card labels the figure a reconstruction.

### 2.4 - Storage conversion

`GB-months = GB-hours / hours_in_month`, documented and now corroborated **in both directions** on the same account: July 432.305 / 744 = 0.581 GB against a 0.5 GB allowance, which GitHub showed as saturated; August 64.568 / 744 = 0.087 GB, shown as "0 GB used". Verifying only the small case would have left a constant-factor error undetectable.

The unit-matching guard in `allowances.ts` was kept intact. The consumption is converted into GB *before* it reaches the guard, rather than the guard being loosened to compare different dimensions.

### 2.5 - Three allowance states

`verified` renders the teal meter. `none` renders the absolute treatment plus a line stating the plan includes no allowance for this product - which closes the maintainer's original complaint about a Copilot card reading `0` with no context. `unknown` renders the absolute treatment plus a line naming what would make a percentage available. No state renders `0%` or `100%` for a null allowance.

### 2.6 - Tests

27 new tests across [`enrich.test.ts`](../../../../extensions/github-usage-monitor/test/enrich.test.ts) and additions to `drawdown.test.ts` and `allowances-store.test.ts`, built from the real figures rather than round numbers: the July reconstruction that falsified 1:1, the 1,287-versus-120.7 regression asserting the percentage is drawdown-based and explicitly *not* the gross-based 64%, both storage observations, and an assertion that `allowanceSource` is never `"api"`.

## Troubleshooting

**The measurement tooling was wrong three times before it was right**, and every failure produced a plausible answer rather than an error.

1. **Token scope.** The first run used a `user`-only PAT, so `GET /repos/{owner}/{repo}` 404'd for private repositories and every private candidate summed zero. My instruction caused it. The runner now withholds its verdict entirely when any visibility lookup fails.
2. **SKU misclassification.** The rule treated any `N-core` SKU as a larger runner, misclassifying `Actions macOS 3-core` - the standard macOS runner - and dropping 111 minutes. Now a per-OS core ceiling, with a regression test pinned to the strings the account actually emitted.
3. **Period mismatch.** August API data was compared against displayed figures from an earlier month. The runner now prints the queried period directly above the verdict.

**A false positive that nearly shipped.** After the first two fixes, `privateHostedStandardLinuxMinutes` reported RECONCILES at 0.6%. It was arithmetically impossible: the API's 120 Linux minutes is an upper bound on true Linux time, yet the displayed drawdown was 120.7. A bound check caught what a tolerance check had passed. Shipping on that green verdict would have silently excluded all Windows and macOS drawdown for every user.

**One retraction.** I attributed the August gap to per-job round-up inflation. June and July return fractional quantities (`1450.666666667`), so there is no rounding to blame. The real cause was that August was still accruing between the screenshot and the probe run.

## Test results

| Suite | Result |
|---|---|
| Extension (Vitest, `npm run test:coverage`) | 273 passed, 0 failed (17 files) |
| Extension coverage | 82.78% statements, 78.49% branches, 84.69% functions, 86.3% lines - all above threshold |
| Compile + package | `tsc` clean; `npm run package` + `verify:package` succeed at `0.2.0` (57 files) |
| `catalog/hooks/tests/test_installer_smoke.py` + `tests/installer/test_github_monitor_naming.py` | 48 passed |

## CI/CD

No workflow change needed. `.github/workflows/github-usage-monitor.yml` triggers on `extensions/github-usage-monitor/**`, covering all four new source modules and the new test file. No new test directory was created, so the v3.15.8 QG-2 hazard (a directory invisible to CI until named) does not apply; collection was verified empirically at 17 files, up from 16.

## Deviations from the plan

1. **2.2 inverted.** The plan demoted the plan table to a non-writing hint with manual entry as the primary path. Shipped the reverse - table as the automatic source, manual as override - at the maintainer's direction, after the plan's supporting evidence for the demotion (the 10 GB LFS figure) turned out to be mistaken.
2. **2.3 neither reconciled nor took the cut line.** Its gate assumed a binary outcome. The measured reality is a model that survives every available test on constants GitHub no longer publishes. Escalated to the maintainer, who chose to ship with the caveat.
3. **A measurement script was added** (`scripts/reconcile-drawdown.js`), not in the plan. Without it the reconciliation the plan mandates could not have been run at all. It is a development diagnostic, excluded from the VSIX.
4. **`GET /user` and `GET /repos/{owner}/{repo}` are new outbound calls.** Both go to GitHub with the credential the billing call already succeeded with, and the repository call reads one boolean. The plan's scope note said no new outbound call; the reconstruction is impossible without repository visibility.

## Known gaps recorded

`NI-2` (weights unverifiable, shipped by decision with a re-check trigger), `NI-3` (two SKU vocabularies, classifier survives by substring luck), `MT-2` (self-hosted and larger-runner rules validated only against invented strings), `NI-4` (policy: the three sibling monitors read vendor-internal usage endpoints while this one is barred from GitHub's equivalent by its own contract), `QG-2` (closed in phase: the three tooling defects above). Zero release blockers.

## Next steps

Phase 3, "First-run connection". One item feeds it directly: MT-1 from Phase 1 asked for an activation-ordering assertion, and Phase 3 builds the activation harness that makes it cheap.

NI-4 is the more consequential thread and is deliberately **not** Phase 3's business. It asks whether the GitHub monitor should be held to the same standard as its three siblings, all of which read vendor-internal endpoints. Answering it would make most of this phase's reconstruction unnecessary; leaving it unanswered means the reconstruction stays load-bearing.
