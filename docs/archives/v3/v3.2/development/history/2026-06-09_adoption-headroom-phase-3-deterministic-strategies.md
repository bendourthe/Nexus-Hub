# Session History -- v3.2.0 adoption-headroom Phase 3: Remaining deterministic strategies

**Date**: 2026-06-09
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 3 of 7 -- Remaining deterministic strategies (re-full)
**Branch**: `feat/adoption-headroom` (continuing from Phase 2)
**Outcome**: complete; all four sub-tasks (T008-T011) closed, all quality gates green (GO).

## Goal

Add the three remaining deterministic strategies on top of the Phase 1-2 spine (SmartCrusher + reversible CCR store): **CacheAligner** (KV-cache prefix stabilization), **ContentRouter** (content-type classify + dispatch), and the AST-aware **CodeCompressor** that reuses the `nexus-code-search` tree-sitter extractors. All local, deterministic, zero outbound; any strategy that drops data stays reversible through the Phase 2 CCR store via the same `store=` injection seam.

## Branch correction (pre-work)

The session opened on `feat/usage-monitor-fable` (an unrelated Fable-5 usage-monitor branch). Only stale `.pyc` artifacts of the compressor were present on disk -- no tracked source -- confirming Phases 1-2 lived elsewhere. `git ls-tree` showed the full Phase 1-2 source on `feat/adoption-headroom` (0 behind / 2 ahead of `develop`, in sync with its remote). Switched to `feat/adoption-headroom` (clean tree, safe) before any Phase 3 work, so the headroom feature stays isolated on its own branch per the project's develop+main model.

## Subtasks completed

1. **T008 -- CacheAligner** (`transforms/cache_aligner.py`). Regex-detects volatile tokens (ISO dates/date-times, clock times, UUIDs, long-hex hashes/tokens, semantic versions, epoch timestamps), moves every line carrying one to a dynamic tail, rstrips trailing whitespace, and collapses blank runs -- leaving a **byte-identical stable prefix** that two otherwise-identical prompts share for a provider KV-cache hit. `AlignResult` exposes `stable_prefix` / `dynamic_tail` / `moved_lines` separately. An optional spaCy NER pass sits behind a default-off `use_ner` flag and degrades silently to regex-only when spaCy (or its model) is absent. It compresses nothing (reorders only), so there is no CCR store and nothing to retrieve.
2. **T009 -- ContentRouter** (`transforms/content_router.py`). `classify(text)` distinguishes JSON-array / JSON-object / code / log / plain-text with local heuristics (JSON parse first, then line-oriented log prefixes, then strong code signals, else text). `route()` splits mixed content on fenced code blocks, dispatches JSON arrays to SmartCrusher and code (fenced or sniffed) to CodeCompressor, leaves log/text untouched (per the plan -- free-text dropping is the optional Phase 6 ML module), and reassembles -- preserving prose between and around fences exactly. The shared CCR `store` is threaded down to both strategies.
3. **T010 -- CodeCompressor** (`transforms/code_compressor.py`). **Reuses** `nexus-code-search`'s `parse_file` (tree-sitter) to find innermost function/method node line ranges, then keeps every line and elides only the body interior -- so imports, decorators (which sit above the node), signatures, type annotations, and class structure survive automatically. Bodies >= `ccr_min_lines` become reversible `<<ccr:HASH N_rows>>` markers (persisted to the store); smaller bodies get a plain non-retrievable note. A dependency-free regex/indent/brace fallback runs when the AST infra is absent or the language is unsupported (e.g. `.js`/`.jsx`). Extended the marker codec with `find_marker` / `find_all_markers` for markers embedded in code comments.
4. **T011 -- tests + stabilization.** 62 new tests (130 total) across three new files (CacheAligner, ContentRouter, CodeCompressor) plus embedded-marker tests added to the existing marker-codec file. All green; 92% package coverage (`ccr/` still 100%; the three new transforms 88-97%). Registered the package in the `make test` target so its suite runs alongside the other extensions. `make validate` emulated green; all four sibling extension suites still pass (no regressions).

## Key decisions

