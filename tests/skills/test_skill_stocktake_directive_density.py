"""Tests for the directive-density review added to skill-stocktake (v3.16.1 Phase 4.3).

Two things need guarding here, and they pull in opposite directions.

The first is that the check must actually discriminate. A quality signal that
marks everything "directive" is worse than no signal, because it produces a
reassuring report while catching nothing. The `classify_section` function below
is a REFERENCE IMPLEMENTATION of the rule the skill states - it is not what the
agent executes, and it is not shipped. Its only job is to demonstrate on
fixtures that the five signals the skill names do separate explanation-only
prose from prose that changes what an agent does. If a future edit weakens those
signals into something vacuous, `test_rule_discriminates_on_fixtures` fails.

The second is that the check must not damage good skills. The obvious
implementation - count imperative verbs, flag a low ratio - would flag the
"Reality" column of every Common Rationalizations table in the catalog, which is
explanatory by design and is the most valuable prose in the schema. So the
contract tests assert the skill states the non-goals explicitly: no ratio, no
word-count metric, no flagging of Tier-3 references, and no removing rationale
to raise the signal. Those are the guardrails that make the check safe to run,
and they are exactly the sort of caveat a later condensing edit drops.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_STOCKTAKE = _ROOT / "catalog" / "skills" / "workflow" / "skill-stocktake" / "SKILL.md"


# --------------------------------------------------------------------------- #
# Reference implementation of the rule (test-only; see module docstring)
# --------------------------------------------------------------------------- #

# The five signals the skill names. A section is `directive` when ANY is present.
_SIGNALS = {
    "observable_action": re.compile(
        r"^\s*(?:\d+\.\s*)?(?:Run|Execute|Write|Add|Record|Compute|Generate|Compare|Invoke)\b.*`",
        re.M,
    ),
    "decision_rule": re.compile(
        r"\b(?:is the default|only when|only for|default to|if .+?, (?:use|pick|choose)|"
        r"prefer .+? over|move to .+? only)\b",
        re.I,
    ),
    "artifact": re.compile(r"`[\w./-]+\.(?:md|json|jsonl|csv|py|sh|ps1)`|`[a-z]+_[a-z_]+`"),
    "gate": re.compile(
        r"\b(?:reject|must not|never|fail(?:s)? the|block(?:s)?|stop and|do not proceed)\b",
        re.I,
    ),
    "verification_condition": re.compile(r"^\s*- \[ \] ", re.M),
}


def classify_section(text: str) -> tuple[str, list[str]]:
    """Return ('directive'|'expository', [signals found]) for one section body."""
    found = [name for name, pattern in _SIGNALS.items() if pattern.search(text)]
    return ("directive" if found else "expository"), found


# Fixtures deliberately chosen to sit near the boundary, not at the extremes.
EXPOSITORY_FIXTURES = {
    "pure_background": (
        "Retrieval-augmented generation combines a retriever with a generator. "
        "The retriever selects passages from a corpus and the generator produces "
        "an answer conditioned on them. This architecture became popular because "
        "it lets a system cite sources without retraining the underlying model."
    ),
    "history_and_motivation": (
        "Evaluation of language models has evolved considerably. Early work "
        "relied on n-gram overlap metrics, which correlate poorly with human "
        "judgment. Later approaches introduced learned metrics, and more "
        "recently practitioners have turned to model-based judges."
    ),
}

DIRECTIVE_FIXTURES = {
    # The target state: one sentence of why, paired with an observable instruction.
    "rationale_plus_action": (
        "Measure retrieval before generation. A model cannot ground an answer in "
        "a passage it never received, so a low faithfulness score on top of low "
        "recall is not a generation problem.\n\n"
        "Run `python scripts/eval_retrieval.py --k 5` before reading any "
        "generation metric."
    ),
    # A decision rule with no command at all - still directive.
    "decision_rule_only": (
        "Pairwise coverage is the default. Most interaction bugs involve two "
        "factors, and pairwise reaches them for roughly a tenth of the cost of "
        "full cartesian coverage. Move to 3-tuple only for a specific "
        "interaction you have reason to suspect."
    ),
    # A Common Rationalizations style entry: mostly explanation, but it names a
    # gate. This is the fixture that would fail under a verb-ratio rule.
    "rationalization_entry": (
        "| \"The output looks good, so it passes\" | \"Looks good\" is the "
        "verbosity-bias trap this skill exists to break; a 100-line function "
        "that reads well can still fail a correctness dimension. Never accept a "
        "score without an evidence quote. |"
    ),
    "verification_checklist": (
        "Confirm the following before declaring the phase done.\n\n"
        "- [ ] The output file exists at the recorded path\n"
        "- [ ] All tests pass\n"
    ),
}


@pytest.fixture(scope="module")
def stocktake() -> str:
    return _STOCKTAKE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# The rule discriminates
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("name", sorted(EXPOSITORY_FIXTURES))
def test_explanation_only_content_is_flagged(name: str) -> None:
    verdict, found = classify_section(EXPOSITORY_FIXTURES[name])
    assert verdict == "expository", (
        f"Fixture {name!r} is pure background with nothing an agent can act on, "
        f"but the rule found signals {found} and marked it directive. A signal "
        "set that matches explanation is vacuous and the report it produces is "
        "reassuring noise."
    )


@pytest.mark.parametrize("name", sorted(DIRECTIVE_FIXTURES))
def test_actionable_content_passes(name: str) -> None:
    verdict, found = classify_section(DIRECTIVE_FIXTURES[name])
    assert verdict == "directive", (
        f"Fixture {name!r} contains something an agent can act on, but the rule "
        "found no signal and flagged it as expository. False positives here are "
        "worse than false negatives: they argue for deleting good prose."
    )


def test_rationale_paired_with_instruction_is_not_flagged() -> None:
    """The explicit non-goal, asserted directly.

    A section that pairs one sentence of why with an observable instruction is
    the target state. If the rule ever flags it, the signal starts arguing for
    stripping rationale, which is the failure mode the skill's non-goals name.
    """
    verdict, found = classify_section(DIRECTIVE_FIXTURES["rationale_plus_action"])
    assert verdict == "directive" and found, (
        "Rationale paired with an observable instruction must classify as "
        "directive. Flagging it would make the signal argue for removing the "
        "explanation that makes the instruction followable."
    )


def test_rationalization_table_entry_survives() -> None:
    """A Common Rationalizations entry is mostly prose and must still pass.

    This is the fixture a verb-ratio implementation would flag, and it is the
    single most valuable prose in the Nexus-Hub skill schema.
    """
    verdict, _ = classify_section(DIRECTIVE_FIXTURES["rationalization_entry"])
    assert verdict == "directive", (
        "A Common Rationalizations entry citing a concrete failure mode and "
        "naming a gate must not be flagged as expository."
    )


def test_rule_discriminates_on_fixtures() -> None:
    """The whole point: the rule must separate the two groups, not pass everything."""
    expository = {n: classify_section(t)[0] for n, t in EXPOSITORY_FIXTURES.items()}
    directive = {n: classify_section(t)[0] for n, t in DIRECTIVE_FIXTURES.items()}

    assert set(expository.values()) == {"expository"}, (
        f"Expository fixtures were not all flagged: {expository}"
    )
    assert set(directive.values()) == {"directive"}, (
        f"Directive fixtures were not all passed: {directive}"
    )


# --------------------------------------------------------------------------- #
# The skill states the check and its guardrails
# --------------------------------------------------------------------------- #

def test_skill_declares_the_directive_density_step(stocktake: str) -> None:
    assert re.search(r"[Dd]irective[- ][Dd]ensity", stocktake), (
        "skill-stocktake must define the directive-density review. It is the "
        "only part of the stocktake that catches a skill which passes every "
        "structural check and still does not change what the agent does."
    )


@pytest.mark.parametrize(
    "signal",
    ["observable action", "decision rule", "artifact", "gate", "verification condition"],
)
def test_skill_names_each_signal(stocktake: str, signal: str) -> None:
    assert signal in stocktake, (
        f"The directive-density step must name the {signal!r} signal. The five "
        "together are what make the per-section question answerable without a "
        "numeric threshold."
    )


def test_check_is_advisory_not_a_gate(stocktake: str) -> None:
    section = stocktake.split("Directive-density review", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"advisory", section, re.I), (
        "The directive-density review must be declared advisory. A quality "
        "signal promoted to a gate gets optimized against."
    )
    assert re.search(r"never (?:fails|blocks)", section, re.I), (
        "The step must state that it never fails a run or blocks a merge."
    )


def test_check_forbids_a_ratio_or_word_count(stocktake: str) -> None:
    section = stocktake.split("Directive-density review", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"imperative-verb ratio|word-count", section, re.I), (
        "The non-goals must explicitly forbid an imperative-verb ratio or "
        "word-count metric. That is the obvious implementation, and it would "
        "flag every Common Rationalizations table in the catalog."
    )


def test_check_protects_rationale_and_required_sections(stocktake: str) -> None:
    section = stocktake.split("Directive-density review", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"not slop", section, re.I) or re.search(
        r"must not be removed", section, re.I
    ), (
        "The non-goals must state that concise rationale explaining a failure "
        "mode is not slop and must not be removed to raise directive density."
    )
    assert "Common Rationalizations" in section and "Verification" in section, (
        "The non-goals must name the two required sections the signal must "
        "never argue for shortening."
    )


def test_check_exempts_tier3_references(stocktake: str) -> None:
    section = stocktake.split("Directive-density review", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"references/", section), (
        "The non-goals must exempt Tier-3 reference files. Under the three-tier "
        "model those exist to carry the explanation that does not belong in the "
        "body, so expository prose there is correct, not a defect."
    )


def test_check_is_bounded(stocktake: str) -> None:
    section = stocktake.split("Directive-density review", 1)[1].split("\n### ", 1)[0]
    assert re.search(r"cap at \d+|at most \d+", section, re.I), (
        "The review must be bounded (a cap on sections sampled per skill). An "
        "unbounded holistic pass over a 271-skill catalog is too slow to run "
        "routinely, and a check that stops being run guards nothing."
    )


def test_stocktake_verification_covers_the_new_step(stocktake: str) -> None:
    section = stocktake.split("## Verification", 1)[1].split("\n## ", 1)[0]
    assert re.search(r"directive", section, re.I), (
        "The Verification checklist must cover the directive-density review, "
        "including that it emits no ratio, threshold, or pass/fail verdict."
    )


def test_stocktake_remains_ascii_and_within_the_size_norm(stocktake: str) -> None:
    assert stocktake.isascii(), "English Markdown in this repo is ASCII-only."
    lines = len(stocktake.split("\n"))
    assert lines <= 500, (
        f"skill-stocktake is {lines} lines, over the 500-line Tier-2 target."
    )
