#!/usr/bin/env python3
"""Validate all Nexus-Hub skills for structural compliance and security.

Checks YAML frontmatter, required fields, directory naming, and scans for
hardcoded secrets. A strict-YAML gate additionally fails the run when a
frontmatter block does not parse under PyYAML (e.g. an unquoted `description:`
scalar containing a `: ` sequence that a strict skill-discovery consumer would
silently reject); it runs in both the full validator and `--bundles-only`.
Also exposes a non-blocking quality-heuristics pass
behind `--quality` (missing Common Rationalizations, prose-only
Verification, over-long Tier-1 fields, missing Related Skills links) --
warnings only, never errors. Returns exit code 0 if all checks pass
(warnings OK), exit code 1 if any ERROR-level issue is found.

Usage:
    python scripts/validate_skills.py
    python scripts/validate_skills.py --path catalog/skills/framework-specialists/
    python scripts/validate_skills.py --verbose
    python scripts/validate_skills.py --quality --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml  # PyYAML: powers the strict-frontmatter gate below.
    _HAS_YAML = True
except ImportError:  # pragma: no cover - PyYAML is a catalog-tooling dependency.
    yaml = None  # type: ignore[assignment]
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_FIELDS = {"name", "description", "summary_l0", "overview_l1"}
OPTIONAL_FRONTMATTER_FIELDS = {"version", "author", "license", "category", "tags"}

# Single-line frontmatter discipline (insight I-03 from the Nexus
# adoption-skill-cleaner track; enforced upstream at PR time rather than at
# runtime in the consumer). `name` must be single-line kebab-case; `description`
# must be single-line and stay within DESCRIPTION_MAX_CHARS. When `name` is
# absent the parent directory name is the default and must itself be kebab-case.
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
DESCRIPTION_MAX_CHARS = 250

# Transitional allowlist consulted only under `--allow-existing`: files whose
# pre-existing single-line violations are grandfathered (demoted to warnings)
# while the catalog drains them. Lives beside this script.
ALLOWLIST_PATH = Path(__file__).resolve().parent / "validate_skills.allowlist.json"
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

# Low-confidence patterns whose matches inside a fenced code block of a
# Markdown file are documentation examples (e.g., `password = "hunter2"` in a
# snippet) rather than real leaked credentials. These are suppressed in that
# context only. High-confidence credential patterns (real API-key / token
# formats) are intentionally NOT listed here, so a genuinely leaked key pasted
# into a code block is still flagged even inside a fence.
FENCE_EXEMPT_PATTERN_NAMES = {"Generic secret assignment"}


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


def _frontmatter_block(content: str) -> str | None:
    """Return the raw text between the first two `---` fences, or None.

    Unlike parse_frontmatter (which returns a naive line-split dict), this hands
    back the untouched YAML source so it can be fed to a strict parser.
    """
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return content[3:end]


def validate_frontmatter_strict_yaml(skill_file: Path, content: str) -> list[str]:
    """Hard gate: the frontmatter block must parse under a strict YAML parser.

    The tolerant parse_frontmatter() above line-splits on the first `:` and so
    silently accepts malformed YAML that a strict consumer rejects -- most
    commonly an UNQUOTED `description:` scalar whose text contains a `: `
    sequence (e.g. from a `SKIP:` clause), which makes PyYAML raise a
    ScannerError and the skill fail to load in Claude Code skill discovery and
    the flatten adapter's downstream parsers. This gate fails the run on any
    such file so the defect cannot regress.

    When PyYAML is unavailable, degrades to a minimal heuristic: an unquoted
    top-level scalar value containing `: ` is reported, with a clear message
    that a heuristic (not a full parse) was used.

    Returns a list of error strings (empty when the block parses cleanly or is
    absent -- a missing fence is the caller's own concern).
    """
    block = _frontmatter_block(content)
    if block is None:
        return []
    if _HAS_YAML:
        try:
            yaml.safe_load(block)
        except yaml.YAMLError as exc:
            msg = " ".join(str(exc).split())
            return [
                f"{skill_file}: frontmatter is not valid YAML ({msg}); quote the "
                f"offending scalar value (e.g. wrap the description: value in "
                f"double quotes) so a strict parser can load the skill"
            ]
        return []
    # Fallback (PyYAML absent): flag an unquoted top-level scalar with `: `.
    errors: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#") or line[0].isspace():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if not value or value.startswith(('"', "'")):
            continue
        if ": " in value:
            errors.append(
                f"{skill_file}: frontmatter key '{key.strip()}' has an unquoted "
                f"value containing ': ' (heuristic; PyYAML unavailable for a full "
                f"parse) -- wrap the value in double quotes"
            )
    return errors


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def load_allowlist(path: Path = ALLOWLIST_PATH) -> set[str]:
    """Load the transitional single-line-violation allowlist.

    Returns the set of POSIX-style relative SKILL.md paths whose new-rule
    violations are grandfathered. A missing or malformed file yields an empty
    set (the allowlist is purely optional and additive).
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    allow = data.get("allow", []) if isinstance(data, dict) else []
    return {str(entry) for entry in allow}


def validate_frontmatter_format(
    skill_file: Path, skill_dir: Path, fm: dict[str, str]
) -> list[str]:
    """Enforce the single-line name/description discipline (insight I-03).

    Three checks:
      (a) `name:` is single-line kebab-case (^[a-z0-9-]+$).
      (b) `description:` is single-line and at most DESCRIPTION_MAX_CHARS.
      (c) when `name:` is absent, the parent directory name is the effective
          name and must itself satisfy rule (a).

    Returns a list of error strings (empty when the frontmatter conforms).
    """
    errors: list[str] = []

    # (a) + (c): effective name is the frontmatter value, or the directory name
    # when `name:` is absent. Either way it must be single-line kebab-case.
    name = fm.get("name") or skill_dir.name
    if "\n" in name or not NAME_PATTERN.fullmatch(name):
        source = "frontmatter name" if fm.get("name") else "directory name (default for absent name)"
        errors.append(
            f"{skill_file}: {source} '{name}' must be single-line kebab-case "
            f"(^[a-z0-9-]+$)"
        )

    # (b): description single-line and within the character budget.
    description = fm.get("description", "")
    if "\n" in description:
        errors.append(f"{skill_file}: description must be a single line (no embedded newline)")
    if len(description) > DESCRIPTION_MAX_CHARS:
        errors.append(
            f"{skill_file}: description is {len(description)} characters "
            f"(max {DESCRIPTION_MAX_CHARS})"
        )

    return errors


def validate_skill_dir(
    skill_dir: Path, grandfathered: frozenset[str] | set[str] = frozenset()
) -> tuple[list[str], list[str]]:
    """Validate a single skill directory. Returns (errors, warnings).

    `grandfathered` is the set of POSIX SKILL.md paths whose single-line-format
    violations are demoted from errors to warnings (populated from the allowlist
    only when `--allow-existing` is passed).
    """
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

    # Hard rule (v3.14.3): the frontmatter block must parse under a STRICT YAML
    # parser. parse_frontmatter above is tolerant and would accept an unquoted
    # scalar with a `: ` sequence that a strict consumer (Claude skill discovery)
    # rejects, so the skill would silently fail to load.
    errors.extend(validate_frontmatter_strict_yaml(skill_file, content))

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

    # Hard rule (insight I-03): single-line name/description discipline.
    # Grandfathered files have their format violations demoted to warnings.
    format_errors = validate_frontmatter_format(skill_file, skill_dir, fm)
    if skill_file.as_posix() in grandfathered:
        warnings.extend(f"grandfathered single-line violation: {e}" for e in format_errors)
    else:
        errors.extend(format_errors)

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


# A fenced-code delimiter: 3+ backticks or 3+ tildes, optionally indented,
# optionally followed by an info string (only on the OPENING fence).
_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def scan_text_for_secrets(text: str, filepath: Path) -> list[str]:
    """Scan one file's text for hardcoded secrets, fenced-code-aware.

    Inside a fenced code block of a Markdown file, the low-confidence patterns
    in FENCE_EXEMPT_PATTERN_NAMES are suppressed because such matches are
    documentation examples, not real leaked credentials. High-confidence
    credential patterns are always flagged, even inside a fence.

    Fence tracking follows the CommonMark rule so nested examples (e.g. a
    ```markdown block that itself shows ```bash snippets) are handled
    correctly: an opening fence may carry an info string, but a CLOSING fence
    must use the same character, be at least as long, and carry NO info string.
    A fence-looking line that is not a valid closer while already inside a
    fence is treated as block content.
    """
    errors: list[str] = []
    is_markdown = filepath.suffix.lower() == ".md"
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if is_markdown:
            m = _FENCE_RE.match(line)
            if m:
                fence = m.group("fence")
                info = m.group("info").strip()
                char = fence[0]
                if not in_fence:
                    in_fence, fence_char, fence_len = True, char, len(fence)
                    continue
                if char == fence_char and len(fence) >= fence_len and not info:
                    in_fence, fence_char, fence_len = False, "", 0
                    continue
                # fence-looking content inside an open fence: fall through.
        for pattern_name, pattern in SECRET_PATTERNS:
            if is_markdown and in_fence and pattern_name in FENCE_EXEMPT_PATTERN_NAMES:
                continue
            if pattern.search(line):
                errors.append(
                    f"{filepath}: potential {pattern_name} detected "
                    f"(line ~{line_no})"
                )
    return errors


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
            errors.extend(scan_text_for_secrets(text, filepath))
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
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help=(
            "Demote single-line name/description violations (insight I-03) to "
            "warnings for files listed in scripts/validate_skills.allowlist.json. "
            "Transitional: grandfathers known offenders while the catalog drains "
            "them. New files are still hard-errors."
        ),
    )
    args = parser.parse_args()

    grandfathered: set[str] = load_allowlist() if args.allow_existing else set()

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
                # The strict-YAML gate is a hard error even in --bundles-only,
                # the mode CI runs, so an unparseable frontmatter fails CI.
                total_errors.extend(validate_frontmatter_strict_yaml(skill_file, content))
                total_warnings.extend(validate_skill_bundles(skill_dir, content))
            if args.quality:
                # --quality keeps its always-exit-0 contract, so the gate is not
                # run here (it runs in the full validator and --bundles-only).
                total_warnings.extend(validate_skill_quality(skill_dir, content))
        else:
            errs, warns = validate_skill_dir(skill_dir, grandfathered)
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
