"""Structure and pinned-wording contracts for agent-orchestration-primitives.

Two things make this skill fragile to edit. It is cross-linked from many other
skills, so a renamed or renumbered step silently breaks their references; and
its escalation gate carries wording other skills quote ("a concrete, measured
problem"), so a rewrite that reads as an improvement can quietly widen the
gate. The pinned-wording tests below exist to make that change loud.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = (
    ROOT / "catalog" / "skills" / "orchestration" / "agent-orchestration-primitives"
)
SKILL_MD = SKILL_DIR / "SKILL.md"

BODY_LINE_CEILING = 500

# Captured from `git show HEAD:...SKILL.md` BEFORE the v4.8.0 Phase 2 edit, per
# the plan's instruction to pin it rather than retype it. Widening the gate now
# requires editing this constant, which is a visible decision in review.
PINNED_STEP_4_MEASURED_PROBLEM = (
    '1. **The problem from Step 2 is real and named** (not "it feels big").'
)
PINNED_ESCALATION_SENTENCE = (
    "Escalate only when Step 2 names a concrete, measured problem."
)

SCORECARD_RELATIVE_LINK = (
    "../../workflow/loop-engineering/references/loop-readiness-scorecard.md"
)

# Every file bundled beside SKILL.md must be linked from it (AGENTS.md orphan rule).
BUNDLED_FILES = (
    "references/five-patterns.md",
    "references/graph-readiness-checklist.md",
    "assets/example-fanout-workflow.js",
)

AUTONOMY_RUNGS = (
    "Prompt or chat",
    "Deterministic workflow",
    "Delegated chunk",
    "Single goal loop",
    "Persistent loop",
    "Graph",
)

CHECKLIST = SKILL_DIR / "references" / "graph-readiness-checklist.md"


def _body() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_step_0_exists_and_precedes_step_1() -> None:
    """Ordering is the point: an autonomy decision taken after the structure is
    chosen is a justification, not a decision."""
    body = _body()
    step0 = body.find("### Step 0:")
    step1 = body.find("### Step 1:")
    assert step0 != -1, "Step 0 autonomy ladder is missing"
    assert step1 != -1, "Step 1 is missing"
    assert step0 < step1, "Step 0 must appear before Step 1"


@pytest.mark.parametrize("rung", AUTONOMY_RUNGS)
def test_autonomy_ladder_declares_every_rung(rung: str) -> None:
    body = _body()
    ladder = body.split("### Step 0:", 1)[1].split("\n### ", 1)[0]
    assert rung in ladder, f"the autonomy ladder omits the {rung!r} rung"


def test_autonomy_ladder_selects_by_the_three_named_inputs() -> None:
    ladder = _body().split("### Step 0:", 1)[1].split("\n### ", 1)[0]
    assert SCORECARD_RELATIVE_LINK in ladder, (
        "the ladder must select on the loop-engineering readiness score; without "
        "it, rung choice is back to taste"
    )
    assert "blast radius" in ladder
    assert "Reversibility" in ladder or "reversibility" in ladder


def test_scorecard_link_from_the_ladder_actually_resolves() -> None:
    """A relative link into another skill's bundle is easy to get wrong and
    nothing at runtime reports a 404."""
    target = (SKILL_DIR / SCORECARD_RELATIVE_LINK).resolve()
    assert target.is_file(), f"the ladder's scorecard link does not resolve: {target}"


def test_minimum_sufficient_autonomy_rule_is_stated() -> None:
    ladder = _body().split("### Step 0:", 1)[1].split("\n### ", 1)[0]
    assert "Minimum sufficient autonomy" in ladder
    assert "do not add three" in ladder, (
        "the rule needs its concrete form, not just its name"
    )


def test_ladder_is_marked_as_operator_recorded_not_a_platform_setting() -> None:
    """The retired v3.17.0 toggle was a lever; conflating the two would invite a
    reader to look for a setting that does not exist."""
    ladder = _body().split("### Step 0:", 1)[1].split("\n### ", 1)[0]
    assert "not a platform setting" in ladder
    assert "v3.17.0" in ladder


def test_step_4_measured_problem_wording_is_unchanged() -> None:
    assert PINNED_STEP_4_MEASURED_PROBLEM in _body(), (
        "the Step 4 escalation-gate wording changed; it is quoted by other skills, "
        "so update this pin deliberately or restore the sentence"
    )


def test_step_1_escalation_wording_is_unchanged() -> None:
    assert PINNED_ESCALATION_SENTENCE in _body()


def test_step_4_cites_the_checklist_as_the_gate_condition() -> None:
    body = _body()
    step4 = body.split("### Step 4:", 1)[1].split("\n### ", 1)[0]
    assert "references/graph-readiness-checklist.md" in step4, (
        "Step 4 must name the checklist as the gate condition for a graph"
    )


@pytest.mark.parametrize("bundled", BUNDLED_FILES)
def test_bundled_file_exists_and_is_linked(bundled: str) -> None:
    assert (SKILL_DIR / bundled).is_file(), f"missing bundled file {bundled}"
    assert bundled in _body(), (
        f"{bundled} is an orphan bundle: nothing in SKILL.md links to it"
    )


def test_body_stays_under_the_size_norm() -> None:
    lines = len(_body().splitlines())
    assert lines <= BODY_LINE_CEILING, (
        f"SKILL.md is {lines} lines, over the {BODY_LINE_CEILING}-line norm"
    )


def test_checklist_declares_six_signals_and_eight_gate_items() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    signals = text.split("## Six signals", 1)[1].split("\n## ", 1)[0]
    assert len(re.findall(r"^- \*\*", signals, flags=re.MULTILINE)) == 6, (
        "expected exactly six graph-helps signals"
    )
    items = re.findall(r"^- \[ \] ", text, flags=re.MULTILINE)
    assert len(items) == 8, f"expected exactly eight checklist items, found {len(items)}"


def test_checklist_first_item_requires_a_measured_not_predicted_failure() -> None:
    """This is the item the plan's verification expectation turns on: a graph is
    entered on an observed single-loop limitation, never an anticipated one."""
    text = CHECKLIST.read_text(encoding="utf-8")
    first = re.search(r"^- \[ \] (.*)$", text, flags=re.MULTILINE).group(1)
    assert "measured" in first
    assert "Not a predicted one." in text


def test_checklist_states_the_fan_out_economics() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "## The economics" in text
    assert "deliberate" in text.split("## The economics", 1)[1]


def test_checklist_is_attributed_generically() -> None:
    """Reverse-engineering attribution rule: no external repo, product, or
    evaluation metric named in a distributed artifact."""
    text = CHECKLIST.read_text(encoding="utf-8").lower()
    for banned in ("field guide", "the article", "blog post"):
        assert banned not in text, f"checklist names an external source: {banned!r}"
