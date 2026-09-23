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

Document assertions follow the repository's `*_has_teeth` pattern through
`assert_has_teeth`, which asserts the needle IS present in the real file before
asserting it is gone from a mutated copy. The first half is the load-bearing
one: an earlier version of these controls asserted only the second half, which
is a property of `str.replace` and holds whether or not the needle was ever
there, so a silently reworded guard still passed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load_trace_example_module():
    """Import the bundled trace script so its guards can be unit-tested directly.

    The subprocess tests prove end-to-end behavior; these in-process checks
    reach the branches a shell cannot express, such as a NUL byte in a path.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("_trace_example", _TRACE_EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_has_teeth(path: Path, needle: str) -> None:
    """Prove a document guard is neither vacuous nor unfalsifiable.

    An earlier version of this helper asserted only `needle not in
    document.replace(needle, "")`. That is a property of `str.replace`, not of
    the guard: it holds identically whether or not the needle was ever in the
    file, so a guard whose needle had been silently reworded still passed. The
    load-bearing half is the first assertion, which fails when the needle is
    absent; the second then confirms removal is complete, which is not free
    because an overlapping needle can reappear ("aabb".replace("ab", "") ==
    "ab").
    """
    text = path.read_text(encoding="utf-8")
    assert needle in text, f"vacuous guard: {needle!r} is absent from {path}"
    mutated = text.replace(needle, "")
    assert needle not in mutated, f"mutation left {needle!r} in place in {path}"


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
        """Negative control: a scorer that detects nothing must not pass.

        The earlier form asserted only that the constant scorer separated
        nothing. That is a property of the constant scorer (`c < c` is false for
        every input), not of the fixture, so it passed on an EMPTY fixture and on
        one whose degraded side had collapsed onto its baseline. What carries the
        meaning is the pair of verdicts together: the reference scorer must
        separate these pairs and the constant scorer must not. A fixture that
        stopped discriminating fails the first half.
        """
        pairs = _cases(judge_sensitivity, "degraded_lower")
        assert pairs, "the fixture declares no degraded pairs, so it guards nothing"

        def separates(scorer) -> list:
            return [
                case
                for case in pairs
                if scorer(case["degraded"]["response"])[case["target_criterion"]]
                < scorer(case["baseline"]["response"])[case["target_criterion"]]
            ]

        assert len(separates(reference_scorer)) == len(pairs), (
            "the reference scorer no longer separates every degraded pair; the "
            "fixture has stopped discriminating and the control below is vacuous"
        )
        assert not separates(constant_scorer), (
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
    # Single words ("inverted", "inconclusive") occurred in unrelated checklist
    # lines, so the governing guidance could be deleted with the tests green.
    "inverted_diagnosis": "Insensitive and inverted are different diagnoses",
    "inconclusive_disposition": "An inconclusive result is a real outcome",
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
        assert_has_teeth(_EVALUATOR_VALIDATION, _EVALUATOR_CLAIMS[claim])

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
        assert_has_teeth(_EVAL_PIPELINE_AUDIT, _AUDIT_CLAIMS[claim])

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
        assert "private-key" not in raw
        assert "/srv/secrets" not in raw
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

    def test_refuses_a_nul_byte_in_the_path(self) -> None:
        """A NUL made `Path.exists()` swallow a ValueError, so the path was accepted."""
        module = _load_trace_example_module()
        with pytest.raises(ValueError, match="NUL"):
            module.resolve_output("trace\x00.jsonl")

    def test_refuses_a_symlinked_target(self, tmp_path: Path) -> None:
        """The final component must never be followed."""
        real = tmp_path / "real.jsonl"
        real.write_text("do not overwrite me", encoding="utf-8")
        link = tmp_path / "link.jsonl"
        try:
            link.symlink_to(real)
        except (OSError, NotImplementedError):
            pytest.skip("this host does not permit creating a symlink")
        proc = subprocess.run(
            [sys.executable, str(_TRACE_EXAMPLE), "--output", str(link)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 2
        assert real.read_text(encoding="utf-8") == "do not overwrite me"

    def test_a_redirected_ancestor_is_disclosed_rather_than_hidden(self, tmp_path: Path) -> None:
        """A junction or symlink above the file must be named in the output.

        Refusing every redirected ancestor was tried and rejected, because on
        macOS `/tmp` and `$TMPDIR` are themselves symlinks and this script
        documents a temporary directory as its intended destination. What is
        required instead is that the caller is told where the bytes landed.
        """
        module = _load_trace_example_module()
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("this host does not permit creating a directory symlink")

        described = module.describe_destination(link / "trace.jsonl")
        assert "an ancestor redirects" in described

    def test_an_ordinary_path_is_not_described_as_redirected(self, tmp_path: Path) -> None:
        """Control for the test above: no false positive on a plain path.

        Comparing a resolved path against an unresolved one would fail here on
        Windows, where `resolve()` also expands 8.3 short names.
        """
        module = _load_trace_example_module()
        described = module.describe_destination(tmp_path / "trace.jsonl")
        assert "an ancestor redirects" not in described

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
        assert_has_teeth(_SPAN_CONTRACT, needle)


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


# === Phase 3: approved lessons to regression evidence ===

_LIFECYCLE = _FIXTURES / "improvement-lifecycle.json"
_CONTINUOUS_LEARNING = _SKILLS / "workflow" / "continuous-learning" / "SKILL.md"
_IMPROVEMENT_LOOP = (
    _SKILLS
    / "workflow"
    / "continuous-learning"
    / "references"
    / "verified-improvement-loop.md"
)
_SKILL_EVAL_LOOP = _SKILLS / "workflow" / "skill-eval-loop" / "SKILL.md"


@pytest.fixture(scope="module")
def lifecycle() -> dict:
    return json.loads(_LIFECYCLE.read_text(encoding="utf-8"))


def evaluate_checks(content: str, checks: list[dict]) -> dict[str, bool]:
    """The independent oracle.

    It reads only the artifact content and the check definitions. It never
    consults a candidate's `expected_*` fields, so the tests below compare a
    derived disposition against a declared one rather than restating it.
    """
    results: dict[str, bool] = {}
    for check in checks:
        if check["kind"] == "must_contain":
            results[check["check_id"]] = check["value"] in content
        elif check["kind"] == "must_not_contain":
            results[check["check_id"]] = check["value"] not in content
        else:  # pragma: no cover - guarded by a test below
            raise ValueError(f"unknown check kind: {check['kind']}")
    return results


def derive_disposition(content: str, checks: list[dict]) -> tuple[str, bool, bool]:
    """Approve only when the seeded failure closes AND nothing else broke."""
    results = evaluate_checks(content, checks)
    seeded = [c["check_id"] for c in checks if c.get("role") == "seeded_failure"]
    existing = [c["check_id"] for c in checks if c.get("role") == "existing_regression"]
    seeded_ok = all(results[c] for c in seeded)
    existing_ok = all(results[c] for c in existing)
    disposition = "approved" if seeded_ok and existing_ok else "rejected"
    return disposition, seeded_ok, existing_ok


def record_dispositions(records: list[dict]) -> dict[str, str]:
    """Fail closed on a repeated id or a contradictory disposition."""
    seen: dict[str, str] = {}
    for record in records:
        cid = record["candidate_id"]
        if cid in seen:
            raise ValueError(
                f"{cid} already recorded as {seen[cid]}; refusing to overwrite "
                f"with {record['disposition']}"
            )
        seen[cid] = record["disposition"]
    return seen


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestImprovementLifecycleReplay:
    """A deterministic replay over a disposable file. No model, no network."""

    def test_the_seeded_failure_is_real_on_the_original(self, lifecycle: dict) -> None:
        """If the original already passed, the whole exercise proves nothing."""
        results = evaluate_checks(
            lifecycle["artifact"]["original_content"], lifecycle["checks"]
        )
        seeded = [c for c in lifecycle["checks"] if c.get("role") == "seeded_failure"]
        assert seeded, "fixture declares no seeded failure"
        for check in seeded:
            assert results[check["check_id"]] is False, (
                f"{check['check_id']} passes on the original content, so there is "
                "no failure for a candidate to close"
            )

    def test_existing_checks_pass_on_the_original(self, lifecycle: dict) -> None:
        results = evaluate_checks(
            lifecycle["artifact"]["original_content"], lifecycle["checks"]
        )
        for check in lifecycle["checks"]:
            if check.get("role") == "existing_regression":
                assert results[check["check_id"]] is True, (
                    f"{check['check_id']} already fails on the original; it cannot "
                    "serve as a regression guard"
                )

    def test_derived_disposition_matches_the_declared_one(
        self, lifecycle: dict
    ) -> None:
        """The oracle decides; the fixture only states what it should decide."""
        for candidate in lifecycle["candidates"]:
            disposition, seeded_ok, existing_ok = derive_disposition(
                candidate["content"], lifecycle["checks"]
            )
            assert disposition == candidate["expected_disposition"], (
                f"{candidate['candidate_id']}: oracle derived {disposition}, "
                f"fixture expects {candidate['expected_disposition']}"
            )
            assert seeded_ok == candidate["expected_seeded_check_passes"]
            assert existing_ok == candidate["expected_existing_checks_pass"]

    def test_approved_candidate_closes_the_failure_and_keeps_regressions(
        self, lifecycle: dict, tmp_path: Path
    ) -> None:
        approved = [
            c for c in lifecycle["candidates"]
            if c["expected_disposition"] == "approved"
        ]
        assert approved, "fixture declares no approved candidate"
        target = tmp_path / lifecycle["artifact"]["filename"]
        target.write_text(lifecycle["artifact"]["original_content"], encoding="utf-8")

        for candidate in approved:
            target.write_text(candidate["content"], encoding="utf-8")
            disposition, seeded_ok, existing_ok = derive_disposition(
                target.read_text(encoding="utf-8"), lifecycle["checks"]
            )
            assert disposition == "approved"
            assert seeded_ok and existing_ok

    def test_rejected_candidate_restores_prior_bytes_exactly(
        self, lifecycle: dict, tmp_path: Path
    ) -> None:
        """Byte-exact rollback, not merely 'revert the intent'."""
        target = tmp_path / lifecycle["artifact"]["filename"]
        original = lifecycle["artifact"]["original_content"]
        target.write_text(original, encoding="utf-8")
        sha_before = _sha256(target)

        rejected = [
            c for c in lifecycle["candidates"]
            if c["expected_disposition"] == "rejected"
        ]
        assert rejected, "fixture declares no rejected candidate"

        for candidate in rejected:
            target.write_text(candidate["content"], encoding="utf-8")
            assert _sha256(target) != sha_before, "candidate did not change the file"

            disposition, _, _ = derive_disposition(
                target.read_text(encoding="utf-8"), lifecycle["checks"]
            )
            assert disposition == "rejected"

            # Rollback.
            target.write_text(original, encoding="utf-8")
            assert _sha256(target) == sha_before, (
                f"{candidate['candidate_id']}: rollback did not restore prior bytes"
            )

    def test_a_candidate_that_trades_safety_for_the_target_metric_is_rejected(
        self, lifecycle: dict
    ) -> None:
        """The case a target-metric-only checker would wrongly accept."""
        trap = next(
            c for c in lifecycle["candidates"] if c["candidate_id"] == "CAND-0045"
        )
        disposition, seeded_ok, existing_ok = derive_disposition(
            trap["content"], lifecycle["checks"]
        )
        assert seeded_ok is True, "the trap must actually close the seeded failure"
        assert existing_ok is False, "the trap must break an existing regression"
        assert disposition == "rejected"
        broken = [
            cid
            for cid, ok in evaluate_checks(trap["content"], lifecycle["checks"]).items()
            if not ok
        ]
        assert broken == trap["expected_broken_checks"]

    def test_holdout_is_never_the_regression_pool(self, lifecycle: dict) -> None:
        regression = lifecycle["regression"]
        assert regression["pool"] in {"train", "development"}
        assert regression["never_holdout"] is True

    def test_measurement_frame_is_frozen_before_scoring(self, lifecycle: dict) -> None:
        frame = lifecycle["measurement_frame"]
        assert frame["frozen_before_scoring"] is True
        assert frame["rubric_version"]
        assert frame["split_manifest"]

    def test_fixture_carries_no_real_session_or_production_data(
        self, lifecycle: dict
    ) -> None:
        prov = lifecycle["provenance"]
        assert prov["synthetic"] is True
        assert prov["contains_real_sessions"] is False
        assert prov["contains_production_data"] is False

    def test_oracle_rejects_an_unknown_check_kind(self) -> None:
        """A silently ignored check kind would pass everything."""
        with pytest.raises(ValueError):
            evaluate_checks("anything", [{"check_id": "X", "kind": "vibes", "value": "y"}])


class TestLifecycleFailsClosed:
    @pytest.mark.parametrize("case_id", ["FC-1", "FC-2"])
    def test_declared_fail_closed_cases_raise(
        self, lifecycle: dict, case_id: str
    ) -> None:
        case = next(c for c in lifecycle["fail_closed_cases"] if c["case_id"] == case_id)
        assert case["must_fail_closed"] is True
        with pytest.raises(ValueError):
            record_dispositions(case["records"])

    def test_distinct_candidates_are_accepted(self) -> None:
        """The guard must not reject legitimate distinct records."""
        result = record_dispositions(
            [
                {"candidate_id": "CAND-0044", "disposition": "approved"},
                {"candidate_id": "CAND-0045", "disposition": "rejected"},
            ]
        )
        assert result == {"CAND-0044": "approved", "CAND-0045": "rejected"}


class TestImprovementLoopDocument:
    @pytest.mark.parametrize(
        "claim",
        [
            "No automatic base-instruction edits",
            "No model training or fine-tuning",
            "No background observer",
            "The checker must be independent of the candidate",
            "Byte-exact restoration is the requirement",
        ],
    )
    def test_claim_present(self, claim: str) -> None:
        assert claim in _IMPROVEMENT_LOOP.read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "claim",
        [
            "The checker must be independent of the candidate",
            "Byte-exact restoration is the requirement",
        ],
    )
    def test_claim_has_teeth(self, claim: str) -> None:
        assert_has_teeth(_IMPROVEMENT_LOOP, claim)

    def test_chain_links_to_its_owners_rather_than_restating_them(self) -> None:
        text = _IMPROVEMENT_LOOP.read_text(encoding="utf-8")
        for owner in (
            "ai-output-evaluation",
            "skill-eval-loop",
            "loop-engineering",
            "error-analysis.md",
            "evaluator-validation.md",
        ):
            assert owner in text

    def test_linked_from_the_owning_skill(self) -> None:
        text = _CONTINUOUS_LEARNING.read_text(encoding="utf-8")
        assert "references/verified-improvement-loop.md" in text


class TestGraduationPoolContract:
    def test_graduation_stays_in_its_original_pool(self) -> None:
        text = _SKILL_EVAL_LOOP.read_text(encoding="utf-8")
        assert "stays in the pool it already belonged to" in text

    def test_holdout_never_becomes_tuning_input(self) -> None:
        text = _SKILL_EVAL_LOOP.read_text(encoding="utf-8")
        assert "never becomes tuning input" in text

    def test_missing_owner_blocks_a_promoted_learning(self) -> None:
        text = _SKILL_EVAL_LOOP.read_text(encoding="utf-8")
        assert "record the coverage as incomplete and stop" in text
        assert "do not mint a promoted learning on partial coverage" in text

    def test_existing_gates_are_preserved(self) -> None:
        text = _SKILL_EVAL_LOOP.read_text(encoding="utf-8")
        assert "the user approves" in text
        assert "immutable base is not edited" in text
        assert "verifier stays independent" in text

    def test_no_skill_retirement_was_introduced(self) -> None:
        """Phase 3 retires nothing; retirement stays the existing advisory rule."""
        text = _SKILL_EVAL_LOOP.read_text(encoding="utf-8")
        assert "it is RETIRED with a recorded reason" in text


# === Phase 4: smallest useful visual explanation ===

_REPRESENTATION = _FIXTURES / "representation-cases.json"
_HTML_CONVENTIONS = (
    _SKILLS / "developer-experience" / "html-output-conventions" / "SKILL.md"
)
_AGENT_COMMUNICATION = (
    _SKILLS / "developer-experience" / "agent-communication" / "SKILL.md"
)
_COMMS_STYLE_GUIDE = _ROOT / "catalog" / "style-guides" / "agent-communication.md"


@pytest.fixture(scope="module")
def representation() -> dict:
    return json.loads(_REPRESENTATION.read_text(encoding="utf-8"))


class TestRepresentationCases:
    def test_every_ladder_rung_that_matters_has_a_scenario(
        self, representation: dict
    ) -> None:
        covered = {c["expected_rung"] for c in representation["cases"]}
        for rung in ("table", "pseudocode", "mermaid", "html"):
            assert rung in covered, f"no scenario expects the {rung} rung"

    def test_expected_rungs_are_on_the_declared_ladder(
        self, representation: dict
    ) -> None:
        ladder = set(representation["ladder"])
        for case in representation["cases"]:
            assert case["expected_rung"] in ladder

    def test_no_case_expects_what_it_forbids(self, representation: dict) -> None:
        """A self-contradictory case would be satisfiable either way."""
        for case in representation["cases"]:
            assert case["expected_rung"] not in case["must_not_be"], (
                f"{case['case_id']} both expects and forbids {case['expected_rung']}"
            )

    def test_both_near_misses_are_present_and_point_opposite_ways(
        self, representation: dict
    ) -> None:
        near = [c for c in representation["cases"] if "near_miss_of" in c]
        assert len(near) >= 2, "fewer than two near-misses"
        directions = {c["near_miss_of"] for c in near}
        assert "html" in directions, "no near-miss guarding against over-climbing"
        assert "prose" in directions, "no near-miss guarding against over-collapsing"

    def test_short_static_table_must_not_force_html(
        self, representation: dict
    ) -> None:
        case = next(
            c for c in representation["cases"] if c["case_id"] == "REP-5-near-miss"
        )
        assert case["expected_rung"] == "table"
        assert "html" in case["must_not_be"]

    def test_interactive_state_comparison_must_not_collapse_to_prose(
        self, representation: dict
    ) -> None:
        case = next(
            c for c in representation["cases"] if c["case_id"] == "REP-6-near-miss"
        )
        assert case["expected_rung"] == "html"
        assert "prose" in case["must_not_be"]

    def test_responsibility_list_is_not_accepted_for_topology(
        self, representation: dict
    ) -> None:
        case = next(c for c in representation["cases"] if c["case_id"] == "REP-7")
        assert "responsibility_list" in case["must_not_be"]

    def test_ascii_box_diagram_is_excluded_wherever_a_diagram_applies(
        self, representation: dict
    ) -> None:
        diagram_cases = [
            c for c in representation["cases"] if c["expected_rung"] == "mermaid"
        ]
        assert diagram_cases
        for case in diagram_cases:
            assert "ascii_box_diagram" in case["must_not_be"] or any(
                inv["invariant_id"] == "INV-2"
                and case["case_id"] in inv["applies_to"]
                for inv in representation["invariants"]
            )

    def test_invariants_reference_real_cases(self, representation: dict) -> None:
        ids = {c["case_id"] for c in representation["cases"]}
        for invariant in representation["invariants"]:
            assert invariant["applies_to"], f"{invariant['invariant_id']} applies to nothing"
            for case_id in invariant["applies_to"]:
                assert case_id in ids, f"{invariant['invariant_id']} names unknown {case_id}"

    def test_fixture_does_not_claim_a_comprehension_result(
        self, representation: dict
    ) -> None:
        prov = representation["provenance"]
        assert prov["synthetic"] is True
        assert "comprehension" in prov["not_evidence_of"]


class TestRepresentationOwner:
    def test_ladder_exists_with_its_rungs(self) -> None:
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "The smallest useful representation" in text
        for rung in ("Small table", "Pseudocode", "Mermaid diagram", "HTML artifact"):
            assert rung in text

    def test_short_answer_needs_no_file(self) -> None:
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "A short answer must not require creating or opening a file." in text

    def test_ascii_box_diagrams_stay_excluded(self) -> None:
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "Decorative ASCII box diagrams remain excluded at every rung" in text

    def test_html_rules_are_preserved_not_relaxed(self) -> None:
        """Reaching rung 5 must not weaken any existing HTML requirement."""
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "no color-only meaning" in text
        assert "offline self-contained delivery" in text
        assert "responsive layout rules" in text
        assert "full artifact quality pass" in text

    def test_pseudocode_is_not_a_substitute_for_a_spatial_graphic(self) -> None:
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "not** substitutes for an accessible spatial graphic" in text

    def test_the_original_html_decision_table_survives(self) -> None:
        text = _HTML_CONVENTIONS.read_text(encoding="utf-8")
        assert "## HTML vs Markdown decision table" in text
        assert "grid-comparison.html" in text
        assert "annotated-diff.html" in text

    @pytest.mark.parametrize(
        "needle",
        [
            "A short answer must not require creating or opening a file.",
            "Decorative ASCII box diagrams remain excluded at every rung",
        ],
    )
    def test_ladder_claims_have_teeth(self, needle: str) -> None:
        assert_has_teeth(_HTML_CONVENTIONS, needle)


class TestCommunicationHandoff:
    def test_communication_defers_representation_choice(self) -> None:
        text = _AGENT_COMMUNICATION.read_text(encoding="utf-8")
        assert "html-output-conventions" in text
        assert "do not restate it here" in text

    def test_communication_does_not_duplicate_the_ladder(self) -> None:
        """One owner per rule; a copied ladder is a second source of truth."""
        text = _AGENT_COMMUNICATION.read_text(encoding="utf-8")
        assert "The smallest useful representation" not in text
        assert "Decorative ASCII box diagrams" not in text

    def test_closing_report_requirements_are_unchanged(self) -> None:
        text = _AGENT_COMMUNICATION.read_text(encoding="utf-8")
        assert "Completed" in text and "Verified" in text
        assert "Open" in text and "Next" in text

    def test_style_guide_was_left_alone(self) -> None:
        """It governs chat formatting, not representation choice, so it is untouched."""
        text = _COMMS_STYLE_GUIDE.read_text(encoding="utf-8")
        assert "The smallest useful representation" not in text
        assert "html-output-conventions" not in text


# === Phase 5: context fact freshness ===

_FRESHNESS = _FIXTURES / "context-freshness.json"
_PACK_BUILDER = _SKILLS / "workflow" / "context-pack-builder" / "SKILL.md"
_CONTEXT_ENGINEERING = _SKILLS / "ai-development" / "context-engineering" / "SKILL.md"


@pytest.fixture(scope="module")
def freshness() -> dict:
    return json.loads(_FRESHNESS.read_text(encoding="utf-8"))


def derive_freshness(fact: dict, now: str, target: str) -> str:
    """Decide a disposition from the record and a CONTROLLED clock.

    Takes `now` as an argument rather than reading a wall clock, so the matrix
    is reproducible on any host at any date. Order matters: a future timestamp
    is checked before recency, and an unresolved conflict before volatility.
    """
    if fact["observed_at"] > now:
        return "unknown"
    if not fact["source_reachable"]:
        return "unknown"
    if "superseded_by" in fact:
        return "superseded"
    if "conflict_with" in fact:
        return "unknown"
    if not fact["volatile"]:
        return "current"
    if fact["trigger_fired"] or fact["observed_of_target"] != target:
        return "historical"
    return "current"


class TestContextFreshnessMatrix:
    def test_required_scenarios_are_present(self, freshness: dict) -> None:
        ids = {f["fact_id"] for f in freshness["facts"]}
        for required in (
            "CF-1-stale-check",
            "CF-2-stable-convention",
            "CF-3-missing-source",
            "CF-4-future-timestamp",
            "CF-5-contradicted",
            "CF-6-superseded",
        ):
            assert required in ids, f"missing scenario {required}"

    def test_derived_disposition_matches_the_declared_one(
        self, freshness: dict
    ) -> None:
        clock = freshness["evaluation_clock"]
        for fact in freshness["facts"]:
            derived = derive_freshness(fact, clock["now"], clock["target_identity"])
            assert derived == fact["expected_disposition"], (
                f"{fact['fact_id']}: derived {derived}, "
                f"fixture expects {fact['expected_disposition']}"
            )

    def test_all_dispositions_are_declared_values(self, freshness: dict) -> None:
        allowed = set(freshness["dispositions"])
        for fact in freshness["facts"]:
            assert fact["expected_disposition"] in allowed

    def test_high_confidence_stale_fact_is_not_promoted_to_current(
        self, freshness: dict
    ) -> None:
        """Confidence is agreement among past observations, not currency."""
        fact = next(f for f in freshness["facts"] if f["fact_id"] == "CF-1-stale-check")
        assert fact["confidence"] == "high"
        assert fact["expected_disposition"] == "historical"
        assert fact["requires_revalidation"] is True

    def test_stable_fact_needs_no_arbitrary_expiry(self, freshness: dict) -> None:
        fact = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-2-stable-convention"
        )
        assert fact["volatile"] is False
        assert fact["expected_disposition"] == "current"
        assert fact["requires_revalidation"] is False

    def test_stable_fact_is_older_than_the_stale_one(self, freshness: dict) -> None:
        """Proves age alone does not drive the disposition."""
        stable = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-2-stable-convention"
        )
        stale = next(f for f in freshness["facts"] if f["fact_id"] == "CF-1-stale-check")
        assert stable["observed_at"] < stale["observed_at"]
        assert stable["expected_disposition"] == "current"
        assert stale["expected_disposition"] == "historical"

    def test_future_timestamp_is_unknown_not_freshest(self, freshness: dict) -> None:
        clock = freshness["evaluation_clock"]
        fact = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-4-future-timestamp"
        )
        assert fact["observed_at"] > clock["now"]
        assert fact["expected_disposition"] == "unknown"

    def test_conflict_and_supersession_both_retain_provenance(
        self, freshness: dict
    ) -> None:
        for fact_id in ("CF-5-contradicted", "CF-6-superseded"):
            fact = next(f for f in freshness["facts"] if f["fact_id"] == fact_id)
            assert fact["retains_both_provenance"] is True

    def test_conflict_is_unresolved_while_supersession_is_resolved(
        self, freshness: dict
    ) -> None:
        """A newer reading is not automatically the resolution."""
        conflict = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-5-contradicted"
        )
        superseded = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-6-superseded"
        )
        assert conflict["expected_disposition"] == "unknown"
        assert "conflict_with" in conflict and "superseded_by" not in conflict
        assert superseded["expected_disposition"] == "superseded"
        assert "superseded_by" in superseded

    def test_volatile_facts_carry_a_forbidden_present_tense_statement(
        self, freshness: dict
    ) -> None:
        for fact in freshness["facts"]:
            if fact["expected_disposition"] != "current":
                assert "must_not_be_stated_as" in fact, (
                    f"{fact['fact_id']} is not current but names no forbidden phrasing"
                )

    def test_prohibited_behaviors_name_real_guards(self, freshness: dict) -> None:
        ids = {f["fact_id"] for f in freshness["facts"]}
        for behavior in freshness["prohibited_behaviors"]:
            for guard in behavior["guarded_by"].split(", "):
                assert guard in ids, f"{behavior['id']} names unknown fact {guard}"

    def test_clock_is_controlled_not_wall_time(self, freshness: dict) -> None:
        clock = freshness["evaluation_clock"]
        assert clock["now"].endswith("Z")
        assert clock["target_identity"]

    def test_derivation_is_stable_under_a_different_evaluation_instant(
        self, freshness: dict
    ) -> None:
        """A later clock must not silently flip a stable fact to stale."""
        clock = freshness["evaluation_clock"]
        later = "2026-12-31T00:00:00Z"
        stable = next(
            f for f in freshness["facts"] if f["fact_id"] == "CF-2-stable-convention"
        )
        assert (
            derive_freshness(stable, later, clock["target_identity"]) == "current"
        ), "a stable design fact decayed purely because time passed"


class TestFreshnessOwner:
    def test_procedure_is_optional_and_prose_first(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "Fact Freshness and Revalidation" in text
        assert "optional" in text.lower()
        assert "prose-first" in text or "prose annotations" in text

    def test_separates_creation_and_confidence_from_validity(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "A high-confidence historical fact is still historical" in text

    def test_no_universal_ttl_for_stable_facts(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "Stable design facts need no arbitrary expiry" in text

    def test_conflicts_retain_both_records(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "Conflicts retain both provenance records" in text

    def test_no_automatic_deletion_or_fabricated_confirmation(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "No automatic deletion and no fabricated confirmation" in text

    def test_defers_to_existing_owners(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "loop-engineering" in text and "evidence_freshness" in text
        assert "agent-memory" in text

    def test_introduces_no_required_schema_change(self) -> None:
        text = _PACK_BUILDER.read_text(encoding="utf-8")
        assert "nothing here requires a schema version" in text
        assert "existing packs stay readable unchanged" in text

    @pytest.mark.parametrize(
        "needle",
        [
            "A high-confidence historical fact is still historical",
            "Conflicts retain both provenance records",
        ],
    )
    def test_freshness_claims_have_teeth(self, needle: str) -> None:
        assert_has_teeth(_PACK_BUILDER, needle)


class TestContextEngineeringHandoff:
    def test_handoff_points_at_the_pack_owner(self) -> None:
        text = _CONTEXT_ENGINEERING.read_text(encoding="utf-8")
        assert "context-pack-builder" in text

    def test_revalidation_is_decision_scoped_not_every_turn(self) -> None:
        text = _CONTEXT_ENGINEERING.read_text(encoding="utf-8")
        assert "not a mandatory full-memory reread at every turn" in text

    def test_unreachable_source_has_no_endless_retry(self) -> None:
        text = _CONTEXT_ENGINEERING.read_text(encoding="utf-8")
        assert "No endless retries" in text

    def test_existing_readers_are_unchanged(self) -> None:
        text = _CONTEXT_ENGINEERING.read_text(encoding="utf-8")
        assert "not a format change" in text

    def test_handoff_does_not_duplicate_the_procedure(self) -> None:
        """One owner per rule."""
        text = _CONTEXT_ENGINEERING.read_text(encoding="utf-8")
        assert "Four things to record" not in text
        assert "Stable design facts need no arbitrary expiry" not in text


# ---------------------------------------------------------------------------
# Phase 6: the measured trigger pilot
#
# Phase 6 promoted nothing, so the artifact under test is the measurement
# itself. Two things can rot silently here. A results document can claim
# numbers its own raw data does not support, and a "promote nothing"
# disposition can be quietly contradicted by a later edit that lands variant
# B's wording in the catalog anyway. Both are checked against the data rather
# than against prose.
# ---------------------------------------------------------------------------

_PILOT_DIR = _ROOT / "docs" / "releases" / "v4" / "v4.13" / "development"
_PILOT_RESULTS_JSON = _PILOT_DIR / "trigger-pilot-results.json"
_PILOT_RESULTS_MD = _PILOT_DIR / "trigger-pilot-results.md"
_PILOT_VARIANT_B = _PILOT_DIR / "pilot-variant-b.json"

_SAMPLED_SKILLS = {
    "plan-before-code": _ROOT / "catalog" / "skills" / "workflow" / "plan-before-code" / "SKILL.md",
    "html-output-conventions": _ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "html-output-conventions"
    / "SKILL.md",
    "skill-description-authoring": _ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "skill-description-authoring"
    / "SKILL.md",
    "context-engineering": _ROOT
    / "catalog"
    / "skills"
    / "ai-development"
    / "context-engineering"
    / "SKILL.md",
}


def _pilot_results() -> list[dict]:
    return json.loads(_PILOT_RESULTS_JSON.read_text(encoding="utf-8"))["results"]


def _positive_hits(rows: list[dict], tier: str, variant: str) -> int:
    return sum(
        1
        for r in rows
        if r["model_tier"] == tier
        and r["variant"] == variant
        and r["prompt_class"] == "positive"
        and r["selected"] is True
    )


def _irrelevant_hits(rows: list[dict], tier: str, variant: str) -> int:
    return sum(
        1
        for r in rows
        if r["model_tier"] == tier
        and r["variant"] == variant
        and r["prompt_class"] in {"near-miss", "trivial-edit"}
        and r["selected"] is True
    )


class TestTriggerPilotRunIntegrity:
    """A partial run may not be reported as a measured result."""

    def test_the_run_completed_the_frozen_matrix(self) -> None:
        payload = json.loads(_PILOT_RESULTS_JSON.read_text(encoding="utf-8"))
        assert payload["complete"] is True
        assert payload["calls_made"] == payload["calls_planned"] == 96
        assert not payload["stopped_early"]

    def test_no_call_failed(self) -> None:
        assert [r for r in _pilot_results() if r["status"] != "ok"] == []

    def test_no_selection_is_evidence_missing(self) -> None:
        """`None` means unknown; it must never be read as a non-selection."""
        assert [r for r in _pilot_results() if r["selected"] is None] == []

    def test_spend_stayed_under_the_authorized_ceiling(self) -> None:
        payload = json.loads(_PILOT_RESULTS_JSON.read_text(encoding="utf-8"))
        assert payload["total_spend_usd"] <= payload["ceiling_usd"]

    def test_both_arms_ran_the_same_matrix(self) -> None:
        rows = _pilot_results()
        cells = {(r["model_tier"], r["variant"]) for r in rows}
        assert len(cells) == 4
        for tier, variant in cells:
            assert len([r for r in rows if r["model_tier"] == tier and r["variant"] == variant]) == 24

    def test_the_two_arms_differ_only_in_the_sampled_corpus(self) -> None:
        """Variant B must actually be a different corpus from variant A."""
        rows = _pilot_results()
        a_hashes = {tuple(sorted(r["corpus_hashes"].items())) for r in rows if r["variant"] == "A"}
        b_hashes = {tuple(sorted(r["corpus_hashes"].items())) for r in rows if r["variant"] == "B"}
        assert len(a_hashes) == 1, "control corpus drifted mid-run"
        assert len(b_hashes) == 1, "candidate corpus drifted mid-run"
        assert a_hashes != b_hashes, "both arms ran the same corpus; the comparison is void"


class TestTriggerPilotDocumentMatchesItsData:
    """The narrative numbers are recomputed from the raw results."""

    @pytest.mark.parametrize(
        "tier,variant,positives,irrelevant",
        [
            ("fast", "A", 1, 0),
            ("fast", "B", 0, 0),
            ("strong", "A", 3, 0),
            ("strong", "B", 1, 0),
        ],
    )
    def test_reported_counts_are_the_measured_counts(
        self, tier: str, variant: str, positives: int, irrelevant: int
    ) -> None:
        rows = _pilot_results()
        assert _positive_hits(rows, tier, variant) == positives
        assert _irrelevant_hits(rows, tier, variant) == irrelevant

    def test_the_document_states_those_same_counts(self) -> None:
        text = _PILOT_RESULTS_MD.read_text(encoding="utf-8")
        for claim in ("**1 / 8**", "**0 / 8**", "**3 / 8**", "0 / 16"):
            assert claim in text

    def test_criterion_one_failure_is_derivable_not_asserted(self) -> None:
        """B must actually lose positive selections on both models."""
        rows = _pilot_results()
        for tier in ("fast", "strong"):
            assert _positive_hits(rows, tier, "B") < _positive_hits(rows, tier, "A")

    def test_criterion_three_was_unreachable_by_construction(self) -> None:
        """No reduction in irrelevant loading was available: A was already zero."""
        rows = _pilot_results()
        for tier in ("fast", "strong"):
            assert _irrelevant_hits(rows, tier, "A") == 0

    def test_disposition_is_recorded_as_measured_no_change(self) -> None:
        assert "MEASURED_NO_CHANGE" in _PILOT_RESULTS_MD.read_text(encoding="utf-8")

    def test_disposition_claim_has_teeth(self) -> None:
        assert_has_teeth(_PILOT_RESULTS_MD, "MEASURED_NO_CHANGE")


class TestNothingWasPromoted:
    """`MEASURED_NO_CHANGE` means the candidate wording stayed out of the catalog."""

    @staticmethod
    def _was_promoted(document: str, candidate: str) -> bool:
        """The predicate under test, so the control can run the same code."""
        return candidate in document

    @pytest.mark.parametrize("skill", sorted(_SAMPLED_SKILLS))
    def test_candidate_description_did_not_reach_the_catalog(self, skill: str) -> None:
        candidate = json.loads(_PILOT_VARIANT_B.read_text(encoding="utf-8"))["descriptions"][skill]
        shipped = _SAMPLED_SKILLS[skill].read_text(encoding="utf-8")
        assert not self._was_promoted(shipped, candidate)

    @pytest.mark.parametrize("skill", sorted(_SAMPLED_SKILLS))
    def test_the_check_would_notice_a_promotion(self, skill: str) -> None:
        """Run the SAME predicate against a planted copy; it must flip.

        The earlier form asserted `candidate in (shipped + candidate)`, which is
        true regardless of what the real check does. Calling the predicate is
        what makes this a control: if `_was_promoted` were rewritten to return a
        constant, one of the two assertions below fails.
        """
        candidate = json.loads(_PILOT_VARIANT_B.read_text(encoding="utf-8"))["descriptions"][skill]
        shipped = _SAMPLED_SKILLS[skill].read_text(encoding="utf-8")
        assert not self._was_promoted(shipped, candidate)
        assert self._was_promoted(shipped + chr(10) + candidate, candidate)

    def test_every_sampled_skill_still_exists(self) -> None:
        for path in _SAMPLED_SKILLS.values():
            assert path.is_file()


# ---------------------------------------------------------------------------
# Phase 7: defects an adversarial pass confirmed in the pilot runner.
#
# The runner spends real money and produces the evidence the phase rests on, so
# each of these is a regression test for a way it could have reported a number
# that was not measured, or spent more than the ceiling it claims to enforce.
# ---------------------------------------------------------------------------


def _runner():
    """Import the pilot runner for in-process inspection. It is never executed.

    The module must be registered in `sys.modules` before `exec_module`, because
    its dataclasses resolve postponed annotations through the module entry.
    """
    import importlib.util

    if "_run_trigger_pilot" in sys.modules:
        return sys.modules["_run_trigger_pilot"]
    spec = importlib.util.spec_from_file_location(
        "_run_trigger_pilot", _ROOT / "scripts" / "run_trigger_pilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["_run_trigger_pilot"] = module
    spec.loader.exec_module(module)
    return module


def _stream(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events)


_INIT = {"type": "system", "subtype": "init", "model": "m", "skills": ["a", "b"]}


def _skill_call(**tool_input) -> dict:
    return {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Skill", "input": tool_input}]},
    }


class TestRunnerSelectionIsNotASubstringMatch:
    """A mention of the skill is not a selection of it."""

    def test_naming_the_skill_counts(self) -> None:
        m = _runner()
        parsed = m.parse_stream(
            _stream(_INIT, _skill_call(command="context-engineering"),
                    {"type": "result", "num_turns": 2, "total_cost_usd": 0.1}),
            "context-engineering",
        )
        assert parsed["selected"] is True
        assert parsed["skill_selectors"] == [{"command": "context-engineering"}]

    def test_another_skill_mentioning_this_one_does_not_count(self) -> None:
        """The defect: `skill in json.dumps(input)` scored this as a selection."""
        m = _runner()
        parsed = m.parse_stream(
            _stream(
                _INIT,
                _skill_call(command="plan-before-code", prompt="ignore context-engineering here"),
                {"type": "result", "num_turns": 2, "total_cost_usd": 0.1},
            ),
            "context-engineering",
        )
        assert parsed["selected"] is False
        assert parsed["skill_selectors"] == [{"command": "plan-before-code"}]
        assert "ignore context-engineering here" not in json.dumps(parsed)

    def test_a_leading_slash_still_counts(self) -> None:
        m = _runner()
        parsed = m.parse_stream(
            _stream(_INIT, _skill_call(command="/context-engineering"),
                    {"type": "result", "total_cost_usd": 0.1}),
            "context-engineering",
        )
        assert parsed["selected"] is True
        assert parsed["skill_selectors"] == [{"command": "context-engineering"}]

    def test_non_skill_selector_is_redacted(self) -> None:
        m = _runner()
        parsed = m.parse_stream(
            _stream(
                _INIT,
                _skill_call(command="private notes: example@example.com"),
                {"type": "result", "total_cost_usd": 0.1},
            ),
            "context-engineering",
        )
        assert parsed["selected"] is False
        assert parsed["skill_selectors"] == [{"command": "<invalid>"}]
        assert "example@example.com" not in json.dumps(parsed)

    def test_saved_row_retains_only_selector_evidence(self, monkeypatch, tmp_path: Path) -> None:
        m = _runner()
        monkeypatch.setattr(m, "stage_variant", lambda *args: {})
        monkeypatch.setattr(m, "build_command", lambda *args: ["claude"])
        monkeypatch.setattr(
            m.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=["claude"],
                returncode=0,
                stdout=_stream(
                    _INIT,
                    _skill_call(command="plan-before-code", prompt="private prompt text"),
                    {"type": "result", "total_cost_usd": 0.1},
                ),
            ),
        )
        item = {
            "skill": "context-engineering",
            "prompt_id": "p1",
            "prompt_class": "positive",
            "variant": "A",
            "model_tier": "fast",
            "prompt": "private prompt text",
        }
        row = asdict(m.run_call(item, tmp_path, None, tmp_path, {}))
        assert row["skill_selectors"] == [{"command": "plan-before-code"}]
        assert row["selected"] is False
        assert "private prompt text" not in json.dumps(row)

    def test_timeout_row_retains_observed_selector(self, monkeypatch, tmp_path: Path) -> None:
        m = _runner()
        monkeypatch.setattr(m, "stage_variant", lambda *args: {})
        monkeypatch.setattr(m, "build_command", lambda *args: ["claude"])

        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(
                cmd=["claude"],
                timeout=m.PER_CALL_TIMEOUT_S,
                output=_stream(_INIT, _skill_call(command="context-engineering")),
            )

        monkeypatch.setattr(m.subprocess, "run", timeout)
        item = {
            "skill": "context-engineering",
            "prompt_id": "p1",
            "prompt_class": "positive",
            "variant": "A",
            "model_tier": "fast",
            "prompt": "private prompt text",
        }
        row = asdict(m.run_call(item, tmp_path, None, tmp_path, {}))
        assert row["skill_selectors"] == [{"command": "context-engineering"}]
        assert row["selected"] is None
        assert row["status"] == "timeout"


class TestRunnerDistinguishesUnknownFromNegative:
    def test_a_clean_run_with_no_skill_call_is_a_measured_non_selection(self) -> None:
        m = _runner()
        parsed = m.parse_stream(
            _stream(_INIT, {"type": "result", "num_turns": 2, "total_cost_usd": 0.1}),
            "context-engineering",
        )
        assert parsed["selected"] is False

    def test_a_budget_truncated_run_is_evidence_missing(self) -> None:
        """It never got the chance to invoke the skill, so it measured nothing."""
        m = _runner()
        parsed = m.parse_stream(
            _stream(
                _INIT,
                {
                    "type": "result",
                    "subtype": "error_max_budget_exceeded",
                    "is_error": True,
                    "total_cost_usd": 0.5,
                },
            ),
            "context-engineering",
        )
        assert parsed["selected"] is None

    def test_no_result_event_at_all_is_evidence_missing(self) -> None:
        m = _runner()
        assert m.parse_stream(_stream(_INIT), "context-engineering")["selected"] is None


class TestRunnerSpendAccounting:
    def test_an_unreported_cost_is_charged_at_the_worst_case_not_zero(self) -> None:
        """A ledger that under-counts spend permits more of it."""
        m = _runner()
        parsed = m.parse_stream(
            _stream(_INIT, {"type": "result", "num_turns": 1, "total_cost_usd": None}),
            "context-engineering",
        )
        assert parsed["cost_usd"] == m.PER_CALL_BUDGET_USD

    def test_a_non_numeric_cost_does_not_crash_the_run(self) -> None:
        m = _runner()
        parsed = m.parse_stream(
            _stream(_INIT, {"type": "result", "total_cost_usd": "not-a-number"}),
            "context-engineering",
        )
        assert parsed["cost_usd"] == m.PER_CALL_BUDGET_USD

    def test_the_ledger_refuses_a_call_that_would_breach_the_ceiling(self) -> None:
        m = _runner()
        ledger = m.Ledger(m.MAX_SPEND_USD, m.MAX_CALLS, m.TOTAL_WALL_S)
        ledger.spent = m.MAX_SPEND_USD - 0.1
        allowed, why = ledger.may_start()
        assert allowed is False
        assert "spend ceiling" in why


class TestRunnerStagingCannotProduceIdenticalArms:
    def test_a_description_that_does_not_match_is_a_hard_failure(self, tmp_path: Path) -> None:
        """A silent no-op here would compare A with A and measure nothing."""
        m = _runner()
        repo = tmp_path / "repo"
        for name, rel in m.SKILLS.items():
            d = repo / "catalog" / "skills" / rel
            d.mkdir(parents=True)
            # No `description:` line anywhere, so the substitution cannot match.
            (d / "SKILL.md").write_text("---\nname: " + name + "\n---\nbody\n", encoding="utf-8")

        fixture = tmp_path / "fixture"
        fixture.mkdir()
        (fixture / m.FIXTURE_MARKER).write_text("marker", encoding="utf-8")
        variant_b = {"descriptions": {name: "rewritten" for name in m.SKILLS}}

        with pytest.raises(SystemExit, match="expected exactly 1"):
            m.stage_variant("B", fixture, repo, variant_b)

    def test_staging_refuses_a_directory_it_does_not_own(self, tmp_path: Path) -> None:
        """`--fixture .` must not delete a real project's skills."""
        m = _runner()
        fixture = tmp_path / "someones-project"
        (fixture / ".claude" / "skills" / "precious").mkdir(parents=True)
        keep = fixture / ".claude" / "skills" / "precious" / "SKILL.md"
        keep.write_text("do not delete me", encoding="utf-8")

        with pytest.raises(SystemExit, match="not a runner-owned fixture"):
            m.stage_variant("A", fixture, tmp_path, {"descriptions": {}})
        assert keep.read_text(encoding="utf-8") == "do not delete me"


