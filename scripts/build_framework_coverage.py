#!/usr/bin/env python3
"""Build a security-framework coverage matrix from Nexus-Hub skill frontmatter.

Reads the optional framework-mapping frontmatter fields introduced by the
`security-framework-mapping` skill / convention (see AGENTS.md, "Optional
Security and Compliance Framework Mapping") across `catalog/skills/`:

    mitre_attack       MITRE ATT&CK technique IDs        e.g. [T1003.001, T1071]
    atlas_techniques   MITRE ATLAS (adversarial ML) IDs  e.g. [AML.T0047]
    d3fend_techniques  MITRE D3FEND countermeasure IDs   e.g. [D3-NTA, D3-PA]
    nist_csf           NIST CSF category IDs             e.g. [DE.CM, RS.AN]
    nist_ai_rmf        NIST AI RMF control IDs           e.g. [MEASURE-2.6]

and emits a coverage matrix (Markdown by default, JSON with --format json)
showing which Nexus-Hub skills cover which framework controls.

The script is read-only, local, and makes zero outbound calls -- it only reads
SKILL.md files on disk. Skills that declare none of the five fields are simply
absent from the matrix; the tool never fails on an untagged catalog.

Usage:
    python scripts/build_framework_coverage.py
    python scripts/build_framework_coverage.py --format json
    python scripts/build_framework_coverage.py --out docs/framework-coverage.md
    python scripts/build_framework_coverage.py --root catalog/skills/security

Exit code is 0 on success and 1 only on an I/O / argument error (a catalog with
no tagged skills is a successful empty matrix, not a failure).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Ordered so the Markdown report reads attack -> defense -> governance.
FRAMEWORKS: list[tuple[str, str]] = [
    ("mitre_attack", "MITRE ATT&CK"),
    ("atlas_techniques", "MITRE ATLAS"),
    ("d3fend_techniques", "MITRE D3FEND"),
    ("nist_csf", "NIST CSF"),
    ("nist_ai_rmf", "NIST AI RMF"),
]

FRAMEWORK_FIELDS = {field for field, _ in FRAMEWORKS}


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def extract_frontmatter_block(content: str) -> str | None:
    """Return the raw text between the leading `---` fences, or None."""
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    return content[3:end]


def parse_id_list(raw_value: str) -> list[str]:
    """Parse a frontmatter list value into a clean list of framework IDs.

    Handles inline-flow lists (`[T1071, T1003.001]`), single-item lists
    (`[T1071]`), and bare scalars (`T1071`). Quotes and surrounding
    whitespace are stripped; empty entries are dropped. The relative order
    in the source is preserved.
    """
    value = raw_value.strip()
    if not value:
        return []
    # Strip a single pair of surrounding brackets if present.
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    ids: list[str] = []
    for token in value.split(","):
        token = token.strip().strip('"').strip("'").strip()
        if token:
            ids.append(token)
    return ids


def parse_framework_tags(content: str) -> dict[str, list[str]]:
    """Extract the five optional framework-mapping fields from a SKILL.md.

    Returns a dict keyed by the field name (only fields actually present and
    non-empty are included).
    """
    block = extract_frontmatter_block(content)
    if block is None:
        return {}
    tags: dict[str, list[str]] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        if key not in FRAMEWORK_FIELDS:
            continue
        ids = parse_id_list(value)
        if ids:
            tags[key] = ids
    return tags


def skill_name(content: str, skill_dir: Path) -> str:
    """Return the skill's frontmatter `name`, falling back to the dir name."""
    block = extract_frontmatter_block(content)
    if block:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("name:"):
                name = stripped.partition(":")[2].strip().strip('"').strip("'")
                if name:
                    return name
    return skill_dir.name


# ---------------------------------------------------------------------------
# Matrix construction
# ---------------------------------------------------------------------------

def find_skill_files(root: Path) -> list[Path]:
    """Find every SKILL.md under root, sorted for deterministic output."""
    return sorted(root.rglob("SKILL.md"))


def build_coverage(root: Path) -> dict[str, dict[str, list[str]]]:
    """Build {framework_field: {control_id: [skill_name, ...]}}.

    Each skill list is sorted and de-duplicated.
    """
    coverage: dict[str, dict[str, set[str]]] = {field: {} for field in FRAMEWORK_FIELDS}
    for skill_file in find_skill_files(root):
        try:
            content = skill_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tags = parse_framework_tags(content)
        if not tags:
            continue
        name = skill_name(content, skill_file.parent)
        for field, ids in tags.items():
            for control_id in ids:
                coverage[field].setdefault(control_id, set()).add(name)
    # Freeze sets into sorted lists.
    return {
        field: {cid: sorted(names) for cid, names in sorted(ids.items())}
        for field, ids in coverage.items()
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_markdown(coverage: dict[str, dict[str, list[str]]], root: Path) -> str:
    """Render the coverage matrix as a Markdown document."""
    lines: list[str] = []
    lines.append("# Security Framework Coverage Matrix")
    lines.append("")
    lines.append(
        f"Generated from optional framework-mapping frontmatter across `{root.as_posix()}`. "
        "Each row links a public framework control ID to the Nexus-Hub skills tagged with it. "
        "See `catalog/skills/security/security-framework-mapping/SKILL.md` for the tagging convention."
    )
    lines.append("")

    # Summary table.
    lines.append("## Summary")
    lines.append("")
    lines.append("| Framework | Distinct controls covered | Skill tags |")
    lines.append("|---|---|---|")
    for field, display in FRAMEWORKS:
        ids = coverage.get(field, {})
        tag_count = sum(len(names) for names in ids.values())
        lines.append(f"| {display} | {len(ids)} | {tag_count} |")
    lines.append("")

    # Per-framework detail tables.
    for field, display in FRAMEWORKS:
        ids = coverage.get(field, {})
        lines.append(f"## {display}")
        lines.append("")
        if not ids:
            lines.append("_No skills currently tagged with this framework._")
            lines.append("")
            continue
        lines.append("| Control ID | Skills |")
        lines.append("|---|---|")
        for control_id, names in ids.items():
            lines.append(f"| `{control_id}` | {', '.join(names)} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(coverage: dict[str, dict[str, list[str]]], root: Path) -> str:
    """Render the coverage matrix as JSON."""
    summary = {
        field: {
            "display": display,
            "controls": len(coverage.get(field, {})),
            "tags": sum(len(n) for n in coverage.get(field, {}).values()),
        }
        for field, display in FRAMEWORKS
    }
    payload = {
        "root": root.as_posix(),
        "summary": summary,
        "coverage": coverage,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a security-framework coverage matrix from skill frontmatter",
    )
    parser.add_argument(
        "--root",
        "--path",
        dest="root",
        type=Path,
        default=Path("catalog/skills"),
        help="Root directory to scan for SKILL.md files (default: catalog/skills)",
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the matrix to this file instead of stdout",
    )
    args = parser.parse_args()

    if not args.root.exists():
        print(f"ERROR: path does not exist: {args.root}", file=sys.stderr)
        return 1

    coverage = build_coverage(args.root)
    rendered = render_json(coverage, args.root) if args.format == "json" else render_markdown(coverage, args.root)

    if args.out is not None:
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write {args.out}: {exc}", file=sys.stderr)
            return 1
        tagged = sum(len(ids) for ids in coverage.values())
        print(f"Wrote framework coverage matrix to {args.out} ({tagged} control rows).")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
