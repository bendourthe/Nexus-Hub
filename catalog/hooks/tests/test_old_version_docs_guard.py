"""
Tests for catalog/hooks/old-version-docs-guard.sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_old_version_docs_guard.py -v

Tests invoke the bash hook via subprocess against a synthetic docs/ tree in a
tmp directory. Each case asserts on (stdout, stderr, exit_code). The hook is
designed to be non-blocking by default and to upgrade to a hard block only
when DEVAI_OLD_DOCS_GUARD=block.

If bash is not on PATH (e.g. a Windows runner without Git Bash), all tests
skip rather than fail.
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

_HOOK_FILE = Path(__file__).parent.parent / "old-version-docs-guard.sh"
_BASH = shutil.which("bash")
_JQ = shutil.which("jq")

# The hook follows the existing Nexus-Hub pattern of relying on jq for stdin
# JSON parsing. Without jq, the hook silently exits 0 (consistent with
# large-file-guard.sh and secret-scan.sh). Cases that expect a warning are
# only meaningful when jq is available; skip them otherwise.
_REQUIRES_JQ = pytest.mark.skipif(
    _JQ is None,
    reason="jq not on PATH; hook silently no-ops without it",
)

pytestmark = pytest.mark.skipif(
    _BASH is None,
    reason="bash not on PATH; skipping shell hook tests",
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_payload(file_path: str) -> dict[str, Any]:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "irrelevant"},
    }


def _run_hook(payload: dict[str, Any], cwd: Path, env_overrides: dict[str, str] | None = None) -> tuple[str, str, int]:
    """Invoke the hook via bash with the given JSON payload and working dir."""
    env = os.environ.copy()
    # Strip any inherited profile overrides FIRST so the test environment is deterministic.
    # Apply env_overrides AFTER the pop so test-supplied vars are not silently removed.
    env.pop("DEVAI_HOOK_PROFILE", None)
    env.pop("DEVAI_DISABLED_HOOKS", None)
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        [_BASH, str(_HOOK_FILE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def _make_docs_tree(root: Path, versions: list[str]) -> None:
    """Create docs/v<version>/ subdirectories for each entry in versions."""
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for v in versions:
        (docs / f"v{v}").mkdir(parents=True, exist_ok=True)


# ── Tests ──────────────────────────────────────────────────────────────────


@_REQUIRES_JQ
def test_warns_when_writing_to_old_version_dir(tmp_path: Path) -> None:
    """Writing to docs/v0.8.1/foo.md with v1.0.0 active emits a stderr warning."""
    _make_docs_tree(tmp_path, ["0.8.1", "0.9.7", "1.0.0"])
    payload = _make_payload("docs/v0.8.1/foo.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0, f"hook should not block by default (got exit {code}, stderr={stderr})"
    assert "old-version-docs-guard" in stderr
    assert "docs/v0.8.1" in stderr
    assert "v1.0.0" in stderr
    assert "/refactor-docs" in stderr


def test_silent_when_writing_to_active_version(tmp_path: Path) -> None:
    """Writing to docs/v1.0.0/foo.md when v1.0.0 is the active version is silent."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs/v1.0.0/plans/new-plan.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0
    assert stderr == "", f"expected silent output, got: {stderr}"


@_REQUIRES_JQ
def test_blocks_when_env_set_to_block(tmp_path: Path) -> None:
    """DEVAI_OLD_DOCS_GUARD=block upgrades the warning to a hard block."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs/v0.8.1/foo.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path, env_overrides={"DEVAI_OLD_DOCS_GUARD": "block"})

    assert code == 1, f"hook should block (got exit {code})"
    assert "Blocked by DEVAI_OLD_DOCS_GUARD=block" in stderr


def test_silent_for_non_docs_path(tmp_path: Path) -> None:
    """Writing to a file outside docs/ is always silent."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("src/main.py")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0
    assert stderr == ""


def test_silent_for_top_level_docs_file(tmp_path: Path) -> None:
    """docs/DEVLOG.md (no version segment) is always silent."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs/DEVLOG.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0
    assert stderr == ""


def test_silent_when_no_version_dirs_exist(tmp_path: Path) -> None:
    """If docs/v*/ does not exist, the hook is a no-op even for docs paths."""
    (tmp_path / "docs").mkdir()
    payload = _make_payload("docs/v0.8.1/foo.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0
    assert stderr == ""


def test_disabled_via_env(tmp_path: Path) -> None:
    """DEVAI_DISABLED_HOOKS containing old-version-docs-guard short-circuits silently."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs/v0.8.1/foo.md")

    stdout, stderr, code = _run_hook(
        payload,
        cwd=tmp_path,
        env_overrides={"DEVAI_DISABLED_HOOKS": "old-version-docs-guard"},
    )

    assert code == 0
    assert stderr == ""


def test_minimal_profile_short_circuits(tmp_path: Path) -> None:
    """DEVAI_HOOK_PROFILE=minimal skips advisory hooks like this one."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs/v0.8.1/foo.md")

    stdout, stderr, code = _run_hook(
        payload,
        cwd=tmp_path,
        env_overrides={"DEVAI_HOOK_PROFILE": "minimal"},
    )

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_windows_path_separator_is_normalized(tmp_path: Path) -> None:
    """Backslash separators in file_path are normalized before pattern matching."""
    _make_docs_tree(tmp_path, ["0.8.1", "1.0.0"])
    payload = _make_payload("docs\\v0.8.1\\foo.md")

    stdout, stderr, code = _run_hook(payload, cwd=tmp_path)

    assert code == 0
    assert "old-version-docs-guard" in stderr
    assert "docs/v0.8.1" in stderr
