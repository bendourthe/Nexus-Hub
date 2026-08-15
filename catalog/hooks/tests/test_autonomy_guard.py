"""Tests for the autonomy execution-trigger guard and its shell siblings."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib.autonomy import EXECUTION_TRIGGER_PATHS, STATE_VERSION, guard_path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parent.parent
_ENGINE = _REPO_ROOT / "scripts" / "lib" / "autonomy.py"

_CANONICAL_SAMPLES = (
    ".claude/settings.json",
    ".claude/hooks/pre-tool.sh",
    ".vscode/tasks.json",
    ".vscode/launch.json",
    ".git/hooks/post-merge",
    ".git/config",
    ".cursor/rules/security.md",
    ".venv/bin/python",
    ".venv/Scripts/python.exe",
    "venv/bin/python",
    "venv/Scripts/python.exe",
    "pyvenv.cfg",
)


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def _write_active_state(repo: Path) -> None:
    state_dir = repo / ".nexus-hub"
    state_dir.mkdir(exist_ok=True)
    (state_dir / "autonomy-state.json").write_text(
        json.dumps(
            {
                "version": STATE_VERSION,
                "platforms": {
                    "claude": {
                        "tier": "edits",
                        "expiry": "2099-01-01T00:00:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def _payload(path: str) -> str:
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}})


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _init_repo(tmp_path)
    return tmp_path


@pytest.fixture(params=["sh", "ps1"])
def run_hook(request, bash_bin: str, powershell_bin: str):
    if request.param == "sh":
        argv = [bash_bin, str(_HOOKS_DIR / "autonomy-guard.sh")]
    else:
        argv = [
            powershell_bin,
            "-NoProfile",
            "-File",
            str(_HOOKS_DIR / "autonomy-guard.ps1"),
        ]

    def _run(
        working_dir: Path,
        path: str,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "NEXUS_AUTONOMY_ENGINE": str(_ENGINE)}
        env.pop("NEXUS_DISABLED_HOOKS", None)
        env.pop("NEXUS_HOOK_PROFILE", None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            argv,
            input=_payload(path),
            text=True,
            capture_output=True,
            cwd=working_dir,
            env=env,
            timeout=120,
            check=False,
        )

    return _run


@pytest.mark.parametrize("path", _CANONICAL_SAMPLES)
def test_every_canonical_path_is_denied_while_active(
    repo: Path, run_hook, path: str
) -> None:
    _write_active_state(repo)

    proc = run_hook(repo, path)

    assert proc.returncode == 2
    assert "AUTONOMY BLOCKED" in proc.stderr
    assert path.replace("\\", "/") in proc.stderr


def test_no_state_is_a_quiet_fast_noop(repo: Path, run_hook) -> None:
    proc = run_hook(repo, ".claude/settings.json")

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_benign_path_is_allowed_while_active(repo: Path, run_hook) -> None:
    _write_active_state(repo)

    proc = run_hook(repo, "src/feature.py")

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_message_names_the_traversal_target(repo: Path, run_hook) -> None:
    _write_active_state(repo)

    proc = run_hook(repo, "src/../.vscode/tasks.json")

    assert proc.returncode == 2
    assert ".vscode/tasks.json" in proc.stderr


def test_symlink_alias_to_trigger_path_is_denied(repo: Path, run_hook) -> None:
    _write_active_state(repo)
    target = repo / ".claude"
    target.mkdir()
    alias = repo / "settings-alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    proc = run_hook(repo, "settings-alias/settings.json")

    assert proc.returncode == 2
    assert ".claude/settings.json" in proc.stderr


def test_unreadable_state_fails_closed_for_trigger_path(repo: Path, run_hook) -> None:
    state_dir = repo / ".nexus-hub"
    state_dir.mkdir()
    (state_dir / "autonomy-state.json").write_text("not json", encoding="utf-8")

    proc = run_hook(repo, ".cursor/rules.md")

    assert proc.returncode == 2
    assert "state is unreadable" in proc.stderr
    assert (state_dir / "autonomy-state.json").read_text(encoding="utf-8") == "not json"


@pytest.mark.parametrize(
    "env_extra",
    [
        {"NEXUS_DISABLED_HOOKS": "autonomy-guard"},
        {"NEXUS_HOOK_PROFILE": "minimal"},
    ],
)
def test_runtime_controls_are_honored(
    repo: Path, run_hook, env_extra: dict[str, str]
) -> None:
    _write_active_state(repo)

    proc = run_hook(repo, ".git/config", env_extra)

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert proc.stderr == ""


def test_direct_guard_rejects_absolute_alias_but_not_outside_path(repo: Path) -> None:
    _write_active_state(repo)
    protected = repo / ".vscode" / "tasks.json"
    protected.parent.mkdir()
    alias = repo / "task-alias.json"
    try:
        alias.symlink_to(protected)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    assert guard_path(alias, project_dir=repo).blocked is True
    assert guard_path(repo.parent / "tasks.json", project_dir=repo).blocked is False


def test_canonical_path_list_has_one_phase4_code_definition() -> None:
    expected = (
        ".claude/settings*.json",
        ".claude/hooks/*",
        ".vscode/tasks.json",
        ".vscode/launch.json",
        ".git/hooks/*",
        ".git/config",
        ".cursor/*",
        ".venv/bin/*",
        ".venv/Scripts/*",
        "venv/bin/*",
        "venv/Scripts/*",
        "pyvenv.cfg",
    )
    assert EXECUTION_TRIGGER_PATHS == expected

    definitions = []
    for path in (_REPO_ROOT / "scripts").rglob("*.py"):
        if "EXECUTION_TRIGGER_PATHS =" in path.read_text(encoding="utf-8"):
            definitions.append(path.relative_to(_REPO_ROOT).as_posix())
    assert definitions == ["scripts/lib/autonomy.py"]


def test_guard_cli_reads_the_original_hook_payload(repo: Path) -> None:
    _write_active_state(repo)
    proc = subprocess.run(
        [
            sys.executable,
            str(_ENGINE),
            "guard",
            "--project",
            str(repo),
        ],
        input=_payload(".claude/settings.local.json"),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert proc.returncode == 2
    assert ".claude/settings.local.json" in proc.stderr


def test_powershell_guard_reads_hook_stdin_unconditionally() -> None:
    """Windows service runners may misreport a redirected standard-input pipe."""
    script = (_HOOKS_DIR / "autonomy-guard.ps1").read_text(encoding="utf-8")

    assert "$stdin = [Console]::OpenStandardInput()" in script
    assert "$raw = $reader.ReadToEnd()" in script
    assert "[Console]::IsInputRedirected" not in script
    assert "[Console]::In" not in script
