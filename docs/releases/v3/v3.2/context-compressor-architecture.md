# Architecture -- nexus-context-compressor (v3.2.0)

**Status**: Adopted in the v3.2.0 `adoption-headroom` plan ([`plans/adoption-headroom.md`](plans/adoption-headroom.md)).
**Source comparison**: [`comparison-headroom.md`](comparison-headroom.md).
**Engine README** (deep detail): [`../../extensions/nexus-context-compressor/README.md`](../../../../extensions/nexus-context-compressor/README.md).
**Operator guide**: [`../../guides/RTK_CONTEXT_COMPRESSION.md`](../../../../guides/reference/RTK_CONTEXT_COMPRESSION.md).

This note is the project-level overview of the internal context-compression engine adopted in v3.2.0. It explains what the engine is, why it exists, and how its pieces fit together. The engine README is the implementation-level reference; this document is the map.

## Why it exists

Before v3.2.0, Nexus-Hub owned no compression *engine* -- only methodology skills (`context-compression`, `prompt-token-optimization`, `context-optimization`) and a recommendation to install the external `rtk` Rust binary via `cargo install --git` from a raw GitHub repository. That is a "trust an unaudited third-party binary that sees every command's output" posture. `rtk` was also lossy: dropped output was gone for good.

The v3.2.0 adoption rebuilds the high-value subset of headroom's compression engine as an owned, in-repo Python package (`extensions/nexus-context-compressor/`), a sibling of `nexus-code-search` / `nexus-skill-scanner`. It eliminates the external-binary trust surface, adds no new data flow, and makes compression reversible.

## Design principles

- **Local-first, zero-outbound.** Every default-path strategy is pure standard library. The single required dependency, `tiktoken`, is used only for token accounting and degrades to a deterministic stdlib estimate when absent, so the package never requires a network call. The reversible store is a local SQLite file. No command output, file content, or prompt leaves the machine; there is no bundled LLM client and no API key.
- **Reversible by construction.** Every drop is non-lossy: the originals are persisted and the output carries a `<<ccr:HASH N_rows>>` marker that resolves back to them on demand.
- **Reverse-engineer-first.** Per the AGENTS.md MCP Registry Policy, the engine is a clean-room internal port (decision-tree bucket `re-full`), not a wrapper around an external service. The dropped `headroom` components (telemetry beacon, API-key proxy, cross-agent memory subsystem) are documented in the plan's "Items explicitly NOT adopted" appendix.

## How it fits together

The engine has one router and two public entry points:

- `compress_output(text)` -- the single-blob runtime seam the PreToolUse hook (via its CLI) and the internal MCP `context_compress` tool call on raw tool output.
- `compress(messages)` -- routes each message's `content` in a `[{role, content}]` list.

Both delegate to `ContentRouter.route`, which classifies each segment with local heuristics and dispatches it:

| Content type | Strategy | Behavior |
|---|---|---|
| JSON array | `SmartCrusher` | Keep informative records; collapse low-variance runs into a CCR marker |
| Code | `CodeCompressor` | Elide function/method bodies AST-aware; keep imports, signatures, structure |
| Log / free text | (pass through) | Untouched on the default path (see ML note below) |

A fourth deterministic strategy, `CacheAligner`, stabilizes a provider KV-cache *prefix* by moving volatile tokens (dates, UUIDs, versions) to a dynamic tail. It operates on system prompts rather than routed tool output, so it is a standalone, individually-callable transform rather than a `route` branch.

### Reversible compression (CCR)

When a strategy drops content it persists the originals in the CCR store (a local SQLite file at `~/.nexus-hub/cache/ccr-store.db`, content-addressed by SHA-256) and leaves a `<<ccr:HASH N_rows>>` marker in the output. A consumer resolves the marker back to the exact originals via the `context_retrieve` MCP tool or `python -m nexus_context_compressor retrieve "<<ccr:...>>"`, or receives a `NOT_FOUND` sentinel if the span was evicted. The marker grammar lives in one module (`ccr/marker.py`) so the producer and consumer can never drift.

### Accuracy-regression gate

Because aggressive compression ratios are only safe if they preserve answer quality, the package ships a deterministic, offline `evals/` harness that measures structural fidelity (CCR round-trip completeness, code signature-preservation rate, a character-reduction effectiveness floor) against a committed baseline. It runs as `make compress-eval`, inside `make validate`, and as a CI gate, so a change that makes compression lossy or under-effective fails the build. The baseline and methodology are recorded in [`compression-eval-baseline.md`](compression-eval-baseline.md).

### Optional ML token-dropper (offline-first)

The one strategy that compresses free text -- `transforms/ml_token_dropper.py` -- is deliberately fenced off: default-off, opt-in, lossy, and not wired into `route`. When enabled (the `[ml]` extra plus pre-placed public ModernBERT ONNX weights), it scores words by importance and keeps the top fraction. It is offline-first to the strongest degree: it only *loads* pre-placed local weights, never downloads them, and sends no user data anywhere. Missing dependencies or weights degrade to the original text plus an install hint, never a crash or a fetch. The deterministic strategies remain the default pipeline.

## Runtime integration

| Surface | Mechanism | Default |
|---|---|---|
| Claude Code (macOS/Linux) | PreToolUse hook `catalog/hooks/compress-output.sh`, enabled with `NEXUS_CONTEXT_COMPRESS=1` | Off (opt-in) |
| Claude Code (Windows) | CLAUDE.md-injected instruction to pipe structured output through the CLI | Off (opt-in) |
| Any agent | Internal MCP server (`context_compress` + `context_retrieve`), `[mcp]` extra | Off (opt-in) |
| Gemini / Codex / Copilot | Prompt-level output minimization (no hook surface) | N/A |

The hook is jq-gated and fail-open: when unsupported or disabled it is a safe no-op and the original command runs unmodified.

## rtk migration

The internal engine supersedes the external `rtk` recommendation. Existing rtk users remove the rtk hook (or the Windows `CLAUDE.md` block), optionally `cargo uninstall rtk`, and enable the internal hook. The two must not run at the same time. Full steps are in [`../../guides/RTK_CONTEXT_COMPRESSION.md`](../../../../guides/reference/RTK_CONTEXT_COMPRESSION.md).

## Open items

Per-phase deferrals, warnings, and limitations are tracked in [`known-gaps.md`](known-gaps.md) (IDs `DF-v32hr-*`, `WN-v32hr-*`, `MT-v32hr-1`). The notable architectural deferrals are: auto-eviction scheduling for the CCR store (DF-v32hr-4), wiring `CacheAligner` into the runtime messages path (DF-v32hr-9), and auto-wiring the ML dropper into the default pipeline (DF-v32hr-14). All are enhancements; none affect the local-first, reversible, zero-outbound guarantees.
