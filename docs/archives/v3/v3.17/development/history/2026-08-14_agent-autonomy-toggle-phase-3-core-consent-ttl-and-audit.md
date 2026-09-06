# Development Log: v3.17.0 Phase 3 core consent, TTL, and audit

**Date**: 2026-08-14
**Operator**: Nexus-Hub maintainer
**Assisted by**: OpenAI Codex
**Objective**: Add one project-scoped autonomy engine with hard consent gates, automatic expiry, reversible writes, and a forensic audit trail.
**Outcome**: Phase 3 is complete. The core engine, paired expiry hooks, SessionStart registration, focused three-OS CI workflow, and refusal-path-heavy test suite are implemented and locally verified.

---

## 1. Starting State

- **Branch**: `feat/v3.17.0-agent-autonomy-toggle`
- **Starting commit**: `e78fcbea`
- **Environment**: Windows PowerShell, Python 3.12.10
- **Prior session reference**: [Phase 2 capability model and lever verification](2026-08-14_agent-autonomy-toggle-phase-2-capability-model-and-lever-verification.md)
- **Plan reference**: [v3.17.0 agent autonomy toggle](../../plans/v3.17.0-agent-autonomy-toggle.md)

Phase 2 had established verified descriptors without writing configuration. Phase 3 consumed that contract while preserving the branch isolation and commit-only boundary required by known-gaps BG-4.

---

## 2. Chronological Steps

### 2.1 Core engine and enforced preconditions

`scripts/lib/autonomy.py` now provides `enable`, `disable`, `revert`, `expire`, and `status` as the single state-transition implementation. Enablement requires a real git repository, a clean worktree, a non-protected branch, a TTL from 1 through 480 minutes, and project-name typed confirmation for the full tier. Descriptors that resolve globally are refused in code, so the three verified global-only platforms cannot be written accidentally.

Configuration updates support JSON, literal-key JSONC, and TOML descriptors. Every successful write has a timestamped backup, a unified preview diff, and an atomic replace. State is stored in `.nexus-hub/autonomy-state.json`, separate from platform configuration.

### 2.2 Expiry and SessionStart integration

`catalog/hooks/autonomy-expiry.sh` and `catalog/hooks/autonomy-expiry.ps1` call the same Python engine and remain fast no-ops when no state exists. Expired state restores its backup and clears state only after a successful revert. Missing or unusable backups fail loudly and preserve the state file.

The maintainer approved the ask-first `catalog/hooks/settings.json` registration. The expiry gate intentionally does not honor general hook-disable controls, matching the repository's non-bypassable security-gate policy; the sibling-parity test encodes that exception.

### 2.3 Append-only audit trail

Every successful transition and rejected enable attempt writes exactly one locked JSONL record with timestamp, platform, tier, config and backup paths, expiry, branch, commit, and outcome. The record schema excludes environment dumps, tokens, config contents, and typed confirmation values. POSIX creation uses restrictive permissions.

### 2.4 Test and CI gate

The core suite uses real temporary git repositories for state-dependent behavior and covers all required refusal paths, backup ordering, simulated atomic-write interruption, expiry, audit validity, and secret exclusion. Hook tests execute the native Bash and PowerShell siblings. The maintainer also approved `.github/workflows/autonomy-security.yml`, a path-filtered fixed three-OS matrix with read-only permissions and concurrency cancellation.

The repository-wide hook aggregate remained non-diagnostic for more than six minutes in the OneDrive-backed Windows workspace and was terminated without a result. It is not reported as a pass. The exact changed surfaces passed their focused core, hook behavior, cross-shell parity, and workflow-policy suites.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| Autonomy core tests and coverage | PASS: 28 passed, 81.28% statement coverage, 80% floor met |
| Expiry-hook behavior | PASS: 6 passed |
| New-hook cross-shell sibling parity | PASS: 8 passed, 262 deselected |
| Workflow policy suite | PASS: 98 passed |
| Repository validation commands | PASS: catalog, bundle, permission, path, Unicode, supply-chain, workflow, solution, incident, version, base-parity, model, platform-contract, freshness, default, and compression checks |
| Python compile, Ruff check, and Ruff format check | PASS |
| JSON, YAML, Bash, PowerShell AST, and ShellCheck parsing | PASS |
| `git diff --check` | PASS |
| Full hook aggregate | NO RESULT: terminated after more than six minutes without output; focused changed-surface suites above are green |

---

## 4. Known Issues

No new functional defect, missing test, quality-gate bypass, or release blocker was identified. Existing v3.17 items remain unchanged, including BG-4's controlled Phase 6 merge requirement and WN-2's pre-existing integration-framework Ruff debt.

---

## 5. Plan Discrepancies

- The engine rejects verified descriptors whose scope is global instead of writing them, because the phase's project-only safety rule is stricter than descriptor availability.
- The dedicated security workflow keeps all three operating systems on pull requests and protected-branch pushes. It does not spend remote action minutes at this non-final local commit boundary.
- The broad hook aggregate produced no result in the local OneDrive workspace; focused tests cover every changed hook path and the limitation is recorded rather than converted into a success claim.

---

## 6. Assumptions Made

- A global-only descriptor is a supported platform capability but an unsupported Phase 3 write target.
- The expiry hook is a non-bypassable safety gate, so general hook opt-out controls cannot turn a mandatory TTL into advisory behavior.
- User-facing CLI commands remain Phase 5 work; Phase 3 exposes only the engine entry points needed by the expiry hook and tests.

---

## 7. Testing Summary

### Automated Tests

- Core: 28 passed at 81.28% coverage.
- Hook behavior: 6 passed.
- Cross-shell parity for the new hook: 8 passed.
- Workflow policy: 98 passed.
- Static and repository validators: passed as listed in the verification table.

### Manual Verification

- Confirmed no global descriptor can pass the project-scope gate.
- Confirmed the SessionStart registration invokes the Bash expiry sibling through the installed hook path.
- Confirmed the CI matrix names all three operating systems and documents the security-critical cost exception.
- Confirmed `.nexus-hub/` is already ignored by the repository.

### Manual Testing Still Needed

Phase 4 owns live-build verification that Claude Code hooks remain active when prompt bypass is enabled. No Phase 3 claim depends on that result.

---

## 8. TODO Tracker

### Completed This Session

- [x] 3.1 Implement core transitions, preconditions, backup, atomic write, and preview.
- [x] 3.2 Implement idempotent TTL expiry through paired SessionStart hooks.
- [x] 3.3 Implement locked append-only JSONL auditing for transitions and rejections.
- [x] 3.4 Add refusal-heavy tests and the approved three-OS security workflow.

### Remaining

- [ ] Phase 4: deny layer integration and hook-independence verification.
- [ ] Phase 5: CLI, installer registration, usage-monitor toggles, and documentation.
- [ ] Phase 6: architecture refactor, known-gaps reconciliation, CI/CD, and controlled integration.

---

## 9. Summary and Next Steps

Phase 3 provides a reversible, time-bounded, project-only autonomy core. Hard gates are enforced in one stdlib module, expiry is automatic and non-bypassable, and every transition or refusal leaves a minimal forensic record.

**Next session should**:

1. Start Phase 4 from the committed Phase 3 engine.
2. Extend the deny layer to cover execution-trigger configuration paths without weakening existing protections.
3. Run the planned live-build hook-independence experiment and record the result plainly.
