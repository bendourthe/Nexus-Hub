"""Contract tests for the /implement execution lifecycle (v4.0.0 Phase 4).

`implement-phase` is the only skill in the catalog that mutates git history and
external state. The assertions here cover the four transitions that matter:
non-final (commit-only), final (reconcile, gate, publish, integrate), failed
remote check (reopen, reproduce locally, amend or one stabilization commit), and
release handoff (blocked until integration is green and merged).

Negative fixtures are included deliberately. The behaviors this plan removes -
"commit and push every phase" and "update CI every phase" - were the DEFAULTS
before v4.0.0, so a regression would look like a restoration to anyone who
remembers the old runbook. Asserting their absence is what makes the removal
stick.

Companion to `test_plan_lifecycle_contract.py` (what plans SAY) and
`test_cicd_lifecycle_contract.py` (what the pipeline DOES). This file covers
what the executor DOES.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

SKILL = _ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
RUNBOOK = (
    _ROOT / "catalog" / "skills" / "workflow" / "implement-phase"
    / "references" / "implement-phase-runbook.md"
)
IMPLEMENT_CMD = _ROOT / "catalog" / "commands" / "implement.md"
COMMIT_SKILL = _ROOT / "catalog" / "skills" / "workflow" / "code-commit-workflow" / "SKILL.md"


@pytest.fixture(scope="module")
def runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def command() -> str:
    return IMPLEMENT_CMD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def commit_skill() -> str:
    return COMMIT_SKILL.read_text(encoding="utf-8")


def _phase_7(runbook: str) -> str:
    marker = "## Phase 7: Quality gate (GO / NO-GO)"
    assert marker in runbook, "Phase 7 is missing"
    return runbook.split(marker, 1)[1].split("\n## ", 1)[0]


def _step_84(runbook: str) -> str:
    marker = "- **8.4 Plan-delta note (always written)**"
    assert marker in runbook, "step 8.4 is missing or was renamed"
    return runbook.split(marker, 1)[1].split("\n- **8.5", 1)[0]


def _step_811(runbook: str) -> str:
    marker = "- **8.11 Commit prompt (REQUIRED, every phase)**"
    assert marker in runbook, "step 8.11 is missing or was renamed"
    return runbook.split(marker, 1)[1].split("\n## ", 1)[0]


def _phase_9f(runbook: str) -> str:
    marker = "### 9F. Publication and integration"
    assert marker in runbook, "phase 9F is missing"
    return runbook.split(marker, 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]


# ---------------------------------------------------------------------------
# Transition 1 -- non-final phase: local validation and one commit, no push.
# ---------------------------------------------------------------------------


def test_phase_gate_keeps_four_static_gates_and_adds_proportional_smoke(runbook: str):
    gate = _phase_7(runbook)
    assert "Evaluate five gates" in gate
    for existing_gate in (
        "all tests passing (0 failures)",
        "line coverage >= 80%",
        "0 lint errors",
        "build/compile succeeds",
    ):
        assert existing_gate in gate, f"the fifth gate replaced: {existing_gate!r}"
    assert "phase's own feature was exercised and observed" in gate
    assert "primary real boundary" in gate
    assert "expected behavior matching observed behavior" in gate
    assert "[[functional-verification]]" in gate
    assert "one representative phase-scoped smoke" in gate
    assert "not the whole-plan deep pass or another full suite" in gate


def test_tests_passing_alone_is_not_functional_evidence(skill: str):
    assert '"The tests pass, so the feature works"' in skill
    assert "broken layout through four green gates" in skill


def test_non_final_phase_is_commit_only_in_every_mode(runbook: str):
    step = _step_811(runbook)
    assert "a NON-FINAL phase is commit-only in every mode" in step


def test_one_phase_non_final_offers_no_push_option(runbook: str):
    step = _step_811(runbook)
    ask = step.split("**One-phase (default), non-final:**", 1)[1].split("\n    -", 1)[0]
    assert "1. Commit only" in ask
    assert "2. Amend" in ask
    assert "3. Stop" in ask
    assert "push" not in ask.lower(), f"a push option survives in the non-final ask: {ask!r}"


def test_phase_by_phase_non_final_offers_no_push_option(runbook: str):
    step = _step_811(runbook)
    menu = step.split("**`phase-by-phase`, non-final:**", 1)[1].split("\n    -", 1)[0]
    assert "(1) commit and continue" in menu
    assert "(2) commit and pause" in menu
    assert "(3) other" in menu
    assert "push" not in menu.lower(), f"a push option survives in the phase-by-phase menu: {menu!r}"


def test_full_non_final_still_auto_commits_without_pushing(runbook: str):
    step = _step_811(runbook)
    assert "**`full` non-final:** auto-select commit-only" in step
    assert "Do not push." in step


def test_the_no_push_default_does_not_override_an_explicit_user_request(runbook: str):
    """A default is not a prohibition. Removing the menu must not remove the authority."""
    step = _step_811(runbook)
    assert "explicitly asks to push a non-final phase" in step
    assert "removes the DEFAULT, not the user's authority" in step


def test_non_final_phase_records_ci_impact_without_touching_a_pipeline(runbook: str):
    assert "- **8.3 CI impact record (per-phase, no remote run)**" in runbook
    body = runbook.split("- **8.3 CI impact record", 1)[1].split("- **8.4", 1)[0]
    assert "[[cicd-architect]]" in body
    assert "do NOT change a pipeline file" in body
    assert "unless CI/CD is THIS phase's explicit deliverable" in body
    assert "is a valid outcome and must still be written" in body


def test_every_phase_writes_one_plan_delta_in_its_history(runbook: str):
    step = _step_84(runbook)
    assert "No delta" in step
    assert "Wrong" in step
    assert "Incomplete" in step
    assert "False assumption" in step
    assert "exactly one primary disposition" in step
    assert "`## Plan delta`" in step
    assert "<version_dir>/development/history/<phase-session-history>.md" in step
    assert "observed evidence" in step
    assert "consequence for every remaining phase" in step
    assert "MUST still be written" in step


def test_only_a_blocking_plan_delta_escalates(runbook: str):
    step = _step_84(runbook)
    assert "A non-blocking delta stays in session history" in step
    assert "without plan or gap escalation" in step
    assert "A blocking delta updates the plan before the driver continues" in step
    assert "`DF` or `QG` known gap" in step


# ---------------------------------------------------------------------------
# Transition 2 -- final phase: reconcile, gate locally, publish once, integrate.
# ---------------------------------------------------------------------------


def test_final_phase_runs_the_terminal_reconciliation(runbook: str):
    duty = runbook.split("5. Run the TERMINAL PIPELINE RECONCILIATION", 1)
    assert len(duty) == 2, "duty 5 is not the terminal reconciliation"
    body = duty[1].split("\n6. ", 1)[0]
    assert "[[cicd-architect]]" in body
    for step in ("DETECT", "COMPARE", "PROPOSE", "APPROVAL", "APPLY", "RECORD"):
        assert step in body, f"the reconciliation is missing its {step} step"
    assert "ONE place in the whole plan where pipeline files change" in body


def test_the_pre_publication_gate_is_local_by_construction(runbook: str):
    assert "### 9B. Complete LOCAL gate" in runbook
    body = runbook.split("### 9B. Complete LOCAL gate", 1)[1].split("### 9F", 1)[0]
    assert "cannot depend on a remote result" in body


def test_final_phase_publishes_once_after_explicit_approval(runbook: str):
    body = _phase_9f(runbook)
    assert "EXPLICIT approval before the plan's first branch push" in body
    assert "**Push once.**" in body
    assert "Silence is not approval." in body


def test_integration_validates_the_merge_result_not_the_branch_tip(runbook: str):
    body = _phase_9f(runbook)
    assert "synthetic MERGE RESULT rather than the branch tip" in body


def test_integration_targets_the_integration_branch(runbook: str):
    body = _phase_9f(runbook)
    assert "not the protected release branch" in body


# ---------------------------------------------------------------------------
# Transition 3 -- a red required check reopens the phase.
# ---------------------------------------------------------------------------


def test_a_red_check_reopens_the_phase_and_requires_a_local_reproduction(runbook: str):
    body = _phase_9f(runbook)
    assert "REOPEN this phase" in body
    assert "reproduce it LOCALLY" in body
    assert "Never re-run a red check without a local reproduction" in body


def test_an_unreproducible_check_is_named_as_the_finding(runbook: str):
    """The gap between local and remote IS the defect; a green re-run hides it."""
    body = _phase_9f(runbook)
    assert "cannot be reproduced locally is itself the finding" in body


def test_correction_work_is_an_amend_or_one_stabilization_commit(runbook: str):
    body = _phase_9f(runbook)
    assert "ONE narrowly scoped stabilization commit" in body
    assert "never both, and never a series" in body.lower(), (
        "without this, a red check invites a stream of fix-up commits"
    )
    assert "[[code-commit-workflow]]" in body, "the choice between the two is owned there"


# ---------------------------------------------------------------------------
# Transition 4 -- release handoff is gated on green, merged integration.
# ---------------------------------------------------------------------------


def test_release_handoff_is_held_until_integration_is_green_and_merged(runbook: str):
    hold = runbook.split("**Hold the handoff**", 1)[1].split("\n\n", 1)[0]
    for condition in (
        "the branch has not been published",
        "a required check is not green",
        "the merge to the integration branch has not landed",
    ):
        assert condition in hold, f"the handoff is not held on: {condition!r}"


def test_post_merge_behavior_is_verified_before_release(runbook: str):
    body = _phase_9f(runbook)
    assert "did NOT rerun the complete suite" in body


def test_no_tag_or_release_is_created_in_the_publication_step(runbook: str):
    body = _phase_9f(runbook)
    assert "Never tag and never publish a release here" in body


def test_publication_is_a_required_evidence_section(runbook: str):
    assert "10. Publication and integration" in runbook


def test_tier_3_deep_pass_is_a_required_evidence_section(runbook: str):
    evidence = runbook.split("Required sections:", 1)[1].split("\n### 9.0", 1)[0]
    assert "6. Tier 3 deep pass" in evidence
    gate = runbook.split("### 9.0", 1)[1].split("\n### 9A", 1)[0]
    assert "[[functional-verification]]" in gate
    assert "references/deep-pass.md" in gate
    assert "`## Tier 3 deep pass`" in gate
    assert "<version_dir>/development/last-phase-evidence.md" in gate
    assert "ambiguous evidence selects `run`" in gate


def test_tier_3_duty_is_fail_closed_and_has_no_silent_skip(runbook: str):
    gate = runbook.split("### 9.0", 1)[1].split("\n### 9A", 1)[0]
    assert "This duty is fail-closed" in gate
    assert "may be omitted only by recording a `QG` or `DF` known gap" in gate
    assert "A reasoned no-op is completion of the duty, not an omission" in gate


# ---------------------------------------------------------------------------
# Negative fixtures -- the pre-v4.0.0 defaults must stay gone.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phrase",
    [
        "2. Commit and push",
        "(2) commit, push, and continue",
        "(4) commit, push, and pause",
        "five-option menu",
        "Commit-and-push prompt",
    ],
)
def test_the_old_commit_and_push_every_phase_wording_is_gone(runbook: str, phrase: str):
    assert phrase not in runbook, f"pre-v4.0.0 push default survives in the runbook: {phrase!r}"


@pytest.mark.parametrize(
    "phrase",
    [
        "CI/CD readiness + optimization (per-phase)",
        "run an optimization pass",
    ],
)
def test_the_old_update_ci_every_phase_wording_is_gone(runbook: str, phrase: str):
    assert phrase not in runbook, f"pre-v4.0.0 per-phase CI authorship survives: {phrase!r}"


def test_the_command_no_longer_advertises_a_per_phase_push(command: str):
    for phrase in ("commit, push, and continue", "commit, push, and pause", "commit-and-push prompt"):
        assert phrase not in command, f"the dispatcher still advertises: {phrase!r}"


# ---------------------------------------------------------------------------
# The skill's always-loaded invariants agree with the runbook.
# ---------------------------------------------------------------------------


def test_skill_invariants_state_commit_only_and_terminal_publication(skill: str):
    assert "COMMIT-ONLY on every non-final phase in every mode" in skill
    assert "[[cicd-architect]]" in skill
    assert "terminal pipeline reconciliation" in skill


def test_skill_verification_covers_the_new_gates(skill: str):
    assert "recorded CI impact without changing a pipeline file" in skill
    assert "five-part GO/NO-GO gate" in skill
    assert "`## Plan delta`" in skill
    assert "`## Tier 3 deep pass`" in skill
    assert "pushed exactly once after explicit approval" in skill
    assert "a non-green integration blocked `/update release`" in skill


def test_tier_one_overview_tracks_the_current_lifecycle(skill: str):
    frontmatter = skill.split("---", 2)[1]
    for phrase in (
        "five-part GO/NO-GO gate",
        "eleven ordered steps",
        "always writes the Plan delta",
        "non-final phase commit-only",
        "Tier 3 deep pass",
    ):
        assert phrase in frontmatter
    for obsolete in ("four-part GO/NO-GO", "ten-step post-phase", "commit-and-push prompt"):
        assert obsolete not in frontmatter


def test_phase_seven_reopens_and_reruns_a_failed_functional_smoke(runbook: str):
    phase_7 = _phase_7(runbook)
    assert "Any failure REOPENS the phase" in phase_7
    assert "return a fifth-gate mismatch or blocked exercise to Phase 2" in phase_7
    assert "rerun the proportional smoke and all of Phase 7" in phase_7
    assert "three-iteration budget" in phase_7
    assert "explicit `QG` known gap" in phase_7


def test_terminal_deep_pass_precedes_fresh_goal_review(runbook: str):
    evidence = runbook.split("Required sections:", 1)[1].split("\n### 9.0", 1)[0]
    gate = runbook.split("### 9.0", 1)[1].split("\n### 9A", 1)[0]
    assert evidence.index("6. Tier 3 deep pass") < evidence.index(
        "7. Goal-vs-codebase review"
    )
    assert gate.index("6. Invoke `[[functional-verification]]`") < gate.index(
        "7. Independent Goal-vs-codebase review"
    )
    assert "after the deep pass reaches its terminal disposition" in gate


# ---------------------------------------------------------------------------
# The dispatcher stays thin.
# ---------------------------------------------------------------------------


def test_command_states_the_lifecycle_guarantee(command: str):
    assert "## Phase lifecycle (guarantee)" in command
    assert "[[cicd-architect]]" in command


def test_command_does_not_duplicate_the_runbook(command: str):
    for procedural in ("### 9F.", "- **8.11", "- **8.4 Plan-delta", "- **8.3", "DETECT"):
        assert procedural not in command, (
            f"the dispatcher copied procedure from the runbook: {procedural!r}"
        )


def test_command_stays_within_its_scope_budget(command: str):
    assert len(command.splitlines()) <= 120, "the implement dispatcher has stopped being thin"


# ---------------------------------------------------------------------------
# code-commit-workflow keeps its generic workflow and gains plan context.
# ---------------------------------------------------------------------------


def test_commit_skill_defines_a_plan_context_mode(commit_skill: str):
    assert "## Plan-Context Mode (invoked by `/implement`)" in commit_skill
    body = commit_skill.split("## Plan-Context Mode", 1)[1].split("## Instructions", 1)[0]
    assert "The commit unit is the phase, not the sub-task" in body
    assert "Non-final plan commits stay LOCAL" in body


def test_plan_context_mode_is_explicitly_scoped(commit_skill: str):
    """Without this, the phase-boundary rule leaks into every one-off commit."""
    body = commit_skill.split("## Plan-Context Mode", 1)[1].split("## Instructions", 1)[0]
    assert "Outside that context, ignore it." in body


def test_plan_context_mode_preserves_plan_defined_granularity(commit_skill: str):
    body = commit_skill.split("## Plan-Context Mode", 1)[1].split("## Instructions", 1)[0]
    assert "independently revertible units inside a phase" in body


def test_generic_one_off_commit_workflow_survives(commit_skill: str):
    """The plan-context mode must not have replaced the skill's ordinary use."""
    for section in (
        "### Step 1: Review Staged Changes",
        "### Step 3: Write Commit Message",
        "### Step 5: Verify Commit",
        "## Atomic Commits",
        "## Pre-Commit Checklist",
    ):
        assert section in commit_skill, f"the generic workflow lost: {section!r}"


def test_commit_skill_explains_remote_correction_work(commit_skill: str):
    body = commit_skill.split("## Plan-Context Mode", 1)[1].split("## Instructions", 1)[0]
    assert "Correction work after a red required check" in body
    assert "Never both, and never a series." in body
