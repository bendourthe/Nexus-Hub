#!/usr/bin/env python3
"""Validate Unicode safety across distributed text content.

Detects two classes of issues:

(1) Unsafe / confusable Unicode (ERRORS, exit 1):
    - Bidirectional override and isolate controls (Trojan Source, CVE-2021-42574).
    - Zero-width characters (ZWSP, ZWNJ, ZWJ, BOM, word joiner, ZWNB space).
    - Unicode tag characters (U+E0001 and U+E0020-U+E007F), which mirror ASCII
      but render as nothing and are a hidden-text smuggling channel.

(2) Non-ASCII punctuation and space homoglyphs in English Markdown (WARNINGS
    by default, promoted to errors with --strict):
    - Em-dash, en-dash, curly quotes, ellipsis character.
    - Space homoglyphs: no-break space, U+2000-U+200A, ogham space mark,
      narrow no-break space, medium mathematical space, ideographic space.
    - Soft hyphen, which is deleted rather than replaced (it has no width).
    - Variation selectors (U+FE00-U+FE0F and the U+E0100-U+E01EF supplement),
      a steganography channel, also deleted. A VS16 immediately following a
      symbol or keycap base is legitimate emoji presentation and is exempt;
      see `variation_selector_is_legitimate`.

The strict pass mirrors the global CLAUDE.md "Critical Rules" ASCII-only
constraint for commit messages and English Markdown.

The unsafe character set is constructed from Unicode codepoint integers so the
validator source file itself contains no Trojan-Source or zero-width characters
(and therefore does not self-detect).

Reporting is the default. `--fix` additionally repairs findings in place: hard
errors are always removed, the strict-class replacements apply only when
`--strict` is also passed, writes are atomic, and each repaired file is
re-scanned so a residual finding still exits 1.

Exit codes:
    0 - no errors (warnings may exist; --strict promotes warnings to errors)
    1 - one or more findings classified as errors
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import NamedTuple

_UNSAFE_CODEPOINTS: dict[int, str] = {
    0x202A: "LEFT-TO-RIGHT EMBEDDING (bidi override)",
    0x202B: "RIGHT-TO-LEFT EMBEDDING (bidi override)",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE (Trojan Source)",
    0x202E: "RIGHT-TO-LEFT OVERRIDE (Trojan Source)",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER (invisible)",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM",
    0xE0001: "LANGUAGE TAG (invisible tag character)",
}
# Unicode tag characters U+E0020-U+E007F mirror printable ASCII but render as
# nothing, so an arbitrary hidden message can be smuggled inside visible text.
# They are never legitimate in this repository's content, which is why they are
# hard errors alongside the zero-width set rather than strict-mode warnings.
# The description carries the mirrored ASCII character so a reader can recover
# smuggled text straight from the report.
_UNSAFE_CODEPOINTS.update({
    cp: f"TAG character mirroring {chr(cp - 0xE0000)!r} (invisible)"
    for cp in range(0xE0020, 0xE0080)
})
UNSAFE_CHARS: dict[str, str] = {chr(cp): desc for cp, desc in _UNSAFE_CODEPOINTS.items()}

_NON_ASCII_PUNCT_CODEPOINTS: dict[int, tuple[str, str]] = {
    0x2014: ("EM DASH", "-- or ()"),
    0x2013: ("EN DASH", "- or --"),
    0x2018: ("LEFT SINGLE QUOTATION MARK", "'"),
    0x2019: ("RIGHT SINGLE QUOTATION MARK", "'"),
    0x201C: ("LEFT DOUBLE QUOTATION MARK", '"'),
    0x201D: ("RIGHT DOUBLE QUOTATION MARK", '"'),
    0x2026: ("HORIZONTAL ELLIPSIS", "..."),
    0x00A0: ("NO-BREAK SPACE", "regular space"),
    0x00AD: ("SOFT HYPHEN", "remove"),
    0x1680: ("OGHAM SPACE MARK", "regular space"),
    0x202F: ("NARROW NO-BREAK SPACE", "regular space"),
    0x205F: ("MEDIUM MATHEMATICAL SPACE", "regular space"),
    0x3000: ("IDEOGRAPHIC SPACE", "regular space"),
}
# Variation selectors are a steganography channel: the 240-value supplement
# block in particular encodes one byte per selector, so an arbitrary payload
# can ride invisibly behind ordinary text. They stay in the warn-by-default
# class rather than the hard-error class because VS16 has a large legitimate
# population (emoji presentation), guarded by the base-aware exemption in
# `variation_selector_is_legitimate`.
_NON_ASCII_PUNCT_CODEPOINTS.update({
    cp: (f"VARIATION SELECTOR-{cp - 0xFE00 + 1}", "remove")
    for cp in range(0xFE00, 0xFE10)
})
_NON_ASCII_PUNCT_CODEPOINTS.update({
    cp: (f"VARIATION SELECTOR-{cp - 0xE0100 + 17}", "remove")
    for cp in range(0xE0100, 0xE01F0)
})
# U+2000-U+200A are the general-punctuation space homoglyphs. Unlike the tag
# characters above they can appear in legitimate non-English typography, so
# they follow the warn-by-default / --strict promotion path and inherit the
# existing exemption that applies punctuation rules to Markdown only.
_NON_ASCII_PUNCT_CODEPOINTS.update({
    cp: (name, "regular space")
    for cp, name in {
        0x2000: "EN QUAD",
        0x2001: "EM QUAD",
        0x2002: "EN SPACE",
        0x2003: "EM SPACE",
        0x2004: "THREE-PER-EM SPACE",
        0x2005: "FOUR-PER-EM SPACE",
        0x2006: "SIX-PER-EM SPACE",
        0x2007: "FIGURE SPACE",
        0x2008: "PUNCTUATION SPACE",
        0x2009: "THIN SPACE",
        0x200A: "HAIR SPACE",
    }.items()
})
NON_ASCII_PUNCT: dict[str, tuple[str, str]] = {
    chr(cp): val for cp, val in _NON_ASCII_PUNCT_CODEPOINTS.items()
}

# Machine-applicable replacement for each strict-mode codepoint, used only by
# --fix. It is kept separate from the human-readable suggestion above because a
# suggestion like "-- or ()" is advice, not a substitution. A drift guard in
# tests/validators/test_validate_unicode_safety.py asserts the two tables cover
# exactly the same codepoints.
_FIX_REPLACEMENTS: dict[int, str] = {
    0x2014: "--",
    0x2013: "-",
    0x2018: "'",
    0x2019: "'",
    0x201C: '"',
    0x201D: '"',
    0x2026: "...",
    0x00A0: " ",
    0x00AD: "",
    0x1680: " ",
    0x202F: " ",
    0x205F: " ",
    0x3000: " ",
}
_FIX_REPLACEMENTS.update({cp: " " for cp in range(0x2000, 0x200B)})
_FIX_REPLACEMENTS.update({cp: "" for cp in range(0xFE00, 0xFE10)})
_FIX_REPLACEMENTS.update({cp: "" for cp in range(0xE0100, 0xE01F0)})
PUNCT_FIX_REPLACEMENTS: dict[str, str] = {
    chr(cp): repl for cp, repl in _FIX_REPLACEMENTS.items()
}

# PowerShell scripts conventionally start with a UTF-8 BOM so Windows PowerShell
# 5.1 interprets them as UTF-8 rather than the system ANSI code page. We exempt
# a leading BOM in `.ps1` files only.
BOM_EXEMPT_EXTENSIONS: frozenset[str] = frozenset({".ps1"})

DEFAULT_TARGETS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "catalog",
    "docs",
    "templates",
    "scripts",
)

EXEMPT_DIR_PARTS: frozenset[str] = frozenset({
    "archive",
    # v4.0.0 renamed the frozen container to the plural form. Frozen release
    # snapshots are exempt because they are historical records, not text the
    # project is still free to reword; both spellings are listed so a consuming
    # repo on the legacy singular tree behaves identically.
    "archives",
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
})

TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh",
    ".ps1", ".js", ".ts", ".cfg", ".ini", ".rst", ".bash",
})

MARKDOWN_EXTENSIONS: frozenset[str] = frozenset({".md"})


def path_is_excluded(path: Path, root: Path, excludes: tuple[Path, ...]) -> bool:
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return False
    for ex in excludes:
        try:
            rel.relative_to(ex)
            return True
        except ValueError:
            continue
    return False


def in_exempt_dir(path: Path) -> bool:
    return any(part in EXEMPT_DIR_PARTS for part in path.parts)


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if path.suffix == "" and path.name.isupper():
        return True
    return False


def is_english_markdown(path: Path) -> bool:
    return path.suffix.lower() in MARKDOWN_EXTENSIONS


_VS16 = chr(0xFE0F)
_KEYCAP_BASES: frozenset[str] = frozenset("#*0123456789")


def variation_selector_is_legitimate(selector: str, base: str) -> bool:
    """True when `selector` is a legitimate variation selector after `base`.

    VS16 selects emoji presentation for a base character that defaults to text
    presentation, so it is legitimate immediately after a symbol (Unicode
    general category So or Sk) or after a keycap base. Anywhere else -- after a
    letter, after a space, after another selector, or at the start of a line --
    a variation selector is a stray invisible character and is reported.

    Only VS16 is exempted. VS1-VS15 and the U+E0100-U+E01EF supplement have no
    legitimate use in this repository's content and are always reported. Known
    limitation: a CJK ideographic variation sequence (VS1-VS3 after an
    ideograph) would be reported; it stays a warning unless --strict is passed.
    """
    if selector != _VS16 or not base:
        return False
    if base in _KEYCAP_BASES:
        return True
    return unicodedata.category(base) in {"So", "Sk"}


def punct_finding_applies(ch: str, base: str) -> bool:
    """Shared detect/repair policy for one strict-class character."""
    return not variation_selector_is_legitimate(ch, base)


class FileText(NamedTuple):
    """A file decoded for scanning, or the reason it could not be."""

    bom_prefix: bytes
    text: str | None
    io_error: str | None


def read_text_for_scan(path: Path) -> FileText:
    """Read and strictly decode a file.

    A strict decode (rather than errors="replace") is required because --fix
    writes the decoded text back: replacing undecodable bytes with U+FFFD and
    then writing would silently corrupt the file. Both modes therefore report
    an undecodable or unreadable file rather than skipping it silently.
    """
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return FileText(b"", None, f"cannot read file: {exc.strerror or exc}")

    bom = chr(0xFEFF).encode("utf-8")
    bom_prefix = b""
    if raw.startswith(bom) and path.suffix.lower() in BOM_EXEMPT_EXTENSIONS:
        bom_prefix = bom

    try:
        text = raw[len(bom_prefix):].decode("utf-8")
    except UnicodeDecodeError as exc:
        return FileText(bom_prefix, None, f"not valid UTF-8: {exc}")
    return FileText(bom_prefix, text, None)


def scan_text(
    text: str,
    check_punctuation: bool,
) -> tuple[list[tuple[int, int, str, str]], list[tuple[int, int, str, str, str]]]:
    """Return (errors, warnings).

    errors  = [(line, col, char_repr, description)]
    warnings = [(line, col, char_repr, name, suggestion)]
    """
    errors: list[tuple[int, int, str, str]] = []
    warnings: list[tuple[int, int, str, str, str]] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        previous = ""
        for col, ch in enumerate(line, start=1):
            base, previous = previous, ch
            if ch in UNSAFE_CHARS:
                errors.append((line_no, col, f"U+{ord(ch):04X}", UNSAFE_CHARS[ch]))
                continue
            if (
                check_punctuation
                and ch in NON_ASCII_PUNCT
                and punct_finding_applies(ch, base)
            ):
                name, suggestion = NON_ASCII_PUNCT[ch]
                warnings.append(
                    (line_no, col, f"U+{ord(ch):04X}", name, suggestion)
                )
    return errors, warnings


def repair_text(text: str, fix_punctuation: bool) -> tuple[str, int, int]:
    """Return (repaired_text, chars_removed, chars_replaced).

    Applies the same per-character policy `scan_text` reports on, so a repaired
    string cannot retain a finding the scanner would flag. Newline characters
    are never touched, so the caller's original line endings survive verbatim.
    """
    out: list[str] = []
    removed = 0
    replaced = 0
    previous = ""
    for ch in text:
        base, previous = previous, ch
        if ch in UNSAFE_CHARS:
            removed += 1
            continue
        if (
            fix_punctuation
            and ch in NON_ASCII_PUNCT
            and punct_finding_applies(ch, base)
        ):
            out.append(PUNCT_FIX_REPLACEMENTS[ch])
            replaced += 1
            continue
        out.append(ch)
    return "".join(out), removed, replaced


def atomic_write(path: Path, data: bytes) -> None:
    """Replace `path` with `data` via a same-directory temp file and rename.

    A same-directory temp file keeps the rename atomic (os.replace is only
    atomic within one filesystem), so a crash or a concurrent --fix run leaves
    either the original or one run's complete output, never a partial file.
    """
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        # mkstemp creates 0600; carry the original mode over so a fixed .sh
        # does not silently lose its executable bit.
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def display_path(path: Path, root: Path) -> str:
    """Path for reporting, relative to root when possible.

    An explicit --path may point outside --root, so this must not assume the
    two are related; `relative_to` would raise for such a file.
    """
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_target_files(
    root: Path,
    targets: tuple[str, ...],
    excludes: tuple[Path, ...] = (),
    missing: list[str] | None = None,
) -> list[Path]:
    """Collect scannable files under `targets`.

    A target that does not exist is skipped, and recorded in `missing` when a
    list is supplied. Callers pass a list only for explicitly requested paths:
    a missing default target is normal (not every repo has AGENTS.md), but a
    missing explicit target means the caller scanned nothing it asked for, and
    reporting "clean" there would be a silent no-op.
    """
    files: list[Path] = []
    for target in targets:
        full = root / target
        if not full.exists():
            if missing is not None:
                missing.append(target)
            continue
        if full.is_file():
            if (
                is_text_file(full)
                and not in_exempt_dir(full)
                and not path_is_excluded(full, root, excludes)
            ):
                files.append(full)
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIR_PARTS]
            current = Path(dirpath)
            dirnames[:] = [
                d for d in dirnames
                if not path_is_excluded(current / d, root, excludes)
            ]
            for name in filenames:
                candidate = current / name
                if not is_text_file(candidate):
                    continue
                if in_exempt_dir(candidate):
                    continue
                if path_is_excluded(candidate, root, excludes):
                    continue
                files.append(candidate)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root.",
    )
    parser.add_argument("--path", action="append", default=None)
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Exclude a path (relative to --root) from scanning; repeatable.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote non-ASCII punctuation warnings (Markdown only) to errors.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=(
            "Repair findings in place instead of only reporting them: remove "
            "unsafe characters, and with --strict also apply the ASCII "
            "punctuation replacements. Files are re-scanned after writing and "
            "any residual finding still exits 1."
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    explicit_targets = bool(args.path)
    targets = tuple(args.path) if explicit_targets else DEFAULT_TARGETS
    excludes = tuple(Path(e) for e in (args.exclude or ()))
    missing: list[str] = []
    files = iter_target_files(
        root, targets, excludes, missing if explicit_targets else None
    )
    if missing:
        for target in missing:
            print(
                f"ERROR: --path target not found under {root}: {target}",
                file=sys.stderr,
            )
        return 2

    if args.verbose:
        print(f"Scanning {len(files)} text file(s) under {root}...")

    total_errors = 0
    total_warnings = 0
    io_failures = 0
    fixed_files = 0
    for path in files:
        rel = display_path(path, root)
        check_punctuation = is_english_markdown(path)
        bom_prefix, text, io_error = read_text_for_scan(path)
        if text is None:
            print(f"{rel}: IO: {io_error}", file=sys.stderr)
            io_failures += 1
            continue

        if args.fix:
            # Punctuation repair is gated on the same predicate that gates
            # punctuation detection, so the Markdown-only exemption that keeps
            # non-English content out of the strict pass also keeps it out of
            # the rewrite path.
            fixed, removed, replaced = repair_text(
                text, fix_punctuation=args.strict and check_punctuation
            )
            if fixed != text:
                try:
                    atomic_write(path, bom_prefix + fixed.encode("utf-8"))
                except OSError as exc:
                    print(f"{rel}: IO: cannot write file: {exc}", file=sys.stderr)
                    io_failures += 1
                    continue
                fixed_files += 1
                print(
                    f"FIXED {rel}: {removed} unsafe character(s) removed, "
                    f"{replaced} punctuation replacement(s)."
                )
                # Re-read from disk so the findings below describe the file as
                # it now exists, not an in-memory projection of it.
                bom_prefix, text, io_error = read_text_for_scan(path)
                if text is None:
                    print(f"{rel}: IO: {io_error}", file=sys.stderr)
                    io_failures += 1
                    continue

        errors, warnings = scan_text(text, check_punctuation)
        for line, col, code, desc in errors:
            print(
                f"{rel}:{line}:{col}: unsafe Unicode {code} ({desc})",
                file=sys.stderr,
            )
            total_errors += 1
        for line, col, code, name, suggestion in warnings:
            stream = sys.stderr if args.strict else sys.stdout
            label = "ERROR" if args.strict else "WARN"
            print(
                f"{rel}:{line}:{col}: {label}: non-ASCII punctuation "
                f"{code} {name} -- use {suggestion}",
                file=stream,
            )
            if args.strict:
                total_errors += 1
            else:
                total_warnings += 1

    if args.fix:
        print(f"validate_unicode_safety: repaired {fixed_files} file(s).")

    # An unreadable or undecodable file is an IO condition, not a content
    # finding, so it takes the exit-2 branch even when findings also exist.
    if io_failures:
        print(
            f"\nvalidate_unicode_safety: {io_failures} file(s) could not be "
            f"read or decoded; {total_errors} error(s) and {total_warnings} "
            f"warning(s) in the {len(files) - io_failures} file(s) scanned.",
            file=sys.stderr,
        )
        return 2

    if total_errors:
        print(
            f"\nvalidate_unicode_safety: {total_errors} error(s), "
            f"{total_warnings} warning(s) across {len(files)} file(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(
            f"validate_unicode_safety: clean "
            f"({len(files)} file(s) scanned, "
            f"{total_warnings} warning(s), 0 errors)."
        )
    elif total_warnings:
        print(
            f"validate_unicode_safety: 0 errors, {total_warnings} warning(s)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
