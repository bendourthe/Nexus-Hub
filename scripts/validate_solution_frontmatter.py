#!/usr/bin/env python3
"""Validate parser-safety of solution-doc YAML frontmatter (stdlib only).

Solution knowledge-base entries (docs/solutions/<category>/<slug>.md, written by
the `solution-knowledge-base` skill and audited by `solution-refresh`) carry a
two-track YAML frontmatter that is read by lightweight stdlib parsers. This
checker enforces the YAML-safety quoting rule documented in
catalog/skills/workflow/solution-knowledge-base/references/schema.md so an entry
never silently mis-parses. It deliberately uses NO PyYAML -- it is a line-level
parser-safety linter, not a schema validator.

It detects four classes of parser hazard:

  1. Malformed `---` delimiter lines (missing opening, trailing characters on a
     delimiter, or a missing closing delimiter).
  2. An unquoted ` #` (space-hash) inside a scalar value -- a YAML comment that
     silently truncates the value.
  3. An unquoted `: ` (colon-space) inside a scalar value -- read as a nested
     mapping instead of the intended string.
  4. A block- or flow-sequence item (or scalar value) that begins with a YAML
     reserved indicator and is not quoted.

Exit codes:
    0 - every scanned file is parser-safe (or there was nothing to scan)
    1 - one or more parser hazards detected (each named on stderr)
    2 - usage / IO error (an explicitly named target does not exist)

Usage:
    python scripts/validate_solution_frontmatter.py
    python scripts/validate_solution_frontmatter.py docs/solutions/bug/foo.md
    python scripts/validate_solution_frontmatter.py --path docs/solutions --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# YAML indicator characters that are unsafe as the first character of an
# unquoted plain scalar or sequence item (a leading `[` / `{` is handled
# separately as an intentional flow collection, so it is excluded here).
RESERVED_START_CHARS = frozenset("!&*?|>%@`,#:")

# Block-scalar indicators: a value of exactly one of these opens a literal /
# folded block whose indented continuation lines are free text, not scalars to
# lint, so we skip them.
BLOCK_SCALAR_INDICATORS = frozenset({"|", ">", "|-", ">-", "|+", ">+"})


class Finding:
    """One parser-safety hazard, with enough context to fix it."""

    def __init__(self, line_no: int, field: str, message: str) -> None:
        self.line_no = line_no
        self.field = field
        self.message = message


def _strip_bom(text: str) -> str:
    """Drop a single leading UTF-8 BOM so delimiter checks do not false-fire."""
    return text[1:] if text and ord(text[0]) == 0xFEFF else text


def _is_quoted(value: str) -> bool:
    """True if a stripped scalar value is wrapped in matching quotes."""
    if len(value) < 2:
        return False
    return (value[0] == '"' and value[-1] == '"') or (
        value[0] == "'" and value[-1] == "'"
    )


def _check_scalar(raw_value: str, line_no: int, field: str) -> list[Finding]:
    """Apply the quoting rules to one scalar region (text after `key:` or `- `).

    `raw_value` is the substring AFTER the delimiter, including its leading
    space, so the ` #` / `: ` checks see the real character sequence a parser
    would. Quoted values are safe and short-circuit.
    """
    findings: list[Finding] = []
    stripped = raw_value.strip()

    # Empty value -> a block parent (sequence / nested mapping follows). Nothing
    # to lint on this line.
    if not stripped:
        return findings

    # Quoted scalars are safe: quoting is exactly the fix this linter asks for.
    if _is_quoted(stripped):
        return findings

    # Intentional inline flow collections are linted element-by-element by the
    # caller, not here.
    if stripped[0] in "[{":
        return findings

    # Rule 2: an unquoted ` #` truncates the value as a comment.
    if " #" in raw_value:
        findings.append(
            Finding(
                line_no,
                field,
                "unquoted ' #' in value (parsed as a comment, truncating it); "
                "quote the whole value",
            )
        )

    # Rule 3: an unquoted `: ` is read as a nested mapping.
    if ": " in stripped or stripped.endswith(":"):
        findings.append(
            Finding(
                line_no,
                field,
                "unquoted ': ' in value (parsed as a nested mapping); "
                "quote the whole value",
            )
        )

    # Rule 4: a leading reserved indicator on an unquoted scalar.
    if stripped[0] in RESERVED_START_CHARS:
        findings.append(
            Finding(
                line_no,
                field,
                f"value begins with reserved YAML indicator '{stripped[0]}' "
                f"and is not quoted",
            )
        )

    return findings


def _check_flow_sequence(inside: str, line_no: int, field: str) -> list[Finding]:
    """Lint each element of an inline `[a, b, c]` sequence (naive comma split)."""
    findings: list[Finding] = []
    for element in inside.split(","):
        item = element.strip()
        if not item or _is_quoted(item):
            continue
        if " #" in element:
            findings.append(
                Finding(line_no, field, f"flow-sequence item '{item}' has an unquoted ' #'")
            )
        if item[0] in RESERVED_START_CHARS:
            findings.append(
                Finding(
                    line_no,
                    field,
                    f"flow-sequence item '{item}' begins with reserved indicator "
                    f"'{item[0]}' and is not quoted",
                )
            )
    return findings


def validate_frontmatter(text: str) -> list[Finding]:
    """Validate the frontmatter of one solution doc. Returns a list of Findings."""
    lines = _strip_bom(text).splitlines()

    if not lines or lines[0].rstrip() != "---":
        if lines and lines[0].startswith("---"):
            return [Finding(1, "frontmatter", "malformed opening '---' delimiter (trailing characters)")]
        return [Finding(1, "frontmatter", "missing opening '---' frontmatter delimiter")]

    # Locate the closing delimiter.
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return [Finding(1, "frontmatter", "missing closing '---' delimiter")]

    findings: list[Finding] = []
    current_field = "frontmatter"
    skip_until_indent: int | None = None

    for offset in range(1, end_idx):
        raw_line = lines[offset]
        line_no = offset + 1  # 1-based real line number
        stripped = raw_line.strip()

        if not stripped:
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        # Inside a block scalar: skip continuation lines indented deeper than
        # the owning key.
        if skip_until_indent is not None:
            if indent > skip_until_indent:
                continue
            skip_until_indent = None

        # Block- or flow-sequence item: `- value`.
        if stripped.startswith("- "):
            findings.extend(_check_scalar(raw_line.split("-", 1)[1][1:], line_no, current_field))
            continue
        if stripped == "-":
            continue

        # Mapping line: split on the FIRST colon. A key with no colon at all is
        # not a mapping line we understand; leave it alone.
        if ":" not in stripped:
            continue
        colon_idx = raw_line.find(":")
        key = raw_line[:colon_idx].strip().strip('"').strip("'")
        if key:
            current_field = key
        raw_value = raw_line[colon_idx + 1:]
        value = raw_value.strip()

        # Block scalar opener: skip its indented continuation.
        if value in BLOCK_SCALAR_INDICATORS:
            skip_until_indent = indent
            continue

        # Inline flow sequence value.
        if value.startswith("[") and value.endswith("]"):
            findings.extend(_check_flow_sequence(value[1:-1], line_no, current_field))
            continue

        findings.extend(_check_scalar(raw_value, line_no, current_field))

    return findings


def iter_target_files(targets: list[Path]) -> tuple[list[Path], list[Path]]:
    """Expand targets into (markdown_files, missing_explicit_targets)."""
    files: list[Path] = []
    missing: list[Path] = []
    for target in targets:
        if target.is_file():
            if target.suffix.lower() == ".md":
                files.append(target)
        elif target.is_dir():
            files.extend(sorted(target.rglob("*.md")))
        else:
            missing.append(target)
    return files, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Solution-doc files or directories to validate.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root; the default scan target is <root>/docs/solutions.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=None,
        help="Additional target file or directory; repeatable.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()

    targets: list[Path] = [Path(p) for p in args.paths]
    if args.path:
        targets.extend(Path(p) for p in args.path)
    if not targets:
        default_target = root / "docs" / "solutions"
        if default_target.exists():
            targets = [default_target]

    if not targets:
        if args.verbose:
            print("validate_solution_frontmatter: nothing to scan (no docs/solutions).")
        return 0

    files, missing = iter_target_files(targets)
    if missing:
        for m in missing:
            print(f"ERROR: target does not exist: {m}", file=sys.stderr)
        return 2

    if args.verbose:
        print(f"Scanning {len(files)} solution doc(s)...")

    total = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        for finding in validate_frontmatter(text):
            print(
                f"{rel}:{finding.line_no}: field '{finding.field}': {finding.message}",
                file=sys.stderr,
            )
            total += 1

    if total:
        print(
            f"\nvalidate_solution_frontmatter: {total} parser-safety finding(s) "
            f"in {len(files)} scanned file(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(
            f"validate_solution_frontmatter: clean "
            f"({len(files)} file(s) scanned, 0 findings)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
