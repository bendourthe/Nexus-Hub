# Plan -- Adopt headroom context-compression engine (reverse-engineer-first)

**Project**: Nexus-Hub
**Version**: v3.2.0
**Slug**: adoption-headroom
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-04
**Goal**: Build an internal `extensions/nexus-context-compressor` that ports headroom's deterministic, local-first compression strategies plus reversible retrieval, retire the external `rtk` dependency, and ship an optional ML token-dropper -- with zero new outbound calls, credentials, or third-party processors.

## Overview

This plan operationalizes the adoption candidates in [`../comparison-headroom.md`](../comparison-headroom.md) at full scope (P0-P3). headroom is an Apache-2.0 context-compression engine whose deep-dive (Section 9) confirmed it is local-first: no tool output, file content, RAG data, or prompt ever leaves the machine. Nexus-Hub today owns no compression *engine* -- only methodology skills (`context-compression`, `prompt-token-optimization`, etc.) and a dependency on the external `rtk` Rust binary (command-output-only, lossy, installed via `cargo install --git`). This plan rebuilds the high-value subset internally as a sibling of `nexus-code-search` / `nexus-skill-scanner`, reusing the established Python+Rust extension build and tree-sitter infrastructure.

**Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale.** There are no `skill-native` items to ship first (the engine is code, not LLM-native guidance), so Phase 1 begins the `re-full` core: the deterministic strategies and the reversible-retrieval store are the spine (Phases 1-5), the `re-partial` ML token-dropper is an optional default-off module (Phase 6), the methodology-skill cross-links close the loop (Phase 7), and the `drop-outright` items (telemetry beacon, proxy form, cross-agent memory) are excluded -- see the out-of-scope appendix.

This plan is single-source and forward-looking; it intentionally does NOT ingest the v2.4.0 / v3.0.0 general known-gaps backlog (those remain tracked for the next general version plan), so its scope stays bounded to the headroom comparison.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.2/constitution.md - skipping check. Recommend running /constitution to establish project principles.

