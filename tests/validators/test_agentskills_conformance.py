"""Tests for scripts/check_agentskills_conformance.py.

The guard proves the agentskills.io open-standard contract (name + description
present and sized) on every catalog/skills/<category>/<name>/SKILL.md. Extra
Nexus-Hub keys are information, not failures. Name-equals-directory and the
angle-bracket placeholder lint stay in validate_skills.py.
"""

from __future__ import annotations

import json
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py.
from tests.validators._ci_reachability import assert_wired_into_ci

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "check_agentskills_conformance.py"
MAKEFILE = REPO_ROOT / "Makefile"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def write_skill(
    root: Path,
    category: str,
    name: str,
    *,
    description: str = "A valid description for the fixture skill.",
    extra_frontmatter: str = "",
) -> Path:
    skill_dir = root / "catalog" / "skills" / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    extra = f"\n{extra_frontmatter}" if extra_frontmatter else ""
    path = skill_dir / "SKILL.md"
    path.write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f'summary_l0: "Fixture summary"\n'
        f'overview_l1: "Fixture overview paragraph."\n'
        f"{extra.strip()}\n"
        "---\n\n"
        f"# {name}\n\nBody.\n",
        encoding="utf-8",
    )
    return path


def test_real_catalog_conforms(runner) -> None:
    result = runner(SCRIPT, REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_empty_description_fails_naming_the_skill(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "security", "empty-desc", description="")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "empty-desc" in result.stdout
    assert "description is missing or empty" in result.stdout


def test_missing_name_fails(tmp_path: Path, runner) -> None:
    skill_dir = tmp_path / "catalog" / "skills" / "security" / "no-name"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "description: A skill whose name key was omitted on purpose.\n"
        'summary_l0: "Fixture"\n'
        'overview_l1: "Fixture overview."\n'
        "---\n\n# no-name\n",
        encoding="utf-8",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "name is missing or empty" in result.stdout
    assert "no-name" in result.stdout


def test_invalid_name_pattern_fails(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "security", "Bad_Name")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "Bad_Name" in result.stdout
    assert "must match" in result.stdout


def test_extra_keys_are_information_not_failures(tmp_path: Path, runner) -> None:
    write_skill(
        tmp_path,
        "security",
        "extra-keys",
        extra_frontmatter="mitre_f3: [F1010]",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "INFO:" in result.stdout
    assert "summary_l0" in result.stdout
    assert "mitre_f3" in result.stdout


def test_json_report_shape(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "security", "json-ok")
    result = runner(SCRIPT, tmp_path, ["--json"])
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["skills_scanned"] == 1
    assert payload["failures"] == []
    assert "summary_l0" in payload["information"]["extra_top_level_keys"]


def test_new_overlong_description_fails(tmp_path: Path, runner) -> None:
    write_skill(
        tmp_path,
        "security",
        "too-wordy",
        description="x" * 1025,
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "too-wordy" in result.stdout
    assert "1025 characters" in result.stdout


def test_json_report_includes_failures(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "security", "json-empty", description="")
    result = runner(SCRIPT, tmp_path, ["--json"])
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["failures"][0]["skill"] == "json-empty"
    assert payload["failures"][0]["field"] == "description"


def test_collects_all_failures_before_exit(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "security", "empty-one", description="")
    write_skill(tmp_path, "security", "empty-two", description="")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "empty-one" in result.stdout
    assert "empty-two" in result.stdout


def test_makefile_and_ci_invoke_the_guard() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    ci = CI.read_text(encoding="utf-8")
    assert "scripts/check_agentskills_conformance.py" in makefile
    assert_wired_into_ci("check_agentskills_conformance.py")
