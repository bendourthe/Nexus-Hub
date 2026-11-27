# CI Speed Phase 5

**Version**: v4.15.7
**Phase**: 5, Architecture Refactor, Known-Gaps Reconciliation, and CI/CD (local work only; no publication)
**Started**: 2026-11-15T14:38:04-08:00
**Ended**: 2026-11-16T07:06:22-08:00 (work complete; the local commit follows immediately)
**Base**: `40f9b0b1c90ee48d2f2fc679b3bfd228ed2d4d74`

## Outcome

The final-phase duties T019 to T022 and T024 to T027 were run and are quoted in `v4.15.7-last-phase-evidence.md`. T023 (pipeline reconciliation) found three differences and could not apply them, because the three pipeline files were not admitted for writing. T028 (publication) was not performed: this run stops at local work.

## Task status

| Task | State | Evidence section |
|---|---|---|
| T019 refactor | Done, ticked: scan quoted, no move needed | Architecture refactor |
| T020 known gaps | Done locally, ticked: dispositions quoted; the ledger edits are coordinator-owned (D2, D5, D6) | Known-gaps reconciliation |
| T021 living docs | Done, ticked: handbook precondition passes, both decision records exist | Living docs architecture |
| T022 git-tree hygiene | Done, ticked: report only | Git-tree hygiene |
| T023 CI reconciliation | Not complete, unticked: three differences, diffs verified in a scratch clone | CI/CD coverage |
| T024 Tier 3 deep pass | Done, ticked: 12 of 12 features exercised, 1 fix cycle of 3, residual items recorded | Tier 3 deep pass |
| T025 Goal review | Done, ticked: Goal partly met, headline measurement pending publication; gaps recorded | Goal-vs-codebase review |
| T026 manual suggestions | Done, ticked | Human/manual testing suggestions |
| T027 full gate | Not complete, unticked: the full suite is deferred to hosted CI (coordinator decision; host limit WN-1); fast profile, focused tests and Python 3.11 checks ran | Full-suite testing and stabilization |
| T028 publication | Not performed, unticked | Publication and integration |

## Verification

| Check | Result | Meaning |
|---|---|---|
| `python scripts/ci/run.py --profile fast` | 17 passed, 1 failed in 100.3 s | The one failure is `check_registry_entries` (delta D1). |
| Focused tests, Python 3.12 and 3.11 | 115 passed, 1 skipped; 105 passed | No difference between interpreters. |
| `ruff check` on the script and its tests | All checks passed | Lint clean after the hardening. |
| `python -m pytest tests/skills/test_ci_latency_audit.py` | 32 passed | Includes three regression tests for the adversarial findings. |
| `nexus-hub attribution check` | VERIFIED | Run before the commit. |

## CI Impact

No pipeline file changed. The reconciliation's three differences (cache seeding and blobless checkout, pre-push stage, Windows validator balance) are carried as sensitive deltas S1 to S3.

## Plan delta

Disposition: Incomplete, blocking for T014, T017, T018, T023 and T028 only. Evidence: the plan expects the final phase to apply approved pipeline changes and publish; the run holds no permission for three pipeline files and no publication approval. Consequence: those tasks stay open and are recorded as known gaps with a ready, scratch-verified diff and the exact next steps; the plan Goal's headline measurement waits for publication.

## Deferred Final Validation

The full gate result (T027) is recorded in the evidence file. Anything the gate could not run locally is listed there.

## Open Work

- Coordinator: apply D1 to D7 and, with the typed permission, S1 to S3; then rerun the fast profile and the seven pipeline policy test files; tick T014, T015, T017, T018, T023.
- Publication (T028) and the after-measurement.
