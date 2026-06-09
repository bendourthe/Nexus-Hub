# nexus-context-compressor

Local-first context-compression engine for Nexus-Hub. An owned, audited replacement for the external `rtk` binary: it routes message content to deterministic strategies, makes every drop reversible through a local content-hashed CCR store, and offers an optional default-off ML token-dropper.

The engine is local-first and self-contained: standard-library strategies, a single required dependency (`tiktoken`, with an offline stdlib fallback), zero outbound calls, no bundled LLM client, and no API key.

## Why it exists

Nexus-Hub today owns no compression engine, only methodology skills (`context-compression`, `prompt-token-optimization`) and a dependency on the external `rtk` Rust binary (command-output-only, lossy, installed via `cargo install --git`). This package rebuilds the high-value subset internally as a sibling of `nexus-code-search` / `nexus-skill-scanner`, so Nexus-Hub controls and audits the code that touches a user's context window.

## Design

- **Local-first, zero-outbound.** The deterministic strategies are pure standard library. The only dependency, `tiktoken`, is used for accurate token accounting and degrades to a deterministic stdlib estimate when unavailable, so the package never *requires* a network call. tiktoken's one-time vocab fetch is a static asset carrying no user data.
- **Reversible compression (CCR).** When a strategy drops content, it leaves a `<<ccr:HASH N_rows>>` marker and persists the originals in a local content-hashed store, so a consumer can fetch the dropped data back on demand. Compression is therefore non-lossy.
- **Content-routed strategies.** A router classifies each segment (JSON, code, log, text) and dispatches it to the optimal compressor.

## Status

Built incrementally across the v3.2.0 `adoption-headroom` plan:

- **Phase 1** - package skeleton, `CompressResult` metrics, no-op pipeline, and the first deterministic strategy (SmartCrusher JSON-array dedup) emitting CCR markers.
- **Phase 2** - the reversible CCR store: a local SQLite store keyed by each span's content hash (`ccr/store.py`), a shared marker codec (`ccr/marker.py`), and a `retrieve()` interface (`ccr/retrieve.py`) that resolves a marker back to the originals (or a `NOT_FOUND` sentinel). SmartCrusher persists its drops through an optional injected store, so compression is now provably non-lossy.
- **Phase 3** - the remaining deterministic strategies: `CacheAligner` (KV-cache prefix stabilization), AST-aware `CodeCompressor` (reusing the `nexus-code-search` tree-sitter extractors), and `ContentRouter` (classify JSON / code / log / text and dispatch each to the right strategy).
- **Phase 4 (this phase)** - runtime integration and rtk retirement: the `compress_output(text)` runtime seam, a CLI (`compress` / `retrieve` / `serve`), a rewired `compress(messages)` (routes content; no longer a no-op), an opt-in PreToolUse hook (`catalog/hooks/compress-output.sh`), and an internal MCP server (`server.py`) exposing `context_compress` + `context_retrieve`. The external `rtk` recommendation is superseded by this owned engine.
- **Phases 5-7** - an accuracy-regression gate, the optional ML token-dropper, and methodology cross-links.

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

PreToolUse hook (`catalog/hooks/compress-output.sh`): opt-in and default-off. Enable it with `export NEXUS_CONTEXT_COMPRESS=1`; it then rewrites each Bash command so its stdout pipes through the engine, preserving the exit status. See [`guides/RTK_CONTEXT_COMPRESSION.md`](../../guides/RTK_CONTEXT_COMPRESSION.md).

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
