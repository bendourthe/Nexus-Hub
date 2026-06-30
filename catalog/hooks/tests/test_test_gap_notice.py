"""
Tests for catalog/hooks/test-gap-notice.sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_test_gap_notice.py -v

This is an advisory worker-check hook (v3.10.0 Phase 6, candidate A10). It
is advisory only: it always exits 0 and emits a coverage-gap marker to stderr
when a Write/Edit targets a (non-test) source file with no discoverable
companion test. Tests invoke the bash hook via subprocess and assert on
(stdout, stderr, exit_code).

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

_HOOK_FILE = Path(__file__).parent.parent / "test-gap-notice.sh"
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


def _make_payload(file_path: str, tool_name: str = "Write") -> dict[str, Any]:
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
def test_flags_source_without_companion_test(tmp_path: Path) -> None:
    """A source file with no nearby test emits a coverage-gap marker."""
    src = tmp_path / "src" / "widget.py"
    src.parent.mkdir(parents=True)
    src.write_text("def widget(): ...\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0, f"advisory hook must never block (got exit {code}, stderr={stderr})"
    assert "test-gap-notice" in stderr
    assert str(src).replace("\\", "/") in stderr


@_REQUIRES_JQ
def test_silent_when_sibling_test_exists(tmp_path: Path) -> None:
    """A source file with a same-dir test_<stem>.py companion is silent."""
    src = tmp_path / "src" / "widget.py"
    src.parent.mkdir(parents=True)
    src.write_text("def widget(): ...\n")
    (src.parent / "test_widget.py").write_text("def test_widget(): ...\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0
    assert stderr == "", f"expected silent output, got: {stderr}"


@_REQUIRES_JQ
def test_silent_when_test_in_tests_dir(tmp_path: Path) -> None:
    """A companion test under an adjacent tests/ directory is found."""
    src = tmp_path / "pkg" / "service.ts"
    src.parent.mkdir(parents=True)
    src.write_text("export const service = () => {};\n")
    tests_dir = tmp_path / "pkg" / "__tests__"
    tests_dir.mkdir()
    (tests_dir / "service.test.ts").write_text("test('service', () => {});\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_for_test_file_itself(tmp_path: Path) -> None:
    """Editing the test file itself is silent (it is not source needing a test)."""
    test_file = tmp_path / "test_widget.py"
    test_file.write_text("def test_widget(): ...\n")

    stdout, stderr, code = _run_hook(_make_payload(str(test_file)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_for_non_source_extension(tmp_path: Path) -> None:
    """A non-source file (e.g. Markdown) is silent."""
    doc = tmp_path / "README.md"
    doc.write_text("# readme\n")

    stdout, stderr, code = _run_hook(_make_payload(str(doc)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_for_inline_test_language(tmp_path: Path) -> None:
    """Rust (inline-test convention) is not in the trigger set, so it is silent."""
    src = tmp_path / "src" / "lib.rs"
    src.parent.mkdir(parents=True)
    src.write_text("pub fn f() {}\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_for_entrypoint_file(tmp_path: Path) -> None:
    """Aggregator files like __init__.py are skipped to avoid noise."""
    src = tmp_path / "pkg" / "__init__.py"
    src.parent.mkdir(parents=True)
    src.write_text("\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_silent_inside_node_modules(tmp_path: Path) -> None:
    """A source file inside node_modules is skipped."""
    src = tmp_path / "node_modules" / "dep" / "index.js"
    src.parent.mkdir(parents=True)
    src.write_text("module.exports = {};\n")

    stdout, stderr, code = _run_hook(_make_payload(str(src)))

    assert code == 0
    assert stderr == ""


@_REQUIRES_JQ
def test_windows_path_separator_is_normalized() -> None:
    """Backslash separators are normalized before pattern matching."""
    stdout, stderr, code = _run_hook(_make_payload("src\\nope\\orphan.go"))

    assert code == 0
    assert "test-gap-notice" in stderr
    assert "src/nope/orphan.go" in stderr


def test_disabled_via_env(tmp_path: Path) -> None:
    """NEXUS_DISABLED_HOOKS containing test-gap-notice short-circuits silently."""
    src = tmp_path / "orphan.py"
    src.write_text("def f(): ...\n")

    stdout, stderr, code = _run_hook(
        _make_payload(str(src)),
        env_overrides={"NEXUS_DISABLED_HOOKS": "test-gap-notice"},
    )

    assert code == 0
    assert stderr == ""


def test_minimal_profile_short_circuits(tmp_path: Path) -> None:
    """NEXUS_HOOK_PROFILE=minimal skips this advisory hook."""
    src = tmp_path / "orphan.py"
    src.write_text("def f(): ...\n")

    stdout, stderr, code = _run_hook(
        _make_payload(str(src)),
        env_overrides={"NEXUS_HOOK_PROFILE": "minimal"},
    )

    assert code == 0
    assert stderr == ""
