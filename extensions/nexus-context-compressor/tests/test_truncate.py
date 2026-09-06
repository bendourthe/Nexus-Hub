"""Truncation tees the full blob and the dropped tail is recoverable."""

from __future__ import annotations

from pathlib import Path

from nexus_context_compressor.truncate import recovered_tail, truncate_text


def test_short_text_is_unchanged() -> None:
    text = "one\ntwo\n"
    result = truncate_text(text, max_lines=10)
    assert result.truncated is False
    assert result.text == text
    assert recovered_tail(text, result) == ""


def test_line_cap_spools_full_output_and_recovers_tail(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("NEXUS_COMPRESSOR_SPOOL_DIR", str(tmp_path / "spool"))
    original = "".join(f"line-{i}\n" for i in range(1, 11))
    result = truncate_text(original, max_lines=3)
    assert result.truncated is True
    assert result.full_path is not None
    assert result.full_path.read_text(encoding="utf-8") == original
    kept_body = result.text.split("]\n", 1)[-1]
    assert "line-1\n" in kept_body
    assert "line-4\n" not in kept_body
    dropped = recovered_tail(original, result)
    assert dropped == "".join(f"line-{i}\n" for i in range(4, 11))
    assert dropped == "".join(result.full_path.read_text(encoding="utf-8").splitlines(keepends=True)[3:])


def test_spool_failure_returns_original(tmp_path: Path, monkeypatch) -> None:
    blocked = tmp_path / "blocked"
    blocked.write_text("not-a-directory", encoding="utf-8")
    monkeypatch.setenv("NEXUS_COMPRESSOR_SPOOL_DIR", str(blocked))
    original = "".join(f"line-{i}\n" for i in range(1, 20))
    result = truncate_text(original, max_lines=2)
    assert result.truncated is False
    assert result.text == original
