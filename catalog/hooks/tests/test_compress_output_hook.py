"""Tests for the PreToolUse output-compression hook (catalog/hooks/compress-output.sh).

The hook rewrites a Bash command so its stdout is piped through the internal
nexus-context-compressor engine. These tests verify the hook's transformation
*logic* (given a PreToolUse JSON payload on stdin, what it emits on stdout),
not live Claude Code behavior:

* It is inert (exit 0, no output) unless NEXUS_CONTEXT_COMPRESS=1.
* When enabled, it emits a PreToolUse `updatedInput` whose `.command` wraps the
  original command in a pipe through the compressor and preserves the exit code.
* It never rewrites an empty command, an already-wrapped command, or (when the
  engine cannot be imported / jq is absent) anything at all -- always fail-open.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_compress_output_hook.py -v
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOK = Path(__file__).parent.parent / "compress-output.sh"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_SRC = _REPO_ROOT / "extensions" / "nexus-context-compressor" / "src"


def _bash_path() -> str:
    """Return the bash interpreter path. On Windows, prefer Git for Windows bash."""
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError("bash not found on PATH; cannot run compress-output hook tests")


_BASH = _bash_path()


def _run(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke the hook with ``payload`` JSON on stdin; return the completed process."""
    import os

    env = dict(os.environ)
    # Make the engine importable for the hook's fail-open import gate.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_ENGINE_SRC) + (os.pathsep + existing if existing else "")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [_BASH, str(_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def _rewrite_path_available() -> bool:
    """True when both prerequisites for the rewrite path are present: jq + an
    interpreter that can import the engine with PYTHONPATH set to the package src."""
    if shutil.which("jq") is None:
        return False
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(_ENGINE_SRC) + os.pathsep + env.get("PYTHONPATH", "")
    for interp in ("python3", "python"):
        if shutil.which(interp) is None:
            continue
        probe = subprocess.run(
            [interp, "-c", "import nexus_context_compressor"],
            capture_output=True,
            env=env,
        )
        if probe.returncode == 0:
            return True
    return False


_REWRITE_AVAILABLE = _rewrite_path_available()
_needs_rewrite = pytest.mark.skipif(
    not _REWRITE_AVAILABLE,
    reason="rewrite path needs jq and an interpreter that can import nexus_context_compressor",
)

_SAMPLE = {"tool_name": "Bash", "tool_input": {"command": "cat data.json", "description": "read"}}


# --- Inert paths (no dependencies; run everywhere) -----------------------


def test_inert_when_not_enabled() -> None:
    """Default OFF: no env var => exit 0 and no stdout (command runs unchanged)."""
    result = _run(_SAMPLE)  # NEXUS_CONTEXT_COMPRESS unset
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_inert_when_explicitly_disabled() -> None:
    result = _run(_SAMPLE, {"NEXUS_CONTEXT_COMPRESS": "0"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_empty_command_is_passthrough() -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": ""}}
    result = _run(payload, {"NEXUS_CONTEXT_COMPRESS": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_non_bash_tool_is_passthrough() -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": "/x"}}
    result = _run(payload, {"NEXUS_CONTEXT_COMPRESS": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


# --- Rewrite path (needs jq + importable engine) -------------------------


@_needs_rewrite
def test_enabled_rewrites_command() -> None:
    result = _run(_SAMPLE, {"NEXUS_CONTEXT_COMPRESS": "1"})
    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    hso = emitted["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "allow"
    new_cmd = hso["updatedInput"]["command"]
    # The original command survives, gets grouped + piped through the engine, and
    # the original exit status is restored.
    assert "cat data.json" in new_cmd
    assert "-m nexus_context_compressor compress" in new_cmd
    assert "${PIPESTATUS[0]}" in new_cmd


@_needs_rewrite
def test_other_tool_input_fields_preserved() -> None:
    result = _run(_SAMPLE, {"NEXUS_CONTEXT_COMPRESS": "1"})
    emitted = json.loads(result.stdout)
    # The non-command field (description) is preserved through the rewrite.
    assert emitted["hookSpecificOutput"]["updatedInput"]["description"] == "read"


@_needs_rewrite
def test_already_wrapped_command_is_not_rewrapped() -> None:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "cat x | python -m nexus_context_compressor compress"},
    }
    result = _run(payload, {"NEXUS_CONTEXT_COMPRESS": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


@_needs_rewrite
def test_command_with_percent_is_safe() -> None:
    """A command containing % must not be mangled by printf in the rewrite."""
    payload = {"tool_name": "Bash", "tool_input": {"command": "date +%s"}}
    result = _run(payload, {"NEXUS_CONTEXT_COMPRESS": "1"})
    emitted = json.loads(result.stdout)
    assert "date +%s" in emitted["hookSpecificOutput"]["updatedInput"]["command"]
