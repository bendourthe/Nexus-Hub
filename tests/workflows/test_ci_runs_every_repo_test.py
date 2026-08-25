"""CI must run every test in the repo-level `tests/` tree (v4.0.0).

The failure this prevents is fail-open and silent. `ci.yml` used to enumerate
test directories by name (`pytest tests/integrations tests/installer`,
`pytest tests/validators`, and so on), which meant a test that existed, passed
locally, and was committed could still never run in CI. Two real instances:

- `tests/plans/` shipped in v3.15.8 and was invisible until a later step added
  it, which the workflow's own comment recorded at the time.
- `tests/test_removed_autonomy_surface.py` sits at the root of `tests/` and was
  never covered by ANY enumerated step, because every step named a subdirectory.

A missing test does not fail; it just quietly stops guarding. That is the same
fail-open shape as the required-check antipattern in
`docs/decisions/implemented/tooling/2026-08-19-required-checks-must-be-unconditionally-produced.md`,
and it deserves the same treatment: assert the property, do not trust the habit.

This test asserts coverage of the tree, not the exact wording of a step, so
reorganizing CI is allowed as long as every test still runs.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
TESTS = REPO_ROOT / "tests"

# Directories under tests/ that hold no tests and are not expected to be run.
NON_TEST_DIRS = {"__pycache__", "fixtures"}


def _pytest_targets() -> set[str]:
    """Every path argument passed to a `pytest` invocation anywhere in ci.yml."""
    text = CI.read_text(encoding="utf-8")
    targets: set[str] = set()
    for line in text.splitlines():
        if "pytest" not in line:
            continue
        # Strip everything up to and including the pytest token, then take the
        # bare (non-flag) arguments that look like paths.
        tail = line.split("pytest", 1)[1]
        for token in tail.split():
            if token.startswith("-"):
                continue
            if not re.fullmatch(r"[\w./*\[\]-]+", token):
                continue
            if "/" in token or token == "tests":
                targets.add(token.rstrip(","))
    return targets


def _covers(target: str, path: Path) -> bool:
    """True when running `pytest <target>` would collect `path`."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    return rel == target or rel.startswith(target.rstrip("/") + "/")


def test_ci_yml_exists() -> None:
    assert CI.is_file(), "ci.yml is missing; this guard has nothing to check"


def test_every_repo_test_file_is_collected_by_ci() -> None:
    targets = _pytest_targets()
    assert targets, "no pytest invocations found in ci.yml"

    test_files = [
        p
        for p in TESTS.rglob("test_*.py")
        if not any(part in NON_TEST_DIRS for part in p.relative_to(TESTS).parts)
    ]
    assert test_files, "fixture precondition: tests/ contains no test files"

    uncovered = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in test_files
        if not any(_covers(t, p) for t in targets)
    ]
    assert not uncovered, (
        "these repo tests exist but no ci.yml pytest step would collect them, so "
        "they pass locally and guard nothing in CI: "
        f"{sorted(uncovered)}. Fix ci.yml (running `pytest tests` covers the "
        "whole tree), not this test."
    )


def test_every_test_directory_is_collected_by_ci() -> None:
    """Directory-level form of the same property, so an empty-but-new dir fails early."""
    targets = _pytest_targets()
    dirs = [
        d
        for d in TESTS.iterdir()
        if d.is_dir() and d.name not in NON_TEST_DIRS
    ]
    uncovered = [
        d.relative_to(REPO_ROOT).as_posix()
        for d in dirs
        if not any(_covers(t, d) or _covers(t, d / "x") for t in targets)
    ]
    assert not uncovered, f"test directories not reachable from any CI pytest step: {sorted(uncovered)}"


def test_catalog_hook_tests_are_still_run() -> None:
    """The hooks suite lives outside tests/ and must not be lost in a CI edit."""
    targets = _pytest_targets()
    assert any(t.startswith("catalog/hooks/tests") for t in targets), (
        "no ci.yml step runs catalog/hooks/tests/"
    )
