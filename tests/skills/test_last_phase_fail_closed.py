"""Contract tests for fail-closed last-phase duties (v3.21.0 Phase 1).

These assertions lock the planner/implementer wording the phase rewrote:
last-phase work is evidenced, Goal-vs-codebase review is independent of
checkboxes, and there is no casual skip license on Phase 9.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLANNER = ROOT / "catalog" / "skills" / "workflow" / "implementation-plan" / "SKILL.md"
RUNBOOK = (
    ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "implement-phase"
    / "references"
    / "implement-phase-runbook.md"
)
PLAN_CMD = ROOT / "catalog" / "commands" / "plan.md"
SESSION_HISTORY = ROOT / "catalog" / "skills" / "workflow" / "session-history" / "SKILL.md"
COMMAND_SCOPE_LINE_BUDGET = 150
EVIDENCE_PATH = "<version_dir>/development/last-phase-evidence.md"
GOAL_REVIEW = "Goal-vs-codebase"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_planner_requires_evidence_file_and_goal_review() -> None:
    text = _read(PLANNER)
    assert EVIDENCE_PATH in text
    assert GOAL_REVIEW in text
    assert "fail-closed" in text


def test_planner_has_no_near_noop_license() -> None:
    text = _read(PLANNER)
    assert "near-no-op" not in text
    assert "accept `skip <X>`" not in text


def test_runbook_requires_evidence_file_and_goal_review() -> None:
    text = _read(RUNBOOK)
    assert EVIDENCE_PATH in text
    assert GOAL_REVIEW in text
    assert "BLOCKS the 9C-9E" in text or "BLOCKED" in text or "blocks" in text.lower()


def test_runbook_has_no_casual_phase_9_skip() -> None:
    text = _read(RUNBOOK)
    assert "near-no-op" not in text
    assert "accept `skip <X>`" not in text


def test_runbook_requires_the_tier_3_deep_pass_evidence_section() -> None:
    text = _read(RUNBOOK)
    gate = text[text.index("### 9.0"):text.index("### 9A")]
    assert "[[functional-verification]]" in gate
    assert "references/deep-pass.md" in gate
    assert "<version_dir>/development/last-phase-evidence.md" in gate
    assert "`## Tier 3 deep pass`" in gate


def test_tier_3_omission_requires_a_recorded_quality_or_deferral_gap() -> None:
    text = _read(RUNBOOK)
    gate = text[text.index("### 9.0"):text.index("### 9A")]
    assert "may be omitted only by recording a `QG` or `DF` known gap" in gate
    for field in ("Source phase", "Plan reference", "Reason", "Suggested next step"):
        assert field in gate


def test_plan_command_is_thin_and_mentions_fail_closed_last_phase() -> None:
    text = _read(PLAN_CMD)
    line_count = len(text.splitlines())
    assert line_count < COMMAND_SCOPE_LINE_BUDGET, (
        f"catalog/commands/plan.md is {line_count} lines; "
        f"command-scope budget is {COMMAND_SCOPE_LINE_BUDGET}"
    )
    assert "thin dispatcher" in text
    assert "fail-closed last phase" in text
    assert "does not duplicate the template" in text


def test_session_history_defers_human_qa_until_last_phase() -> None:
    text = _read(SESSION_HISTORY)
    assert "human QA is deferred to the last phase" in text
    assert "last phase of a plan" in text or "plan's last phase" in text
