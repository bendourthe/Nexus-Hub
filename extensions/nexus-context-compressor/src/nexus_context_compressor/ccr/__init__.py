"""Reversible CCR (Compressed-Content Retrieval) subsystem.

A strategy that drops a span of records leaves a ``<<ccr:HASH N_rows>>`` marker
and persists the originals in a local content-hashed store, so the drop is
reversible: a consumer resolves the marker back to the exact records on demand.
That round-trip is what lets the engine claim non-lossy compression.

Three pieces, in dependency order:

* :mod:`~nexus_context_compressor.ccr.marker` -- the marker codec
  (``format_marker`` / ``parse_marker``), the single source of truth for the
  ``<<ccr:HASH N_rows>>`` grammar shared by the producer and the consumer.
* :mod:`~nexus_context_compressor.ccr.store` -- :class:`CCRStore`, a local
  SQLite store mapping a span's content hash to its JSON-serialized originals,
  with oldest-first :meth:`CCRStore.prune` eviction.
* :mod:`~nexus_context_compressor.ccr.retrieve` -- :func:`retrieve`, which
  resolves a marker to its originals or the :data:`NOT_FOUND` sentinel.
"""

from __future__ import annotations

from .marker import (
    DROPPED_KEY,
    ParsedMarker,
    extract_hash,
    find_all_markers,
    find_marker,
    format_marker,
    make_marker_object,
    parse_marker,
)
from .retrieve import NOT_FOUND, retrieve
from .store import CCRStore, default_store_path

__all__ = [
    "CCRStore",
    "default_store_path",
    "retrieve",
    "NOT_FOUND",
    "format_marker",
    "make_marker_object",
    "parse_marker",
    "extract_hash",
    "find_marker",
    "find_all_markers",
    "ParsedMarker",
    "DROPPED_KEY",
]
