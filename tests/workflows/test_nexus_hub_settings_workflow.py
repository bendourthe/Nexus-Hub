"""Policy tests for .github/workflows/nexus-hub-settings.yml (v4.14.6 Phase 5).

Modeled on ``test_copilot_usage_monitor_workflow.py``: the trigger, permission,
concurrency, pinning, and Node rules are the same, and the sibling-consistency
tests keep the checkout and setup-node pins in step with the other extension
workflows. The workflow is path-filtered at the workflow level, which is safe only
while it produces no required status check, so that is asserted too.

Two rules are specific to this workflow:

- It merges to ``develop`` BEFORE ``extensions/nexus-hub-settings`` does, and
  ``scripts/ci/**`` is a trigger path. A pull request from an older base that touches
  ``scripts/ci/`` must therefore pass without an extension to build. The first step
  after checkout detects the package, and every later step is conditioned on it.
  Tests that read the extension itself skip while the extension is absent.
- The agreement test drives the real ``nexus-hub settings`` Python command line, so
  the job provisions Python 3.11 with the constrained ``tomlkit`` and ``PyYAML``
  and the profile group hands that interpreter to the test.

The ``nexus-hub-settings`` profile group lives in ``scripts/ci/profiles.py``. It must
reach ``develop`` with (or before) this workflow, or
``test_every_only_group_named_by_a_workflow_exists`` fails.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOW_DIR / "nexus-hub-settings.yml"
EXTENSION_DIR = "extensions/nexus-hub-settings"
REQUIRED_CHECKS = REPO_ROOT / "docs" / "policy" / "required-checks.json"
CONSTRAINTS = "scripts/ci/requirements-py311.txt"
PRESENT = "steps.extension.outputs.present == 'true'"

SIBLING_EXTENSION_WORKFLOWS = (
    WORKFLOW_DIR / "claude-usage-monitor.yml",
    WORKFLOW_DIR / "codex-usage-monitor.yml",
    WORKFLOW_DIR / "copilot-usage-monitor.yml",
    WORKFLOW_DIR / "cursor-usage-monitor.yml",
    WORKFLOW_DIR / "gemini-usage-monitor.yml",
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


def settings_group() -> Any:
    from scripts.ci.profiles import PROFILES

    return next(group for group in PROFILES["full"] if group.name == "nexus-hub-settings")


def test_triggers_are_path_filtered_to_the_extension(workflow: dict[str, Any]) -> None:
    triggers = workflow[ON_KEY]
    assert set(triggers) == {"pull_request"}
    paths = triggers["pull_request"]["paths"]
    assert sorted(paths) == sorted(
        [f"{EXTENSION_DIR}/**", ".github/workflows/nexus-hub-settings.yml", "scripts/ci/**"]
    )
    assert not any(path.startswith("scripts/") and path != "scripts/ci/**" for path in paths)


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


def test_the_first_step_after_checkout_detects_the_extension(
    build_steps: list[dict[str, Any]],
) -> None:
    """The workflow lands before the extension, so a missing package must not fail it."""
    assert build_steps[0]["uses"].startswith("actions/checkout@")
    detect = build_steps[1]
    assert detect["id"] == "extension"
    assert f"{EXTENSION_DIR}/package.json" in detect["run"]
    assert "present=true" in detect["run"] and "present=false" in detect["run"]
    assert "GITHUB_OUTPUT" in detect["run"]


def test_every_step_after_detection_is_conditioned_on_it(
    build_steps: list[dict[str, Any]],
) -> None:
    for step in build_steps[2:]:
        label = step.get("name") or step.get("uses")
        assert PRESENT in str(step.get("if", "")), (
            f"{label} must be conditioned on the detection output, or a pull request "
            "from a base without the extension fails here"
        )


def test_the_always_steps_still_require_the_extension(
    build_steps: list[dict[str, Any]],
) -> None:
    """``if: always()`` alone would run the report steps with nothing to report."""
    for name in ("Publish native profile summary", "Retain native profile reports"):
        condition = str(step_named(build_steps, name)["if"])
        assert condition.startswith("always()") and PRESENT in condition


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


def test_python_is_provisioned_with_the_constrained_test_dependencies(
    build_steps: list[dict[str, Any]],
) -> None:
    setup = next(
        step
        for step in build_steps
        if step.get("uses", "").startswith("actions/setup-python@")
    )
    assert setup["with"]["python-version"] == "3.11"
    # The agreement test needs tomlkit to write the Codex file; the pins match ci.yml.
    install = step_named(build_steps, "Install Python test dependencies")["run"]
    assert f"-c {CONSTRAINTS}" in install
    assert "tomlkit" in install and "PyYAML" in install
    constraints = (REPO_ROOT / CONSTRAINTS).read_text(encoding="utf-8").lower()
    assert "tomlkit==" in constraints and "pyyaml==" in constraints


def test_setup_python_is_pinned_to_the_same_sha_as_ci(
    build_steps: list[dict[str, Any]],
) -> None:
    def pin(steps: list[dict[str, Any]]) -> str:
        return next(
            step["uses"] for step in steps if step.get("uses", "").startswith("actions/setup-python@")
        )

    ci_steps = [step for job in load(WORKFLOW_DIR / "ci.yml")["jobs"].values() for step in job["steps"]]
    assert pin(build_steps) == pin(ci_steps)


def test_the_profile_group_hands_its_interpreter_to_the_agreement_test() -> None:
    coverage = next(command for command in settings_group().commands if "test:coverage" in command.argv)
    assert "NEXUS_HUB_TEST_PYTHON" in coverage.env


def test_job_runs_inside_the_extension_directory() -> None:
    assert all(command.cwd == EXTENSION_DIR for command in settings_group().commands)


def test_gate_covers_clean_install_compile_coverage_and_packaging(
    build_steps: list[dict[str, Any]],
) -> None:
    install = step_named(build_steps, "Install dependencies")["run"].strip()
    assert install == "npm ci --ignore-scripts --prefix " + EXTENSION_DIR
    scripts = "\n".join(step.get("run", "") for step in build_steps)
    assert "--profile full --only nexus-hub-settings" in scripts
    commands = [list(command.argv) for command in settings_group().commands]
    for script in ("compile", "test:coverage", "package", "verify:package"):
        assert any(script in argv for argv in commands), script


def test_the_group_is_explicit_only() -> None:
    """A normal full run must not install Node packages for this extension."""
    assert settings_group().explicit_only is True


@pytest.mark.skipif(
    not (REPO_ROOT / EXTENSION_DIR / "package.json").is_file(),
    reason="the extension reaches this tree after the workflow does",
)
def test_the_extension_scripts_the_gate_calls_exist() -> None:
    scripts = json.loads(
        (REPO_ROOT / EXTENSION_DIR / "package.json").read_text(encoding="utf-8")
    )["scripts"]
    for name in ("compile", "test:coverage", "package", "verify:package"):
        assert name in scripts, f"{EXTENSION_DIR}/package.json has no {name!r} script"


def test_the_path_filtered_check_is_not_required() -> None:
    """A workflow-level ``paths:`` filter is safe only for a non-required check.

    GitHub leaves a required check from an untriggered workflow Pending forever.
    """
    assert "nexus-hub-settings" not in REQUIRED_CHECKS.read_text(encoding="utf-8")


@pytest.mark.parametrize("sibling", SIBLING_EXTENSION_WORKFLOWS, ids=lambda p: p.name)
def test_extension_workflows_share_checkout_and_node_pins(
    workflow: dict[str, Any], sibling: Path
) -> None:
    def pins(path: Path) -> dict[str, str]:
        found: dict[str, str] = {}
        for job in load(path)["jobs"].values():
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


def test_installs_without_scripts_and_watches_itself(workflow: dict[str, Any]) -> None:
    """AR-60 and WN-32: no dependency lifecycle script runs, and an edit to the
    workflow file itself re-runs the workflow."""
    steps = workflow["jobs"]["build-and-test"]["steps"]
    install = step_named(steps, "Install dependencies")
    assert install["run"].strip() == "npm ci --ignore-scripts --prefix " + EXTENSION_DIR
    assert ".github/workflows/nexus-hub-settings.yml" in workflow[ON_KEY]["pull_request"]["paths"]


@pytest.mark.parametrize("sibling", SIBLING_EXTENSION_WORKFLOWS, ids=lambda p: p.name)
def test_extension_workflows_share_the_trigger_and_permission_shape(
    workflow: dict[str, Any], sibling: Path
) -> None:
    theirs = load(sibling)
    assert set(theirs[ON_KEY]) == set(workflow[ON_KEY])
    assert sorted(theirs[ON_KEY]["pull_request"]["branches"]) == sorted(
        workflow[ON_KEY]["pull_request"]["branches"]
    )
    assert theirs["permissions"] == workflow["permissions"]
    assert theirs["concurrency"] == workflow["concurrency"]
