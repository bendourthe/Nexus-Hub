"""Deterministic token accounting for the compiled context map.

Prefers ``tiktoken`` (the ``cl100k_base`` encoding) when it is importable and
loads without reaching the network; otherwise falls back to a stdlib-only
heuristic. tiktoken is NOT a hard dependency of the extension, and any failure
in its load path (missing package, or an offline first-use vocab fetch) falls
through to the heuristic, preserving the extension's zero-outbound posture.

Both paths are deterministic within a given environment: the same text always
yields the same count. That is what the token-count header, the tool-versus-CLI
byte-identical guarantee, and the accuracy assertions rely on.
"""

from __future__ import annotations

import re

# Word runs and standalone punctuation. This approximates a byte-pair token
# count closely enough for a human-facing size header, without any dependency.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def count_tokens(text: str) -> int:
    """Return an integer token count for ``text`` (0 for empty input)."""
    if not text:
        return 0
    encoded = _tiktoken_count(text)
    if encoded is not None:
        return encoded
    return _heuristic_tokens(text)


def estimate_tokens_offline(text: str) -> int:
    """Return the stable stdlib estimate used for cross-environment baselines."""
    return _heuristic_tokens(text)


def _tiktoken_count(text: str) -> int | None:
    """Return the tiktoken count, or None if tiktoken is unavailable/offline."""
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:  # pragma: no cover - offline vocab fetch or load failure
        # Never let an optional accelerator break generation; fall back cleanly.
        return None


def _heuristic_tokens(text: str) -> int:
    """Stdlib token estimate: count word and punctuation runs."""
    return len(_TOKEN_RE.findall(text))
