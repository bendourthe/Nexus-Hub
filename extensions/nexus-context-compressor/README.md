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

- **Phase 1 (this phase)** - package skeleton, `CompressResult` metrics, no-op pipeline, and the first deterministic strategy (SmartCrusher JSON-array dedup) emitting CCR markers.
- **Phases 2-7** - CCR reversible store, the remaining deterministic strategies, runtime hook + internal MCP tool (retiring `rtk`), an accuracy-regression gate, the optional ML token-dropper, and methodology cross-links.

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

## Install

```bash
pip install -e "extensions/nexus-context-compressor/[dev]"
```

Optional extras: `ml` (Phase 6 ONNX token-dropper), `code` (Phase 3 tree-sitter fallback).

## Tests

```bash
cd extensions/nexus-context-compressor && python -m pytest -q
```
