"""Contract tests for the context-compression fire/suppress rubric."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
COMPRESSION = ROOT / "catalog" / "skills" / "orchestration" / "context-compression"
COMPRESSION_SKILL = COMPRESSION / "SKILL.md"
RUBRIC = COMPRESSION / "references" / "compaction-rubric.md"
DEGRADATION_SKILL = (
    ROOT / "catalog" / "skills" / "orchestration" / "context-degradation" / "SKILL.md"
)


def _description(text: str) -> str:
    return next(
        line.removeprefix("description: ").strip().strip('"')
        for line in text.splitlines()
        if line.startswith("description: ")
    )


def test_context_compression_links_owned_rubric() -> None:
    skill = COMPRESSION_SKILL.read_text(encoding="utf-8")

    assert "[compaction fire/suppress rubric](references/compaction-rubric.md)" in skill
    assert RUBRIC.is_file()


def test_rubric_has_four_evidence_gated_conditions_and_fire_rule() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    for condition in ("CLOSED-UNIT", "SUMMARIZABLE", "PROGRESS", "STUCK"):
        assert text.count(f"| {condition} |") == 1
    assert "Every YES answer requires a verbatim quotation" in text
    assert "An answer without a quotation defaults to NO" in text
    assert (
        "Compact only when CLOSED-UNIT, SUMMARIZABLE, and PROGRESS are all YES, "
        "and STUCK is NO."
    ) in text


def test_context_degradation_delegates_without_copying_conditions() -> None:
    text = DEGRADATION_SKILL.read_text(encoding="utf-8")

    assert "owned by `[[context-compression]]`" in text
    assert not all(condition in text for condition in ("CLOSED-UNIT", "SUMMARIZABLE", "PROGRESS", "STUCK"))


def test_description_stays_within_agentskills_limit() -> None:
    text = COMPRESSION_SKILL.read_text(encoding="utf-8")

    assert len(_description(text)) <= 1024
