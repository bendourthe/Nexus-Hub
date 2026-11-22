# Behavioral Harness Phase 1

**Version**: v4.15.3
**Phase**: 1, Evidence projection
**Started**: 2026-11-16T23:32:59-08:00
**Ended**: see the commit time of this phase (local host time)
**Base**: `0f62fe8d48b411a8ee3b63aec91b4f0f5ba4a957`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.3`

## Subtasks

| Task | Outcome |
|---|---|
| T001 | Admission, predecessor effects, gap inputs and literal claims recorded in `v4.15.3-admission.md`. |
| T002 | Projection contract written in `security-review/references/generic-review-projection.md`. |
| T003 | Hand-written valid and hostile controls in `tests/fixtures/review-evidence/v4.15.3/cases.json`. |
| T004 | `project-review-findings.py` added, reusing the shared validator and strict decoder. |
| T005 | 21 CLI tests including foreign, empty-complete and evidence-drop controls. |
| T006 | Script and reference linked from `security-review/SKILL.md`; recursive installer distribution needs no edit. |
| T007 | Verified locally; one local commit. |

## Deviations

The fixture oracle uses the existing golden envelopes under `tests/fixtures/security-audit/envelopes/`; the plan's fixture path holds only the case table. No plan prose changed.

## CI impact

None. See `v4.15.3-phase-1-evidence.md`.
