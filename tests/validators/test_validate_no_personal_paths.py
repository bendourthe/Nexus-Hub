"""Tests for scripts/validate_no_personal_paths.py."""

from __future__ import annotations

from pathlib import Path


SCRIPT = "validate_no_personal_paths.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_clean_tree_passes(tmp_path: Path, runner) -> None:
    write(tmp_path / "docs" / "README.md", "Run `npm install` and then `make build`.\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_posix_personal_path_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "docs" / "leak.md",
        "Open the file at /Users/jdoe/code/secrets.txt and edit it.\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "/Users/jdoe" in result.stderr
    assert "jdoe" in result.stderr


def test_windows_personal_path_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "catalog" / "ex.md",
        r"Sample path: C:\Users\janedoe\Downloads\project on the laptop." + "\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "janedoe" in result.stderr


def test_home_personal_path_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "templates" / "demo.md",
        "Replace /home/realuser/.config/app.yml with your file.\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "realuser" in result.stderr


def test_placeholder_username_is_allowed(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "docs" / "ok.md",
        "Set this to /Users/example/config or /home/username/.bashrc.\n"
        r"On Windows: C:\Users\testuser\AppData." + "\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_angle_bracket_placeholder_is_allowed(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "docs" / "ok.md",
        "Replace /Users/<you>/path with your real path.\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0


def test_exclude_skips_directory(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "docs" / "v0.1.0" / "old.md",
        "/Users/realname/old/path\n",
    )
    write(
        tmp_path / "docs" / "v0.2.0" / "new.md",
        "Use /Users/example/path.\n",
    )
    leaky = runner(SCRIPT, tmp_path)
    assert leaky.returncode == 1
    clean = runner(SCRIPT, tmp_path, ["--exclude", "docs/v0.1.0"])
    assert clean.returncode == 0, clean.stderr


def test_non_text_file_is_skipped(tmp_path: Path, runner) -> None:
    binary = tmp_path / "docs" / "image.png"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"\x89PNG\r\n\x1a\n" + b"/Users/realuser/x")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0
