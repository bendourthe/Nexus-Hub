# Harness Economics Phase 3

**Version**: v4.15.2
**Phase**: 3, Isolated local pairing runner
**Started**: 2026-11-15T13:52:51-08:00
**Ended**: 2026-11-15T14:14:17-08:00 (wall clock, local host time)
**Base**: Phase 2 commit

## Subtasks

| Task | Outcome |
|---|---|
| T015 | Runner preflight, manifest validation, executable discovery, and `--dry-run`. |
| T016 | Workspace hygiene with sentinel cleanup; live modes fail closed behind a missing isolation backend. |
| T017 | Shell-free execution, bounded output, process-tree termination, spend-control rules. |
| T018 | Trusted-root evaluator, tamper detection, normalized fingerprints. |
| T019 | Redaction before persistence, immutable receipts, aggregation, escaped report. |
| T020 | Eleven fake-adapter behaviors and the echo workload. |
| T021 | Credential-free Claude Code and Codex profiles. |
| T022 | 36 end-to-end tests. |
| T053 | Synthetic `full` against `pointer` pair with measurer-derived payload figures. |
| T023 | Repository-local runner documentation and the explicit live-run gate. |
| T024 | Stabilization, end-to-end observation, one local commit. |

## Evidence path mapping

Phase evidence is `v4.15.2-phase3-evidence.md` under `docs/releases/v4/v4.15/development/`, the coordinator-mapped name, not the plan's `phase-3-evidence.md` under the v4.17 tree.

## Queue re-assessment

No drift: v4.15.1 and v4.15.4 write disjoint paths. The only shared path with v4.15.6 is `catalog/hooks/tests/test_installer_smoke.py` (one added line in a set literal), flagged for the coordinator.

## Model-routing pre-flight

The plan recommends frontier tier at max effort. This unattended worker ran on its session model and could not switch posture. Recorded as `verification effort not applied: unattended worker session`. The hostile-adapter matrix, the canary-secret scan, the process-tree check, and the independent oracle comparison were the explicit verification behaviors.

## Plan delta

Disposition: Incomplete, non-blocking, with one addition to the contract.

Evidence: the plan names five outcomes in the receipt and says an adapter's attempt to change evaluator code is a "containment failure"; the Phase 2 enum had no such value. `containment-failure` was added to the oracle's outcome set and the guide in this phase.

Second finding: the plan says the trusted root is "read-only". Synthetic mode cannot enforce that without making the adapter's write fail silently, which would hide the attempt. The runner hashes the root before and after each adapter and treats a change as a containment failure; enforcement is a live isolation-backend duty. Documented in the guide.

Third finding: the first real `conformance` run exposed a Windows defect (the bare name `claude` is not launchable by `CreateProcess`). The runner now resolves the executable to its full path and turns any launch failure into a typed non-result.

Consequence for remaining phases: none for Phase 4. The final phase records POSIX coverage of the runner as a known gap.

## CI impact

None to pipeline files. One new Windows-heavy test file; see the evidence file.

## Deviations

None.

## Next steps

Phase 4 converges supported Claude project sessions on one shared `AGENTS.md` owner.
