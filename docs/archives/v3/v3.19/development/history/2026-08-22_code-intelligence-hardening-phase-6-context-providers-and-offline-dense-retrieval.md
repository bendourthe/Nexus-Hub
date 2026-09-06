# Session History - Code-Intelligence Hardening Phase 6: Context Providers and Offline Dense Retrieval

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 6 - Context providers and offline dense retrieval
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, pytest-cov, Ruff; GNU Make unavailable, so repository targets were executed as their constituent commands
**Outcome**: `nexus-code-search` can now index Markdown through a documented local context-provider port and optionally blend keyword and dense scores through a default-off ONNX path that accepts only pre-placed local weights. Missing configuration, dependencies, weights, or encoder execution degrades to keyword search with an actionable hint and never initiates a download.

## 1. Starting State and Architecture

- **Starting commit**: `4ea828da` (`feat(code-search): add safety preflights`)
- **Working boundary**: Phase 5 remained uncommitted so Phases 5 and 6 can share the user-requested commit
- **Plan recommendation**: strong reasoning tier, high effort
- **Provider design**: extend the existing framework resolver seam instead of introducing a parallel registry
- **Dense design**: preserve FTS5 as the mandatory retrieval layer and make local dense scoring an optional enhancement

The architecture uses one narrow `ContextProvider` port that contributes native graph nodes and edges. The initial registry contains only Markdown because it provides immediate repository value while keeping additional ecosystems as explicit extension points. Dense retrieval has a separate injected encoder seam, which keeps ranking deterministic in tests and makes the production dependency boundary lazy and fail-soft.

## 2. Context-Provider Implementation

- Added file-pattern discovery and an `applies_to` contract to the existing framework abstraction.
- Added an intentionally small provider registry with one Markdown provider.
- Parsed ATX headings locally and represented document hierarchy through existing module nodes and containment edges.
- Extended the extraction orchestrator to admit provider-owned non-code files and merge their graph contributions without invoking a code parser.
- Isolated provider failures so one malformed contextual artifact cannot abort repository indexing.
- Documented the provider contract, registration point, local-only restriction, and extension procedure.

## 3. Offline Dense Retrieval

- Added a `dense` optional dependency group for ONNX Runtime, NumPy, and tokenizers while leaving the default installation unchanged.
- Added `NEXUS_CODE_SEARCH_DENSE` as the explicit opt-in and `NEXUS_CODE_SEARCH_MODEL_DIR` as the optional local path override.
- Required both `model.onnx` and `tokenizer.json` to exist before any optional dependency import occurs.
- Loaded the tokenizer and ONNX session directly from local filesystem paths; the implementation has no URL, HTTP client, download helper, or implicit model acquisition path.
- Added cosine scoring and reciprocal-rank-style keyword/dense blending while retaining the existing keyword result contract.
- Returned the actual execution mode, degradation state, and exact installation or weight-placement hint from hybrid searches.
- Preserved the README policy statement exactly and documented that users obtain and place weights themselves.

## 4. Test-Driven Stabilization

The initial red state failed collection because neither the provider registry nor dense module existed. The completed tests exercise provider discovery, Markdown graph contributions, orchestrator searchability, network-blocked parsing, default-off behavior, absent optional imports, missing weights, missing dependencies, a pre-placed injected encoder, hybrid ranking, encoder failure, the README claim, and static absence of outbound acquisition surfaces.

One integration test that previously asserted hybrid mode was unsupported was updated to assert the new durable behavior: with dense retrieval disabled, a hybrid request succeeds through keyword fallback and reports the precise reason. No default search behavior changed.

## 5. Verification

| Gate | Result |
|---|---|
| Focused Phase 6 suite | 18 passed |
| Full `nexus-code-search` suite | 359 passed, 1 skipped |
| Overall extension coverage | 89% |
| New Markdown provider coverage | 97% |
| Dense module coverage | 71%; all offline and fallback branches required by the phase are covered |
| Network-blocked provider and dense paths | Pass; no connection attempted |
| Optional-import boundary | Pass; default and missing-weight paths do not import dense dependencies |
| Static dense egress proof | No URL constant, download helper, known remote model loader, or HTTP client import |
| README policy claim | Exact `zero outbound calls, zero API keys, zero model downloads` line retained |
| RE matrix | No diff; `already-local` remains accurate |
| Ruff | Pass for all Phase 6 files |

## 6. CI/CD and Post-Phase Review

The existing `.github/workflows/code-search.yml` remains the optimized Phase 6 route: it is extension-path scoped, read-only, cached, cancel-in-progress, and runs the comprehensive extension suite containing the network-blocked provider and dense tests. A heavyweight dense dependency job is unnecessary because production dependencies remain optional and the tests inject a local encoder at the seam; adding such a job would increase cost without testing the offline contract more effectively.

The docs cleanup audit classifies all fifteen current v3.19 artifacts as active and proposes no move or deletion. The v3.19 known-gaps ledger records zero open items through Phase 6. `docs/DEVLOG.md` remains unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 7. Files Changed

| File | Change |
|---|---|
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/base.py` | Context-provider contract |
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/markdown.py` | Local Markdown heading provider |
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/__init__.py` | Intentionally small provider registry |
| `extensions/nexus-code-search/src/nexus_code_search/extraction/orchestrator.py` | Provider file discovery and graph integration |
| `extensions/nexus-code-search/src/nexus_code_search/search_dense.py` | Local-only encoder loading and hybrid scoring |
| `extensions/nexus-code-search/src/nexus_code_search/config.py` | Default-off dense configuration |
| `extensions/nexus-code-search/src/nexus_code_search/server.py` | Hybrid mode dispatch and fail-soft response metadata |
| `extensions/nexus-code-search/pyproject.toml` | Optional dense dependency group |
| `extensions/nexus-code-search/docs/context-providers.md` | Provider extension documentation |
| `extensions/nexus-code-search/README.md` | Provider and user-supplied-weight instructions |
| `extensions/nexus-code-search/tests/test_context_providers.py` | Provider, graph, searchability, and offline contracts |
| `extensions/nexus-code-search/tests/test_dense_search.py` | Dense opt-in, local-weight, degradation, ranking, egress, and documentation contracts |
| `extensions/nexus-code-search/tests/test_server_integration.py` | Hybrid keyword-fallback integration behavior |
| `docs/todos.md` | Phase 6 progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Phase 6 completion checklist |
| `docs/v3/v3.19/known-gaps.md` | Zero-gap reconciliation through Phase 6 |
| `docs/v3/v3.19/docs-cleanup-report.md` | Fifteen-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-6-context-providers-and-offline-dense-retrieval.md` | This history |

## 8. Next Step

Phase 7 performs the final architecture and policy audit, reconciles known gaps across all phases, and hardens CI with a whole-extension network-blocked gate. Per the requested boundary, Phases 5 and 6 are committed together locally before Phase 7 begins.
