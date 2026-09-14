# Docs cleanup report - v4.12 Phase 1

**Active version**: v4.12.0
**Mode**: audit
**Scope**: Phase 1 release records and proposed decision; full docs inventory and Git-index-scoped refgraph retained externally.

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 0 |
| Cat 3 (leave in place) | 1 |
| Cat 4 (active) | 7 |
| Total | 8 |

## Dispositions

| Path | Category | Reason |
|---|---|---|
| `docs/releases/v4/v4.12/development/attribution-inventory.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/development/attribution-policy.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/development/history/2026-09-14-phase-1-attribution-checker.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/development/phase-1-queue-assessment.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/known-gaps.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/plans/v4.12.0-sole-contributor-attribution.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/releases/v4/v4.12/docs-cleanup-report.md` | Cat 4 | Active release evidence; preserve in place. |
| `docs/decisions/proposed/process/2026-09-06-sole-contributor-history-rewrite.md` | Cat 3 | Append-only proposed decision; preserve until publication disposition. |

## Cat 3 refresh queue

No stale document introduced by this phase. The proposed decision awaits the final publication disposition.

## Lifespan contradictions

No contradiction in the phase scope: v4.12 is open, the decision is proposed, and no frozen historical document was modified.

## Detector evidence

`audit-docs.py inventory --root docs --repo-root .` inventoried 2407 files and 5 initial v4.12 files. The helper's `cmd_refgraph` completed for `docs/releases/v4/v4.12` with its walk restricted to `git ls-files` (all staged Phase 1 files included); raw records are retained in `../Nexus-Hub-backups/2026-09-14-pre-v4.12-cleanup/phase1-docs-inventory.json` and `phase1-docs-refgraph.json`. All seven staged v4.12 documents were scanned; the compact result contains the two with inbound references. Later phase history and this report are accounted for in the table. The unrestricted and release-scoped filesystem walks were stopped after exceeding the proportional phase window. Reusing the helper with the Git index excluded unrelated untracked generated data; this is a scoped source-reference result, not an untracked-files audit. No files were moved or deleted.

## Target tree preview

Retain `docs/releases/v4/v4.12/{plans,development,known-gaps.md,docs-cleanup-report.md}` and the proposed process decision. Living DEVLOG/todos remain in place.

## Self-classification

This report is Cat 4 active release evidence; it freezes at release close.

## Phase 2 addendum - 2026-09-14

The phase-scoped inventory contains 9 active v4.12 documents. The same helper reference calculation, restricted to Git-indexed sources, completed for the staged tree. New `development/rewrite-backup.md` and `development/history/2026-09-14-phase-2-history-rewrite.md` are Cat 4 active release evidence. No delete, archive, stale-refresh or lifespan-contradiction finding applies to these new records. No file moved. The earlier Phase 1 table remains its dated inventory, not the current total. Detector records are retained beside the Phase 2 mirror as `phase2-docs-inventory.json` and `phase2-docs-refgraph.json`.