- **Reuse-not-re-vendor via a lazy, cached AST loader.** `code_compressor._load_ast()` imports `nexus_code_search.extraction.parse_file` lazily; on `ImportError` it discovers the sibling `extensions/nexus-code-search/src` on disk and retries, and on any failure degrades to the regex fallback. This honors the plan's "reuse, do not re-vendor the tree-sitter extractors" while keeping `nexus-context-compressor` self-contained (no hard dependency on the sibling) -- the same offline-first / graceful-degradation posture as the Phase 1 `tokens.py` tiktoken fallback.
- **"Elide only the body interior" instead of enumerating what to keep.** Tree-sitter function nodes exclude their decorators (those precede `start_line`), and imports/class headers/signatures lie outside any body. So copying every line and removing only innermost function/method body interiors preserves all structure with no explicit keep-list -- there is no "did I remember to keep X?" failure mode. Confirmed empirically against `parse_file` output for Python and TypeScript before coding.
- **Markers embedded in text need a new codec entry.** SmartCrusher's markers are standalone JSON objects (`parse_marker` is anchored). CodeCompressor leaves a marker inside a language comment on a line of code, so the codec gained `find_marker` / `find_all_markers` (unanchored search) built from the same shared inner grammar -- keeping `ccr/marker.py` the single source of truth and the Phase 4 retrieve tool able to resolve code markers.
- **ContentRouter splits on fences + whole-chunk classification, not paragraph-level.** Splitting prose into paragraphs to hunt embedded JSON risks cutting non-code text. The high-value shapes (a tool dump that *is* a JSON array; fenced ` ```json ` / code blocks) are handled exactly; a JSON array buried mid-paragraph is left untouched (DF-v32hr-5). Routing an over-eager code classification is safe because CodeCompressor returns its input unchanged when it finds no function bodies -- the downstream transform is its own backstop.
- **`compress()` stays the Phase 1 no-op.** The three strategies are standalone, individually-callable transforms. Wiring ContentRouter (and CacheAligner for system prompts) into the `compress()` entry point and into the live PreToolUse hook + internal MCP is the explicit job of Phase 4 (runtime integration), so it is intentionally not done here (DF-v32hr-7).
- **Dead-config / dead-code hygiene.** Removed two `RouterConfig` fields and a `_NerSupport` dataclass that were introduced and then not consumed, keeping every line traceable to the task.

## Test results

- Package suite: **130 passed** (`python -m pytest -q`). 68 prior (Phase 1-2) + 62 new (CodeCompressor 28, ContentRouter 22, CacheAligner 14, embedded-marker 8 added to the codec file -- minus overlap counted once). **92% line coverage** (`ccr/` 100%, cache_aligner 97%, content_router 91%, code_compressor 88%).
- Stability gate (Phase 3): ContentRouter classifies each sample type and dispatches (arrays -> SmartCrusher, code -> CodeCompressor); CodeCompressor preserves imports + signatures + decorators + class structure while eliding bodies for Python and TypeScript (and round-trips an elided body back through the CCR store); CacheAligner produces a byte-identical `stable_prefix` for two prompts differing only in a trailing date (and a trailing UUID). All local, deterministic, no outbound.
- No regressions: sibling extension suites all green -- skill-server 43, code-search 201 (+1 skipped), web-fetch 29, skill-scanner 87.
- `make validate` emulated (each validator invoked directly; `make` unavailable on host, WN-v32-2): catalog JSON parses (skills.json unchanged -- this phase adds extension code, not a skill), `validate_no_personal_paths.py` / `validate_unicode_safety.py` / `check_version_sync.py` all clean, **zero findings in the new files** (the unicode WARNs are pre-existing legacy templates).
- `make lint` (ShellCheck): **N/A** -- Python-only, no shell surface.

## CI/CD edits

- `Makefile` `test` target gained `@cd extensions/nexus-context-compressor && python -m pytest -q`, so the compressor suite now runs as part of `make test` alongside the other extensions (Phases 1-2 had run it only directly). The package itself auto-distributes via the Phase 1 installer copy + editable-install blocks (no new top-level `scripts/<name>.py`, so no copy-by-name installer step). No new GitHub Actions workflow or env var.

## Deviations

- None that change plan scope. The AST-reuse-with-regex-fallback design is the faithful reading of T010 ("reuse the tree-sitter extractors ... fall back to a regex elision for unsupported languages") extended with graceful degradation when the sibling/tree-sitter is absent -- consistent with the package's stdlib-first ethos. The `find_marker` codec addition is the maintainable way to let code-embedded markers resolve through the same single-source grammar.

## Troubleshooting / environment notes

- Opened on the wrong branch (`feat/usage-monitor-fable`); detected via stale `.pyc` with no tracked source and corrected by switching to `feat/adoption-headroom` (see Branch correction above).
- A pytest fixture cleared an `lru_cache` on a monkeypatched lambda during teardown (`AttributeError: 'function' object has no attribute 'cache_clear'`); fixed by capturing and clearing the original cached function instead of the patch.
- Shell quote-escaping for an inline `python -c` smoke test was error-prone on PowerShell/Bash; switched to a throwaway scratch file (removed after) and then to the real test suite.

## Known gaps

See [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md). **4 new DF this phase** (DF-v32hr-5 ContentRouter prose-embedded arrays not isolated; DF-v32hr-6 regex fallback best-effort, multi-line brace signatures + string/comment-unaware depth; DF-v32hr-7 `compress()` runtime wiring is Phase 4; DF-v32hr-8 spaCy NER default-off / regex epoch-version over-match), 0 resolved; 11 open total (8 DF + 3 carried-over teach WN). DF-v32hr-1 and DF-v32hr-3 updated to record that CacheAligner shipped and ContentRouter was kept minimal (error-preservation re-deferred to Phase 5).

## Next steps

- **Phase 4 (runtime integration + retire rtk)**: a PreToolUse compression hook, an internal MCP `context_compress` / `context_retrieve` tool (Tier-1 local-only registry entry + matrix row), wiring `compress()` through ContentRouter, and superseding the external `rtk` recommendation once command-output parity is reached.
- **Commit + push**: commit Phase 3 on `feat/adoption-headroom` and push the branch.
