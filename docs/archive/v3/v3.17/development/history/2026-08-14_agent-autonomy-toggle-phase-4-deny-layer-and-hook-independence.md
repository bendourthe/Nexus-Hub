# Development Log: v3.17.0 Phase 4 deny layer and hook independence

**Date**: 2026-08-14
**Operator**: Nexus-Hub maintainer
**Assisted by**: OpenAI Codex
**Objective**: Verify that Claude Code hooks remain enforcing when permission prompts are bypassed, then block autonomy-active writes to canonical execution-trigger configuration paths.
**Outcome**: Phase 4 is complete. Hook independence matched across all six planned mode and matcher combinations, the shared guard blocks canonical paths through Bash and PowerShell siblings, platform adapters materialize both scripts, and focused local verification is green.

---

## 1. Starting State

- **Branch**: `feat/v3.17.0-agent-autonomy-toggle`
- **Starting commit**: `4b7d13e8`
- **Environment**: Windows PowerShell, Python 3.12.10, Claude Code 2.1.156
- **Prior session reference**: [Phase 3 core consent, TTL, and audit](2026-08-14_agent-autonomy-toggle-phase-3-core-consent-ttl-and-audit.md)
- **Plan reference**: [v3.17.0 agent autonomy toggle](../../plans/v3.17.0-agent-autonomy-toggle.md)

Phase 3 had committed the reversible autonomy engine and expiry hook locally. Phase 4 began from that clean checkpoint and first tested the safety premise that prompt-bypass modes do not suppress blocking hooks.

---

## 2. Chronological Steps

### 2.1 Empirical hook-independence probe

**Plan specification**: In a throwaway repository, cross the `acceptEdits`, `bypassPermissions`, and dangerous CLI autonomy surfaces with Bash and Write matchers, and stop if any hook is bypassed.

**What happened**: A project `PreToolUse` hook logged the attempted tool name and target, printed a fixed marker, and exited 2. Claude Code attempted all six requested tool calls. Every call reached the hook, every requested marker file remained absent, and every Claude process failed closed. The dated MATCH verdict and official contract links are recorded beside the Phase 2 autonomy evidence in `docs/policy/platform-read-contracts.md`.

**Key files changed**: `docs/policy/platform-read-contracts.md`.

**Troubleshooting**:

- **Problem**: The first `--dangerously-skip-permissions` Bash probe added no new log entry.
- **Actual result**: The rerun reported `subtype=error_max_budget_usd` after the hook attempt.
- **Root cause**: The initial per-call budget was exhausted before the result could be reported, making that first observation inconclusive rather than negative.
- **Resolution**: Only that case was rerun with a slightly higher hard cap. The Bash event appeared in the hook log and the marker file remained absent.

No commit was created for the probe itself; its repository lives under ignored `.nexus-hub/` state.

### 2.2 Shared autonomy guard and shell parity

**Plan specification**: Block Write and Edit calls to every v3.15.6 canonical execution-trigger path while autonomy is active, with traversal and symlink coverage and identical Bash/PowerShell behavior.

**What happened**: `scripts/lib/autonomy.py` now owns one Phase 4 tuple and symlink-aware matcher for the canonical file-path groups. Group B command forms remain with `git-guardrails`, because Write/Edit payloads do not carry shell commands. `guard_path` is fail-closed for unreadable state, fast and silent with no state, and blocks only when project autonomy state exists and the normalized lexical or resolved path matches. The shell siblings locate the shared engine and forward the original hook payload instead of duplicating policy.

The maintainer approved the exact `Write|Edit` registration in `catalog/hooks/settings.json`. Both standard runtime opt-outs remain supported for catalog consistency, with the scripts documenting that disabling this guard while autonomy is active is unsupported.

**Key files changed**: `scripts/lib/autonomy.py`, `catalog/hooks/autonomy-guard.sh`, `catalog/hooks/autonomy-guard.ps1`, `catalog/hooks/settings.json`.

### 2.3 Tests, adapter regression, and CI

**Plan specification**: Cover every path, aliases, inactive state, exit/message parity, and the one-definition invariant; reuse the existing hook CI job.

**What happened**: The new suite covers all canonical samples through both native shells, traversal normalization, symlink aliases where the host permits link creation, malformed-state preservation, runtime controls, direct engine behavior, and the CLI payload seam. The repository-wide CI already runs the full hook suite on Linux and Windows. The dedicated autonomy workflow was extended to cover the guard on its fixed Linux, macOS, and Windows matrix, and its combined coverage command avoids a redundant second guard run.

**Troubleshooting**:

- **Problem**: The expanded engine initially failed its CI floor: `Coverage failure: total of 74 is less than fail-under=80`.
- **Root cause**: Wrapper subprocesses verified behavior but did not contribute lines to the parent pytest coverage process.
- **Resolution**: Direct engine tests were added for every guard branch and both CLI inputs. Final module coverage is 85.06%.
- **Problem**: `test_shell_hooks_point_at_their_powershell_sibling` failed because it assumed `session-start.sh` was the only SessionStart handler and encountered `autonomy-expiry.sh` first.
- **Root cause**: The assertion encoded list position rather than the cross-shell sibling contract.
- **Resolution**: The test now compares stems for every SessionStart handler and explicitly asserts installation of both autonomy hook pairs.

