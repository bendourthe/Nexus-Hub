"""Policy tests for .github/workflows/cursor-usage-monitor.yml (v3.15.9 Phase 6).

Mirrors the GitHub monitor workflow policy tests, with two Phase 6 additions:

- the workflow may include a second ``e2e-cursor-profile`` job that degrades
  honestly when the Cursor CLI is absent on the hosted runner;
- Dependabot must track the new extension npm tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOW_DIR / "cursor-usage-monitor.yml"
EXTENSION_DIR = "extensions/cursor-usage-monitor"
LIVE_SMOKE = (
    REPO_ROOT / "docs" / "v3" / "v3.15" / "development" / "cursor-usage-live-smoke.md"
)

SIBLING_MONITOR_WORKFLOWS = (
    WORKFLOW_DIR / "claude-usage-monitor.yml",
    WORKFLOW_DIR / "codex-usage-monitor.yml",
    WORKFLOW_DIR / "github-usage-monitor.yml",
)

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
    assert "build-and-test" in jobs, "missing build-and-test job"
    assert "e2e-cursor-profile" in jobs, "missing e2e-cursor-profile job"
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
    assert set(triggers) == {"push", "pull_request"}
    for event in ("push", "pull_request"):
        paths = triggers[event]["paths"]
        assert f"{EXTENSION_DIR}/**" in paths
        assert ".github/workflows/cursor-usage-monitor.yml" in paths
        assert not any(path.startswith("scripts/") for path in paths), (
            "installers are covered by ci.yml's installer smoke test"
        )


def test_push_trigger_is_limited_to_protected_branches(
    workflow: dict[str, Any],
) -> None:
    assert sorted(workflow[ON_KEY]["push"]["branches"]) == ["develop", "main"]


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
        in step_named(build_steps, "Unit tests with V8 coverage (Vitest)")["run"]
    )
    assert "npm run package" in step_named(build_steps, "Package VSIX")["run"]
    assert (
        "npm run verify:package"
        in step_named(build_steps, "Verify packaged contents")["run"]
    )


def test_e2e_job_degrades_when_cursor_cli_is_absent(workflow: dict[str, Any]) -> None:
    e2e = workflow["jobs"]["e2e-cursor-profile"]
    assert e2e["needs"] == "build-and-test" or e2e["needs"] == ["build-and-test"]
    install_step = step_named(
        e2e["steps"], "Install into throwaway Cursor profile or skip-with-note"
    )
    script = install_step["run"]
    assert "command -v cursor" in script
    assert "cursor-usage-live-smoke.md" in script
    assert "--user-data-dir" in script
    assert "nexus-hub.cursor-usage-monitor" in script
    assert "exit 0" in script, (
        "missing Cursor CLI must skip-with-note, not fail the job"
    )


def test_live_smoke_checklist_exists_for_ci_degrade() -> None:
    assert LIVE_SMOKE.is_file(), (
        "CI E2E skip-with-note requires docs/v3/v3.15/development/cursor-usage-live-smoke.md"
    )
    text = LIVE_SMOKE.read_text(encoding="utf-8")
    assert "Cursor Models" in text
    assert "Other Models" in text
    assert "on-demand" in text.lower() or "On-demand" in text
    assert "claude-usage-monitor" in text
    assert "nexus-hub.cursor-usage-monitor" in text


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


def test_dependabot_tracks_the_new_extension() -> None:
    config = load(REPO_ROOT / ".github" / "dependabot.yml")
    directories = {entry["directory"] for entry in config["updates"]}
    assert f"/{EXTENSION_DIR}" in directories
