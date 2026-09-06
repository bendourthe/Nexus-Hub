#!/usr/bin/env python3
"""Assert each skill's registry entries still match its SKILL.md.

The three `data/` registry files are hand-edited on purpose: the full catalog
builder rewrites the whole tree and turns a one-skill change into a diff nobody
can review. The cost of that choice is drift, and drift here is quiet. An entry
whose summary went stale when SKILL.md was edited, or whose category no longer
matches the directory it lives in, is still present and still counted, so every
existing membership and count check passes while the catalog misdescribes
itself.

This guard closes that gap by rendering what each entry SHOULD say from the
skill's own frontmatter and comparing it against the committed bytes. It never
writes: `--emit` prints a paste-ready entry, which keeps the hand-edit
convention intact while making the hand edit checkable.

Scope note. Membership and aggregate counts are already covered by
`tests/validators/test_registry_consistency.py`; this checks per-skill FIELD
AGREEMENT, which nothing else does. It also checks capability-module
reachability, which was previously provable only by a ~30-minute integration
suite, because a skill missing from every module installs fine and is simply
unreachable to any focused install.

Editorial fields (downloads, security, priority, size, status) are checked for
presence and type only, never value. This guard must never demand a
regeneration it is forbidden to perform.

Repo-internal guard, standard library only, no outbound call. It is NOT a
distributed artifact and therefore needs no installer copy step; it belongs in
DEV_ONLY_SCRIPTS alongside the other repo-only guards.

Usage:
    python scripts/check_registry_entries.py [--check] [--root .]
    python scripts/check_registry_entries.py --emit <skill-name>

Exit codes:
    0  every skill's entries agree with its SKILL.md (or --emit succeeded)
    1  at least one drift, membership, or source failure
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

# Editorial: a human sets these and no derivation can predict them. Checked for
# presence and type, never value.
EDITORIAL_FIELDS = {
    "downloads": int,
    "size": dict,          # {lines, characters, tokens_estimate}
    "status": str,
    "priority": str,
    "security": dict,
}

# Structural: derivable from the directory itself, and currently clean. These
# are hard failures -- a wrong category or path makes an entry misfile itself.
STRUCTURAL_FIELDS = ("name", "category", "path")

# Text: derivable from frontmatter, but the catalog carries substantial
# pre-existing drift here (see TEXT_DRIFT_NOTE). Reported always; fatal only
# under --strict, so the structural gate can be enforced today without a
# 140-field rewrite of a distributed registry landing in the same change.
TEXT_FIELDS = ("description", "summary_l0", "overview_l1")

TEXT_DRIFT_NOTE = (
    "Text-field drift is REPORTED but not fatal without --strict. The catalog "
    "carries pre-existing drift from skills edited after registration; "
    "repairing it changes descriptions that feed routing, so it is tracked "
    "separately rather than bundled into an unrelated change."
)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return the frontmatter as flat string values, or None when absent.

    Deliberately not a YAML parse: the catalog's frontmatter is flat
    `key: value` lines, and the quoted summary fields must be compared as the
    literal bytes the registries store, quotes included.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def index_rows(index_text: str) -> dict[str, list[str]]:
    """Return skill name -> the row's cells, for every table row in the index."""
    rows: dict[str, list[str]] = {}
    for line in index_text.splitlines():
        if not line.startswith("| ") or line.startswith("| Skill"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 6:
            continue
        rows[cells[1]] = cells
    return rows


def expected_index_row(name: str, category: str, summary: str, skill_path: str) -> str:
    return f"| {name} | {category} | {summary} | {skill_path} |"


def expected_json_entry(fields: dict[str, str], category: str, dir_path: str) -> dict[str, str]:
    return {
        "name": fields.get("name", ""),
        "category": category,
        "path": dir_path,
        "description": fields.get("description", ""),
        "summary_l0": fields.get("summary_l0", ""),
        "overview_l1": fields.get("overview_l1", ""),
    }


def load_json(path: Path, failures: list[str]) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # A file-level abort, not a per-skill cascade.
        failures.append(f"unreadable {path.name}: {exc}")
        return None


def collect_skills(catalog: Path) -> list[tuple[str, str, Path]]:
    """Return (name, category, path) for every skill directory on disk."""
    found: list[tuple[str, str, Path]] = []
    for skill_md in sorted(catalog.rglob("SKILL.md")):
        rel = skill_md.relative_to(catalog)
        if len(rel.parts) != 3:
            continue
        category, name, _ = rel.parts
        found.append((name, category, skill_md))
    return found


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (structural failures, text drift), each collected in full."""
    failures: list[str] = []
    drift: list[str] = []
    catalog = root / "catalog" / "skills"
    data = root / "data"

    if not catalog.is_dir():
        return [f"no catalog at {catalog}"], []

    skills_json = load_json(data / "skills.json", failures)
    marketplace = load_json(data / "marketplace.json", failures)
    bundles = load_json(data / "bundles.json", failures)
    try:
        index_text = (data / "SKILL_INDEX.md").read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"unreadable SKILL_INDEX.md: {exc}")
        index_text = ""

    if failures:
        return failures, drift

    rows = index_rows(index_text)
    entries = {s.get("name"): s for s in skills_json.get("skills", [])}
    on_disk = collect_skills(catalog)
    disk_names = {name for name, _, _ in on_disk}

    # Reachability: a skill in no module and no bundle installs fine and is
    # simply unreachable to any focused install. Silent by construction.
    reachable: set[str] = set()
    for collection in ("modules", "bundles"):
        for entry in bundles.get(collection, []):
            reachable |= set(entry.get("skills", []))

    for name, category, skill_md in on_disk:
        try:
            text = skill_md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            failures.append(f"source: {name}: SKILL.md unreadable ({exc})")
            continue

        fields = parse_frontmatter(text)
        if fields is None:
            failures.append(f"source: {name}: SKILL.md has no frontmatter block")
            continue
        if "summary_l0" not in fields:
            failures.append(f"source: {name}: frontmatter is missing summary_l0")
            continue

        dir_path = f"catalog/skills/{category}/{name}/"
        md_path = f"{dir_path}SKILL.md"

        # SKILL_INDEX row.
        row = rows.get(name)
        if row is None:
            failures.append(f"missing: {name} SKILL_INDEX.md (no row)")
        else:
            expected = expected_index_row(name, category, fields["summary_l0"], md_path)
            if row[2] != category:
                failures.append(
                    f"stale: {name} SKILL_INDEX.md category "
                    f"(row says {row[2]!r}, directory says {category!r})"
                )
            if row[3] != fields["summary_l0"]:
                drift.append(
                    f"drift: {name} SKILL_INDEX.md summary_l0 "
                    f"(row and SKILL.md disagree)"
                )
            if row[4] != md_path:
                failures.append(
                    f"stale: {name} SKILL_INDEX.md path "
                    f"(row says {row[4]!r}, expected {md_path!r})"
                )
            if any(f"{name} SKILL_INDEX.md" in f for f in failures + drift):
                drift.append(f"        expected row: {expected}")

        # skills.json entry.
        entry = entries.get(name)
        if entry is None:
            failures.append(f"missing: {name} skills.json (no entry)")
        else:
            want = expected_json_entry(fields, category, dir_path)
            for field in STRUCTURAL_FIELDS:
                if entry.get(field) != want[field]:
                    failures.append(
                        f"stale: {name} skills.json {field} "
                        f"(entry says {entry.get(field)!r}, expected "
                        f"{want[field]!r})"
                    )
            for field in TEXT_FIELDS:
                if entry.get(field) != want[field]:
                    drift.append(
                        f"drift: {name} skills.json {field} "
                        f"(entry and SKILL.md disagree)"
                    )
            for field, kind in EDITORIAL_FIELDS.items():
                if field not in entry:
                    failures.append(f"missing: {name} skills.json {field}")
                elif not isinstance(entry[field], kind):
                    failures.append(
                        f"stale: {name} skills.json {field} "
                        f"(expected {kind.__name__}, got "
                        f"{type(entry[field]).__name__})"
                    )

        if name not in reachable:
            failures.append(
                f"unreachable: {name} bundles.json (in no module and no "
                f"bundle, so only a `full` install can ever include it)"
            )

    # Orphans: a registry entry with no directory on disk.
    for name in sorted(set(entries) - disk_names):
        failures.append(f"orphan: {name} skills.json (no catalog directory)")
    for name in sorted(set(rows) - disk_names):
        failures.append(f"orphan: {name} SKILL_INDEX.md (no catalog directory)")

    # Census: per-category marketplace counts against the disk.
    census: dict[str, int] = {}
    for _, category, _ in on_disk:
        census[category] = census.get(category, 0) + 1
    for cat_entry in marketplace.get("categories", []):
        cat_id = cat_entry.get("id")
        declared = cat_entry.get("skill_count")
        actual = census.get(cat_id, 0)
        if declared != actual:
            failures.append(
                f"stale: {cat_id} marketplace.json skill_count "
                f"(says {declared}, disk has {actual})"
            )

    return failures, drift


def emit(root: Path, name: str) -> int:
    """Print the paste-ready registry entries for one skill. Writes nothing."""
    catalog = root / "catalog" / "skills"
    for skill_name, category, skill_md in collect_skills(catalog):
        if skill_name != name:
            continue
        fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fields is None:
            print(f"{name}: SKILL.md has no frontmatter block", file=sys.stderr)
            return 1
        dir_path = f"catalog/skills/{category}/{name}/"
        print("# data/SKILL_INDEX.md row\n")
        print(expected_index_row(name, category, fields["summary_l0"], f"{dir_path}SKILL.md"))
        print("\n# data/skills.json entry (derivable fields; add editorial fields to taste)\n")
        print(json.dumps(expected_json_entry(fields, category, dir_path), indent=2, ensure_ascii=False))
        print(
            "\n# Also remember: skills.json statistics, marketplace.json "
            "category count, and a bundles.json module.",
        )
        return 0
    print(f"{name}: no such skill under catalog/skills/", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repo root (default: .)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="read-only drift check (the default when --emit is absent)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail on text-field drift (description/summary_l0/overview_l1)",
    )
    parser.add_argument(
        "--emit",
        metavar="SKILL",
        help="print the paste-ready registry entries for one skill; writes nothing",
    )
    args = parser.parse_args()
    root = Path(args.root)

    if args.emit:
        return emit(root, args.emit)

    failures, drift = check(root)

    if failures:
        print("FAIL registry entries", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print(
            "\nThe data/ registries are hand-edited on purpose (the full "
            "builder rewrites the whole tree). Fix the named field by hand; "
            "`--emit <skill>` prints a paste-ready entry.",
            file=sys.stderr,
        )
        return 1

    if drift:
        stream = sys.stderr if args.strict else sys.stdout
        label = "FAIL" if args.strict else "WARN"
        print(f"{label} registry text drift: {len(drift)} field(s)", file=stream)
        for item in drift[:20]:
            print(f"  - {item}", file=stream)
        if len(drift) > 20:
            print(f"  - ... and {len(drift) - 20} more", file=stream)
        if args.strict:
            return 1
        print(f"  {TEXT_DRIFT_NOTE}", file=stream)

    print("  registry entries: structure and reachability agree with the catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
