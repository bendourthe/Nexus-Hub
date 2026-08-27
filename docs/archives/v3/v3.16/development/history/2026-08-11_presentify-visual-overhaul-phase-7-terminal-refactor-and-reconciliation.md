# Session History - v3.16.5 Phase 7: terminal refactor, reconciliation, and CI/CD

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 7 of 7 - **the terminal phase**
**Branch**: `feat/v3.16.5-presentify-visual-overhaul` (worktree at `.claude/worktrees/v3.16.5-presentify`)
**Model**: Opus 5. The plan recommends **frontier at max effort**; the maintainer's standing preference across three prior tier deltas was applied rather than asking a fourth time.
**Terminal-phase detection**: 4 of 5 signals - numerically highest phase, the v3.11.0+ terminal title ("Architecture Refactor, Known-Gaps Reconciliation, and CI/CD"), all six prior phases carrying session-history files, and the sole plan under the active version directory.

## Sub-tasks completed

### 7.1 - Architecture refactor

**The calibration fixture is homed.** `nexus-hub-unit-test-workflow.html` moved from the repository root to `tests/fixtures/presentify/`, by maintainer decision, with `git mv` so history follows it. This is the one file every phase since Phase 1 deferred.

Reference repair, and one reference that was not a path:

- The CI scoring step's path was updated.
- The dual-candidate lookup in `test_presentify_visual_qa.py` was **removed**, not kept. It existed only to survive this move (pre-wired in Phase 3 so the move would need no test change); leaving it would have left a second accepted location nobody maintains, quietly masking a future misplacement.
- **The third reference was a trigger condition.** `presentify-extractor.yml` path-filtered `tests/skills/**` but not `tests/fixtures/**`, so after the move a fixture-only edit would no longer trigger the job that scores it - the standing gate would have silently stopped gating the exact file it guards. `tests/fixtures/presentify/**` was added to both filter lists. Worth recording because the move looked complete after the two obvious path repairs.

Historical session-history entries were deliberately NOT rewritten: they record where the file was at the time, which is accurate.

**Bundle layout: clean, no action.** Seven `references/`, four `assets/`, seven `scripts/`, every one referenced from `SKILL.md` (orphan audit 0 warnings). No empty directories, no duplicates, no strays. `SKILL.md` is 292 lines against a 500-line target and an 800-line cap.

**Docs layout: clean, no action.** `docs/v3/v3.16/` holds `plans/` (5), `comparisons/` (4), `development/` (6 plus `history/` 32), and exactly the two conventional root files. Matches the per-version scheme; nothing to move.

### 7.2 / 9A - Known-gaps reconciliation

