from __future__ import annotations

from pathlib import Path

from devai_skill_server.catalog import SkillCatalog
from devai_skill_server.config import ServerConfig
from devai_skill_server.types import DetailLevel, SkillFull, SkillOverview, SkillSummary


def _make_config(root: Path) -> ServerConfig:
    return ServerConfig(
        hub_root=root,
        skills_json_path=root / "data" / "skills.json",
        bundles_json_path=root / "data" / "bundles.json",
        catalog_skills_dir=root / "catalog" / "skills",
    )


def test_load_catalog(sample_skills_json: Path):
    """Catalog loads skills and bundles from JSON files."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    assert catalog.is_loaded
    assert len(catalog.get_all_skill_names()) == 3


def test_get_skill_l0(sample_skills_json: Path):
    """L0 retrieval returns SkillSummary with summary_l0 field."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    skill = catalog.get_skill("code-review-security", DetailLevel.L0)
    assert isinstance(skill, SkillSummary)
    assert skill.name == "code-review-security"
    assert "OWASP" in skill.summary_l0


def test_get_skill_l1(sample_skills_json: Path):
    """L1 retrieval returns SkillOverview with overview_l1 and tags."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    skill = catalog.get_skill("ai-agent-development", DetailLevel.L1)
    assert isinstance(skill, SkillOverview)
    assert "agents" in skill.tags
    assert len(skill.overview_l1) > 50


def test_get_skill_l2_with_content(sample_skills_with_content: Path):
    """L2 retrieval returns SkillFull with file content."""
    catalog = SkillCatalog(_make_config(sample_skills_with_content))
    catalog.load()
    skill = catalog.get_skill("kubernetes-ops", DetailLevel.L2)
    assert isinstance(skill, SkillFull)
    assert "Full content for kubernetes-ops" in skill.content


def test_get_skill_l2_missing_file(sample_skills_json: Path):
    """L2 retrieval with missing SKILL.md returns graceful error."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    skill = catalog.get_skill("code-review-security", DetailLevel.L2)
    assert isinstance(skill, SkillFull)
    assert "not found" in skill.content.lower() or "unavailable" in skill.content.lower()


def test_get_skill_not_found(sample_skills_json: Path):
    """Non-existent skill returns None."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    assert catalog.get_skill("nonexistent-skill") is None


def test_find_closest_match(sample_skills_json: Path):
    """Closest match suggests similar skill names."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    match = catalog.find_closest_match("kubernets-ops")
    assert match == "kubernetes-ops"


def test_list_categories(sample_skills_json: Path):
    """Categories list includes all distinct categories."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    categories = catalog.list_categories()
    cat_names = {c.name for c in categories}
    assert "Code Review" in cat_names
    assert "AI Development" in cat_names
    assert "Infrastructure" in cat_names


def test_list_bundles(sample_skills_json: Path):
    """Bundles load correctly with skill lists."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    bundles = catalog.list_bundles()
    assert len(bundles) == 2
    assert bundles[0].id == "core-developer"


def test_get_bundle(sample_skills_json: Path):
    """Get specific bundle by ID."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    bundle = catalog.get_bundle("devops-engineer")
    assert bundle is not None
    assert "kubernetes-ops" in bundle.skills


def test_get_bundle_not_found(sample_skills_json: Path):
    """Non-existent bundle returns None."""
    catalog = SkillCatalog(_make_config(sample_skills_json))
    catalog.load()
    assert catalog.get_bundle("nonexistent") is None
