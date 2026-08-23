# Development Log: v3.17.0 Phase 6 - Architecture, Known Gaps, and Installer Parity

**Date**: 2026-08-15
**Operator**: Benjamin Dourthe
**Assisted by**: OpenAI Codex
**Objective**: Complete the terminal architecture, known-gaps, CI/CD, installer-parity, platform-contract, and release-readiness phase for the agent autonomy toggle.
**Outcome**: Phase 6 implementation, BG-4 reconciliation, `develop` integration, and protected-branch CI are complete. No version bump, tag, or release was performed; publication remains owned by `/update release`.

---

## 1. Starting State

- **Branch**: `feat/v3.17.0-agent-autonomy-toggle`
- **Starting tag/commit**: `04df15d33020df805cc88ac55bfa3fd9ec5f042c`
- **Environment**: Windows PowerShell, Python 3.12, Node.js extension toolchains, no GNU Make, no pytest-xdist
- **Prior session reference**: `docs/archive/v3/v3.17/development/history/2026-08-15_agent-autonomy-toggle-phase-5-cli-monitors-and-decision-walkthrough.md`
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.0-agent-autonomy-toggle.md`

Context: Phases 1 through 5 had delivered the permission baseline, autonomy descriptors, core state engine, deny layer, CLI, and usage-monitor controls. Phase 6 had to reconcile architecture and known gaps, make installer parity a standing hard gate, audit every workflow, re-verify platform contracts, and hand the branch to the separate release workflow.

---

## 2. Chronological Steps

### 2.1 Architecture and documentation reconciliation

**Branch**: `feat/v3.17.0-agent-autonomy-toggle` | **PR**: none | **Merged to**: none

**Plan specification**: Audit deprecated, empty, duplicate, and overcomplicated structures; collapse any duplicate execution-trigger list; retain the approved v3.18.2 slot and repair stale references.

**What happened**: The v3.15.6 endpoint-hardening work was confirmed merged. `scripts/lib/autonomy.py` already contains the only Phase 4 executable definition of the execution-trigger paths and the wrappers delegate to it, so no duplicate was removed. Candidate duplicate files were intentional platform counterparts, and empty directories were local scaffolding rather than tracked artifacts. The v3.18.2 RTK and Meterless plan and comparison remain canonical under `docs/v3/v3.18/`; stale pre-move paths and release wording were corrected without re-slotting the work.

**Key files changed**: `docs/v3/v3.17/plans/v3.17.0-agent-autonomy-toggle.md`, `docs/v3/v3.18/plans/v3.18.2-rtk-and-meterless.md`, `docs/v3/v3.18/comparisons/v3.18.2-comparison-rtk-and-meterless.md`

**Verification**: Targeted path and symbol searches found one execution-trigger constant and no tracked empty-directory artifact requiring deletion.

### 2.2 Known-gaps reconciliation and warning cleanup

**Branch**: `feat/v3.17.0-agent-autonomy-toggle` | **PR**: none | **Merged to**: none

**Plan specification**: Resolve, defer, or transfer every open v3.17.0 item, including autonomy non-delivery, permission coverage, Hermes installer wiring, matcher uncertainty, and Windows warnings.

**What happened**: After protected-branch integration and repair, the ledger records 12 open, 8 closed, and zero release blockers. It explicitly names the eight descriptor-free integrations, twelve integrations without a read-only baseline, Hermes installer non-delivery, the standalone permissions-helper asymmetry, both matcher probes, the Windows Gemini baseline gap, and the Phase 4 Claude-only hook evidence boundary. The Claude and Codex usage-monitor Vitest configs were renamed from `.ts` to `.mts`, closing WN-3 without changing test behavior. BG-4 was closed during integration by reconciling the feature branch with current `origin/develop`, restoring every revert-owned artifact, and verifying the silent-deletion paths. Protected-branch CI then exposed BG-5 through BG-7. BG-6 and BG-7 passed after the defaults provenance and npm 10 lockfile repairs. Hosted tracing isolated BG-5 to the native PowerShell-to-Python stdin pipeline; the final adapter parses the payload and forwards `--path` explicitly, and the authoritative Windows rerun passed.

**Key files changed**: `docs/v3/v3.17/known-gaps.md`, `extensions/claude-usage-monitor/vitest.config.mts`, `extensions/codex-usage-monitor/vitest.config.mts`

**Verification**: Claude Usage Monitor passed 11 tests and Codex Usage Monitor passed 81 tests with no native-loader warning.

### 2.3 Installer parity hard gate and real-install CI

**Branch**: `feat/v3.17.0-agent-autonomy-toggle` | **PR**: none | **Merged to**: none

**Plan specification**: Add a generic manifest-driven parity checker, make it a release and planning hard gate, and execute both installers on hosted Linux, macOS, and Windows runners with identical postconditions.

**What happened**: `configs/installer-parity.json` declares installer artifacts, fourteen platform keys, function counterparts, documented exceptions, and external dependency fallbacks. `scripts/check_installer_parity.py` enforces the declaration with only the standard library; `scripts/check_installer_smoke.py` owns the common postcondition set. The Makefile, CI workflow, `/update release`, `implementation-plan`, and `implement-phase` now carry the gate. CI runs Ubuntu on every branch push and gates macOS and Windows to pull requests, tags, and manual dispatch; the dangerous autonomy core retains its separate unconditional three-OS matrix.

**Key files changed**: `configs/installer-parity.json`, `scripts/check_installer_parity.py`, `scripts/check_installer_smoke.py`, `Makefile`, `.github/workflows/ci.yml`, `catalog/commands/update.md`, `catalog/skills/workflow/implementation-plan/SKILL.md`, `catalog/skills/workflow/implement-phase/SKILL.md`, `catalog/skills/workflow/implement-phase/references/implement-phase-runbook.md`

**Verification**: Static parity PASS; 70 focused parity and lifecycle tests passed; a real Windows PowerShell installer smoke run passed against a redirected user profile.

### 2.4 CI/CD optimization audit

**Branch**: `feat/v3.17.0-agent-autonomy-toggle` | **PR**: none | **Merged to**: none

**Plan specification**: Compare every existing pipeline with the optimized lifecycle and either migrate it or retain its difference explicitly.

| Pipeline | Optimized comparison | Decision |
|---|---|---|
| `autonomy-security.yml` | Fixed three-OS matrix is more expensive than merge-gated matrices | Retain: dangerous-state core requires unconditional OS coverage |
| `ci.yml` | Dynamic OS gating, concurrency cancellation, timeouts, caching, path-aware jobs | Migrate installer coverage into this workflow via the new gated smoke matrix |
| `claude-usage-monitor.yml` | Single Ubuntu cached, path-filtered package test | Retain |
| `code-search.yml` | Single Ubuntu cached, path-filtered extension test | Retain |
| `codex-usage-monitor.yml` | Single Ubuntu cached, path-filtered package test | Retain |
| `cursor-usage-monitor.yml` | Cached build plus Linux E2E | Retain |
| `github-usage-monitor.yml` | Single Ubuntu cached, path-filtered package test | Retain |
| `codeql.yml` | Main, schedule, and manual security analysis on Ubuntu | Retain |
| `doc-colocation.yml` | Path-filtered Ubuntu documentation guard | Retain |
| `presentify-extractor.yml` | Verification avoids schedule; rendering is limited to schedule and integration pushes | Retain |

Every workflow has concurrency cancellation and explicit timeouts; dependency-heavy jobs cache their package-manager inputs.

### 2.5 Platform-contract full pass

**Branch**: `feat/v3.17.0-agent-autonomy-toggle` | **PR**: none | **Merged to**: none

**Plan specification**: Run the release-readiness platform discovery and defaults-lever verification alongside installer parity.

**What happened**: All ten read contracts and sixteen defaults-lever platforms were re-fetched from first-party documentation. Read-path results remain eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI contract. The pass found two real defaults changes: Hermes now documents `agent.reasoning_effort` rather than a top-level key, and Gemini Code Assist now documents `geminicodeassist.agentYoloMode` in VS Code user settings. Hermes was corrected in the source manifest and regression tests. Gemini moved from UNVERIFIED to VERIFIED-with-mismatch for defaults and to DRIFT for the project-only autonomy descriptor; it remains deliberately not writable.

**Key files changed**: `configs/platform-defaults.json`, `docs/policy/platform-defaults-levers.md`, `docs/policy/platform-read-contracts.json`, `docs/policy/platform-read-contracts.md`, `tests/validators/test_platform_defaults_seeding.py`

**Troubleshooting**:

- **Problem**: The first JSON patch caused `Expecting ',' delimiter: line 6 column 5 (char 830)`.
- **Root cause**: The replacement for the long `verified_for_version_note` line omitted its trailing comma.
- **Resolution**: Restored the comma and reran JSON parsing and contract tests.
- **Problem**: `test_gemini_never_declares_a_write_target` failed after Gemini became verified.
- **Root cause**: The regression encoded the old assumption that Gemini could never appear in the defaults manifest.
- **Resolution**: The test now requires an empty settings map and `mode: not-writable`, while confirming Gemini CLI remains sole owner of `~/.gemini/settings.json`.

**Verification**: Contract JSON and defaults JSON parse; defaults sync reports 13 platforms; all 10 platform checks pass; the current-tree freshness gate passes; 95 focused contract, autonomy, freshness, and defaults tests pass.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| Installer parity checker | PASS |
| Focused Phase 6 parity/lifecycle suite | PASS - 70 tests |
| Focused contract/autonomy/defaults suite | PASS - 95 tests |
| Claude Usage Monitor | PASS - 11 tests |
| Codex Usage Monitor | PASS - 81 tests |
| Complete Makefile validation commands | PASS |
| Skill bundle audit | PASS - 271 skills, 0 errors, 0 warnings |
| Trigger-routing hard gate | PASS - 0 failures |
| Permission baseline validator | PASS |
| Workflow security and version sync | PASS |
| Base-template parity | PASS - 5 of 5 |
| Platform contracts | PASS - 10 platforms |
| Platform defaults sync | PASS - 13 platforms |
| Compression accuracy gate | PASS - CCR 100 percent |
| Real Windows installer smoke | PASS |
| Full `tests` plus hook suite | BOUNDED - combined run exceeded 15 minutes locally without an early failure result |
| Full repository `tests` suite alone | BOUNDED - 2,550 tests exceeded 15 minutes locally without an early failure result |
| Model-prompting freshness advisory | UNKNOWN - no live roster supplied; non-blocking by policy |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| BG-4: `develop` reverted the Phase 1 checkpoint while this branch was based on v3.16.6 | Resolved | Merged current `origin/develop` into the feature branch first, restored every revert-owned artifact, then passed the exact 80-test regression suite and hard validators |
| BG-5: Windows PowerShell discarded the autonomy hook payload on the hosted runner | Resolved | Hosted tracing isolated the native PowerShell-to-Python pipeline; the adapter now parses JSON, forwards `--path` explicitly, and passed Windows job `95060274953` |
| BG-6: defaults provenance URLs disagreed with the verified contract | Resolved | Aligned Hermes, Gemini CLI, and Gemini Code Assist URLs and passed all 23 contract tests plus 695 validators |
| BG-7: npm 10 rejected the Claude monitor lock graph | Resolved | Regenerated the lock with npm 10.9.4 and passed clean install, compile, 11 tests with coverage, and packaging |
| Local full-suite duration exceeds the bounded Windows verification budget | P2 | Focused local evidence plus the green protected-branch CI matrix provides the release gate |
| Temporary smoke directory remains outside the repository because cleanup was blocked by the execution policy | Cosmetic | Reported; no repository artifact is affected |
| 12 open known gaps | P2 or lower | Carried with explicit dispositions; zero are release blockers |

---

## 5. Plan Discrepancies

- The Phase 6 model recommendation was upshifted from the legacy strong/high entry to frontier/max because the phase combines repository-wide architecture, security-sensitive installer parity, and live vendor-contract decisions.
- The machine freshness stamp now matches the reconciled tree's canonical 3.16.8 version. The full evidence pass is prepared for v3.17.0, but `/update release` owns the version bump and must advance the stamp with the canonical version files.
- The full local Python suite could not be claimed green because it exceeded the bounded 15-minute Windows run. Focused suites, hard validators, real Windows installer smoke, and protected-branch remote CI are green; the remote matrix is the authoritative full-suite integration evidence.

---

## 6. Assumptions Made

- **Codex redundant path retention**: repeated omission of `~/.codex/skills` is weaker than explicit removal evidence; retaining it is harmless because `.agents/skills` is the confirmed delivery path.
- **Gemini write boundary**: a documented VS Code user setting does not authorize writing the OS-specific editor profile or a project `.vscode/settings.json` file through the Gemini integration.
- **No architectural moves**: intentional cross-platform counterparts and local empty scaffolding are not redundant tracked artifacts.
- **Remote CI authority**: hosted macOS and Linux installer execution is the authoritative evidence for platforms unavailable on the Windows workstation.

---

## 7. Testing Summary

### Automated Tests

- Focused Phase 6 parity and lifecycle tests: 70 passed.
- Focused contract, autonomy, defaults, and freshness tests: 95 passed.
- Usage monitors: 11 Claude and 81 Codex tests passed.
- Hard validation battery: all gates passed; quality and Unicode checks emitted existing warnings only.
- Full local repository suite: bounded by a 15-minute timeout, so no aggregate pass claim is made.

### Manual Testing Performed

- Real PowerShell installer executed into a redirected temporary user profile and passed the shared smoke postconditions.
- Workflow YAML parsed and the dynamic installer matrix conditions were inspected against the plan.
- Current first-party platform documentation was checked for all read-path and defaults-lever records.

### Manual Testing Still Needed

- [x] Run the protected-branch GitHub Actions checks, including hosted macOS and Linux real-installer legs. CI run `31904566621`, autonomy-security run `31904566683`, and Doc Co-location run `31904566521` passed on integrated code commit `a14c9812`.
- [x] Resolve BG-4 explicitly when integrating the feature branch into the current `develop` tip.
- [ ] Run `/update release` only after green integration to bump versions, advance the contract stamp, generate release notes, tag, and publish.

---

## 8. TODO Tracker

### Completed This Session

- [x] 6.1 architecture and documentation reconciliation
- [x] 6.2 known-gaps reconciliation
- [x] 6.3 CI/CD coverage and optimization audit
- [x] 6.4 testing and stabilization with bounded local evidence
- [x] 6.5 standing installer parity and real-install CI gate

### Remaining (Not Started or Partially Done)

- [x] User approved commit and integration publication.
- [x] Protected-branch CI passed after integration.
- [ ] `/update release` performs the versioned v3.17.0 release workflow.

### Out of Scope (Deferred)

- [ ] The 12 non-blocking items in `docs/v3/v3.17/known-gaps.md`.
- [ ] Broad Ruff cleanup of the integration framework.
- [ ] Expanding read-only permission baselines to the other twelve integrations.

---

## 9. Summary and Next Steps

Phase 6, BG-4 integration handling, and protected-branch remote CI are complete. Installer parity is now a generic standing hard gate, every pipeline has an explicit optimize-or-retain decision, the platform contracts have fresh evidence, and the known-gaps ledger is reconciled with zero release blockers.

**Next session should**:

1. Invoke `/update release` for v3.17.0.
