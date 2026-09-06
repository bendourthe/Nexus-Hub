"""Tests for the marker-delimited section helper (T003)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib.installer import instruction_merge
from scripts.lib.installer.instruction_merge import (
    DEFAULT_END_MARKER,
    DEFAULT_START_MARKER,
    merge_marker_section,
    remove_marker_section,
)

START = DEFAULT_START_MARKER
END = DEFAULT_END_MARKER


@pytest.fixture
def doc_path(tmp_path: Path) -> Path:
    return tmp_path / "CLAUDE.md"


def test_module_imports_without_preloading_integration_registry() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scripts.lib.installer.instruction_merge import merge_marker_section",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_creates_file_when_missing(doc_path: Path) -> None:
    action = merge_marker_section(doc_path, "Body line one.\nBody line two.")
    assert action.action == "created"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert START in text
    assert END in text
    assert "Body line one." in text
    assert "Body line two." in text


def test_replaces_existing_marker_block(doc_path: Path) -> None:
    doc_path.write_text(
        f"User preamble.\n\n{START}\nOld body.\n{END}\n\nUser appendix.\n",
        encoding="utf-8",
    )
    action = merge_marker_section(doc_path, "New body.")
    assert action.action == "updated"
    text = doc_path.read_text(encoding="utf-8")
    assert "Old body." not in text
    assert "New body." in text
    assert "User preamble." in text
    assert "User appendix." in text


def test_unchanged_on_byte_identical_rerun(doc_path: Path) -> None:
    body = "Stable content."
    first = merge_marker_section(doc_path, body)
    assert first.action == "created"
    second = merge_marker_section(doc_path, body)
    assert second.action == "unchanged"


def test_appends_block_when_file_has_no_markers(doc_path: Path) -> None:
    doc_path.write_text("Just user content.\n", encoding="utf-8")
    action = merge_marker_section(doc_path, "Appended body.")
    assert action.action == "updated"
    text = doc_path.read_text(encoding="utf-8")
    assert text.startswith("Just user content.")
    assert START in text
    assert "Appended body." in text
    assert text.index("Just user content.") < text.index(START)


def test_migrates_legacy_header_inline(doc_path: Path) -> None:
    doc_path.write_text(
        "# Notes\n\n## Nexus-Hub\n\nOld unmanaged body.\n\n## Other\n\nOther body.\n",
        encoding="utf-8",
    )
    action = merge_marker_section(
        doc_path, "New managed body.", legacy_header="## Nexus-Hub"
    )
    assert action.action == "updated"
    text = doc_path.read_text(encoding="utf-8")
    assert "## Nexus-Hub" not in text
    assert "Old unmanaged body." not in text
    assert "New managed body." in text
    assert "## Other" in text
    assert "Other body." in text


def test_user_content_outside_markers_preserved(doc_path: Path) -> None:
    doc_path.write_text(
        f"# My notes\n\n{START}\nNexus content.\n{END}\n\n## My TODOs\n\n- foo\n- bar\n",
        encoding="utf-8",
    )
    action = merge_marker_section(doc_path, "Refreshed Nexus content.")
    assert action.action == "updated"
    text = doc_path.read_text(encoding="utf-8")
    assert "Refreshed Nexus content." in text
    assert "Nexus content." not in text or "Refreshed Nexus content." in text
    assert "## My TODOs" in text
    assert "- foo" in text
    assert "- bar" in text


def test_remove_marker_section_strips_block_and_keeps_user_content(
    doc_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc_path.write_text(
        f"User preamble.\n\n{START}\nNexus content.\n{END}\n\nUser appendix.\n",
        encoding="utf-8",
    )
    replacements: list[tuple[Path, Path]] = []
    real_replace = instruction_merge.os.replace

    def recording_replace(source: str | Path, destination: str | Path) -> None:
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(instruction_merge.os, "replace", recording_replace)
    action = remove_marker_section(doc_path)
    assert action.action == "removed"
    text = doc_path.read_text(encoding="utf-8")
    assert START not in text
    assert END not in text
    assert "User preamble." in text
    assert "User appendix." in text
    assert replacements and replacements[0][1] == doc_path
    assert replacements[0][0].parent == doc_path.parent


def test_remove_marker_section_deletes_file_when_block_was_only_content(
    doc_path: Path,
) -> None:
    doc_path.write_text(f"{START}\nNexus content.\n{END}\n", encoding="utf-8")
    action = remove_marker_section(doc_path)
    assert action.action == "removed"
    assert not doc_path.exists()


def test_remove_marker_section_returns_kept_when_no_marker(doc_path: Path) -> None:
    doc_path.write_text("user content only", encoding="utf-8")
    action = remove_marker_section(doc_path)
    assert action.action == "kept"


def test_remove_marker_section_returns_not_found_when_file_missing(
    doc_path: Path,
) -> None:
    action = remove_marker_section(doc_path)
    assert action.action == "not-found"


def test_dry_run_does_not_write_bytes(doc_path: Path) -> None:
    action = merge_marker_section(doc_path, "Body.", dry_run=True)
    assert action.action == "created"
    assert not doc_path.exists()


def test_custom_markers_round_trip(doc_path: Path) -> None:
    start = "<!-- CUSTOM_START -->"
    end = "<!-- CUSTOM_END -->"
    first = merge_marker_section(doc_path, "Body.", start_marker=start, end_marker=end)
    assert first.action == "created"
    text = doc_path.read_text(encoding="utf-8")
    assert start in text
    assert end in text
    second = remove_marker_section(doc_path, start_marker=start, end_marker=end)
    assert second.action == "removed"
