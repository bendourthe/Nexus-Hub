# Session History - Code-Intelligence Hardening Phase 7: Architecture, Policy, and CI

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, pytest-cov, Ruff; GNU Make unavailable, so repository targets were executed as their constituent commands
**Outcome**: The seven-phase code-intelligence plan is locally complete. Profile policy is separated from the MCP transport, the offline contract has executable static and process-level guards, the benchmark is repeatable on Windows OneDrive workspaces, CI runs the full extension suite and regression benchmark inside a container with networking disabled, and the v3.19 gap ledger is finalized with no open items.

## 1. Starting State and Architecture Audit

- **Starting commit**: `4b8245b3` (`feat(code-search): add offline intelligence layers`)
- **Plan recommendation**: strong reasoning tier, high effort
- **Repository audit**: no deprecated or obsolete files, empty directories, duplicate tracked files, redundant directories, or archive candidates were found in the extension scope
- **Documentation audit**: all sixteen v3.19 artifacts are active; no move, rename, archive, or deletion is proposed
- **Module disposition**: the Phase 3 response codec already resides in `response_codec.py`, Phase 4 safety policy already resides in `graph/safety.py`, Phase 5 benchmarks are separated under `benchmarks/`, and Phase 6 providers and dense retrieval are separated from the transport

The only material architecture issue was the Phase 1 profile policy remaining inside `server.py`. It now lives in `tool_profiles.py`, while compatibility wrappers preserve the server's tested import surface. This reduces transport responsibility without changing tool visibility or token-count behavior.

## 2. Whole-Tree Offline Policy Audit

The audit compared every addition since the plan's merge base, then checked the complete current tree for HTTP clients, URL constants, download helpers, and secret-shaped environment reads. The thirteen plan-owned literal matches are loopback proxy traps, forbidden-literal assertions, or policy prose. Twelve pre-existing installer URL hits remain sanctioned installation and help destinations; no plan phase added one.

The durable `test_offline_policy.py` gate now verifies all runtime source, benchmark, and routing-hook files, the exact README policy statement, the reverse-engineering matrix classification, the CI container network isolation, and an actual rejected non-loopback socket connection. The test-level guard permits only loopback traffic needed by Windows asyncio internals.

The final decisions are recorded in `known-gaps.md`: live-model A/B evaluation is dropped, not deferred, because it requires outbound access and credentials; download-based embedding acquisition is dropped, not deferred, because it violates the no-download contract; and additional context providers remain documented extension points rather than release omissions.

## 3. CI/CD Hardening

The path-scoped code-search workflow retains read-only permissions and concurrency cancellation. It builds one focused Python test image, then runs the full extension suite plus the deterministic benchmark regression gate inside a Linux container whose network is disabled and whose only interface is loopback. This provides broader proof without adding an operating-system matrix, scheduled job, duplicate dependency installation, or remote service.

The workflow security validator passes. Local execution of the same guarded test and benchmark commands is green; remote GitHub execution is checked after the Phase 7 push and must not be represented as complete until GitHub reports it.

## 4. Stabilization

Two issues surfaced during final verification:

- Extracting profile policy initially removed a still-required `json` import from `server.py`. The focused suite caught the regression immediately; restoring the import returned all profile and transport tests to green.

- GitHub-hosted runners rejected the initial `unshare --net` isolation before pytest could start. The workflow now uses Docker's supported `--network none` isolation, which preserves the same process-level egress guarantee without disconnecting the runner.

- The fresh container resolved MCP SDK 2.0, which renamed the Python `Tool.inputSchema` attribute to `Tool.input_schema` while retaining the `inputSchema` wire alias. A narrow compatibility accessor now supports both MCP 1.x and 2.x without adding an unnecessary dependency ceiling.

- Repeating the benchmark against its default work root failed on Windows OneDrive with `WinError 5` because the synchronized `.work` reparse directory could retain a corpus handle. Each invocation now creates a unique run directory beneath the selected work root and removes it best-effort, preventing collisions without weakening cleanup.

Two unrelated root-suite cases also encountered one-time `WinError 5` rename denials under the Windows temporary directory. The exact settings-hook case passed 10 of 10 immediate reproductions, and the exact organization-bundle case passed 5 of 5. No unrelated installer change was made for non-reproducible host contention; the final uninterrupted root run passed all 2,904 runnable tests with 28 expected platform-capability skips.

Dense-path coverage was raised from 71% to 92% with local fake-runtime tests that execute tokenizer, ONNX CPU-provider, attention-mask, empty-input, invalid-rank, and backend-failure branches. No remote model or network dependency was introduced.

## 5. Verification

| Gate | Result |
|---|---|
| Focused Phase 7 behavior suite | 37 passed |
| Dense retrieval suite | 11 passed; `search_dense.py` at 92% coverage |
| Measurement harness suite | 9 passed, including repeated same-root execution |
| Default benchmark CLI repeat | Pass twice |
| Full network-guarded `nexus-code-search` suite | 368 passed, 1 skipped |
| `nexus-skill-server` suite | 43 passed |
| `nexus-web-fetch` suite | 29 passed |
| `nexus-skill-scanner` suite | 89 passed |
| `nexus-context-compressor` suite | 215 passed |
| Repository validation | All 24 declared constituent gates passed; skill-quality emitted 7 non-blocking warnings |
| Root repository pytest suite | 2,904 passed, 28 skipped |
| Ruff | Pass for all new and modified Phase 7 Python files |
| Workflow security | Pass |
| Policy statement and matrix | Exact README statement retained; `already-local` remains accurate |

## 6. Files Changed

| File | Change |
|---|---|
| `.github/workflows/code-search.yml` | Full suite and benchmark run in a Linux container with networking disabled |
| `extensions/nexus-code-search/src/nexus_code_search/tool_profiles.py` | Profile ownership, drift guard, visibility filter, and definition-token accounting |
| `extensions/nexus-code-search/src/nexus_code_search/server.py` | Compatibility wrappers over the separated profile policy |
| `extensions/nexus-code-search/benchmarks/harness.py` | Unique per-run work directory for repeatable Windows execution |
| `extensions/nexus-code-search/tests/conftest.py` | Opt-in process-level non-loopback network guard |
| `extensions/nexus-code-search/tests/test_offline_policy.py` | Static, documentation, matrix, workflow, and socket policy proof |
| `extensions/nexus-code-search/tests/test_tool_profiles.py` | Module ownership and compatibility coverage |
| `extensions/nexus-code-search/tests/test_dense_search.py` | Production-adapter and degradation branch coverage |
| `extensions/nexus-code-search/tests/test_measurement_harness.py` | Same-root repeat-run regression coverage |
| `docs/todos.md` | Seven-of-seven completion tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Final Phase 7 exit checklist |
| `docs/v3/v3.19/known-gaps.md` | Final policy audit and zero-gap disposition |
| `docs/v3/v3.19/docs-cleanup-report.md` | Sixteen-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-7-architecture-policy-and-ci.md` | This history |

## 7. Next Step

Commit Phase 7 locally and push the feature branch. Then derive the v3.19.0 release notes from the actual branch diff and obtain explicit approval before any merge, tag, package, or GitHub release action.
