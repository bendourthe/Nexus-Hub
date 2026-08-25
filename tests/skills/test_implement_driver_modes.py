"""Contract tests for /implement driver modes (v3.21.0 Phase 2).

Locks argument tokens, commit-only non-final in-full behavior, and the
phase-by-phase five-option menu. Also proves the old one-phase
commit-and-push ask is no longer the only 8.10 path.
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
COMMAND_SCOPE_LINE_BUDGET = 150


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_implement_command_names_driver_tokens_and_aliases() -> None:
    text = _read(IMPLEMENT_CMD)
    assert "in-full" in text
    assert "full" in text
    assert "phase-by-phase" in text
    assert "commit-only on non-final phases" in text
    assert "(1) commit and continue" in text
    assert "(2) commit, push, and continue" in text
    assert "(3) commit and pause" in text
    assert "(4) commit, push, and pause" in text
    assert "(5) other" in text


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
    assert "five-option menu" in text
    assert "(1) commit and continue" in text
    assert "(5) other" in text
    assert "Never tag or push the release from the driver" in text


def test_one_phase_commit_prompt_is_not_the_only_810_path() -> None:
    """Negative fixture: the old always-ask-then-stop 8.10 is not exclusive."""
    runbook = _read(RUNBOOK)
    command = _read(IMPLEMENT_CMD)
    # v4.0.0: assert the four options and their order, not the exact sentence.
    # The Communication Contract requires each option to carry a plain-language
    # consequence, so the wording grew; pinning the old one-line form made this
    # a text-fossil test that failed on a deliberate improvement and taught
    # nothing about the contract it was written to protect.
    assert "always ask" in runbook
    options = ["1. Commit only", "2. Commit and push", "3. Amend", "4. Stop"]
    positions = [runbook.find(opt) for opt in options]
    assert all(pos != -1 for pos in positions), f"missing 8.10 option(s): {
        [opt for opt, pos in zip(options, positions) if pos == -1]
    }"
    assert positions == sorted(positions), "8.10 options are out of order"
    assert "loop to 8.9" in runbook
    assert "One-phase (default):" in runbook
    assert "**`in-full` non-final:** auto-select commit-only" in runbook
    assert "always ask" not in command
    assert "the only path" not in runbook.lower()


def test_skill_overview_mentions_driver_loop() -> None:
    text = _read(SKILL)
    assert "in-full" in text
    assert "phase-by-phase" in text
    assert "commit-only" in text
    assert "five-option menu" in text
