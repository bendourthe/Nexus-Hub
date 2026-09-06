# Session History - v3.16.0 Phase 5: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.0-platform-defaults-config.md](../../plans/v3.16.0-platform-defaults-config.md)
**Phase**: 5 of 5 - **the final phase** (release-readiness workflow ran)
**Branch**: `feat/platform-defaults-config`
**Outcome**: Complete. All quality gates passed. No version bump, tag, merge, or push performed in-phase.

## Goal

Leave the project well-organized, its known gaps reconciled, and its CI/CD complete and optimized.

## Sub-tasks completed

### 5.1 - Architecture refactor

**The named target, and the point of the phase**: the four documentation surfaces corrected in v3.15.5 each restated `medium` as prose *and* pointed readers at `catalog/hooks/settings.json` - which this release turned into a generated artifact. All four now name `configs/platform-defaults.json` as the source, label the template as generated, and state that the source wins on disagreement.

| Surface | Change |
|---|---|
| `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md` | Pointer retargeted; adds "if the value quoted here ever disagrees with that file, the file is right" |
| `extensions/claude-usage-monitor/README.md` | Split into a source line and a generated-template line |
| `catalog/skills/ai-development/prompt-engineering/SKILL.md` | Pointer retargeted; pedagogy about *why* `medium` retained |
| `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` | "the shipped `medium` default" now names its source |

Layout detectors, proposed then applied with confirmation:

- **Empty directories**: 5 found, all `node_modules` / build / runtime. Four are gitignored; `.antigravitycli/` was added to `.gitignore`. Git never commits empty directories, so nothing shipped was affected.
- **Orphan bundles**: 11 warnings, **all** gitignored `__pycache__/*.pyc`. Fixed at the validator rather than by deleting files, since they regenerate. Now 0 warnings.
- **Loose file**: `github-ci-cd-cost-effective-alternatives.md` moved from the v3.16 version root into a new `research/` subdirectory.

### 5.2 - Known-gaps reconciliation

Every one of the sixteen registered platforms received an explicit disposition in a per-platform table, and every remaining `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` item was closed or carried forward with a reason.

**Final tally: 12 closed, 3 carried forward (NI-1, NI-6, BG-1). None gates the release.**

Platform outcome: 7 seeded, 1 already delivered, 4 declared-but-not-writable, 4 UNVERIFIED and absent.

### 5.3 - CI/CD

**Verified, no change needed.** All four requested optimizations are already present: `concurrency` with cancel-in-progress, pip caching, `timeout-minutes` on seven jobs, and expensive Windows / matrix jobs gated to non-PR events. The drift check runs in the `validate` job (line 160), and `tests/validators` (line 436) covers all three of this plan's test modules, with `tomlkit` and `PyYAML` installed there since Phase 3. The one CI change this cycle needed was Phase 2's trigger fix, so `docs/policy/` no longer skips the job set.

### 5.4 - Testing and Definition of Done

## Definition of Done, item by item

**Plan goal**: *"Establish `configs/platform-defaults.json` as the single place a maintainer edits a per-platform install default, so one edit propagates to every derived artifact on the next install, with a guard that fails the build when any artifact drifts from the declared source, and with every non-Claude lever seeded only after it is verified against that platform's official documentation."*

| Goal clause | Status | Evidence |
|---|---|---|
| Single place a maintainer edits a default | **Met** | `configs/platform-defaults.json`; `_PROJECT_SETTINGS_STUB` deleted, three test surfaces retargeted from literals to the source, four doc surfaces retargeted in 5.1 |
| One edit propagates to every derived artifact | **Met** | Phase 1 end-to-end test: editing the declared effort changed both derived surfaces with no code edit |
| A guard fails the build on drift | **Met** | `sync_platform_defaults.py --check` in `make validate` + CI; red on any single key edited away from source |
| Every non-Claude lever verified against official docs first | **Met** | 16/16 classified with fetched first-party evidence; 12 VERIFIED with URL + date, 4 UNVERIFIED with reasons; machine-enforced by the completeness test |

| Phase | Stability Gate | Status |
|---|---|---|
| 1 | Editing the source updates the template's core keys while leaving `hooks` byte-identical; stub produces the value with no literal; `--check` red on drift; runs in validate + CI | **Met** (byte-identity proven under both LF and CRLF) |
| 2 | All 16 classified with URL + date or a reason; nothing on inference; a test asserts URL + date | **Met** (12/4; parser verified non-vacuous) |
| 3 | Every VERIFIED lever declared and reaching its config; UNVERIFIED absent; guard covers the widened set; no platform gets a setting it cannot honour | **Met, with one documented deviation** (see below) |
| 4 | Re-verification in the existing remit, no new gate; AGENTS.md documents the surface; parity green | **Met** |
| 5 | Layout clean, gaps reconciled, CI complete and optimized, validation green | **Met** |

**The one deviation**: Phase 3 did not extend `--check` to the new install targets. Those are files on a user's machine, not repo artifacts, so a repo-side drift check cannot observe them; per-platform propagation is asserted by 41 seeding tests plus a throwaway-HOME install instead. Recorded in the Phase 3 session history and CHANGELOG.

## Exit checklist

- [x] All sub-tasks completed
- [x] All tests passing (unit, integration, and per-platform install tests)
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Definition of Done confirmed item by item
- [x] Handed off to `/update release`; **no tag or push created in-phase**

## Troubleshooting trail

- **The layout move was less trivial than proposed.** No `research/` convention exists anywhere in `docs/` (only `plans`, `development`, `comparisons` across 21 version directories), and the file carried a **live** inbound reference (the v3.19.0 plan) plus a **frozen** one (a v3.15 session history). Proceeded by creating the subdirectory, repairing the live reference, and leaving the history untouched: a session history records what was true at the time, and rewriting its paths to match a later reorganization would falsify the record.
- **The bundle-audit fix was checked for over-reach.** A filter that silences everything is worse than the noise it replaces, so a real orphan was injected and confirmed still reported before the change was kept.

## Release readiness

- **9A - Known gaps**: reconciled; 12 closed, 3 carried forward, none blocking.
- **9B - Tests and CI**: full suite run; all 14 `validate` guards pass; CI verified complete and optimized.
- **9C-9E**: handed to `/update release`, which owns the version bump, changelog finalization, tag, push, and GitHub Release behind its own confirmation gates.

**Hold conditions**: none active.

## Next steps

Run `/update release` to cut v3.16.0. Before it does the version bump, note that `check_platform_contract_freshness.py` hard-gates on `meta.verified_for_version` in `docs/policy/platform-read-contracts.json`, which is currently stamped for the previously-released version. `/update release` invokes `platform-contract-verification` as governance step 4, which re-stamps it as part of its own flow - and, as of Phase 4, that same pass now also re-verifies the lever contract advisorily.
