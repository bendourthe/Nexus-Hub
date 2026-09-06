"""Contract tests for generated-plan lifecycle defaults (v4.0.0 Phase 3).

`implementation-plan` is the skill that writes every future multi-phase plan in
this repository and in every downstream project that installs the catalog. A
regression here does not break a build; it silently reintroduces per-phase
remote CI into every plan written afterwards, and nobody notices until the bill
arrives. So the assertions below are semantic and specific rather than
snapshot-shaped: they name the behavior, not the wording of a paragraph.

Companion to `test_cicd_lifecycle_contract.py`, which covers the pipeline half.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

PLAN_SKILL = _ROOT / "catalog" / "skills" / "workflow" / "implementation-plan" / "SKILL.md"
PLAN_CMD = _ROOT / "catalog" / "commands" / "plan.md"
PLAN_REVIEW = _ROOT / "catalog" / "skills" / "code-review" / "plan-review" / "SKILL.md"
FINAL_PHASE_REF = (
    _ROOT / "catalog" / "skills" / "workflow" / "implementation-plan"
    / "references" / "mandatory-final-phase.md"
)

#: The strict task-line grammar `tasks-to-issues` parses.
TASK_LINE = re.compile(r"^- \[ \] T\d{3}(?: \[P\])?(?: \[US\d+\])? .+ \S+$")


@pytest.fixture(scope="module")
def plan_skill() -> str:
    return PLAN_SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def final_phase() -> str:
    """The final-phase template lives in a Tier 3 reference (v4.0.0 Phase 3).

    Moved out of the body when the body crossed the 500-line soft cap. The
    template is copied once at plan-generation time, so it does not need to be
    loaded on every trigger.
    """
    return FINAL_PHASE_REF.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def plan_cmd() -> str:
    return PLAN_CMD.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Strict task format -- unchanged by this plan, asserted so it stays unchanged.
# ---------------------------------------------------------------------------


def test_skill_requires_the_strict_task_line_grammar(plan_skill: str):
    """`tasks-to-issues` parses these lines; a loosened grammar breaks the fan-out."""
    assert "T###" in plan_skill or "`T###`" in plan_skill
    assert "[P]" in plan_skill
    assert "[US" in plan_skill


def test_this_plans_own_task_lines_parse(plan_skill: str):
    """A round-trip check against a real plan, not a synthetic fixture."""
    plan = _ROOT / "docs" / "releases" / "v4" / "v4.0" / "plans" / "v4.0.0-cost-effective-ci-cd.md"
    lines = [
        ln
        for ln in plan.read_text(encoding="utf-8").splitlines()
        if re.match(r"^- \[ \] T\d{3}", ln)
    ]
    assert len(lines) >= 60, f"expected the plan's 62 task lines, found {len(lines)}"
    bad = [ln for ln in lines if not TASK_LINE.match(ln)]
    assert not bad, f"task lines that do not match the strict grammar: {bad[:3]}"


# ---------------------------------------------------------------------------
# Per-phase lifecycle.
# ---------------------------------------------------------------------------


def test_phase_testing_subtask_records_ci_impact_instead_of_authoring_the_pipeline(plan_skill: str):
    assert "CI IMPACT" in plan_skill, "the per-phase prompt must record CI impact"
    assert "[[cicd-architect]]" in plan_skill, "the record must be made against the canonical contract"
    assert "unless CI/CD is this phase's explicit deliverable" in plan_skill, (
        "the one legitimate exception must be stated, or authors will treat the ban as absolute"
    )


def test_per_phase_pipeline_authorship_is_gone(plan_skill: str):
    """The exact instruction this plan exists to remove."""
    banned = [
        "create or update the\n> CI/CD pipeline to cover this phase's changes",
        "also creates or updates the CI/CD pipeline for that phase's changes",
    ]
    for phrase in banned:
        assert phrase not in plan_skill, f"per-phase CI/CD authorship survives: {phrase!r}"


def test_a_no_op_ci_impact_record_is_explicitly_valid(plan_skill: str):
    """Without this, an author with nothing to record writes nothing and the step rots."""
    assert "is a valid outcome and must" in plan_skill


def test_every_phase_ends_with_one_local_commit(plan_skill: str):
    assert "create ONE local commit scoped to this phase" in plan_skill
    assert "- [ ] One local commit created for this phase" in plan_skill


def test_non_final_phases_are_forbidden_from_pushing(plan_skill: str):
    assert "Do NOT push, do NOT open a pull request, and do NOT start remote CI." in plan_skill
    assert "- [ ] No branch push, pull request, or remote CI run occurred" in plan_skill


def test_phase_exit_checklist_requires_a_ci_impact_record_without_a_remote_run(plan_skill: str):
    assert "- [ ] CI impact recorded against the canonical contract, with no remote CI run" in plan_skill


def test_phase_template_pairs_stability_with_a_concrete_verification_expectation(plan_skill: str):
    template = plan_skill.split("#### Phase Structure", 1)[1].split("## Complexity Tracking", 1)[0]
    assert re.search(
        r"\*\*Stability Gate\*\*: \[[^\n]+\]\n"
        r"\*\*Verification Expectation\*\*: \[[^\n]+\]",
        template,
    ), "the functional expectation must sit directly beside the Stability Gate"
    assert "reader can run or open" in template
    assert "must observe" in template
    assert "[[functional-verification]]" in template
    assert '"Tests pass" alone is not sufficient.' in template


def test_phase_exit_checklist_requires_recorded_functional_evidence(plan_skill: str):
    assert "- [ ] Verification expectation exercised and its observable result recorded" in plan_skill


# ---------------------------------------------------------------------------
# Mandatory final phase.
# ---------------------------------------------------------------------------


def test_final_phase_is_the_only_phase_permitted_to_publish(plan_skill: str):
    assert "ONLY phase permitted to push, open a pull request, or start remote CI" in plan_skill


def test_final_phase_runs_the_six_step_reconciliation(final_phase: str):
    block = final_phase.split("#### N.5 - Terminal CI/CD reconciliation", 1)
    assert len(block) == 2, "the final phase must carry the terminal reconciliation sub-task"
    body = block[1].split("#### N.6", 1)[0]
    assert "[[cicd-architect]]" in body
    for step in ("DETECT", "COMPARE", "PROPOSE", "APPROVAL", "APPLY", "RECORD"):
        assert step in body, f"the reconciliation is missing its {step} step"
    assert "none detected" in body, "a repository with no pipeline must be recorded, not assumed"
    assert "silence is not approval" in body.lower()


def test_final_phase_records_declined_differences_as_known_gaps(final_phase: str):
    body = final_phase.split("#### N.5 - Terminal CI/CD reconciliation", 1)[1].split("#### N.6", 1)[0]
    assert "[[known-gaps-tracker]]" in body
    assert "owner and a next step" in body


def test_final_phase_runs_the_tier_three_deep_pass(final_phase: str):
    body = final_phase.split("#### N.6 - Tier 3 deep pass", 1)[1].split("#### N.7", 1)[0]
    assert "[[functional-verification]]" in body
    assert "references/deep-pass.md" in body
    assert "every artifact this plan produced" in body
    assert "`## Tier 3 deep pass`" in body
    assert "global iteration budget" in body


def test_final_phase_gate_names_its_functional_expectation(final_phase: str):
    header = final_phase.split("### Sub-tasks", 1)[0]
    assert re.search(
        r"\*\*Stability Gate\*\*: [^\n]+\n"
        r"\*\*Verification Expectation\*\*: [^\n]+",
        header,
    )
    assert "[[functional-verification]]" in header
    assert "`## Tier 3 deep pass`" in header


def test_final_phase_gate_is_local_before_publication(final_phase: str):
    body = final_phase.split("#### N.9 - Testing and Stabilization", 1)[1].split("#### N.10", 1)[0]
    assert "local" in body.lower()
    assert "before the branch is published" in body


def test_final_phase_publishes_once_with_explicit_approval(final_phase: str):
    body = final_phase.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    assert "EXPLICIT approval before the plan's first branch push" in body
    assert "Push once" in body


def test_a_red_required_check_reopens_the_final_phase(final_phase: str):
    body = final_phase.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    assert "REOPENS this phase" in body
    assert "reproduce it locally" in body
    assert "without a local reproduction" in body, (
        "a blind re-run must be named as the failure mode, not merely discouraged"
    )


def test_release_handoff_waits_for_green_integration(final_phase: str):
    body = final_phase.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    assert "Merge only after every required check is green" in body
    assert "Only then hand off to `/update release`" in body


def test_final_phase_verifies_post_merge_did_not_rerun_the_suite(final_phase: str):
    body = final_phase.split("#### N.10 - Publication and integration", 1)[1].split("```", 1)[0]
    assert "did not rerun the complete suite" in body


# ---------------------------------------------------------------------------
# The dispatcher stays thin.
# ---------------------------------------------------------------------------


def test_plan_command_states_the_lifecycle_guarantee(plan_cmd: str):
    assert "## Plan lifecycle (guarantee)" in plan_cmd
    for claim in (
        "one local commit",
        "No non-final phase pushes",
        "[[cicd-architect]]",
        "green integration",
    ):
        assert claim in plan_cmd, f"the dispatcher does not surface: {claim!r}"


def test_plan_command_does_not_duplicate_the_terminal_procedure(plan_cmd: str):
    """A dispatcher that copies the procedure is a second source of truth."""
    for procedural in ("DETECT", "COMPARE", "PROPOSE", "#### N.5", "#### N.9"):
        assert procedural not in plan_cmd, (
            f"the dispatcher copied procedure from implementation-plan: {procedural!r}"
        )
    assert "lives in `[[implementation-plan]]`" in plan_cmd or (
        "live in `[[implementation-plan]]`" in plan_cmd
    ), "the dispatcher must name where the procedure actually lives"


def test_plan_command_stays_short(plan_cmd: str):
    """Thin is a size property as well as a content property."""
    assert len(plan_cmd.splitlines()) <= 150, "the plan dispatcher has stopped being thin"


# ---------------------------------------------------------------------------
# Plan review can detect a non-conforming plan.
# ---------------------------------------------------------------------------


def test_plan_review_flags_lifecycle_violations():
    text = PLAN_REVIEW.read_text(encoding="utf-8")
    assert "[[cicd-architect]]" in text, "plan review must cross-link rather than restate the policy"
    for signal in (
        "per-phase push",
        "missing local phase commit",
        "remote CI before the terminal phase",
        "missing terminal pipeline comparison",
        "release before green integration",
    ):
        assert signal in text, f"plan review cannot detect: {signal!r}"


def test_plan_review_does_not_restate_the_full_lifecycle_policy():
    """Ownership: cicd-architect states the rule; plan-review detects violations of it."""
    text = PLAN_REVIEW.read_text(encoding="utf-8")
    for owned_elsewhere in ("fast, full, platform, report, release", "runs-on", "merge_group"):
        assert owned_elsewhere not in text, (
            f"plan review duplicated policy owned by cicd-architect: {owned_elsewhere!r}"
        )


def test_body_points_at_the_final_phase_reference(plan_skill: str):
    """The template moved to Tier 3; the body must still name it, or it is an orphan."""
    assert "references/mandatory-final-phase.md" in plan_skill
    assert "N.1 through N.10" in plan_skill


def test_final_phase_reference_is_the_only_copy_of_the_template(plan_skill: str, final_phase: str):
    """Two copies of a template drift. The body keeps the rule, the reference the block."""
    assert "#### N.5 - Terminal CI/CD reconciliation" not in plan_skill
    assert "#### N.5 - Terminal CI/CD reconciliation" in final_phase
