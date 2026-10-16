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
    _, unpinned_text = rationale.split("## Deliberately unpinned", 1)
    unpinned_text = unpinned_text.split("## Platform compatibility", 1)[0]
    row = r"^\| `([a-z0-9-]+)` \| (.+) \|$"
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
            pinned.add(path.stem)
    assert names, "catalog roster is empty"
    assert not pinned & unpinned, (
        "agent cannot be both pinned and deliberately unpinned"
    )
    assert names == pinned | unpinned, (
        f"unclassified: {sorted(names - pinned - unpinned)}; stale: {sorted((pinned | unpinned) - names)}"
    )
