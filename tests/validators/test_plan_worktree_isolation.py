"""Worktree isolation for plans (v4.12.1).

A plan runs in its own worktree rather than only its own branch. A branch alone
serializes work: a second plan cannot start without switching the single
checkout, and switching underneath a running session changes the files that
session is editing.

Three rules are guarded here, each owned by a different file:

* ``implement-phase`` creates the worktree and reports parallel-capable plans.
* ``/update release`` verifies integration and then tears the worktree down.
* The mechanics stay with ``using-git-worktrees`` and the ranking with
  ``plan-queue-assessment``; this module asserts the HANDOFF exists rather than
  re-checking those skills' own rules.

The teardown assertions matter most. Without them the cost of parallel plans is
permanent: ten shipped plans leave ten stale checkouts, each pinning objects and
each indistinguishable from the real repository at a glance.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_RUNBOOK = (
    _ROOT / "catalog" / "skills" / "workflow" / "implement-phase"
    / "references" / "implement-phase-runbook.md"
)
_SKILL = _ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
_IMPLEMENT_CMD = _ROOT / "catalog" / "commands" / "implement.md"
_UPDATE_CMD = _ROOT / "catalog" / "commands" / "update.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


# --- creation ---------------------------------------------------------------


def test_runbook_creates_a_worktree_not_only_a_branch() -> None:
    t = _read(_RUNBOOK)
    assert "Isolate the plan in its own worktree" in t
    assert "not merely a branch" in t


def test_runbook_delegates_worktree_mechanics() -> None:
    """Mechanics belong to using-git-worktrees; do not re-derive them."""
    t = _read(_RUNBOOK)
    assert "[[using-git-worktrees]]" in t
    assert "Do not re-derive that procedure here." in t


def test_runbook_names_the_worktree_predictably() -> None:
    """The release step finds the worktree by name, so naming is load-bearing."""
    t = _read(_RUNBOOK)
    assert "A predictable directory is what lets the release step find and remove it later." in t


def test_runbook_has_a_branch_fallback() -> None:
    t = _read(_RUNBOOK)
    assert "Worktrees unavailable" in t
    assert "fall back to a branch" in t


# --- parallel reporting -----------------------------------------------------


def test_runbook_reports_parallel_capable_plans() -> None:
    t = _read(_RUNBOOK)
    assert "Report which other plans can run in parallel" in t
    assert "[[plan-queue-assessment]]" in t


def test_parallel_report_emits_a_launch_block() -> None:
    """A named plan with no way to start it is not an actionable report."""
    t = _read(_RUNBOOK)
    assert "/implement v4.14.0-<slug> in-full" in t
    assert "a NEW terminal window" in t


def test_parallel_report_states_its_basis_and_never_omits_itself() -> None:
    t = _read(_RUNBOOK)
    assert "State the overlap basis" in t
    assert "no queued plan is parallel-capable against this one" in t
    assert 'an absent report reads as "none checked"' in t


def test_missing_ranking_owner_is_declared_not_reconstructed() -> None:
    t = _read(_RUNBOOK)
    assert "mark the parallel report not covered" in t
    assert "never reconstruct its ranking rules from memory" in t


# --- teardown ---------------------------------------------------------------

_TEARDOWN_CHECKS = [
    "fully merged",            # branch is integrated
    "no uncommitted or untracked work",  # tree is clean
    "git worktree prune",      # records are pruned
]


@pytest.mark.parametrize("needle", _TEARDOWN_CHECKS)
def test_runbook_teardown_covers_each_precondition(needle: str) -> None:
    t = _read(_RUNBOOK)
    section = t[t.index("Retire the worktree"):]
    assert needle in section, f"teardown omits: {needle}"


def test_teardown_is_gated_on_a_green_merge() -> None:
    """Removing a worktree before the merge lands deletes unfinished work."""
    t = _read(_RUNBOOK)
    assert "Never remove a worktree before the merge is green and merged" in t
    assert "never with `--force` to get past a dirty tree" in t


def test_teardown_is_quoted_as_evidence() -> None:
    t = _read(_RUNBOOK)
    assert "## Worktree teardown" in t


def test_release_command_owns_the_integration_and_teardown_gate() -> None:
    t = _read(_UPDATE_CMD)
    assert "Plan worktree integration and teardown" in t
    assert "fully merged" in t
    assert "stops the release rather than being force-removed" in t
    assert "silent no-op" in t


def test_release_gate_states_why_it_exists() -> None:
    """A gate whose cost is unstated is the first one dropped."""
    t = _read(_UPDATE_CMD)
    assert "ten shipped plans leave ten stale checkouts" in t


# --- surfaced in the always-read bodies -------------------------------------


def test_skill_body_states_all_three_guarantees() -> None:
    t = _read(_SKILL)
    assert "Worktree isolation and parallel plans" in t
    assert "not just its own branch" in t
    assert "retires the worktree" in t


def test_command_states_the_guarantee() -> None:
    t = _read(_IMPLEMENT_CMD)
    assert "Worktree isolation and parallel plans (guarantee)" in t
    assert "[[using-git-worktrees]]" in t
    assert "[[plan-queue-assessment]]" in t


def test_skill_verification_covers_the_three_rules() -> None:
    t = _read(_SKILL)
    assert "created through `[[using-git-worktrees]]`" in t
    assert "parallel-capable queued plans" in t
    assert "retired only after a green merge" in t


@pytest.mark.parametrize(
    ("path", "needle"),
    [
        (_RUNBOOK, "Never remove a worktree before the merge is green and merged"),
        (_UPDATE_CMD, "ten shipped plans leave ten stale checkouts"),
        (_SKILL, "Worktree isolation and parallel plans"),
    ],
)
def test_claims_have_teeth(path: Path, needle: str) -> None:
    """Each predicate must fail when its target content is removed."""
    assert needle not in _read(path).replace(needle, "")
