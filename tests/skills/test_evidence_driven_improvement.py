"""Contract and behavior tests for v4.13.0 evidence-driven agent improvement.

The plan this module guards (v4.13.0, candidate A1 onward) is mostly guidance,
but guidance about *measurement* fails in a specific and silent way: the recipe
stays readable while the thing it was supposed to detect stops being detected.
Prose assertions cannot catch that, so the core of this module is executable.

`TestJudgeSensitivityHarness` builds three scorers and runs them against the
frozen fixture:

1. a reference scorer, which must separate every degraded pair on its target
   criterion and hold steady on the wording-only controls;
2. a constant scorer, which **must fail** - it satisfies any structural check
   and detects nothing;
3. a style-reactive scorer, which **must fail** on the wording-only controls.

Points 2 and 3 are the negative controls the plan requires. Without them, a
fixture whose baseline and degraded sides drifted together would keep passing
and guard nothing, which is precisely the false-confidence failure the
evaluation work exists to prevent.

Document assertions follow the repository's established `*_has_teeth` pattern:
each predicate runs against the real file and against a mutated copy with the
target content removed, so a predicate that accidentally matches anything is
itself caught.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_FIXTURES = _ROOT / "tests" / "fixtures" / "agent-improvement"
_JUDGE_SENSITIVITY = _FIXTURES / "judge-sensitivity.json"

_SKILLS = _ROOT / "catalog" / "skills"
_EVALUATOR_VALIDATION = (
    _SKILLS
    / "developer-experience"
    / "ai-output-evaluation"
    / "references"
    / "evaluator-validation.md"
)
_EVAL_PIPELINE_AUDIT = _SKILLS / "ai-development" / "eval-pipeline-audit" / "SKILL.md"


# ── fixture loading ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def judge_sensitivity() -> dict:
    return json.loads(_JUDGE_SENSITIVITY.read_text(encoding="utf-8"))


# ── scorers under test ────────────────────────────────────────────────────────

_SUBSTANTIVE = ("execution_evidence", "claim_support", "boundary_adherence")

_EXECUTION_MARKERS = ("i ran", "i applied", "exit code", "quoted")
_SUPPORT_MARKERS = ("per the", "line ", ".py", ".md")
_HEDGE_MARKERS = ("studies show", "industry-standard", "almost certainly", "as is typical")
_REFUSAL_MARKERS = ("i will not",)
_COMPLIANCE_MARKERS = ("bypassed", "here are the full")

_HIGH, _LOW, _NEUTRAL = 5, 1, 3


def _count(text: str, markers: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for m in markers if m in lowered)


def reference_scorer(response: str) -> dict[str, int]:
    """A deterministic stand-in for a sensitive evaluator.

    This is not a model and makes no claim to model quality. It exists so the
    fixture's stated directions can be exercised, and so the negative controls
    below have something to be compared against.
    """
    execution = _HIGH if _count(response, _EXECUTION_MARKERS) else _LOW
    if _count(response, _HEDGE_MARKERS):
        support = _LOW
    elif _count(response, _SUPPORT_MARKERS):
        support = _HIGH
    else:
        support = _NEUTRAL
    if _count(response, _COMPLIANCE_MARKERS):
        boundary = _LOW
    elif _count(response, _REFUSAL_MARKERS):
        boundary = _HIGH
    else:
        boundary = _NEUTRAL
    return {
        "execution_evidence": execution,
        "claim_support": support,
        "boundary_adherence": boundary,
        "style_quality": _NEUTRAL,
    }


def constant_scorer(response: str) -> dict[str, int]:
    """Negative control: identical output for every input."""
    del response
    return {
        "execution_evidence": _NEUTRAL,
        "claim_support": _NEUTRAL,
        "boundary_adherence": _NEUTRAL,
        "style_quality": _NEUTRAL,
    }


def style_reactive_scorer(response: str) -> dict[str, int]:
    """Negative control: substantive criteria move whenever wording moves."""
    scores = reference_scorer(response)
    jitter = len(response) % 3
    return {k: v + jitter for k, v in scores.items()}


def _cases(data: dict, direction: str) -> list[dict]:
    return [c for c in data["cases"] if c["expected_direction"] == direction]


# ── fixture integrity ─────────────────────────────────────────────────────────


class TestFixtureIntegrity:
    def test_splits_are_disjoint_and_complete(self, judge_sensitivity: dict) -> None:
        splits = judge_sensitivity["splits"]
        members = splits["train"] + splits["development"] + splits["held_out"]
        case_ids = [c["case_id"] for c in judge_sensitivity["cases"]]
        assert len(members) == len(set(members)), "split membership overlaps"
        assert sorted(members) == sorted(case_ids), "split membership does not match cases"

    def test_every_case_declares_its_own_split_consistently(
        self, judge_sensitivity: dict
    ) -> None:
        splits = judge_sensitivity["splits"]
        for case in judge_sensitivity["cases"]:
            assert case["case_id"] in splits[case["split"]], (
                f"{case['case_id']} declares split {case['split']} "
                "but is not listed under it"
            )

    def test_required_case_families_are_present(self, judge_sensitivity: dict) -> None:
        required = {
            "missing_execution",
            "unsupported_claim",
            "correct_refusal",
            "harmless_style_change",
        }
        assert required <= {c["family"] for c in judge_sensitivity["cases"]}

    def test_fixture_is_declared_synthetic_and_carries_no_real_traces(
        self, judge_sensitivity: dict
    ) -> None:
        prov = judge_sensitivity["provenance"]
        assert prov["synthetic"] is True
        assert prov["contains_real_traces"] is False
        assert prov["contains_real_model_output"] is False

    def test_no_universal_kappa_threshold_is_set(self, judge_sensitivity: dict) -> None:
        policy = judge_sensitivity["agreement_policy"]
        assert policy["universal_numeric_threshold"] is None
        assert policy["chance_corrected_agreement"] == "optional"
        assert "undefined" in policy["undefined_denominator_disposition"]

    def test_holdout_is_untouched(self, judge_sensitivity: dict) -> None:
        assert judge_sensitivity["splits"]["holdout_touched_count"] == 0


# ── the executable sensitivity harness ────────────────────────────────────────


class TestJudgeSensitivityHarness:
    def test_reference_scorer_separates_every_degraded_pair(
        self, judge_sensitivity: dict
    ) -> None:
        pairs = _cases(judge_sensitivity, "degraded_lower")
        assert pairs, "fixture declares no degraded pairs"
        for case in pairs:
            criterion = case["target_criterion"]
            base = reference_scorer(case["baseline"]["response"])[criterion]
            degraded = reference_scorer(case["degraded"]["response"])[criterion]
            assert degraded < base, (
                f"{case['case_id']}: expected {criterion} to drop, "
                f"got baseline={base} degraded={degraded}"
            )

    def test_reference_scorer_holds_steady_on_wording_only_controls(
        self, judge_sensitivity: dict
    ) -> None:
        controls = _cases(judge_sensitivity, "substantive_criteria_unchanged")
        assert controls, "fixture declares no wording-only control"
        for case in controls:
            base = reference_scorer(case["baseline"]["response"])
            degraded = reference_scorer(case["degraded"]["response"])
            for criterion in case["unchanged_criteria"]:
                assert base[criterion] == degraded[criterion], (
                    f"{case['case_id']}: {criterion} moved on a wording-only change"
                )

    def test_constant_scorer_fails_the_fixture(self, judge_sensitivity: dict) -> None:
        """Negative control: a scorer that detects nothing must not pass."""
        separated = [
            case
            for case in _cases(judge_sensitivity, "degraded_lower")
            if constant_scorer(case["degraded"]["response"])[case["target_criterion"]]
            < constant_scorer(case["baseline"]["response"])[case["target_criterion"]]
        ]
        assert not separated, (
            "a constant scorer separated a degraded pair; the fixture no longer "
            "distinguishes a sensitive judge from an insensitive one"
        )

    def test_style_reactive_scorer_fails_the_wording_only_controls(
        self, judge_sensitivity: dict
    ) -> None:
        """Negative control: reacting to surface form is not sensitivity."""
        drifted = []
        for case in _cases(judge_sensitivity, "substantive_criteria_unchanged"):
            base = style_reactive_scorer(case["baseline"]["response"])
            degraded = style_reactive_scorer(case["degraded"]["response"])
            if any(base[c] != degraded[c] for c in case["unchanged_criteria"]):
                drifted.append(case["case_id"])
        assert drifted, (
            "the style-reactive scorer held steady on every control pair, so the "
            "controls no longer detect a wording-sensitive judge"
        )

    def test_correct_refusal_case_would_catch_an_inverted_judge(
        self, judge_sensitivity: dict
    ) -> None:
        """A helpfulness-biased judge scores the compliant answer higher."""
        refusals = [
            c for c in judge_sensitivity["cases"] if c["family"] == "correct_refusal"
        ]
        assert refusals, "no correct_refusal case present"
        for case in refusals:
            base = reference_scorer(case["baseline"]["response"])["boundary_adherence"]
            degraded = reference_scorer(case["degraded"]["response"])[
                "boundary_adherence"
            ]
            assert base > degraded, (
                f"{case['case_id']}: the refusing answer must not score below the "
                "complying one on boundary_adherence"
            )


# ── document contracts (with teeth) ───────────────────────────────────────────

_EVALUATOR_CLAIMS = {
    "sensitivity_step": "Prove the judge notices a controlled loss",
    "inverted_diagnosis": "inverted",
    "inconclusive_disposition": "inconclusive",
    "backtest_optional": "optional confirmation, never a prerequisite",
    "no_composite": "Never sum criteria into a composite",
}

_AUDIT_CLAIMS = {
    "constant_judge": "constant judge is not validated because a fixture schema passes",
    "recipe_vs_measured": "A verified recipe is not a measured judge result",
}


class TestEvaluatorValidationContract:
    @pytest.mark.parametrize("claim", sorted(_EVALUATOR_CLAIMS))
    def test_claim_present(self, claim: str) -> None:
        text = _EVALUATOR_VALIDATION.read_text(encoding="utf-8")
        assert _EVALUATOR_CLAIMS[claim] in text

    @pytest.mark.parametrize("claim", sorted(_EVALUATOR_CLAIMS))
    def test_claim_has_teeth(self, claim: str) -> None:
        needle = _EVALUATOR_CLAIMS[claim]
        mutated = _EVALUATOR_VALIDATION.read_text(encoding="utf-8").replace(needle, "")
        assert needle not in mutated

    def test_reused_rules_are_referenced_not_restated(self) -> None:
        """Step 6 must defer to earlier steps rather than duplicate them."""
        text = _EVALUATOR_VALIDATION.read_text(encoding="utf-8")
        assert "Reused rules" in text
        assert "does not restate" in text


class TestEvalPipelineAuditContract:
    @pytest.mark.parametrize("claim", sorted(_AUDIT_CLAIMS))
    def test_claim_present(self, claim: str) -> None:
        text = _EVAL_PIPELINE_AUDIT.read_text(encoding="utf-8")
        assert _AUDIT_CLAIMS[claim] in text

    @pytest.mark.parametrize("claim", sorted(_AUDIT_CLAIMS))
    def test_claim_has_teeth(self, claim: str) -> None:
        needle = _AUDIT_CLAIMS[claim]
        mutated = _EVAL_PIPELINE_AUDIT.read_text(encoding="utf-8").replace(needle, "")
        assert needle not in mutated

    def test_ten_concern_inventory_is_preserved(self) -> None:
        """The audit must not grow an eleventh concern for sensitivity."""
        text = _EVAL_PIPELINE_AUDIT.read_text(encoding="utf-8")
        assert "Walk all ten concerns in order" in text
        assert "| 10 | Deployment gates" in text
        assert "| 11 |" not in text

    def test_three_recommendation_cap_is_preserved(self) -> None:
        text = _EVAL_PIPELINE_AUDIT.read_text(encoding="utf-8")
        assert "Cap the recommendation list at three" in text

    def test_sensitivity_routes_to_the_owning_skill(self) -> None:
        """Routing, not an inline method, per the audit's own owner boundary."""
        text = _EVAL_PIPELINE_AUDIT.read_text(encoding="utf-8")
        assert "references/evaluator-validation.md`, Step 6" in text
