"""Contract tests for the v3.16.1 evaluation methodology (Phase 1).

Phase 1 ships no runtime code. It ships two documents: the shared evaluation
artifact contract (`docs/releases/v3/v3.16/development/evaluation-artifact-contract.md`)
and the retrieval-evaluation reference owned by `rag-implementation`. Everything
Phases 2 through 4 build reads that vocabulary, so what needs guarding is not
prose style but the specific claims later phases depend on.

Three failure modes motivate this module, all of them silent:

1. **A formula gets dropped in an edit.** A reference that names Recall@k but no
   longer defines it still reads fine and is useless to anyone computing it.
2. **The retrieval/generation separation erodes.** The whole point of Phase 1.2
   is that a weak answer must not be reflexively blamed on retrieval. That
   separation lives in prose and is exactly the kind of nuance a later
   consolidating edit flattens.
3. **The local-first rule quietly disappears.** These artifacts hold production
   traces and human labels. A reference that stops saying so still passes every
   Markdown gate in the repo.

Assertions are semantic and targeted rather than whole-file snapshots, so
rewording a paragraph does not fail the suite but deleting a contract does.

Each predicate below is exercised twice: once against the real file, and once
against a mutated copy with the target content removed (the `test_*_has_teeth`
tests). Without the mutation tests, a predicate that accidentally matched
anything would pass forever and guard nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_SKILLS = _ROOT / "catalog" / "skills"
_RAG_SKILL_DIR = _SKILLS / "ai-development" / "rag-implementation"
_RAG_SKILL = _RAG_SKILL_DIR / "SKILL.md"
_RAG_EVAL_REF = _RAG_SKILL_DIR / "references" / "evaluation.md"
_CONTRACT = (
    _ROOT / "docs" / "releases" / "v3" / "v3.16" / "development"
    / "evaluation-artifact-contract.md"
)

# Phase 3: the two references owned by ai-output-evaluation.
_AOE_SKILL_DIR = _SKILLS / "developer-experience" / "ai-output-evaluation"
_AOE_SKILL = _AOE_SKILL_DIR / "SKILL.md"
_ERROR_ANALYSIS = _AOE_SKILL_DIR / "references" / "error-analysis.md"
_EVALUATOR_VALIDATION = _AOE_SKILL_DIR / "references" / "evaluator-validation.md"

# Phase 4: the remaining two references owned by ai-output-evaluation.
_SYNTHETIC_DATA = _AOE_SKILL_DIR / "references" / "synthetic-data.md"
_REVIEW_INTERFACE = _AOE_SKILL_DIR / "references" / "review-interface.md"

# Metric name -> (section heading pattern, defining-formula pattern).
# A metric counts as "defined" only when BOTH are present: a heading alone is a
# mention, and Phase 1.2's deliverable is reproducible arithmetic.
METRIC_SPECS: dict[str, tuple[str, str]] = {
    "Recall@k": (r"###\s+Recall@k", r"Recall@k\s*=\s*\|R intersect"),
    "Precision@k": (r"###\s+Precision@k", r"Precision@k\s*=\s*\|R intersect"),
    "MRR": (r"###\s+MRR", r"MRR\s*=\s*mean of RR"),
    "NDCG@k": (r"###\s+NDCG@k", r"NDCG@k\s*=\s*DCG@k\s*/\s*IDCG@k"),
    "multi-hop recall": (r"###\s+Multi-hop recall", r"hop_recall\(query\)\s*="),
}

# Every artifact the Phase 1 contract must define. The last two are cross-cutting
# metadata blocks embedded in the others rather than standalone files, but they
# are named artifacts in the contract and later phases reference them by name.
REQUIRED_ARTIFACTS = (
    "dataset_manifest",
    "split_manifest",
    "trace_sample",
    "error_taxonomy",
    "evaluator_result",
    "retrieval_result",
    "human_annotation",
    "adjudication_record",
    "regression_case",
    "provenance",
    "redaction_status",
)

# Phrases that carry the local-first rule. A document satisfies the rule when it
# states the default AND names the gate that governs an exception.
LOCAL_FIRST_MARKERS = ("export_authorized", "egress-redaction")


# --------------------------------------------------------------------------- #
# Predicates (shared by the real assertions and the mutation tests)
# --------------------------------------------------------------------------- #

def defines_metric(text: str, metric: str) -> bool:
    """True when `metric` has both a section heading and its defining formula."""
    heading, formula = METRIC_SPECS[metric]
    return bool(re.search(heading, text)) and bool(re.search(formula, text))


def defines_artifact(text: str, artifact: str) -> bool:
    """True when `artifact` has its own section heading in the contract."""
    return bool(re.search(rf"###\s+{re.escape(artifact)}\b", text))


def maps_artifact_ownership(text: str, artifact: str) -> bool:
    """True when `artifact` has a row in the ownership map table."""
    ownership = text.split("## Ownership map", 1)
    if len(ownership) != 2:
        return False
    row = rf"^\|\s*`{re.escape(artifact)}`\s*\|"
    return bool(re.search(row, ownership[1], re.MULTILINE))


def separates_retrieval_from_generation(text: str) -> bool:
    """True when the reference tells the reader to read retrieval metrics first.

    Requires the ordering rule to be stated, not merely that both words appear:
    a document can mention retrieval and generation in one breath and still leave
    a reader blaming the generator for a recall failure.
    """
    lowered = text.lower()
    states_both = "retrieval" in lowered and "generation" in lowered
    states_order = bool(
        re.search(r"retrieval\s+(?:metrics\s+)?(?:before|first)", lowered)
        or re.search(r"measure retrieval (?:first|before)", lowered)
    )
    names_generation_metric = "faithfulness" in lowered
    return states_both and states_order and names_generation_metric


def declares_local_first(text: str) -> bool:
    """True when the document declares the local-first default and its gate."""
    return all(marker in text for marker in LOCAL_FIRST_MARKERS)


def is_ascii(text: str) -> bool:
    return text.isascii()


def _without(text: str, pattern: str) -> str:
    """Delete every line matching `pattern`. Used to build negative fixtures."""
    kept = [line for line in text.splitlines() if not re.search(pattern, line)]
    return "\n".join(kept)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def rag_reference() -> str:
    assert _RAG_EVAL_REF.is_file(), (
        f"Missing the retrieval-evaluation reference at {_RAG_EVAL_REF}. "
        "Phase 1.2 requires it and Phases 2-4 read its vocabulary."
    )
    return _RAG_EVAL_REF.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rag_skill() -> str:
    return _RAG_SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def contract() -> str:
    assert _CONTRACT.is_file(), (
        f"Missing the evaluation artifact contract at {_CONTRACT}. "
        "Phase 1.1 requires it as the shared vocabulary for Phases 2-4."
    )
    return _CONTRACT.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# The RAG retrieval-evaluation reference
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("metric", sorted(METRIC_SPECS))
def test_reference_defines_each_required_metric(rag_reference: str, metric: str) -> None:
    assert defines_metric(rag_reference, metric), (
        f"{_RAG_EVAL_REF.name} must define {metric} with BOTH a section heading "
        f"and its formula. Expected heading {METRIC_SPECS[metric][0]!r} and "
        f"formula {METRIC_SPECS[metric][1]!r}. A metric named but not defined "
        "cannot be computed by a reader."
    )


def test_reference_is_linked_from_the_parent_skill(rag_skill: str) -> None:
    assert "references/evaluation.md" in rag_skill, (
        f"{_RAG_SKILL.name} must link the reference by basename path "
        "('references/evaluation.md'). An unreferenced bundled file is an orphan "
        "and the catalog bundle audit will flag it."
    )


def test_reference_separates_retrieval_from_generation(rag_reference: str) -> None:
    assert separates_retrieval_from_generation(rag_reference), (
        f"{_RAG_EVAL_REF.name} must state that retrieval is measured BEFORE "
        "generation and name a generation metric (faithfulness) as the thing "
        "that must not be read first. Losing this ordering rule reintroduces the "
        "most common RAG debugging error: blaming the generator for low recall."
    )


def test_parent_skill_also_states_the_retrieval_first_order(rag_skill: str) -> None:
    assert separates_retrieval_from_generation(rag_skill), (
        f"{_RAG_SKILL.name} Step 7 must carry the retrieval-before-generation "
        "ordering in the Tier-2 body. A reader who never opens the Tier-3 "
        "reference still needs the diagnostic order."
    )


def test_reference_has_a_worked_example_with_computed_values(rag_reference: str) -> None:
    assert re.search(r"##\s+Worked example", rag_reference), (
        f"{_RAG_EVAL_REF.name} must contain a '## Worked example' section."
    )
    # The example is only useful if it carries arithmetic a reader can check.
    for expected in ("0.667", "0.400", "0.498"):
        assert expected in rag_reference, (
            f"{_RAG_EVAL_REF.name} worked example lost the computed value "
            f"{expected}. Bounded worked examples must show the arithmetic, not "
            "just describe it."
        )


def test_reference_has_a_multi_hop_case(rag_reference: str) -> None:
    assert re.search(r"###\s+Multi-hop worked example", rag_reference), (
        f"{_RAG_EVAL_REF.name} must contain a multi-hop worked example."
    )
    assert "all_hops_rate" in rag_reference, (
        "The multi-hop section must define all_hops_rate. Mean hop_recall alone "
        "overstates answerability: 3-of-4 hops scores 0.75 and answers nothing."
    )


def test_reference_requires_confidence_intervals(rag_reference: str) -> None:
    assert "Wilson" in rag_reference, (
        f"{_RAG_EVAL_REF.name} must give a concrete interval procedure (Wilson "
        "for rates). Phase 1.2 requires confidence intervals where appropriate."
    )
    assert re.search(r"bootstrap", rag_reference, re.IGNORECASE), (
        "Mean-style metrics (mean Recall@k, mean NDCG@k) are not Bernoulli "
        "trials, so the reference must name a separate procedure for them."
    )


def test_reference_describes_one_variable_at_a_time_grid_search(rag_reference: str) -> None:
    assert re.search(r"##\s+Grid search", rag_reference), (
        f"{_RAG_EVAL_REF.name} must document the chunking/retrieval grid search."
    )
    assert re.search(r"one variable at a time|exactly one variable", rag_reference), (
        "The grid-search procedure must require changing exactly one variable "
        "per cell. Changing chunk size and k together produces an unattributable "
        "result, which is the most common wasted grid search."
    )


def test_reference_declares_local_first_artifacts(rag_reference: str) -> None:
    assert declares_local_first(rag_reference), (
        f"{_RAG_EVAL_REF.name} must declare that evaluation artifacts stay local "
        f"by default. Expected all of {LOCAL_FIRST_MARKERS} to appear."
    )


def test_reference_uses_the_shared_artifact_vocabulary(rag_reference: str) -> None:
    assert "retrieval_result" in rag_reference, (
        f"{_RAG_EVAL_REF.name} must persist results as `retrieval_result` "
        "records so Phase 2's audit can inventory them by name."
    )


def test_reference_adds_no_dependency_or_credential(rag_reference: str) -> None:
    forbidden = ("pip install", "npm install", "API key", "api_key", "curl -")
    found = [token for token in forbidden if token in rag_reference]
    assert not found, (
        f"{_RAG_EVAL_REF.name} must add no package dependency, credential, or "
        f"remote fetch. Found: {found}. Every metric here is arithmetic over "
        "records the project already has."
    )


# --------------------------------------------------------------------------- #
# The shared evaluation artifact contract
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("artifact", REQUIRED_ARTIFACTS)
def test_contract_defines_each_required_artifact(contract: str, artifact: str) -> None:
    assert defines_artifact(contract, artifact), (
        f"{_CONTRACT.name} must define `{artifact}` under its own '### {artifact}' "
        "section with its required fields. Later phases reference these by name."
    )


@pytest.mark.parametrize("artifact", REQUIRED_ARTIFACTS)
def test_contract_maps_each_artifact_to_an_owner(contract: str, artifact: str) -> None:
    assert maps_artifact_ownership(contract, artifact), (
        f"{_CONTRACT.name} ownership map has no row for `{artifact}`. An artifact "
        "with no single owning skill is the drift this contract exists to stop."
    )


def test_contract_owners_are_real_or_planned_skills(contract: str) -> None:
    """Every `[[skill]]` named as an owner must exist, or be planned by this plan."""
    ownership = contract.split("## Ownership map", 1)
    assert len(ownership) == 2, f"{_CONTRACT.name} must have an '## Ownership map'."

    planned = {"eval-pipeline-audit"}  # created in Phase 2
    owners = set(re.findall(r"\[\[([a-z0-9-]+)\]\]", ownership[1]))
    assert owners, "The ownership map must name at least one owning skill."

    missing = [
        name for name in sorted(owners)
        if name not in planned and not list(_SKILLS.glob(f"*/{name}/SKILL.md"))
    ]
    assert not missing, (
        f"{_CONTRACT.name} assigns ownership to skills that do not exist and are "
        f"not planned by v3.16.1: {missing}."
    )


def test_contract_declares_the_local_first_rule(contract: str) -> None:
    assert declares_local_first(contract), (
        f"{_CONTRACT.name} must state the local-by-default rule and name "
        f"`egress-redaction` as the gate. Expected all of {LOCAL_FIRST_MARKERS}."
    )
    assert re.search(r"minimiz", contract, re.IGNORECASE), (
        "The contract must require minimization before any authorized export, "
        "not merely forbid casual export."
    )


def test_contract_requires_provenance_on_every_artifact(contract: str) -> None:
    assert re.search(r"###\s+provenance", contract), (
        "provenance must be defined as a required cross-cutting block."
    )
    for field in ("source", "created_at", "created_by"):
        assert field in contract, (
            f"provenance is missing the required field `{field}`. An artifact "
            "with no recorded origin cannot be reproduced or audited."
        )


def test_contract_guards_holdout_leakage(contract: str) -> None:
    assert "holdout_touched_count" in contract, (
        "`split_manifest` must record how many times the held-out partition has "
        "been evaluated against. Repeated tuning on the test split is the "
        "leakage failure Phase 3's evaluator calibration depends on catching."
    )


# --------------------------------------------------------------------------- #
# Repository conventions for the new documents
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "path",
    [_RAG_EVAL_REF, _CONTRACT],
    ids=lambda p: p.name,
)
def test_new_documents_are_ascii_only(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert is_ascii(text), (
        f"{path} contains non-ASCII characters. English Markdown in this repo is "
        "ASCII-only (hyphens, straight quotes, '...') to avoid encoding "
        "corruption on Windows."
    )


@pytest.mark.parametrize(
    "path",
    [_RAG_EVAL_REF, _CONTRACT],
    ids=lambda p: p.name,
)
def test_new_documents_have_a_verification_section(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert re.search(r"##\s+Verification", text), (
        f"{path.name} must end with a binary Verification checklist. 'The "
        "document looks complete' is not a verification criterion."
    )


# --------------------------------------------------------------------------- #
# Negative fixtures: prove each predicate actually fails when content is removed
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("metric", sorted(METRIC_SPECS))
def test_metric_assertion_has_teeth(rag_reference: str, metric: str) -> None:
    """Deleting a formula line must make `defines_metric` fail for that metric."""
    _, formula = METRIC_SPECS[metric]
    mutated = _without(rag_reference, formula)
    assert not defines_metric(mutated, metric), (
        f"The {metric} check passes even with its formula deleted, so it guards "
        "nothing. Tighten METRIC_SPECS."
    )


@pytest.mark.parametrize("artifact", REQUIRED_ARTIFACTS)
def test_artifact_assertion_has_teeth(contract: str, artifact: str) -> None:
    """Deleting an artifact's heading must make both artifact checks fail."""
    mutated = _without(contract, rf"###\s+{re.escape(artifact)}\b")
    assert not defines_artifact(mutated, artifact), (
        f"The `{artifact}` definition check passes with its heading deleted."
    )


