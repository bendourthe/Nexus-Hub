# Known Gaps -- v3.6.0

**Status**: v3.6.0 is in active development on `feat/spec-kit-delta-adoption`. The `adoption-spec-kit` plan (`docs/v3.6.0/plans/adoption-spec-kit.md`) is in progress: Phase 1 (skill-native doctrine folds N2a + N3b) and Phase 2 (the `base-*.md` parity-governance guard, N3a) are complete; Phases 3-5 remain. The two deliberate declines (N5 authentication framework, N1b third-party extension install) and the two deferred items (N4 self-upgrade CLI, N2b portable workflow engine) are recorded by Phase 5 (matrix rows + DF entries here).
**Last updated**: 2026-06-16 (adoption-spec-kit Phase 2)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.6.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 3 | 0 |
| QG | 0 | 0 |
| **Total** | **3** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v33-1 | WN | carried forward from v3.3.0; re-confirmed adoption-spec-kit Phases 1-2 | 1.3, 2.3 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` were run by invoking the underlying validators and pytest directly. Re-confirmed for Phase 2 (the `check_base_template_parity.py` guard): the direct chain passed green (JSON catalog integrity 256 skills; orphan-bundle audit PASS; unicode-safety 0 errors; no-personal-paths exit 0; workflow-security exit 0; version-sync six surfaces match 3.5.0; the new parity guard exit 0 on the five in-sync templates). | Confirm CI `validate` is green on the ubuntu runner (the parity guard was added to `ci.yml` as a step after version-sync, so it now runs there too). No code change expected. | Low (direct validator equivalents passed; the guard itself is exercised by 9 pytest cases) |
| WN-v36-1 | WN | adoption-spec-kit Phase 2 | 2.3 | Running the full repo-level `tests/` suite locally on Windows surfaced 4 PRE-EXISTING failures unrelated to this phase: `tests/installer/test_branch_flag.py` (3 cases) and `tests/validators/test_session_query_extract.py::test_discover_obsidian_vault_marker` (1 case). All four invoke a bash `.sh` script via `bash.EXE`, which returns exit 127 because the system bash cannot resolve a script path containing spaces ("OneDrive - Supira ...") -- the referenced scripts exist on disk. They are a Windows-host shell-invocation limitation, not a logic defect, and pass on the CI ubuntu runner. Phase 2's own 9 parity tests and the other 485 repo-level tests pass (494 passed, 4 failed locally). | Confirm the four tests pass on the CI ubuntu runner; optionally make the affected tests skip cleanly when the bash interpreter cannot resolve a space-containing path on Windows. No production-code change. | Low (pre-existing; environment-only; green on CI; isolated to bash-invoking tests Phase 2 did not touch) |
| WN-v33-2 | WN | carried forward from v3.3.0 | n/a | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored, never committed), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate, and neither is touched by Phase 2. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | | | | |
