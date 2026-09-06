# Docs Cleanup Audit - v3.20.3 Phase 6

**Date**: 2026-08-24
**Mode**: propose-then-apply
**Plan**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`

## Layout check

`docs/v3/v3.20/` already matches the canonical minor-grouped layout (`plans/`, `comparisons/`, `development/history/`, `known-gaps.md`, `docs-cleanup-report.md`). The Claude marketplace submission draft lives at `development/claude-marketplace-submission.md` (Cat 4, stay).

## Retention apply

`scripts/check_docs_retention.py` reported `docs/v3/v3.18/development/history/` (17 files) as two minors behind v3.20. Per `docs/policy/docs-retention.md`, only `history/` ages out.

Applied:

- 17 git renames to `docs/archive/v3/v3.18/development/history/`
- Four DEVLOG index history links for v3.18.0-v3.18.3 now point at the archive
- Two self-path rows inside archived presentify histories updated
- Empty live `history/` directory removed
- Re-check: `nothing due for archival`

Plans, comparisons, known-gaps, and non-history `development/` files for v3.18 stay in the live tree.

## Project cleanliness (outside docs/)

| Detector | Result |
|---|---|
| Empty directories in Phase 2 skill trees (`design-interview`, `setup-wizard-generator`, `decision-questionnaire`) and `docs/policy/out-of-scope/` | None |
| Duplicate plugin marketplace schemas | Resolved in Phase 5 (rewrote `.claude-plugin/marketplace.json`) |
| `_tmp*` leftovers | None |

No Cat 1 deletes. Confirmation: archive apply is the retention policy, not a discretionary rearrange of the active tree.

## Disposition

| Path | Cat | Action |
|---|---|---|
| `plans/v3.20.3-skills-craft-and-prime-agent.md` | 4 active | Stay. |
| `comparisons/v3.20.3-comparison-skills-craft-and-prime-agent.md` | 4 active | Stay. |
| `development/history/*skills-craft-phase-*.md` | 4 active | Stay. |
| `development/claude-marketplace-submission.md` | 4 active | Stay. Maintainer packet; not a session history. |
| `known-gaps.md` | 4 active | Stay. |
| `docs/v3/v3.18/development/history/*` | 2 archive | Moved. |

---

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
