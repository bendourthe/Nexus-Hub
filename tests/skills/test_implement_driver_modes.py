"""Contract tests for /implement driver modes (v3.21.0 Phase 2, v4.3.0 T012).

Locks argument tokens and per-mode 8.11 behavior.

v4.0.0 Phase 4 changed what this file protects. The push options it used to
pin - the one-phase "2. Commit and push" and the phase-by-phase five-option
menu - were REMOVED, because a non-final phase is now commit-only in every
mode. The mode tokens, the aliases, the driver-loop structure, and the
dispatcher-stays-thin budget are unchanged and still asserted here.

The removed options are covered by NEGATIVE fixtures in
`test_implement_lifecycle_contract.py`, which owns the lifecycle contract.
This file keeps its original job: proving the three modes exist, are named
consistently across the command, the skill, and the runbook, and each resolves
to a defined 8.11 behavior.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENT_CMD = ROOT / "catalog" / "commands" / "implement.md"
RUNBOOK = (
    ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "implement-phase"
    / "references"
    / "implement-phase-runbook.md"
)
SKILL = ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
README = ROOT / "README.md"
GUIDE = ROOT / "guides" / "website" / "nexus-hub-guide.html"
SKILL_REGISTRY = ROOT / "data" / "skills.json"
COMMAND_SCOPE_LINE_BUDGET = 150


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_implement_command_names_driver_tokens_and_aliases() -> None:
    text = _read(IMPLEMENT_CMD)
    assert "in-full" in text
    assert "full" in text
    assert "phase-by-phase" in text
    assert "commit-only on non-final phases" in text
    # v4.0.0: the phase-by-phase menu lost its two push options.
    assert "(1) commit and continue" in text
    assert "(2) commit and pause" in text
    assert "(3) other" in text


def test_full_is_canonical_and_in_full_is_the_compatibility_alias() -> None:
    command = _read(IMPLEMENT_CMD)
    runbook = _read(RUNBOOK)
    skill = _read(SKILL)
    readme = _read(README)
    guide = _read(GUIDE)
    registry = _read(SKILL_REGISTRY)

    assert "`/implement <slug-or-path> full` (alias `in-full`)" in command
    assert "Driver mode is a later whole token only: `full` (alias `in-full`)" in runbook
    assert "mode is `full` (alias `in-full`)" in skill
    assert "`/implement <slug> full` (alias `in-full`)" in readme
    assert "<code>full</code><span>Run every incomplete phase in order (alias: in-full)." in guide
    assert "implement full (alias in-full)" in registry

    for text in (command, runbook, skill, readme):
        assert "`in-full` (alias `full`)" not in text
    assert "<code>in-full</code><span>Run every incomplete phase in order (alias: full)." not in guide
    assert "implement in-full (alias full)" not in registry


def test_implement_command_stays_thin_and_one_phase_by_default() -> None:
    text = _read(IMPLEMENT_CMD)
    line_count = len(text.splitlines())
    assert line_count < COMMAND_SCOPE_LINE_BUDGET, (
        f"catalog/commands/implement.md is {line_count} lines; "
        f"command-scope budget is {COMMAND_SCOPE_LINE_BUDGET}"
    )
    assert "thin dispatcher" in text
    assert "/implement` (bare)" in text
    assert "stay one-phase" in text
    assert "The driver loop lives in that skill" in text
    assert "## Phase 0:" not in text
    assert "## Phase 8:" not in text


def test_runbook_documents_driver_loop_and_commit_only_non_final() -> None:
    text = _read(RUNBOOK)
    assert "in-full" in text
    assert "full" in text
    assert "phase-by-phase" in text
    assert "commit-only" in text
    assert "Do not push" in text
    # v4.0.0: three options, not five; the two push options were removed.
    assert "three-option menu" in text
    assert "(1) commit and continue" in text
    assert "(3) other" in text
    assert "Never tag or push the release from the driver" in text


def test_one_phase_commit_prompt_is_not_the_only_811_path() -> None:
    """Negative fixture: the old always-ask-then-stop commit path is not exclusive."""
    runbook = _read(RUNBOOK)
    command = _read(IMPLEMENT_CMD)
    # v4.0.0 Phase 4: three options, not four. "Commit and push" was removed
    # because a non-final phase is commit-only in every mode; its absence is a
    # negative fixture in test_implement_lifecycle_contract.py.
    #
    # Asserting the options and their ORDER rather than the exact sentence: the
    # Communication Contract requires each option to carry a plain-language
    # consequence, so the wording grows over time, and pinning the one-line form
    # made this a text-fossil test that failed on a deliberate improvement.
    assert "always ask" in runbook
    options = ["1. Commit only", "2. Amend", "3. Stop"]
    positions = [runbook.find(opt) for opt in options]
    missing = [opt for opt, pos in zip(options, positions) if pos == -1]
    assert not missing, "missing 8.11 option(s): " + repr(missing)
    assert positions == sorted(positions), "8.11 options are out of order"
    assert "loop to 8.10" in runbook
    assert "One-phase (default), non-final:" in runbook
    assert "**`full` non-final:** auto-select commit-only" in runbook
    assert "always ask" not in command
    assert "the only path" not in runbook.lower()


def test_skill_overview_mentions_driver_loop() -> None:
    text = _read(SKILL)
    assert "in-full" in text
    assert "phase-by-phase" in text
    assert "commit-only" in text
    # v4.3.0: the skill states the per-mode 8.11 shapes rather than a menu size.
    assert "COMMIT-ONLY on every non-final phase in every mode" in text
