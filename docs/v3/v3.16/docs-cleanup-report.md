# Docs Cleanup Audit - v3.16

**Mode**: audit only. No file was moved, renamed, or deleted by this pass.
**Run at**: v3.16.0 Phase 1, post-phase step 8.5 (2026-08-08).
**Scope**: `docs/v3/v3.16/`, plus the repo-root and `configs/` surfaces this phase touched.

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

### F-1 - LOW: a loose reference doc sits at the version root

`docs/v3/v3.16/github-ci-cd-cost-effective-alternatives.md` is a research/reference document parked directly in the version directory rather than under a subdirectory, unlike every other file in the tree (which lives in `plans/` or `comparisons/`). It predates this phase.

**No action taken.** Moving it would require repairing any inbound references, which is Phase 5's remit under `[[docs-layout-refactor]]` propose-then-apply. Recorded here so that pass does not have to rediscover it.

### F-2 - INFORMATIONAL: no scratch docs were created by this phase

This phase created exactly two documentation artifacts, both intentional and both at canonical paths: the session-history file under `development/history/` and this report. `configs/README.md` is product documentation, not a scratch doc, and is referenced from the code it documents.

Per the audit rule, no cleanup of this phase's own documents is proposed.

## Cross-surface check

- `README.md` makes no reference to `configs/`, so the new source needs no README change. Documenting the surface in `AGENTS.md` is explicitly Phase 4.2's sub-task and was deliberately NOT done here, to avoid doing a later phase's work.
- `configs/README.md` did not exist before this phase; it now documents both the pre-existing `permissions/` templates and the new defaults source, so `configs/` is no longer an undocumented directory.
