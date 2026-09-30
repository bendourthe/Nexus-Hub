"""The run goal is restated in three surfaces, and all three point at one verdict (v4.13.6 T056).

`/implement`, the mandatory final-phase template (inside N.10), and `/update release`
each carry a short "Run goal" block. The redundancy is useful only while every copy
names the same checker verdicts, links the completion contract that owns them, and
restates no predicate: a copy that grew its own definition of done would drift from
the checker. Definition of Done 7 also requires each copy to say plainly what an
agent can do when the native goal is missing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from .test_completion_contract_ownership import CONTRACT, _predicate_ids

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENT = REPO_ROOT / "catalog" / "commands" / "implement.md"
UPDATE = REPO_ROOT / "catalog" / "commands" / "update.md"
TEMPLATE = REPO_ROOT / "catalog" / "skills" / "workflow" / "implementation-plan" / "references" / "mandatory-final-phase.md"
RUNBOOK = REPO_ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "references" / "implement-phase-runbook.md"
VERDICT = re.compile(r"\b(PLAN COMPLETE|MINOR COMPLETE|INCOMPLETE|BLOCKED|PAUSED)\b")
# The minor-level ids the per-plan regex in the ownership test does not match.
MINOR_ID = re.compile(r"`((?:members|member|minor|archive|gaps|cleanup)\.[a-z-]+)`")
CONDITIONAL = "When the run record's scope is minor, the minor close in the runbook follows the last member's release."
N4_NEW = "Report branch hygiene; removal happens only through `cleanup_merged.py --apply` under a recorded approval."
N4_OLD = "Report only; never delete branches."


def _section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.count(heading + "\n") == 1, f"{path.name}: {heading!r} must appear exactly once"
    return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


def _template_block() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    n10 = text.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    blocks = [line for line in n10.splitlines() if line.startswith("> **Run goal.**")]
    assert len(blocks) == 1, "the final-phase template carries one Run goal block, inside N.10"
    return blocks[0]


BLOCKS = {
    "implement": lambda: _section(IMPLEMENT, "## Run goal"),
    "final-phase": _template_block,
    "update-release": lambda: _section(UPDATE, "## release scope: run goal"),
}


def _all_ids() -> set[str]:
    return _predicate_ids() | set(MINOR_ID.findall(CONTRACT.read_text(encoding="utf-8")))


def test_the_three_blocks_name_the_same_verdicts() -> None:
    verdicts = {name: set(VERDICT.findall(read())) for name, read in BLOCKS.items()}
    assert verdicts["implement"] == {"PLAN COMPLETE", "MINOR COMPLETE"}, verdicts
    assert len({frozenset(v) for v in verdicts.values()}) == 1, verdicts


@pytest.mark.parametrize("name", sorted(BLOCKS))
def test_each_block_links_the_completion_contract(name: str) -> None:
    assert "implement-phase/references/completion-contract.md" in BLOCKS[name]()


@pytest.mark.parametrize("name", sorted(BLOCKS))
def test_each_block_names_no_predicate_id(name: str) -> None:
    block = BLOCKS[name]()
    ids = _all_ids()
    assert {"gaps.minor", "minor.close-pr", "archive.minor", "cleanup.merged"} <= ids  # the list is the contract's
    named = sorted(pid for pid in ids if re.search(rf"(?<![\w.-]){re.escape(pid)}(?![\w-])", block))
    assert not named, f"{name} restates predicate ids: {named}"


@pytest.mark.parametrize("name", sorted(BLOCKS))
def test_each_block_is_honest_about_the_native_goal(name: str) -> None:
    block = BLOCKS[name]()
    assert "should already be set by the user's approval paste" in block
    assert "ask the user to paste the printed goal line again, because an agent cannot set it" in block
    assert "`nexus-hub run-plan` is the only fully automatic path" in block


def test_final_phase_adds_one_conditional_minor_line_only() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    n10 = text.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    assert text.count(CONDITIONAL) == 1 and CONDITIONAL in n10
    for owned in ("minor_close.py", "migrate", "archive --minor"):
        assert owned not in n10, f"N.10 restates the minor close procedure ({owned})"


@pytest.mark.parametrize("path", [TEMPLATE, RUNBOOK], ids=["final-phase", "runbook"])
def test_git_tree_hygiene_routes_removal_through_the_executor(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert N4_OLD not in text
    assert text.count(N4_NEW) == 1
