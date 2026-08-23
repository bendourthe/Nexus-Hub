# Docs Cleanup Audit - v3.20.1 Phase 1

**Date**: 2026-08-23
**Mode**: audit only (no files moved)
**Plan**: `docs/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md`

## Layout check

The v3.20 tree already matches the canonical minor-grouped layout:

- `docs/v3/v3.20/plans/`
- `docs/v3/v3.20/comparisons/`
- `docs/v3/v3.20/development/history/`
- `docs/v3/v3.20/known-gaps.md`

No stray comparison reports sit outside `comparisons/`. This phase did not create scratch docs.

## Disposition

| Path | Cat | Action |
|---|---|---|
| `plans/v3.20.1-adoption-cybersecurity-skills.md` | 4 active | Stay. |
| `comparisons/v3.20.1-comparison-cybersecurity-skills-library.md` | 4 active | Stay. |
| `development/history/2026-08-23_adoption-cybersecurity-skills-phase-1-framework-conformance.md` | 4 active | Stay. Session record, not scratch. |
| `known-gaps.md` | 4 active | Stay. Gained a v3.20.1 subsection. |
| `docs-cleanup-report.md` | 4 active | This audit. |

No Cat 1 (delete) or Cat 2 (archive) candidates from this phase.

## Cross-cutting

`python scripts/check_docs_retention.py` is advisory and was not required to archive anything for this phase. Coverage-map artifacts (`docs/framework-coverage.md`, `docs/attack-navigator-layer.json`) are Phase 2 deliverables and were not written here.

## Apply gate

No moves proposed. Nothing to confirm.
