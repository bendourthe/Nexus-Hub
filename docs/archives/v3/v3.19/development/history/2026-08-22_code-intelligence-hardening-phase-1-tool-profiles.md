# Session History - Code-Intelligence Hardening Phase 1: Tool Profiles and Dependency Ceilings

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 1 - Tool-profile gating and dependency-ceiling convention
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, coverage, Ruff, ShellCheck; GNU Make unavailable, so `make validate` was executed as its constituent commands
**Outcome**: `nexus-code-search` now exposes `minimal`, `standard`, and `full` tool profiles through `NEXUS_CODE_SEARCH_TOOL_PROFILE`, defaults to the backward-compatible full surface, measures a reproducible offline definition-token baseline, and documents evidence-bearing dependency ceilings. Every required gate passed and no known gap remains open.

## 1. Starting State and Routing

- **Starting commit**: `9d06e989` (`Merge pull request #92 from bendourthe/main`)
- **Branch base**: clean `develop`, following the declared develop+main model
- **Plan recommendation**: mid reasoning tier, medium effort
- **Implementation route**: the active Codex session remained at or above the planned tier, so no downshift or model switch was made

The plan claimed 18 current MCP tools. Runtime inspection of `_all_tools()` proved the live surface has 17. The implementation and plan were reconciled to the verified count; no placeholder or speculative eighteenth tool was added.

## 2. What Was Implemented

### 2.1 - Tool profiles

- Added `tool_profile` to `CodeSearchConfig`, with `full` as the backward-compatible default.
- Added the `NEXUS_CODE_SEARCH_TOOL_PROFILE` environment override with whitespace/case normalization and fail-open fallback to `full` for invalid values.
- Added one `TOOL_MINIMUM_PROFILE` registry assigning all 17 definitions to their lowest useful profile, plus a runtime drift guard comparing the registry against `_all_tools()`.
- Wired the configured profile into the real MCP `list_tools` callback.

Profile composition is 7 tools for `minimal`, 13 for `standard`, and 17 for `full`. Profiles reduce the advertised schema surface only; they are explicitly not an authorization boundary.

### 2.2 - Reproducible cost measurement and documentation

- Added `estimate_tokens_offline()` as the stable stdlib baseline alongside the existing optional-tokenizer path.
- Added `tool_definition_token_count()` over compact, sorted MCP definition JSON.
- Documented 952 estimated tokens for `minimal`, 1,962 for `standard`, and 2,594 for `full`, including the roughly 63% and 24% savings against full.
- Added tier guidance using the existing `fast`, `standard`, `strong`, and `frontier` vocabulary and cross-links to `model-routing` and `prompt-token-optimization`.
- Corrected the README's older twelve-tool introduction to the live 17-tool count while preserving the policy-compliance line exactly.

### 2.3 - Dependency-ceiling convention

- Added the repository rule that every upper bound records unacceptable or unknown newer behavior, why it matters, verification date, evidence, newer-version suite result, and lift condition.
- Reconciled every upper bound under `extensions/*/pyproject.toml`; the only active set is the tree-sitter family in `extensions/nexus-code-search/pyproject.toml`.
- Replaced historical shorthand with dated, explicit evidence and lift conditions without claiming a nonexistent 0.26-compatible suite run.

## 3. Tests and Troubleshooting

The new `test_tool_profiles.py` covers exact profile membership, full-profile reachability, default compatibility, environment override normalization, invalid-value fail-open behavior, monotonic token cost, README measurement drift, registry completeness, and the actual stdio server registration.

Two issues surfaced and were fixed during the loop:

- The README parser initially accepted digits only and missed the comma-formatted four-digit counts; the test now parses thousands separators.
- The first cost measurement used an installed optional tokenizer and would have drifted on CI hosts without it; profile documentation now deliberately uses the deterministic stdlib estimator.

Ruff also surfaced six pre-existing warnings in touched modules. Its two unrelated autofixes were reviewed and reverted; the phase did not clean adjacent code. The repository's declared lint target, ShellCheck over both installer scripts, passed.

## 4. Verification

| Gate | Result |
|---|---|
| Focused profile and token tests | 28 passed before transport coverage; final profile file has 10 focused tests |
| Full extension coverage | 304 passed, 1 skipped, 88% overall |
| Modified-module coverage | `config.py` 81%, `tokens.py` 91%, `server.py` 80% |
| JSON, bundle, quality, routing, permission, installer, security, and workflow validators | Pass |
| Required checks, docs, decisions, registry, version, template, model-profile, platform-contract, and defaults validators | Pass |
| Compression accuracy gate | Pass: CCR 100.0%, signatures 100.0%, reduction 45.8% |
| ShellCheck | Pass for `scripts/installer.sh` and `install.sh` |
| Git diff hygiene | `git diff --check` passed; coverage and pytest caches are ignored |

## 5. CI/CD and Post-Phase Review

No CI edit was needed. `.github/workflows/code-search.yml` already uses extension-only path filters, read-only permissions, cancel-in-progress concurrency, pip dependency caching keyed to the extension manifest, and a single Ubuntu job with no expensive matrix to gate. The comprehensive extension suite remains present in `.github/workflows/ci.yml`.

The docs cleanup audit classified all ten final v3.19 artifacts as active and proposed no move or deletion. The v3.19 known-gaps ledger records zero open items. `docs/DEVLOG.md` remained unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 6. Files Changed

| File | Change |
|---|---|
| `extensions/nexus-code-search/src/nexus_code_search/config.py` | Profile configuration and environment override |
| `extensions/nexus-code-search/src/nexus_code_search/server.py` | Profile registry, filtering, token measurement, and MCP wiring |
| `extensions/nexus-code-search/src/nexus_code_search/contextmap/tokens.py` | Stable offline estimate entry point |
| `extensions/nexus-code-search/tests/test_tool_profiles.py` | Profile, cost, drift, config, and transport regressions |
| `extensions/nexus-code-search/README.md` | Selection guidance, measured costs, live tool count, skill cross-links |
| `extensions/nexus-code-search/pyproject.toml` | Complete dependency-ceiling rationales |
| `AGENTS.md` | Dependency upper-bound convention |
| `docs/todos.md` | v3.19.0 code-intelligence progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Live tool-count reconciliation and Phase 1 completion |
| `docs/v3/v3.19/known-gaps.md` | In-progress zero-gap v3.19.0 ledger |
| `docs/v3/v3.19/docs-cleanup-report.md` | Audit-mode disposition report |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-1-tool-profiles.md` | This history |

## 7. Next Step

Phase 2 adds the advisory-by-default search-routing guard with Bash and PowerShell siblings, registration, disable controls, matcher precision, and fail-open tests. It must preserve legitimate native-search cases while steering broad repository discovery to the local index.
