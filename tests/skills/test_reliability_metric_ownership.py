"""v4.7.0 Phase 5: reliability-metric ownership and the four behavioral rules with their owners.

Two aggregate, data-driven tests per the AGENTS.md retention policy:

1. The pass@k / pass^k definitions live in exactly one owning skill; the two consumers
   reference the owner by name and do not restate the defining phrases.
2. Each of the four behavioral rules is present in its named owner, and the /test versus
   restraint decision is cited from both sides of the boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SK = _ROOT / "catalog" / "skills"

_OWNER = _SK / "developer-experience" / "ai-output-evaluation" / "SKILL.md"
_CONSUMERS = [
    _SK / "workflow" / "skill-eval-loop" / "SKILL.md",
    _SK / "orchestration" / "quality-gate-definitions" / "SKILL.md",
]
_DEFINING_PHRASES = [
    "passes in at least one of k independent trials",
    "passes in all k independent trials",
]

_RULES = {
    "scope-restraint": (
        _SK / "code-cleanup" / "minimal-construction" / "SKILL.md",
        [
            "do not turn scratch checks into permanent test files",
            "test-scope-decision.md",
        ],
    ),
    "compaction-preservation": (
        _SK / "orchestration" / "context-compression" / "SKILL.md",
        ["Preservation contract for client-side summaries", "defect to report"],
    ),
    "append-only-and-batching": (
        _SK / "ai-development" / "claude-agent-sdk" / "SKILL.md",
        ["Append-only history", "Batch independent tool calls"],
    ),
    "non-blocking-delegation": (
        _SK / "orchestration" / "agent-orchestration-primitives" / "SKILL.md",
        ["Non-blocking delegation", "separate wait tool"],
    ),
}
_TEST_COMMAND = _ROOT / "catalog" / "commands" / "test.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_owner_defines_both_metrics_and_the_counting_rules():
    text = _read(_OWNER)
    for phrase in _DEFINING_PHRASES:
        assert text.count(phrase) == 1, phrase
    assert "errored or incomplete trial" in text
    assert "retried trial is not an independent trial" in text
    assert "`ai-output-evaluation` owns these definitions" in text


@pytest.mark.parametrize("path", _CONSUMERS, ids=lambda p: p.parent.name)
def test_consumers_reference_the_owner_without_restating(path: Path):
    text = _read(path)
    assert "[[ai-output-evaluation]]" in text
    for phrase in _DEFINING_PHRASES:
        assert phrase not in text, (
            f"{path.parent.name} restates the definition: {phrase!r}"
        )


@pytest.mark.parametrize("rule", sorted(_RULES), ids=sorted(_RULES))
def test_each_rule_is_present_in_its_owner(rule: str):
    path, markers = _RULES[rule]
    text = _read(path)
    for marker in markers:
        assert marker in text, f"{rule}: {marker!r} missing from {path.parent.name}"


def test_the_test_scope_boundary_is_findable_from_both_sides():
    assert "test-scope-decision.md" in _read(_TEST_COMMAND)
    assert "test-scope-decision.md" in _read(_RULES["scope-restraint"][0])
