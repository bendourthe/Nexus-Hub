"""Policy tests for .github/workflows/copilot-usage-monitor.yml (v4.13.7 Phase 3).

Modeled on ``test_cursor_usage_monitor_workflow.py``: the trigger, permission,
concurrency, pinning, and Node rules are the same, and the sibling-consistency
test keeps the checkout and setup-node pins in step with the other monitors.
The workflow is path-filtered at the workflow level, which is safe only while
it produces no required status check, so that is asserted too.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOW_DIR / "copilot-usage-monitor.yml"
EXTENSION_DIR = "extensions/copilot-usage-monitor"
REQUIRED_CHECKS = REPO_ROOT / "docs" / "policy" / "required-checks.json"

SIBLING_MONITOR_WORKFLOWS = (
    WORKFLOW_DIR / "claude-usage-monitor.yml",
    WORKFLOW_DIR / "codex-usage-monitor.yml",
    WORKFLOW_DIR / "cursor-usage-monitor.yml",
)

# PyYAML reads the bare key ``on`` as the boolean True.
ON_KEY = True


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    assert WORKFLOW.is_file(), f"Missing workflow: {WORKFLOW}"
    return load(WORKFLOW)


@pytest.fixture(scope="module")
def build_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = workflow["jobs"]
    assert set(jobs) == {"build-and-test"}
    return jobs["build-and-test"]["steps"]


def step_named(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(
        f"missing step {name!r}; present: {[s.get('name') for s in steps]}"
    )


def test_triggers_are_path_filtered_to_the_extension(workflow: dict[str, Any]) -> None:
    triggers = workflow[ON_KEY]
    assert set(triggers) == {"pull_request"}
    paths = triggers["pull_request"]["paths"]
    assert sorted(paths) == sorted(
        [f"{EXTENSION_DIR}/**", ".github/workflows/copilot-usage-monitor.yml"]
    )
    assert not any(path.startswith("scripts/") for path in paths), (
        "installers are covered by ci.yml's installer smoke test"
    )


def test_the_workflow_does_not_rerun_itself_after_the_merge(
    workflow: dict[str, Any],
) -> None:
    assert "push" not in workflow[ON_KEY], (
        "a post-merge push run repeats the pull request's tree; see the "
        "lifecycle contract section 4"
    )


def test_the_pull_request_trigger_is_limited_to_protected_branches(
    workflow: dict[str, Any],
) -> None:
    assert sorted(workflow[ON_KEY]["pull_request"]["branches"]) == ["develop", "main"]


def test_permissions_are_read_only(workflow: dict[str, Any]) -> None:
    assert workflow["permissions"] == {"contents": "read"}


def test_concurrency_cancels_superseded_runs(workflow: dict[str, Any]) -> None:
    concurrency = workflow["concurrency"]
    assert concurrency["cancel-in-progress"] is True
    assert "github.ref" in concurrency["group"]


def test_every_action_is_pinned_to_an_immutable_sha(workflow: dict[str, Any]) -> None:
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            uses = step.get("uses")
            if uses is None:
                continue
            _, _, ref = uses.partition("@")
            assert len(ref) == 40 and all(char in "0123456789abcdef" for char in ref), (
                f"{uses} must be pinned to a full 40-character commit SHA"
            )


def test_node_setup_uses_node_22_and_the_exact_lockfile_cache(
    build_steps: list[dict[str, Any]],
) -> None:
    setup = next(
        step
        for step in build_steps
        if step.get("uses", "").startswith("actions/setup-node@")
    )
    assert setup["with"]["node-version"] == "22"
    assert setup["with"]["cache"] == "npm"
    assert (
        setup["with"]["cache-dependency-path"] == f"{EXTENSION_DIR}/package-lock.json"
    )


def test_job_runs_inside_the_extension_directory(workflow: dict[str, Any]) -> None:
    defaults = workflow["jobs"]["build-and-test"]["defaults"]["run"]
    assert defaults["working-directory"] == EXTENSION_DIR


def test_gate_covers_clean_install_compile_coverage_and_packaging(
    build_steps: list[dict[str, Any]],
) -> None:
    assert step_named(build_steps, "Install dependencies")["run"].strip() == "npm ci"
    assert "npm run compile" in step_named(build_steps, "Compile (tsc)")["run"]
    assert (
        "npm run test:coverage"
        in step_named(build_steps, "Unit tests with coverage (Vitest)")["run"]
    )
    assert "npm run package" in step_named(build_steps, "Package VSIX")["run"]


def test_the_extension_scripts_the_gate_calls_exist() -> None:
    scripts = json.loads(
        (REPO_ROOT / EXTENSION_DIR / "package.json").read_text(encoding="utf-8")
    )["scripts"]
    for name in ("compile", "test:coverage", "package"):
        assert name in scripts, f"{EXTENSION_DIR}/package.json has no {name!r} script"


def test_the_path_filtered_check_is_not_required() -> None:
    """A workflow-level ``paths:`` filter is safe only for a non-required check.

    GitHub leaves a required check from an untriggered workflow Pending forever.
    """
    assert "copilot-usage-monitor" not in REQUIRED_CHECKS.read_text(encoding="utf-8")


@pytest.mark.parametrize("sibling", SIBLING_MONITOR_WORKFLOWS, ids=lambda p: p.name)
def test_monitor_workflows_share_checkout_and_node_pins(sibling: Path) -> None:
    def pins(path: Path) -> dict[str, str]:
        data = load(path)
        found: dict[str, str] = {}
        for job in data["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if uses is not None:
                    action, _, ref = uses.partition("@")
                    if action in {"actions/checkout", "actions/setup-node"}:
                        found[action] = ref
        return found

    ours = pins(WORKFLOW)
    theirs = pins(sibling)
    for action in ("actions/checkout", "actions/setup-node"):
        assert ours[action] == theirs[action], (
            f"{action} is pinned to {ours[action]} here but {theirs[action]} in "
            f"{sibling.name}; bump both together"
        )


@pytest.mark.parametrize("sibling", SIBLING_MONITOR_WORKFLOWS, ids=lambda p: p.name)
def test_monitor_workflows_share_the_trigger_and_permission_shape(
    workflow: dict[str, Any], sibling: Path
) -> None:
    theirs = load(sibling)
    assert set(theirs[ON_KEY]) == set(workflow[ON_KEY])
    assert sorted(theirs[ON_KEY]["pull_request"]["branches"]) == sorted(
        workflow[ON_KEY]["pull_request"]["branches"]
    )
    assert theirs["permissions"] == workflow["permissions"]
    assert theirs["concurrency"] == workflow["concurrency"]
