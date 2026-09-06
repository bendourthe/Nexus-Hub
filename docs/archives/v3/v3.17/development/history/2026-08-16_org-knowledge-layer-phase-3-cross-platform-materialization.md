# Development Log: Org Knowledge Layer Phase 3 - Cross-Platform Materialization

**Date**: 2026-08-16
**Operator**: Nexus-Hub maintainer
**Objective**: Implement Phase 3 of the v3.17.4 Org Knowledge Layer plan by projecting a connected bundle into every installed platform's existing instruction and rules surfaces.
**Outcome**: Organization instruction blocks, native rules mirrors, posture reporting, refresh survival, fail-soft behavior, and cross-installer ordering parity are implemented and verified. The phase is ready for Phase 4 guided authoring work.

---

## 1. Starting State

- **Branch**: `feat/v3.17.4-org-knowledge-layer`, with Phases 1 and 2 committed locally
- **Starting commit**: `9742b449`
- **Environment**: Windows PowerShell, Python 3.12.10, pytest, coverage.py, and ShellCheck; GNU Make unavailable
- **Prior session reference**: `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-2-connect-cli.md`
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md`

Phase 2 had established the durable connection record and bundle validation seam. Phase 3 needed to consume only that seam, project deterministic content into existing platform read paths, survive destructive catalog refreshes, and describe the resulting posture without claiming managed enforcement.

---

## 2. Implementation

### 2.1 Materialize connected organization knowledge

`scripts/lib/integrations/org_knowledge.py` now resolves the connected directory or cached Git clone, validates it, renders a dedicated organization block, and discovers the actual instruction destinations registered by each integration. The block uses independent organization markers, is placed after the Nexus-Hub marker block, includes explicit precedence and an on-demand references pointer, and warns without truncation if its rendered body exceeds 200 lines.

Rules are copied into an `org/` subtree under every declared or manifest-discovered native rules root. The destination directory and every copied rule file are manifest-tracked. Missing connections are silent during quiet installer runs, while invalid connections, unreadable bundles, and write or bookkeeping failures produce one warning and skip materialization without failing the platform install.

### 2.2 Wire the dispatcher for both scopes

`IntegrationBase.install()` invokes organization seeding at the same detection-gated dispatcher seam as platform defaults. Platform defaults retain their existing global-only behavior inside their helper; organization seeding handles both scopes so workspace-only surfaces such as Cursor and Aider receive organization instructions without invented global paths. The runner exposes verbosity through one additive `InstallContext` field.

### 2.3 Preserve Claude organization rules after refresh

The empirical ordering check found that both installers invoked the Claude registry before mirroring `catalog/rules/`. Refresh mode uses deletion semantics, so it could remove the newly seeded `rules/org/` subtree. After explicit approval, the unchanged Claude registry call was moved after the rules mirror in the global and workspace blocks of both installers. No command argument, template, platform config key, dependency, or read path changed.

### 2.4 Report platform posture

`nexus-hub org status` now prints all 16 registered platforms even without a connection. Verified Claude, Cursor, Codex, Gemini, and Antigravity families report `default`; Copilot reports `advisory` with the documented `Personal > Repository > Organization` inversion; platforms without verified precedence evidence degrade to `advisory (unclassified)`. The footer states that projections are instructions rather than enforcement and points to the Phase 4 authoring escalation guidance.

---

## 3. Testing and Verification

### Focused Phase 3 evidence

| Check | Result |
|---|---|
| Phase 3 materialization suite | PASS - 18 passed |
| Phase 1 through Phase 3 org suite with coverage | PASS - 83 passed, 1 skipped |
| `org_knowledge.py` line coverage | PASS - 87.38 percent |
| Representative recovery and dry-run contracts | PASS - 12 passed |
| All-platform idempotence | PASS - 16 passed |
| All-platform uninstall reversal | PASS - 16 passed |
| All-platform sibling preservation | PASS - 15 passed, 1 skipped |
| Integration lifecycle ownership | PASS - 10 passed |

### Repository gates

| Check | Result |
|---|---|
| Installer tests | PASS - 418 passed, 17 skipped |
| Non-contract integration tests | PASS - 564 passed |
| Plans and skills tests | PASS - 782 passed |
| Validators, workflows, and root regression | PASS - 791 passed, 2 skipped |
| Five extension suites | PASS - 670 passed, 1 skipped |
| Exact `make validate` constituents | PASS |
| ShellCheck | PASS |
| Python compile/import checks | PASS |
| CI readiness and optimization audit | PASS - no workflow edit required |
| Gitignore audit | PASS - 0 patterns added |

The monolithic repository suite and an all-platform partial-recovery slice exceeded bounded local Windows runtimes without reporting an assertion failure. The same condition is already tracked as WN-6. Every affected Phase 3 path, all 16 idempotence/uninstall paths, all non-contract integration modules, and the six representative recovery/dry-run platforms passed. Protected-branch Linux CI remains the authoritative unbounded full-matrix result.

---

## 4. Empirical Questions and Decisions

1. **Claude refresh ordering**: The Bash and PowerShell installers both mirrored catalog rules after their registry call. Refresh deletion could prune `rules/org/`. The approved resolution is to reseed after the mirror by moving the registry call in all four Claude blocks.
2. **Dedicated instruction mode**: Dedicated mode rewrites the whole instruction file when overwrite is enabled. Dispatcher ordering writes the instruction first and then re-appends the organization block; the Nexus-AI regression proves the block remains singular after a second overwrite install.
3. **PowerShell parity**: `Invoke-RegistryPlatform` now follows `Safe-Folder-Copy` for Claude rules in both scopes, matching the Bash order. Installer parity and PowerShell portability gates pass.
4. **Scope discrepancy**: The plan described the platform-default precedent as reaching both scopes, while the helper itself is global-only. The dispatcher now shares the detection gate, leaves platform-default scope behavior unchanged, and lets organization seeding cover both scopes as required by the Cursor and Aider acceptance criteria.

---

## 5. CI/CD and Documentation Audit

The main CI workflow already triggers on every changed code and test path, uses cancel-in-progress concurrency, caches Python dependencies, runs the complete integration and installer suites on Linux, and runs installer plus validator coverage on Windows. Expensive Windows and multi-OS smoke jobs remain push-gated. No new dependency, secret, runtime, workflow, or job is required.

The docs layout audit classifies all nineteen v3.17 artifacts as active and proposes no move, archive, or deletion. README and standalone devlog updates are no-ops in this phase: Phase 5 owns lifecycle and user documentation, and the repository has no separate devlog artifact. The Unreleased changelog, plan checklist, progress dashboard, known-gaps ledger, cleanup report, and this history are updated.

---

## 6. Known Gaps and Deviations

- **WN-6 remains open**: the local Windows monolithic integration matrix exceeds the bounded phase runtime. Fresh Phase 3 shards substantially improve evidence but do not replace protected-branch CI for the complete unbounded matrix.
- **No new gap**: Phase 3 adds no NI, DF, BG, MT, or QG item and no release blocker.
- **Approved deviation**: The original design expected no installer edit, but the empirical refresh-order finding required moving four existing registry calls. The maintainer approved that bounded ordering change before it was applied.
- **Tooling deviation**: GNU Make was unavailable, so every `make validate`, `make lint`, and `make test` constituent was invoked directly or in bounded shards.

---

## 7. Next Steps

1. Commit the Phase 3 checkpoint according to the maintainer's selected commit option.
2. Begin Phase 4 guided authoring from the committed Phase 3 state.
3. Confirm the complete integration matrix on protected-branch CI during final integration.
