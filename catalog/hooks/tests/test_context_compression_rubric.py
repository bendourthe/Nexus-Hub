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


def test_summary_rules_preserve_verification_debt_without_inference() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    assert "Carry verification debt forward" in text
    assert "[[verification-before-completion]]" in text
    assert "Do not infer" in text
    assert "Preserve the resolved result verbatim" in text


def test_staged_gate_orders_preconditions_rubric_and_backstop() -> None:
    text = RUBRIC.read_text(encoding="utf-8")
    preconditions = text.index("**Cheap deterministic preconditions.**")
    rubric = text.index("**Evidence-gated rubric.**")
    backstop = text.index("**Hard backstop.**")

    assert preconditions < rubric < backstop
    assert "at least 40,000 tokens" in text
    assert "at least 2 rounds" in text
    assert "0.30 times the context window" in text
    assert "source study's values, not Nexus-Hub-validated thresholds" in text


def test_probe_hygiene_is_mandatory_and_does_not_pollute_context() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    assert "must not remain in the trajectory it judges" in text
    assert "remove both probe and verdict after a CONTINUE decision" in text
    assert "This is mandatory whenever the fire/suppress rubric is used" in text


def test_context_degradation_does_not_duplicate_phase_three_rules() -> None:
    text = DEGRADATION_SKILL.read_text(encoding="utf-8")

    for owned_phrase in (
        "Carry verification debt forward",
        "Do not infer",
        "Preserve the resolved result verbatim",
        "Cheap deterministic preconditions",
        "Hard backstop",
        "Probe hygiene",
    ):
        assert owned_phrase not in text
