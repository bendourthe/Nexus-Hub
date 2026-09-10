# Session history - v4.10.0 Phase 1

**Plan**: [v4.10.0-plan-queue-continuity](../../plans/v4.10.0-plan-queue-continuity.md)
**Phase**: 1 - Queue enumeration and baseline
**Date**: 2026-09-10
**Branch**: `feat/v4.10.0-plan-queue-continuity`
**Evidence**: [phase-1-enumeration.md](../phase-1-enumeration.md)

## Context

This plan was authored in the v4.11.0 slot and swapped to v4.10.0 on the same day so the ordering capability would ship before the plans it is meant to sequence. That swap was the third manual renumber of the session and the first performed while the displaced plan was mid-implementation; both facts are now design input for Phase 5 rather than incidental history.

## Subtasks completed

- **T001** - Baselined the real inventory (99 plan files; the evidence first said 101, corrected in Phase 6), reconstructed the three renumbers from `git log --diff-filter=R`, and enumerated seven distinct reference classes plus two traps that a blanket rewrite hits.
- **T002** - Added `scripts/enumerate_plan_queue.py`, stdlib only, with numeric version sorting, whole-tree scanning, status reporting, and touched-path extraction. Declared repo-internal in `DEV_ONLY_SCRIPTS`.
- **T003** - Added 18 fixture tests covering both historical sort and scope traps plus the full reporting contract.
- **T004** - Ran the tests, the installer-smoke suite, ruff, and the fast profile; confirmed by inspection that the new test path is already collected.

## Files changed

- `scripts/enumerate_plan_queue.py` - new.
- `tests/validators/test_enumerate_plan_queue.py` - new, 18 tests.
- `catalog/hooks/tests/test_installer_smoke.py` - one `DEV_ONLY_SCRIPTS` entry with its reason.
- `docs/releases/v4/v4.10/development/phase-1-enumeration.md` - new, phase evidence.

## Test results

18 new tests pass. Installer-smoke 33 pass. Ruff clean after formatting and three automatic fixes. Fast profile: 13 passed, 0 failed. The script exits 0 against the live tree.

## Deviations

None requiring a `# DEVIATION:` marker. Two design corrections were made inside the task's stated latitude and are recorded in the evidence: the task-line pattern requires a trailing space, and a missing `Status` line is a note rather than an error.

## Plan delta

**Disposition: Incomplete (non-blocking).**

Evidence: the plan's D1 says the script must report "a malformed or unreadable plan as an explicit finding rather than omitting it from the queue". Implementation showed that phrase conflates two different conditions with opposite correct handling. A plan that cannot be read is genuinely exceptional and should fail the exit code. A plan with no `Status` line is not exceptional at all: **83 of 99 plans** in the live tree have none, because the header convention post-dates most of them. Treating the second as a failure would make every real run exit 1, which destroys the signal D1 was trying to create.

The implementation therefore splits the two: `error` for unreadable, exit 1; `note` for undeclared status, exit 0, summarised in the table footer. Both remain explicit findings and neither plan is omitted, so D1's actual intent is satisfied.

A second, smaller gap: the plan's own T001 prompt and the ad-hoc verification during authoring both used a `grep -c '^- \[ \] T'` shape that counts exit-checklist items beginning with "The". The plan's stated task count was right, but the method quoted in it was not. The script's pattern is correct and a test pins it.

Consequence for remaining phases: Phase 2's ranking must not treat open-task count as membership, which the evidence now states explicitly and the script's output footer carries. No plan text needs editing, because the D1 wording is satisfied by the split rather than contradicted by it. This is recorded here rather than escalated.

## CI/CD

No pipeline change. One new test path under `tests/`, already collected by the `TESTS` group's `pytest tests` step at `scripts/ci/profiles.py:227`, confirmed by inspection rather than assumed. One new script, declared repo-internal, so no installer copy step applies; the installer-smoke suite proves the declaration is consistent. Nothing carried forward to Phase 6.

## Next steps

Phase 2 (T005-T007) authors `catalog/skills/workflow/plan-queue-assessment/SKILL.md`, the single owner for staleness verdicts and the ranking rule, registers it in the three registries, and applies it to the real five-plan queue as authoring evidence.