# ---------------------------------------------------------------------------
# Phase 7: the representation ladder gains the oracle it was missing.
#
# Two independent reviews found the same hole: `representation-cases.json`
# declared an `expected_rung` per case that no code derived, so the fixture
# could only be checked for internal self-consistency. A declared expectation
# that nothing contradicts cannot catch a ladder that drifts. This mirrors what
# `derive_disposition` (Phase 3) and `derive_freshness` (Phase 5) already do.
# ---------------------------------------------------------------------------


def derive_rung(signals: dict) -> str:
    """Pick the lowest rung that carries the answer, from the ladder's own rules.

    Transcribed from the ladder table in `html-output-conventions/SKILL.md`:

    1. prose      -- one or two facts with no structure to show
    2. table      -- a handful of items compared across two or three attributes
    3. pseudocode -- the answer is a sequence, an algorithm, or a control flow
    4. mermaid    -- a small graph; past roughly a dozen nodes rung 5 applies
    5. html       -- state, interactivity, spatial complexity, a many-way
                     comparison, or length past roughly 100 lines

    This function never reads `expected_rung`. If it did, it would agree by
    construction and prove nothing.
    """
    if (
        signals["needs_interaction"]
        or signals["needs_persistent_state"]
        or signals["estimated_lines"] > 100
        or signals["graph_nodes"] > 12
        or signals["attributes"] > 3
    ):
        return "html"
    if signals["graph_nodes"] > 0:
        return "mermaid"
    if signals["has_control_flow"]:
        return "pseudocode"
    # The discriminator between rungs 1 and 2 is whether there is structure to
    # show, not how many rows there are: rung 1 is "one or two facts with NO
    # STRUCTURE", and a two-item comparison across two attributes has structure.
    # An earlier transcription used a row-count threshold and put REP-5, a 2x2
    # comparison, on prose. The fixture caught it.
    if signals["attributes"] >= 2:
        return "table"
    return "prose"


