# Known Gaps -- v3.4.0

**Status**: v3.4.0 is in active development on `develop`. The `model-routing` plan (`docs/v3.4.0/plans/model-routing.md`) is complete (all 4 phases); the `adoption-nessie-and-agency-agents` plan (`docs/v3.4.0/plans/adoption-nessie-and-agency-agents.md`) is in progress (Phase 2 of 5 complete -- Phase 1 the `context-pack-builder` skill, Phase 2 the Aider + Windsurf platform integrations). The release cut (version bump + tag) is handed to `/update release` and not yet run.
**Last updated**: 2026-06-15 (adoption-nessie-and-agency-agents Phase 2)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.4.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 1 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 2 | 0 |
| QG | 0 | 0 |
| **Total** | **3** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| DF-v34-1 | DF | model-routing Phase 1; narrowed Phase 2 | 1.3, 1.5, 2.4 | The switch helper (`switch-model.sh`) is now covered by a pytest gate (`catalog/hooks/tests/test_model_routing_switch.py`, 10 cases: every switch tier, model-in-enumerated-set validation, clean unknown-platform refusal, and `.sh`/`.ps1` parity), which exercises `enumerate-models.sh` indirectly via the sibling call. CI ShellChecks all `catalog/**/*.sh` on the ubuntu runner (`ci.yml`, non-blocking `|| true`); `make lint` itself still ShellChecks only `installer.sh` / `install.sh`, and ShellCheck is not on the local PATH (WN-v33-1). Residual: `detect-platform.sh` and `enumerate-models.sh` have no DIRECT pytest (only the indirect coverage above). | Optionally add a direct unit test for `detect-platform.sh` / `enumerate-models.sh`, and/or extend `make lint` to ShellCheck `catalog/skills/**/scripts/*.sh` (blocking). | Low (switch helper gated; enumerate exercised indirectly; CI ShellChecks skill scripts; logic small and guarded) |
| WN-v33-1 | WN | carried forward from v3.3.0; re-confirmed model-routing Phases 1-4 and adoption-nessie Phases 1-2 | 1.5, 2.4, 2.5, 3.4, 4.4 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` were run by invoking the underlying validators, the scanner, and pytest directly. Re-confirmed for adoption-nessie-and-agency-agents Phase 2 (two new `IntegrationBase` subclasses + two installer scripts + two templates + docs): the direct chain passed green (`tests/integrations/` 231 passed including the parameterized contract suite over both new keys + the new `test_aider_windsurf.py` 8 cases; hook suite `catalog/hooks/tests/` 439 passed / 7 skipped; full `runner.py check` lands `CONVENTIONS.md` / `.windsurfrules` with no integration error; JSON integrity 256 skills; orphan-bundle audit PASS 0 errors + 1 pre-existing WN-v33-2 `.pyc` warning; no-personal-paths clean; unicode-safety 0 errors; version sync all surfaces match 3.3.4). Phase 2 DID ship `.sh` (the `scripts/installer.sh` AIDER/WINDSURF blocks) and `.ps1` edits; ShellCheck is not on the local PATH, so the bash edit was verified with `bash -n` (clean) and the PowerShell edit with the `[Parser]::ParseFile` AST (clean); CI ShellChecks `installer.sh` on the ubuntu runner. | Confirm CI `validate` / `scan` / `shellcheck` are green on the ubuntu runner. No code change expected. | Low (direct validator/scanner equivalents passed; both installers parse clean) |
| WN-v33-2 | WN | carried forward from v3.3.0 | n/a | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored, never committed), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate, and neither is touched by model-routing Phase 1. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | | | | |
