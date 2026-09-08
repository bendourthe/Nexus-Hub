"""
Tests for catalog/hooks/lint-autofix.sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_lint_autofix.py -v

The lint-autofix hook is OPT-IN and file-mutating: on a `git commit` Bash tool
call it runs available formatters' native --fix on the STAGED files that have no
unstaged changes, then re-stages them. It is inert unless
NEXUS_ENABLE_LINT_AUTOFIX=1, honors NEXUS_DISABLED_HOOKS / NEXUS_HOOK_PROFILE,
never touches a file with unstaged changes, and always exits 0.

Tests invoke the bash hook via subprocess against a throwaway git repo and
assert on the STAGED blob content plus (stderr, exit_code). If bash or git is
not on PATH the tests skip. The formatting / skip cases additionally require
ruff (the formatter they exercise). The hook extracts the command with jq when
present and a grep/sed fallback otherwise, so the tests do not require jq.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


# -- Module-level locations --------------------------------------------------

_HOOK_FILE = Path(__file__).parent.parent / "lint-autofix.sh"
_BASH = shutil.which("bash")
_GIT = shutil.which("git")
_RUFF = shutil.which("ruff")

_REQUIRES_RUFF = pytest.mark.skipif(
    _RUFF is None,
    reason="ruff not on PATH; cannot exercise the Python formatter path",
)

pytestmark = pytest.mark.skipif(
    _BASH is None or _GIT is None,
    reason="bash or git not on PATH; skipping shell hook tests",
)

_UNFORMATTED_PY = "import os\nx=1\n"  # os is unused (F401), x=1 is unformatted


# -- Helpers -----------------------------------------------------------------


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run([_GIT, "init", "-q"], cwd=repo, check=True)
    subprocess.run([_GIT, "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run([_GIT, "config", "user.name", "Test"], cwd=repo, check=True)
    return repo


def _stage(repo: Path, name: str, content: str) -> Path:
    p = repo / name
    p.write_text(content, encoding="utf-8")
    subprocess.run([_GIT, "add", name], cwd=repo, check=True)
    return p


def _staged_content(repo: Path, name: str) -> str:
    result = subprocess.run(
        [_GIT, "show", f":{name}"], cwd=repo, capture_output=True, text=True
    )
    return result.stdout


def _run_hook(
    repo: Path, command: str, env_overrides: dict[str, str] | None = None
) -> tuple[str, str, int]:
    env = os.environ.copy()
    # Deterministic base: strip inherited controls.
    for key in ("NEXUS_HOOK_PROFILE", "NEXUS_DISABLED_HOOKS", "NEXUS_ENABLE_LINT_AUTOFIX"):
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)

    payload: dict[str, Any] = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        [_BASH, str(_HOOK_FILE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


# -- Tests -------------------------------------------------------------------


def test_inert_by_default(tmp_path: Path) -> None:
    """Without NEXUS_ENABLE_LINT_AUTOFIX the hook does nothing (opt-in gate)."""
    repo = _init_repo(tmp_path)
    _stage(repo, "m.py", _UNFORMATTED_PY)

    _stdout, _stderr, code = _run_hook(repo, "git commit -m x")

    assert code == 0
    assert _staged_content(repo, "m.py") == _UNFORMATTED_PY  # untouched


def test_disabled_via_env(tmp_path: Path) -> None:
    """Enabled but NEXUS_DISABLED_HOOKS=lint-autofix short-circuits before any work."""
    repo = _init_repo(tmp_path)
    _stage(repo, "m.py", _UNFORMATTED_PY)

    _stdout, _stderr, code = _run_hook(
        repo,
        "git commit -m x",
        {"NEXUS_ENABLE_LINT_AUTOFIX": "1", "NEXUS_DISABLED_HOOKS": "lint-autofix"},
    )

    assert code == 0
    assert _staged_content(repo, "m.py") == _UNFORMATTED_PY


def test_minimal_profile_short_circuits(tmp_path: Path) -> None:
    """Enabled but NEXUS_HOOK_PROFILE=minimal short-circuits."""
    repo = _init_repo(tmp_path)
    _stage(repo, "m.py", _UNFORMATTED_PY)

    _stdout, _stderr, code = _run_hook(
        repo,
        "git commit -m x",
        {"NEXUS_ENABLE_LINT_AUTOFIX": "1", "NEXUS_HOOK_PROFILE": "minimal"},
    )

    assert code == 0
    assert _staged_content(repo, "m.py") == _UNFORMATTED_PY


def test_failopen_on_garbage_stdin(tmp_path: Path) -> None:
    """Enabled, but non-JSON stdin must never block (fail-open, exit 0)."""
    repo = _init_repo(tmp_path)
    env = os.environ.copy()
    for key in ("NEXUS_HOOK_PROFILE", "NEXUS_DISABLED_HOOKS"):
        env.pop(key, None)
    env["NEXUS_ENABLE_LINT_AUTOFIX"] = "1"

    result = subprocess.run(
        [_BASH, str(_HOOK_FILE)],
        input="this is not json",
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )

    assert result.returncode == 0


def test_noop_for_non_commit_command(tmp_path: Path) -> None:
    """Enabled, but a non-`git commit` command leaves staged content untouched."""
    repo = _init_repo(tmp_path)
    _stage(repo, "m.py", _UNFORMATTED_PY)

    _stdout, _stderr, code = _run_hook(
        repo, "ls -la", {"NEXUS_ENABLE_LINT_AUTOFIX": "1"}
    )

    assert code == 0
    assert _staged_content(repo, "m.py") == _UNFORMATTED_PY


@_REQUIRES_RUFF
def test_formats_and_restages_staged_py(tmp_path: Path) -> None:
    """Enabled + `git commit` + a staged, unstaged-clean .py file: reformat + re-stage."""
    repo = _init_repo(tmp_path)
    _stage(repo, "m.py", _UNFORMATTED_PY)

    _stdout, _stderr, code = _run_hook(
        repo, "git commit -m x", {"NEXUS_ENABLE_LINT_AUTOFIX": "1"}
    )

    assert code == 0
    staged = _staged_content(repo, "m.py")
    assert "import os" not in staged  # unused import removed by ruff check --fix
    assert "x = 1" in staged  # reformatted by ruff format


@_REQUIRES_RUFF
def test_skips_file_with_unstaged_changes(tmp_path: Path) -> None:
    """A staged file that ALSO has unstaged changes is skipped (never re-staged)."""
    repo = _init_repo(tmp_path)
    path = _stage(repo, "m.py", _UNFORMATTED_PY)
    # Introduce an unstaged change on top of the staged content.
    path.write_text(_UNFORMATTED_PY + "y=2\n", encoding="utf-8")

    _stdout, stderr, code = _run_hook(
        repo, "git commit -m x", {"NEXUS_ENABLE_LINT_AUTOFIX": "1"}
    )

    assert code == 0
    # Staged blob is the original unformatted content - the hook did not touch it.
    assert _staged_content(repo, "m.py") == _UNFORMATTED_PY
    assert "skipped" in stderr
