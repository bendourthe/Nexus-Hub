#!/usr/bin/env python3
"""Validate all DevAI-Hub skills for structural compliance and security.

Checks YAML frontmatter, required fields, directory naming, and scans for
hardcoded secrets. Returns exit code 0 if all checks pass (warnings OK),
exit code 1 if any ERROR-level issue is found.

Usage:
    python scripts/validate_skills.py
    python scripts/validate_skills.py --path catalog/skills/framework-specialists/
    python scripts/validate_skills.py --verbose
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_FIELDS = {"name", "description", "summary_l0", "overview_l1"}
OPTIONAL_FRONTMATTER_FIELDS = {"version", "author", "license", "category", "tags"}
SCANNABLE_EXTENSIONS = {
    ".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml",
    ".txt", ".toml", ".cfg", ".ini", ".ps1", ".bash",
}

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Hardcoded Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{50,}")),
    ("GitHub PAT (classic)", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub PAT (fine-grained)", re.compile(r"github_pat_[A-Za-z0-9_]{82}")),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}")),
    ("Generic secret assignment", re.compile(r"""(?:password|secret|token|api_key)\s*=\s*["'][^"']{8,}["']""", re.IGNORECASE)),
]


# ---------------------------------------------------------------------------
# YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Extract YAML frontmatter from a Markdown file (between --- delimiters)."""
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


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_skill_dir(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Validate a single skill directory. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    # Hard rule: SKILL.md must exist
    if not skill_file.exists():
        errors.append(f"{skill_dir}: missing SKILL.md")
        return errors, warnings

    content = skill_file.read_text(encoding="utf-8", errors="replace")

    # Hard rule: YAML frontmatter must parse
    fm = parse_frontmatter(content)
    if fm is None:
        errors.append(f"{skill_file}: no valid YAML frontmatter (must start with ---)")
        return errors, warnings

    # Hard rule: required fields present
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm or not fm[field]:
            errors.append(f"{skill_file}: missing required frontmatter field '{field}'")

    # Hard rule: name must match directory name
    if "name" in fm and fm["name"] != skill_dir.name:
        errors.append(
            f"{skill_file}: frontmatter name '{fm['name']}' does not match "
            f"directory name '{skill_dir.name}'"
        )

    # Soft rule: optional fields
    for field in OPTIONAL_FRONTMATTER_FIELDS:
        if field not in fm:
            warnings.append(f"{skill_file}: missing optional field '{field}'")

    # Hard rule: scan for hardcoded secrets
    secret_errors = scan_for_secrets(skill_dir)
    errors.extend(secret_errors)

    return errors, warnings


def scan_for_secrets(directory: Path) -> list[str]:
    """Scan all scannable files in a directory tree for hardcoded secrets."""
    errors: list[str] = []
    for root, _dirs, files in os.walk(directory):
        for filename in files:
            filepath = Path(root) / filename
            if filepath.suffix.lower() not in SCANNABLE_EXTENSIONS:
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pattern_name, pattern in SECRET_PATTERNS:
                for match in pattern.finditer(text):
                    errors.append(
                        f"{filepath}: potential {pattern_name} detected "
                        f"(line ~{text[:match.start()].count(chr(10)) + 1})"
                    )
    return errors


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_skill_dirs(root: Path) -> list[Path]:
    """Find all directories containing a SKILL.md file."""
    skill_dirs: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            skill_dirs.append(Path(dirpath))
    return sorted(skill_dirs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DevAI-Hub skills")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("catalog/skills"),
        help="Root directory to scan for skills (default: catalog/skills)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show warnings in addition to errors",
    )
    args = parser.parse_args()

    scan_root = args.path
    if not scan_root.exists():
        print(f"ERROR: path does not exist: {scan_root}", file=sys.stderr)
        return 1

    skill_dirs = find_skill_dirs(scan_root)
    if not skill_dirs:
        print(f"WARNING: no SKILL.md files found under {scan_root}", file=sys.stderr)
        return 0

    total_errors: list[str] = []
    total_warnings: list[str] = []

    for skill_dir in skill_dirs:
        errs, warns = validate_skill_dir(skill_dir)
        total_errors.extend(errs)
        total_warnings.extend(warns)

    # Report results
    print(f"Scanned {len(skill_dirs)} skills under {scan_root}")

    if args.verbose and total_warnings:
        print(f"\n--- {len(total_warnings)} WARNING(S) ---")
        for w in total_warnings:
            print(f"  WARN: {w}")

    if total_errors:
        print(f"\n--- {len(total_errors)} ERROR(S) ---")
        for e in total_errors:
            print(f"  ERROR: {e}")
        print(f"\nRESULT: FAIL ({len(total_errors)} errors, {len(total_warnings)} warnings)")
        return 1

    print(f"\nRESULT: PASS (0 errors, {len(total_warnings)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
