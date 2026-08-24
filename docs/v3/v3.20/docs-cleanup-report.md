# Docs Cleanup Audit - v3.20.2 Phase 7

**Date**: 2026-08-23
**Mode**: propose-then-apply (no moves)
**Plan**: `docs/v3/v3.20/plans/v3.20.2-interface-craft-skills.md`

## Layout check

`docs/v3/v3.20/` already matches the canonical minor-grouped layout (`plans/`, `comparisons/`, `development/history/`, `known-gaps.md`, `docs-cleanup-report.md`). Nothing to archive or relocate.

## Project cleanliness (outside docs/)

| Detector | Result |
|---|---|
| Empty directories in the six new skill trees + `hallmark-design/references/` | None |
| Thin `references/` restating only the body | None. Each reference file carries recipes, formulas, or tables the body links to |
| New `agents/openai.yaml` sidecars | None (cluster skills did not inherit D1) |

No Cat 1 deletes, Cat 2 archives, or path moves. Confirmation gate: apply was a no-op.

## Disposition

| Path | Cat | Action |
|---|---|---|
| `plans/v3.20.2-interface-craft-skills.md` | 4 active | Stay. |
| `comparisons/v3.20.2-comparison-interface-craft-skills.md` | 4 active | Stay. |
| `development/history/*interface-craft-skills-phase-*.md` | 4 active | Stay. |
| `known-gaps.md` | 4 active | Stay. |
| `docs-cleanup-report.md` | 4 active | This audit. |