@pytest.mark.parametrize("artifact", REQUIRED_ARTIFACTS)
def test_ownership_assertion_has_teeth(contract: str, artifact: str) -> None:
    """Deleting an ownership row must make the ownership check fail."""
    mutated = _without(contract, rf"^\|\s*`{re.escape(artifact)}`\s*\|")
    assert not maps_artifact_ownership(mutated, artifact), (
        f"The `{artifact}` ownership check passes with its table row deleted."
    )


def test_local_first_assertion_has_teeth(contract: str) -> None:
    """Deleting the egress gate must make the local-first check fail."""
    mutated = contract.replace("egress-redaction", "REMOVED")
    assert not declares_local_first(mutated), (
        "The local-first check passes with the egress gate removed, so a "
        "document could drop its only export control and still pass."
    )


def test_retrieval_first_assertion_has_teeth(rag_reference: str) -> None:
    """Removing the ordering rule must fail the separation check.

    Both words survive the mutation; only the ordering statement is removed. If
    the check still passes, it is matching mere co-occurrence and would not
    notice the separation collapsing.
    """
    mutated = re.sub(
        r"retrieval\s+(?:metrics\s+)?(?:before|first)",
        "retrieval and generation together",
        rag_reference,
        flags=re.IGNORECASE,
    )
    mutated = re.sub(
        r"measure retrieval (?:first|before)",
        "measure retrieval and generation together",
        mutated,
        flags=re.IGNORECASE,
    )
    assert not separates_retrieval_from_generation(mutated), (
        "The retrieval-before-generation check passes with the ordering rule "
        "removed, so it is only detecting that both words appear."
    )


