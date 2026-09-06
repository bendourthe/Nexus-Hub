"""Tests for the `ci-required` aggregate gate in .github/workflows/ci.yml.

v3.17.6 sub-task 2.2 collapsed ten required status checks into three, because
GitHub evaluates a job-level `if:` BEFORE matrix expansion: a skipped matrix job
publishes one check run named after the bare job, so the per-leg contexts
(`installer-smoke (ubuntu-latest)` and friends) never exist on a docs-only PR and
sit Pending forever. The docs-only proof PR reached BLOCKED, which is how this
was found.

That makes `ci-required` the single thing standing between a broken build and a
green merge, so it is tested directly rather than trusted. Three properties
matter, and every one of them fails SILENTLY if wrong:

1. **Coverage.** `needs` must list every other job. A job missing from it can
   fail without blocking anything.
2. **Wiring.** Every needed job must have a matching `R_<job>` env var. A job in
   `needs` with no env var is invisible to the verdict loop, so it could fail
   while the aggregate still reported success.
3. **Verdict.** `skipped` passes (the detector doing its job) while `failure`,
   `cancelled`, an unrecognised value, and an empty value all fail.

The verdict tests execute the shipped `run:` script through its real interface
rather than reimplementing its logic, so they test the thing that ships.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Explicit sys.path insert, matching the idiom already used in this directory:
# a bare `from conftest import ...` would resolve to tests/conftest.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bash_helper import BASH

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
MANIFEST = REPO_ROOT / "docs" / "policy" / "required-checks.json"

GATE_JOB = "ci-required"

# BASH is resolved empirically by conftest rather than by shutil.which: the
# Windows System32 WSL launcher stub precedes Git Bash on PATH and exits 1.
needs_bash = pytest.mark.skipif(
    BASH is None, reason="the aggregate gate is a bash script"
)


def workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def gate_step() -> dict:
    for step in workflow()["jobs"][GATE_JOB]["steps"]:
        if step.get("run"):
            return step
    raise AssertionError(f"no run: step found in the {GATE_JOB} job")


def base_env() -> dict[str, str]:
    """A minimal environment.

    The parent environment is deliberately not inherited: a stray R_* variable on
    the developer's machine would otherwise join the verdict loop and change the
    outcome.
    """
    return {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }


def run_gate(
    results: dict[str, str] | None, tmp_path: Path
) -> subprocess.CompletedProcess[str]:
    """Execute the shipped script, passing results the way the workflow does."""
    script = tmp_path / "gate.sh"
    script.write_text(gate_step()["run"], encoding="utf-8", newline="\n")
    env = base_env()
    for job, result in (results or {}).items():
        env["R_" + job.replace("-", "_")] = result
    return subprocess.run(
        [BASH, str(script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=env,
    )


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------


def test_gate_job_always_runs() -> None:
    """`if: always()` is load-bearing, not decorative.

    Without it, a FAILED dependency would skip this job, and a skipped required
    check reports Success -- so the one job guarding the merge would wave through
    exactly the case it exists to catch.
    """
    condition = str(workflow()["jobs"][GATE_JOB].get("if", "")).strip()
    assert "always()" in condition, (
        f"{GATE_JOB} must use `if: always()`; without it a failed dependency "
        "skips this job and a skipped required check reports Success"
    )


def test_gate_needs_every_other_job() -> None:
    """A job absent from `needs` can fail without blocking a merge."""
    jobs = workflow()["jobs"]
    others = {name for name in jobs if name != GATE_JOB}
    declared = set(jobs[GATE_JOB]["needs"])
    assert not others - declared, (
        f"{GATE_JOB} does not depend on {sorted(others - declared)}. Those jobs "
        "could fail without blocking a merge. Add them to `needs`."
    )
    assert not declared - others, (
        f"{GATE_JOB} depends on nonexistent job(s) {sorted(declared - others)}"
    )


def test_every_needed_job_has_a_result_env_var() -> None:
    """The verdict loop can only inspect jobs wired into `env:`.

    A job in `needs` with no matching env var is invisible to the loop: it could
    fail while the aggregate reported success. The `needs` coverage test above
    does not close this hole, so it is asserted separately.
    """
    job = workflow()["jobs"][GATE_JOB]
    mapped = {key[len("R_") :].replace("_", "-") for key in gate_step()["env"]}
    declared = set(job["needs"])
    assert mapped == declared, (
        "the `env:` block and `needs:` list disagree; a missing env var lets a "
        "job fail invisibly. "
        f"in needs only: {sorted(declared - mapped)}; "
        f"in env only: {sorted(mapped - declared)}"
    )


def test_manifest_requires_the_gate_and_no_matrix_leg() -> None:
    """The manifest must name the aggregate, never a per-leg matrix context.

    A `job (leg)` context is unsatisfiable whenever that job is skipped, which is
    the defect this sub-task fixes. Requiring one again would reintroduce it.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for branch, cfg in manifest["branches"].items():
        contexts = cfg["contexts"]
        assert GATE_JOB in contexts, f"{branch} does not require {GATE_JOB}"
        legged = [c for c in contexts if c.endswith(")") and " (" in c]
        assert not legged, (
            f"{branch} requires matrix-leg context(s) {legged}. A skipped matrix "
            "job never publishes its per-leg names, so these can sit Pending "
            "forever. Require the aggregate instead."
        )


# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------


@needs_bash
def test_all_success_passes(tmp_path: Path) -> None:
    result = run_gate({"validate": "success", "tests": "success"}, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout


@needs_bash
def test_skipped_is_acceptable(tmp_path: Path) -> None:
    """A skipped job is the detector working, not a problem."""
    result = run_gate(
        {
            "changes": "success",
            "validate": "success",
            "bootstrap": "skipped",
            "tests": "skipped",
            "installer-smoke": "skipped",
        },
        tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@needs_bash
@pytest.mark.parametrize("value", ["failure", "cancelled"])
def test_failure_and_cancelled_are_fatal(tmp_path: Path, value: str) -> None:
    result = run_gate({"validate": "success", "tests": value}, tmp_path)
    assert result.returncode == 1, result.stdout
    assert f"tests={value}" in result.stdout


@needs_bash
def test_unrecognised_result_is_fatal(tmp_path: Path) -> None:
    """A conclusion GitHub has not used before must not pass by default.

    The verdict is an allowlist (success or skipped) rather than a denylist on
    failure/cancelled, so a new value fails closed instead of slipping through.
    """
    result = run_gate({"validate": "success", "tests": "neutral"}, tmp_path)
    assert result.returncode == 1, result.stdout


@needs_bash
def test_empty_result_value_is_fatal(tmp_path: Path) -> None:
    """An empty result means the expression produced nothing; not a success."""
    result = run_gate({"validate": "success", "tests": ""}, tmp_path)
    assert result.returncode == 1, result.stdout


@needs_bash
def test_one_failure_among_many_successes_is_caught(tmp_path: Path) -> None:
    result = run_gate(
        {
            "changes": "success",
            "validate": "success",
            "shellcheck": "success",
            "bootstrap": "skipped",
            "tests": "success",
            "install-smoke": "success",
            "installer-smoke": "failure",
        },
        tmp_path,
    )
    assert result.returncode == 1, result.stdout
    assert "installer-smoke=failure" in result.stdout


@needs_bash
def test_no_results_at_all_fails_closed(tmp_path: Path) -> None:
    """An empty result set must fail rather than report a green aggregate.

    This is the fail-open shape the rest of v3.17.6 exists to prevent: a guard
    that asserted nothing and said OK anyway. If the env wiring is ever dropped,
    the loop has nothing to inspect and must refuse.
    """
    result = run_gate(None, tmp_path)
    assert result.returncode == 1, result.stdout
    assert "OK:" not in result.stdout
