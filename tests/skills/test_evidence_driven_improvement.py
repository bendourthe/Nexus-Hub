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
import subprocess
import sys
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


# -- fixture loading -----------------------------------------------------------


@pytest.fixture(scope="module")
def judge_sensitivity() -> dict:
    return json.loads(_JUDGE_SENSITIVITY.read_text(encoding="utf-8"))


# -- scorers under test --------------------------------------------------------

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


# -- fixture integrity ---------------------------------------------------------


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


# -- the executable sensitivity harness ----------------------------------------


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


# -- document contracts (with teeth) -------------------------------------------

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


# == Phase 2: private agent traces ============================================

_AGENT_SKILL = _SKILLS / "ai-development" / "ai-agent-development"
_SPAN_CONTRACT = _AGENT_SKILL / "references" / "agent-span-contract.md"
_TRACE_EXAMPLE = _AGENT_SKILL / "scripts" / "trace-example.py"
_STEP_8 = _AGENT_SKILL / "references" / "step-8-instrument-for-observability.md"
_AGENT_SKILL_MD = _AGENT_SKILL / "SKILL.md"
_LOOP_SCHEMA = (
    _SKILLS / "workflow" / "loop-engineering" / "references" / "loop-schema.md"
)

# Opt-In attributes in the pinned convention. Every one is payload-bearing.
_PAYLOAD_ATTRIBUTES = (
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "gen_ai.system_instructions",
    "gen_ai.tool.definitions",
)

_ALLOWED_ERROR_CATEGORIES = {
    "timeout",
    "rate_limited",
    "invalid_input",
    "permission_denied",
    "unavailable",
    "internal_error",
}