# --------------------------------------------------------------------------- #
# Phase 3: error analysis and evaluator calibration
#
# These two references carry the methods that decide whether a judge may block a
# release. The assertions below target the specific claims that make that
# decision safe, because each is a rule a well-meaning condensing edit would drop
# as detail: the held-out split, the tuning isolation, the blind review, and the
# prevalence caveat all read like caveats and are load-bearing.
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def error_analysis() -> str:
    assert _ERROR_ANALYSIS.is_file(), (
        f"Missing the error-analysis reference at {_ERROR_ANALYSIS}. Phase 3.1 "
        "requires it and eval-pipeline-audit already routes gaps to it."
    )
    return _ERROR_ANALYSIS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def evaluator_validation() -> str:
    assert _EVALUATOR_VALIDATION.is_file(), (
        f"Missing the evaluator-validation reference at {_EVALUATOR_VALIDATION}. "
        "Phase 3.2 requires it and eval-pipeline-audit already routes gaps to it."
    )
    return _EVALUATOR_VALIDATION.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def aoe_skill() -> str:
    return _AOE_SKILL.read_text(encoding="utf-8")


@pytest.mark.parametrize("basename", ["error-analysis.md", "evaluator-validation.md"])
def test_phase3_references_are_linked_from_the_parent_skill(aoe_skill: str, basename: str) -> None:
    assert f"references/{basename}" in aoe_skill, (
        f"ai-output-evaluation/SKILL.md must link `references/{basename}` by "
        "basename. An unreferenced bundled file is an orphan and the catalog "
        "bundle audit flags it."
    )


