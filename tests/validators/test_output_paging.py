"""Tests for the Phase 1 output-paging helper and self-naming commands.

Transport paging is how agent-consumed script output survives every target
CLI's truncation behavior. These tests pin the contract in
docs/policy/output-truncation-limits.md and scripts/lib/output_paging.py:

- a payload under both caps is one part with no framing
- a payload over the byte cap only, the line cap only, or both, is split
- a single line longer than the byte cap is reported, never split
- a next-part trailer names a command that resolves to an existing file
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB = REPO_ROOT / "scripts" / "lib"
POLICY = REPO_ROOT / "docs" / "policy" / "output-truncation-limits.md"
RETENTION = REPO_ROOT / "scripts" / "check_docs_retention.py"

sys.path.insert(0, str(LIB))

from output_paging import (  # noqa: E402
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    OversizedLineError,
    page_text,
)
from self_naming import (  # noqa: E402
    expand_printed_path,
    first_existing_path_in_command,
    fold_user_path,
    runnable_self_command,
)


def test_defaults_match_the_policy_safe_default() -> None:
    """A helper whose defaults drift from the policy silently truncates agents."""
    text = POLICY.read_text(encoding="utf-8")
    assert "16,000 bytes" in text
    assert "256 lines" in text
    assert DEFAULT_MAX_BYTES == 16_000
    assert DEFAULT_MAX_LINES == 256


def test_payload_under_both_caps_is_one_part_with_no_framing() -> None:
    payload = "alpha\nbeta\ngamma\n"
    page = page_text(payload, max_bytes=200, max_lines=20, next_command_prefix="tool")

    assert page.total_parts == 1
    assert page.next_command is None
    assert page.text == payload
    assert "# next:" not in page.text


def test_payload_over_byte_cap_only_is_split() -> None:
    # Each line is 20 bytes; a 50-byte cap with a short trailer fits one
    # line per part once the trailer reservation is applied.
    lines = [f"line-{i:02d}-xxxxxxxx" for i in range(4)]
    payload = "\n".join(lines)
    first = page_text(
        payload, part=1, max_bytes=50, max_lines=20, next_command_prefix="tool"
    )

    assert first.total_parts > 1
    assert first.next_command == "tool --part 2"
    assert first.text.endswith("# next: tool --part 2")
    assert utf8_size(first.text) <= 50
    assert first.text.count("\n") + (0 if first.text.endswith("\n") else 1) <= 20
    assert "line-00" in first.text
    # later lines belong to later parts
    last_line = lines[-1]
    assert last_line not in first.text.split("# next:")[0]


def test_payload_over_line_cap_only_is_split() -> None:
    payload = "\n".join(f"row-{i}" for i in range(10))
    first = page_text(
        payload, part=1, max_bytes=10_000, max_lines=3, next_command_prefix="tool"
    )
    second = page_text(
        payload, part=2, max_bytes=10_000, max_lines=3, next_command_prefix="tool"
    )

    assert first.total_parts > 1
    # line cap 3, one reserved for the trailer, so two content lines per part
    content = first.text.split("\n# next:")[0]
    assert content.count("\n") + 1 <= 2
    assert "row-0" in first.text
    assert "row-2" in second.text or "row-2" in first.text
    assert utf8_size(first.text) <= 10_000


def test_payload_over_both_caps_is_split_and_each_part_is_under_both() -> None:
    payload = "\n".join(f"item-{i:03d}-xxxxxxxxxx" for i in range(20))
    first = page_text(
        payload, part=1, max_bytes=80, max_lines=4, next_command_prefix="tool"
    )
    assert first.total_parts > 1
    for index in range(1, first.total_parts + 1):
        page = page_text(
            payload,
            part=index,
            max_bytes=80,
            max_lines=4,
            next_command_prefix="tool",
        )
        assert utf8_size(page.text) <= 80
        assert page.text.count("\n") + 1 <= 4


def test_oversized_single_line_is_reported_not_split() -> None:
    payload = "x" * 80
    with pytest.raises(OversizedLineError) as caught:
        page_text(payload, max_bytes=40, max_lines=10, next_command_prefix="tool")

    assert caught.value.line_number == 1
    assert caught.value.byte_length == 80
    assert caught.value.max_bytes == 40
    # the error text must name the recovery, not just the size
    assert "cannot be paged without splitting" in str(caught.value)


def test_next_part_command_resolves_to_an_existing_file() -> None:
    payload = "\n".join(f"row-{i}" for i in range(40))
    page = page_text(
        payload,
        part=1,
        max_bytes=400,
        max_lines=8,
        script_path=RETENTION,
        extra_args=["--quiet"],
    )

    assert page.next_command is not None
    assert "--part 2" in page.next_command
    resolved = first_existing_path_in_command(page.next_command)
    assert resolved is not None
    assert resolved == RETENTION.resolve()
    assert resolved.is_file()


def test_self_naming_folds_a_home_path_and_stays_resolvable() -> None:
    command = runnable_self_command(
        ["--root", ".", "--part", "2"],
        script_path=RETENTION,
    )
    resolved = first_existing_path_in_command(command)
    assert resolved == RETENTION.resolve()
    assert resolved.is_file()
    folded = fold_user_path(RETENTION)
    if folded.startswith("~/"):
        assert "~/" in command


def test_retention_script_small_report_has_no_paging_frame(tmp_path: Path) -> None:
    """Existing consumer: a report under both caps is unchanged (no framing)."""
    root = tmp_path / "repo"
    plugin = root / ".claude-plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text('{"version": "3.17.6"}', encoding="utf-8")
    history = root / "docs" / "v3" / "v3.15" / "development" / "history"
    history.mkdir(parents=True)
    (history / "note.md").write_text("# note\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(RETENTION), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "WARN" in proc.stdout
    assert "# next:" not in proc.stdout


def test_invalid_part_index_is_reported() -> None:
    payload = "one line\n"
    with pytest.raises(ValueError, match="does not exist"):
        page_text(payload, part=2, max_bytes=200, max_lines=20, next_command_prefix="tool")
    with pytest.raises(ValueError, match="part must be"):
        page_text(payload, part=0, max_bytes=200, max_lines=20, next_command_prefix="tool")
    with pytest.raises(ValueError, match="max_bytes"):
        page_text(payload, part=1, max_bytes=0, max_lines=20, next_command_prefix="tool")
    with pytest.raises(ValueError, match="max_lines"):
        page_text(payload, part=1, max_bytes=200, max_lines=0, next_command_prefix="tool")


def test_emit_paged_and_has_more_helpers() -> None:
    from output_paging import emit_paged

    small = emit_paged("ok\n", max_bytes=200, max_lines=20, next_command_prefix="tool")
    assert small == "ok\n"
    payload = "\n".join(f"row-{i}" for i in range(10))
    page = page_text(payload, max_bytes=80, max_lines=3, next_command_prefix="tool")
    assert page.has_more is True
    last = page_text(
        payload, part=page.total_parts, max_bytes=80, max_lines=3, next_command_prefix="tool"
    )
    assert last.has_more is False


def utf8_size(text: str) -> int:
    return len(text.encode("utf-8"))
