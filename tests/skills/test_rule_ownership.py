"""Rule ownership: each rule lives in one owner, and the skills that reach it hand off by name.

One data-driven aggregate test per the AGENTS.md retention policy. Each row names a rule, the
file that owns it, a distinctive clause of the rule (never its title, so a handoff that names the
rule does not trip the check), the token a non-owner uses to name the owner, and the non-owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SK = _ROOT / "catalog" / "skills"


@dataclass(frozen=True)
class Rule:
    rule: str
    owner: Path
    anchor: str
    owner_name: str
    non_owners: tuple[Path, ...]


_HANDOFF_SITES = (
    _SK / "workflow" / "incremental-implementation" / "SKILL.md",
    _SK / "workflow" / "implement-phase" / "references" / "implement-phase-runbook.md",
)

RULES = (
    Rule(
        rule="refactor-first",
        owner=_SK / "developer-experience" / "refactoring-expert" / "SKILL.md",
        anchor="verified green before the change it makes room for",
        owner_name="[[refactoring-expert]]",
        non_owners=_HANDOFF_SITES,
    ),
    Rule(
        rule="design-invariants",
        owner=_SK / "code-cleanup" / "code-simplification" / "references" / "design-invariants.md",
        anchor="A new helper beside old copies is one more duplicate",
        owner_name="references/design-invariants.md",
        non_owners=_HANDOFF_SITES,
    ),
    Rule(
        rule="prompt-cache-stability",
        owner=_SK / "ai-development" / "prompt-engineering" / "references" / "step-8-optimize-cost-and-latency.md",
        anchor="any byte change anywhere in the prefix invalidates everything after it",
        owner_name="step-8-optimize-cost-and-latency.md",
        non_owners=(
            _SK / "ai-development" / "model-routing" / "SKILL.md",
            _ROOT / "docs" / "policy" / "model-routing-in-plan-and-implement.md",
            _ROOT / "catalog" / "commands" / "implement.md",
        ),
    ),
    Rule(
        rule="tool-call-decision-policy",
        owner=_SK / "ai-development" / "ai-agent-development" / "references" / "decision-policy-harness.md",
        anchor="pure policy function returns the verdict",
        owner_name="references/decision-policy-harness.md",
        non_owners=(_SK / "ai-development" / "ai-agent-development" / "SKILL.md",),
    ),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _id(path: Path) -> str:
    parts = path.relative_to(_SK).parts[1:] if _SK in path.parents else path.relative_to(_ROOT).parts
    return "/".join(parts)


@pytest.mark.parametrize("row", RULES, ids=[r.rule for r in RULES])
def test_each_rule_lives_in_its_owner_and_is_only_handed_off_elsewhere(row: Rule) -> None:
    assert row.owner.is_file(), f"{row.rule}: owner {_id(row.owner)} is missing"
    assert row.anchor in _read(row.owner), f"{row.rule}: owner {_id(row.owner)} lacks its anchor clause"
    for path in row.non_owners:
        text = _read(path)
        assert row.owner_name in text, f"{row.rule}: {_id(path)} is missing the handoff to {row.owner_name}"
        # A copy-paste tripwire, not proof of single ownership: it catches the owner's distinctive
        # clause pasted into a non-owner, while a paraphrased restatement still needs review.
        assert row.anchor not in text, f"{row.rule}: {_id(path)} restates the owner's rule"


@pytest.mark.parametrize("path", [
    _SK / "ai-development" / "model-routing" / "SKILL.md",
    _ROOT / "docs" / "policy" / "model-routing-in-plan-and-implement.md",
    _ROOT / "catalog" / "commands" / "implement.md",
    _SK / "workflow" / "implement-phase" / "references" / "implement-phase-runbook.md",
], ids=_id)
def test_the_upshift_names_its_cache_cost_where_it_is_described(path: Path) -> None:
    # The owner link alone is not enough: model-routing already linked step-8 before this rule existed.
    text = _read(path)
    assert "sub-task boundary" in text, f"{_id(path)} lacks the sub-task-boundary upshift rule"
    assert "step-8-optimize-cost-and-latency.md" in text, f"{_id(path)} does not hand cache details to step-8"


def test_the_harness_reference_names_no_hosted_scorer_endpoint() -> None:
    # A hosted per-call scorer would send every tool call, arguments included, to a third party.
    text = _read(_SK / "ai-development" / "ai-agent-development" / "references" / "decision-policy-harness.md")
    assert "http://" not in text and "https://" not in text
