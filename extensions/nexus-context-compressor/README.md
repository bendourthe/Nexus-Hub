# nexus-context-compressor

Local-first context-compression engine for Nexus-Hub. An owned, audited replacement for the external `rtk` binary: it routes message content to deterministic strategies, makes every drop reversible through a local content-hashed CCR store, and offers an optional default-off ML token-dropper.

The engine is local-first and self-contained: standard-library strategies, a single required dependency (`tiktoken`, with an offline stdlib fallback), zero outbound calls, no bundled LLM client, and no API key.

## Why it exists

Nexus-Hub today owns no compression engine, only methodology skills (`context-compression`, `prompt-token-optimization`) and a dependency on the external `rtk` Rust binary (command-output-only, lossy, installed via `cargo install --git`). This package rebuilds the high-value subset internally as a sibling of `nexus-code-search` / `nexus-skill-scanner`, so Nexus-Hub controls and audits the code that touches a user's context window.

## Design

- **Local-first, zero-outbound.** The deterministic strategies are pure standard library. The only dependency, `tiktoken`, is used for accurate token accounting and degrades to a deterministic stdlib estimate when unavailable, so the package never *requires* a network call. tiktoken's one-time vocab fetch is a static asset carrying no user data.
- **Reversible compression (CCR).** When a strategy drops content, it leaves a `<<ccr:HASH N_rows>>` marker and persists the originals in a local content-hashed store, so a consumer can fetch the dropped data back on demand. Compression is therefore non-lossy.
- **Content-routed strategies.** A router classifies each segment (JSON, code, log, text) and dispatches it to the optimal compressor.

### Producer encoding versus consumer compression

`nexus-code-search` may encode its own structured MCP responses with the schema-aware Nexus Compact Wire format before they reach this engine. That producer-side codec removes repeated table keys and uses the exact `NEXUS-CW/1` first-line marker. This package remains consumer-side and content-routed: it accepts arbitrary tool output, classifies it, and uses reversible CCR markers for any dropped content.

The paths compose in that order: producer encoding first, consumer compression second. `compress_output(text)` recognizes the exact compact-wire marker and returns those bytes unchanged with identity metrics, preventing double compression or delimiter corruption. CCR marker strings inside a compact response remain ordinary typed values and round-trip through the producer decoder unchanged. The format and JSON retry contract are documented in the [`nexus-code-search` wire-format specification](../nexus-code-search/docs/wire-format.md).

## Architecture

### The pipeline

