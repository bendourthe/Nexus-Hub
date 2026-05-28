#!/usr/bin/env python3
"""Validate Unicode safety across distributed text content.

Detects two classes of issues:

(1) Unsafe / confusable Unicode (ERRORS, exit 1):
    - Bidirectional override and isolate controls (Trojan Source, CVE-2021-42574).
    - Zero-width characters (ZWSP, ZWNJ, ZWJ, BOM, word joiner, ZWNB space).

(2) Non-ASCII punctuation in English Markdown (WARNINGS by default,
    promoted to errors with --strict):
    - Em-dash, en-dash, curly quotes, ellipsis character, non-breaking space.

The strict pass mirrors the global CLAUDE.md "Critical Rules" ASCII-only
constraint for commit messages and English Markdown.

The unsafe character set is constructed from Unicode codepoint integers so the
validator source file itself contains no Trojan-Source or zero-width characters
(and therefore does not self-detect).

Exit codes:
    0 - no errors (warnings may exist; --strict promotes warnings to errors)
    1 - one or more findings classified as errors
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

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
}
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
}
NON_ASCII_PUNCT: dict[str, tuple[str, str]] = {
    chr(cp): val for cp, val in _NON_ASCII_PUNCT_CODEPOINTS.items()
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


def scan_file(
    path: Path,
    check_punctuation: bool,
) -> tuple[list[tuple[int, int, str, str]], list[tuple[int, int, str, str, str]]]:
    """Return (errors, warnings).

    errors  = [(line, col, char_repr, description)]
    warnings = [(line, col, char_repr, name, suggestion)]
    """
    errors: list[tuple[int, int, str, str]] = []
    warnings: list[tuple[int, int, str, str, str]] = []

    try:
        raw = path.read_bytes()
    except OSError:
        return errors, warnings

    bom = chr(0xFEFF).encode("utf-8")
    bom_offset = 0
    if (
        raw.startswith(bom)
        and path.suffix.lower() in BOM_EXEMPT_EXTENSIONS
    ):
        bom_offset = len(bom)

    try:
        text = raw[bom_offset:].decode("utf-8", errors="replace")
    except (UnicodeDecodeError, AttributeError):
        return errors, warnings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for col, ch in enumerate(line, start=1):
            if ch in UNSAFE_CHARS:
                errors.append((line_no, col, f"U+{ord(ch):04X}", UNSAFE_CHARS[ch]))
                continue
            if check_punctuation and ch in NON_ASCII_PUNCT:
                name, suggestion = NON_ASCII_PUNCT[ch]
                warnings.append(
                    (line_no, col, f"U+{ord(ch):04X}", name, suggestion)
                )
    return errors, warnings


def iter_target_files(
    root: Path,
    targets: tuple[str, ...],
    excludes: tuple[Path, ...] = (),
) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        full = root / target
        if not full.exists():
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
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    targets = tuple(args.path) if args.path else DEFAULT_TARGETS
    excludes = tuple(Path(e) for e in (args.exclude or ()))
    files = iter_target_files(root, targets, excludes)

    if args.verbose:
        print(f"Scanning {len(files)} text file(s) under {root}...")

    total_errors = 0
    total_warnings = 0
    for path in files:
        errors, warnings = scan_file(path, check_punctuation=is_english_markdown(path))
        rel = path.relative_to(root)
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