**Key files changed**: `catalog/hooks/tests/test_autonomy_guard.py`, `tests/test_autonomy.py`, `tests/integrations/test_codex_native.py`, `.github/workflows/autonomy-security.yml`.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| Live Claude Code autonomy modes crossed with Bash and Write matchers | PASS: 6 of 6 blocked by exit 2 |
| Core plus guard coverage suite | PASS: 81 passed, 3 skipped, 85.06% coverage |
| Autonomy sibling-parity selection | PASS: 18 passed, 262 deselected |
| Platform hook adapters | PASS: 120 passed |
| Existing escalation-trigger and Git guardrails | PASS: 162 passed |
| Workflow policy suite | PASS: 98 passed |
| Focused Ruff check and format check | PASS |
| JSON, YAML, Bash, PowerShell AST, ShellCheck, and Python parsing | PASS |
| `git diff --check` | PASS |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| The ignored `.nexus-hub/phase4-hook-probe/` directory contains the throwaway live-test repository because recursive cleanup was rejected by the execution safety policy | P3 local hygiene | Leave ignored and uncommitted; remove manually or during a later approved cleanup |

No Phase 4 functional defect, release blocker, missing test, or new version-level known gap remains open.

---

## 5. Plan Discrepancies

- The v3.15.6 canonical list had already shipped, but its normative source is prose and existing consumers already duplicate shell patterns. Phase 4 established one named code definition for its enforcing guard and left the existing v3.15.6 advisory consumers unchanged; tests assert there is one Phase 4 Python definition.
- The dedicated autonomy workflow was updated in addition to inheriting the repository-wide hook jobs, because its security-critical three-OS exception would otherwise ignore Phase 4 files.
- The full hook directory was not rerun locally after the prior OneDrive-backed aggregate produced no diagnostic result. Exact changed surfaces, adapter consumers, inherited guards, and CI policy were run in bounded suites; remote CI retains the full Linux and Windows hook matrices.

---

## 6. Assumptions Made

- **Hook independence is version-specific**: The MATCH supports Claude Code 2.1.156 and must be reverified after a material hook or permission architecture change.
- **Any preserved autonomy state is enforcing**: The guard stays active until expiry or reversion successfully clears state; it does not treat an expired-but-unreverted record as safe.
- **Group B remains a Bash concern**: `core.hooksPath` and `core.fsmonitor` command strings stay with the existing Git guardrail because a Write/Edit hook cannot inspect them.
- **Installer lockstep remains Phase 5**: This phase registers and materializes hook pairs through hook adapters; explicit installer script registration remains assigned to the next plan phase.

---

## 7. Testing Summary

### Automated Tests

- Core plus guard coverage: 81 passed, 3 skipped, 85.06% coverage.
- Autonomy cross-shell parity: 18 passed.
- Settings-hook and Codex materialization: 120 passed.
- Existing execution-trigger advisory and Git command guards: 162 passed.
- Workflow policy: 98 passed.

### Manual Testing Performed

- Ran real Claude Code tool attempts for all six mode and matcher combinations and confirmed no marker file was created.
- Confirmed the registered settings matcher is exactly `Write|Edit` and points to `autonomy-guard.sh`.
- Confirmed the dedicated security workflow covers both siblings, the new suite, settings changes, and the shared engine on all three operating systems.

### Manual Testing Still Needed

None for Phase 4. Phase 5 owns end-to-end installed CLI and extension behavior.

---

## 8. TODO Tracker

### Completed This Session

- [x] 4.1 Verify hook independence under all planned prompt-bypass modes.
- [x] 4.2 Add and register the autonomy execution-trigger guard with Bash/PowerShell parity.
- [x] 4.3 Add comprehensive tests, fix the discovered adapter regression, and extend focused CI.

### Remaining

- [ ] Phase 5: CLI, installer registration, usage-monitor toggles, and documentation.
- [ ] Phase 6: architecture refactor, known-gaps reconciliation, CI/CD, and controlled integration.

### Out of Scope

- [ ] Explicit installer registration and user-facing autonomy surfaces remain Phase 5 work.

---

## 9. Summary and Next Steps

Phase 4 validates the load-bearing safety premise and turns the v3.15.6 execution-trigger taxonomy into an autonomy-aware blocking control. The guard is shared, path-normalizing, fail-closed, cross-shell, registered with approval, materialized by platform adapters, and covered above the required module threshold.

**Next session should**:

1. Add the thin `nexus-hub autonomy` CLI surface over the committed engine.
2. Present both installer diffs for approval before registering the new scripts.
3. Add and verify the autonomy status and toggle surfaces in both usage-monitor extensions.
