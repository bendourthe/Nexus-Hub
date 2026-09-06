# Known Gaps -- v3.4.0

**Status**: v3.4.0 is in active development on `develop`. The `model-routing` plan (`docs/v3/v3.4/plans/model-routing.md`) is complete (all 4 phases); the `adoption-nessie-and-agency-agents` plan (`docs/v3/v3.4/plans/adoption-nessie-and-agency-agents.md`) is complete (all 5 phases -- Phase 1 the `context-pack-builder` skill, Phase 2 the Aider + Windsurf platform integrations, Phase 3 the `session-query` extension to Obsidian + exported ChatGPT/Gemini history, Phase 4 the optional Kimi + Qwen + OpenClaw platform integrations, Phase 5 selective agent-body enrichment). With both plans complete, the release cut (version bump 3.3.4 -> 3.4.0 + tag) is handed to `/update release` and not yet run.
**Last updated**: 2026-06-15 (adoption-nessie-and-agency-agents Phase 5)

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
| WN-v33-1 | WN | carried forward from v3.3.0; re-confirmed model-routing Phases 1-4 and adoption-nessie Phases 1-5 | 1.5, 2.4, 2.5, 3.4, 4.4, 5.3 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` were run by invoking the underlying validators, the scanner, and pytest directly. Re-confirmed for adoption-nessie-and-agency-agents Phase 5 (selective agent-body enrichment -- "Success Metrics" / "Deliverable Template" sections added to `build-error-resolver`, `harness-optimizer`, `doc-updater`): the direct chain passed green (unicode-safety / no-personal-paths / workflow-security / supply-chain-iocs all exit 0; JSON integrity 256 skills / 15 bundles; orphan-bundle audit PASS; solution-frontmatter exit 0; version-sync six surfaces match 3.3.4; the three edited files ASCII-clean in all added content, with all 14 `--strict` em-dash flags confirmed pre-existing). The compression accuracy eval was not run locally (the phase does not touch `extensions/nexus-context-compressor`); CI runs it on the ubuntu runner. Note: agents are auto-distributed by folder copy, so no installer or registry surface was touched this phase. | Confirm CI `validate` / `scan` / `shellcheck` are green on the ubuntu runner. No code change expected. | Low (direct validator equivalents passed; agent-Markdown-only change) |
| WN-v33-2 | WN | carried forward from v3.3.0 | n/a | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored, never committed), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate, and neither is touched by model-routing Phase 1. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | | | | |
