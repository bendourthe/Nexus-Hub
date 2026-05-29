#!/usr/bin/env python3
"""Validate all Nexus-Hub skills for structural compliance and security.

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

# Per-skill bundled-resource subdirectories per the AGENTS.md
# "Per-skill Bundled Resources" convention.
BUNDLED_SUBDIRS = ("scripts", "references", "assets")
BUNDLE_EXEMPT_FILENAMES = {".gitkeep"}

# Quality-heuristics thresholds (Tier-1 field limits from AGENTS.md "Write SKILL.md").
QUALITY_SUMMARY_L0_MAX_WORDS = 15
QUALITY_OVERVIEW_L1_MAX_WORDS = 150
QUALITY_CHECKLIST_MAX = 6

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

    # Soft rule: per-skill bundled-resource orphan detection
    bundle_warnings = validate_skill_bundles(skill_dir, content)
    warnings.extend(bundle_warnings)

    return errors, warnings


def validate_skill_bundles(skill_dir: Path, skill_md_content: str) -> list[str]:
    """Detect orphan files under per-skill scripts/, references/, assets/ subdirs.

    Per the AGENTS.md "Per-skill Bundled Resources" convention, every file
    under these subdirectories must be referenced at least once from SKILL.md
    (or from another reference file in the same bundle that is itself
    referenced from SKILL.md). Files named `.gitkeep` are exempt because they
    are placeholders for future expansion.

    Returns a list of warning strings (never errors -- a work-in-progress
    branch may legitimately have an unreferenced file). The caller is
    responsible for printing them when --verbose is requested.
    """
    warnings: list[str] = []

    # Build the "haystack" of text we search for filename references:
    # SKILL.md plus every references/*.md file (because references can
    # cross-link to scripts/ or assets/).
    haystack = skill_md_content
    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for ref_file in references_dir.rglob("*.md"):
            try:
                haystack += "\n" + ref_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

    for subdir_name in BUNDLED_SUBDIRS:
        subdir = skill_dir / subdir_name
        if not subdir.is_dir():
            continue
        for entry in subdir.rglob("*"):
            if not entry.is_file():
                continue
            if entry.name in BUNDLE_EXEMPT_FILENAMES:
                continue
            # Reference check: look for the basename anywhere in the haystack.
            # We deliberately check basename rather than the full path so that
            # SKILL.md can write `references/schemas.md` or just `schemas.md`
            # and either form satisfies the audit.
            basename = entry.name
            if basename not in haystack:
                rel = entry.relative_to(skill_dir).as_posix()
                warnings.append(
                    f"{skill_dir / 'SKILL.md'}: bundled file '{rel}' is not "
                    f"referenced from SKILL.md or any references/*.md "
                    f"(either reference this file from SKILL.md or remove it)"
                )

    return warnings


def _section_body(content: str, heading: str) -> str | None:
    """Return the body text of a `## <heading>` section, or None if absent.

    The body runs from just after the heading line to the next `## ` heading
    (or end of file). Matching is case-insensitive on the heading text.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE
    )
    match = pattern.search(content)
    if match is None:
        return None
    start = match.end()
    next_heading = re.compile(r"^##\s+", re.MULTILINE).search(content, start)
    end = next_heading.start() if next_heading else len(content)
    return content[start:end]


def validate_skill_quality(skill_dir: Path, content: str) -> list[str]:
    """Non-blocking quality heuristics for a single skill. Returns warnings.

    These are quality signals, NOT structural errors -- a work-in-progress
    branch can legitimately trip them, so they are always warnings and never
    affect the exit code. The checks mirror the authoring norms in AGENTS.md
    "Write SKILL.md":

    1. A `## Common Rationalizations` section is present.
    2. `## Verification` is present AND uses a binary checklist (`- [ ]`),
       not prose ("the code looks good" is explicitly not a valid criterion).
    3. Tier-1 fields stay within budget: `summary_l0` <= 15 words and
       `overview_l1` <= 150 words.
    4. A `## Related Skills` section is present AND wires at least one
       `[[skill-name]]` cross-link.

    Each returned warning is prefixed with `quality:` so callers and the
    skill-stocktake skill can distinguish quality findings from orphan-bundle
    findings.
    """
    warnings: list[str] = []
    sf = skill_dir / "SKILL.md"

    def warn(msg: str) -> None:
        warnings.append(f"{sf}: quality: {msg}")

    # 1. Common Rationalizations table
    if _section_body(content, "Common Rationalizations") is None:
        warn("missing '## Common Rationalizations' section")

    # 2. Binary (non-prose) Verification
    verification = _section_body(content, "Verification")
    if verification is None:
        warn("missing '## Verification' section")
    elif "- [ ]" not in verification and "- [x]" not in verification.lower():
        warn("Verification section is prose-only (no binary '- [ ]' checklist)")

    # 3. Over-long Tier-1 fields
    fm = parse_frontmatter(content) or {}
    summary = fm.get("summary_l0", "")
    if summary and len(summary.split()) > QUALITY_SUMMARY_L0_MAX_WORDS:
        warn(
            f"summary_l0 is {len(summary.split())} words "
            f"(soft limit {QUALITY_SUMMARY_L0_MAX_WORDS})"
        )
    overview = fm.get("overview_l1", "")
    if overview and len(overview.split()) > QUALITY_OVERVIEW_L1_MAX_WORDS:
        warn(
            f"overview_l1 is {len(overview.split())} words "
            f"(soft limit {QUALITY_OVERVIEW_L1_MAX_WORDS})"
        )

    # 4. Related Skills with at least one cross-link
    related = _section_body(content, "Related Skills")
    if related is None:
        warn("missing '## Related Skills' section")
    elif "[[" not in related:
        warn("Related Skills section has no [[skill-name]] cross-links")

    return warnings


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
    parser = argparse.ArgumentParser(description="Validate Nexus-Hub skills")
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
    parser.add_argument(
        "--bundles-only",
        action="store_true",
        help=(
            "Run only the per-skill bundled-resources orphan audit (skip "
            "frontmatter and secret-scan checks). Used by `make validate` so "
            "the default target stays narrow; the unflagged invocation runs "
            "the full strict validator for manual audits."
        ),
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help=(
            "Run only the non-blocking quality-heuristics pass (missing "
            "Common Rationalizations / prose-only Verification / over-long "
            "Tier-1 fields / missing Related Skills links). Always exits 0; "
            "quality findings are warnings, surfaced with --verbose. Consumed "
            "by the skill-stocktake skill."
        ),
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
        if args.bundles_only or args.quality:
            skill_file = skill_dir / "SKILL.md"
            try:
                content = skill_file.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                total_errors.append(f"{skill_file}: cannot read ({exc})")
                continue
            if args.bundles_only:
                total_warnings.extend(validate_skill_bundles(skill_dir, content))
            if args.quality:
                total_warnings.extend(validate_skill_quality(skill_dir, content))
        else:
            errs, warns = validate_skill_dir(skill_dir)
            total_errors.extend(errs)
            total_warnings.extend(warns)

    # Report results
    if args.quality:
        mode = "quality heuristics"
    elif args.bundles_only:
        mode = "bundle audit"
    else:
        mode = "full validator"
    print(f"Scanned {len(skill_dirs)} skills under {scan_root} ({mode})")

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
