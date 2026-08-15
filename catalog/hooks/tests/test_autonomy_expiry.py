"""Targeted parity tests for the autonomy TTL SessionStart hook pair."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib import autonomy

HOOKS = ROOT / "catalog" / "hooks"
ENGINE = ROOT / "scripts" / "lib" / "autonomy.py"
PAST = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True
    )


def _repo(tmp_path: Path, name: str) -> Path:
    if shutil.which("git") is None:  # pragma: no cover
        pytest.skip("git not available")
    root = tmp_path / name
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Hook Test")
    (root / ".gitignore").write_text(".nexus-hub/\n", encoding="utf-8")
    config = root / ".claude" / "settings.local.json"
    config.parent.mkdir()
    config.write_text('{"permissions":{"defaultMode":"default"}}\n', encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _git(root, "branch", "-M", "feat/hook-test")
    return root


def _command(kind: str, request: pytest.FixtureRequest) -> list[str]:
    if kind == "sh":
        bash_bin = request.getfixturevalue("bash_bin")
        return [bash_bin, str(HOOKS / "autonomy-expiry.sh")]
    powershell_bin = request.getfixturevalue("powershell_bin")
    return [powershell_bin, "-NoProfile", "-File", str(HOOKS / "autonomy-expiry.ps1")]


def _run_hook(
    kind: str,
    repo: Path,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    fake_home = tmp_path / f"home-{kind}"
    fake_home.mkdir(exist_ok=True)
    env = {**os.environ}
    env["HOME"] = str(fake_home)
    env["USERPROFILE"] = str(fake_home)
    env["NEXUS_AUTONOMY_ENGINE"] = str(ENGINE)
    return subprocess.run(
        _command(kind, request),
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_expired_state_is_reverted_by_each_hook(
    kind: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    repo = _repo(tmp_path, f"expired-{kind}")
    config = repo / ".claude" / "settings.local.json"
    original = config.read_text(encoding="utf-8")
    enabled = autonomy.enable(
        "claude",
        "edits_only",
        1,
        project_dir=repo,
        now=PAST,
        user="hook-test",
        process="pytest:1",
    )
    assert enabled.outcome == "enabled"

    result = _run_hook(kind, repo, request, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert config.read_text(encoding="utf-8") == original
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert not Path(enabled.backup_path).exists()


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_missing_backup_fails_loudly_and_preserves_state_for_each_hook(
    kind: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    repo = _repo(tmp_path, f"missing-{kind}")
    config = repo / ".claude" / "settings.local.json"
    enabled = autonomy.enable(
        "claude",
        "edits_only",
        1,
        project_dir=repo,
        now=PAST,
        user="hook-test",
        process="pytest:1",
    )
    assert enabled.outcome == "enabled"
    enabled_text = config.read_text(encoding="utf-8")
    Path(enabled.backup_path).unlink()

    result = _run_hook(kind, repo, request, tmp_path)

    assert result.returncode == 1
    assert "missing" in result.stderr.lower()
    assert config.read_text(encoding="utf-8") == enabled_text
    assert (repo / autonomy.STATE_RELATIVE_PATH).exists()


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_no_state_is_a_quiet_success_for_each_hook(
    kind: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    repo = _repo(tmp_path, f"no-state-{kind}")

    result = _run_hook(kind, repo, request, tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
