"""Tests for the marker-delimited section helper (T003)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_state_root_honors_isolated_nexus_home_without_overriding_global_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nexus_home = tmp_path / "nexus-home"
    monkeypatch.setenv("NEXUS_HUB_HOME", str(nexus_home))
    assert instruction_merge.state_root(SimpleNamespace(scope="workspace")) == nexus_home / "state"
    explicit = tmp_path / "global-profile"
    assert instruction_merge.state_root(SimpleNamespace(scope="global", global_root=explicit)) == (
        explicit / ".nexus-hub" / "state"
    )


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


# WN-5-v4133: native teardown must preserve user line-ending bytes.

@pytest.mark.parametrize(
    ("head", "tail", "block_eol", "expected"),
    [
        (b"First\nSecond\n\n", b"\nTail one\nTail two\n", b"\n", b"First\nSecond\n\nTail one\nTail two\n"),
        (b"First\r\nSecond\r\n\r\n", b"\r\nTail one\r\nTail two\r\n", b"\r\n", b"First\r\nSecond\r\n\r\nTail one\r\nTail two\r\n"),
        (b"First\r\nSecond\n\n", b"\nTail one\r\nTail two\n", b"\n", b"First\r\nSecond\n\nTail one\r\nTail two\n"),
        (b"First\nSecond\r\n\r\n", b"\nTail one\nTail two\r\n", b"\n", b"First\nSecond\r\n\r\nTail one\nTail two\r\n"),
        (b"First\r\nSecond\r\n\r\n", b"", b"\r\n", b"First\r\nSecond\r\n"),
        (b"", b"\r\nTail one\r\nTail two\r\n", b"\r\n", b"Tail one\r\nTail two\r\n"),
    ],
)
def test_remove_marker_section_preserves_user_line_endings(
    doc_path: Path, head: bytes, tail: bytes, block_eol: bytes, expected: bytes
) -> None:
    source = head + START.encode() + block_eol + b"Owned body" + block_eol + END.encode() + block_eol + tail
    doc_path.write_bytes(source)
    preview = remove_marker_section(doc_path, dry_run=True)
    assert preview.action == "removed"
    assert doc_path.read_bytes() == source
    result = remove_marker_section(doc_path)
    assert result.action == "removed"
    assert doc_path.read_bytes() == expected
    assert remove_marker_section(doc_path).action == "kept"
    assert doc_path.read_bytes() == expected


def test_remove_marker_section_crlf_only_block_deletes_file(doc_path: Path) -> None:
    doc_path.write_bytes((START + "\r\nOwned body\r\n" + END + "\r\n").encode())
    assert remove_marker_section(doc_path).action == "removed"
    assert not doc_path.exists()


# --- Project CLAUDE.md migration states keep user bytes (v4.15.2, Phase 4) ----


def _claude_state_ctx(tmp_path):
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest

    project = tmp_path / "state-project"
    project.mkdir(exist_ok=True)
    return InstallContext(
        repo_root=Path(__file__).resolve().parents[2], target_root=project, scope="workspace",
        instruction_only=True, manifest=InstallManifest(),
    )


def test_malformed_markers_are_user_bytes_and_migration_leaves_them_alone(tmp_path, monkeypatch):
    from scripts.lib.integrations.claude import ClaudeIntegration, classify_project_claude_md

    ctx = _claude_state_ctx(tmp_path)
    original = b"# Mine\r\n<!-- NEXUS_HUB_START -->\r\nunterminated block\r\n"
    (ctx.target_root / "CLAUDE.md").write_bytes(original)
    assert classify_project_claude_md(ctx.target_root) == "user-authored"
    ClaudeIntegration()._migrate_project_claude_md(ctx.target_root, ctx)
    assert (ctx.target_root / "CLAUDE.md").read_bytes() == original


def test_mixed_file_migration_removes_only_the_owned_block_and_keeps_crlf_bytes(tmp_path):
    from scripts.lib.integrations.claude import ClaudeIntegration

    ctx = _claude_state_ctx(tmp_path)
    block = "<!-- NEXUS_HUB_START -->\nbody\n<!-- NEXUS_HUB_END -->\n"
    (ctx.target_root / "CLAUDE.md").write_bytes(b"# Mine\r\nline two\r\n\r\n" + block.encode())
    actions = ClaudeIntegration()._migrate_project_claude_md(ctx.target_root, ctx)
    assert [a.action for a in actions] == ["removed"]
    left = (ctx.target_root / "CLAUDE.md").read_bytes()
    assert left.startswith(b"# Mine\r\nline two") and b"NEXUS_HUB" not in left


def test_managed_only_file_migration_is_reversible_by_a_later_install(tmp_path, monkeypatch):
    from scripts.lib.integrations.claude import ClaudeIntegration

    ctx = _claude_state_ctx(tmp_path)
    for key, value in (("NEXUS_HUB_CLAUDE_VERSION", "2.1.270"),
                       ("CLAUDE_CONFIG_DIR", str(tmp_path / "cfg")),
                       ("NEXUS_HUB_CLAUDE_MANAGED_SETTINGS", str(tmp_path / "none.json"))):
        monkeypatch.setenv(key, value)
    ClaudeIntegration().install_workspace(ctx)
    claude_md = ctx.target_root / "CLAUDE.md"
    assert claude_md.exists()
    ClaudeIntegration()._migrate_project_claude_md(ctx.target_root, ctx)
    assert not claude_md.exists()
    ClaudeIntegration().install_workspace(ctx)
    assert "NEXUS_HUB_START" in claude_md.read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _isolated_nexus_home_v4152(tmp_path, monkeypatch):
    """The merge owner keeps lock and backup state under NEXUS_HUB_HOME; never the real home."""
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "nexus-home-v4152"))
