"""Local SQLite store for reversible CCR compression.

When a strategy drops a span of records it leaves a ``<<ccr:HASH N_rows>>``
marker (see :mod:`nexus_context_compressor.ccr.marker`) and persists the
originals here, keyed by the same content hash. A consumer (the Phase 4 MCP
``retrieve`` tool and the PreToolUse hook) can then resolve the marker back to
the exact dropped records, so compression is non-lossy.

Design constraints (from the adoption-headroom plan, T005):

* **SQLite only.** No Redis, no Qdrant, no network service -- the store is a
  single local file. Opening it makes zero outbound calls.
* **Content-addressed and idempotent.** The key is the span's content hash, so
  re-persisting the same span is a no-op-equivalent (``INSERT OR REPLACE``).
* **Survives process restart.** The data is a real file on disk, not an
  in-memory cache, so a hook that writes in one process and an MCP tool that
  reads in another (or a later session) both see the same records.

Store location
--------------
By default the store lives at ``~/.nexus-hub/cache/ccr-store.db``. Resolution
order (see :func:`default_store_path`):

1. ``NEXUS_CCR_STORE_PATH`` -- an explicit file path, if set.
2. ``NEXUS_HUB_ROOT`` (or ``~/.nexus-hub``) ``/cache/ccr-store.db``.

Tests and embedders pass an explicit ``path`` to :class:`CCRStore` to keep the
store off the real home directory.

Size / TTL eviction
--------------------
A reversible store grows with every dropped span, so it needs a bound. Each row
records a ``created_at`` epoch second at insert time, and :meth:`CCRStore.prune`
evicts oldest-first down to a maximum entry count (or older than a cutoff). The
hot path never evicts automatically -- ``put`` only inserts -- so callers stay
deterministic; eviction is an explicit, opt-in maintenance step a hook or a
scheduled job invokes. The recommended policy is a periodic
``store.prune(max_entries=...)``; markers whose rows have been evicted resolve
to the not-found sentinel via :mod:`nexus_context_compressor.ccr.retrieve`,
which the consumer is required to handle gracefully.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class CCRWriter(Protocol):
    """The write seam a strategy needs to make its drops reversible.

    A strategy (SmartCrusher and, later, CodeCompressor) persists each dropped
    span through this one-method surface rather than importing the concrete
    :class:`CCRStore`, so the strategy layer stays decoupled from SQLite and a
    test can inject a trivial in-memory fake. :class:`CCRStore` satisfies it
    structurally.
    """

    def put(self, span_hash: str, original: list) -> None:  # pragma: no cover - protocol
        ...

# Schema kept tiny on purpose: one table mapping a content hash to the
# JSON-serialized original records, plus an insert timestamp for TTL eviction.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS ccr_spans (
    hash       TEXT PRIMARY KEY,
    records    TEXT NOT NULL,
    n_rows     INTEGER NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ccr_created_at ON ccr_spans(created_at);
"""

_DEFAULT_DB_FILENAME = "ccr-store.db"
# How long a writer waits for a competing writer's lock before erroring. A hook
# and an MCP tool may touch the store concurrently; a short busy timeout lets
# the loser wait rather than fail.
_BUSY_TIMEOUT_MS = 5000


def default_store_path() -> Path:
    """Resolve the default on-disk location of the CCR store.

    Order: ``NEXUS_CCR_STORE_PATH`` (explicit file) -> ``NEXUS_HUB_ROOT``/cache ->
    ``~/.nexus-hub/cache``. The parent directory is *not* created here; the
    store creates it on open.
    """
    explicit = os.environ.get("NEXUS_CCR_STORE_PATH")
    if explicit:
        return Path(explicit).expanduser()
    hub_root = os.environ.get("NEXUS_HUB_ROOT")
    base = Path(hub_root).expanduser() if hub_root else Path.home() / ".nexus-hub"
    return base / "cache" / _DEFAULT_DB_FILENAME


