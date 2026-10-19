"""Guard the grouping contract in the stage that already resolves review scope."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "catalog/skills/code-review/multi-agent-code-review/SKILL.md"


def test_stage_one_grouping_preserves_scope_and_separates_findings():
    text = SKILL.read_text(encoding="utf-8")
    stage = text.split("### Stage 1", 1)[1].split("### Stage 2", 1)[0]
    assert "union of bundle members equals the changed-file set" in stage
    assert "at most 8 files" in stage
    assert "parent directory" in stage
    assert "empty diff" in stage and "unreadable diff" in stage
    assert "every selected file appears exactly once" in stage
    assert "~800 changed lines" not in stage
    grouping = stage.split("Deterministic grouping", 1)[1]
    assert "taxonomy" not in grouping and "verifier class" not in grouping
    assert "does not mechanically remove" in grouping
