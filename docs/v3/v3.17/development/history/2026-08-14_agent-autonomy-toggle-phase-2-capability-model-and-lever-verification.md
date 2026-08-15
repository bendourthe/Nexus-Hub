# Development Log: v3.17.0 Phase 2 autonomy capability model and lever verification

**Date**: 2026-08-14
**Operator**: Nexus-Hub maintainer
**Assisted by**: OpenAI Codex
**Objective**: Establish one declarative, verified autonomy capability contract for every registered integration before any configuration-writing behavior is added.
**Outcome**: Phase 2 is complete. Eight integrations expose verified descriptors, eight deliberately omit them under sourced DRIFT or UNVERIFIED verdicts, all 16 roster entries have dated first-party evidence, and the full integration suite passes.

---

## 1. Starting State

- **Branch**: `feat/v3.17.0-agent-autonomy-toggle`, 20 commits behind and 2 commits ahead of `develop`
- **Starting commit**: `765c7324`
- **Environment**: Windows PowerShell, Python 3.12.10
- **Prior session reference**: [Phase 1 permission baseline and merge parity](2026-08-13_agent-autonomy-toggle-phase-1-permission-baseline-and-merge-parity.md)
- **Plan reference**: [v3.17.0 agent autonomy toggle](../../plans/v3.17.0-agent-autonomy-toggle.md)

Context: Phase 1 was already complete on the isolated feature branch. The branch was deliberately not synchronized with `develop` because known-gaps BG-4 records a revert-then-merge hazard that could silently delete Phase 1 work before the Phase 6 integration procedure.

---

## 2. Chronological Steps

### 2.1 Branch and model gate

**Plan specification**: Confirm the active phase branch and re-evaluate the phase model recommendation before implementation.

**What happened**: The local feature branch existed, was not attached to another worktree, and was checked out cleanly. The phase's load-bearing platform-contract work scored above the plan's strong/high recommendation, so the session used the current frontier reasoning model at high effort without changing any repository or user model configuration.

**Key files changed**: None.

**Troubleshooting**: None.

### 2.2 Declarative capability model

**Plan specification**: Add an optional `autonomy` config descriptor and a read-side gate that returns `None` for absent or unverified data.

**What happened**: `IntegrationBase` now documents the descriptor fields and exposes `autonomy_descriptor`. The accessor returns verified declarative data unchanged and fails soft to `None` for unsupported integrations. No writer, installer, or configuration mutation was added.

**Key files changed**: `scripts/lib/integrations/base.py`.

**Troubleshooting**: None.

### 2.3 Current first-party platform verification

**Plan specification**: Record a dated MATCH, DRIFT, or UNVERIFIED verdict with a source URL for every registered platform, treating negative-only evidence as UNVERIFIED.

**What happened**: Sixteen roster entries were verified and recorded in matching JSON and Markdown evidence. The sweep corrected the Copilot starting point to VS Code 1.131's `chat.permissions.default`, kept Gemini CLI descriptor-free because full YOLO remains CLI-only, distinguished Kimi `auto` from the narrower `yolo` mode, and rejected single-file descriptors where the platform needs another state store or an unsupported format.

**Key files changed**: `docs/policy/platform-read-contracts.json`, `docs/policy/platform-read-contracts.md`.

**Troubleshooting**: Dynamic Workflows were unavailable, so the independent platform checks were performed sequentially. This changed execution shape only, not scope or evidence requirements.

### 2.4 MATCH-only descriptors and omission notes

**Plan specification**: Add descriptors only where the contract verdict is MATCH; add a contract-pointer comment everywhere else; do not edit installers.

**What happened**: Descriptors were added for `antigravity2`, `claude`, `codex`, `copilot`, `cursor`, `kimi`, `opencode`, and `qwen`. `aider`, `antigravity`, `gemini`, `gemini-cli`, `hermes`, `nexus-ai`, `openclaw`, and `windsurf` remain descriptor-free with one-line reasons. The descriptor set equals the MATCH set in both directions.

**Key files changed**: 16 integration modules under `scripts/lib/integrations/`.

**Troubleshooting**: None.

### 2.5 Tests, validation, and CI audit

**Plan specification**: Add accessor, completeness, code-contract parity, and freshness tests; run the integration suite; reuse existing CI jobs.

**What happened**: A new four-test contract suite covers the accessor gate, full roster evidence, descriptor structure, exact MATCH parity, and the release freshness script. The integration suite was partitioned because a monolithic quiet run exceeded 20 minutes in the OneDrive workspace; the same directory then completed as 566 non-contract tests plus 79 passed and 1 skipped lifecycle contract case. CI already runs `tests/integrations` on Linux, runs freshness in `validate`, uses concurrency cancellation and pip caching, and includes `docs/policy/**` in path filtering, so no workflow change was needed.