MT-1 closed. All sixteen v3.16.5 items dispositioned in a terminal reconciliation block: 1 closed here, 7 closed in earlier phases (plus v3.15's MT-1 and MT-2, both closed by APPENDED notes rather than rewrites - verified present), 7 carried by design with a stated reason and a named place where each is answered, and 2 accepted-or-deferred with a decision.

The one `# DEVIATION` marker in the bundle is pre-existing (v3.15.4 Phase 1.3, in `build_presentation.py`) and was already dispositioned by that cycle as code documentation. Left alone.

### 7.3 - CI/CD and R12 distribution

**R12 verified mechanically** by diffing the whole branch against its base: 13 distributed artifacts, all in auto-copied trees (`catalog/skills/`, `catalog/commands/`, `data/`), and **zero** repo-level `scripts/` files added - so no installer edit and no `DEV_ONLY_SCRIPTS` entry is owed. The scroll-scrub engine is a per-skill `assets/` file, which both installers copy recursively; being `.js` it also owes no `.ps1` sibling.

**CI audited as complete and optimized**: path filters on both trigger lists, `concurrency` with cancel-in-progress, pip caching in both jobs, a browser-download cache keyed on the resolved Playwright version (not the workflow file, so it invalidates only when the pinned revision moves), per-job timeouts, least-privilege `permissions: contents: read`, the expensive render job gated to merges plus a weekly cron, and the fast job opting OUT of the cron so it is not double-billed. The minute reduction is real: a pull request pays for the browser-free job only.

### 7.4 / 9B - Stabilization

Full sweep, below. No behavior change from the refactor: the only functional edits were a file move plus its three reference repairs, and the suite covering that fixture passes identically before and after.

## The 9.0 terminal gate

- **`[[project-refactor]]` detectors** (empty dirs, duplicates, non-version orphans, structure complexity): clean, no proposals.
- **`[[docs-layout-refactor]]`**: clean, no moves.
- **`[[known-gaps-tracker]]`**: the reconciliation above.
- **CI/CD create/update/optimize**: audited, one path-filter addition applied.
- **`[[model-prompting-research]]` advisory staleness check**: ran, reported UNKNOWN because no live roster was supplied. Left at that, deliberately - the gate specifies this check as advisory-only: it never blocks a phase and never re-stamps a freshness marker. The recorded roster was last verified 2026-07-27 (fifteen days), which is not a release concern. This is the deliberate opposite of the platform read-contract check, which DOES hard-gate a release.

## Verification evidence

| Check | Result |
|---|---|
| `tests/skills/` | **634 passed, 0 skipped** |
| Installer smoke suite | 33 passed |
| Lint (CI's exact target) | `ruff check --ignore RUF100` clean |
| Validators (15, run individually) | all pass, including `sync_platform_defaults --check`, `check_base_template_parity`, `check_version_sync`, `validate_workflow_security`, the orphan-bundle audit (0 warnings), the skill quality pass (271 skills, 0 errors), and the trigger-eval gate |
| Workflow YAML | valid; jobs `verify` + `render`; triggers push / schedule / pull_request |
| R12 distribution | 13 artifacts in auto-copied trees; 0 repo-level scripts added |
| Fixture at its new home | tracked, scored by CI, guarded by 3 tests |
| `make` availability | absent on this host (long-standing environmental WN-1), so every guard was invoked directly rather than through the Makefile target |

## Deviations from the plan

- **The plan's 7.1 asked to decide the fixture home "with the maintainer"**, which was done as an explicit question rather than a unilateral call, since the plan reserves it.
- **One addition beyond the plan's letter**: the `tests/fixtures/presentify/**` path filter. The plan asked to move the fixture with reference repair; a trigger condition is a reference in the sense that matters, and omitting it would have left the move looking complete while disabling the gate.

## What this cycle is worth remembering

**A false PASS costs far more than a false FAIL.** BG-2 produced one of each. Sixteen false failures were loud, obviously wrong, and fixed within the hour. One false pass - a band fraction the checker inflated from 0.947 to 0.954, across its own 0.95 threshold - sat inside a green run for two phases and would have shipped.

**A parser and a renderer answer different questions.** Six of the seven carried items are the same shape, and Phase 3 is what made that division of labour correct rather than a gap. Rendering found five defects that eleven deterministic checks had passed, and two of those five were bugs in the checker.

**Gates need word boundaries.** The vendor-name grep initially returned 57 hits, 56 of which were `emons` matching "demonstrate". A gate nobody can read is a gate nobody runs.

## Release readiness - 9C-9E handoff

**v3.16.5 is release-ready.** No hold condition is active: zero release blockers, tests green, coverage above threshold on every changed module, CI complete and optimized, no version-sync inconsistency.

This phase performed **no version bump, no changelog finalization, no tag, no merge, and no push**. Those are `/update release`'s, which owns them as one atomic flow behind its own confirmation gates. The `## [Unreleased]` CHANGELOG block is written and ready for it to stamp.

One housekeeping note for the merge: an untracked copy of the fixture remains at the ROOT of the primary checkout, where it was originally authored. After `develop` receives this branch, delete it - git will have placed the tracked copy under `tests/fixtures/presentify/`, and nothing reads the root copy any more.
