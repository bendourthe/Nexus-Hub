"""
Tests for catalog/hooks/workflow-phase-notice.sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_workflow_phase_notice.py -v

This is the runnable example for candidate N1a (workflow-phase hook recipe).
The hook is advisory only: it always exits 0 and emits a phase-boundary marker
to stderr when a Write/Edit targets a Nexus-Hub workflow artifact (a plan file
under docs/**/plans/, a spec.md, a tasks.md, or CHANGELOG.md). Tests invoke the
bash hook via subprocess and assert on (stdout, stderr, exit_code).

If bash is not on PATH (e.g. a Windows runner without Git Bash), all tests skip
rather than fail. Cases that expect a marker also require jq (the hook silently
no-ops without it, mirroring large-file-guard.sh / old-version-docs-guard.sh).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


# ── Module-level locations ─────────────────────────────────────────────────

_HOOK_FILE = Path(__file__).parent.parent / "workflow-phase-notice.sh"
_BASH = shutil.which("bash")
_JQ = shutil.which("jq")

_REQUIRES_JQ = pytest.mark.skipif(
    _JQ is None,
    reason="jq not on PATH; hook silently no-ops without it",
)

pytestmark = pytest.mark.skipif(
    _BASH is None,
    reason="bash not on PATH; skipping shell hook tests",
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_payload(file_path: str, tool_name: str = "Write") -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, "content": "irrelevant"},
    }


def _run_hook(payload: dict[str, Any], env_overrides: dict[str, str] | None = None) -> tuple[str, str, int]:
    """Invoke the hook via bash with the given JSON payload."""
    env = os.environ.copy()
    # Strip inherited profile overrides FIRST so the environment is deterministic.
    env.pop("NEXUS_HOOK_PROFILE", None)
    env.pop("NEXUS_DISABLED_HOOKS", None)
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        [_BASH, str(_HOOK_FILE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


# ── Tests ──────────────────────────────────────────────────────────────────


@_REQUIRES_JQ
def test_marks_plan_artifact(tmp_path: Path) -> None:
    """A Write to docs/releases/v9/v9.9/plans/foo.md emits a plan-phase marker."""
    stdout, stderr, code = _run_hook(_make_payload("docs/releases/v9/v9.9/plans/adoption-foo.md"))

    assert code == 0, f"advisory hook must never block (got exit {code}, stderr={stderr})"
    assert "workflow-phase-notice" in stderr
    assert "plan-phase" in stderr
    assert "docs/releases/v9/v9.9/plans/adoption-foo.md" in stderr


@_REQUIRES_JQ
def test_marks_spec_artifact() -> None:
    """A Write to a spec.md emits a spec-phase marker."""
    stdout, stderr, code = _run_hook(_make_payload("specs/feature-x/spec.md"))

    assert code == 0
    assert "spec-phase" in stderr


@_REQUIRES_JQ
def test_marks_tasks_artifact() -> None:
    """A Write to a tasks.md emits a tasks-phase marker."""
    stdout, stderr, code = _run_hook(_make_payload("specs/feature-x/tasks.md"))

    assert code == 0
    assert "tasks-phase" in stderr


@_REQUIRES_JQ
def test_marks_release_artifact() -> None:
    """A Write to CHANGELOG.md emits a release-phase marker."""
    stdout, stderr, code = _run_hook(_make_payload("CHANGELOG.md"))

    assert code == 0
    assert "release-phase" in stderr


@_REQUIRES_JQ
def test_silent_for_non_workflow_artifact() -> None:
    """A Write to ordinary source is silent (and never blocks)."""
    stdout, stderr, code = _run_hook(_make_payload("src/main.py"))

    assert code == 0
    assert stderr == "", f"expected silent output, got: {stderr}"


@_REQUIRES_JQ
def test_silent_for_bare_plan_md_outside_plans_dir() -> None:
    """A bare plan.md NOT under a plans/ directory is not treated as a plan artifact."""
    stdout, stderr, code = _run_hook(_make_payload("notes/plan.md"))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_windows_path_separator_is_normalized() -> None:
    """Backslash separators are normalized before pattern matching."""
    stdout, stderr, code = _run_hook(_make_payload("docs\\releases\\v9\\v9.9\\plans\\foo.md"))

    assert code == 0
    assert "plan-phase" in stderr
    assert "docs/releases/v9/v9.9/plans/foo.md" in stderr


def test_disabled_via_env() -> None:
    """NEXUS_DISABLED_HOOKS containing workflow-phase-notice short-circuits silently."""
    stdout, stderr, code = _run_hook(
        _make_payload("CHANGELOG.md"),
        env_overrides={"NEXUS_DISABLED_HOOKS": "workflow-phase-notice"},
    )

    assert code == 0
    assert stderr == ""


def test_minimal_profile_short_circuits() -> None:
    """NEXUS_HOOK_PROFILE=minimal skips this advisory hook."""
    stdout, stderr, code = _run_hook(
        _make_payload("CHANGELOG.md"),
        env_overrides={"NEXUS_HOOK_PROFILE": "minimal"},
    )

    assert code == 0
    assert stderr == ""
