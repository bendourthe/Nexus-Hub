"""Tests for the WriteResult / FileAction action vocabulary (T001)."""

from __future__ import annotations

import pytest

from scripts.lib.integrations import FileAction, VALID_ACTIONS, WriteResult


class TestFileAction:
    @pytest.mark.parametrize(
        "action",
        ["created", "updated", "unchanged", "removed", "not-found", "kept"],
    )
    def test_accepts_every_valid_action(self, action: str) -> None:
        fa = FileAction(path="/tmp/example", action=action)  # type: ignore[arg-type]
        assert fa.action == action
        assert fa.path == "/tmp/example"

    def test_rejects_unknown_action(self) -> None:
        with pytest.raises(ValueError, match="Invalid FileAction action"):
            FileAction(path="/tmp/x", action="overwritten")  # type: ignore[arg-type]

    def test_is_frozen(self) -> None:
        fa = FileAction(path="/tmp/x", action="created")
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            fa.path = "/tmp/y"  # type: ignore[misc]


class TestWriteResult:
    def test_defaults_to_empty_files_and_notes(self) -> None:
        result = WriteResult()
        assert result.files == []
        assert result.notes == []

    def test_add_appends_fileaction(self) -> None:
        result = WriteResult()
        result.add("/tmp/a", "created")
        result.add("/tmp/b", "unchanged")
        assert len(result.files) == 2
        assert result.files[0].action == "created"
        assert result.files[1].path == "/tmp/b"

    def test_note_appends_message(self) -> None:
        result = WriteResult()
        result.note("manifest written")
        assert result.notes == ["manifest written"]

    def test_extend_merges_other_in_place(self) -> None:
        a = WriteResult()
        a.add("/tmp/a", "created")
        a.note("note-a")
        b = WriteResult()
        b.add("/tmp/b", "updated")
        b.note("note-b")

        a.extend(b)

        assert [fa.path for fa in a.files] == ["/tmp/a", "/tmp/b"]
        assert a.notes == ["note-a", "note-b"]

    def test_actions_by_kind_counts_each_kind(self) -> None:
        result = WriteResult()
        result.add("/a", "created")
        result.add("/b", "created")
        result.add("/c", "unchanged")
        result.add("/d", "kept")
        counts = result.actions_by_kind()
        assert counts == {"created": 2, "unchanged": 1, "kept": 1}


def test_valid_actions_frozenset_contents() -> None:
    assert VALID_ACTIONS == frozenset(
        {"created", "updated", "unchanged", "removed", "not-found", "kept"}
    )
    assert len(VALID_ACTIONS) == 6
