# Session History - Code-Intelligence Hardening Phase 3: Compact Response Encoding

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 3 - Compact response encoding
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, coverage, Ruff; GNU Make unavailable, so repository targets were executed as their constituent commands
**Outcome**: `nexus-code-search` now offers a Nexus-Hub-owned, deterministic, round-trippable compact wire format on every MCP tool through `response_format=json|compact|auto`. JSON remains the compatibility default, automatic mode selects compact output only after measured UTF-8 savings meet the configurable 15% default, producer exceptions return valid JSON, decoder failures can retry JSON, and the consumer compressor explicitly preserves compact-wire bytes.

## 1. Starting State and Routing

- **Starting commit**: `8999ae97` (`feat(hooks): route searches to local index`)
- **Branch state**: clean feature branch after the Phase 2 local-only commit
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: the active Codex session remained at or above the planned tier because the silent-corruption risk required exact schema and type reasoning

The implementation uses one producer response seam rather than modifying seventeen handlers independently. Tool logic still produces its existing JSON, and the MCP boundary applies a requested alternate format once after dispatch.

## 2. What Was Implemented

### 2.1 - Independent wire-format contract

- Added `extensions/nexus-code-search/docs/wire-format.md` as the normative Nexus-Hub specification.
- Defined the exact `NEXUS-CW/1` first-line marker, JSON envelope, deterministic table ordering, column declarations, presence bitmaps, and typed JSON value arrays.
- Preserved top-level key order, first-seen column order, nested JSON values, Unicode, delimiter characters, null values, and the distinction between null and a missing field.
- Documented the protocol-level JSON retry requirement for corrupt or unsupported compact responses.

### 2.2 - Standard-library codec and server seam

- Added `nexus_code_search.response_codec` with encoding, decoding, JSON retry, and actual UTF-8 savings measurement.
- Added `response_format` and `compact_min_savings_pct` to every live tool schema.
- Kept `json` as the default and returned the original handler `TextContent` objects untouched on that path.
- Added `compact` for forced wire output and `auto` for threshold-selected output.
- Caught every producer encoding or response-formatting exception and preserved the valid JSON handler response.
- Refactored only the dispatch boundary needed to apply formatting once; individual handler behavior remains unchanged.

### 2.3 - Consumer-compressor composition

- Added an exact-marker identity guard to `compress_output()` so producer-formatted payloads cannot be double-compressed or have framing changed.
- Verified that CCR marker strings remain typed response values and round-trip unchanged.
- Documented the producer-side schema codec versus consumer-side content router split in both extension READMEs.

### 2.4 - Measured tool behavior

The README table is generated conceptually from one committed representative response fixture per tool and machine-checked against `measure_savings()`. At the default 15% threshold, automatic mode selects compact for `search_code`, `generate_context_map`, `map_health`, `generate_knowledge_map`, `code_search`, and `code_node`; smaller or deeply nested shapes remain JSON. Forced compact remains available for consumers that prioritize one format over size.

Adding two response controls to every input schema changed the measured tool-definition baselines to 1,841 tokens for `minimal`, 3,613 for `standard`, and 4,753 for `full`. The relative savings remain about 61% and 24% against full.

## 3. Tests and Troubleshooting

The codec test suite began red at the missing `response_codec` import. The implemented suite then exercised explicit edge cases plus 100 fixed-seed generated JSON structures. It covers empty and single-row responses, delimiters, non-ASCII text, nested data, null and missing fields, deterministic bytes, threshold selection, invalid-control fail-open behavior, injected encoder failure, decoder JSON retry, every tool schema, the shared response boundary, per-tool README measurements, consumer composition, CCR markers, and blocked-network purity.

The first measurement command failed in PowerShell string parsing before project code ran; the calculation was rerun with an unambiguous print expression. Ruff identified three issues introduced in the new codec/test files, which were corrected. Other Ruff findings in `server.py` and the compressor module were verified as pre-existing and left untouched to preserve phase scope.

## 4. Verification

| Gate | Result |
|---|---|
| Focused codec, profile, and offline tests | 30 passed |
| Focused compressor routing tests | 24 passed, 191 deselected |
| Full `nexus-code-search` suite | 323 passed, 1 skipped |
| Full `nexus-context-compressor` suite | 215 passed |
| Full root regression suite | 2,904 passed, 28 skipped |
| Full code-search coverage | 88% overall; `response_codec.py` 93%; `server.py` 81% |
| New-file Ruff check | Pass for the codec and codec tests |
| Wire determinism and generated round trips | Pass across 100 fixed-seed structures plus explicit edge cases |
| Producer fail-open and decoder JSON retry | Pass through injected failure tests |
| Compressor composition and CCR marker preservation | Pass with identity metrics and no routed segments |
| Offline and credential-free codec contract | Pass under blocked proxies plus static forbidden-primitive audit |

## 5. CI/CD and Post-Phase Review

No CI edit was needed. `.github/workflows/code-search.yml` already provides path-scoped code-search coverage, read-only permissions, cancel-in-progress concurrency, pip caching, and no expensive matrix. The stable aggregate workflow remains always-on for required-check safety and already runs both complete extension suites, so it covers the cross-extension composition contract without adding a duplicate runner.

The docs cleanup audit classifies all twelve final v3.19 artifacts as active and proposes no move or deletion. The v3.19 known-gaps ledger records zero open items. `docs/DEVLOG.md` remains unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 6. Files Changed

| File | Change |
|---|---|
| `extensions/nexus-code-search/docs/wire-format.md` | Normative compact-wire specification and retry contract |
| `extensions/nexus-code-search/src/nexus_code_search/response_codec.py` | Standard-library encoder, decoder, and byte measurement |
| `extensions/nexus-code-search/src/nexus_code_search/server.py` | Shared dispatch/format seam and all-tool input controls |
| `extensions/nexus-code-search/tests/test_response_codec.py` | Round-trip, failure, measurement, composition, and offline regressions |
| `extensions/nexus-code-search/README.md` | Usage, producer/consumer split, measured savings, and definition costs |
| `extensions/nexus-context-compressor/src/nexus_context_compressor/__init__.py` | Exact compact-wire identity guard |
| `extensions/nexus-context-compressor/README.md` | Consumer-side composition contract |
| `docs/todos.md` | Phase 3 progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Phase 3 completion checklist |
| `docs/v3/v3.19/known-gaps.md` | Zero-gap reconciliation through Phase 3 |
| `docs/v3/v3.19/docs-cleanup-report.md` | Twelve-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-3-compact-response-encoding.md` | This history |

## 7. Next Step

Phase 4 adds three read-only edit-safety verdict tools composed from the existing graph. They must distinguish unsafe, caution, safe, and insufficient-data cases without expanding into a general analytics surface.
