# CI Speed Phase 2

**Version**: v4.15.7
**Phase**: 2, Linux Test Matrix (delivered by PR #650; verified here)
**Started**: 2026-11-15T13:54:37-08:00
**Ended**: 2026-11-15T14:09:00-08:00 (work complete; the local commit follows immediately)
**Base**: `40f9b0b1c90ee48d2f2fc679b3bfd228ed2d4d74`, which already contains PR #650 (merge `c3c483d3b`; commits `0c1ca42d3`, `cefd7b0f5`, `e1514acaa`)

## Outcome

No code changed in this phase. PR #650 ("ci: split the slow Linux and Windows test jobs into shards with a partition proof") delivered T006 to T009 and the decision record for T005. Each task was verified against its acceptance check on the current tree and ticked; T005's measurement document was written here.

## Task verification

| Task | Acceptance check | Observed |
|---|---|---|
| T005 decision | Measured evidence, predicted minutes per leg, rejected options, decision record under `docs/decisions/` | `v4.15.7-shard-measurements.md` records the choice, the two plan options as rejected, and measured CI minutes per leg (all five Linux legs 3.6 to 15.2 min, limit 22). Decision record: `docs/decisions/implemented/tooling/2026-11-13-ci-test-shards-with-partition-proof.md` has Alternatives considered. Local per-file timings were not taken (machine not quiet); measured CI times replace them. |
| T006 family selection | `--only <family>` selects members; unknown name fails; a group named like a family is rejected | `tests/ci/test_ci_engine.py::test_only_family_*`, `test_unknown_only_name_still_fails_and_lists_families_and_groups`, `test_a_group_named_like_a_family_is_rejected` pass. |
| T007 profile shards | A `tests` family, `HOOK_HEAVY_FILES` constant, catch-all that ignores it, junit per shard, no workers added | `scripts/ci/profiles.py` defines `HOOK_HEAVY_FILES`, `HOOK_TESTS_HEAVY`/`HOOK_TESTS_REST`, family `tests` (core, validators, governance) and `--junitxml` on the hook shards. |
| T008 workflow matrix | Job id `tests` kept, `fail-fast: false`, per-leg artifacts and `--expect-artifact` entries, `ci-required` needs unchanged, no required context added | `.github/workflows/ci.yml` lines 233-296 (matrix legs `tests-validators`, `tests-governance`, `tests-core,extension-tests`) and the three `ci-test-reports-*` entries in `report`; `docs/policy/required-checks.json` unchanged. Read-only verification: no pipeline file was edited. |
| T009 partition proof | Node-ID proof, SHA-pinned actions, no new `permissions:`, exit 5 counts as failure | `tests/validators/test_ci_partition_proof.py` (the plan named `tests/workflows/`; PR #650 placed it under `tests/validators/`), `test_pytest_exit_five_no_tests_collected_counts_as_a_failure`. |

## Verification

| Check | Result | Meaning |
|---|---|---|
| `python scripts/ci/run.py --profile full --only tests --list` | Lists the three family groups (tests-core, tests-validators, tests-governance) with their commands and the host skips | `--only tests` selects exactly the shard family. |
| Partition proof, control | `assert_partition` holds for the delivered hook split | The proof passes on the real tree. |
| Partition proof, a hook test file excluded from every shard (`test_settings_guardrail_switches.py` removed from the heavy shard, still ignored by the rest shard) | Fails: "no shard runs ['catalog/hooks/tests/test_settings_guardrail_switches.py::...']" | A dropped test is caught. |
| Partition proof, the same file included in two shards | Fails: "heavy and rest both run [...]" | A duplicated test is caught. |
| `pytest` of the proof, `tests/ci`, report/cache/native-parity/guide-serial-shard workflow tests, required-gate and workflow-contract validators | 400 passed, 1 skipped in 321.5 s | Policy tests agree with the sharded profiles and workflow. |
| `python scripts/check_required_check_coverage.py` | OK, 10 declared contexts produced unconditionally | No required context was added or made conditional. |
| `python scripts/ci/run.py --profile fast` | 16 passed, 2 failed in 148.7 s | Both failures are mine and understood: `validate_no_personal_paths` flagged the worktree path in the Phase 1 history (fixed in this commit by editing `history/v4.15.7/phase-1.md`; the scan now reports no finding), and `check_registry_entries` still waits for the coordinator's `data/skills.json` delta D1. |
| Post-merge CI evidence | 10 full-scope runs after PR #650: every Linux leg 3.6 to 15.2 min; gate mean 29.2 min | The shard set meets the 22-minute leg rule in measured time. |

The two deliberate misplacements were run by a scratch script that imports the proof's own `_collect` and `assert_partition`; nothing in the repository was modified.

## CI Impact

None from this phase (no workflow, profile or test file edited). The existing pipeline already carries the matrix legs, per-leg artifacts and unchanged required contexts that the plan describes.

## Plan delta

Disposition: Incomplete, non-blocking. Evidence: the plan names option A (four legs) and a proof under `tests/workflows/`; PR #650 delivered a different but conforming shape (five Linux legs, proof under `tests/validators/`) and the decision is documented. Consequence: Phase 3's file claims shift from write to read-only verification, and the plan's shard-count wording is superseded by the measurements document.

## Deferred Final Validation

None added; the full profile runs once in 9B (T027).

## Open Work

- Local per-file Linux durations were not collected; the measured CI minutes make them unnecessary for the 22-minute rule.
