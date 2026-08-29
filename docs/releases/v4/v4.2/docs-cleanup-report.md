# Docs Cleanup Audit - v4.2.0 Interactive Guide Redesign

**Date**: 2026-08-29
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md`

## Phase 1 - Baseline, Content Model, and UX Contract

### Layout check

Phase 1 adds only release-scoped design evidence and a focused test module. Paths sit under the canonical `docs/releases/v4/v4.2/` tree plus `tests/guides/`. No scratch document is proposed for deletion. Diagnostic helpers `_audit_guide.py` and `_ids.py` were deleted before commit and are not part of the tree.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` | Active plan | Keep. |
| `docs/releases/v4/v4.2/development/guide-redesign-baseline/` | Active phase evidence | Keep; static baseline until Phase 7 adds rendered captures. |
| `docs/releases/v4/v4.2/development/guide-redesign-content-map.md` | Active contract | Keep; later phases update in place. |
| `docs/releases/v4/v4.2/known-gaps.md` | Active release gap ledger | Keep. |
| `docs/releases/v4/v4.2/docs-cleanup-report.md` | Active release audit record | Keep and append later phase audits until release close. |
| `docs/releases/v4/v4.2/development/history/2026-08-29_v4.2.0-interactive-guide-redesign-phase-1-baseline.md` | Active phase evidence | Keep under the current version's development history. |

### Result

No duplicate, orphaned, scratch, or misplaced documentation was created by Phase 1. No file moved, and no cleanup change was approved or applied.

## Phase 2 - Portfolio-Aligned Shell, Theme, and Navigation

### Layout check

Phase 2 edits the canonical guide HTML in place and adds `docs/releases/v4/v4.2/development/guide-redesign-phase-2/` plus a session-history file. No move.

### Result

No documentation move. Token-role table updated in the content-map.

## Phase 3 - Concise Home and Embedded Installation

### Layout check

Phase 3 edits the canonical guide HTML in place, adds `docs/releases/v4/v4.2/development/guide-redesign-phase-3/`, and a session-history file. Temporary splice helpers were deleted and are not in the tree.

### Result

No documentation move. Setup-page content that still has a learning purpose now lives on Home or Reference.

## Phase 4 - Model-versus-Harness Foundations

### Layout check

Phase 4 rewrites Foundations in the canonical guide HTML and adds `docs/releases/v4/v4.2/development/guide-redesign-phase-4/` plus a session-history file. Splice helpers were deleted before commit.

### Result

No documentation move.
