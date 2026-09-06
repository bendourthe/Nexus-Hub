# Session History - GitHub Usage Monitor Accuracy Phase 5: Policy Document and Decision Record

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 5 - Policy document and decision record
**Environment**: Windows 11, Git Bash, Python 3.12, ShellCheck; GNU Make unavailable, so `make` targets were run as their constituent commands
**Outcome**: When Actions minutes are consumed is written down once, with every claim marked documented-with-source or inferred-with-evidence. The weight change carries its own falsifier and the four alternatives it beat.

## 1. Starting State

- **Starting commit**: `03fbe344` (Phase 4: panel provenance and split)
- **Routing decision**: the plan recorded `strong / medium`, noting the risk is asserting an undocumented GitHub behavior as documented. Implementation ran on Opus 5. The mitigation was structural: every claim in the policy document carries an explicit **documented** or **inferred** marker, so an unsourced assertion is visible rather than blended into prose.

## 2. The Single Largest Hazard, and How It Was Bounded

The plan named it precisely: **stating the multiplier as GitHub-documented**. It is not. GitHub's current pages publish per-minute prices and state that Windows and macOS cost more; they publish no multiplier for included-minute consumption, and the page that once did has been withdrawn on all three documentation variants.

The document therefore says so outright, in its own section, rather than leaving the absence to be inferred from what is missing. Every rate carries a verified date because prices change - they changed on 2026-01-01, which is the whole reason this release exists.

Four claims are marked **documented** with a live source URL and a 2026-08-19 verification date: the `discount_amount` definition covering public-repository and self-hosted usage, the current per-minute prices, the GB-hours to GB-months conversion, and the blocking behavior on exhaustion without a payment method. Three are marked **inferred**, each with the evidence: that gross minutes overstate the drawdown by the public share, that the legacy multipliers are price ratios, and that the exhaustion block applies specifically to the usage that draws down.

## 3. What Changed

| File | Change |
|---|---|
| `docs/policy/github-actions-minute-consumption.md` | New. The four-row summary table, one section per claim class, the pre-2026 versus 2026 rate tables, the "the allowance is not readable" section, and what it all means for reading the meter. |
| `docs/decisions/implemented/architecture/2026-08-22-derive-actions-drawdown-weights-from-price.md` | New. The three-revision history as a table, the decision, four alternatives, and the consequences including what the decision does **not** grant. |
| `extensions/github-usage-monitor/README.md` | The "Where the percentages come from" section corrected to describe derived weights, with the stale 1,584 figure updated to the measured 1,724, plus links to all three documents. |

## 4. Two Path Corrections Against the Plan

The plan was retargeted from v3.17.11 to v3.18.1 and its header instructs that self-referencing paths be reconciled at implementation time. Two applied here:

- The decision record was specified under `docs/decisions/accepted/`. That lifecycle folder does not exist: `docs/decisions/README.md` defines exactly three, `proposed` / `implemented` / `rejected`. The record is a shipped decision, so it went to `implemented/architecture/`.
- `docs/policy/doc-budgets.json` was checked as the plan required. It governs **always-loaded instruction docs only** - `AGENTS.md`, `CLAUDE.md`, the style guide, and the five `base-*.md` templates. A policy document loaded on demand is not in its scope, so no ceiling entry was added. Recording that explicitly, because the plan asked the question and "checked, does not apply" is the answer rather than an omission.

## 5. The Record Names What It Does Not Grant

`## Alternatives considered` is mandatory in this repo precisely because a decision without it invites re-litigation, and this number has already been re-litigated twice. Four alternatives are recorded with the reason each lost:

| Alternative | Verdict |
|---|---|
| Keep the unweighted model | Refuted by measurement - two saturated months both predict below the cap |
| Reinstate hardcoded 2x / 10x | Fits the data within 0.3%, but re-freezes a price list that has already moved once |
| Show an uncertainty band | Honest and unactionable for a meter whose purpose is to warn at a threshold |
| Scrape the billing page | Not reachable with an OAuth Bearer token; undocumented surface with no stability contract |

The Consequences section states three things the decision does **not** grant: the figure is still a reconstruction, GitHub publishes no multiplier, and the allowance remains plan-table-derived. It also names the Phase 3 falsifier explicitly, so the next challenge has a defined target.

## 6. Verification

| Gate | Result |
|---|---|
| `make validate` (27 constituent commands) | All pass. 273 skills, 13 decision records OK, 8 budgeted docs within ceiling, required-check coverage OK, platform contracts OK |
| `make lint` (ShellCheck on `scripts/installer.sh`, `install.sh`) | Pass |
| `validate_unicode_safety.py --strict` | Clean on both new documents and repo-wide |
| `validate_decision_records.py` | Accepts the new record: correct lifecycle folder, `Status:` matching, mandatory `## Alternatives considered` present |
| Relative-link resolution | 0 dangling across all four touched documents |
| External claims | Every one carries a source URL and a 2026-08-19 verified date, or is explicitly marked inferred with its evidence |

**One advisory, deliberately not acted on**: `check_docs_retention.py` reports `docs/archive/v3/v3.16/development/history` (39 files) due for archival. That is a pre-existing condition unrelated to this plan, and Phase 6.1 forbids refactoring outside plan scope. It is recorded as a known gap in Phase 6.3 rather than swept into this release.

## 7. Next Step

Phase 6: the terminal phase - layout pass, the 0.4.0 version bump and CHANGELOG, known-gaps reconciliation, CI/CD completion, and release readiness.
