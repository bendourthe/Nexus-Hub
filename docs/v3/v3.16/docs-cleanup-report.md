# Docs Cleanup Audit - v3.16

**Mode**: audit only. No file was moved, renamed, or deleted by this pass.
**Run at**: v3.16.0 Phase 2, post-phase step 8.5 (2026-08-08). Supersedes the Phase 1 run; findings carried forward below.
**Scope**: `docs/v3/v3.16/`, plus `docs/policy/` and the repo-root and `configs/` surfaces these phases touched.

## Layout verdict

The version directory follows the canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme with `plans/` and `comparisons/` subdirectories. No legacy flat (`docs/v*/plans/`) or three-level (`docs/versions/v*/v*/plans/`) duplicate of any v3.16 plan exists, so there is no inconsistent-layout condition to report.

| Path | Verdict |
|------|---------|
| `docs/v3/v3.16/plans/` (3 files) | Canonical. Keep. |
| `docs/v3/v3.16/comparisons/` (3 files) | Canonical. Keep. |
| `docs/v3/v3.16/known-gaps.md` | Canonical per-minor ledger. Keep. |
| `docs/v3/v3.16/development/history/` | Created by this phase for the session-history artifact. Expected location. |
| `docs/v3/v3.16/docs-cleanup-report.md` | This file. Regenerated per phase; Phase 5 should reconcile or remove it. |

## Findings

### F-1 - RESOLVED (Phase 5): the loose reference doc was relocated

`github-ci-cd-cost-effective-alternatives.md` moved from the v3.16 version root into a new `research/` subdirectory. Two wrinkles surfaced during the move and are recorded because they shaped how it was done:

1. **No `research/` convention existed.** Across 21 version directories, only `plans` (21), `development` (17), and `comparisons` (17) appear. The subdirectory is new; a future cleanup may prefer to consolidate it.
2. **Two inbound references, handled differently.** The live one in `docs/v3/v3.19/plans/v3.19.0-cost-effective-ci-cd.md` ("Seeded from") was repaired. The one inside a v3.15 session history was **deliberately left unchanged**: a session history is a frozen record of what was true at the time, and rewriting its paths to match a later reorganization would falsify the record. A stale path in a dated historical document is correct.

The original finding is retained below for the record.

### F-1 (original) - LOW: a loose reference doc sits at the version root

`docs/v3/v3.16/github-ci-cd-cost-effective-alternatives.md` is a research/reference document parked directly in the version directory rather than under a subdirectory, unlike every other file in the tree (which lives in `plans/` or `comparisons/`). It predates this phase.

**No action taken.** Moving it would require repairing any inbound references, which is Phase 5's remit under `[[docs-layout-refactor]]` propose-then-apply. Recorded here so that pass does not have to rediscover it.

### F-2 - INFORMATIONAL: no scratch docs were created by this phase

This phase created exactly two documentation artifacts, both intentional and both at canonical paths: the session-history file under `development/history/` and this report. `configs/README.md` is product documentation, not a scratch doc, and is referenced from the code it documents.

Per the audit rule, no cleanup of this phase's own documents is proposed.

### F-3 - INFORMATIONAL: `docs/policy/` now holds two sibling contracts (Phase 2)

Phase 2 added `docs/policy/platform-defaults-levers.md` alongside the existing `platform-read-contracts.md` / `.json` pair. The two are deliberately separate documents with a stated scope boundary (behavioral defaults here, discovery paths and capabilities there), and each names the other in its header so a reader landing on either learns where the other half lives.

**No action taken, and none recommended.** Merging them would create the single overgrown document the boundary exists to prevent. Worth noting for Phase 5's layout pass so the pairing reads as intentional rather than as duplication.

### F-4 - RESOLVED IN-PHASE: `docs/policy/` was excluded from CI

Phase 2's step 8.3 found that `ci.yml`'s `paths-ignore: ['docs/**']` prevented any CI run for a push touching only `docs/policy/`, even though that directory is validator input rather than prose. Fixed within the phase; recorded in full as known gap QG-1. Noted here because it is a docs-layout fact, not only a CI fact: `docs/policy/` is the one subtree of `docs/` that behaves like source.

### F-5 - INFORMATIONAL: the policy pair is now cross-referenced in both directions (Phase 4)

`docs/policy/platform-defaults-levers.md` and `docs/policy/platform-read-contracts.md` each name the other and state the scope boundary, and the `platform-contract-verification` skill now enumerates both in a single re-verification pass while stating which one hard-gates a release. The pairing is intentional and legible from any entry point; no consolidation is warranted.

## Cross-surface check

- `README.md` makes no reference to `configs/`, so the new source needs no README change. Documenting the surface in `AGENTS.md` is explicitly Phase 4.2's sub-task and was deliberately NOT done here, to avoid doing a later phase's work.
- `configs/README.md` did not exist before this phase; it now documents both the pre-existing `permissions/` templates and the new defaults source, so `configs/` is no longer an undocumented directory.
