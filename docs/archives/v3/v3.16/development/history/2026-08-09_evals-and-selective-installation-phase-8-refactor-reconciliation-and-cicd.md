# Session History - v3.16.1 Phase 8: Refactor, reconciliation, and CI/CD

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 8 of 8 - **terminal phase**
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Local work complete and green. Branch NOT pushed and `/update release` NOT invoked - both are approval-gated and awaiting the user.

## Final-phase detection

All five signals agree, so the release-readiness workflow applies:

- Phase 8 is the numerically highest and the last by document order
- Title matches the v3.11.0 terminal heuristic ("Architecture Refactor, Known-Gaps Reconciliation, and CI/CD")
- All seven prior phases have a session-history file
- Seven phase commits on the branch, one per phase
- The plan is the only one under the active version directory for this cycle

## Sub-tasks completed

### 8.1 - Architecture refactor (T050)

Audited the v3.16.1 diff with the v3.11.0 detectors. **Nothing needed changing**, which is the honest outcome and is recorded rather than dressed up as work:

| Detector | Result |
|---|---|
| Empty directories | None in any touched tree |
| Duplicated prose | 0 duplicated paragraphs across the contract, the baseline, and the user guide |
| Orphaned bundle resources | Bundle audit: 0 errors, 0 warnings across 271 skills |
| Redundant selection logic | None. One resolver; both installers delegate to it rather than reimplementing the contract |
| Docs layout | Canonical (`comparisons/`, `development/`, `plans/`, `research/`, plus the two version-root files), matching the v3.16.0 convention |
| Stale references | The deleted `selection.jq` is referenced only by the DF-5 entry that records its deletion, which is correct |

One documentation correction: the Phase 5 baseline stated "6 modules, schema 1.4.0", which Phase 7.1 superseded. Rather than rewrite the audit record (which would falsify what the audit found), a dated forward-note was appended pointing at the change and at NI-4 / NI-5.

### 8.2 - Known-gaps reconciliation (T051)

**16 closed, 3 carried forward, 0 release blockers.** Per the user's direction, QG-1 and NI-2 were fixed here; WN-1 and BG-1 carry forward with reasons. WN-2 was newly recorded during 8.4.

The v3.16.0 section and the transferred v3.15.14 items were left untouched.

### 8.3 - Terminal CI/CD comparison (T052)

Created `v3.16.1-ci-cd-comparison.md`: a nine-workflow inventory, an element-by-element comparison against the optimized contract, and a migrate-or-retain decision per pipeline. The pipeline was **already at the optimized contract** - concurrency with cancel-in-progress, path filters, caching, `timeout-minutes`, least-privilege permissions, gated Windows leg, SHA-pinned actions.

**One migration, QG-1.** `ci.yml` triggered on `['**', '!docs/**', 'docs/policy/**']`, but Phase 1 added a test that asserts against a document under `docs/`. A push editing only that contract skipped CI, so the exact edit the guard exists to catch was the edit that never ran it. Added `- 'docs/v*/*/development/*.md'` to both the `push` and `pull_request` events.

Four differences were examined and **retained with reasons** (no `jq` in CI, no per-job path filters, no Python lint gate, Windows leg not running the full suite).

**NI-2** was also closed here: all 118 remaining truncated agent descriptors rebuilt from their skill's own frontmatter, taking whole sentences. 140 descriptors, 0 truncated, 0 non-ASCII, every `display_name` preserved.

### 8.4 - Validation (T053, T054)

See Verification below.

### 8.5 - Final commit

Prepared; the push is a separate, approval-gated step.

## Decisions made

