"""Registry-vs-disk consistency guard for the data/ catalog files (v3.15.5 Phase 4).

Adding a skill means hand-editing three registry files (`data/SKILL_INDEX.md`,
`data/skills.json`, `data/marketplace.json`), because the full catalog rebuild
rewrites the whole tree and is deliberately not run. Hand-editing is fine, but
nothing verified the result, and the counts had silently drifted:

  * `skills.json.statistics.total_skills` read 260 against 268 actual entries.
  * `SKILL_INDEX.md`'s "Total: N skills" line read 267 against 268.

Both were corrected while registering `model-prompting-research`. This module is
the guard that stops the drift recurring: every count must agree with the number
of `SKILL.md` files actually on disk, and every on-disk skill must appear in the
index and the catalog. Cheap, deterministic, and it would have caught both.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "catalog" / "skills"
SKILLS_JSON = REPO_ROOT / "data" / "skills.json"
MARKETPLACE_JSON = REPO_ROOT / "data" / "marketplace.json"
SKILL_INDEX = REPO_ROOT / "data" / "SKILL_INDEX.md"


def _disk_skills() -> dict[str, str]:
    """Map skill name (directory name) to its category, from the file tree."""
    found: dict[str, str] = {}
    for dirpath, _dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" not in files:
            continue
        path = Path(dirpath)
        found[path.name] = path.parent.name
    return found


def _catalog() -> dict:
    return json.loads(SKILLS_JSON.read_text(encoding="utf-8"))


def test_every_on_disk_skill_is_in_skills_json() -> None:
    registered = {s["name"] for s in _catalog()["skills"]}

    missing = sorted(set(_disk_skills()) - registered)

    assert not missing, (
        f"{len(missing)} skill(s) exist on disk but are absent from data/skills.json: "
        f"{missing}. Register them per AGENTS.md rule 2 (hand-edit the three data/ files)."
    )


def test_skills_json_has_no_entry_without_a_skill_on_disk() -> None:
    on_disk = set(_disk_skills())

    orphans = sorted({s["name"] for s in _catalog()["skills"]} - on_disk)

    assert not orphans, f"data/skills.json lists skill(s) with no SKILL.md on disk: {orphans}"


def test_statistics_total_matches_the_entry_count() -> None:
    catalog = _catalog()

    assert catalog["statistics"]["total_skills"] == len(catalog["skills"])


def test_statistics_per_category_counts_match_the_entries() -> None:
    catalog = _catalog()
    actual: dict[str, int] = {}
    for skill in catalog["skills"]:
        actual[skill["category"]] = actual.get(skill["category"], 0) + 1

    assert catalog["statistics"]["categories"] == actual


def test_marketplace_category_counts_sum_to_the_catalog_size() -> None:
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))

    total = sum(c["skill_count"] for c in marketplace["categories"])

    assert total == len(_catalog()["skills"])


def test_marketplace_per_category_counts_match_skills_json() -> None:
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    stats = _catalog()["statistics"]["categories"]

    mismatched = {
        c["id"]: (c["skill_count"], stats.get(c["id"]))
        for c in marketplace["categories"]
        if c["skill_count"] != stats.get(c["id"])
    }

    assert not mismatched, f"marketplace vs skills.json category drift: {mismatched}"


def test_skill_index_total_line_matches_the_catalog() -> None:
    text = SKILL_INDEX.read_text(encoding="utf-8")

    match = re.search(r"^\*\*Total: (\d+) skills across (\d+) categories\*\*", text, re.M)

    assert match, "data/SKILL_INDEX.md has no '**Total: N skills across M categories**' line"
    assert int(match.group(1)) == len(_catalog()["skills"])


def test_skill_index_has_a_row_for_every_on_disk_skill() -> None:
    rows = set(re.findall(r"^\| ([a-z0-9-]+) \|", SKILL_INDEX.read_text(encoding="utf-8"), re.M))

    missing = sorted(set(_disk_skills()) - rows)

    assert not missing, f"{len(missing)} skill(s) missing a data/SKILL_INDEX.md row: {missing}"


def test_index_summaries_are_quoted() -> None:
    """The MCP server parses these; an unquoted summary breaks discovery."""
    text = SKILL_INDEX.read_text(encoding="utf-8")

    unquoted = [
        name
        for name, summary in re.findall(r"^\| ([a-z0-9-]+) \| [a-z-]+ \| (.+?) \|", text, re.M)
        if not (summary.strip().startswith('"') and summary.strip().endswith('"'))
    ]

    assert not unquoted, f"SKILL_INDEX rows with an unquoted summary: {unquoted}"
