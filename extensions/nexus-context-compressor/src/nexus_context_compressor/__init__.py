"""Nexus-Hub local-first context-compression engine.

Reverse-engineered, owned-and-audited replacement for the external ``rtk``
context-compression binary. The engine routes message content to deterministic
strategies (SmartCrusher JSON-array dedup, CacheAligner, ContentRouter,
AST-aware CodeCompressor), makes every drop reversible through a local
content-hashed CCR store, and offers an optional default-off ML token-dropper.

It is local-first and self-contained: standard-library strategies, a single
required dependency (``tiktoken``, with an offline stdlib fallback), zero
outbound calls, no bundled LLM client, and no API key.

Runtime integration (Phase 4) wires the ContentRouter into the public entry
points so the engine actually compresses: :func:`compress` routes each message's
content, and :func:`compress_output` is the single-blob seam the PreToolUse hook
and the internal MCP ``context_compress`` tool call on raw tool output. The
deterministic strategies compress structured content (JSON arrays, code) and
leave logs and prose untouched; reversibility is provided by the CCR store
(``ccr/``), so a dropped span can be fetched back via ``context_retrieve``.

Public API:
    compress(messages, model=...) -> CompressResult   # route each message's content
    compress_output(text, *, persist=...) -> RouteResult  # the runtime single-blob seam
    CompressResult                -> the result + metrics type
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .filters import apply_trusted_filters
from .reformatters import try_reformat
from .savings import record_passthrough
from .tokens import count_tokens
from .transforms.content_router import RouterConfig, RouteResult, route
from .truncate import truncate_text
from .types import CompressResult

_NEXUS_COMPACT_WIRE_PREFIX = "NEXUS-CW/1\n"


def _finish_output(
    result: RouteResult,
    *,
    persist: bool,
    max_lines: int | None,
    max_bytes: int | None,
    allow_truncate: bool = True,
) -> RouteResult:
    if persist and result.tokens_after >= result.tokens_before:
        record_passthrough(
            tokens=result.tokens_before,
            bytes_in=len(result.text.encode("utf-8")),
        )
    if not allow_truncate or (max_lines is None and max_bytes is None):
        return result
    trunc = truncate_text(result.text, max_lines=max_lines, max_bytes=max_bytes)
    if not trunc.truncated:
        return result
    return RouteResult(
        text=trunc.text,
        segments=result.segments,
        tokens_before=result.tokens_before,
        tokens_after=count_tokens(trunc.text),
    )


if TYPE_CHECKING:
    from .ccr.store import CCRWriter

__all__ = [
    "compress",
    "compress_output",
    "route",
    "CompressResult",
    "RouteResult",
    "count_tokens",
]

__version__ = "3.2.0"


def _message_text(message: object) -> str:
    """Extract the text of a single message for token accounting.

    Accepts a plain string or a mapping carrying a ``content`` field (the
    common ``{"role": ..., "content": ...}`` shape). Anything else is
    stringified so counting never raises on an unexpected shape.
    """
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        content = message.get("content", "")
        return content if isinstance(content, str) else str(content)
    return str(message)


def _total_text(messages: list) -> str:
    """Join the text of all messages for a single token count."""
    return "\n".join(_message_text(m) for m in messages)


def _with_content(message: object, new_text: str) -> object:
    """Return ``message`` with its text replaced by ``new_text``.

    A plain-string message becomes ``new_text``. A mapping keeps every other
    field and swaps only a *string* ``content``; a mapping with absent or
    non-string content is returned untouched (nothing to route). When the text
    is unchanged the rebuilt value compares equal to the original, so a no-op
    route leaves ``compress`` output identical to its input.
    """
    if isinstance(message, str):
        return new_text
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return {**message, "content": new_text}
    return message


def compress_output(
    text: object,
    *,
    persist: bool = True,
    store: "CCRWriter | None" = None,
    config: RouterConfig | None = None,
    max_lines: int | None = None,
    max_bytes: int | None = None,
) -> RouteResult:
    """Compress a single raw output blob -- the runtime seam.

    This is the entry point the PreToolUse compression hook (via the CLI) and the
    internal MCP ``context_compress`` tool call on raw tool output. It runs the
    ContentRouter, which classifies the blob and dispatches structured segments
    (JSON arrays, code) to their deterministic compressors while leaving logs and
    prose untouched.

    Args:
        text: the tool output to compress. A non-string is stringified so the
            call never raises on an unexpected shape.
        persist: when ``True`` (the default for the runtime path) and no explicit
            ``store`` is given, open the default local CCR store so any dropped
            span is reversible via ``context_retrieve``. Set ``False`` for a pure,
            side-effect-free compression.
        store: an explicit CCR write seam. Takes precedence over ``persist``; a
            long-lived consumer (the MCP server) may pass a shared store.
        config: router tunables; defaults to :class:`RouterConfig`.
        max_lines: optional line cap applied after compression. The full blob is
            teed to a spool file and the kept prefix carries a recovery pointer.
        max_bytes: optional UTF-8 byte cap, same recovery contract as ``max_lines``.

    Returns:
        A :class:`RouteResult` with the compressed text, per-segment metrics, and
        whole-blob token accounting. Two runtime-boundary guarantees beyond a raw
        :func:`~nexus_context_compressor.transforms.content_router.route` call:

        * **Never expand.** If routing would *grow* the payload (e.g. a JSON array
          below the crush threshold gets pretty-printed), the original text is
          returned verbatim with identity metrics. The runtime path must never
          make a tool's output larger.
        * **Never lose output.** Opening the store is guarded: a missing or
          unwritable cache directory degrades to a pure (non-persisting)
          compression rather than raising, because this runs on the hot path of a
          consumer that must not lose the user's output.
    """
    if text is None:
        text = ""
    elif not isinstance(text, str):
        text = str(text)

    # Producer-side nexus-code-search responses are already schema-compacted.
    # Preserve their versioned wire bytes so a consumer never double-compresses
    # the payload or changes delimiter framing before the reference decoder runs.
    if text.startswith(_NEXUS_COMPACT_WIRE_PREFIX):
        tokens = count_tokens(text)
        return _finish_output(
            RouteResult(
                text=text,
                segments=[],
                tokens_before=tokens,
                tokens_after=tokens,
            ),
            persist=persist,
            max_lines=max_lines,
            max_bytes=max_bytes,
            allow_truncate=False,
        )

    text = apply_trusted_filters(text)

    reformatted = try_reformat(text)
    if reformatted is not None:
        before = count_tokens(text)
        after = count_tokens(reformatted)
        if after < before:
            return _finish_output(
                RouteResult(
                    text=reformatted,
                    segments=[],
                    tokens_before=before,
                    tokens_after=after,
                ),
                persist=persist,
                max_lines=max_lines,
                max_bytes=max_bytes,
            )

    own_store = None
    if store is None and persist:
        try:
            from .ccr.store import CCRStore

            store = own_store = CCRStore()
        except OSError:
            store = None
    try:
        result = route(text, config=config, store=store)
    finally:
        if own_store is not None:
            own_store.close()

    # Never expand: if reserialization/indenting outweighed any savings, prefer
    # the original verbatim. Any span already persisted is harmless (idempotent,
    # content-addressed, pruned later); the output simply omits the marker.
    if result.tokens_after >= result.tokens_before:
        result = RouteResult(
            text=text,
            segments=result.segments,
            tokens_before=result.tokens_before,
            tokens_after=result.tokens_before,
        )
    return _finish_output(
        result,
        persist=persist,
        max_lines=max_lines,
        max_bytes=max_bytes,
    )


def compress(
    messages: list,
    model: str = "cl100k_base",
    *,
    store: "CCRWriter | None" = None,
    config: RouterConfig | None = None,
) -> CompressResult:
    """Compress a list of messages by routing each message's content.

    Each message's text is run through the ContentRouter: structured segments
    (JSON arrays, code) are compressed and logs/prose pass through unchanged. The
    call is pure by default (``store=None`` => no persistence); pass a ``store``
    to make any dropped span reversible.

    Args:
        messages: the messages to compress. Each is a plain string or a mapping
            with a ``content`` field.
        model: the token-encoding name used for accounting (a proxy; see
            ``tokens`` for why Claude has no public vocab).
        store: an optional CCR write seam threaded to every message's route, so
            drops stay reversible. ``None`` (the default) keeps the call pure.
        config: router tunables; defaults to :class:`RouterConfig`.

    Returns:
        A :class:`CompressResult` carrying the routed messages and token metrics.
        ``transforms_applied`` lists ``"content_router"`` only when routing
        actually changed the content, so an all-prose input round-trips as an
        identity transform (``transforms_applied == []``, ``ratio == 1.0``).
    """
    if messages is None:
        messages = []
    config = config or RouterConfig()

    out_messages: list = []
    changed = False
    for message in messages:
        original_text = _message_text(message)
        routed = route(original_text, config=config, store=store)
        if routed.text != original_text:
            changed = True
        out_messages.append(_with_content(message, routed.text))

    return CompressResult(
        messages=out_messages,
        tokens_before=count_tokens(_total_text(messages), model),
        tokens_after=count_tokens(_total_text(out_messages), model),
        transforms_applied=["content_router"] if changed else [],
    )
