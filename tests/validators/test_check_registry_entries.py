"""Tests for scripts/check_registry_entries.py.

The registries are hand-edited on purpose, so drift is the expected failure and
it is quiet: an entry that is present and counted still passes every membership
and count check while misdescribing the skill. These tests therefore assert
failure in both directions on a synthetic mini-catalog, and separately assert
the two properties that matter on the real tree (structure clean, drift
reported rather than hidden).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_registry_entries.py"

SKILL_MD = """---
name: {name}
description: A test skill for {name}.
summary_l0: "Does the {name} thing"
overview_l1: "A longer paragraph about the {name} thing."
---

# {name}

Body.
"""


def build(root: Path, skills: list[tuple[str, str]]) -> None:
    """Create a mini catalog plus three registry files in sync."""
    index_rows = []
    entries = []
    census: dict[str, int] = {}

    for name, category in skills:
        d = root / "catalog" / "skills" / category / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(SKILL_MD.format(name=name), encoding="utf-8")
        dir_path = f"catalog/skills/{category}/{name}/"
        summary = f'"Does the {name} thing"'
        index_rows.append(
            f"| {name} | {category} | {summary} | {dir_path}SKILL.md |"
        )
        entries.append(
            {
                "name": name,
                "category": category,
                "path": dir_path,
                "description": f"A test skill for {name}.",
                "summary_l0": summary,
                "overview_l1": f'"A longer paragraph about the {name} thing."',
                "downloads": 0,
                "size": {"lines": 1, "characters": 1, "tokens_estimate": 1},
                "status": "active",
                "priority": "MEDIUM",
                "security": {"structural": 100},
            }
        )
        census[category] = census.get(category, 0) + 1

    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "SKILL_INDEX.md").write_text(
        "| Skill | Category | Summary | File |\n|---|---|---|---|\n"
        + "\n".join(index_rows)
        + "\n",
        encoding="utf-8",
    )
    (data / "skills.json").write_text(
        json.dumps({"skills": entries}, indent=2), encoding="utf-8"
    )
    (data / "marketplace.json").write_text(
        json.dumps(
            {"categories": [{"id": c, "skill_count": n} for c, n in census.items()]},
            indent=2,
        ),
        encoding="utf-8",
    )
    (data / "bundles.json").write_text(
        json.dumps(
            {"modules": [{"id": "all", "skills": [n for n, _ in skills]}], "bundles": []},
            indent=2,
        ),
        encoding="utf-8",
    )


def run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *extra],
        capture_output=True,
        text=True,
    )


def edit_json(root: Path, name: str, field: str, value) -> None:
    path = root / "data" / "skills.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    for e in d["skills"]:
        if e["name"] == name:
            if value is None:
                e.pop(field, None)
            else:
                e[field] = value
    path.write_text(json.dumps(d, indent=2), encoding="utf-8")


def test_a_catalog_in_sync_passes(tmp_path):
    build(tmp_path, [("alpha", "workflow"), ("beta", "security")])
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "structure and reachability agree" in result.stdout


def test_missing_index_row_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    index = tmp_path / "data" / "SKILL_INDEX.md"
    index.write_text("| Skill | Category | Summary | File |\n|---|---|---|---|\n", encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "missing: alpha SKILL_INDEX.md" in result.stderr


def test_missing_json_entry_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    path = tmp_path / "data" / "skills.json"
    path.write_text(json.dumps({"skills": []}), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "missing: alpha skills.json" in result.stderr


def test_category_mismatch_is_a_hard_failure(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "category", "security")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "stale: alpha skills.json category" in result.stderr
    assert "'security'" in result.stderr and "'workflow'" in result.stderr


def test_path_mismatch_is_a_hard_failure(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "path", "catalog/skills/elsewhere/alpha/")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "stale: alpha skills.json path" in result.stderr


def test_index_category_mismatch_is_a_hard_failure(tmp_path):
    """The real catalog carried exactly this defect: 'Workflow' vs 'workflow'."""
    build(tmp_path, [("alpha", "workflow")])
    index = tmp_path / "data" / "SKILL_INDEX.md"
    index.write_text(
        index.read_text(encoding="utf-8").replace("| alpha | workflow |", "| alpha | Workflow |"),
        encoding="utf-8",
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "stale: alpha SKILL_INDEX.md category" in result.stderr


def test_orphan_registry_entry_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    path = tmp_path / "data" / "skills.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d["skills"].append(dict(d["skills"][0], name="ghost"))
    path.write_text(json.dumps(d, indent=2), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "orphan: ghost skills.json" in result.stderr


def test_bad_marketplace_count_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    path = tmp_path / "data" / "marketplace.json"
    path.write_text(
        json.dumps({"categories": [{"id": "workflow", "skill_count": 9}]}), encoding="utf-8"
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "marketplace.json skill_count" in result.stderr
    assert "says 9" in result.stderr


def test_a_skill_in_no_module_is_unreachable(tmp_path):
    """The Phase 2 defect: installs fine, invisible to any focused install."""
    build(tmp_path, [("alpha", "workflow")])
    path = tmp_path / "data" / "bundles.json"
    path.write_text(json.dumps({"modules": [], "bundles": []}), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "unreachable: alpha bundles.json" in result.stderr
    assert "only a `full` install" in result.stderr


def test_editorial_fields_are_checked_for_type_not_value(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "downloads", 99999)
    assert run(tmp_path).returncode == 0, "a different value must not fail"
    edit_json(tmp_path, "alpha", "downloads", "many")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "skills.json downloads" in result.stderr


def test_size_must_be_the_dict_schema(tmp_path):
    """Regression: a Phase 2 entry shipped `size` as an int."""
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "size", 21166)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "skills.json size" in result.stderr
    assert "expected dict, got int" in result.stderr


def test_missing_editorial_field_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "security", None)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "missing: alpha skills.json security" in result.stderr


def test_text_drift_warns_but_does_not_fail_by_default(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "description", "Something else entirely.")
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "WARN registry text drift" in result.stdout
    assert "drift: alpha skills.json description" in result.stdout


def test_text_drift_fails_under_strict(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    edit_json(tmp_path, "alpha", "description", "Something else entirely.")
    result = run(tmp_path, "--strict")
    assert result.returncode == 1
    assert "FAIL registry text drift" in result.stderr


def test_malformed_frontmatter_is_a_source_failure(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    skill = tmp_path / "catalog" / "skills" / "workflow" / "alpha" / "SKILL.md"
    skill.write_text("# No frontmatter here\n", encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "source: alpha" in result.stderr
    assert "no frontmatter" in result.stderr


def test_missing_summary_l0_is_a_source_failure(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    skill = tmp_path / "catalog" / "skills" / "workflow" / "alpha" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace('summary_l0: "Does the alpha thing"', "other: x"),
        encoding="utf-8",
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "missing summary_l0" in result.stderr


def test_unparseable_registry_aborts_at_file_level(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    (tmp_path / "data" / "skills.json").write_text("{not json", encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "unreadable skills.json" in result.stderr
    # A file-level abort, not a per-skill cascade.
    assert "stale: alpha" not in result.stderr


def test_all_failures_are_collected_before_the_single_exit(tmp_path):
    build(tmp_path, [("alpha", "workflow"), ("beta", "security")])
    edit_json(tmp_path, "alpha", "category", "security")
    edit_json(tmp_path, "beta", "downloads", "many")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "alpha skills.json category" in result.stderr
    assert "beta skills.json downloads" in result.stderr


def test_emit_prints_a_paste_ready_entry_and_writes_nothing(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    before = (tmp_path / "data" / "skills.json").read_bytes()
    result = run(tmp_path, "--emit", "alpha")
    assert result.returncode == 0, result.stderr
    assert "| alpha | workflow |" in result.stdout
    assert '"name": "alpha"' in result.stdout
    assert (tmp_path / "data" / "skills.json").read_bytes() == before


def test_emit_for_an_unknown_skill_fails(tmp_path):
    build(tmp_path, [("alpha", "workflow")])
    result = run(tmp_path, "--emit", "nope")
    assert result.returncode == 1
    assert "no such skill" in result.stderr


def test_the_real_tree_is_structurally_clean():
    """Structure and reachability must be green, or the gate cannot be wired in."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_real_tree_has_zero_text_drift():
    """MT-5 was repaired in v3.17.5 Phase 7; the registries are byte-synced.

    This replaces the Phase 5 test that asserted the drift stayed VISIBLE while
    the backlog existed. The backlog is gone, the gate runs `--strict` in
    `make validate` and CI, and any reappearance is a fresh regression.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT), "--strict"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "registry text drift has reappeared. Every entry's description, "
        "summary_l0, and overview_l1 must match its SKILL.md, which is the "
        "source of truth. Use --emit <skill> for a paste-ready entry.\n"
        + result.stderr
    )
