"""Tests for scripts/validate_unicode_safety.py."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


SCRIPT = "validate_unicode_safety.py"

ZWSP = chr(0x200B)
RLO = chr(0x202E)
EM_DASH = chr(0x2014)
CURLY_OPEN = chr(0x201C)
CURLY_CLOSE = chr(0x201D)
TAG_A = chr(0xE0041)
LANGUAGE_TAG = chr(0xE0001)
EN_SPACE = chr(0x2002)
IDEOGRAPHIC_SPACE = chr(0x3000)
SOFT_HYPHEN = chr(0x00AD)
VS16 = chr(0xFE0F)
VS1 = chr(0xFE00)
VS_SUPPLEMENT = chr(0xE0100)
WARNING_SIGN = chr(0x26A0)


def load_validator(scripts_dir: Path):
    """Import the validator as a module for table- and unit-level assertions.

    The other tests drive the CLI as a subprocess (the surface users run). A
    few invariants are about internal tables rather than behavior, so those
    import the module directly.
    """
    spec = importlib.util.spec_from_file_location(
        "validate_unicode_safety", scripts_dir / SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


# ---------------------------------------------------------------------------
# Extended character coverage (sub-task 1.1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("char", "code"),
    [(TAG_A, "U+E0041"), (LANGUAGE_TAG, "U+E0001")],
)
def test_tag_characters_are_hard_errors(
    tmp_path: Path, runner, char: str, code: str
) -> None:
    """Tag characters smuggle hidden text and are never legitimate here."""
    write(tmp_path / "docs" / "tagged.md", "Visible text" + char + "\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert code in result.stderr


@pytest.mark.parametrize(
    ("char", "code"),
    [
        (EN_SPACE, "U+2002"),
        (IDEOGRAPHIC_SPACE, "U+3000"),
        (SOFT_HYPHEN, "U+00AD"),
        (VS1, "U+FE00"),
        (VS_SUPPLEMENT, "U+E0100"),
        (chr(0x1680), "U+1680"),
        (chr(0x202F), "U+202F"),
        (chr(0x205F), "U+205F"),
    ],
)
def test_strict_class_characters_warn_then_error(
    tmp_path: Path, runner, char: str, code: str
) -> None:
    """Each strict-class addition warns by default and errors under --strict."""
    write(tmp_path / "docs" / "spacey.md", "Hello" + char + "world\n")

    warn = runner(SCRIPT, tmp_path)
    assert warn.returncode == 0, warn.stderr
    assert code in warn.stdout

    strict = runner(SCRIPT, tmp_path, ["--strict"])
    assert strict.returncode == 1
    assert code in strict.stderr


def test_stray_variation_selector_16_is_flagged(tmp_path: Path, runner) -> None:
    """A VS16 with no emoji base is a stray invisible character."""
    write(tmp_path / "docs" / "stray.md", "plain" + VS16 + "text\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0
    assert "U+FE0F" in result.stdout


def test_variation_selector_16_after_emoji_base_is_exempt(
    tmp_path: Path, runner
) -> None:
    """Emoji presentation is legitimate and must not be reported."""
    write(tmp_path / "docs" / "emoji.md", "Warning " + WARNING_SIGN + VS16 + " here\n")
    result = runner(SCRIPT, tmp_path, ["--strict"])
    assert result.returncode == 0, result.stderr
    assert "U+FE0F" not in result.stdout + result.stderr


def test_fix_table_covers_every_strict_codepoint(scripts_dir: Path) -> None:
    """Guard against drift between the detection table and the fix table."""
    module = load_validator(scripts_dir)
    assert set(module.NON_ASCII_PUNCT) == set(module.PUNCT_FIX_REPLACEMENTS)


def test_unsafe_and_strict_sets_are_disjoint(scripts_dir: Path) -> None:
    """A character must be a hard error or a strict finding, never both."""
    module = load_validator(scripts_dir)
    assert not set(module.UNSAFE_CHARS) & set(module.NON_ASCII_PUNCT)


def test_repair_output_has_no_findings(scripts_dir: Path) -> None:
    """The repair pass must satisfy the scan pass it shares a policy with."""
    module = load_validator(scripts_dir)
    dirty = (
        "Text" + ZWSP + RLO + TAG_A + EM_DASH + CURLY_OPEN + "q" + CURLY_CLOSE
        + EN_SPACE + SOFT_HYPHEN + VS1 + VS_SUPPLEMENT + VS16 + "\n"
        + WARNING_SIGN + VS16 + " kept\n"
    )
    fixed, _, _ = module.repair_text(dirty, fix_punctuation=True)
    errors, warnings = module.scan_text(fixed, check_punctuation=True)
    assert errors == []
    assert warnings == []
    assert WARNING_SIGN + VS16 in fixed


# ---------------------------------------------------------------------------
# Fix mode (sub-task 1.2)
# ---------------------------------------------------------------------------


def test_fix_removes_unsafe_characters(tmp_path: Path, runner) -> None:
    target = tmp_path / "docs" / "dirty.md"
    write(target, "before" + ZWSP + "after" + RLO + TAG_A + "\n")
    result = runner(SCRIPT, tmp_path, ["--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == "beforeafter\n"


def test_fix_without_strict_leaves_punctuation(tmp_path: Path, runner) -> None:
    """--fix alone repairs hard errors only; punctuation needs --strict."""
    target = tmp_path / "docs" / "mixed.md"
    write(target, "a" + ZWSP + "b " + EM_DASH + " c\n")
    result = runner(SCRIPT, tmp_path, ["--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == "ab " + EM_DASH + " c\n"


def test_strict_fix_replaces_punctuation(tmp_path: Path, runner) -> None:
    target = tmp_path / "docs" / "punct.md"
    write(
        target,
        "a " + EM_DASH + " b " + CURLY_OPEN + "q" + CURLY_CLOSE
        + " c" + chr(0x2026) + EN_SPACE + "d\n",
    )
    result = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == 'a -- b "q" c... d\n'


def test_strict_fix_preserves_emoji_variation_selector(
    tmp_path: Path, runner
) -> None:
    target = tmp_path / "docs" / "emoji.md"
    body = "Note " + WARNING_SIGN + VS16 + " and stray" + VS16 + "\n"
    write(target, body)
    result = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == (
        "Note " + WARNING_SIGN + VS16 + " and stray\n"
    )


def test_fix_does_not_rewrite_punctuation_outside_markdown(
    tmp_path: Path, runner
) -> None:
    """The Markdown-only punctuation exemption also gates the rewrite path."""
    target = tmp_path / "scripts" / "note.py"
    write(target, "# dash " + EM_DASH + " and zwsp" + ZWSP + "\n")
    result = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_text(encoding="utf-8") == "# dash " + EM_DASH + " and zwsp\n"


def test_fix_preserves_ps1_bom(tmp_path: Path, runner) -> None:
    bom = chr(0xFEFF).encode("utf-8")
    target = tmp_path / "scripts" / "x.ps1"
    write_bytes(target, bom + ("Write-Host 'ok'" + ZWSP + "\n").encode("utf-8"))
    result = runner(SCRIPT, tmp_path, ["--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == bom + b"Write-Host 'ok'\n"


def test_fix_preserves_crlf_line_endings(tmp_path: Path, runner) -> None:
    target = tmp_path / "docs" / "crlf.md"
    write_bytes(target, ("line one" + ZWSP + "\r\nline two\r\n").encode("utf-8"))
    result = runner(SCRIPT, tmp_path, ["--fix"])
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == b"line one\r\nline two\r\n"


def test_fix_does_not_rewrite_clean_file(tmp_path: Path, runner) -> None:
    target = tmp_path / "docs" / "clean.md"
    write(target, "Nothing to repair here.\n")
    before = target.stat().st_mtime_ns
    result = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert result.returncode == 0, result.stderr
    assert target.stat().st_mtime_ns == before
    assert "repaired 0 file(s)" in result.stdout


def test_fix_revalidates_and_reports_clean(tmp_path: Path, runner) -> None:
    write(tmp_path / "docs" / "a.md", "x" + ZWSP + EM_DASH + "\n")
    fix = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert fix.returncode == 0, fix.stderr
    assert "repaired 1 file(s)" in fix.stdout

    recheck = runner(SCRIPT, tmp_path, ["--strict"])
    assert recheck.returncode == 0, recheck.stderr


def test_undecodable_file_reports_io_error_and_is_not_written(
    tmp_path: Path, runner
) -> None:
    target = tmp_path / "docs" / "latin1.md"
    original = b"caf\xe9 text\n"
    write_bytes(target, original)
    result = runner(SCRIPT, tmp_path, ["--strict", "--fix"])
    assert result.returncode == 2
    assert "not valid UTF-8" in result.stderr
    assert target.read_bytes() == original


# ---------------------------------------------------------------------------
# --path resolution (the gate surfaces in v3.16.8 Phase 2 depend on this)
# ---------------------------------------------------------------------------


def test_missing_explicit_path_is_an_error_not_a_silent_pass(
    tmp_path: Path, runner
) -> None:
    """A gate that scans nothing must not report success.

    A --path target that does not exist under --root used to be skipped, so the
    run exited 0 having scanned no file at all. A caller wiring this as a
    pre-commit gate would see a pass and ship the very content the gate exists
    to catch.
    """
    write(tmp_path / "docs" / "real.md", "Clean.\n")
    result = runner(SCRIPT, tmp_path, ["--strict", "--path", "docs/nope.md"])
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_missing_default_target_is_still_tolerated(tmp_path: Path, runner) -> None:
    """Not every repository has every default target; that is not an error."""
    write(tmp_path / "docs" / "only.md", "Clean.\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_absolute_path_outside_root_is_reported_not_crashed(
    tmp_path: Path, runner
) -> None:
    """An explicit path need not live under --root."""
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "stray.md"
    write(target, "text" + ZWSP + "\n")
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)

    result = runner(SCRIPT, root, ["--path", str(target)])
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "U+200B" in result.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes only")
def test_fix_preserves_executable_bit(tmp_path: Path, runner) -> None:
    target = tmp_path / "scripts" / "run.sh"
    write(target, "#!/usr/bin/env bash\necho ok" + ZWSP + "\n")
    target.chmod(0o755)
    result = runner(SCRIPT, tmp_path, ["--fix"])
    assert result.returncode == 0, result.stderr
    assert os.stat(target).st_mode & 0o111
