"""Token accounting with an offline-safe fallback.

The engine reports compression metrics in tokens, so it needs a token counter.
We prefer ``tiktoken`` (accurate BPE counts) but never *require* a network
call: if tiktoken is not importable, or its vocab cannot be loaded from the
local cache, we fall back to a deterministic stdlib estimator. This preserves
the package's zero-outbound guarantee on air-gapped machines and in CI.

tiktoken ships OpenAI's encodings, not Anthropic's; for Claude there is no
public BPE vocab. ``cl100k_base`` is used as a stable proxy. Token counts here
are therefore approximate in absolute terms but consistent across a single
``compress`` call, which is what the before/after *ratio* needs.
"""

from __future__ import annotations

import re
from functools import lru_cache

# Default proxy encoding. Claude has no public tokenizer; cl100k_base is a
# widely-used, stable proxy adequate for relative before/after ratios.
_DEFAULT_ENCODING = "cl100k_base"

# Deterministic stdlib fallback: split into word runs and standalone
# punctuation. This over-counts vs. BPE but is stable and dependency-free, so
# ratios computed entirely in fallback mode remain meaningful.
_FALLBACK_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


@lru_cache(maxsize=4)
def _load_encoding(encoding_name: str):
    """Return a tiktoken encoding, or ``None`` if unavailable offline.

    Cached so the (possibly expensive) load happens once per encoding. Any
    failure -- tiktoken not installed, or the vocab not present in the local
    cache and unreachable -- resolves to ``None`` and triggers the stdlib
    fallback in :func:`count_tokens`.
    """
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception:
        # Network error fetching vocab, unknown encoding name, or any other
        # failure: degrade gracefully rather than raise.
        return None


def _estimate_tokens(text: str) -> int:
    """Deterministic, dependency-free token estimate."""
    return len(_FALLBACK_TOKEN_RE.findall(text))


def count_tokens(text: str, encoding_name: str = _DEFAULT_ENCODING) -> int:
    """Count tokens in ``text``, preferring tiktoken with a stdlib fallback."""
    if not text:
        return 0
    encoding = _load_encoding(encoding_name)
    if encoding is None:
        return _estimate_tokens(text)
    return len(encoding.encode(text))


def using_accurate_counter(encoding_name: str = _DEFAULT_ENCODING) -> bool:
    """True when tiktoken is available offline; False when in fallback mode.

    Useful for tests and diagnostics that need to know whether counts are exact
    BPE counts or the stdlib estimate.
    """
    return _load_encoding(encoding_name) is not None