**Key files changed**: `tests/integrations/test_autonomy_descriptors.py`.

**Troubleshooting**:

- **Problem**: the monolithic command ended with `command timed out after 1204069 milliseconds` and no failing assertion.
- **Attempted**: the suite was split into all non-contract integration tests and `test_contract.py`.
- **Root cause**: the lifecycle matrix repeatedly copies the large catalog under a OneDrive-backed Windows workspace; the live process continued accumulating CPU and was slow rather than deadlocked.
- **Resolution**: both partitions completed successfully, giving aggregate evidence for the entire directory without changing test semantics.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| New descriptor contract tests | PASS: 4 passed |
| Integration tests excluding lifecycle contract | PASS: 566 passed |
| Lifecycle contract matrix | PASS: 79 passed, 1 skipped |
| Full integration aggregate | PASS: 645 passed, 1 skipped |
| JSON parsing and Python compilation | PASS |
| Skill, permission, path, Unicode, workflow, incident, version, model, and platform validators | PASS |
| Platform freshness gate for branch manifest v3.16.6 | PASS |
| Context-compressor accuracy gate | PASS: CCR 100%, signatures 100%, reduction 45.8% |
| Focused Ruff check for the new test | PASS |
| `git diff --check` | PASS |
| CI coverage and cost audit | PASS: existing jobs retained, no workflow edit |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| Integration framework has 180 pre-existing findings under an unscoped Ruff run | P2 | Deferred as WN-2; establish a deliberate baseline during Phase 6 rather than broad-cleaning this phase |
| Revert-then-merge hazard between this branch and `develop` | P1 procedural | Remains BG-4; do not synchronize casually before the Phase 6 merge procedure |

No Phase 2 functional regression or release blocker was identified.

---

## 5. Plan Discrepancies

- Dynamic Workflows were unavailable, so the platform verification sweep ran sequentially as the plan's documented fallback.
- The broad integration suite was partitioned into two commands after the monolithic command exceeded its bounded window. Coverage remained complete.
- No installer was modified and no CI job was added, as required.

---

## 6. Assumptions Made

- **MATCH requires a seedable declarative file contract**: CLI-only flags, UI-only controls, YAML-only levers, or multi-store permission systems remain descriptor-free even when they offer some autonomy behavior.
- **No intermediate tier means `edits_only` is `None`**: consumers can distinguish a real two-tier platform from one that only exposes full autonomy.
- **The branch manifest remains v3.16.6 until the release phase**: the additive autonomy evidence does not restamp the general read-contract freshness marker or perform a version bump during Phase 2.

---

## 7. Testing Summary

### Automated Tests

- `tests/integrations`: 645 passed, 1 skipped across two complete partitions.
- `tests/integrations/test_autonomy_descriptors.py`: 4 passed on the final tree.
- Repository validators and offline compression evaluation: all passed.

### Manual Testing Performed

- Confirmed all 16 registry IDs exist in the autonomy evidence block.
- Confirmed code descriptors equal MATCH verdicts exactly in both directions.
- Confirmed no installer file or CI workflow appears in the Phase 2 diff.
- Confirmed generated caches, coverage files, and logs are ignored.

### Manual Testing Still Needed

None for Phase 2. Live configuration writes and reversions begin in Phase 3 and require their own fixtures and safety gates.

---

## 8. TODO Tracker

### Completed This Session

- [x] 2.1 Design and add the autonomy capability descriptor
- [x] 2.2 Verify every platform's autonomy lever against official documentation
- [x] 2.3 Declare descriptors on verified integrations only
- [x] 2.4 Testing and stabilization

### Remaining

- [ ] Phase 3: autonomy core engine, consent gate, TTL, and audit
- [ ] Phase 4: deny layer integration and hook-independence verification
- [ ] Phase 5: CLI, installer registration, usage-monitor toggles, and documentation
- [ ] Phase 6: architecture refactor, known-gaps reconciliation, CI/CD, and controlled integration

### Out of Scope

- [ ] Configuration writes, backups, TTL reversion, audit records, CLI surfaces, usage-monitor toggles, and installer registration remain assigned to Phases 3 through 5.

---

## 9. Summary and Next Steps

Phase 2 establishes a conservative capability boundary: eight platforms have verified declarative descriptors, and every other platform fails soft with a sourced reason. The complete integration suite and repository validators are green, post-phase tracking is updated, and no installer, runtime configuration, or CI workflow was changed.

**Next session should**:

1. Start Phase 3 from the verified descriptor contract without synchronizing `develop` casually.
2. Build the pure state-transition and config-edit engine with consent, backup, preview, TTL, and audit behavior.
3. Preserve absence-as-unsupported semantics for every DRIFT and UNVERIFIED integration.
