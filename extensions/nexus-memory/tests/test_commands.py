"""Tests for the read / record / merge command surface."""

from __future__ import annotations

import re
from pathlib import Path

from nexus_memory.cli import main
from nexus_memory.commands import (
    cmd_drop,
    cmd_merge,
    cmd_read,
    cmd_record,
    cmd_search,
    cmd_zoom,
    render_read,
)
from nexus_memory.config import StoreConfig
from nexus_memory.store import MemoryStore
from nexus_memory.tree import TreeStore


def _store(tmp_path: Path, n: int = 0, budget: int = 8) -> MemoryStore:
    cfg = StoreConfig(record_width=256, max_entry_length=128, read_budget=budget)
    store = MemoryStore(tmp_path, config=cfg)
    for i in range(n):
        store.append(f"entry-{i}")
    return store


def _drain(store: MemoryStore) -> int:
    answered = 0
    for _ in range(store.count() * 4 + 8):
        tree = TreeStore(
            store.root,
            record_width=store.config.record_width,
            log_count=store.count(),
        )
        pending = tree.pending()
        if not pending:
            return answered
        lo, hi = pending[0]
        cmd_merge(store, lo, hi, f"summary-{lo}-{hi}")
        answered += 1
    raise AssertionError("merge drain did not terminate")


def test_large_unread_store_stays_within_budget(tmp_path: Path) -> None:
    store = _store(tmp_path, n=80, budget=10)
    text = render_read(store)
    lines = [line for line in text.splitlines() if line]
    assert len(lines) <= 10
    assert lines[-1] == "entry-79"


def test_merge_request_names_a_real_pending_range(tmp_path: Path) -> None:
    store = _store(tmp_path, budget=8)
    store.append("alpha")
    request = cmd_record(store, "beta", source="pytest")
    match = re.search(r"# merge \[(\d+), (\d+)\)", request)
    assert match is not None
    lo, hi = int(match.group(1)), int(match.group(2))
    tree = TreeStore(
        store.root,
        record_width=store.config.record_width,
        log_count=store.count(),
    )
    assert (lo, hi) in tree.pending()
    assert "keep what has lasting effect" in request
    assert "max_chars:" in request
    assert "# return:" in request
    assert "alpha" in request and "beta" in request


def _next_visible_due(store: MemoryStore) -> tuple[int, int]:
    """Merge hidden children until a tiled placeholder is itself due."""
    for _ in range(store.count() * 4 + 8):
        text = render_read(store)
        visible = [
            (int(lo), int(hi))
            for lo, hi in re.findall(r"\[(\d+):(\d+) pending merge\]", text)
        ]
        tree = TreeStore(
            store.root,
            record_width=store.config.record_width,
            log_count=store.count(),
        )
        pending = tree.pending()
        for pair in visible:
            if pair in pending:
                return pair
        if not pending:
            raise AssertionError("no pending merge left to make a tiled range due")
        lo, hi = pending[0]
        cmd_merge(store, lo, hi, f"summary-{lo}-{hi}")
    raise AssertionError("never reached a visible due merge")


def test_answering_a_merge_changes_the_next_read(tmp_path: Path) -> None:
    store = _store(tmp_path, n=16, budget=4)
    lo, hi = _next_visible_due(store)
    before = render_read(store)
    assert f"[{lo}:{hi} pending merge]" in before
    cmd_merge(store, lo, hi, f"summary-{lo}-{hi}")
    after = render_read(store)
    assert f"summary-{lo}-{hi}" in after
    assert f"[{lo}:{hi} pending merge]" not in after


def test_end_to_end_fill_merge_and_bounded_read(tmp_path: Path) -> None:
    store = _store(tmp_path, budget=8)
    for i in range(40):
        request = cmd_record(store, f"entry-{i}", source="pytest")
        if request.startswith("# merge"):
            match = re.search(r"# merge \[(\d+), (\d+)\)", request)
            assert match is not None
            cmd_merge(
                store,
                int(match.group(1)),
                int(match.group(2)),
                f"summary-{match.group(1)}-{match.group(2)}",
            )
    remaining = _drain(store)
    text = render_read(store)
    lines = [line for line in text.splitlines() if line]
    assert remaining >= 0
    assert len(lines) <= store.config.read_budget
    assert "pending merge" not in text
    assert lines[-1] == "entry-39"
    assert lines == sorted(lines, key=lambda line: _order_key(line))


def _order_key(line: str) -> tuple[int, int]:
    if line.startswith("summary-"):
        lo, hi = line.split("-")[1], line.split("-")[2]
        return (int(lo), int(hi))
    assert line.startswith("entry-")
    idx = int(line.split("-", 1)[1])
    return (idx, idx + 1)


def test_search_and_zoom_and_drop(tmp_path: Path) -> None:
    store = _store(tmp_path, n=16, budget=4)
    cmd_merge(store, 0, 2, "first-pair")
    hits = cmd_search(store, r"entry-3")
    assert "3: entry-3" in hits
    zoomed = cmd_zoom(store, 0, 4)
    assert "first-pair" in zoomed
    cmd_drop(store, 0, 2)
    tree = TreeStore(
        store.root,
        record_width=store.config.record_width,
        log_count=store.count(),
    )
    assert tree.get(0, 2) is None


def test_cli_read_and_record(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path), "record", "--text", "one", "--source", "pytest"]) == 0
    assert main(["--root", str(tmp_path), "record", "--text", "two", "--source", "pytest"]) == 0
    assert main(["--root", str(tmp_path), "count"]) == 0
    assert main(["--root", str(tmp_path), "read"]) == 0
    paged = cmd_read(MemoryStore(tmp_path), part=1)
    assert "one" in paged or "pending merge" in paged
