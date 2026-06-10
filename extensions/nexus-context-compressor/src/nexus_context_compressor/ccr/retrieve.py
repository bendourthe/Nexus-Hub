"""Resolve a CCR marker back to the original dropped records.

This is the read side of reversible compression. Given a ``<<ccr:HASH N_rows>>``
marker (or a marker object, or a bare hash), :func:`retrieve` parses out the
content hash, looks it up in the :class:`~nexus_context_compressor.ccr.store.CCRStore`,
and returns the exact records that were dropped. It is the function the Phase 4
MCP ``context_retrieve`` tool and the PreToolUse hook call when a consumer wants
the dropped data back.

Failure handling is the whole point of the contract here: a marker may be
malformed (truncated, hand-edited) or its span may have been evicted by the
store's TTL/size policy. Neither is an error -- both are a *miss*. :func:`retrieve`
therefore never raises on bad input; it returns the :data:`NOT_FOUND` sentinel,
which the caller is required to handle gracefully (the plan, T006). Distinguish a
hit from a miss with an identity check::

    result = retrieve(marker, store=store)
    if result is NOT_FOUND:
        ...  # span expired or marker unrecognized; fall back
    else:
        ...  # result is the list of original records
"""

from __future__ import annotations

import sqlite3
from typing import Final

from .marker import extract_hash
from .store import CCRStore


class _NotFound:
    """Type of the :data:`NOT_FOUND` sentinel.

    A dedicated singleton type (rather than ``None``) so a miss is unambiguous
    and self-describing in logs and tracebacks: a stored span is always a
    ``list``, and ``None`` could be confused with one, but ``NOT_FOUND`` cannot.
    The sentinel is falsy so ``if not result:`` reads naturally, and its ``repr``
    explains itself.
    """

    _instance: _NotFound | None = None

    def __new__(cls) -> _NotFound:
        # Singleton: every miss returns the same object, so ``is NOT_FOUND``
        # always holds and callers can branch on identity.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<ccr:not-found>"


NOT_FOUND: Final = _NotFound()
"""Returned by :func:`retrieve` when the marker is unrecognized or its span is gone."""


def retrieve(
    marker_or_hash: object, store: CCRStore | None = None
) -> list | _NotFound:
    """Resolve a CCR marker (or hash) to the original dropped records.

    Args:
        marker_or_hash: a ``<<ccr:HASH N_rows>>`` string, a marker object
            ``{"_ccr_dropped": "..."}``, or a bare 12-hex-char hash.
        store: the store to read from. If ``None``, a transient
            :class:`CCRStore` is opened at the default location for this one
            call and closed afterwards. Long-lived consumers (the MCP server)
            should pass a shared store instead of paying the open/close cost per
            call.

    Returns:
        The list of original records on a hit, or :data:`NOT_FOUND` if the
        marker is unrecognizable or its span is absent/evicted. Never raises on
        a malformed marker or a missing hash.
    """
    span_hash = extract_hash(marker_or_hash)
    if span_hash is None:
        return NOT_FOUND

    if store is not None:
        return _coerce(store.get(span_hash))

    # No store supplied: open a transient one at the default location. Guard the
    # open itself -- a missing store file or an unwritable cache dir is a miss,
    # not a crash, because retrieve runs on the hot path of a consumer that must
    # degrade gracefully.
    try:
        with CCRStore() as transient:
            return _coerce(transient.get(span_hash))
    except (OSError, sqlite3.Error):
        return NOT_FOUND


def _coerce(original: list | None) -> list | _NotFound:
    """Map the store's ``None``-on-miss to the public :data:`NOT_FOUND` sentinel."""
    return NOT_FOUND if original is None else original