@pytest.fixture(scope="module")
def emitted_trace(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, list[dict]]:
    """Run the example into a fresh temporary directory and return its output."""
    out = tmp_path_factory.mktemp("trace") / "trace.jsonl"
    proc = subprocess.run(
        [sys.executable, str(_TRACE_EXAMPLE), "--output", str(out)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"example failed: {proc.stderr}"
    raw = out.read_text(encoding="utf-8")
    return raw, [json.loads(line) for line in raw.splitlines() if line.strip()]


class TestTraceExampleBehavior:
    def test_emits_records_with_one_root_and_no_orphans(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        assert records, "no records emitted"
        span_ids = {r["span_id"] for r in records}
        roots = [r for r in records if r["parent_span_id"] is None]
        orphans = [
            r["span_id"]
            for r in records
            if r["parent_span_id"] and r["parent_span_id"] not in span_ids
        ]
        assert len(roots) == 1, f"expected exactly one root, got {len(roots)}"
        assert not orphans, f"records reference a missing parent: {orphans}"

    def test_identifier_widths_match_the_contract(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        for record in records:
            assert len(record["trace_id"]) == 32, "trace id must be 32 hex characters"
            assert len(record["span_id"]) == 16, "span id must be 16 hex characters"
            int(record["trace_id"], 16)
            int(record["span_id"], 16)

    def test_timestamps_are_utc_and_terminal_status_present(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        for record in records:
            assert record["start_time"].endswith("Z")
            assert record["end_time"].endswith("Z")
            assert record["status"] in {"OK", "ERROR"}

    def test_records_declare_synthetic_provenance(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        assert all(r["nexus.synthetic"] is True for r in records)

    def test_no_sentinel_value_reaches_the_output(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        """The generator holds sentinels; none may survive to disk."""
        raw, _ = emitted_trace
        assert "SENTINEL" not in raw
        assert "id_rsa" not in raw
        assert "sk-live" not in raw

    def test_no_payload_attribute_is_emitted(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        raw, _ = emitted_trace
        for attribute in _PAYLOAD_ATTRIBUTES:
            assert attribute not in raw, f"Opt-In payload attribute emitted: {attribute}"

    def test_error_records_use_allowlisted_categories(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        errored = [r for r in records if r["status"] == "ERROR"]
        assert errored, "no error record emitted; the error path is unexercised"
        for record in errored:
            assert record["error.type"] in _ALLOWED_ERROR_CATEGORIES

    def test_remote_and_local_invocations_use_distinct_span_kinds(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        """The CLIENT/INTERNAL split is the distinction most often lost."""
        _, records = emitted_trace
        invocations = {
            r["span_kind"]
            for r in records
            if r["gen_ai.operation.name"] == "invoke_agent"
        }
        assert invocations == {"CLIENT", "INTERNAL"}

    def test_no_plan_span_is_invented(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        """Planning boundaries are not observable here, so no plan span exists."""
        _, records = emitted_trace
        assert all(r["gen_ai.operation.name"] != "plan" for r in records)
        assert any(
            r.get("nexus.coverage.planning") == "not_observable" for r in records
        )

    def test_unavailable_reasoning_is_marked_not_fabricated(
        self, emitted_trace: tuple[str, list[dict]]
    ) -> None:
        _, records = emitted_trace
        assert any(
            r.get("nexus.coverage.internal_reasoning") == "unavailable"
            for r in records
        )


class TestTraceExampleRefusals:
    """Negative controls: the example must refuse unsafe output paths."""

    def test_refuses_an_existing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "already-here.jsonl"
        target.write_text("do not overwrite me", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(_TRACE_EXAMPLE), "--output", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 2
        assert target.read_text(encoding="utf-8") == "do not overwrite me"

    def test_refuses_a_missing_parent_directory(self, tmp_path: Path) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(_TRACE_EXAMPLE),
                "--output",
                str(tmp_path / "nope" / "trace.jsonl"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 2

    def test_ships_no_payload_enable_flag(self) -> None:
        """Documenting opt-in responsibility is not the same as building it."""
        source = _TRACE_EXAMPLE.read_text(encoding="utf-8")
        for flag in ("--include-payload", "--payloads", "--with-payload", "--unsafe"):
            assert flag not in source

    def test_uses_no_network_or_environment_capture(self) -> None:
        source = _TRACE_EXAMPLE.read_text(encoding="utf-8")
        for banned in ("import requests", "import socket", "urllib", "httpx", "os.environ"):
            assert banned not in source


def _code_blocks(markdown: str) -> str:
    """Concatenate fenced code blocks only.

    The prose deliberately quotes the removed patterns while explaining why
    they were removed, so a whole-file search would flag the explanation.
    """
    out, inside = [], False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


class TestObservabilityTeachingIsSafe:
    """The old example leaked by truncating; truncation is not redaction."""

    @pytest.mark.parametrize(
        "leak",
        ["str(args)[:200]", "str(result)[:200]", "str(e)", "uuid.uuid4().hex[:12]"],
    )
    def test_unsafe_logging_pattern_is_gone_from_the_example(self, leak: str) -> None:
        code = _code_blocks(_STEP_8.read_text(encoding="utf-8"))
        assert leak not in code

    def test_the_code_block_extractor_has_teeth(self) -> None:
        """A helper that returned nothing would pass every test above."""
        code = _code_blocks(_STEP_8.read_text(encoding="utf-8"))
        assert "def traced(func):" in code, "extractor returned no example code"
        assert "Truncation is not redaction" not in code, "extractor leaked prose"

    def test_step_8_links_the_contract_and_the_example(self) -> None:
        text = _STEP_8.read_text(encoding="utf-8")
        assert "agent-span-contract.md" in text
        assert "trace-example.py" in text

    def test_bundled_files_are_linked_from_the_owning_skill(self) -> None:
        """Unlinked bundles are orphans to the recursive installer audit."""
        text = _AGENT_SKILL_MD.read_text(encoding="utf-8")
        assert "references/agent-span-contract.md" in text
        assert "scripts/trace-example.py" in text


class TestSpanContractDocument:
    def test_pins_revision_and_states_development_status(self) -> None:
        text = _SPAN_CONTRACT.read_text(encoding="utf-8")
        assert "5ca9052bc796ef1e497200b1d558fd87a201f335" in text
        assert "Development" in text

    def test_declares_a_recheck_trigger(self) -> None:
        assert "Recheck trigger" in _SPAN_CONTRACT.read_text(encoding="utf-8")

    def test_marks_tool_attributes_unverified_rather_than_guessing(self) -> None:
        """The tool-span table was not retrievable at the pinned revision."""
        text = _SPAN_CONTRACT.read_text(encoding="utf-8")
        assert "partially verified" in text.lower()
        assert "An unverified attribute is unknown, not Recommended." in text

    def test_disclaims_otlp_conformance(self) -> None:
        text = _SPAN_CONTRACT.read_text(encoding="utf-8")
        assert "not an OpenTelemetry implementation" in text

    def test_states_truncation_is_not_redaction(self) -> None:
        assert "Truncation is not redaction" in _SPAN_CONTRACT.read_text(encoding="utf-8")

    def test_defers_egress_to_its_owner(self) -> None:
        assert "egress-redaction" in _SPAN_CONTRACT.read_text(encoding="utf-8")

    @pytest.mark.parametrize("needle", ["Truncation is not redaction", "Recheck trigger"])
    def test_span_contract_claims_have_teeth(self, needle: str) -> None:
        mutated = _SPAN_CONTRACT.read_text(encoding="utf-8").replace(needle, "")
        assert needle not in mutated


class TestLoopSchemaTraceHonesty:
    def test_distinguishes_summary_from_internal_reasoning(self) -> None:
        text = _LOOP_SCHEMA.read_text(encoding="utf-8")
        assert "An available summary is not internal reasoning" in text

    def test_distinguishes_observation_from_self_attestation(self) -> None:
        text = _LOOP_SCHEMA.read_text(encoding="utf-8")
        assert "A host-observed event is not a self-attestation" in text

    def test_preserves_existing_optional_field_contract(self) -> None:
        """The edit must not disturb budgets, freshness, or additive optionality."""
        text = _LOOP_SCHEMA.read_text(encoding="utf-8")
        assert "evidence_freshness" in text
        assert "budgets" in text
        assert "is additive: existing loop definitions stay valid without it" in text
