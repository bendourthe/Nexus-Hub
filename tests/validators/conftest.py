"""Shared fixtures for the v2.3.0 CI validator suite.

Each validator script under `scripts/` is invoked as a subprocess against a
per-test temporary directory so the tests verify the actual CLI surface end
users will run.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"


@pytest.fixture
def scripts_dir() -> Path:
    return SCRIPTS_DIR


def run_validator(
    script: str,
    root: Path,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a validator script as a subprocess with `--root <root>`.

    Returns the CompletedProcess so individual tests can assert on returncode,
    stdout, and stderr separately.
    """
    cmd = [sys.executable, str(SCRIPTS_DIR / script), "--root", str(root)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


@pytest.fixture
def runner():
    return run_validator

@pytest.fixture(scope="session")
def minor_git_seed(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Only initial Git state is shared; every test copies both repositories."""
    from .test_completion_minor_record import MINOR_DIR, PUSH_URL, TRANSPORT_OVERRIDE_ENV, _plan_text

    seed = tmp_path_factory.mktemp("minor-git-seed")
    empty = seed / "empty.gitconfig"
    empty.write_text("", encoding="utf-8")
    # Session setup cannot use function-scoped monkeypatch or isolated config.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_") and key not in TRANSPORT_OVERRIDE_ENV}
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")

    def git(cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True,
                       text=True, check=True, timeout=30)

    work, remote = seed / "work", seed / "remote.git"
    git(seed, "init", "--bare", "-q", "-b", "main", str(remote))
    work.mkdir()
    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.email", "t@example.invalid")
    git(work, "config", "user.name", "Test")
    git(work, "remote", "add", "origin", str(remote))
    git(work, "remote", "set-url", "--push", "origin", PUSH_URL)
    for version, slug in (("v0.5.2", "alpha"), ("v0.5.10", "omega")):
        plan = work / MINOR_DIR / f"{version}-{slug}.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(_plan_text(version, slug, "queued"), encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-q", "--allow-empty", "-m", "start")
    git(work, "branch", "develop")
    git(work, "push", "-q", str(remote), "main", "develop")
    git(work, "fetch", "-q", "origin")
    return seed
