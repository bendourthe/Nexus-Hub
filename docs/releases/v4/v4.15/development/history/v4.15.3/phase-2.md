# Behavioral Harness Phase 2

**Version**: v4.15.3
**Phase**: 2, Consumer preservation
**Started**: 2026-11-16T23:42:00-08:00
**Ended**: see the commit time of this phase (local host time)
**Base**: Phase 1 commit `b643cbb02`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.3`

## Subtasks

| Task | Outcome |
|---|---|
| T008 | Security evidence extension added to `findings-schema.md`; legacy findings unchanged. |
| T009 | `validator-template.md` keeps pending items visibly pending and exempts extension findings from the refutation pass. |
| T010 | `multi-agent-code-review/SKILL.md` states evidence ownership and pending visibility. |
| T011 | `review-fanout-workflow.js` associates only context-bound projections, bypasses the gate for extension findings, and returns tiers, coverage and caveats. |
| T012 | `final-report/SKILL.md` retains coverage limits and separates confirmed, pending and rejected results. |
| T013 | `test_review_evidence_consumers.py`: 11 tests against the real projector with legacy, foreign, forged empty-complete and mutation controls. |
| T014 | Verified locally; one local commit. |

## Deviations

None. Native workflow execution was not attempted; the runtime boundary is stubbed and named in the evidence file. v4.17.1's general unrefuted and incremental rules stay out of scope; the future bridge is recorded in `v4.15.3-admission.md`.

## CI impact

None. See `v4.15.3-phase-2-evidence.md`.
