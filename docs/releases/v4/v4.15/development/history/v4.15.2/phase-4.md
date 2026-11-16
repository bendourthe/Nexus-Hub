# Harness Economics Phase 4

**Version**: v4.15.2
**Phase**: 4, Provider-aware Claude `AGENTS.md` convergence
**Started**: 2026-11-15T14:15:45-08:00
**Ended**: 2026-11-15T15:38:25-08:00 (wall clock, local host time)
**Base**: Phase 3 commit

## Subtasks

| Task | Outcome |
|---|---|
| T025, T054 | Vendor contract re-verified 2026-11-15; capability decision object and policy entries written; `instructionFiles` VERIFIED and not seeded. |
| T026, T027 | `base-agents.md` and the section-level inventory (four consumers, three recorded blocked migrations). |
| T028, T029 | Shared-owner seam in `base.py`, Claude's scope-aware install and explicit migration, Codex, Cursor, and OpenCode as consumers, organization-block and teardown protection. |
| T030, T031 | One checklist row in each installer (BOM kept; parse-checked, not executed). |
| T032, T033 | Capability-aware harness audit and tests. |
| T034, T035, T037, T038, T040 | Capability matrix, migration-state, lifecycle, contract, and parity tests. |
| T039 | Done in the follow-up commit after the permission. |
| T036 | Done in the follow-up commit after the maintainer permitted the extra paths. |
| T041, T055 | Synthetic before-and-after through the Phase 3 evaluator; DF-1 left open with the missing evidence named. |
| T042 | Stabilization, observation of the runner end to end, one local commit. |

## Evidence path mapping

Evidence files use the coordinator-mapped names under `docs/releases/v4/v4.15/development/` (`v4.15.2-phase4-evidence.md`, `v4.15.2-shared-agents-inventory.md`, `v4.15.2-claude-agents-evaluation.md`), not the plan's v4.17 paths.

## Queue re-assessment

No new overlap with v4.15.1 or v4.15.4. v4.15.6 overlaps on both installers, the template directory, the smoke postcondition test and checker, and the integrations directory; sequencing is the coordinator's.

## Model-routing pre-flight

The plan recommends frontier tier at max effort. This unattended worker ran on its session model and could not switch posture. Recorded as `verification effort not applied: unattended worker session`. The capability matrix, the migration-state tests, the live probe observation, and the two-shell parse checks were the explicit verification behaviors.

## Plan delta

Disposition: Wrong (two vendor facts) and Incomplete (claims), non-blocking. Details are in the Phase 4 evidence file: the plugin ID is now `cc-plugin-agents-md@builtin` (read alongside the legacy ID), the vendor page lists three residual differences rather than eight, and the new template, the roster tests, the fingerprints, and the smoke checker need edits outside the admitted write set, delivered as verified coordinator patches. Consequence for Phase 5: the final gate records six roster-related failures as caused by the missing coordinator delta and verifies green with it applied locally.

## CI impact

Two installer edits (one checklist row each), no pipeline change. New opt-in environment variables documented in the policy entry.

## Deviations

None in code. Two places where the plan's wording was not followed literally: the persisted decision lives beside the install manifest at `.nexus-hub/claude-instruction-decision.json` and is tracked by it, because `manifest.py` is not in the admitted claims; and the installer scripts were parse-checked but not run, per the run rules.

## Next steps

Phase 5: architecture refactor scan, known-gaps reconciliation, living-doc check, git hygiene, CI/CD reconciliation, Tier 3 deep pass, Goal review, full gate, and local completion.
