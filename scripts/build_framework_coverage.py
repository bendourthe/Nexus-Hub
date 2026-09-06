#!/usr/bin/env python3
"""Build a security-framework coverage matrix from Nexus-Hub skill frontmatter.

Reads the optional framework-mapping frontmatter fields introduced by the
`security-framework-mapping` skill / convention (see AGENTS.md, "Optional
Security and Compliance Framework Mapping") across `catalog/skills/`:

    mitre_attack       MITRE ATT&CK technique IDs        e.g. [T1003.001, T1071]
    atlas_techniques   MITRE ATLAS (adversarial ML) IDs  e.g. [AML.T0047]
    mitre_f3           MITRE Fight Fraud Framework IDs   e.g. [F1005.006, F1010]
    d3fend_techniques  MITRE D3FEND countermeasure IDs   e.g. [D3-NTA, D3-PA]
    nist_csf           NIST CSF category IDs             e.g. [DE.CM, RS.AN]
    nist_ai_rmf        NIST AI RMF control IDs           e.g. [MEASURE-2.6]

and emits a coverage matrix (Markdown by default, JSON with --format json)
showing which Nexus-Hub skills cover which framework controls. Pass
`--navigator-layer <path>` to also write a MITRE ATT&CK Navigator layer JSON
derived solely from `mitre_attack` values already on disk.

The script is read-only of the catalog (it only reads SKILL.md files) and
makes zero outbound calls. Skills that declare none of the six fields are
simply absent from the matrix; the tool never fails on an untagged catalog.

Usage:
    python scripts/build_framework_coverage.py
    python scripts/build_framework_coverage.py --format json
    python scripts/build_framework_coverage.py --out docs/framework-coverage.md
    python scripts/build_framework_coverage.py --navigator-layer docs/attack-navigator-layer.json
    python scripts/build_framework_coverage.py --check
    python scripts/build_framework_coverage.py --root catalog/skills/security

Exit code is 0 on success. Exit 1 on an I/O / argument error, or when `--check`
finds the committed coverage Markdown or Navigator layer out of date. A catalog
with no tagged skills is a successful empty matrix, not a failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Ordered so the Markdown report reads attack -> fraud -> defense -> governance.
FRAMEWORKS: list[tuple[str, str]] = [
    ("mitre_attack", "MITRE ATT&CK"),
    ("atlas_techniques", "MITRE ATLAS"),
    ("mitre_f3", "MITRE F3"),
    ("d3fend_techniques", "MITRE D3FEND"),
    ("nist_csf", "NIST CSF"),
    ("nist_ai_rmf", "NIST AI RMF"),
]

# ATT&CK Navigator layer format v4.5. `layer` and `navigator` are required by
# the spec; `attack` is pinned to a dated major so the file diffs cleanly.
# https://github.com/mitre-attack/attack-navigator/blob/master/layers/spec/v4.5/layerformat.md
NAVIGATOR_LAYER_VERSIONS: dict[str, str] = {
    "attack": "17",
    "layer": "4.5",
    "navigator": "5.1.0",
}

FRAMEWORK_FIELDS = {field for field, _ in FRAMEWORKS}

DEFAULT_COVERAGE_MD = Path("docs/framework-coverage.md")
DEFAULT_NAVIGATOR_LAYER = Path("docs/attack-navigator-layer.json")
REGENERATE_COMMAND = (
    "python scripts/build_framework_coverage.py "
    "--out docs/framework-coverage.md "
    "--navigator-layer docs/attack-navigator-layer.json"
)


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
    """Extract the optional framework-mapping fields from a SKILL.md.

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

def display_root(root: Path) -> str:
    """Return a stable posix path so --check does not depend on how --root was spelled."""
    try:
        return root.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return root.as_posix()


