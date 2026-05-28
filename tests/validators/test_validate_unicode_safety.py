"""Tests for scripts/validate_unicode_safety.py."""

from __future__ import annotations

from pathlib import Path


SCRIPT = "validate_unicode_safety.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_bytes(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def test_clean_tree_passes(tmp_path: Path, runner) -> None:
    write(tmp_path / "docs" / "README.md", "Plain ASCII content.\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_rlo_trojan_source_is_flagged(tmp_path: Path, runner) -> None:
    body = "Looks normal " + chr(0x202E) + " backwards\n"
    write(tmp_path / "docs" / "trojan.md", body)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "U+202E" in result.stderr


def test_zero_width_space_is_flagged(tmp_path: Path, runner) -> None:
    body = "valid" + chr(0x200B) + "name\n"
    write(tmp_path / "scripts" / "src.py", body)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "U+200B" in result.stderr


def test_em_dash_in_markdown_warns_not_errors(tmp_path: Path, runner) -> None:
    body = "Hello " + chr(0x2014) + " world\n"
    write(tmp_path / "docs" / "warn.md", body)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0
    assert "U+2014" in result.stdout


def test_em_dash_in_markdown_errors_in_strict_mode(tmp_path: Path, runner) -> None:
    body = "Hello " + chr(0x2014) + " world\n"
    write(tmp_path / "docs" / "warn.md", body)
    result = runner(SCRIPT, tmp_path, ["--strict"])
    assert result.returncode == 1
    assert "U+2014" in result.stderr


def test_em_dash_in_python_source_is_not_warned(tmp_path: Path, runner) -> None:
    body = "# Comment with " + chr(0x2014) + " dash\n"
    write(tmp_path / "scripts" / "x.py", body)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0


def test_bom_in_ps1_is_allowed(tmp_path: Path, runner) -> None:
    bom = chr(0xFEFF).encode("utf-8")
    write_bytes(tmp_path / "scripts" / "x.ps1", bom + b"Write-Host 'ok'\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_bom_in_markdown_is_flagged(tmp_path: Path, runner) -> None:
    bom = chr(0xFEFF).encode("utf-8")
    write_bytes(tmp_path / "docs" / "with_bom.md", bom + b"# Title\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "U+FEFF" in result.stderr
