"""The minor-entry re-plan step stays in the implement-phase runbook (v4.15.6).

During the v4.15 run, plans declared serial routes and dependencies that nobody challenged, and
three dispatchable members sat idle. The runbook now requires a whole-minor re-plan at every
`/implement vX.Y` start and resume. These assertions keep that step from being edited away.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = (
    ROOT
    / "catalog/skills/workflow/implement-phase/references/implement-phase-runbook.md"
)
QUEUE_SKILL = ROOT / "catalog/skills/workflow/plan-queue-assessment/SKILL.md"


def _phase_0c() -> str:
    text = RUNBOOK.read_text(encoding="utf-8")
    start = text.index("### Phase 0c:")
    end = text.index("\n### ", start + 1)
    return text[start:end]


def test_phase_0c_requires_a_whole_minor_replan_at_start_and_resume():
    section = _phase_0c()
    assert "Minor-entry re-plan" in section
    assert "every `/implement vX.Y` start and every resume" in section
    assert "re-assess all unshipped members together" in section


def test_replan_names_concrete_reasons_and_challenges_the_rest():
    section = _phase_0c()
    assert "serial route" in section and "`depends_on`" in section
    assert "concrete reason" in section
    assert "challengeable" in section


def test_replan_records_the_maximum_parallel_lane_set_before_dispatch():
    section = _phase_0c()
    assert "maximum parallel lane set" in section
    assert "before dispatching" in section


def test_queue_skill_points_back_to_the_minor_entry_step():
    text = QUEUE_SKILL.read_text(encoding="utf-8")
    assert "minor-entry re-plan" in text and "Phase 0c" in text


def test_idle_lane_is_a_defect_with_a_recorded_blocker_form():
    section = _phase_0c()
    assert "IDLE LANE DEFECT" in section
    assert "blocked:waits-merge:" in section
    assert "ACTION: dispatch-required" in section


def test_replan_starts_from_the_claims_that_block_lanes():
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "Claims that block parallel lanes" in text
    assert "Claims that block parallel lanes" in QUEUE_SKILL.read_text(encoding="utf-8")