def test_parent_skill_separates_scoring_from_validating_the_evaluator(aoe_skill: str) -> None:
    assert "Evaluating Output vs Validating the Evaluator" in aoe_skill, (
        "The parent skill must name the distinction between scoring output and "
        "validating the scorer. Without it a reader treats an unvalidated judge "
        "as interchangeable with a measured one."
    )


def test_parent_skill_requires_held_out_evidence_for_a_gating_evaluator(aoe_skill: str) -> None:
    section = aoe_skill.split("## Verification", 1)[1].split("\n## ", 1)[0]
    assert "held-out" in section, (
        "Verification must require held-out evidence before an evaluator gates a "
        "release. That is the difference between a measured gate and an "
        "unmeasured blocker nobody can appeal."
    )
    assert "disagreement review" in section, (
        "Verification must require a documented disagreement review for a "
        "release-gating evaluator."
    )


@pytest.mark.parametrize(
    "concept,pattern",
    [
        ("trace sampling method", r"sampling_method"),
        ("failure-biased sampling caveat", r"failure[_ ]biased"),
        ("inclusion criteria", r"[Ii]nclusion"),
        ("exclusion criteria", r"[Ee]xclusion"),
        ("multi-label handling", r"[Mm]ulti-label"),
        ("severity ranking", r"[Ss]everity"),
        ("root-cause hypothesis", r"[Hh]ypothesis"),
        ("refuting evidence", r"[Rr]efut"),
    ],
)
def test_error_analysis_covers_its_required_method(
    error_analysis: str, concept: str, pattern: str
) -> None:
    assert re.search(pattern, error_analysis), (
        f"error-analysis.md is missing the {concept}. Each exists because it is "
        "a way a trace review produces numbers that do not mean what they say."
    )


