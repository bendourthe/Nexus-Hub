# Known Gaps -- v3.6.0

**Status**: v3.6.0 is in active development on `feat/spec-kit-delta-adoption`. The `adoption-spec-kit` plan (`docs/v3.6.0/plans/adoption-spec-kit.md`) is in progress: Phase 1 (skill-native doctrine folds N2a + N3b), Phase 2 (the `base-*.md` parity-governance guard, N3a), and Phase 4 (the `/skills import` hygiene gate, N6) are complete; Phase 3 (N1a workflow-phase hook recipe) and Phase 5 (decline-durability + release) remain. Phase 4 was implemented ahead of Phase 3 at the maintainer's request -- the plan declares Phase 4's prerequisites as "None", so the two are independent -- and Phase 3 is tracked as an open item (NI-v36-1) so it is not lost to the out-of-order build. The two deliberate declines (N5 authentication framework, N1b third-party extension install) and the two deferred items (N4 self-upgrade CLI, N2b portable workflow engine) are recorded by Phase 5 (matrix rows + DF entries here).
**Last updated**: 2026-06-16 (adoption-spec-kit Phase 4)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.6.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 1 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 3 | 0 |
| QG | 0 | 0 |
| **Total** | **4** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| NI-v36-1 | NI | adoption-spec-kit Phase 4 (recorded while building Phase 4 ahead of Phase 3) | Phase 3 (N1a workflow-phase hook recipe) | Phase 3 of the plan -- the workflow-phase hook recipe (N1a): document how to approximate spec-kit's per-command `before_/after_` lifecycle hooks using ONLY Nexus-Hub's four supported events (SessionStart / PreToolUse / PostToolUse / Stop), plus at most one minimal opt-in example hook -- was NOT yet implemented when Phase 4 (N6) was built. Phase 4 was done first at the maintainer's request; the plan declares Phase 4's prerequisites as "None", so the order is safe, but Phase 3 remains outstanding. This is a pending sibling phase, not a skipped subtask of Phase 4. | Implement Phase 3 (N1a) before Phase 5 (decline-durability + release), since Phase 5's CHANGELOG enumerates N1a among the five adoptions. Run `/implement phase 3 of v3.6.0 adoption-spec-kit`. | Medium (blocks the plan's completeness; Phase 5 references N1a, so it must land before release) |
| WN-v33-1 | WN | carried forward from v3.3.0; re-confirmed adoption-spec-kit Phases 1-2, 4 | 1.3, 2.3, 4.3 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` were run by invoking the underlying validators and pytest directly. Re-confirmed for Phase 4 (the `/skills import` hygiene gate): the direct validate chain passed green (JSON catalog integrity 256 skills; orphan-bundle audit PASS; unicode-safety 0 errors; no-personal-paths exit 0; supply-chain-iocs exit 0; workflow-security exit 0; version-sync surfaces match 3.5.0; parity guard exit 0), the 42 new import-hygiene tests pass, and the full repo-level `tests/` suite reports 540 passed / 0 failed. `make lint`: ShellCheck is not on PATH, so `installer.sh` was verified with `bash -n` (clean) and `installer.ps1` with the `[Parser]::ParseFile` AST (clean). | Confirm CI `validate` + `tests` are green on the ubuntu runner (the new tests live under `tests/validators/`, which CI already runs). No code change expected. | Low (direct validator equivalents passed; the gate is exercised by 42 pytest cases) |
| WN-v36-1 | WN | adoption-spec-kit Phase 2; re-checked Phase 4 | 2.3, 4.3 | In Phase 2, running the full repo-level `tests/` suite on Windows surfaced 4 failures (`tests/installer/test_branch_flag.py` x3, `tests/validators/test_session_query_extract.py::test_discover_obsidian_vault_marker` x1) -- all invoke a bash `.sh` via `bash.EXE` that returns exit 127 when the script path contains spaces ("OneDrive - Supira"). In Phase 4 the suite was run from a checkout whose path has NO spaces, and all four PASS (540 passed / 0 failed), confirming the root cause is the space-containing path, not the tests. The warning is retained because the failure recurs on any checkout under a space-containing parent. | Optionally make the affected tests skip cleanly when the bash interpreter cannot resolve a space-containing path on Windows; otherwise no action (green on CI and on space-free checkouts). No production-code change. | Low (environment-only; reproduces only under space-containing paths; green here and on CI) |
| WN-v33-2 | WN | carried forward from v3.3.0 | n/a | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored, never committed), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate, and neither is touched by Phase 2. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | | | | |
