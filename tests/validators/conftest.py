"""Shared fixtures for the v2.3.0 CI validator suite.

Each validator script under `scripts/` is invoked as a subprocess against a
per-test temporary directory so the tests verify the actual CLI surface end
users will run.
"""

from __future__ import annotations

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
