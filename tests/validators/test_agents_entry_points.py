"""Validate the runtime debugging entry-point table in AGENTS.md."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.lib.integrations import INTEGRATION_REGISTRY


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS = REPO_ROOT / "AGENTS.md"
CONTRACT = REPO_ROOT / "docs" / "policy" / "platform-read-contracts.json"
EVAL_SKILL = (
    REPO_ROOT / "catalog" / "skills" / "workflow" / "skill-eval-loop" / "SKILL.md"
)
HEADING = "### Runtime integration debugging entry points"
ROW = re.compile(
    r"^\| (?P<label>[^|]+?) \| `(?P<key>[^`]+)` \| `(?P<path>[^`]+)` \|$"
)


def _entry_rows() -> dict[str, tuple[str, str]]:
    text = AGENTS.read_text(encoding="utf-8")
    section = text.split(HEADING, 1)[1].split("\n### ", 1)[0]
    rows: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        match = ROW.match(line)
        if match:
            rows[match.group("key")] = (match.group("label"), match.group("path"))
    return rows


def test_entry_point_table_covers_the_live_integration_registry() -> None:
    rows = _entry_rows()

    assert set(rows) == set(INTEGRATION_REGISTRY)
    for key, integration in INTEGRATION_REGISTRY.items():
        label, documented_path = rows[key]
        expected_path = f"{type(integration).__module__.replace('.', '/')}.py"
        assert label == integration.display_name
        assert documented_path == expected_path


def test_every_documented_entry_point_exists() -> None:
    for _label, documented_path in _entry_rows().values():
        path = REPO_ROOT / documented_path
        assert path.is_file(), f"missing runtime entry point: {documented_path}"


def test_every_read_contract_runtime_has_a_documented_entry_point() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract_keys = set(contract["contract_checks"])

    assert contract_keys <= set(_entry_rows())


def test_eval_safety_contract_names_boundaries_and_consequences() -> None:
    text = EVAL_SKILL.read_text(encoding="utf-8")
    section = text.split("## Eval-code safety contract", 1)[1].split("\n## ", 1)[0]

    required_phrases = (
        "Never execute, import, source, or pass model output to a shell",
        "Touching production systems or unrelated user files can corrupt state",
        "Perform no externally visible action beyond the declared provider inference request",
        "An unbounded loop can create uncontrolled spend",
        "Omitting this provenance makes the score irreproducible",
        "A unit test that reaches a provider can leak fixture data",
        "[[ai-billing-safeguards]]",
    )
    for phrase in required_phrases:
        assert phrase in section
