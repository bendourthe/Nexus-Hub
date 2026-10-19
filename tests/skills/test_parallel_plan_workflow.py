"""Regression contracts for parallel implementation and sequential publication.

These exercise distributed instructions. Native validator and CLI tests prove
the corresponding runtime admissions; textual contracts cannot prove compliance.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "catalog/skills"
RUNBOOK = SKILLS / "workflow/implement-phase/references/implement-phase-runbook.md"
CONTRACT = SKILLS / "workflow/implement-phase/references/completion-contract.md"


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        return text.split("---\n", 2)[2]
    return text


def test_dispatchers_separate_implementation_from_release():
    for name in ("plan", "implement"):
        command = body(ROOT / f"catalog/commands/{name}.md")
        assert "implementation" in command.lower()
        assert (
            "release order" in command
            or "publish and release in semantic-version order" in command
        )
        assert "[[plan-queue-assessment]]" in command
    command = body(ROOT / "catalog/commands/implement.md")
    assert "automatically dispatches eligible whole-plan workers" in command
    assert "available harness agent tools" in command
    assert "implementation-ready" in command


def test_planner_requires_claims_and_preserves_frozen_plans():
    planner = body(SKILLS / "workflow/implementation-plan/SKILL.md")
    assert "## Implementation dependencies and ownership" in planner
    for key in ("depends_on", "read_paths", "write_paths"):
        assert f'"{key}"' in planner
    assert "assessment sidecar" in planner
    assert "do not change the frozen plan prose" in planner


def test_queue_inventory_cannot_treat_task_paths_as_complete_claims():
    queue = body(SKILLS / "workflow/plan-queue-assessment/SKILL.md")
    assert "lower bound" in queue
    assert "write/write and write/read conflicts" in queue
    assert "case collisions" in queue
    assert "semantic implementation inputs" in queue
    assert "snapshot result as current integration proof" in queue
    assert "original implementation task unchecked" in queue
    assert "conservative serial fallback" in queue


@pytest.mark.parametrize("api", ["record member-implement-start", "check-member"])
def test_worker_apis_are_parent_bound(api):
    for path in (RUNBOOK, CONTRACT):
        text = body(path)
        line = next(line for line in text.splitlines() if f"{api} --minor" in line)
        assert "--minor" in line
        assert "--member" in line
        assert "--session" in line
        assert "--repo" in line


def test_workers_are_dispatched_and_observed_instead_of_launch_suggestions():
    text = body(RUNBOOK)
    for requirement in (
        "actual returned agent handle",
        "available slots",
        "aggregate spend budget",
        "Share the run's review and stabilization limits",
        "actual harness agent tool",
        "Do not invoke standalone `/implement`",
        "Only the coordinator mutates signed state",
        "Start another eligible member immediately",
        "READY_FOR_COORDINATOR",
        "not generic validation deferrals",
        "does not push, open a pull request",
    ):
        assert requirement in text
    assert "NEW terminal window" not in text
    assert "one member at a time in the recorded version order" not in text


def test_publication_barrier_preserves_completion_and_coordinator_ownership():
    text = body(CONTRACT)
    publication = text.split("**Member gate (publication admission).**", 1)[1]
    for requirement in (
        "other than `cleanup.*`",
        "cannot-verify non-cleanup",
        "live remote tip",
        "previous release tag/back-merge",
        "--coordinator-claims",
        "exact literal file paths",
        "never grants CI/workflow, permission or secret authority",
        "union of worker and signed coordinator paths",
        "before comprehensive final validation",
        "current member's green merged integration",
        "ancestor of its actual merged result",
    ):
        assert requirement in publication
    assert "Cleanup remains mandatory for final completion" in publication


def test_claim_reservations_survive_agent_exit_and_projection_survives_merge():
    text = body(CONTRACT)
    assert (
        "Failed, interrupted and implementation-ready workers retain reservations"
        in text
    )
    assert "Agent termination is not claim retirement" in text
    assert "same registered branch/root/base/claims" in text
    assert "canonical merged artifacts through the controller" in text
    assert "missing or mismatched worker is cannot-verify" in text


@pytest.mark.parametrize(
    "skill", ["agent-orchestration-primitives", "multi-agent-coordinator"]
)
def test_orchestration_allows_only_scoped_independent_production_writers(skill):
    text = body(SKILLS / f"orchestration/{skill}/SKILL.md")
    assert "exclusive" in text
    assert "pre-agreed contracts" in text
    assert "unknown" in text
    assert "**do not parallelize code-writing**" not in text
    assert "No production code is being written by parallel agents" not in text


def test_missing_agent_tools_has_an_explicit_serial_fallback():
    text = body(RUNBOOK)
    assert "If agent tools or worktrees are unavailable" in text
    assert "use serial implementation under the same ordered publication gate" in text
    assert "Do not add a worker process engine" in text


def test_release_cleanup_keeps_active_minor_controller_without_overriding_executor():
    command = body(ROOT / "catalog/commands/update.md")
    step = command.split("6.5. **Plan worktree integration and teardown**", 1)[1].split(
        "\n7. ", 1
    )[0]
    assert "active minor controller or active worker" in step
    assert "Never override a `KEEP`" in step
    assert "final minor completion still requires cleanup" in step
    assert "completion-contract.md" in step
