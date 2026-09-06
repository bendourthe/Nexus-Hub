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

## Phase 5 - Interactive IDE Training Workbench

### Layout check

Phase 5 adds `guides/website/example/training-scenes.json`, rewrites Training in the canonical guide, and adds a session-history file. Splice helpers were deleted before commit.

### Result

No documentation move. Unused `.nht` slide CSS remains in the guide as dead rules; removing it is optional cleanup, not a layout move.

## Phase 6 - Maintainer Docs and Copy Contract

### Layout check

Phase 6 rewrites `guides/website/README.md` in place, extends `tests/guides/test_nexus_hub_guide.py`, adds Reference rows in the canonical HTML, and adds `docs/releases/v4/v4.2/development/guide-redesign-phase-6/`. No file moved. No installer-copied `scripts/*.py` was added.

### Result

No documentation move. The sibling portfolio remains outside this tree; the copy contract is documentation plus an optional env-gated diff.

## Phase 7 - Architecture Refactor, Known-Gaps, CI/CD

### Layout check

Phase 7 writes `docs/releases/v4/v4.2/development/last-phase-evidence.md` and a hallmark re-audit. It deletes unused `.nht` / `.ts-` CSS from the canonical guide (no matching markup). No documentation file moved. No `docs/testing/` or `docs/validation/` invented.

### Result

No documentation move. Dead slide-deck CSS pruned in place. Publication (push / PR) is gated on explicit approval.

## v4.2.1 Phase 1 - Contract, IA, and example freeze

**Date**: 2026-08-29
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md`

### Layout check

Phase 1 adds a dated v4.2.1 section to the existing content map, a v4.2.1 known-gaps subsection, and a session-history file. The v4.2.0 tables stay in the same content-map file, marked superseded. No scratch document is proposed for deletion. No `docs/testing/` or `docs/validation/` invented.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` | Active plan | Keep. |
| `docs/releases/v4/v4.2/development/guide-redesign-content-map.md` | Active contract | Keep; v4.2.1 section appended in place. |
| `docs/releases/v4/v4.2/known-gaps.md` | Active release gap ledger | Keep; new patch subsection, header unchanged. |
| `docs/releases/v4/v4.2/development/history/2026-08-29_v4.2.1-guide-visual-education-phase-1-contract.md` | Active phase evidence | Keep under the current version's development history. |

### Result

No duplicate, orphaned, scratch, or misplaced documentation was created by Phase 1. No file moved, and no cleanup change was approved or applied.

## v4.2.1 Phase 2 - Chrome, theme, and install terminals

**Date**: 2026-08-29
**Mode**: audit only; no files moved

Phase 2 edits the canonical guide HTML and the focused test file in place. Session history is the only new documentation file.

### Result

No documentation move.

## v4.2.1 Phase 3 - Home loop visual

**Date**: 2026-08-29
**Mode**: audit only; no files moved

Phase 3 edits the canonical guide HTML and the focused test file in place.

### Result

No documentation move.

## v4.2.1 Phase 4 - Foundations visual education

**Date**: 2026-08-29
**Mode**: audit only; no files moved

Phase 4 edits the canonical guide HTML and the focused test file in place.

### Result

No documentation move.

## v4.2.1 Phase 5 - Training slideshow and Glow Booth

**Date**: 2026-08-29
**Mode**: audit only; no files moved

Phase 5 adds `guides/website/example/glow-booth/`, `guides/website/example/glow-booth-shuffle-reference/`, and `guides/website/glow-booth.zip`. It rewrites Training in the canonical guide and updates `guides/website/README.md` plus the focused test file. Session history is the only new documentation file. `example/trivia-quiz/` stays on disk and is not taught. No `docs/testing/` or `docs/validation/` invented. No installer-copied `scripts/*.py` was added.

### Result

No documentation move. Temporary `_patch_phase5.py` was deleted before commit.

## v4.2.1 Phase 6 - Cheatsheets merge

**Date**: 2026-08-29
**Mode**: audit only; no files moved

Phase 6 removes Workflows and Reference from primary nav, adds `#page-cheatsheets`, and rewrites `guides/website/README.md` plus the focused test file. Temporary `_patch_phase6.py` was deleted before commit. No `docs/testing/` or `docs/validation/` invented.

### Result

No documentation move.

## v4.2.1 Phase 7 - Architecture refactor, known-gaps, CI/CD

**Date**: 2026-08-29
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md`

### Layout check

Phase 7 copies the v4.2.0 last-phase record to `docs/releases/v4/v4.2/development/last-phase-evidence-v4.2.0.md` and overwrites `docs/releases/v4/v4.2/development/last-phase-evidence.md` with the v4.2.1 record. It updates root `README.md` and `guides/website/README.md` in place. `example/trivia-quiz/` stays on disk. No `docs/testing/` or `docs/validation/` invented. No installer-copied `scripts/*.py` was added. No `.github/workflows/` edit.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.2/development/last-phase-evidence-v4.2.0.md` | Preserved prior-patch evidence | Keep. |
| `docs/releases/v4/v4.2/development/last-phase-evidence.md` | Active last-phase evidence | Keep; now the v4.2.1 record. |
| `docs/releases/v4/v4.2/development/history/2026-08-29_v4.2.1-guide-visual-education-phase-7-closeout.md` | Active phase evidence | Keep under the current version's development history. |

### Result

No documentation move. Publication (push / PR) is gated on explicit approval.