class TestRepresentationLadderOracle:
    """The derived rung must reproduce the declared one for every case."""

    def test_every_case_carries_signals(self, representation: dict) -> None:
        missing = [c["case_id"] for c in representation["cases"] if "signals" not in c]
        assert not missing, f"cases without machine-readable signals: {missing}"

    def test_derived_rung_matches_the_declared_one(self, representation: dict) -> None:
        mismatches = [
            (c["case_id"], c["expected_rung"], derive_rung(c["signals"]))
            for c in representation["cases"]
            if derive_rung(c["signals"]) != c["expected_rung"]
        ]
        assert not mismatches, f"declared rung disagrees with the ladder: {mismatches}"

    def test_the_derived_rung_is_never_a_forbidden_one(self, representation: dict) -> None:
        for case in representation["cases"]:
            assert derive_rung(case["signals"]) not in case.get("must_not_be", [])

    def test_the_near_miss_pair_is_separated_by_the_oracle(
        self, representation: dict
    ) -> None:
        """The pair exists to catch a ladder that climbs on size alone.

        REP-5 and REP-6 are both comparisons. Only REP-6 needs interaction and
        state, and only REP-6 may reach HTML. A rule keyed on item count would
        put them on the same rung.
        """
        by_id = {c["case_id"]: c for c in representation["cases"]}
        assert derive_rung(by_id["REP-5-near-miss"]["signals"]) == "table"
        assert derive_rung(by_id["REP-6-near-miss"]["signals"]) == "html"

    def test_the_oracle_would_notice_an_unjustified_climb(
        self, representation: dict
    ) -> None:
        """Mutation control: a static case must not reach HTML on size alone."""
        by_id = {c["case_id"]: c for c in representation["cases"]}
        inflated = dict(by_id["REP-1"]["signals"], facts=40)
        assert derive_rung(inflated) == "table", (
            "more rows alone must not justify an artifact; only interaction, "
            "state, width, or length does"
        )

    def test_the_oracle_climbs_when_interaction_is_genuinely_required(
        self, representation: dict
    ) -> None:
        """The opposite control: it must not be stuck below HTML either."""
        by_id = {c["case_id"]: c for c in representation["cases"]}
        interactive = dict(by_id["REP-1"]["signals"], needs_interaction=True)
        assert derive_rung(interactive) == "html"
