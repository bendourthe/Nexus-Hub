"""Every catalog agent must declare a documented effort ceiling.

Decision D1 of the v4.15.9 plan: an opus-pinned agent declares ``effort: high`` so
a session raised to ``xhigh`` or ``max`` no longer spreads that cost to every
helper it spawns. A fast-tier agent declares whatever its row in
``docs/reference/agent-classification.md`` records, or nothing when the row says
``Effort: none``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CLASSIFICATION = ROOT / "docs/reference/agent-classification.md"
LEVELS = {"low", "medium", "high", "xhigh", "max"}
ROW = r"^\| `([a-z0-9-]+)` \| (.+) \|$"


def _fast_tier_effort() -> dict[str, str | None]:
    """Map each fast-tier agent to its recorded effort, or None for no declaration."""
    text = CLASSIFICATION.read_text(encoding="utf-8")
    fast_text = text.split("## Fast-tier agents", 1)[1].split("## Effort", 1)[0]
    recorded: dict[str, str | None] = {}
    for name, reason in re.findall(ROW, fast_text, re.MULTILINE):
        match = re.search(r"Effort: (none|`([a-z]+)`)", reason)
        assert match, f"fast-tier row for {name} records no effort decision"
        recorded[name] = match.group(2)
    return recorded


def _frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n"), f"{path.name}: no frontmatter"
    try:
        meta = yaml.safe_load(content.split("---", 2)[1])
    except yaml.YAMLError as exc:  # an unparseable block must fail, never pass
        raise AssertionError(f"{path.name}: unparseable frontmatter ({exc})") from exc
    assert isinstance(meta, dict), f"{path.name}: frontmatter is not a mapping"
    return meta


def test_every_agent_declares_a_documented_effort():
    fast = _fast_tier_effort()
    agents = sorted((ROOT / "catalog/agents").glob("*.md"))
    assert agents, "catalog roster is empty"
    for path in agents:
        meta = _frontmatter(path)
        if path.stem in fast:
            expected = fast[path.stem]
            if expected is None:
                assert "effort" not in meta, f"{path.stem}: row records no effort"
            else:
                assert meta.get("effort") == expected, path.stem
            continue
        assert "effort" in meta, f"{path.stem}: no effort declaration"
        assert (
            meta["effort"] in LEVELS
        ), f"{path.stem}: invalid effort {meta['effort']!r}"
        if meta.get("model") == "opus":
            assert (
                meta["effort"] == "high"
            ), f"{path.stem}: opus agent must declare effort high"


@pytest.mark.parametrize(
    ("old", "new"),
    [("effort: high\n", ""), ("effort: high\n", "effort: max\n")],
    ids=["removed", "raised-to-max"],
)
def test_missing_or_raised_effort_is_rejected(monkeypatch, tmp_path, old, new):
    import shutil
    import sys

    shutil.copytree(ROOT / "catalog/agents", tmp_path / "catalog/agents")
    shutil.copytree(ROOT / "docs/reference", tmp_path / "docs/reference")
    agent = tmp_path / "catalog/agents/security-reviewer.md"
    text = agent.read_text(encoding="utf-8")
    assert old in text
    agent.write_text(text.replace(old, new), encoding="utf-8")
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module, "CLASSIFICATION", tmp_path / "docs/reference/agent-classification.md"
    )
    with pytest.raises(AssertionError, match="security-reviewer"):
        test_every_agent_declares_a_documented_effort()
