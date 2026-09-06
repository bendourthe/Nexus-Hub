"""Durable contracts for the v4.0.0 documentation-tree prescription."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
# Located by NAME, not by lifecycle stage. A decision record legitimately moves
# proposed/ -> implemented/ at release, so pinning the stage guarantees this test
# breaks on every promotion -- which is exactly what it did at the v4.0.0 release.
_DECISION_NAME = "2026-08-20-docs-tree-organised-by-lifespan.md"
_DECISION_MATCHES = sorted((ROOT / "docs/decisions").rglob(_DECISION_NAME))
assert _DECISION_MATCHES, f"decision record {_DECISION_NAME} not found under docs/decisions/"
assert len(_DECISION_MATCHES) == 1, f"decision record {_DECISION_NAME} exists in more than one lifecycle stage: {_DECISION_MATCHES}"
DECISION = _DECISION_MATCHES[0]
DOCS_LAYOUT = ROOT / "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md"


def test_decision_records_required_alternatives() -> None:
    content = DECISION.read_text(encoding="utf-8")

    assert "## Alternatives considered" in content
    for required in (
        "development",
        "process/",
        "living reference",
        "ADRs",
        "opt-in profile",
        "`archives/` only",
        "plain `mv`",
    ):
        assert required in content


def test_docs_layout_declares_breaking_v2_prescription() -> None:
    content = DOCS_LAYOUT.read_text(encoding="utf-8")

    assert "version: 2.0.0" in content
    assert "## Migration from 1.x" in content
    assert "docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/" in content
    assert "docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/" in content
    assert "audit-docs.py canonicalize-layout --root ./docs" in content


def test_generated_registry_drops_pre_v311_versions_shape() -> None:
    registry_path = ROOT / "data/skills.json"
    raw = registry_path.read_text(encoding="utf-8")
    registry = json.loads(raw)
    docs_layout = next(skill for skill in registry["skills"] if skill["name"] == "docs-layout-refactor")

    assert "docs/versions" not in raw
    assert docs_layout["version"] == "2.0.0"
    assert "docs/releases/" in docs_layout["description"]
    assert "docs/archives/" in docs_layout["overview_l1"]


def test_old_placeholder_paths_are_explicitly_legacy() -> None:
    old_path = re.compile(r"docs/v<MAJOR>|docs/archive/")
    offenders: list[str] = []

    for base in (ROOT / "catalog", ROOT / "templates"):
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(lines, start=1):
                if old_path.search(line) and not re.search(r"legacy|migration-source", line, re.IGNORECASE):
                    offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

    assert not offenders, "\n".join(offenders)
