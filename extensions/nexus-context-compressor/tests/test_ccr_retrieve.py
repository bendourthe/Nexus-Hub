"""Tests for the CCR retrieval interface (Phase 2, T006).

Covers resolving a marker (string, object, or bare hash) back to the originals,
the never-raise contract on malformed markers and evicted spans, the named
NOT_FOUND sentinel, and the transient default-store path.
"""

from __future__ import annotations

from nexus_context_compressor.ccr.marker import format_marker, make_marker_object
from nexus_context_compressor.ccr.retrieve import NOT_FOUND, retrieve
from nexus_context_compressor.ccr.store import CCRStore

_HASH = "0123456789ab"
_ORIGINAL = [{"level": "INFO", "msg": "heartbeat"} for _ in range(12)]


def _seeded_store(tmp_path) -> CCRStore:
    store = CCRStore(tmp_path / "ccr.db")
    store.put(_HASH, _ORIGINAL)
    return store


# -- hits -----------------------------------------------------------------------


def test_retrieve_from_marker_string(tmp_path):
    with _seeded_store(tmp_path) as store:
        assert retrieve(format_marker(_HASH, 12), store=store) == _ORIGINAL


def test_retrieve_from_marker_object(tmp_path):
    with _seeded_store(tmp_path) as store:
        assert retrieve(make_marker_object(_HASH, 12), store=store) == _ORIGINAL


def test_retrieve_from_bare_hash(tmp_path):
    with _seeded_store(tmp_path) as store:
        assert retrieve(_HASH, store=store) == _ORIGINAL


# -- misses (never raise) -------------------------------------------------------


def test_retrieve_absent_hash_returns_sentinel(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        assert retrieve(format_marker("ffffffffffff", 9), store=store) is NOT_FOUND


def test_retrieve_malformed_marker_returns_sentinel(tmp_path):
    with _seeded_store(tmp_path) as store:
        assert retrieve("totally not a marker", store=store) is NOT_FOUND
        assert retrieve(None, store=store) is NOT_FOUND
        assert retrieve({"wrong_key": "x"}, store=store) is NOT_FOUND


def test_retrieve_evicted_span_returns_sentinel(tmp_path):
    with _seeded_store(tmp_path) as store:
        marker = format_marker(_HASH, 12)
        assert retrieve(marker, store=store) == _ORIGINAL
        store.prune(max_entries=0)  # evict everything
        assert retrieve(marker, store=store) is NOT_FOUND


# -- sentinel semantics ---------------------------------------------------------


def test_not_found_is_falsy_and_self_describing():
    assert not NOT_FOUND
    assert repr(NOT_FOUND) == "<ccr:not-found>"


def test_not_found_is_a_singleton():
    # A second resolution of a miss yields the very same object (identity check
    # is the documented way to detect a miss).
    a = retrieve("nope")
    b = retrieve("also nope")
    assert a is NOT_FOUND and b is NOT_FOUND


# -- transient default store ----------------------------------------------------


def test_retrieve_without_store_uses_default_location(tmp_path, monkeypatch):
    db = tmp_path / "default-ccr.db"
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(db))
    # Seed via the same default location, then retrieve with no explicit store.
    with CCRStore(db) as seeded:
        seeded.put(_HASH, _ORIGINAL)
    assert retrieve(format_marker(_HASH, 12)) == _ORIGINAL
    assert retrieve(format_marker("ffffffffffff", 1)) is NOT_FOUND


def test_retrieve_without_store_when_no_db_exists_is_a_miss(tmp_path, monkeypatch):
    # Pointing at a never-created store must degrade to a miss, not crash.
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(tmp_path / "never-made.db"))
    assert retrieve(format_marker(_HASH, 12)) is NOT_FOUND


def test_retrieve_without_store_degrades_when_store_cannot_open(tmp_path, monkeypatch):
    # An unopenable store path (a directory, not a file) must be a miss, not a
    # crash -- the documented graceful-degradation guard on the hot path.
    a_directory = tmp_path / "a_directory"
    a_directory.mkdir()
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(a_directory))
    assert retrieve(format_marker(_HASH, 12)) is NOT_FOUND
