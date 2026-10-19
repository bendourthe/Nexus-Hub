"""Every catalog agent must have an intentional model classification."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RATIONALE = ROOT / "docs/releases/v4/v4.14/development/agent-pinning-rationale.md"
if not RATIONALE.is_file():
    RATIONALE = ROOT / "docs/archives/v4/v4.14/development/agent-pinning-rationale.md"


def test_every_agent_has_exactly_one_model_classification():
    rationale = RATIONALE.read_text(encoding="utf-8")
    pinned_text, unpinned_text = rationale.split("## Deliberately unpinned", 1)
    pinned_text = pinned_text.split("## Pinned agents", 1)[1]
    unpinned_text = unpinned_text.split("## Platform compatibility", 1)[0]
    row = r"^\| `([a-z0-9-]+)` \| (.+) \|$"
    documented_pins = {name for name, _ in re.findall(row, pinned_text, re.MULTILINE)}
    unpinned = {name for name, _ in re.findall(row, unpinned_text, re.MULTILINE)}
    names = set()
    pinned = set()
    for path in sorted((ROOT / "catalog/agents").glob("*.md")):
        names.add(path.stem)
        content = path.read_text(encoding="utf-8")
        assert content.startswith("---\n"), path.name
        frontmatter = yaml.safe_load(content.split("---", 2)[1])
        if "model" in frontmatter:
            assert frontmatter["model"] in {"opus", "sonnet", "haiku"}, path.name
            assert frontmatter["model"] == "opus", path.name
            pinned.add(path.stem)
    assert names, "catalog roster is empty"
    assert pinned == documented_pins, "catalog pins disagree with the documented Opus partition"
    assert not pinned & unpinned, (
        "agent cannot be both pinned and deliberately unpinned"
    )
    assert names == pinned | unpinned, (
        f"unclassified: {sorted(names - pinned - unpinned)}; stale: {sorted((pinned | unpinned) - names)}"
    )


def test_valid_but_wrong_tier_is_rejected(monkeypatch, tmp_path):
    import shutil
    import sys

    import pytest

    shutil.copytree(ROOT / "catalog/agents", tmp_path / "catalog/agents")
    agent = tmp_path / "catalog/agents/security-reviewer.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("model: opus", "model: haiku"), encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    with pytest.raises(AssertionError, match="security-reviewer"):
        test_every_agent_has_exactly_one_model_classification()