def test_error_analysis_forbids_reporting_biased_samples_as_base_rates(error_analysis: str) -> None:
    assert re.search(r"base rate", error_analysis, re.I), (
        "error-analysis.md must warn that a failure-biased sample cannot report "
        "base rates. Presenting category shares from a failure-biased sample as "
        "system failure rates is the most common error in trace review."
    )


def test_error_analysis_requires_exclusion_criteria_per_category(error_analysis: str) -> None:
    assert re.search(r"exclusion_criteria|Exclusion:", error_analysis), (
        "Every taxonomy category must declare exclusion criteria. Without them "
        "two reviewers file the same trace differently and the frequency counts "
        "stop meaning anything."
    )


def test_error_analysis_converts_patterns_into_regression_cases(error_analysis: str) -> None:
    assert "regression_case" in error_analysis, (
        "error-analysis.md must promote confirmed patterns into `regression_case` "
        "artifacts. A pattern with no regression case is a pattern that will be "
        "rediscovered."
    )
    for field in ("origin_trace_id", "assertion", "expected_behavior"):
        assert field in error_analysis, (
            f"The regression_case definition is missing `{field}`, so a promoted "
            "case would not be runnable or traceable to its origin."
        )
    assert re.search(r"minimiz", error_analysis, re.I), (
        "Regression cases must be minimized before promotion: an unminimized "
        "case drags raw production data into a committed test suite."
    )


@pytest.mark.parametrize(
    "concept,pattern",
    [
        ("held-out split", r"held-out"),
        ("three-way separation", r"development"),
        ("holdout touch counting", r"holdout_touched_count"),
        ("confusion matrix", r"[Cc]onfusion [Mm]atrix"),
        ("true positive", r"True Positive"),
        ("true negative", r"True Negative"),
        ("precision", r"Precision\s+="),
        ("recall / TPR", r"Recall \(TPR\)"),
        ("specificity / TNR", r"Specificity \(TNR\)"),
        ("confidence interval", r"Wilson"),
        ("recalibration trigger", r"[Rr]ecalibrat"),
        ("blind annotation", r"[Bb]lind"),
        ("adjudication", r"[Aa]djudicat"),
    ],
)
def test_evaluator_validation_covers_its_required_method(
    evaluator_validation: str, concept: str, pattern: str
) -> None:
    assert re.search(pattern, evaluator_validation), (
        f"evaluator-validation.md is missing the {concept}. A judge promoted to "
        "a release gate without it has an unknown failure mode."
    )


