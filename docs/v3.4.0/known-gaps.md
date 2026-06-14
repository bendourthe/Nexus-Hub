# Known Gaps -- v3.4.0

**Status**: v3.4.0 is in active development on `develop`. The `model-routing` plan (`docs/v3.4.0/plans/model-routing.md`) Phase 1 of 4 is complete; a separate `adoption-nessie-and-agency-agents` plan is also in scope for v3.4.0.
**Last updated**: 2026-06-14 (model-routing Phase 1)

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
| DF-v34-1 | DF | model-routing Phase 1 | 1.3, 1.5 (helpers + stabilization) | The new `model-routing` `.sh` helpers (`detect-platform.sh`, `enumerate-models.sh`) are not yet covered by an automated ShellCheck or pytest gate: `make lint` ShellChecks only `installer.sh` / `install.sh`, and ShellCheck is not on the local PATH (WN-v33-1), so the helpers were verified with `bash -n` plus a cross-platform dry-run (bash + PowerShell) only. The plan schedules helper unit tests in Phase 2 (sub-task 2.4, asserting model-in-enumerated-set validation and clean unknown-platform refusal). | Land the Phase 2.4 helper tests; optionally extend `make lint` to ShellCheck `catalog/skills/**/scripts/*.sh`. | Low (dry-run + `bash -n` green on both platforms; logic is small and guarded) |
| WN-v33-1 | WN | carried forward from v3.3.0; re-confirmed model-routing Phase 1 | 1.5 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` were run by invoking the underlying validators, the scanner, and pytest directly. The full direct chain passed green (JSON integrity, version sync, bundles-only, quality, the v2.3.0 CI validators, skill-security scan, hook suite 429 passed, MCP skill-server 43 passed). | Confirm CI `validate` / `scan` are green on the ubuntu runner. No code change expected. | Low (direct validator/scanner equivalents passed) |
| WN-v33-2 | WN | carried forward from v3.3.0 | n/a | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored, never committed), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate, and neither is touched by model-routing Phase 1. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | | | | |
