"""Provenance envelope, changelog, and maintain tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from nexus_memory.changelog import read_events
from nexus_memory.cli import main
from nexus_memory.commands import cmd_record
from nexus_memory.config import StoreConfig
from nexus_memory.lifecycle import apply_maintain, preview_maintain
from nexus_memory.record import MissingSourceError, format_record, parse_record
from nexus_memory.store import MemoryStore


def _store(tmp_path: Path) -> MemoryStore:
    cfg = StoreConfig(record_width=256, max_entry_length=128, read_budget=8)
    return MemoryStore(tmp_path, config=cfg)


def test_missing_source_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(MissingSourceError):
        cmd_record(store, "a fact with no origin")
    assert store.count() == 0


def test_valid_source_is_accepted(tmp_path: Path) -> None:
    store = _store(tmp_path)
    cmd_record(store, "ship checksum pins", source="conversation:test")
    parsed = parse_record(store.get(0), strict=True)
    assert parsed.source == "conversation:test"
    assert parsed.tier == "working"
    assert parsed.body == "ship checksum pins"
    events = read_events(tmp_path)
    assert any("\tadded\t0\t" in row for row in events)


def test_superseded_record_is_kept(tmp_path: Path) -> None:
    store = _store(tmp_path)
    cmd_record(store, "old default", source="conversation:test")
    cmd_record(
        store,
        "new default",
        source="conversation:test",
        supersedes=0,
    )
    assert store.count() == 2
    assert "old default" in store.get(0)
    parsed = parse_record(store.get(1), strict=True)
    assert parsed.supersedes == 0
    events = read_events(tmp_path)
    assert any("\tsuperseded\t0\t" in row for row in events)


def test_legacy_import_token_is_an_allowed_source() -> None:
    payload = format_record("imported note", source="legacy-import", tier="durable")
    parsed = parse_record(payload, strict=True)
    assert parsed.source == "legacy-import"
    assert parsed.legacy is False


def test_maintain_preview_does_not_write(tmp_path: Path) -> None:
    store = _store(tmp_path)
    cmd_record(store, "scratch", source="conversation:test", tier="session")
    before = store.count()
    text = preview_maintain(store)
    assert "would archive" in text
    assert store.count() == before
    assert read_events(tmp_path).count("\tarchived\t") == 0


def test_maintain_apply_copies_backup_and_keeps_entries(tmp_path: Path) -> None:
    store = _store(tmp_path)
    cmd_record(store, "scratch", source="conversation:test", tier="session")
    text = apply_maintain(store)
    assert "backup at" in text
    assert store.count() == 1
    backups = list((tmp_path / "backups").iterdir())
    assert len(backups) == 1
    assert any("\tarchived\t0\t" in row for row in read_events(tmp_path))


def test_cli_record_without_source_exits_nonzero(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path), "record", "--text", "nope"]) == 1
    assert MemoryStore(tmp_path).count() == 0


def test_cli_record_with_source_round_trips(tmp_path: Path) -> None:
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "record",
                "--text",
                "keep",
                "--source",
                "conversation:cli",
            ]
        )
        == 0
    )
    parsed = parse_record(MemoryStore(tmp_path).get(0), strict=True)
    assert parsed.source == "conversation:cli"
    assert parsed.body == "keep"