Two public entry points feed one router. `compress_output(text)` is the single-blob runtime seam (what the PreToolUse hook's CLI and the MCP `context_compress` tool call on raw tool output); `compress(messages)` routes each message's `content` in a `[{role, content}]` list. Both delegate to `ContentRouter.route`, which is the heart of the engine:

```
compress_output(text)        compress(messages)
        |                            |
        +------------ route(segment) -------------+
                          |
        classify each segment (local heuristics)
                          |
   +----------+-----------+-----------+-----------+
   | JSON array|   code    |   log     |   text    |
   |  -> Smart |  -> Code   | (pass     | (pass     |
   |   Crusher | Compressor | through)  | through)* |
   +----+------+-----+------+-----------+-----------+
        |            |
        |            | (bodies elided; imports/signatures kept)
        v            v
     drops a span?  yes -> persist originals + emit <<ccr:HASH N_rows>> marker
                          |
                    CCR store (local SQLite, content-addressed)
                          ^
                          | retrieve(marker) on demand
              context_retrieve / CLI `retrieve`
```

`*` Free text is passed through unchanged on the default path. The optional ML token-dropper (below) is the only thing that compresses prose, and it is off by default and not wired into `route`.

`CacheAligner` is a fourth deterministic strategy, but it operates on a *system prompt* (stabilizing the KV-cache prefix), not on routed tool output, so it is a standalone, individually-callable transform rather than a `route` branch (see DF-v32hr-9).

### Module map

| Module | Role |
|---|---|
| `__init__.py` | Public API: `compress`, `compress_output`, `route`, `CompressResult` |
| `transforms/content_router.py` | Classify a blob and dispatch each segment to the right strategy |
| `transforms/smart_crusher.py` | JSON-array dedup: keep informative records, collapse low-variance runs |
| `transforms/code_compressor.py` | AST-aware body elision, reusing the `nexus-code-search` tree-sitter extractors |
| `transforms/cache_aligner.py` | KV-cache prefix stabilizer (system prompts; standalone) |
| `transforms/ml_token_dropper.py` | Optional, default-off ML free-text dropper (`[ml]` extra) |
| `ccr/marker.py` | Single source of truth for the `<<ccr:HASH N_rows>>` grammar |
| `ccr/store.py` | Local SQLite store: content-addressed `put`, oldest-first `prune` |
| `ccr/retrieve.py` | Resolve a marker/hash back to originals, or a `NOT_FOUND` sentinel |
| `tokens.py` | Token accounting (`tiktoken` with an offline stdlib fallback) |
| `cli.py` / `__main__.py` | `compress` / `retrieve` / `serve` subcommands |
| `server.py` | Internal MCP server (`context_compress` + `context_retrieve`, `[mcp]` extra) |
| `evals/` | Accuracy-regression harness + committed baseline (the CI fidelity gate) |

### Reversible compression (CCR)

The engine's defining invariant is that **every drop is reversible**. When a strategy removes content it does two things atomically: it persists the original records in the CCR store keyed by a stable SHA-256 content hash, and it leaves a `<<ccr:HASH N_rows>>` marker in the output. A consumer that later needs the dropped data calls `retrieve(marker)` (via the `context_retrieve` MCP tool or the `retrieve` CLI subcommand) and gets the exact originals back, or a `NOT_FOUND` sentinel if the span was evicted. Compression therefore never destroys information; it defers it. The marker grammar lives in exactly one place (`ccr/marker.py`) so the producer and consumer can never drift.

The store is a single local SQLite file (default `~/.nexus-hub/cache/ccr-store.db`), content-addressed and idempotent, with WAL for concurrent hook/MCP access and an oldest-first `prune` eviction primitive. Auto-eviction scheduling is deferred (DF-v32hr-4); a pruned span simply resolves to `NOT_FOUND`, which consumers already handle.

### Local-first, zero-outbound

Every default-path strategy is pure standard library. The only required dependency, `tiktoken`, is used for accurate token accounting and degrades to a deterministic stdlib estimate when absent, so the package never *requires* a network call. The CCR store is a local file. No command output, file content, or prompt is ever routed to a third party, and there is no bundled LLM client and no API key. This is the whole point of the engine: it replaces a "trust an unaudited external binary that sees every command's output" posture with owned, in-repo, audited code.

### The optional ML token-dropper (offline-first)

`transforms/ml_token_dropper.py` is the one strategy that compresses free text, and it is deliberately fenced off: **default-off, opt-in, lossy, and not wired into `route`.** When enabled (the `[ml]` extra plus pre-placed public ModernBERT ONNX weights), it scores each whitespace word for importance and keeps the top `target_ratio`. It is offline-first to the strongest degree -- it only *loads* pre-placed local weights (like `tiktoken`'s vocab or the v3.0.0 OSV.dev database), never downloads them, and sends no user data anywhere. Absent dependencies, absent weights, or a failing scorer all degrade to returning the original text plus a precise install hint, never a crash and never a network fetch. Given a CCR store it is reversible like the deterministic strategies; with no store it is a pure lossy preview.

### Migrating from rtk

This engine supersedes the external `rtk` Rust binary the project previously recommended. Existing rtk users remove the rtk PreToolUse hook (or the Windows `CLAUDE.md` instruction block), optionally `cargo uninstall rtk`, and enable the internal hook with `export NEXUS_CONTEXT_COMPRESS=1`. Do not run both at once. The full migration steps, platform matrix, and trust rationale are in [`guides/reference/RTK_CONTEXT_COMPRESSION.md`](../../guides/reference/RTK_CONTEXT_COMPRESSION.md).

### Semantic reformatters (named short list)

`reformatters.py` parse-and-restructures a handful of high-frequency command outputs before the content router runs: `git status`, pytest/vitest/jest failures-only, and ruff/eslint/tsc diagnostics grouped by file. Each handler has a fixture test that requires at least 60% token reduction. This is not parity with a dedicated ~60-handler command-output compressor; uncovered commands still pass through the existing JSON/code router or leave the text unchanged. See known-gaps **DF-3**.

Command rewrite is a separate PreToolUse decision (`rewrite.py`, `catalog/hooks/rewrite-command.sh`): exit 0 allow / 1 passthrough / 2 deny / 3 ask. The default when a rewrite exists is 3 (ask), never 0 (auto-allow). Host deny beats ask beats allow. A compound command (`&&` `||` `;` `|`) is allowed only when every segment independently matches allow.

### Bring-your-own filters (SHA-256 trust store)

Project file `.nexus-hub/compressor-filters.json`, then `~/.nexus-hub/compressor-filters.json`, then built-in (none), then passthrough. An on-disk file is applied only after `python -m nexus_context_compressor trust <file>` records its SHA-256. Editing the file changes the hash, so compress skips it until trusted again. `untrust` removes the pin. `verify` runs inline `tests[]` (`name` / `input` / `expected`) even on an untrusted file. This is consent plus tamper-evidence, not a sandbox.

### Recoverable truncation

`compress --max-lines N` / `--max-bytes N` (and `compress_output(..., max_lines=, max_bytes=)`) tee the full blob to a spool file, keep a prefix, and print a recovery pointer (`tail -n +LINE FILE`). If the spool cannot be written, the original text is left intact. Nothing is silently unrecoverable.

### Passthrough log (session mining)

When compression does not shrink the blob, one JSON line is appended to `~/.nexus-hub/compressor-passthrough.jsonl` (or a sibling of `NEXUS_CCR_STORE_PATH`). `session-query` and `continuous-learning` mine that log for unrealized savings and repeated CLI mistakes. Local, append-only, no outbound I/O.

## Status

Built incrementally across the v3.2.0 `adoption-headroom` plan:

- **Phase 1** - package skeleton, `CompressResult` metrics, no-op pipeline, and the first deterministic strategy (SmartCrusher JSON-array dedup) emitting CCR markers.
- **Phase 2** - the reversible CCR store: a local SQLite store keyed by each span's content hash (`ccr/store.py`), a shared marker codec (`ccr/marker.py`), and a `retrieve()` interface (`ccr/retrieve.py`) that resolves a marker back to the originals (or a `NOT_FOUND` sentinel). SmartCrusher persists its drops through an optional injected store, so compression is now provably non-lossy.
- **Phase 3** - the remaining deterministic strategies: `CacheAligner` (KV-cache prefix stabilization), AST-aware `CodeCompressor` (reusing the `nexus-code-search` tree-sitter extractors), and `ContentRouter` (classify JSON / code / log / text and dispatch each to the right strategy).
- **Phase 4** - runtime integration and rtk retirement: the `compress_output(text)` runtime seam, a CLI (`compress` / `retrieve` / `serve`), a rewired `compress(messages)` (routes content; no longer a no-op), an opt-in PreToolUse hook (`catalog/hooks/compress-output.sh`), and an internal MCP server (`server.py`) exposing `context_compress` + `context_retrieve`. The external `rtk` recommendation is superseded by this owned engine.
- **Phase 5** - the accuracy-regression harness (`evals/`): deterministic, offline structural-fidelity checks (CCR round-trip completeness, code signature-preservation rate, a character-reduction effectiveness floor) over a fixed local dataset, with a committed `baseline.json`. Wired as `make compress-eval`, a step inside `make validate`, and a CI gate, so a regression that makes compression lossy or under-effective fails the build.
- **Phase 6** - the optional, default-off ML token-dropper (`transforms/ml_token_dropper.py`): a lossy free-text compressor that scores words with public pre-trained ModernBERT ONNX weights (the `[ml]` extra) and keeps the top fraction by importance. Offline-first (it only *loads* pre-placed local weights, never downloads), zero-outbound, and graceful (absent deps or weights => original text + an install hint). It is CCR-reversible when given a store and is **not** wired into the default pipeline -- the deterministic strategies remain the default.
- **Phase 7** - methodology cross-links and this architecture writeup: the `context-compression`, `prompt-token-optimization`, and `context-optimization` skills now point to this engine as their programmatic counterpart, and the `Architecture` section below documents the pipeline end to end.

## Usage

```python
import nexus_context_compressor as ncc

result = ncc.compress(
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
    ]
)
print(result.tokens_before, result.tokens_after, result.ratio)
```

```bash
# Package identity and active token-counting mode
python -m nexus_context_compressor
```

Reversible compression -- persist dropped spans, then resolve a marker back to
the originals on demand:

```python
from nexus_context_compressor.ccr import CCRStore, retrieve, NOT_FOUND
from nexus_context_compressor.transforms.smart_crusher import smart_crush

with CCRStore() as store:  # defaults to ~/.nexus-hub/cache/ccr-store.db
    result = smart_crush(records, store=store)   # drops are persisted as a side channel
    marker = result.records[1]                   # e.g. {"_ccr_dropped": "<<ccr:HASH N_rows>>"}
    original = retrieve(marker, store=store)      # the exact dropped records, or NOT_FOUND
    if original is NOT_FOUND:
        ...  # span was evicted or the marker is unrecognized
```

With no `store=` argument, `smart_crush` stays pure (no persistence, no side effects).

## Runtime integration (Phase 4)

The engine wires into a live session two ways, both local and zero-outbound.

CLI (what the PreToolUse hook pipes a command's output through):

```bash
# Compress raw output read from stdin (stdout = compressed; metrics on stderr)
some-command-with-json-output | python -m nexus_context_compressor compress

# Resolve a CCR marker back to the dropped originals
python -m nexus_context_compressor retrieve "<<ccr:HASH N_rows>>"
```

PreToolUse hook (`catalog/hooks/compress-output.sh`): opt-in and default-off. Enable it with `export NEXUS_CONTEXT_COMPRESS=1`; it then rewrites each Bash command so its stdout pipes through the engine, preserving the exit status. See [`guides/reference/RTK_CONTEXT_COMPRESSION.md`](../../guides/reference/RTK_CONTEXT_COMPRESSION.md).

Internal MCP server (requires the `mcp` extra): exposes `context_compress` and `context_retrieve` over stdio.

```bash
pip install -e "extensions/nexus-context-compressor/[mcp]"
python -m nexus_context_compressor serve
```

## Install

```bash
pip install -e "extensions/nexus-context-compressor/[dev]"
```

Optional extras: `ml` (Phase 6 ONNX token-dropper), `code` (Phase 3 tree-sitter fallback).

## Tests

```bash
cd extensions/nexus-context-compressor && python -m pytest -q
```
