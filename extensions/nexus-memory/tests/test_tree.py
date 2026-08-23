"""Tests for the summary-tree cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_memory.config import StoreConfig
from nexus_memory.store import MemoryStore
from nexus_memory.tree import MissingChildError, TreeStore


def _filled(tmp_path: Path, n: int) -> tuple[MemoryStore, TreeStore]:
    cfg = StoreConfig(record_width=128, max_entry_length=64, read_budget=8)
    store = MemoryStore(tmp_path, config=cfg)
    for i in range(n):
        store.append(f"entry-{i}")
    tree = TreeStore(tmp_path, record_width=128, log_count=store.count())
    return store, tree


def test_pending_is_smallest_first_and_deterministic(tmp_path: Path) -> None:
    _store, tree = _filled(tmp_path, 8)
    first = tree.pending()
    assert first == [(0, 2)]
    assert tree.pending() == first
    assert tree.pending_count() == len(first)


def test_pending_count_matches_enumerated_length(tmp_path: Path) -> None:
    _store, tree = _filled(tmp_path, 16)
    assert tree.pending_count() == len(tree.pending())
    tree.put(0, 2, "s0")
    assert tree.pending_count() == len(tree.pending())


def test_level_with_more_ranges_than_entries_clamps_to_zero(tmp_path: Path) -> None:
    store, tree = _filled(tmp_path, 4)
    tree.put(0, 2, "s0")
    tree.put(2, 4, "s1")
    # A rebuilt view that sees fewer entries than already-written ranges
    # must clamp rather than report a negative remainder.
    stale = TreeStore(tmp_path, record_width=128, log_count=3)
    assert stale.pending_count() >= 0
    assert stale.pending() == []
    assert store.count() == 4


def test_drop_then_rebuild(tmp_path: Path) -> None:
    _store, tree = _filled(tmp_path, 4)
    tree.put(0, 2, "first")
    assert tree.get(0, 2) == "first"
    tree.drop(0, 2)
    assert tree.get(0, 2) is None
    tree.put(0, 2, "rebuilt")
    assert tree.get(0, 2) == "rebuilt"


def test_deleting_every_level_file_loses_no_entry(tmp_path: Path) -> None:
    store, tree = _filled(tmp_path, 6)
    tree.put(0, 2, "a")
    tree.put(2, 4, "b")
    for path in (tmp_path / "tree").glob("level_*"):
        path.unlink()
    assert store.count() == 6
    assert store.get(0) == "entry-0"
    assert store.get(5) == "entry-5"
    rebuilt = TreeStore(tmp_path, record_width=128, log_count=store.count())
    assert rebuilt.pending()[0] == (0, 2)


def test_missing_child_refuses(tmp_path: Path) -> None:
    _store, tree = _filled(tmp_path, 8)
    with pytest.raises(MissingChildError):
        tree.child_contents(0, 4)
