"""session-start prints one idle-lane line for a live minor run of this repository (v4.15.6).

Every case runs on both the `.sh` and the `.ps1` implementation, so each assertion is
also an exit-code and output parity check.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
LANE_HEALTH = (
    HOOKS.parents[0] / "skills/workflow/implement-phase/scripts/lane_health.py"
)
TAG = "[Nexus-Hub: session-start] "
EXPECTED = (
    TAG + "Minor v9.9: 1 idle member (v9.9.1 unadmitted). Dispatch eligible members "
    "(implement-phase runbook, Refill available slots)."
)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )


@pytest.fixture(params=["sh", "ps1"])
def run_hook(request, bash_bin: str, powershell_bin: str, tmp_path: Path):
    home = tmp_path / "nexus-home"
    (home / "runs").mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", "-b", "main", cwd=repo)

    def _run(
        record: dict | None, extra_env: dict[str, str] | None = None
    ) -> tuple[list[str], int]:
        if record is not None:
            (home / "runs" / "rec.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
        if request.param == "sh":
            argv = [bash_bin, str(HOOKS / "session-start.sh")]
        else:
            argv = [
                powershell_bin,
                "-NoProfile",
                "-File",
                str(HOOKS / "session-start.ps1"),
            ]
        env = {
            **os.environ,
            "NEXUS_HOME": home.as_posix(),
            "NEXUS_SESSION_DIGEST": "off",
            "NEXUS_WORKTREE_NOTICE": "off",
            "NEXUS_LANE_HEALTH": LANE_HEALTH.as_posix(),
        }
        for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_LANE_NOTICE"):
            env.pop(key, None)
        env.update(extra_env or {})
        done = subprocess.run(
            argv,
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            stdin=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
        return [line.rstrip("\r") for line in done.stdout.splitlines()], done.returncode

    _run.repo = repo
    return _run


def _record(repo: Path, **extra) -> dict:
    return {
        "minor": "v9.9",
        "repo_root": str(repo),
        "completed": None,
        "pause": None,
        "members": [],
        "minor_amendment_members": [{"version": "v9.9.1"}],
        **extra,
    }


def _lane_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith(TAG + "Minor ")]


def test_idle_member_prints_one_notice(run_hook) -> None:
    lines, code = run_hook(_record(run_hook.repo))
    assert code == 0
    assert _lane_lines(lines) == [EXPECTED]


@pytest.mark.parametrize(
    "case", ["disabled", "no-record", "paused", "other-repo", "no-script"]
)
def test_lane_notice_is_silent_when_nothing_to_report(
    run_hook, tmp_path: Path, case: str
) -> None:
    env: dict[str, str] = {}
    record: dict | None = _record(run_hook.repo)
    if case == "disabled":
        env["NEXUS_LANE_NOTICE"] = "off"
    elif case == "no-record":
        record = None
    elif case == "paused":
        record = _record(run_hook.repo, pause={"at": "2026-11-22T00:00:00Z"})
    elif case == "other-repo":
        other = tmp_path / "other"
        other.mkdir()
        _git("init", "-q", "-b", "main", cwd=other)
        record = _record(other)
    elif case == "no-script":
        env["NEXUS_LANE_HEALTH"] = (tmp_path / "missing.py").as_posix()
        env["HOME"] = tmp_path.as_posix()
    lines, code = run_hook(record, env)
    assert code == 0
    assert _lane_lines(lines) == [], lines