class CCRStore:
    """A local, content-addressed store of dropped record spans.

    Open one with a default location (``CCRStore()``) or an explicit path
    (``CCRStore(path)``); the latter is what tests and embedders use. The store
    owns its SQLite connection and can be used as a context manager::

        with CCRStore(tmp_path / "ccr.db") as store:
            store.put(span.hash, span.records)

    The store is safe to re-open against an existing file (the schema is applied
    idempotently), which is how restart-persistence works.
    """

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        """Open (and bootstrap, if needed) the store at ``path``.

        Args:
            path: the SQLite file path. Defaults to :func:`default_store_path`.
                The parent directory is created if absent.
        """
        self.path = Path(path).expanduser() if path is not None else default_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), timeout=_BUSY_TIMEOUT_MS / 1000)
        # WAL lets a reader (the MCP retrieve tool) and a writer (the hook) work
        # concurrently without blocking each other on a single local file.
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- write -----------------------------------------------------------------

    def put(self, span_hash: str, original: list) -> None:
        """Persist the original records of a dropped span under its content hash.

        Idempotent: re-putting the same hash replaces the row in place (the
        content is identical by construction, since the hash addresses it), so a
        strategy that re-compresses the same payload never duplicates rows or
        errors. ``created_at`` is refreshed on replace so a re-touched span looks
        recently used to the eviction policy.

        Args:
            span_hash: the content hash key (the value in the CCR marker).
            original: the original dropped records (any JSON-serializable list).
        """
        payload = json.dumps(original, ensure_ascii=False, separators=(",", ":"))
        n_rows = len(original) if isinstance(original, (list, tuple)) else 1
        self._conn.execute(
            "INSERT INTO ccr_spans(hash, records, n_rows, created_at) "
            "VALUES(?, ?, ?, ?) "
            "ON CONFLICT(hash) DO UPDATE SET "
            "records = excluded.records, "
            "n_rows = excluded.n_rows, "
            "created_at = excluded.created_at",
            (span_hash, payload, n_rows, time.time()),
        )
        self._conn.commit()

    # -- read ------------------------------------------------------------------

    def get(self, span_hash: str) -> list | None:
        """Return the original records for ``span_hash``, or ``None`` if absent.

        ``None`` covers both "never stored" and "evicted" -- the low-level store
        does not distinguish them. The higher-level
        :func:`nexus_context_compressor.ccr.retrieve.retrieve` maps this to a
        named not-found sentinel for consumer clarity.
        """
        row = self._conn.execute(
            "SELECT records FROM ccr_spans WHERE hash = ?", (span_hash,)
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def __contains__(self, span_hash: object) -> bool:
        if not isinstance(span_hash, str):
            return False
        return (
            self._conn.execute(
                "SELECT 1 FROM ccr_spans WHERE hash = ? LIMIT 1", (span_hash,)
            ).fetchone()
            is not None
        )

    def __len__(self) -> int:
        """Number of spans currently stored."""
        return int(
            self._conn.execute("SELECT COUNT(*) FROM ccr_spans").fetchone()[0]
        )

    # -- maintenance -----------------------------------------------------------

    def prune(
        self, max_entries: int | None = None, older_than_seconds: float | None = None
    ) -> int:
        """Evict stored spans to bound the store's growth.

        Two independent, composable policies (apply both in one call if you want):

        * ``older_than_seconds`` -- drop every span inserted more than this many
          seconds ago (a TTL sweep).
        * ``max_entries`` -- after the TTL sweep, if more than ``max_entries``
          spans remain, drop the oldest until exactly ``max_entries`` are left
          (a size cap).

        Eviction is oldest-first by ``created_at``. This is never called on the
        hot path; a hook or scheduled job invokes it. A pruned span's marker
        later resolves to the not-found sentinel, which consumers must handle.

        Args:
            max_entries: keep at most this many spans (the newest). ``None`` =
                no size cap.
            older_than_seconds: evict spans older than this. ``None`` = no TTL.

        Returns:
            The number of spans evicted.
        """
        evicted = 0
        if older_than_seconds is not None:
            cutoff = time.time() - older_than_seconds
            cur = self._conn.execute(
                "DELETE FROM ccr_spans WHERE created_at < ?", (cutoff,)
            )
            evicted += cur.rowcount
        if max_entries is not None and max_entries >= 0:
            remaining = len(self)
            overflow = remaining - max_entries
            if overflow > 0:
                cur = self._conn.execute(
                    "DELETE FROM ccr_spans WHERE hash IN ("
                    "SELECT hash FROM ccr_spans ORDER BY created_at ASC, hash ASC LIMIT ?"
                    ")",
                    (overflow,),
                )
                evicted += cur.rowcount
        self._conn.commit()
        return evicted

    # -- lifecycle -------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying SQLite connection. Idempotent."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None  # type: ignore[assignment]

    def __enter__(self) -> CCRStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