- **The refactor audit found nothing, and that is reported as nothing.** A terminal phase is under quiet pressure to produce visible cleanup. Moving files to look productive would add risk to a release for no benefit, so the detectors' results are listed individually instead.
- **The QG-1 glob is deliberately narrow.** `docs/v*/*/development/*.md` matches contract docs but not `development/history/*.md`, because a `*` never crosses a `/`. Re-including all of `development/` would run the full matrix on every session-history write-up for no signal. The narrower fix costs nothing and avoids a self-inflicted CI-minute bill.
- **NI-2's repair takes whole sentences rather than a longer character cap.** The original defect was a 200-character hard slice; replacing it with a 300-character hard slice would be the same bug with a bigger number. Sentence completion is the property that actually matters, and the resulting median is 233 characters.
- **The Phase 5 baseline got a forward-note, not a rewrite.** It is a dated audit record. Editing its findings to match a later state would make it agree with the present at the cost of no longer being true about the past.
- **WN-2 was recorded even though nothing is broken.** A `UnicodeDecodeError` traceback in a passing test's log is a real cost to a future reader, and the honest place for it is the gap ledger rather than silence.

## Troubleshooting trail

- **No failures in Phase 8's own work.** Every guard passed on first run.
- **One recurring cosmetic artifact was chased to ground** rather than ignored: the `UnicodeDecodeError` seen in the slow parity tests and again in the manual install comparison is Python's subprocess reader thread decoding the installer's UTF-8 output as cp1252 on Windows. Confirmed harmless (raised in the reader thread, process exits 0, assertions read the filesystem) and recorded as WN-2 with the one-line fix.

## Verification

**All 15 `make validate` guards, run individually** because `make` is unavailable on this host (WN-1): JSON integrity (5 files), bundle orphan audit, quality heuristics, trigger and routing gate, no-personal-paths, unicode safety, supply-chain IOCs, workflow security, solution frontmatter, version sync, base-template parity, model-prompting profiles, platform contracts, contract freshness, platform-defaults drift. **All PASS.**

**Syntax**: `bash -n scripts/installer.sh` PASS; `installer.ps1` parses clean under Windows PowerShell 5.1. `git diff --check` clean.

**Selector matrix, resolved and inspected** (not just exit codes):

| Selection | Skills | Commands | Agents |
|---|---|---|---|
| no selector | 271 | 20 | 23 |
| `--profile full` | 271 | 20 | 23 |
| `--profile minimal` | 10 | 14 | 23 |
| `--profile core` | 45 | 14 | 23 |
| `--modules workflow` | 43 | 16 | 23 |
| `--modules ai-engineering` | 13 | 16 | 23 |
| `--bundles ai-engineer` | 13 | 14 | 23 |
| `core` + `workflow` (union) | 82 | 16 | 23 |

**Invariants**: no-selector hash == explicit `full` hash; CSV form hash == repeatable form hash. **Invalid input**: unknown profile, `full` + module, and an empty comma element each exit 2 before any write.

**Live installs** (bash, workspace scope, `--platforms claude`): full rc=0 with 271 skill dirs; `--modules ai-engineering` rc=0 with 13; the focused set is a strict subset of the full set; `rules`, `commands`, and `agents` present in both.

## Files changed

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | QG-1: `docs/v*/*/development/*.md` re-included on both events |
| `catalog/skills/*/*/agents/openai.yaml` | NI-2: 118 descriptors repaired to sentence boundaries |
| `docs/v3/v3.16/development/v3.16.1-ci-cd-comparison.md` | new |
| `docs/v3/v3.16/development/selective-install-baseline.md` | dated forward-note |
| `docs/v3/v3.16/known-gaps.md` | QG-1, NI-2 closed; WN-2 recorded; final disposition |
| `docs/DEVLOG.md`, `docs/todos.md` | Phase 8 entry and tracker |

## What has NOT been done

Deliberately, and awaiting explicit approval:

- **The branch has not been pushed.** This would be the first push of the cycle.
- **No pull request has been opened**, and no integration checks have run.
- **`/update release` has not been invoked**: no version bump, no changelog finalization, no tag, no GitHub Release.

The version remains 3.16.0 across every surface; `check_version_sync` passes on that basis. The release workflow owns the bump.
