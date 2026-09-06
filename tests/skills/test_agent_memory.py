"""Contract tests for the agent-memory skill (v3.19.1 Phase 5)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILL_DIR = _ROOT / "catalog" / "skills" / "workflow" / "agent-memory"
_SKILL = _SKILL_DIR / "SKILL.md"
_TRIGGER_CASES = _SKILL_DIR / "evals" / "trigger-cases.json"
_SKILLS_JSON = _ROOT / "data" / "skills.json"
_SKILL_INDEX = _ROOT / "data" / "SKILL_INDEX.md"
_MARKETPLACE = _ROOT / "data" / "marketplace.json"
_INSTALLER_SH = _ROOT / "scripts" / "installer.sh"
_INSTALLER_PS1 = _ROOT / "scripts" / "installer.ps1"
_MATRIX = _ROOT / "docs" / "policy" / "mcp-reverse-engineering-matrix.md"

SKILL_NAME = "agent-memory"
REQUIRED_FRONTMATTER = ("name", "description", "summary_l0", "overview_l1")
SKIP_SKILLS = (
    "session-query",
    "context-pack-builder",
    "continuous-learning",
    "solution-knowledge-base",
)


@pytest.fixture(scope="module")
def skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def frontmatter(skill_text: str) -> str:
    assert skill_text.startswith("---\n")
    return skill_text.split("---", 2)[1]


def test_frontmatter_has_required_fields(frontmatter: str) -> None:
    for field in REQUIRED_FRONTMATTER:
        assert re.search(rf"^{field}:", frontmatter, re.M), f"missing {field}"
    assert "name: agent-memory" in frontmatter
    assert all(name in frontmatter for name in SKIP_SKILLS)


def test_no_angle_bracket_placeholders(skill_text: str) -> None:
    leftovers = re.findall(r"<[A-Za-z][^>]*>", skill_text)
    assert leftovers == [], f"unfilled placeholders: {leftovers}"


def test_no_upstream_product_name(skill_text: str) -> None:
    lowered = skill_text.lower()
    assert "optmem" not in lowered
    assert "opt-mem" not in lowered


@pytest.mark.parametrize(
    "heading",
    [
        "When to Use This Skill",
        "Instructions",
        "Common Rationalizations",
        "Verification",
        "Related Skills",
    ],
)
def test_has_required_sections(skill_text: str, heading: str) -> None:
    assert re.search(rf"^##\s+{re.escape(heading)}", skill_text, re.M)


def test_trigger_cases_meet_the_minimum_shape() -> None:
    data = json.loads(_TRIGGER_CASES.read_text(encoding="utf-8"))
    assert data["skill"] == SKILL_NAME
    cases = data["cases"]
    positives = [c for c in cases if c["should_trigger"]]
    negatives = [c for c in cases if not c["should_trigger"]]
    assert len(positives) >= 3
    assert len(negatives) >= 3
    named = " ".join(c["assert"] for c in negatives)
    assert "session-query" in named
    assert "context-pack-builder" in named
    assert "continuous-learning" in named


def test_registered_in_three_catalogs() -> None:
    skills = json.loads(_SKILLS_JSON.read_text(encoding="utf-8"))
    matches = [s for s in skills["skills"] if s["name"] == SKILL_NAME]
    assert len(matches) == 1
    assert matches[0]["category"] == "workflow"
    index = _SKILL_INDEX.read_text(encoding="utf-8")
    rows = [ln for ln in index.splitlines() if ln.startswith(f"| {SKILL_NAME} |")]
    assert len(rows) == 1
    marketplace = json.loads(_MARKETPLACE.read_text(encoding="utf-8"))
    workflow = next(c for c in marketplace["categories"] if c["id"] == "workflow")
    json_count = len(skills["skills"])
    index_rows = len(re.findall(r"^\| [a-z0-9-]+ \| ", index, re.M))
    index_total = int(re.search(r"\*\*Total: (\d+) skills", index).group(1))
    marketplace_sum = sum(c["skill_count"] for c in marketplace["categories"])
    assert json_count == index_rows == index_total == marketplace_sum
    workflow_expected = sum(1 for s in skills["skills"] if s["category"] == "workflow")
    assert workflow["skill_count"] == workflow_expected
    assert skills["statistics"]["total_skills"] == json_count


def test_installers_copy_the_extension() -> None:
    sh = _INSTALLER_SH.read_text(encoding="utf-8")
    ps1 = _INSTALLER_PS1.read_text(encoding="utf-8")
    assert "extensions/nexus-memory" in sh
    assert "extensions\\nexus-memory" in ps1
    assert "$nexus_home/nexus-memory" in sh
    assert 'Join-Path $nexusHome "nexus-memory"' in ps1
    assert "mcpServers']['nexus-memory']" not in sh
    assert 'Name = "nexus-memory"' not in ps1


def test_matrix_row_is_already_local() -> None:
    text = _MATRIX.read_text(encoding="utf-8")
    assert "`nexus-memory`" in text
    assert "already-local" in text
    assert "extensions/nexus-memory/" in text
