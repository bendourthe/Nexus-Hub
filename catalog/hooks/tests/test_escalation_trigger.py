"""Tests for catalog/hooks/escalation-trigger.{sh,ps1}.

Covers the v3.15.6 Phase 2 work (AC2):

  * the stdin JSON input contract (the bug fix: the hook previously read only the
    $CLAUDE_FILE_PATH environment variable, which Claude Code does not set, so it
    was inert in practice and never warned on anything),
  * the legacy $CLAUDE_FILE_PATH fallback, kept for backward compatibility,
  * every group A and group C surface from the canonical execution-trigger list in
    catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md,
  * the `nexus-hub init` self-write carve-out, including that it does NOT
    over-suppress a surface the installer does not own,
  * the default action staying `warn` so the catalog cannot self-block its own
    wiring, with `block` available opt-in,
  * regression coverage for the pre-existing sensitive-path patterns.

Every test runs against BOTH the bash hook and its PowerShell sibling via the
`run` fixture, so the suite is also the .sh/.ps1 parity check. A missing
interpreter skips only that parameter.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_escalation_trigger.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "escalation-trigger.sh"
_HOOK_PS1 = _HOOKS_DIR / "escalation-trigger.ps1"

_WARNING_MARKER = "ESCALATION WARNING"
_BLOCK_MARKER = "ESCALATION BLOCKED"


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    """Invoke either hook implementation with a stdin payload.

    Parametrizing here is what makes every assertion below a parity assertion:
    the same expectation is enforced against both implementations.
    """
    impl = request.param
    if impl == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    def _run(
        payload: str = "", env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        env = {**os.environ}
        # Never let an ambient value leak into a test expectation.
        for key in ("CLAUDE_FILE_PATH", "ESCALATION_MODE", "NEXUS_HUB_INIT"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            timeout=120,
        )

    return _run


def _payload(path: str, key: str = "file_path") -> str:
    return json.dumps({"tool_input": {key: path}})


def _warned(proc: subprocess.CompletedProcess) -> bool:
    return _WARNING_MARKER in proc.stdout


# --- The input-contract fix: a stdin payload must actually reach the matcher ---


def test_stdin_payload_triggers_warning(run) -> None:
    """The core regression: before Phase 2 this produced no output at all."""
    proc = run(_payload("src/auth/login.py"))
    assert proc.returncode == 0
    assert _warned(proc), "hook did not read the path from the stdin JSON payload"


def test_stdin_path_alias_is_honored(run) -> None:
    """tool_input.path is the documented alternate key used by sibling hooks."""
    assert _warned(run(_payload(".git/hooks/post-merge", key="path")))


def test_legacy_env_var_fallback_still_works(run) -> None:
    """An existing setup exporting CLAUDE_FILE_PATH must keep working."""
    proc = run("", {"CLAUDE_FILE_PATH": "src/auth/login.py"})
    assert proc.returncode == 0
    assert _warned(proc)


def test_stdin_wins_over_env_var(run) -> None:
    """The payload is the primary source; the env var is only a fallback."""
    proc = run(_payload("src/main.py"), {"CLAUDE_FILE_PATH": "src/auth/login.py"})
    assert not _warned(proc), "env var overrode a benign stdin path"


# --- Canonical execution-trigger surfaces (groups A and C) ---

_GROUP_A_PATHS = [
    ".claude/settings.json",
    ".claude/settings.local.json",
    "/srv/project/.claude/settings.json",
    ".claude/hooks/my-hook.sh",
    ".vscode/tasks.json",
    ".vscode/launch.json",
    ".git/hooks/pre-commit",
    ".git/config",
    ".cursor/rules/project.mdc",
]

_GROUP_C_PATHS = [
    ".venv/bin/python",
    ".venv/Scripts/python.exe",
    "venv/bin/activate",
    "venv/Scripts/activate",
    "pyvenv.cfg",
    "project/.venv/bin/python",
]


@pytest.mark.parametrize("path", _GROUP_A_PATHS)
def test_group_a_surface_warns(run, path: str) -> None:
    """Group A: file paths a component outside the sandbox later executes."""
    assert _warned(run(_payload(path))), f"group A surface not covered: {path}"


@pytest.mark.parametrize("path", _GROUP_C_PATHS)
def test_group_c_surface_warns(run, path: str) -> None:
    """Group C: interpreter/environment paths run during editor discovery."""
    assert _warned(run(_payload(path))), f"group C surface not covered: {path}"


def test_windows_backslash_path_is_normalized(run) -> None:
    assert _warned(run(_payload("C:\\repo\\.git\\hooks\\pre-commit")))


# --- Group B must NOT be handled here (the matching-surface split) ---


def test_group_b_command_string_is_not_matched_here(run) -> None:
    """Group B belongs to git-guardrails, not to this file-path hook.

    A PreToolUse Write/Edit payload carries no shell command, so a git config key
    can never appear as a file path. Asserting it here pins the split so a future
    edit does not "helpfully" add command patterns to a path matcher, which would
    silently never fire.
    """
    assert not _warned(run(_payload("core.hooksPath")))
    assert not _warned(run(_payload("core.fsmonitor")))


# --- The nexus-hub init self-write carve-out ---

_INIT_OWNED = [
    ".claude/settings.json",
    ".claude/hooks/generated.sh",
    ".cursor/rules/nexus-hub.mdc",
    ".agents/workflows/plan.md",
    ".github/skills/example/SKILL.md",
]


@pytest.mark.parametrize("path", _INIT_OWNED)
def test_init_owned_write_is_silent_when_announced(run, path: str) -> None:
    """A legitimate installer write must not produce a spurious warning."""
    proc = run(_payload(path), {"NEXUS_HUB_INIT": "1"})
    assert proc.returncode == 0
    assert not _warned(proc), f"init-owned write warned spuriously: {path}"


@pytest.mark.parametrize("path", [".git/hooks/pre-commit", ".vscode/tasks.json"])
def test_init_carve_out_does_not_over_suppress(run, path: str) -> None:
    """The carve-out covers only what the installer writes, nothing wider."""
    assert _warned(
        run(_payload(path), {"NEXUS_HUB_INIT": "1"})
    ), f"carve-out wrongly suppressed a non-init-owned surface: {path}"


def test_init_carve_out_inert_when_not_announced(run) -> None:
    """Without the announcement the surface still warns."""
    assert _warned(run(_payload(".claude/settings.json")))


# --- Mode behavior: advisory by default, blocking only opt-in ---


def test_default_mode_is_advisory(run) -> None:
    """Critical: the default must never block, or the catalog self-blocks its own
    `nexus-hub init` writes to .claude/settings.json."""
    proc = run(_payload(".claude/settings.json"))
    assert proc.returncode == 0
    assert _WARNING_MARKER in proc.stdout
    assert _BLOCK_MARKER not in proc.stdout


def test_block_mode_is_opt_in(run) -> None:
    proc = run(_payload(".claude/settings.json"), {"ESCALATION_MODE": "block"})
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stdout


# --- Quiet paths ---


@pytest.mark.parametrize(
    "payload",
    ["", "not json at all", "{}", '{"tool_input":{}}', '{"tool_input":{"file_path":null}}'],
)
def test_unusable_payload_is_silent(run, payload: str) -> None:
    """No path, or an unparseable payload, must exit 0 quietly."""
    proc = run(payload)
    assert proc.returncode == 0
    assert not _warned(proc)


@pytest.mark.parametrize(
    "path", ["src/main.py", "README.md", "docs/guide.md", "tests/test_x.py"]
)
def test_benign_path_is_silent(run, path: str) -> None:
    assert not _warned(run(_payload(path)))


# --- Regression: the pre-existing sensitive-path families still match ---


@pytest.mark.parametrize(
    "path",
    [
        "src/auth/login.py",
        "db/migrations/001_init.sql",
        "app/package.json",
        "infra/Dockerfile",
        "svc/.env.production",
        "deploy/terraform/main.tf",
    ],
)
def test_pre_existing_patterns_still_warn(run, path: str) -> None:
    assert _warned(run(_payload(path))), f"pre-existing pattern regressed: {path}"
