"""Recursive character splitter with language-aware separator preference.

No tree-sitter dependency - v1.0.0 keeps the install path wheels-only
on Windows. Target 600-char windows with 80-char overlap. Separators
prioritize function / class / brace / blank-line / newline / space
boundaries to stay close to semantic units without parsing.
"""
from __future__ import annotations

from nexus_code_search.types import Chunk

DEFAULT_TARGET_SIZE = 600
DEFAULT_OVERLAP = 80

# Separator preference in descending order. Earlier separators are tried first;
# later ones are fallbacks when the text has none of the earlier ones.
SEPARATORS: tuple[str, ...] = (
    "\n\nclass ",
    "\n\ndef ",
    "\nfunction ",
    "\npublic ",
    "\nprivate ",
    "\nprotected ",
    "\nfn ",
    "\nfunc ",
    "\n\n",
    "\n",
    " ",
    "",
)


def chunk_text(
    text: str,
    file_path: str,
    target_size: int = DEFAULT_TARGET_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split `text` into Chunks preserving line-number provenance.

    Empty text returns an empty list. Text shorter than `target_size`
    returns a single Chunk spanning the full text.
    """
    if not text:
        return []

    if overlap < 0 or overlap >= target_size:
        raise ValueError(f"overlap ({overlap}) must be in [0, target_size={target_size})")

    # Fast path: tiny file.
    if len(text) <= target_size:
        return [_make_chunk(text, 0, len(text), text, file_path)]

    segments = _split_with_separators(text, target_size, overlap)
    return [
        _make_chunk(seg, start, end, text, file_path)
        for seg, start, end in segments
    ]


def _split_with_separators(text: str, target_size: int, overlap: int) -> list[tuple[str, int, int]]:
    """Return list of (segment, start_offset, end_offset) tuples."""
    out: list[tuple[str, int, int]] = []
    cursor = 0
    text_len = len(text)

    while cursor < text_len:
        window_end = min(cursor + target_size, text_len)

        # If we're at the end, emit the tail and stop.
        if window_end >= text_len:
            out.append((text[cursor:text_len], cursor, text_len))
            break

        # Find the best separator within the window.
        split_at = _find_split(text, cursor, window_end)
        out.append((text[cursor:split_at], cursor, split_at))

        # Advance cursor with overlap.
        next_cursor = max(split_at - overlap, cursor + 1)
        if next_cursor <= cursor:
            # Defensive: do not loop on pathological input.
            next_cursor = split_at
        cursor = next_cursor

    return out


def _find_split(text: str, start: int, window_end: int) -> int:
    """Find the best split point within [start, window_end] using separator preference."""
    for sep in SEPARATORS:
        if not sep:
            # Final fallback: hard split at window end.
            return window_end
        # Search for the separator in the window, preferring the latest occurrence
        # so the chunk is as large as possible without exceeding target_size.
        idx = text.rfind(sep, start, window_end)
        if idx > start:
            # Split AFTER the separator so the next chunk starts with the new block.
            return idx + len(sep)
    return window_end


def _make_chunk(segment: str, start: int, end: int, full_text: str, file_path: str) -> Chunk:
    """Construct a Chunk with 1-indexed line numbers based on offsets."""
    start_line = full_text.count("\n", 0, start) + 1
    end_line = full_text.count("\n", 0, end) + 1
    return Chunk(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        text=segment,
    )
