# Docs Cleanup Audit - v3.20.0 Phase 3

**Date**: 2026-08-23
**Mode**: audit only (no files moved)
**Plan**: `docs/v3/v3.20/plans/v3.20.0-adoption-agent-security-layers.md`

## Layout check

The v3.20 tree already matches the canonical minor-grouped layout:

- `docs/v3/v3.20/plans/`
- `docs/v3/v3.20/comparisons/`
- `docs/v3/v3.20/development/history/`
- `docs/v3/v3.20/known-gaps.md`

No stray comparison reports sit outside `comparisons/`. Session histories for this plan sit under `development/history/`.

## Disposition

| Path | Cat | Action |
|---|---|---|
| `plans/v3.20.0-adoption-agent-security-layers.md` | 4 active | Stay. Census 272 -> 275 reconciled in Phase 3. |
| `comparisons/v3.20.0-comparison-agent-security-layers.md` | 4 active | Stay. |
| `development/history/2026-08-23_adoption-agent-security-layers-phase-*.md` | 4 active | Stay. These are the plan's session records, not scratch. |
| `known-gaps.md` | 4 active | Stay. |
| `docs-cleanup-report.md` | 4 active | This audit. |

No Cat 1 (delete) or Cat 2 (archive) candidates in the v3.20 tree.

## Cross-cutting

`python scripts/check_docs_retention.py` reports nothing due for archival (canonical version 3.19.2, threshold two minors). Empty directories found in the working tree (`.antigravitycli`, `.claude/worktrees`, benchmark `.work` corpora) are local tooling, not catalog docs, and were left untouched.

## Project-layout detectors (non-docs)

- Empty catalog directories under the new or extended skills: none.
- Duplicate/orphan bundled files: `python scripts/validate_skills.py --bundles-only` PASS. `credential-brokering.md` is referenced from `agentic-endpoint-hardening/SKILL.md`.
- Structure complexity: no single-child chains introduced. Skills remain `SKILL.md` plus `references/` and `evals/` as elsewhere in the catalog.

## Apply gate

No moves proposed. Nothing to confirm.
