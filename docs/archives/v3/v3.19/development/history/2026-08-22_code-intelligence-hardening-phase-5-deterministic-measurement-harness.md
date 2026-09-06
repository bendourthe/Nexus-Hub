# Session History - Code-Intelligence Hardening Phase 5: Deterministic Measurement Harness

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 5 - Deterministic measurement harness
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, Ruff, ShellCheck; GNU Make unavailable, so repository targets were executed as their constituent commands
**Outcome**: `nexus-code-search` now has a repository-only, credential-free benchmark that runs four fixed task shapes through the real index and MCP dispatch, reports cost and quality together, and gates precision, recall, and mean reciprocal rank against a committed baseline. Both installers remove the benchmark tree before installing the extension.

## 1. Starting State and Evaluation Contract

- **Starting commit**: `4ea828da` (`feat(code-search): add safety preflights`)
- **Branch state**: clean feature branch after the Phase 4 local-only commit
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: deterministic labeled-answer scoring replaced any model-based judge, preserving the plan's no-network, no-credential boundary

The contract was written test-first. It requires a versioned goldset, explicit expected ranked answers, hand-checked empty and all-wrong scoring, real tool dispatch, raw-cost arithmetic, a quality regression mode, a socket-blocked empty-environment run, static absence of HTTP or credential surfaces, and installer exclusions for every benchmark artifact.

## 2. What Was Implemented

### 2.1 - Fixed corpus and goldset

- Added a small committed Python corpus with one direct caller edge, one cross-file import, one test, and one unimported uncalled symbol.
- Added four versioned gold tasks: locate `helper`, find all callers of `helper`, classify `orphan` as unused from indexed evidence, and trace the impact radius of `helper`.
- Recorded the smallest valid tool profile for each task so profile-definition cost is measured against the full surface.
- Strictly validate version, corpus confinement, task shape, tool, profile, arguments, expected answers, and unique task identifiers.

### 2.2 - Cost and quality receipt

- Dispatches `index_graph`, `code_search`, `code_callers`, `code_delete_safety`, and `code_impact` through the production server seam.
- Records JSON and compact UTF-8 bytes, deterministic standard-library token estimates, full and task-profile definition tokens, and wall-clock latency for every task.
- Computes precision, recall, and reciprocal rank per task, then macro-averages all three metrics.
- Emits both a stable JSON receipt and a Markdown table, with raw values sufficient to recompute every headline delta.
- Stores only deterministic quality metrics in the CI baseline; latency and serialized byte totals remain observations because host speed and temporary path length vary.

### 2.3 - Regression and installation boundaries

- Added `--check` mode that fails when precision, recall, or mean reciprocal rank drops beyond the configured tolerance.
- Added a path-scoped CI step to the existing cached, cancel-in-progress code-search workflow.
- Updated both installers to remove `benchmarks/` after copying the extension and before editable installation.
- Kept benchmark reports and work directories ignored and outside the installed Python package.

## 3. Test-Driven Troubleshooting

The initial red test failed at import because the repository-only benchmark package did not exist. After implementation, the offline run exposed one real scorer defect: the safety tier lives under `verdict.tier`, not at the response root. Correcting that extractor restored perfect quality without altering the graph or expected answer.

The first cost receipt also disproved an assumption in the test: forced compact encoding is not smaller for these four short responses. The assertion was corrected to require exact arithmetic rather than a positive saving. This is the intended evidence: production `auto` mode should keep JSON for small responses, while the profile reduction is independently substantial.

## 4. Fresh Measurement Receipt

| Metric | Result |
|---|---:|
| Macro precision | 100% |
| Macro recall | 100% |
| Mean reciprocal rank | 1.000 |
| Full definitions across four tasks | 22,404 estimated tokens |
| Task-profile definitions across four tasks | 15,224 estimated tokens |
| Definition-token reduction | 7,180 tokens (32.1%) |
| JSON responses | 2,419 bytes; 898 estimated tokens |
| Forced compact responses | 2,664 bytes; 1,095 estimated tokens |
| Forced compact delta | 245 bytes larger (10.1%); production `auto` therefore retains JSON |

Latency was recorded per task in the machine-readable receipt but was not baselined. The fresh run measured approximately 4.3 to 5.7 ms per query on this host.

## 5. Verification

| Gate | Result |
|---|---|
| Test-first red state | Missing `benchmarks` package failed collection as expected |
| Focused Phase 5 suite | 8 passed |
| Stored quality baseline | Pass at 100% precision, 100% recall, and 1.000 MRR |
| Full `nexus-code-search` suite | 346 passed, 1 skipped |
| Offline and credential-free proof | Full harness passed with socket connections blocked and environment variables removed |
| Static egress proof | No HTTP-client import, URL helper, environment credential read, or API-key surface in the harness |
| Ruff | Pass for the new harness and contract tests |
| Bash installer | ShellCheck pass |
| PowerShell installer | AST parse pass |
| Installer artifact boundary | Both installers contain tested benchmark-removal steps before package installation |

## 6. CI/CD and Post-Phase Review

The existing `.github/workflows/code-search.yml` already had extension-only paths, read-only permissions, cancel-in-progress concurrency, pip caching, and one non-matrix Ubuntu job. Phase 5 adds one cheap explicit benchmark gate after the comprehensive test step; no schedule, credential, artifact upload, or additional runner is needed.

The docs cleanup audit classifies all fourteen current v3.19 artifacts as active and proposes no move or deletion. The v3.19 known-gaps ledger records zero open items through Phase 5. `docs/DEVLOG.md` remains unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 7. Files Changed

| File | Change |
|---|---|
| `extensions/nexus-code-search/benchmarks/` | Offline corpus, validated goldset, quality baseline, methodology, runner, and ignored run outputs |
| `extensions/nexus-code-search/tests/test_measurement_harness.py` | Schema, scoring, offline, arithmetic, regression, egress, and installer contracts |
| `scripts/installer.sh` | Remove repository-only benchmark artifacts before installation |
| `scripts/installer.ps1` | PowerShell-parity benchmark exclusion |
| `.github/workflows/code-search.yml` | Path-scoped offline benchmark quality gate |
| `docs/todos.md` | Phase 5 progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Phase 5 completion checklist |
| `docs/v3/v3.19/known-gaps.md` | Zero-gap reconciliation through Phase 5 |
| `docs/v3/v3.19/docs-cleanup-report.md` | Fourteen-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-5-deterministic-measurement-harness.md` | This history |

## 8. Next Step

Phase 6 adds a documented local context-provider extension point and optional dense-plus-keyword retrieval that loads only pre-placed local weights. Per the requested boundary, Phase 5 changes remain uncommitted until Phase 6 is fully implemented and verified.