def render_markdown(coverage: dict[str, dict[str, list[str]]], root: Path) -> str:
    """Render the coverage matrix as a Markdown document."""
    lines: list[str] = []
    lines.append("<!-- GENERATED FILE. Do not edit by hand.")
    lines.append(f"     Regenerate with: {REGENERATE_COMMAND}")
    lines.append("-->")
    lines.append("")
    lines.append("# Security Framework Coverage Matrix")
    lines.append("")
    lines.append(
        "GENERATED from optional framework-mapping frontmatter. Never hand-edit this file; "
        f"run `{REGENERATE_COMMAND}` instead."
    )
    lines.append("")
    lines.append(
        f"Scanned `{display_root(root)}`. "
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


def render_navigator_layer(coverage: dict[str, dict[str, list[str]]]) -> str:
    """Render a MITRE ATT&CK Navigator layer JSON from `mitre_attack` tags.

    Derived solely from parsed SKILL.md values. Score is the number of
    skills covering the technique; comment lists those skill names. Output
    is deterministic (sorted keys, sorted technique IDs, sorted names).
    """
    attack = coverage.get("mitre_attack", {})
    techniques = [
        {
            "comment": ", ".join(names),
            "score": len(names),
            "techniqueID": technique_id,
        }
        for technique_id, names in sorted(attack.items())
    ]
    layer = {
        "description": (
            "Nexus-Hub catalog coverage of MITRE ATT&CK techniques, derived "
            "from mitre_attack frontmatter on SKILL.md files. Score is the "
            "number of skills that teach the technique."
        ),
        "domain": "enterprise-attack",
        "name": "Nexus-Hub ATT&CK coverage",
        "techniques": techniques,
        "versions": NAVIGATOR_LAYER_VERSIONS,
    }
    return json.dumps(layer, indent=2, sort_keys=True) + "\n"


def normalize_newlines(text: str) -> str:
    """Collapse CRLF to LF so --check is host-independent."""
    return text.replace("\r\n", "\n")


def files_match(path: Path, expected: str) -> str | None:
    """Return an error message if path is missing or differs from expected."""
    if not path.is_file():
        return f"missing committed file {path.as_posix()}"
    actual = normalize_newlines(path.read_text(encoding="utf-8"))
    if actual != expected:
        return f"stale committed file {path.as_posix()} (regenerate with: {REGENERATE_COMMAND})"
    return None


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with LF newlines so re-runs are byte-identical."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
    parser.add_argument(
        "--navigator-layer",
        type=Path,
        default=None,
        help=(
            "Also write a MITRE ATT&CK Navigator layer JSON to this path, "
            "derived from mitre_attack values already parsed from SKILL.md "
            "files (alongside, not instead of, the coverage matrix)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate the coverage Markdown and Navigator layer in memory "
            "and exit 1 if the committed files differ. Defaults to "
            f"{DEFAULT_COVERAGE_MD} and {DEFAULT_NAVIGATOR_LAYER}."
        ),
    )
    args = parser.parse_args()

    if not args.root.exists():
        print(f"ERROR: path does not exist: {args.root}", file=sys.stderr)
        return 1

    coverage = build_coverage(args.root)

    if args.check:
        markdown_path = args.out if args.out is not None else DEFAULT_COVERAGE_MD
        layer_path = (
            args.navigator_layer
            if args.navigator_layer is not None
            else DEFAULT_NAVIGATOR_LAYER
        )
        expected_markdown = render_markdown(coverage, args.root)
        expected_layer = render_navigator_layer(coverage)
        errors = [
            message
            for message in (
                files_match(markdown_path, expected_markdown),
                files_match(layer_path, expected_layer),
            )
            if message
        ]
        if errors:
            for message in errors:
                print(f"ERROR: {message}", file=sys.stderr)
            return 1
        print(
            f"OK: framework coverage in sync "
            f"({markdown_path.as_posix()}, {layer_path.as_posix()})"
        )
        return 0

    rendered = render_json(coverage, args.root) if args.format == "json" else render_markdown(coverage, args.root)

    if args.out is not None:
        try:
            write_text(args.out, rendered)
        except OSError as exc:
            print(f"ERROR: cannot write {args.out}: {exc}", file=sys.stderr)
            return 1
        tagged = sum(len(ids) for ids in coverage.values())
        print(f"Wrote framework coverage matrix to {args.out} ({tagged} control rows).")
    else:
        sys.stdout.write(rendered)

    if args.navigator_layer is not None:
        try:
            write_text(args.navigator_layer, render_navigator_layer(coverage))
        except OSError as exc:
            print(f"ERROR: cannot write {args.navigator_layer}: {exc}", file=sys.stderr)
            return 1
        technique_count = len(coverage.get("mitre_attack", {}))
        print(
            f"Wrote ATT&CK Navigator layer to {args.navigator_layer} "
            f"({technique_count} techniques)."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
