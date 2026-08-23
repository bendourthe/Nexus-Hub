"""Tests for catalog/hooks/memory-store-guard.{sh,ps1}.

Closes v3.19.1 DF-3: a relocated nexus-memory store that lands inside a
git working tree must be blocked on Write/Edit and on git add/commit.
Every assertion runs against both implementations.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "memory-store-guard.sh"
_HOOK_PS1 = _HOOKS_DIR / "memory-store-guard.ps1"


@pytest.fixture(params=["sh", "ps1"])
def run(request):
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
        payload: str,
        *,
        cwd: Path | None = None,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        env = {**os.environ}
        for key in (
            "NEXUS_DISABLED_HOOKS",
            "NEXUS_HOOK_PROFILE",
            "NEXUS_MEMORY_ALLOW_IN_REPO",
        ):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            cwd=str(cwd) if cwd is not None else None,
            timeout=120,
        )

    return _run


def _write_payload(path: str) -> str:
    return json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": path, "content": "x"}}
    )


def _bash_payload(command: str) -> str:
    return json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command, "description": "git"}}
    )


def _git_init(root: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=str(root),
        check=True,
        capture_output=True,
        text=True,
    )


def test_benign_write_is_allowed(run, tmp_path: Path) -> None:
    result = run(_write_payload(str(tmp_path / "src" / "app.py")), cwd=tmp_path)
    assert result.returncode == 0
    assert "BLOCKED" not in result.stderr


def test_write_entries_log_inside_git_repo_is_blocked(run, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    store = repo / "memory"
    store.mkdir(parents=True)
    (store / ".nexus-memory-store").write_text("nexus-memory-store\n", encoding="utf-8")
    _git_init(repo)
    target = store / "entries.log"
    result = run(_write_payload(str(target)), cwd=repo)
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr
    assert "entries.log" in result.stderr


def test_write_tree_level_inside_git_repo_is_blocked(run, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    store = repo / "memory"
    tree = store / "tree"
    tree.mkdir(parents=True)
    (store / "config.json").write_text('{"record_width": 1024}\n', encoding="utf-8")
    _git_init(repo)
    result = run(_write_payload(str(tree / "level_2")), cwd=repo)
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_git_add_of_entries_log_is_blocked(run, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    result = run(_bash_payload("git add memory/entries.log"), cwd=repo)
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_allow_in_repo_override_permits_write(run, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    store = repo / "memory"
    store.mkdir(parents=True)
    (store / ".nexus-memory-store").write_text("nexus-memory-store\n", encoding="utf-8")
    _git_init(repo)
    result = run(
        _write_payload(str(store / "entries.log")),
        cwd=repo,
        env_extra={"NEXUS_MEMORY_ALLOW_IN_REPO": "1"},
    )
    assert result.returncode == 0
    assert "BLOCKED" not in result.stderr


def test_minimal_profile_does_not_disable_the_gate(run, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    store = repo / "memory"
    store.mkdir(parents=True)
    (store / ".nexus-memory-store").write_text("nexus-memory-store\n", encoding="utf-8")
    _git_init(repo)
    result = run(
        _write_payload(str(store / "entries.log")),
        cwd=repo,
        env_extra={"NEXUS_HOOK_PROFILE": "minimal"},
    )
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_empty_payload_is_a_no_op(run) -> None:
    result = run("")
    assert result.returncode == 0