def test_evaluator_validation_isolates_threshold_tuning_from_the_test_split(
    evaluator_validation: str,
) -> None:
    assert "development" in evaluator_validation, (
        "Thresholds must be tuned on a development split."
    )
    assert re.search(r"Never used for|ever\b", evaluator_validation), (
        "The reference must state that the held-out split is never used for a "
        "tuning decision. Re-tuning against the test split and reporting the "
        "improved number turns a test set into a training set."
    )


def test_evaluator_validation_has_a_worked_confusion_matrix(evaluator_validation: str) -> None:
    for value in ("0.600", "0.750", "0.786"):
        assert value in evaluator_validation, (
            f"The worked confusion-matrix example lost the computed value {value}. "
            "The example must show the arithmetic, not describe it."
        )


def test_evaluator_validation_explains_the_prevalence_effect(evaluator_validation: str) -> None:
    assert re.search(r"[Pp]revalence", evaluator_validation), (
        "The reference must cover prevalence: precision is not a property of the "
        "judge, and a judge validated at one failure rate behaves very "
        "differently at another."
    )
    assert "0.156" in evaluator_validation, (
        "The prevalence worked example lost its computed precision. Showing "
        "precision falling from 0.60 to 0.16 with the judge unchanged is what "
        "makes the caveat concrete rather than a warning to skim."
    )


def test_evaluator_validation_distinguishes_advisory_from_gate(evaluator_validation: str) -> None:
    assert re.search(r"[Aa]dvisory", evaluator_validation), "Must define the advisory posture."
    assert re.search(r"[Rr]elease gate", evaluator_validation), (
        "The reference must state when a judge is qualified to gate a release. "
        "Promotion between those postures without evidence is the failure this "
        "whole reference guards."
    )