This plan nonetheless aligns with the standing `AGENTS.md` MCP Registry Policy: every adopted component runs locally, introduces no outbound call (the optional ML module's one-time public weight download carries no user data and ships offline-capable), no credential, and no third-party data processor.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Foundation + SmartCrusher (re-full) | Scaffolded `nexus-context-compressor` package, installer-registered, with deterministic JSON-array dedup emitting CCR markers |
| 2 | CCR reversible store (re-full) | Local SQLite store + retrieval interface so compression is non-lossy (model can fetch dropped originals) |
| 3 | Remaining deterministic strategies (re-full) | CacheAligner, ContentRouter, and AST-aware CodeCompressor (reusing nexus-code-search tree-sitter) |
| 4 | Runtime integration + retire rtk (re-full) | PreToolUse hook + internal MCP compress/retrieve tool; external `rtk` recommendation superseded |
| 5 | Accuracy-regression harness (re-full) | Benchmark gate proving compression preserves answer quality before aggressive ratios ship |
| 6 | Optional ML token-dropper (re-partial) | Default-off ModernBERT importance scorer using public pre-trained ONNX weights, offline-capable |
| 7 | Methodology cross-links + docs (re-partial) | Existing context skills cross-link the engine; architecture writeup |

---

## Phase 1: Foundation + SmartCrusher (re-full)

**Goal**: Stand up the `extensions/nexus-context-compressor` package, register it in both installers, and ship the first deterministic strategy (JSON-array dedup) that emits CCR markers.
**Prerequisites**: None.
**Stability Gate**: `python -m nexus_context_compressor.smart_crusher` compresses a 100-item JSON array to <=15 representative items with CCR markers; package unit tests pass; `make validate` green; both installers reference the new package.

### Sub-tasks

#### 1.1 -- Scaffold the compressor package

- [x] T001 Scaffold `extensions/nexus-context-compressor/` (package, pyproject.toml, tests skeleton, README)

**Objective**: Create a stdlib-first Python package mirroring the layout of `extensions/nexus-skill-scanner`.

**Prompt**:
> Create a new internal extension at `extensions/nexus-context-compressor/`, modeled structurally on `extensions/nexus-skill-scanner/`. Include: a `pyproject.toml` (Python 3.10+, stdlib-first, `tiktoken` as the only required runtime dep, optional extras for `onnxruntime`/`tree-sitter`), a package directory `nexus_context_compressor/` with `__init__.py` exposing a top-level `compress(messages, model=...) -> CompressResult` entry point and a `transforms/` subpackage, a `tests/` directory, and a `README.md` describing the local-first, zero-outbound design. Do not implement strategies yet -- only the package skeleton, the `CompressResult` dataclass (compressed messages + metrics: tokens_before/after, ratio), and a no-op pipeline. Match the code style in `catalog/rules/python/`.

---

#### 1.2 -- Register the package in both installers

- [x] T002 Register `nexus-context-compressor` copy step in scripts/installer.sh and scripts/installer.ps1

**Objective**: Ensure the new extension distributes to all platforms per the AGENTS.md installer-aware rule.

**Prompt**:
> The `extensions/` folder is copied recursively by both installers, so the package tree auto-distributes. Confirm this by tracing `safe_folder_copy` / `Safe-Folder-Copy` in `scripts/installer.sh` and `scripts/installer.ps1`. If the package exposes a top-level entrypoint script under `scripts/` (e.g. a `compress_context.py` CLI), add an explicit-name copy step in BOTH installers modeled on the existing `generate_report.py` / `scan_skill_security.py` blocks, copying to `~/.nexus-hub/scripts/`. Do a dry-run install into a throwaway directory and confirm the package lands at the expected path on both layouts.

---

#### 1.3 -- Implement SmartCrusher (JSON-array dedup)

- [x] T003 Implement deterministic JSON-array compressor in extensions/nexus-context-compressor/nexus_context_compressor/transforms/smart_crusher.py

**Objective**: Port headroom's variance/uniqueness/change-point JSON-array dedup as pure local logic.

**Prompt**:
> Implement `transforms/smart_crusher.py`: given a JSON array of records, score each by variance, uniqueness, position, and change-points; keep high-value items (first ~30%, last ~15%, change-points) up to a configurable `max_items_after_crush` (default 15); drop low-variance duplicates and replace the dropped span with a CCR marker object `{"_ccr_dropped": "<<ccr:HASH N_rows>>"}`. Expose a `SmartCrusherConfig` dataclass (`min_items_to_analyze=5`, `max_items_after_crush=15`, `variance_threshold=2.0`). This is a Python-only port (no Rust required for v1); keep it deterministic and dependency-free. The hash in the CCR marker must be stable and reproducible (content hash, not random -- do not use `Math.random`/uuid). Reference behavior is documented in comparison-headroom.md Section 5a item 1.

---

#### 1.4 -- Testing and Stabilization

- [x] T004 Run and stabilize Phase 1 tests in extensions/nexus-context-compressor/tests/

**Objective**: Generate and run all Phase 1 tests. Iterate until stable.

**Prompt**:
> Generate comprehensive unit tests for the package scaffold and SmartCrusher: a 1000-identical-log-lines array compresses to <=3 + a CCR marker; a high-variance array is preserved; CCR marker hashes are stable across runs; `CompressResult` metrics are correct. Run the tests, fix all failures, run `make validate`, and iterate until everything passes. Do not advance to Phase 2 until verified. After all tests pass, run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: CCR reversible store (re-full)

**Goal**: Make compression non-lossy by storing dropped originals locally and exposing a retrieval interface keyed by the CCR marker hash.
**Prerequisites**: Phase 1 (SmartCrusher emits CCR markers).
**Stability Gate**: a compressed payload's CCR marker can be resolved back to the original dropped records via the retrieval interface; store is local SQLite; no outbound call.

### Sub-tasks

#### 2.1 -- Implement the CCR store

- [x] T005 Implement local CCR store in extensions/nexus-context-compressor/nexus_context_compressor/ccr/store.py

**Objective**: Persist dropped content keyed by content hash in a local SQLite database.

**Prompt**:
> Implement `ccr/store.py`: a SQLite-backed store (default path under the project or `~/.nexus-hub/cache/`) mapping each CCR marker hash to the original dropped records (JSON-serialized). Provide `put(hash, original) -> None` and `get(hash) -> original | None`. SQLite only; no Redis/Qdrant. Wire SmartCrusher (T003) to call `put` when it drops a span. Zero outbound calls. Document the store location and a size/TTL eviction note.

---

#### 2.2 -- Implement the retrieval interface

- [x] T006 Implement CCR retrieval interface in extensions/nexus-context-compressor/nexus_context_compressor/ccr/retrieve.py

**Objective**: Let a consumer (later, an MCP tool / hook) resolve a CCR marker back to originals on demand.

**Prompt**:
> Implement `ccr/retrieve.py`: a `retrieve(marker_or_hash) -> original` function that parses a `<<ccr:HASH N_rows>>` marker, looks the hash up in the store (T005), and returns the original records. Handle missing-hash gracefully (return a clear "expired/not-found" sentinel, never raise unhandled). This is the function the Phase 4 MCP `retrieve` tool and PreToolUse hook will call.

---

#### 2.3 -- Testing and Stabilization

- [x] T007 Run and stabilize Phase 2 tests in extensions/nexus-context-compressor/tests/

**Objective**: Generate and run all Phase 2 tests. Iterate until stable.

**Prompt**:
> Generate tests for the CCR round-trip: compress an array -> persist dropped span -> resolve the marker back to the exact originals; missing-hash returns the not-found sentinel; the store survives process restart (re-open the SQLite file). Run, fix, `make validate`, iterate until green. After passing, run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Remaining deterministic strategies (re-full)

**Goal**: Add the three remaining deterministic strategies -- CacheAligner, ContentRouter, and AST-aware CodeCompressor -- and route content to the right compressor.
**Prerequisites**: Phase 1 (package + pipeline), Phase 2 (CCR store for any strategy that drops data).
**Stability Gate**: ContentRouter correctly classifies and dispatches JSON / code / log / text payloads; CodeCompressor preserves imports+signatures while trimming bodies; CacheAligner stabilizes a system-prompt prefix; all local, no outbound.

### Sub-tasks

#### 3.1 -- Implement CacheAligner

- [x] T008 [P] Implement KV-cache prefix stabilizer in extensions/nexus-context-compressor/nexus_context_compressor/transforms/cache_aligner.py

**Objective**: Move dynamic tail content out of the stable system-prompt prefix and normalize whitespace so provider KV caches hit.

**Prompt**:
> Implement `transforms/cache_aligner.py`: detect dynamic content in a system message (dates, UUIDs, tokens, timestamps, hashes, version numbers) via regex; move the dynamic tail to the end of the message; normalize whitespace; leave the stable prefix intact. Pure local regex (optional spaCy NER behind an extra, default off). No outbound. Reference: comparison-headroom.md Section 5a item 2.

---

#### 3.2 -- Implement ContentRouter

- [x] T009 [P] Implement content-type router in extensions/nexus-context-compressor/nexus_context_compressor/transforms/content_router.py

**Objective**: Detect content type and dispatch each segment to its optimal compressor.

**Prompt**:
> Implement `transforms/content_router.py`: classify a message body as JSON / code / search-output / log / plain-text using local heuristics (no magika dependency required for v1; a small pattern-based classifier is fine). Route JSON to SmartCrusher, code to CodeCompressor (T010), and leave text untouched for now (the ML dropper in Phase 6 is optional). Split mixed content, route segments independently, reassemble. No outbound.

---

#### 3.3 -- Implement CodeCompressor (reuse tree-sitter)

- [x] T010 Implement AST-aware code compressor in extensions/nexus-context-compressor/nexus_context_compressor/transforms/code_compressor.py

**Objective**: Trim function/method bodies while preserving imports, signatures, decorators, and class structure -- reusing the existing nexus-code-search tree-sitter infrastructure.

**Prompt**:
> Implement `transforms/code_compressor.py`: use the tree-sitter grammars already vendored by `extensions/nexus-code-search` to parse code, keep imports / function+method signatures / decorators / type annotations / class structure, and replace bodies with an elision marker (CCR marker when the body is large enough to be worth retrieving). Support the languages nexus-code-search already covers; fall back to a regex elision for unsupported languages. Reuse, do not re-vendor, the tree-sitter extractors. No outbound.

---

#### 3.4 -- Testing and Stabilization

- [x] T011 Run and stabilize Phase 3 tests in extensions/nexus-context-compressor/tests/

**Objective**: Generate and run all Phase 3 tests. Iterate until stable.

**Prompt**:
> Generate tests: ContentRouter classifies each sample type correctly and dispatches; CodeCompressor preserves signatures+imports for at least Python and TypeScript and elides bodies; CacheAligner produces a byte-identical stable prefix across two inputs differing only in a trailing date. Run, fix, `make validate`, iterate. After passing, run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 4

---

## Phase 4: Runtime integration + retire rtk (re-full)

**Goal**: Wire the compressor into a live agent session via a PreToolUse hook and an internal MCP compress/retrieve tool, then supersede the external `rtk` recommendation.
**Prerequisites**: Phases 1-3 (the engine), Phase 2 (retrieval).
**Stability Gate**: a Bash tool output is compressed before entering context via the hook; an agent can call the MCP `retrieve` tool to resolve a CCR marker; the rtk guide points to the internal engine with a migration note; engine reaches at least rtk's command-output parity.

### Sub-tasks

#### 4.1 -- PreToolUse compression hook

- [x] T012 Add PreToolUse compression hook in catalog/hooks/ (+ settings.json registration)

**Objective**: Compress tool output before it is written into the context window, at the same hook point rtk uses.

**Prompt**:
> Add a PreToolUse hook in `catalog/hooks/` that pipes tool output through `nexus-context-compressor.compress` before it reaches context. Register it in `catalog/hooks/settings.json`. Follow the bash safety rules in `catalog/rules/bash/` and the hook test pattern in `catalog/hooks/tests/`. Document the Windows constraint (hooks need a Unix shell; Windows uses CLAUDE.md-injected instructions, exactly as the rtk guide documents) and ship the Windows path. Write a pytest test for the hook per `make test`.

---

#### 4.2 -- Internal MCP compress/retrieve tool

- [x] T013 Add internal MCP server exposing compress + retrieve in extensions/nexus-context-compressor/

**Objective**: Expose `compress` and `retrieve` as local MCP tools, modeled on headroom's MCP server and Nexus-Hub's existing internal MCPs.

**Prompt**:
> Add a local MCP server to the package exposing `context_compress` (compress a payload) and `context_retrieve` (resolve a CCR marker via T006). Model the server on the existing `extensions/nexus-skill-server` / `nexus-web-fetch` internal MCPs (local-only, zero outbound). Add a registry entry to `catalog/mcp-configs/mcp-servers.json` classified Tier 1 (local-only) per the MCP Registry Policy, with the five-question `_comment` audit answered (runs locally, no outbound, no key, no data leaves machine, no commercial relationship). Add the matrix row in `docs/policy/mcp-reverse-engineering-matrix.md`.

---

#### 4.3 -- Supersede the external rtk recommendation

- [x] T014 Supersede external rtk with the internal engine in guides/RTK_CONTEXT_COMPRESSION.md

**Objective**: Convert the "trust a third-party GitHub binary" posture into the owned, audited internal compressor, with a migration note.

**Prompt**:
> Update `guides/RTK_CONTEXT_COMPRESSION.md` (and any AGENTS.md / installer references) to recommend the internal `nexus-context-compressor` instead of `cargo install --git rtk`. Keep a clearly-labeled migration section for existing rtk users (how to remove the rtk hook and switch). Only make this change once T012/T013 reach at least rtk's command-output compression parity. Preserve the cross-platform output-minimization guidance for non-Claude platforms.

---

#### 4.4 -- Testing and Stabilization

- [x] T015 Run and stabilize Phase 4 tests via make test and an installer dry-run

**Objective**: Generate and run all Phase 4 tests. Iterate until stable.

**Prompt**:
> Run `make test` (hook + MCP tests), `make validate` (registry + matrix integrity), and `make lint`. Do an installer dry-run into a throwaway directory and confirm the hook, MCP config, and package land correctly on both bash and PowerShell installers. Fix all failures and iterate. After passing, run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5

---

## Phase 5: Accuracy-regression harness (re-full)

**Goal**: Prove compression preserves answer quality so aggressive ratios can ship safely, and gate it in CI.
**Prerequisites**: Phases 1-4 (the engine exists end-to-end).
**Stability Gate**: a benchmark suite runs locally and reports compression ratio + accuracy delta; CI fails if accuracy regresses beyond a threshold.

### Sub-tasks

#### 5.1 -- Build the accuracy-regression harness

- [x] T016 Build compression accuracy-regression harness in extensions/nexus-context-compressor/evals/

**Objective**: Port headroom's benchmark-gate concept (compression ratio vs. accuracy delta).

**Prompt**:
> Build an `evals/` harness that measures, per strategy and end-to-end, the compression ratio and an accuracy proxy on a small fixed local dataset (no live LLM call required in CI -- use deterministic structural-fidelity checks: CCR round-trip completeness, signature-preservation rate for code, retained-vs-dropped record correctness). Emit a JSON/Markdown report. Model the methodology on comparison-headroom.md Section 7 and headroom's `evals/`. Keep it offline and deterministic.

---

#### 5.2 -- Wire the CI accuracy gate

- [x] T017 Wire compression accuracy gate into the CI validate job and make validate

**Objective**: Fail CI if a compression change degrades fidelity below threshold.

**Prompt**:
> Add a CI step (and a `make` target, e.g. `make compress-eval`) that runs the T016 harness and fails on a fidelity regression beyond a documented threshold. Wire it into the existing `validate` CI job alongside the skill-security gate. Document the threshold and how to update a baseline intentionally.

---

#### 5.3 -- Testing and Stabilization

- [x] T018 Run and stabilize Phase 5 tests and the eval gate

**Objective**: Generate and run all Phase 5 tests. Iterate until stable.

**Prompt**:
> Run the eval harness and the CI gate locally; confirm a deliberately-broken compressor change is caught by the gate (inject a fault in a test branch, confirm red, revert). Run `make validate`. Fix and iterate. After passing, run `/generate-session-history` to document Phase 5.

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 6

---

## Phase 6: Optional ML token-dropper (re-partial)

**Goal**: Add a default-off ML token-importance dropper using public pre-trained ONNX weights, offline-capable, with zero user data sent.
**Prerequisites**: Phases 1-5 (deterministic engine + eval gate to guard quality).
**Stability Gate**: the module is default-off; when enabled it loads local ONNX weights and drops low-importance tokens; with the dependency/weights absent it degrades gracefully with an install hint; the eval gate confirms no accuracy regression at the default ratio.

### Sub-tasks

#### 6.1 -- Implement the optional ML token-dropper

- [x] T019 Implement default-off ML token-dropper in extensions/nexus-context-compressor/nexus_context_compressor/transforms/ml_token_dropper.py

**Objective**: Port the Kompress importance-scoring drop as an optional module using public pre-trained weights (do NOT retrain).

**Prompt**:
> Implement `transforms/ml_token_dropper.py` as a DEFAULT-OFF optional strategy: load the public pre-trained ModernBERT importance-scorer ONNX weights locally (via the package's optional `onnxruntime` extra), score tokens, drop low-importance tokens up to a target ratio, and reconstruct text. Mirror the v3.0.0 OSV.dev offline-first precedent: ship/cache weights so the module works air-gapped, send NO user data anywhere, and degrade gracefully with a clear install hint when `onnxruntime` or the weights are absent. The one-time public weight download carries no user data (document this explicitly). Gate it behind an explicit opt-in config flag; the deterministic strategies remain the default pipeline.

---

#### 6.2 -- Testing and Stabilization

- [x] T020 Run and stabilize Phase 6 tests in extensions/nexus-context-compressor/tests/

**Objective**: Generate and run all Phase 6 tests. Iterate until stable.

**Prompt**:
> Generate tests covering: module is off by default; enabling it drops low-importance tokens at the target ratio; absent-dependency path returns the original text plus an install hint (no crash); no network call occurs in CI (mock/skip the weight fetch). Re-run the Phase 5 accuracy gate with the module enabled. Run `make validate`. Fix and iterate. After passing, run `/generate-session-history` to document Phase 6.

---

### Phase 6 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 7

---

## Phase 7: Methodology cross-links + docs (re-partial)

**Goal**: Connect the new engine to the existing methodology skills and document the architecture.
**Prerequisites**: Phases 1-6 (engine complete).
**Stability Gate**: the relevant context skills cross-link the engine as their programmatic counterpart; an architecture doc explains the pipeline + CCR; `make validate` green.

### Sub-tasks

#### 7.1 -- Cross-link methodology skills to the engine

- [x] T021 Cross-link the engine from catalog/skills/orchestration/context-compression/SKILL.md and prompt-token-optimization/SKILL.md

**Objective**: Make the methodology skills point to the programmatic engine without duplicating it.

**Prompt**:
> Update `catalog/skills/orchestration/context-compression/SKILL.md`, `catalog/skills/orchestration/prompt-token-optimization/SKILL.md`, and `catalog/skills/developer-experience/context-optimization/SKILL.md` to cross-link `nexus-context-compressor` as the programmatic counterpart to their human-facing guidance (a "when the agent should reach for the engine" note + a `[[ ]]` style cross-link). Do not duplicate engine internals into the skill bodies. Keep within the 500-line skill norm.

---

#### 7.2 -- Architecture documentation

- [x] T022 Write the compressor architecture writeup in extensions/nexus-context-compressor/README.md (and docs/v3/v3.2/)

**Objective**: Document the pipeline, CCR reversibility, the local-first/zero-outbound posture, and the rtk migration.

**Prompt**:
> Expand the package README and add a short architecture note under `docs/v3/v3.2/` covering: the ContentRouter -> strategy pipeline, CCR reversible retrieval, the local-first/zero-outbound guarantee, the optional ML module's offline-first design, and the rtk migration path. Follow `catalog/style-guides/markdown.md`.

---

#### 7.3 -- Final validation

- [x] T023 Run full validation suite and installer dry-run

**Objective**: Confirm the entire adoption is green end-to-end.

**Prompt**:
> Run `make validate`, `make lint`, `make test`, and the compression eval gate. Do a full installer dry-run on both bash and PowerShell into throwaway directories. Confirm the package, hook, MCP config, and guide changes all land correctly. Add a CHANGELOG `## [Unreleased]` entry summarizing the internal context-compressor adoption and rtk retirement. After passing, run `/generate-session-history` to document Phase 7.

---

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | -- | All Constitution Check items are N/A (no constitution file); no violations to justify. |

---

### Phase 7 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Adoption complete; CHANGELOG updated

---

## Items explicitly NOT adopted (security / policy reasons)

Per the MCP Registry Policy decision tree (Section 9.3 of the source comparison), the following are `drop-outright` or declined and DO NOT appear as phases:

- **N1 -- Telemetry beacon** (`headroom/telemetry/beacon.py`). Outbound anonymous aggregate metrics to a third-party Supabase endpoint. Dropped under the policy preference for zero new outbound / zero new third-party processors; trivially omitted in this clean-room port.
- **N2 -- FastAPI proxy form** (`headroom/proxy/`). Intercepts and forwards provider API traffic and holds the user's API keys. Declined in favor of the in-process library + PreToolUse-hook integration (Phase 4), which delivers the same benefit without handling credentials or proxying traffic.
- **N3 -- Cross-agent memory subsystem** (`headroom/memory/`, Qdrant / Neo4j / sentence-transformers). Out of scope for a context compressor and pulls heavy optional dependencies. Deferred indefinitely.
