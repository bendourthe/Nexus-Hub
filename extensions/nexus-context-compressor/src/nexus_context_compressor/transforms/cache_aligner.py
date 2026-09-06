"""CacheAligner: KV-cache prefix stabilization.

LLM providers cache a request's prompt *prefix* and bill the cached span at a
fraction of the normal rate (and serve it faster). The catch is that the cache
key is the literal prefix: a single volatile token near the top -- today's date,
a request UUID, a build hash -- changes the prefix and misses the cache for the
entire system prompt that follows. CacheAligner restores the hit by moving the
volatile lines out of the stable region and down to the tail, leaving a long,
byte-identical prefix that two otherwise-identical requests share.

It does not drop or summarize anything (so there is no CCR store and nothing to
retrieve): it *reorders* and *normalizes whitespace*, and the output contains
exactly the same lines as the input, just regrouped. A line is "dynamic" if it
contains any volatile token (an ISO date or time, a UUID, a long hex hash/token,
a semantic version, or an epoch timestamp); every other line is "stable".

    stable lines (normalized, original order)
    <blank separator>
    dynamic lines (original order)

The dynamic detector is pure local regex. An optional spaCy NER pass (richer
date/quantity detection) sits behind the ``ml``/NER extra and is **off by
default**; when enabled without spaCy installed it degrades silently to
regex-only rather than failing. No outbound call, no clock, no randomness:
identical input always yields an identical, identically-partitioned result.

Reference behavior: ``docs/releases/v3/v3.2/comparisons/v3.2.0-comparison-headroom.md`` Section 5a item 2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Volatile-token patterns. A source line matching ANY of these is moved to the
# dynamic tail. Kept deliberately specific to avoid sweeping stable prose into
# the tail (which would shrink the cacheable prefix without cause).
_DYNAMIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    # ISO date (2026-06-09) and date-time, with optional time component.
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?\b"),
    # Clock time (14:03:59 or 14:03).
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
    # UUID (8-4-4-4-12 hex).
    re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),
    # Long hex run: a hash or opaque token (24+ hex chars; short hex words like
    # "cafe" or "deadbeef" stay put).
    re.compile(r"\b[0-9a-fA-F]{24,}\b"),
    # Semantic version (v1.2.3, 1.2.3, 1.2.3-rc.1).
    re.compile(r"\bv?\d+\.\d+\.\d+(?:[-.][0-9A-Za-z.]+)?\b"),
    # Epoch timestamp (10-13 digit integer).
    re.compile(r"\b\d{10,13}\b"),
)


@dataclass(frozen=True)
class CacheAlignerConfig:
    """Tunables for prefix alignment.

    Attributes:
        collapse_blank_runs: collapse runs of 2+ blank lines in the stable region
            to a single blank line (whitespace normalization for a tighter,
            steadier prefix). The dynamic tail is left as-is.
        use_ner: opt into an optional spaCy NER pass for richer dynamic-entity
            detection (dates, cardinals). Default off; if spaCy (or its model) is
            not installed, this silently degrades to the regex detector.
    """

    collapse_blank_runs: bool = True
    use_ner: bool = False


@dataclass
class AlignResult:
    """The outcome of aligning a system prompt.

    Attributes:
        text: the full reordered, normalized prompt (stable prefix + dynamic tail).
        stable_prefix: the stable region only -- the span a provider can cache.
            This is the byte-identical-across-requests part.
        dynamic_tail: the moved volatile lines (empty when nothing was dynamic).
        moved_lines: number of lines moved to the tail.
        total_lines: number of lines in the input.
    """

    text: str
    stable_prefix: str
    dynamic_tail: str
    moved_lines: int = 0
    total_lines: int = 0

    @property
    def had_dynamic(self) -> bool:
        """Whether any volatile line was found and moved."""
        return self.moved_lines > 0


def _is_dynamic(line: str) -> bool:
    """True if ``line`` carries any volatile token (regex detector)."""
    return any(pattern.search(line) for pattern in _DYNAMIC_PATTERNS)


def _load_ner() -> object | None:
    """Load a spaCy English model for the optional NER pass, or ``None``.

    Lazy and fully guarded: a missing ``spacy`` package or model resolves to
    ``None`` (regex-only), never an exception. This keeps the NER pass a true
    opt-in extra that no default code path depends on.
    """
    try:
        import spacy  # type: ignore
    except ImportError:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _ner_dynamic_lines(lines: list[str], nlp: object) -> set[int]:
    """Indices of lines spaCy flags as carrying a DATE/TIME/CARDINAL entity.

    Best-effort and guarded: any failure yields an empty set so the regex result
    stands. Joins lines with newlines so character offsets map back to a line.
    """
    try:
        text = "\n".join(lines)
        doc = nlp(text)  # type: ignore[operator]
        dynamic: set[int] = set()
        for ent in getattr(doc, "ents", []):
            if ent.label_ in ("DATE", "TIME", "CARDINAL", "QUANTITY"):
                line_index = text.count("\n", 0, ent.start_char)
                dynamic.add(line_index)
        return dynamic
    except Exception:
        return set()


def align(text: str, *, config: CacheAlignerConfig | None = None) -> AlignResult:
    """Stabilize a prompt's cacheable prefix by moving volatile lines to the tail.

    Args:
        text: the system prompt (or any prefix-cached message) to align.
        config: tunables; defaults to :class:`CacheAlignerConfig`.

    Returns:
        An :class:`AlignResult`. ``stable_prefix`` is byte-identical for two
        inputs that differ only in their volatile (dynamic) lines -- that is the
        property that restores the provider KV-cache hit. With no dynamic lines,
        ``stable_prefix == text`` (modulo whitespace normalization) and
        ``dynamic_tail`` is empty.
    """
    config = config or CacheAlignerConfig()
    text = text if isinstance(text, str) else str(text)
    lines = text.split("\n")
    total = len(lines)

    dynamic_idx: set[int] = {i for i, ln in enumerate(lines) if _is_dynamic(ln)}
    if config.use_ner:
        nlp = _load_ner()
        if nlp is not None:
            dynamic_idx |= _ner_dynamic_lines(lines, nlp)

    # rstrip every line (whitespace normalization), preserving order within each
    # group. The stable group keeps non-dynamic lines; the tail keeps dynamic ones.
    stable_lines = [lines[i].rstrip() for i in range(total) if i not in dynamic_idx]
    dynamic_lines = [lines[i].rstrip() for i in range(total) if i in dynamic_idx]

    if config.collapse_blank_runs:
        stable_lines = _collapse_blank_runs(stable_lines)

    stable_prefix = "\n".join(stable_lines)
    dynamic_tail = "\n".join(dynamic_lines)
    full = stable_prefix + ("\n" + dynamic_tail if dynamic_tail else "")
    return AlignResult(
        text=full,
        stable_prefix=stable_prefix,
        dynamic_tail=dynamic_tail,
        moved_lines=len(dynamic_lines),
        total_lines=total,
    )


def _collapse_blank_runs(lines: list[str]) -> list[str]:
    """Collapse runs of 2+ blank lines into a single blank line."""
    out: list[str] = []
    blank_prev = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and blank_prev:
            continue
        out.append(line)
        blank_prev = is_blank
    return out
