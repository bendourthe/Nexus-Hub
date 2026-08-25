# Docs Cleanup Audit - v3.21.0 Phase 5

**Date**: 2026-08-24
**Mode**: audit plus living-docs scaffold (no versioned-tree moves)
**Plan**: `docs/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md`

## Layout check

Canonical minor-grouped layout unchanged. `check_doc_colocation.py` reported OK. Retention reports nothing due while the plugin version is still 3.20.3.

## Living-docs scaffold (this phase)

| Path | Cat | Action |
|---|---|---|
| `docs/README.md` | 4 living | Created. Index of living vs versioned vs archive. |
| `docs/handbooks/README.md` | 4 living | Created. Honest catalog note; no fake atlas. |
| `docs/handbooks/markdown/.gitkeep` | 4 living | Created. |
| `docs/handbooks/html/.gitkeep` | 4 living | Created. |
| `docs/decisions/` | 4 living | Stay (already present). |
| `docs/testing/`, `docs/validation/` | self-gated | Not invented. |

## Retention apply

Not due.

## Disposition

| Path | Cat | Action |
|---|---|---|
| `plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md` | 4 active | Stay. |
| `development/last-phase-evidence.md` | 4 active | Stay. Required last-phase artifact. |
| `development/history/` | 4 active | Stay. |
| `docs/v3/v3.17/development/history` (empty) | leftover | Reported; not deleted. |
