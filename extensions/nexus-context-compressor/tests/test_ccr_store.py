"""Tests for the local SQLite CCR store (Phase 2, T005).

Covers the put/get contract, content-addressed idempotency, introspection,
oldest-first eviction (size cap and TTL), and -- the stability-gate item --
that the store survives a process restart by re-opening the same file.
"""

from __future__ import annotations

import nexus_context_compressor.ccr.store as store_mod
from nexus_context_compressor.ccr.store import CCRStore, CCRWriter, default_store_path


class _FakeClock:
    """A controllable stand-in for ``time.time`` so TTL eviction is deterministic."""

    def __init__(self, now: float) -> None:
        self.now = now

    def time(self) -> float:
        return self.now


def _records(n: int, tag: str = "r") -> list:
    return [{"i": i, "tag": tag} for i in range(n)]


# -- put / get ------------------------------------------------------------------


def test_put_then_get_returns_the_exact_records(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        original = [{"level": "INFO", "msg": "x"}, {"level": "ERROR", "msg": "y"}]
        store.put("abc123abc123", original)
        assert store.get("abc123abc123") == original


def test_get_absent_hash_returns_none(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        assert store.get("deadbeefdead") is None


def test_put_is_idempotent_for_the_same_hash(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        store.put("h0", _records(3))
        store.put("h0", _records(3))
        assert len(store) == 1
        assert store.get("h0") == _records(3)


def test_records_round_trip_preserves_nested_and_unicode(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        # chr(233) is a non-ASCII char built at runtime, so the source file
        # stays ASCII-only (repo convention) while still exercising the unicode
        # JSON round-trip (ensure_ascii=False on write, decode on read).
        original = [{"nested": {"a": [1, 2, 3]}, "u": "caf" + chr(233), "n": None}]
        store.put("h1", original)
        assert store.get("h1") == original


# -- introspection --------------------------------------------------------------


def test_contains_and_len(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        assert len(store) == 0
        store.put("h1", _records(2))
        store.put("h2", _records(2))
        assert len(store) == 2
        assert "h1" in store
        assert "missing" not in store
        assert 123 not in store  # non-str never matches


# -- eviction -------------------------------------------------------------------


def test_prune_size_cap_keeps_newest(tmp_path, monkeypatch):
    clock = _FakeClock(1000.0)
    monkeypatch.setattr(store_mod, "time", clock)
    with CCRStore(tmp_path / "ccr.db") as store:
        for i in range(5):
            clock.now = 1000.0 + i  # each put is strictly newer
            store.put(f"h{i}", _records(1))
        evicted = store.prune(max_entries=2)
        assert evicted == 3
        assert len(store) == 2
        # The two newest survive; the three oldest are gone.
        assert "h4" in store and "h3" in store
        assert "h0" not in store and "h1" not in store and "h2" not in store


def test_prune_ttl_evicts_only_old_entries(tmp_path, monkeypatch):
    clock = _FakeClock(1000.0)
    monkeypatch.setattr(store_mod, "time", clock)
    with CCRStore(tmp_path / "ccr.db") as store:
        store.put("old", _records(1))
        clock.now = 5000.0
        store.put("new", _records(1))
        # "now" is 5000; evict anything older than 1000s (created before 4000).
        evicted = store.prune(older_than_seconds=1000)
        assert evicted == 1
        assert "old" not in store
        assert "new" in store


def test_prune_with_no_policy_evicts_nothing(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        store.put("h", _records(1))
        assert store.prune() == 0
        assert len(store) == 1


# -- restart persistence (stability gate) --------------------------------------


def test_store_survives_process_restart(tmp_path):
    db = tmp_path / "ccr.db"
    original = [{"k": "v"} for _ in range(4)]
    first = CCRStore(db)
    first.put("persist", original)
    first.close()

    # A fresh instance on the same file (a new "process") sees the data.
    second = CCRStore(db)
    try:
        assert second.get("persist") == original
        assert len(second) == 1
    finally:
        second.close()


def test_close_is_idempotent(tmp_path):
    store = CCRStore(tmp_path / "ccr.db")
    store.close()
    store.close()  # must not raise


# -- path resolution ------------------------------------------------------------


def test_default_store_path_honors_explicit_env(monkeypatch, tmp_path):
    target = tmp_path / "custom" / "ccr.db"
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(target))
    assert default_store_path() == target


def test_default_store_path_uses_hub_root_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("NEXUS_CCR_STORE_PATH", raising=False)
    monkeypatch.setenv("NEXUS_HUB_ROOT", str(tmp_path))
    assert default_store_path() == tmp_path / "cache" / "ccr-store.db"


def test_store_creates_parent_directory(tmp_path):
    db = tmp_path / "deep" / "nested" / "ccr.db"
    with CCRStore(db) as store:
        store.put("h", _records(1))
    assert db.exists()


def test_ccrstore_satisfies_the_writer_protocol(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        assert isinstance(store, CCRWriter)