@pytest.mark.parametrize(
    "path", [_ERROR_ANALYSIS, _EVALUATOR_VALIDATION], ids=lambda p: p.name
)
def test_phase3_references_declare_local_first(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert declares_local_first(text), (
        f"{path.name} must declare the local-by-default rule and name "
        f"egress-redaction as the gate. Expected all of {LOCAL_FIRST_MARKERS}. "
        "These references handle production traces and human labels about real "
        "interactions."
    )


@pytest.mark.parametrize(
    "path", [_ERROR_ANALYSIS, _EVALUATOR_VALIDATION], ids=lambda p: p.name
)
def test_phase3_references_use_the_shared_artifact_vocabulary(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    expected = {
        "error-analysis.md": ("trace_sample", "error_taxonomy", "regression_case"),
        "evaluator-validation.md": ("split_manifest", "human_annotation", "adjudication_record"),
    }[path.name]
    missing = [a for a in expected if a not in text]
    assert not missing, (
        f"{path.name} does not speak the Phase 1 artifact contract: missing "
        f"{missing}. Shared names are what let eval-pipeline-audit inventory "
        "these by name."
    )


@pytest.mark.parametrize(
    "path", [_ERROR_ANALYSIS, _EVALUATOR_VALIDATION], ids=lambda p: p.name
)
def test_phase3_references_are_ascii_with_binary_verification(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert is_ascii(text), f"{path.name} must be ASCII-only."
    assert re.search(r"##\s+Verification", text), (
        f"{path.name} must end with a binary Verification checklist."
    )
    items = re.findall(r"^- \[ \] (.+)$", text.split("## Verification", 1)[1], re.M)
    assert len(items) >= 8, (
        f"{path.name} has only {len(items)} verification items; these references "
        "carry enough rules that a short checklist means rules went unchecked."
    )


@pytest.mark.parametrize(
    "path,pattern,label",
    [
        (_ERROR_ANALYSIS, r"regression_case", "regression_case promotion"),
        (_EVALUATOR_VALIDATION, r"holdout_touched_count", "holdout touch counting"),
    ],
    ids=["error-analysis", "evaluator-validation"],
)
def test_phase3_assertions_have_teeth(path: Path, pattern: str, label: str) -> None:
    """Deleting the target lines must make the corresponding check fail."""
    mutated = _without(path.read_text(encoding="utf-8"), pattern)
    assert not re.search(pattern, mutated), (
        f"The {label} check still matches after its lines are deleted, so it "
        "guards nothing."
    )


# --------------------------------------------------------------------------- #
# Phase 4: synthetic data and human review
#
# Both references describe how to MANUFACTURE the inputs that every downstream
# number depends on, which makes their controls easy to skip and expensive to
# skip. The assertions target the controls specifically: coverage verified after
# generation rather than assumed, leakage and duplicate filters, held-out
# separation, and - for review - blindness, abstention, and the no-implicit-
# upload rule.
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def synthetic_data() -> str:
    assert _SYNTHETIC_DATA.is_file(), (
        f"Missing the synthetic-data reference at {_SYNTHETIC_DATA}. Phase 4.1 "
        "requires it and eval-pipeline-audit already routes gaps to it."
    )
    return _SYNTHETIC_DATA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def review_interface() -> str:
    assert _REVIEW_INTERFACE.is_file(), (
        f"Missing the review-interface reference at {_REVIEW_INTERFACE}. Phase "
        "4.2 requires it and eval-pipeline-audit already routes gaps to it."
    )
    return _REVIEW_INTERFACE.read_text(encoding="utf-8")


@pytest.mark.parametrize("basename", ["synthetic-data.md", "review-interface.md"])
def test_phase4_references_are_linked_from_the_parent_skill(aoe_skill: str, basename: str) -> None:
    assert f"references/{basename}" in aoe_skill, (
        f"ai-output-evaluation/SKILL.md must link `references/{basename}` by "
        "basename, or the catalog bundle audit flags it as an orphan."
    )


@pytest.mark.parametrize(
    "concept,pattern",
    [
        ("dimensions", r"[Dd]imension"),
        ("allowed values", r"[Aa]llowed values"),
        ("constraints", r"CONSTRAINT|[Cc]onstraint"),
        ("tuple coverage", r"pairwise|2-tuple|tuple"),
        ("batched generation", r"[Bb]atch"),
        ("duplicate detection", r"[Dd]uplicate"),
        ("source leakage", r"leakage|verbatim"),
        ("difficulty validation", r"[Dd]ifficulty"),
        ("human spot check", r"spot[- ]check"),
        ("generator config provenance", r"generator_config"),
    ],
)
def test_synthetic_data_covers_its_required_method(
    synthetic_data: str, concept: str, pattern: str
) -> None:
    assert re.search(pattern, synthetic_data), (
        f"synthetic-data.md is missing the {concept}. Each control exists "
        "because generated cases carry generated labels, and an unfiltered "
        "batch silently reweights every aggregate computed from it."
    )


def test_synthetic_data_has_a_worked_dimension_matrix(synthetic_data: str) -> None:
    assert re.search(r"query_type", synthetic_data), (
        "The worked dimension matrix must show concrete dimensions and values, "
        "not describe the idea of a matrix."
    )
    assert "108" in synthetic_data, (
        "The matrix must show the resulting combination count, which is what "
        "makes the case for a pairwise target rather than full cartesian."
    )


def test_synthetic_data_verifies_coverage_after_generation(synthetic_data: str) -> None:
    assert re.search(r"[Uu]ncovered", synthetic_data), (
        "The reference must require recomputing achieved coverage and reporting "
        "uncovered cells. Declaring a target and generating against it does not "
        "mean the target was hit, and without this step nobody finds out."
    )


def test_synthetic_data_keeps_generated_cases_out_of_the_holdout(synthetic_data: str) -> None:
    assert re.search(r"held-out", synthetic_data), (
        "The reference must address the held-out split explicitly."
    )
    assert re.search(r"proportion|marked", synthetic_data), (
        "If synthetic cases must appear in a test split, the reference must "
        "require marking them and reporting their proportion. A test split of "
        "generated cases measures what a generator imagines users do."
    )


def test_synthetic_data_promotion_has_acceptance_criteria(synthetic_data: str) -> None:
    assert re.search(r"promot", synthetic_data, re.I), (
        "The reference must define what a case must satisfy before it is "
        "promoted into the evaluation set."
    )


@pytest.mark.parametrize(
    "concept,pattern",
    [
        ("annotation schema", r"annotator_id"),
        ("blind review", r"[Bb]lind"),
        ("randomized ordering", r"[Rr]andomiz"),
        ("keyboard-first controls", r"[Kk]eypress|[Kk]eyboard"),
        ("accessible labels", r"programmatic label"),
        ("focus behavior", r"[Ff]ocus"),
        ("reviewer confidence", r"confidence"),
        ("abstention", r"abstain"),
        ("adjudication", r"adjudicat"),
        ("audit history", r"append-only"),
        ("local autosave", r"[Aa]utosave|after every submission"),
        ("resume behavior", r"[Rr]esum"),
        ("deterministic export", r"[Ss]table (?:key|row) order|[Dd]eterministic export"),
    ],
)
def test_review_interface_covers_its_required_contract(
    review_interface: str, concept: str, pattern: str
) -> None:
    assert re.search(pattern, review_interface), (
        f"review-interface.md is missing the {concept}. Labels collected without "
        "it are not merely noisy: they are biased in a specific direction while "
        "looking perfectly precise."
    )


def test_review_interface_forbids_implicit_upload(review_interface: str) -> None:
    assert re.search(r"[Nn]othing uploads|implicit", review_interface), (
        "The reference must forbid implicit upload. An interface with a silent "
        "sync or share is out of contract, not merely undesirable."
    )
    assert re.search(r"confirmed.*path|output path", review_interface, re.I), (
        "Export must write to an operator-confirmed local path."
    )


def test_review_interface_treats_abstention_as_first_class(review_interface: str) -> None:
    assert re.search(r"never imputed|[Nn]ever impute", review_interface), (
        "Abstention must never be imputed to a label. A reviewer forced to "
        "choose on an uncovered item produces a fabricated label that is "
        "indistinguishable from a real one."
    )


def test_review_interface_does_not_mandate_a_framework(review_interface: str) -> None:
    frameworks = ("React", "Vue", "Svelte", "Django", "Flask", "Streamlit")
    named = [f for f in frameworks if f in review_interface]
    assert not named, (
        f"review-interface.md names specific frameworks: {named}. The reference "
        "defines observable completion checks so any stack, including a terminal "
        "loop, can satisfy it. Prescribing a framework narrows it needlessly."
    )


@pytest.mark.parametrize(
    "path", [_SYNTHETIC_DATA, _REVIEW_INTERFACE], ids=lambda p: p.name
)
def test_phase4_references_declare_local_first(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert declares_local_first(text), (
        f"{path.name} must declare the local-by-default rule and name "
        f"egress-redaction as the gate. Expected all of {LOCAL_FIRST_MARKERS}."
    )


@pytest.mark.parametrize(
    "path", [_SYNTHETIC_DATA, _REVIEW_INTERFACE], ids=lambda p: p.name
)
def test_phase4_references_use_the_shared_artifact_vocabulary(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    expected = {
        "synthetic-data.md": ("dataset_manifest", "provenance", "split_manifest"),
        "review-interface.md": ("human_annotation", "adjudication_record", "redaction_status"),
    }[path.name]
    missing = [a for a in expected if a not in text]
    assert not missing, (
        f"{path.name} does not speak the Phase 1 artifact contract: missing "
        f"{missing}."
    )


@pytest.mark.parametrize(
    "path", [_SYNTHETIC_DATA, _REVIEW_INTERFACE], ids=lambda p: p.name
)
def test_phase4_references_are_ascii_with_binary_verification(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert is_ascii(text), f"{path.name} must be ASCII-only."
    assert re.search(r"##\s+Verification", text), (
        f"{path.name} must end with a binary Verification checklist."
    )
    items = re.findall(r"^- \[ \] (.+)$", text.split("## Verification", 1)[1], re.M)
    assert len(items) >= 10, (
        f"{path.name} has only {len(items)} verification items; both references "
        "define more controls than that, so a short checklist means controls "
        "went unchecked."
    )


@pytest.mark.parametrize(
    "path,pattern,label",
    [
        (_SYNTHETIC_DATA, r"[Uu]ncovered", "coverage verification"),
        (_REVIEW_INTERFACE, r"[Nn]ever imputed|[Nn]ever impute", "abstention protection"),
    ],
    ids=["synthetic-data", "review-interface"],
)
def test_phase4_assertions_have_teeth(path: Path, pattern: str, label: str) -> None:
    """Deleting the target lines must make the corresponding check fail."""
    mutated = _without(path.read_text(encoding="utf-8"), pattern)
    assert not re.search(pattern, mutated), (
        f"The {label} check still matches after its lines are deleted, so it "
        "guards nothing."
    )


def test_all_four_owned_references_are_linked(aoe_skill: str) -> None:
    """The Phase 1 contract assigns ai-output-evaluation seven artifacts.

    By the end of Phase 4 all four of its references exist. This asserts the set
    as a whole, because each individual link test passes even if the routing
    table has quietly lost a row.
    """
    for basename in (
        "error-analysis.md",
        "evaluator-validation.md",
        "synthetic-data.md",
        "review-interface.md",
    ):
        assert f"references/{basename}" in aoe_skill, (
            f"The routing table lost its `{basename}` row."
        )
