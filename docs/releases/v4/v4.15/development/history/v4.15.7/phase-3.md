# CI Speed Phase 3

**Version**: v4.15.7
**Phase**: 3, Windows Job Split (delivered by PR #650; verified here)
**Started**: 2026-11-15T14:10:06-08:00
**Ended**: 2026-11-15T14:12:35-08:00 (work complete; the local commit follows immediately)
**Base**: `40f9b0b1c90ee48d2f2fc679b3bfd228ed2d4d74` (contains PR #650, merge `c3c483d3b`)

## Outcome

No profile, workflow or test file changed. PR #650 split `tests-windows` into `tests-windows` and `tests-windows-hooks-rest`, and the Windows validator corpus into four jobs (`tests-windows-validators`, `-2`, `-3`, `-4`). T010 to T013 were verified and ticked under the plan's cut-line, with one residual job above the 22-minute target recorded as a known gap and a ready diff.

## Task verification

| Task | Acceptance check | Observed |
|---|---|---|
| T010 measurements | Per-file medians from a quiet machine, or the cut-line | Cut-line applied. Other sessions were running `scripts/ci/run.py --profile full` and `pytest tests/skills` on this workstation, so no quiet local run was possible. `v4.15.7-shard-measurements.md` records per-command CI times (3 runs) and measured job minutes (10 runs) instead, and states that per-file Windows data does not exist in CI because validator commands write no JUnit file. |
| T011 profile groups | Hooks split with `HOOK_HEAVY_FILES`; each validator group keeps `-p xdist -n 2 --dist loadfile` and its timeout; junit per shard | `WINDOWS_HOOKS` and `WINDOWS_HOOKS_REST` use the shared constant; `INTERPRETERS` stays with the lighter group per profile. `windows-validators` (a-c plus co), `-2` (d-l plus p-z), `-3` (minor-execution) and `-4` (m-o) are separate groups. Difference from the plan text: a-c and co share one group, the source of the residual gap below. |
| T012 jobs | Separate jobs wired into `report` and `ci-required`, artifacts expected, no required context added | `.github/workflows/ci.yml` defines the jobs; `tests-windows-hooks-rest` and `tests-windows-validators-2/-3/-4` appear in `report` (`--expect-artifact` lines 1133 to 1138) and in `ci-required`; `docs/policy/required-checks.json` unchanged. Read-only verification: no pipeline file was edited. |
| T013 partition proof and policy tests | Windows proof and parity tests pass; a misplacement fails them | `test_windows_hook_shards_partition_the_hook_suite` and `test_windows_validator_shards_partition_the_validator_suite` ran on this Windows host in the Phase 2 batch (400 passed, 1 skipped), with `test_ci_native_profile_parity.py`, `test_ci_required_gate.py`, `test_ci_workflow_contract.py` and `test_ci_report_job.py`. |

## Verification

| Check | Result | Meaning |
|---|---|---|
| Windows validator partition, control | Holds across the six validator shard commands | The proof passes on the real tree. |
| Same proof with the `co` shard no longer ignoring the a-c range | Fails: "validators a-c (Windows) and validators co (Windows) both run [...]" | A file assigned to two quarters is caught. |
| Same proof with the p-z shard also ignoring `test_p*` | Fails: "no shard runs [...test_parallel_member_implementation.py...]" | A dropped validator file is caught. |
| Predicted versus measured minutes | See the Windows table in `v4.15.7-shard-measurements.md` | Seven of eight Windows jobs average 22 minutes or less; `tests-windows-validators` averages 26.6 (max 30.1). |
| Gate after PR #650 | `ci-required` mean 29.2 min (median 29.2, max 31.2) over 10 runs | Meets the 30-minute goal on average, with little margin. |
| `python scripts/ci/run.py --profile fast` | 17 passed, 1 failed in 19.0 s (warm, quiet machine) | The one failure is `check_registry_entries`, awaiting the coordinator's `data/skills.json` delta D1. |

The two misplacements ran from a scratch script that reuses the proof's own `_collect` and `assert_partition`; no repository file was modified.

## CI Impact

None from this phase. The Windows jobs, their wiring and the 31-job fan-out (limit 40) already exist; required contexts are unchanged.

## Plan delta

Disposition: Incomplete, non-blocking. Evidence: the plan expects one validator quarter per job and a measurement-driven split; the delivered split is evidence-based at command level and leaves a-c and co together. Consequence for remaining phases: Phase 5's after-measurement should record the gate against the 30-minute target and carry the `tests-windows-validators` rebalance (sensitive deltas S1) as a known gap; no later phase depends on it.

## Deferred Final Validation

None added; the full profile runs once in 9B (T027).

## Open Work

- `DF`: rebalance `tests-windows-validators` (a-c into its own job). Needs a pipeline-file edit outside this worker's authority; the exact diff is in the sensitive deltas file (S1).
- Add `--junitxml` to the Windows validator commands so the next integration run yields per-file timings for any finer split.
