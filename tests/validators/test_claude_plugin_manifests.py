"""Structural contract for the Claude Code plugin/marketplace manifests.

`claude plugin validate . --strict` is the vendor checker and is not a CI
dependency. These tests prove the durable invariants that checker cares about
using only stdlib JSON and the catalog on disk: marketplace schema shape,
plugin.json component paths, full-catalog skill exposure (every category
directory listed), and no hooks/MCP on the plugin path.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CATALOG_SKILLS = REPO_ROOT / "catalog" / "skills"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace_manifest_has_required_schema_fields() -> None:
    data = _load(MARKETPLACE_JSON)
    assert data["name"] == "nexus-hub"
    owner = data["owner"]
    assert isinstance(owner, dict)
    assert owner.get("name")
    plugins = data["plugins"]
    assert isinstance(plugins, list) and plugins, "plugins array must be non-empty"
    plugin = plugins[0]
    assert plugin["name"] == "nexus-hub"
    assert plugin["source"] == "./"
    assert "version" not in plugin, (
        "omit plugins[].version so plugin.json remains the only pin "
        "(Claude Code prefers plugin.json without warning when both are set)"
    )
    assert "version" not in data, (
        "omit marketplace-level version; check_version_sync canonical is plugin.json"
    )


def test_plugin_json_points_at_catalog_commands_and_agents() -> None:
    data = _load(PLUGIN_JSON)
    assert data["name"] == "nexus-hub"
    assert data["version"]
    assert data["commands"] == "./catalog/commands"
    assert data["agents"] == "./catalog/agents"
    assert (REPO_ROOT / "catalog" / "commands").is_dir()
    assert (REPO_ROOT / "catalog" / "agents").is_dir()
    assert "hooks" not in data
    assert "mcpServers" not in data


def test_plugin_json_skills_match_every_catalog_category() -> None:
    data = _load(PLUGIN_JSON)
    listed = data["skills"]
    assert isinstance(listed, list) and listed, "skills must be the category path list"
    expected = [
        f"./catalog/skills/{p.name}"
        for p in sorted(CATALOG_SKILLS.iterdir())
        if p.is_dir()
    ]
    assert listed == expected, (
        "plugin.json skills drifted from catalog/skills/ on disk. "
        "Add or remove the category path in .claude-plugin/plugin.json."
    )
    for rel in listed:
        folder = REPO_ROOT / rel[2:] if rel.startswith("./") else REPO_ROOT / rel
        skill_mds = list(folder.glob("*/SKILL.md"))
        assert skill_mds, f"{rel} has no skill folders with SKILL.md"
