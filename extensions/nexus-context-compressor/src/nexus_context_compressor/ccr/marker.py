"""CCR marker codec: the single source of truth for the ``<<ccr:HASH N_rows>>`` format.

A CCR marker is the placeholder SmartCrusher (and, later, the other strategies)
leaves behind when it drops a span of records: a small object
``{"_ccr_dropped": "<<ccr:HASH N_rows>>"}`` whose string value names the content
hash of the dropped span and how many rows it stood in for. The hash is the key
into the :mod:`nexus_context_compressor.ccr.store`, so a consumer can resolve the
marker back to the original records on demand -- that reversibility is what makes
the compression non-lossy.

This module owns *both* sides of the format so the producer and the consumer can
never drift apart:

* ``format_marker`` builds the string the producer embeds (used by SmartCrusher's
  assembly step).
* ``parse_marker`` reads the string back (used by
  :mod:`nexus_context_compressor.ccr.retrieve`).

Keeping the regex and the f-string in one place means a change to the marker
grammar updates the writer and the reader in lockstep. The module is a pure
leaf: it imports only :mod:`re` and never reaches into the strategy or store
layers, so importing it from a transform introduces no dependency cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Marker grammar. The hash is the first 12 hex chars of a SHA-256 content hash
# (see ``transforms.smart_crusher._content_hash``); ``N_rows`` is the count of
# original records the marker stands in for. Anchored so a marker that has
# trailing junk does not silently parse.
_MARKER_RE = re.compile(r"^<<ccr:(?P<hash>[0-9a-f]{12}) (?P<count>\d+)_rows>>$")

# The key under which a dropped-span marker object carries its marker string.
DROPPED_KEY = "_ccr_dropped"


@dataclass(frozen=True)
class ParsedMarker:
    """The decoded contents of a CCR marker string.

    Attributes:
        hash: the content-hash key into the CCR store.
        count: the number of original records the marker stands in for.
    """

    hash: str
    count: int


def format_marker(span_hash: str, count: int) -> str:
    """Build the marker string for a dropped span.

    Args:
        span_hash: the content hash of the dropped span (12 lowercase hex chars).
        count: the number of records in the span.

    Returns:
        A ``<<ccr:HASH N_rows>>`` string suitable for the ``_ccr_dropped`` field.
    """
    return f"<<ccr:{span_hash} {count}_rows>>"


def make_marker_object(span_hash: str, count: int) -> dict:
    """Build the full ``{"_ccr_dropped": "<<ccr:HASH N_rows>>"}`` marker object.

    This is the object a strategy interleaves into its output array in place of a
    dropped span. Centralizing it here (rather than building the dict inline in
    each strategy) keeps the key name and the string format together.
    """
    return {DROPPED_KEY: format_marker(span_hash, count)}


def parse_marker(value: object) -> ParsedMarker | None:
    """Decode a CCR marker into its hash and row count.

    Accepts either the marker *string* (``"<<ccr:HASH N_rows>>"``) or a marker
    *object* (``{"_ccr_dropped": "<<ccr:HASH N_rows>>"}``), so a caller can pass
    a raw hash-bearing string or a record lifted straight out of a compressed
    array.

    Args:
        value: a marker string, a marker object, or anything else.

    Returns:
        A :class:`ParsedMarker` on a well-formed marker, or ``None`` if ``value``
        is not a recognizable marker. Never raises -- malformed input is a miss,
        not an error, because this runs on data that may have been truncated or
        hand-edited.
    """
    if isinstance(value, dict):
        value = value.get(DROPPED_KEY)
    if not isinstance(value, str):
        return None
    match = _MARKER_RE.match(value.strip())
    if match is None:
        return None
    return ParsedMarker(hash=match.group("hash"), count=int(match.group("count")))


def extract_hash(value: object) -> str | None:
    """Return just the content hash from a marker, or ``None`` if not a marker.

    A convenience over :func:`parse_marker` for callers that only need the store
    key. Also accepts a bare 12-hex-char hash string (so a caller can pass the
    hash directly), which it returns unchanged.
    """
    parsed = parse_marker(value)
    if parsed is not None:
        return parsed.hash
    if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{12}", value.strip()):
        return value.strip()
    return None
