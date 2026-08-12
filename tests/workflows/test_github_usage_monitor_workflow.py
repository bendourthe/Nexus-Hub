"""Policy tests for .github/workflows/github-usage-monitor.yml (v3.15.8 Phase 4.2).

These are semantic assertions about the workflow's cost and safety shape, not a
snapshot of its text. Each one encodes a property that, if it silently
regressed, would either burn action minutes or weaken the extension's gate:

- floating action refs (``@main``, ``@v4`` on a third party) make the build
  non-reproducible and are a supply-chain foothold;
- a wrong or missing ``cache-dependency-path`` silently disables the npm cache
  and re-downloads the dependency tree cold on every run;
- dropping the path filter, or widening it to ordinary feature-branch pushes,
  runs a Node build for changes that cannot affect the extension;
- dropping ``concurrency`` cancellation leaves superseded runs burning minutes;
- dropping the coverage or packaging step turns the gate into a compile check.

The three monitor workflows are compared against each other where they should
agree, so a fix applied to one surface does not quietly skip the others.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOW_DIR / "github-usage-monitor.yml"
EXTENSION_DIR = "extensions/github-usage-monitor"

SIBLING_MONITOR_WORKFLOWS = (
    WORKFLOW_DIR / "claude-usage-monitor.yml",
    WORKFLOW_DIR / "codex-usage-monitor.yml",
)

# PyYAML parses the unquoted YAML 1.1 key `on:` as the boolean True.
ON_KEY = True


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    assert WORKFLOW.is_file(), f"Missing workflow: {WORKFLOW}"
    return load(WORKFLOW)


@pytest.fixture(scope="module")
def steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = workflow["jobs"]
    assert list(jobs) == ["build-and-test"], (
        "the monitor workflow should stay a single focused job; extra jobs add a "
        f"cold runner per run (found {list(jobs)})"
    )
    return jobs["build-and-test"]["steps"]


def step_named(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(f"missing step {name!r}; present: {[s.get('name') for s in steps]}")


def test_triggers_are_path_filtered_to_the_extension(workflow: dict[str, Any]) -> None:
    triggers = workflow[ON_KEY]
    assert set(triggers) == {"push", "pull_request"}, (
        "only push and pull_request should start this workflow; a schedule or "
        "workflow_dispatch trigger would run the Node build with no change to test"
    )
    for event in ("push", "pull_request"):
        paths = triggers[event]["paths"]
        assert f"{EXTENSION_DIR}/**" in paths, (
            f"{event} must be filtered to the extension tree"
        )
        assert ".github/workflows/github-usage-monitor.yml" in paths, (
            f"{event} must re-run when the workflow itself changes, otherwise a "
            "broken edit to this file lands unvalidated"
        )
        assert not any(path.startswith("scripts/") for path in paths), (
            "the installers are covered by ci.yml's installer smoke test; listing "
            "them here rebuilds an unchanged VSIX on every installer edit"
        )


def test_push_trigger_is_limited_to_protected_branches(workflow: dict[str, Any]) -> None:
    push_branches = workflow[ON_KEY]["push"]["branches"]
    assert sorted(push_branches) == ["develop", "main"], (
        "ordinary feature-branch pushes must not trigger the build; the pull "
        f"request into a protected branch is the gate (found {push_branches})"
    )


def test_permissions_are_read_only(workflow: dict[str, Any]) -> None:
    assert workflow["permissions"] == {"contents": "read"}, (
        "this workflow publishes nothing, so its token must stay read-only"
    )


def test_concurrency_cancels_superseded_runs(workflow: dict[str, Any]) -> None:
    concurrency = workflow["concurrency"]
    assert concurrency["cancel-in-progress"] is True
    assert "github.ref" in concurrency["group"], (
        "the concurrency group must be per-ref, otherwise one branch's run "
        "cancels another's"
    )


def test_every_action_is_pinned_to_an_immutable_sha(steps: list[dict[str, Any]]) -> None:
    for step in steps:
        uses = step.get("uses")
        if uses is None:
            continue
        _, _, ref = uses.partition("@")
        assert len(ref) == 40 and all(char in "0123456789abcdef" for char in ref), (
            f"{uses} must be pinned to a full 40-character commit SHA, not a "
            "moving tag or branch"
        )


def test_node_setup_uses_node_22_and_the_exact_lockfile_cache(
    steps: list[dict[str, Any]],
) -> None:
    setup = next(step for step in steps if step.get("uses", "").startswith("actions/setup-node@"))
    assert setup["with"]["node-version"] == "22", (
        "the monitor baseline is Node 22; drifting from it tests a runtime users "
        "do not run"
    )
    assert setup["with"]["cache"] == "npm"
    assert setup["with"]["cache-dependency-path"] == f"{EXTENSION_DIR}/package-lock.json", (
        "a wrong cache-dependency-path silently disables the cache instead of failing"
    )


def test_job_runs_inside_the_extension_directory(workflow: dict[str, Any]) -> None:
    defaults = workflow["jobs"]["build-and-test"]["defaults"]["run"]
    assert defaults["working-directory"] == EXTENSION_DIR


def test_gate_covers_clean_install_compile_coverage_and_packaging(
    steps: list[dict[str, Any]],
) -> None:
    assert step_named(steps, "Install dependencies")["run"].strip() == "npm ci", (
        "npm ci (not npm install) is what makes the CI dependency tree match the "
        "committed lockfile"
    )
    assert "npm run compile" in step_named(steps, "Compile (tsc)")["run"]
    assert "npm run test:coverage" in step_named(
        steps, "Unit tests with V8 coverage (Vitest)"
    )["run"], "plain `npm test` skips the coverage thresholds"
    assert "npm run package" in step_named(steps, "Package VSIX")["run"]
    assert "npm run verify:package" in step_named(steps, "Verify packaged contents")["run"]


def test_step_order_fails_fast(steps: list[dict[str, Any]]) -> None:
    named = [step["name"] for step in steps if "name" in step]
    assert named == [
        "Install dependencies",
        "Compile (tsc)",
        "Unit tests with V8 coverage (Vitest)",
        "Package VSIX",
        "Verify packaged contents",
    ], (
        "cheap gates must run before expensive ones so a compile error does not "
        f"pay for a packaging run (found {named})"
    )


@pytest.mark.parametrize("sibling", SIBLING_MONITOR_WORKFLOWS, ids=lambda p: p.name)
def test_monitor_workflows_share_action_pins(sibling: Path) -> None:
    """A SHA bump applied to one monitor workflow must reach all three.

    Divergent pins mean one extension is built by an older action than its
    siblings, which is exactly the drift the pinning policy exists to prevent.
    """

    def pins(path: Path) -> dict[str, str]:
        data = load(path)
        found: dict[str, str] = {}
        for job in data["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if uses is not None:
                    action, _, ref = uses.partition("@")
                    found[action] = ref
        return found

    ours = pins(WORKFLOW)
    theirs = pins(sibling)
    shared = set(ours) & set(theirs)
    assert shared, f"expected {sibling.name} to share actions with the GitHub monitor"
    for action in sorted(shared):
        assert ours[action] == theirs[action], (
            f"{action} is pinned to {ours[action]} here but {theirs[action]} in "
            f"{sibling.name}; bump both together"
        )


@pytest.mark.parametrize("sibling", SIBLING_MONITOR_WORKFLOWS, ids=lambda p: p.name)
def test_monitor_workflows_all_cancel_superseded_runs(sibling: Path) -> None:
    assert load(sibling)["concurrency"]["cancel-in-progress"] is True, (
        f"{sibling.name} lost its concurrency cancellation"
    )


def test_dependabot_tracks_the_new_extension() -> None:
    """Without an entry, the extension's npm tree is never updated."""
    config = load(REPO_ROOT / ".github" / "dependabot.yml")
    directories = {entry["directory"] for entry in config["updates"]}
    assert f"/{EXTENSION_DIR}" in directories, (
        f"add a monthly npm entry for /{EXTENSION_DIR} to .github/dependabot.yml"
    )
    npm_entry = next(
        entry for entry in config["updates"]
        if entry.get("directory") == f"/{EXTENSION_DIR}"
    )
    ignored = {item["dependency-name"] for item in npm_entry.get("ignore", [])}
    assert "@types/vscode" in ignored, (
        "@types/vscode must stay pinned to engines.vscode; vsce rejects a types bump that exceeds engines (PR #34)"
    )
