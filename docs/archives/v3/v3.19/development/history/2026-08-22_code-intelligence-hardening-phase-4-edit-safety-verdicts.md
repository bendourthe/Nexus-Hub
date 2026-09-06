# Session History - Code-Intelligence Hardening Phase 4: Edit-Safety Verdicts

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 4 - Edit-safety verdicts
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, coverage, Ruff; GNU Make unavailable, so repository targets were executed as their constituent commands
**Outcome**: `nexus-code-search` now exposes exactly three read-only mutation preflights: `code_edit_safety`, `code_delete_safety`, and `code_rename_safety`. Each returns one ordered verdict, one non-empty recommended action, and concrete indexed caller/importer/reference, test-presence, complexity-proxy, and index-health evidence while honestly reporting unavailable cross-repository visibility and insufficient index data.

## 1. Starting State and Routing

- **Starting commit**: `a761ae0b` (`feat(code-search): add compact responses`)
- **Branch state**: clean feature branch after the Phase 3 local-only commit
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: the active Codex session remained at or above the planned tier because an under-reported risk verdict is more dangerous than returning no verdict

The verdict tiers were fixed as a tested module contract before implementation. The scope remained exactly three preflights plus the existing `code_impact` traversal; no generic analytics or mutation executor was added.

## 2. What Was Implemented

### 2.1 - Ordered honesty contract

- Added `docs/edit-safety-verdicts.md` with five ordered tiers: `runtime_dependency`, `insufficient_data`, `external_contract`, `internal_dependency`, and `no_known_callers`.
- Ranked unknown evidence ahead of lower-risk evidence-backed tiers so an absent, empty, or unresolved index constrains action.
- Defined operation-specific one-line recommendations for edit, delete, and rename.
- Explicitly documented that `no_known_callers` is a possible dead-code signal, not proof of safety.
- Explicitly reported cross-repository visibility as unavailable rather than inferring it from one local graph.

### 2.2 - Read-only evidence evaluator

- Added `graph/safety.py`, composed from `GraphQueryManager` resolution and the existing node/edge schema.
- Opened SQLite with `mode=ro`, `immutable=1`, and `query_only`, then closed every connection deterministically.
- Collected incoming calls, imports, references, instantiations, decorators, exports, inheritance, implementation, and override evidence.
- Reused indexed `IMPORT` nodes to represent genuine cross-file imports because language extractors intentionally resolve call edges in-file only.
- Derived conservative test presence from indexed file paths and reported source span plus incoming dependency count as a structural complexity proxy, without claiming cyclomatic complexity.

### 2.3 - Three bounded MCP tools

- Added `code_edit_safety`, `code_delete_safety`, and `code_rename_safety` through one shared handler and one tool-definition helper.
- Assigned all three to the `standard` and `full` profiles, never `minimal`.
- Kept response formatting centralized, so JSON, compact, and automatic response modes apply without per-tool codec code.
- Updated the surface to 7 minimal, 16 standard, and 20 full tools.

## 3. Tests and Troubleshooting

The contract suite started red at the missing safety module. The first implementation correctly classified same-file and missing-symbol cases but found no cross-file caller edges. Inspection confirmed this is an explicit extractor boundary: Python call edges are in-file only. The fix did not expand the resolver or synthesize test edges. It used existing indexed `IMPORT` nodes such as `service.runtime_target`, preserving real file and line evidence for production and test importers.

The final tests build a real indexed fixture with a cross-file production import, a cross-file test import, an internal caller, an unreferenced symbol, and an unresolved symbol. They snapshot every repository and index byte before and after each MCP tool call, run under blocked proxies with a dummy API key, assert all response keys and recommendations, enforce profile placement, and prove the exact three-tool scope cap.

## 4. Verification

| Gate | Result |
|---|---|
| Focused safety contract suite | 14 passed |
| Safety, profile, codec, and README measurement suite | 44 passed |
| Full `nexus-code-search` suite | 338 passed, 1 skipped |
| Full code-search coverage | 89% overall; `graph/safety.py` 96%; `server.py` 80% |
| New-file Ruff check | Pass for the safety module and contract tests |
| Read-only proof | Byte-identical tree and index before/after all three tool calls |
| Offline proof | Pass with blocked proxies and no credential access |
| Honesty rule | Missing index and unresolved symbol both return `insufficient_data` |
| Scope cap | Exactly three tool names end in `_safety` |
| Fresh root regression baseline | Phase 3: 2,904 passed, 28 skipped; not rerun because Phase 4 changes only the extension and its docs |

## 5. CI/CD and Post-Phase Review

No CI edit was needed. `.github/workflows/code-search.yml` already provides extension-only paths, read-only permissions, cancel-in-progress concurrency, pip caching, and one non-matrix Ubuntu job. The full extension suite exercises the new contracts, and the always-on aggregate workflow preserves protected-branch required-check safety.

The docs cleanup audit classifies all thirteen final v3.19 artifacts as active and proposes no move or deletion. The v3.19 known-gaps ledger records zero open items. `docs/DEVLOG.md` remains unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 6. Files Changed

| File | Change |
|---|---|
| `extensions/nexus-code-search/docs/edit-safety-verdicts.md` | Ordered verdict, evidence, response, honesty, and scope contract |
| `extensions/nexus-code-search/src/nexus_code_search/graph/safety.py` | Immutable read-only evidence evaluator and operation recommendations |
| `extensions/nexus-code-search/src/nexus_code_search/server.py` | Three standard-profile tools and shared handler |
| `extensions/nexus-code-search/tests/test_edit_safety.py` | Verdict, response, read-only, offline, profile, and scope contracts |
| `extensions/nexus-code-search/tests/test_tool_profiles.py` | Updated exact standard surface |
| `extensions/nexus-code-search/tests/test_response_codec.py` | Representative measurements for all three new tools |
| `extensions/nexus-code-search/README.md` | 20-tool surface, live profile costs, measurements, and safety reference |
| `docs/todos.md` | Phase 4 progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Phase 4 completion checklist |
| `docs/v3/v3.19/known-gaps.md` | Zero-gap reconciliation through Phase 4 |
| `docs/v3/v3.19/docs-cleanup-report.md` | Thirteen-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-4-edit-safety-verdicts.md` | This history |

## 7. Next Step

Phase 5 adds a deterministic, offline measurement harness for tool-definition savings, response-byte savings, retrieval quality, and edit-safety usefulness. Per the requested boundary, Phase 5 and Phase 6 will share one local commit after both phases pass.
