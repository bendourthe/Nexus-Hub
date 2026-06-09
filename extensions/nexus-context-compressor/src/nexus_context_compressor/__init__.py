"""Nexus-Hub local-first context-compression engine.

Reverse-engineered, owned-and-audited replacement for the external ``rtk``
context-compression binary. The engine routes message content to deterministic
strategies (SmartCrusher JSON-array dedup, CacheAligner, ContentRouter,
AST-aware CodeCompressor), makes every drop reversible through a local
content-hashed CCR store, and offers an optional default-off ML token-dropper.

It is local-first and self-contained: standard-library strategies, a single
required dependency (``tiktoken``, with an offline stdlib fallback), zero
outbound calls, no bundled LLM client, and no API key.

Phase 1 ships the package skeleton: the ``compress`` entry point runs a no-op
pipeline (messages pass through unchanged) while reporting real token metrics.
Subsequent phases register strategies into the pipeline.

Public API:
    compress(messages, model=...) -> CompressResult
    CompressResult                -> the result + metrics type
"""

from __future__ import annotations

from .tokens import count_tokens
from .types import CompressResult

__all__ = ["compress", "CompressResult", "count_tokens"]

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


def compress(messages: list, model: str = "cl100k_base") -> CompressResult:
    """Compress a list of messages.

    Args:
        messages: the messages to compress. Each is a plain string or a mapping
            with a ``content`` field.
        model: the token-encoding name used for accounting (a proxy; see
            ``tokens`` for why Claude has no public vocab).

    Returns:
        A :class:`CompressResult`. In Phase 1 the pipeline is a no-op: the
        messages are returned unchanged and ``tokens_after == tokens_before``.
    """
    if messages is None:
        messages = []
    tokens = count_tokens(_total_text(messages), model)
    return CompressResult(
        messages=list(messages),
        tokens_before=tokens,
        tokens_after=tokens,
        transforms_applied=[],
    )
