"""
Tests for catalog/hooks/dependency-staleness-notice.sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_dependency_staleness_notice.py -v

This is an advisory worker-check hook (v3.10.0 Phase 6, candidate A10). It
is advisory only: it always exits 0 and emits a dependency-audit marker to
stderr when a Write/Edit targets a declared-dependency manifest. Tests invoke
the bash hook via subprocess and assert on (stdout, stderr, exit_code).

If bash is not on PATH (e.g. a Windows runner without Git Bash), all tests skip
rather than fail. Cases that expect a marker also require jq (the hook silently
no-ops without it, mirroring large-file-guard.sh / workflow-phase-notice.sh).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


# -- Module-level locations -------------------------------------------------

_HOOK_FILE = Path(__file__).parent.parent / "dependency-staleness-notice.sh"
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


# -- Helpers ----------------------------------------------------------------


def _make_payload(file_path: str, tool_name: str = "Edit") -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, "content": "irrelevant"},
    }


def _run_hook(payload: dict[str, Any], env_overrides: dict[str, str] | None = None) -> tuple[str, str, int]:
    """Invoke the hook via bash with the given JSON payload."""
    env = os.environ.copy()
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


# -- Tests ------------------------------------------------------------------


@_REQUIRES_JQ
@pytest.mark.parametrize(
    ("manifest", "hint_fragment"),
    [
        ("package.json", "npm audit"),
        ("requirements.txt", "pip-audit"),
        ("pyproject.toml", "pip-audit"),
        ("go.mod", "govulncheck"),
        ("Cargo.toml", "cargo audit"),
        ("Gemfile", "bundle audit"),
        ("composer.json", "composer audit"),
        ("pom.xml", "OWASP"),
        ("app.csproj", "dotnet list package"),
    ],
)
def test_flags_manifest_with_ecosystem_hint(manifest: str, hint_fragment: str) -> None:
    """Each recognized manifest emits a marker carrying its ecosystem audit hint."""
    stdout, stderr, code = _run_hook(_make_payload(manifest))

    assert code == 0, f"advisory hook must never block (got exit {code}, stderr={stderr})"
    assert "dependency-staleness-notice" in stderr
    assert hint_fragment in stderr


@_REQUIRES_JQ
def test_silent_for_non_manifest() -> None:
    """An ordinary source file is silent (and never blocks)."""
    stdout, stderr, code = _run_hook(_make_payload("src/main.py"))

    assert code == 0
    assert stderr == "", f"expected silent output, got: {stderr}"


@_REQUIRES_JQ
def test_silent_for_lockfile() -> None:
    """A generated lockfile is not treated as a declared-dependency manifest."""
    stdout, stderr, code = _run_hook(_make_payload("package-lock.json"))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_inside_node_modules() -> None:
    """A manifest inside node_modules belongs to a dependency, not the project."""
    stdout, stderr, code = _run_hook(_make_payload("node_modules/dep/package.json"))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_windows_path_separator_is_normalized() -> None:
    """Backslash separators are normalized before pattern matching."""
    stdout, stderr, code = _run_hook(_make_payload("services\\api\\go.mod"))

    assert code == 0
    assert "dependency-staleness-notice" in stderr
    assert "services/api/go.mod" in stderr


def test_disabled_via_env() -> None:
    """NEXUS_DISABLED_HOOKS containing dependency-staleness-notice short-circuits."""
    stdout, stderr, code = _run_hook(
        _make_payload("package.json"),
        env_overrides={"NEXUS_DISABLED_HOOKS": "dependency-staleness-notice"},
    )

    assert code == 0
    assert stderr == ""


def test_minimal_profile_short_circuits() -> None:
    """NEXUS_HOOK_PROFILE=minimal skips this advisory hook."""
    stdout, stderr, code = _run_hook(
        _make_payload("package.json"),
        env_overrides={"NEXUS_HOOK_PROFILE": "minimal"},
    )

    assert code == 0
    assert stderr == ""
