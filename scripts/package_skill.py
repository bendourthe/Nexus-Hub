#!/usr/bin/env python3
"""Package a DevAI-Hub skill into a portable ``.skill`` archive.

A ``.skill`` file is a plain ZIP archive whose root contains the skill's
``SKILL.md`` plus any of the per-skill bundled subdirectories that follow the
AGENTS.md "Per-skill Bundled Resources" convention (``scripts/``,
``references/``, ``assets/``, and any sibling subdirs that already live
alongside SKILL.md, e.g. ``themes/``, ``templates/``, ``examples/``,
``agents/``).

The packager validates the SKILL.md frontmatter before zipping. It refuses to
emit an archive if ``name`` or ``description`` are missing - those are the two
fields any downstream consumer (Claude.ai upload, Anthropic API skill upload,
or another DevAI-Hub installation) needs at minimum to display and dispatch
the skill.

Phase 7 / A16 of docs/v1.1.5/plans/adoption-skills.md. The ``.skill`` archive
is intended to round-trip through ``unzip <name>.skill -d <dest>`` so the
extracted layout matches a fresh ``catalog/skills/<cat>/<name>/`` directory.

Usage:
    python scripts/package_skill.py catalog/skills/workflow/skill-eval-loop
    python scripts/package_skill.py catalog/skills/workflow/skill-eval-loop \\
        --output dist/skill-eval-loop.skill
    python scripts/package_skill.py path/to/skill --validate-only

Exit codes:
    0  success (or successful validation under ``--validate-only``)
    1  invalid frontmatter, missing SKILL.md, or other packaging error
    2  CLI usage error (handled by argparse)
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

# Frontmatter fields the consumer absolutely needs. ``summary_l0`` /
# ``overview_l1`` are validated as warnings (they are required by the
# DevAI-Hub catalog convention but a packaged ``.skill`` upload to a
# non-DevAI-Hub consumer does not strictly need them).
REQUIRED_FRONTMATTER_FIELDS = ("name", "description")
RECOMMENDED_FRONTMATTER_FIELDS = ("summary_l0", "overview_l1")


def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Extract YAML frontmatter from a Markdown file (between ``---`` delimiters).

    Mirrors the parser in scripts/validate_skills.py to keep behavior aligned
    without taking a dependency on a YAML library.
    """
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    raw = content[3:end].strip()
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def validate_skill_md(skill_md: Path) -> tuple[dict[str, str], list[str]]:
    """Read SKILL.md, parse frontmatter, and report problems.

    Returns ``(frontmatter, errors)``. ``errors`` is a list of human-readable
    strings; an empty list means the SKILL.md is valid for packaging.
    """
    errors: list[str] = []
    if not skill_md.is_file():
        return ({}, [f"SKILL.md not found at {skill_md}"])

    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return ({}, [f"SKILL.md is not valid UTF-8: {exc}"])

    frontmatter = parse_frontmatter(content)
    if frontmatter is None:
        return ({}, [f"SKILL.md does not start with a YAML frontmatter block (---)"])

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if not frontmatter.get(field):
            errors.append(f"SKILL.md frontmatter missing required field: {field}")

    name = frontmatter.get("name", "")
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        errors.append(
            f"SKILL.md frontmatter `name` must be kebab-case "
            f"(lowercase letters, digits, hyphens; got {name!r})"
        )

    return frontmatter, errors


def collect_payload(skill_dir: Path) -> list[Path]:
    """Return every file under ``skill_dir`` that should be packaged.

    Includes SKILL.md plus every file under any subdirectory of the skill
    folder. Exclusions: ``__pycache__``, ``.DS_Store``, files whose name starts
    with a tilde (Windows lock files), and ``.gitkeep`` placeholders (those
    exist only to track empty subdirs in git and do not need to ship in the
    distributable archive).
    """
    payload: list[Path] = []
    for entry in skill_dir.rglob("*"):
        if not entry.is_file():
            continue
        # Skip housekeeping artifacts that should not ship in a portable archive.
        if entry.name in (".DS_Store", ".gitkeep"):
            continue
        if entry.name.startswith("~"):
            continue
        if "__pycache__" in entry.parts:
            continue
        payload.append(entry)
    return payload


def package_skill(
    skill_dir: Path,
    output_path: Path | None = None,
    validate_only: bool = False,
) -> Path | None:
    """Validate and package a single skill directory.

    Returns the path to the produced archive on success, or ``None`` when
    ``validate_only`` is set. Raises ``SystemExit(1)`` on validation or I/O
    failure with a clear stderr message.
    """
    if not skill_dir.is_dir():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        raise SystemExit(1)

    skill_md = skill_dir / "SKILL.md"
    frontmatter, errors = validate_skill_md(skill_md)
    if errors:
        print("Error: SKILL.md validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        raise SystemExit(1)

    skill_name = frontmatter.get("name") or skill_dir.name

    # Surface recommended-but-not-required gaps as informational lines (still
    # exit 0 for them - the AGENTS.md catalog rule covers those, but a
    # ``.skill`` upload should not be blocked on them).
    for field in RECOMMENDED_FRONTMATTER_FIELDS:
        if not frontmatter.get(field):
            print(
                f"Note: SKILL.md frontmatter missing recommended field "
                f"{field!r}; archive will still be produced."
            )

    if validate_only:
        print(f"OK: {skill_md} validates as a packageable skill ({skill_name}).")
        return None

    if output_path is None:
        output_path = Path.cwd() / f"{skill_name}.skill"
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = collect_payload(skill_dir)
    if not payload:
        print(
            f"Error: skill directory {skill_dir} contains no packageable files",
            file=sys.stderr,
        )
        raise SystemExit(1)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in sorted(payload):
            arcname = src.relative_to(skill_dir).as_posix()
            zf.write(src, arcname)

    print(f"Packaged {len(payload)} file(s) -> {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package a DevAI-Hub skill into a portable .skill archive.",
    )
    parser.add_argument(
        "skill_dir",
        type=Path,
        help="Path to a skill directory (must contain SKILL.md).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output archive path. Defaults to ./<skill-name>.skill.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate SKILL.md frontmatter without writing an archive.",
    )
    args = parser.parse_args(argv)

    package_skill(
        skill_dir=args.skill_dir.resolve(),
        output_path=args.output.resolve() if args.output else None,
        validate_only=args.validate_only,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
