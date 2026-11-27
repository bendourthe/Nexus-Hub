# Harness Economics Phase 2

**Version**: v4.15.2
**Phase**: 2, Behavioral evaluation contract and fixtures
**Started**: 2026-11-15T13:33:24-08:00
**Ended**: 2026-11-15T13:50:48-08:00 (wall clock, local host time)
**Base**: Phase 1 commit `e963f9ee4b39c263977bb81580507418bce7eba1`

## Subtasks

| Task | Outcome |
|---|---|
| T007 | Durable contract written at `guides/reference/HARNESS_PAIRING_EVALUATION.md` with a dense header summary. |
| T008 | Valid, partial, and incomparable manifests added under `tests/fixtures/harness_pairings/`. |
| T009 | Trial and aggregate receipt fixtures added (valid and partial runs). |
| T010 | Modes, objective metrics, measurer-derived instruction figures, organic selection, intervals, gates, and Pareto policy defined in the guide. |
| T011 | Argv, containment, environment, redaction, secret, and cleanup boundaries defined in the guide. |
| T012 | Independent oracle and 17 adversarial mutations; 65 contract tests pass. |
| T013 | `eval-pipeline-audit` routes missing behavioral evidence to the evaluator; the audit skill keeps no runner mechanics. |
| T014 | Stabilization: focused tests, bundle validator, unicode and docs checks, one local commit. |

## Evidence path mapping

Evidence files use the coordinator-mapped v4.15 names (`v4.15.2-phase2-evidence.md`), not the plan's stale v4.17 paths; see the Phase 1 evidence file for the full table.

## Queue re-assessment

No drift beyond Phase 1's record. The two predecessor dependencies the plan names (v4.16.2 cost guidance, v4.19.0 evidence vocabulary) are not landed; recorded as dependencies in the Phase 2 evidence file, not assumed.

## Model-routing pre-flight

The plan recommends frontier tier at max effort for this phase. This unattended worker ran on its session model and could not switch posture mid-run. Recorded as `verification effort not applied: unattended worker session`; the adversarial mutation suite is the explicit verification behavior requested.

## Plan delta

Disposition: Incomplete, non-blocking. The plan does not say where the independent oracle lives; it is placed under `tests/fixtures/harness_pairings/oracle.py` so Phase 3 tests can load it by path. Consequence for remaining phases: Phase 3's runner implements its own validation and aggregation and its tests compare against this oracle; Phase 4 and 5 are unaffected.

## CI impact

None: no pipeline file, command, dependency, environment variable, or installer change.

## Gate note

The first fast-profile run failed one step, `validate_no_personal_paths`, on local path strings in Phase 1 files. They were fixed in the Phase 1 commit before any push (amended once), and the step passed afterward. Lesson recorded: run the personal-path check before the first commit of any evidence file.

## Deviations

None. No `# DEVIATION:` markers.

## Next steps

Phase 3 builds the isolated local pairing runner against this contract.
