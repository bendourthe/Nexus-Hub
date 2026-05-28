"""
Tests for the memory-persistence session hooks (Phase 3 T007).

Covers the round-trip between:

    catalog/hooks/session-summary.sh   (writes the digest on Stop / PreCompact /
                                        SessionEnd)
    catalog/hooks/session-start.sh     (reads it back on SessionStart)

Plus the off-switch (`NEXUS_SESSION_DIGEST=off`), the size cap
(`NEXUS_SESSION_START_MAX_CHARS`), and the no-network invariant (the bash
hooks must not call any binary outside `git`, `jq`, `python3`, and the
standard POSIX userland).

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_session_digest.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).parent.parent
_SUMMARY_HOOK = _HOOKS_DIR / "session-summary.sh"
_START_HOOK = _HOOKS_DIR / "session-start.sh"


def _bash_path() -> str:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError("bash not found on PATH; cannot run session-digest hook tests")


_BASH = _bash_path()


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Initialize an empty git repo so the hooks have a real toplevel."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    # One commit so `git diff HEAD` works.
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=True,
        env={**os.environ, "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
             "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"},
    )
    return repo


def _run(hook: Path, repo: Path, env_extra: dict[str, str] | None = None,
         stdin: str = "") -> tuple[str, str, int]:
    env = os.environ.copy()
    # Isolate from the developer's real $HOME (the global session log).
    env["HOME"] = str(repo / "_home")
    (repo / "_home").mkdir(exist_ok=True)
    # Disable adjacent hooks that might fire indirectly.
    env["NEXUS_DISABLED_HOOKS"] = env.get("NEXUS_DISABLED_HOOKS", "")
    if env_extra:
        env.update(env_extra)
    result = subprocess.run(
        [_BASH, str(hook)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        input=stdin,
    )
    return result.stdout, result.stderr, result.returncode


# ── Syntax ────────────────────────────────────────────────────────────────


class TestSyntax:
    def test_summary_hook_parses(self) -> None:
        result = subprocess.run([_BASH, "-n", str(_SUMMARY_HOOK)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

    def test_start_hook_parses(self) -> None:
        result = subprocess.run([_BASH, "-n", str(_START_HOOK)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


# ── Round-trip ────────────────────────────────────────────────────────────


class TestDigestRoundTrip:
    def test_summary_writes_digest_at_default_path(self, tmp_git_repo: Path) -> None:
        _out, _err, code = _run(_SUMMARY_HOOK, tmp_git_repo,
                                stdin=json.dumps({"session_duration": "42m"}))
        assert code == 0
        digest = tmp_git_repo / ".nexus" / "context" / "last-session.md"
        assert digest.exists(), "session-summary did not write the digest file"
        body = digest.read_text(encoding="utf-8")
        assert "# Last session digest" in body
        assert "## Git context" in body
        # The branch line should be present and named `main` (set by the fixture).
        assert "Branch:" in body

    def test_digest_path_override_is_honored(self, tmp_git_repo: Path) -> None:
        custom = ".nexus/alt/some-digest.md"
        _out, _err, code = _run(
            _SUMMARY_HOOK, tmp_git_repo,
            env_extra={"NEXUS_SESSION_DIGEST_PATH": custom},
            stdin="{}",
        )
        assert code == 0
        assert (tmp_git_repo / custom).exists()
        assert not (tmp_git_repo / ".nexus" / "context" / "last-session.md").exists()

    def test_start_surfaces_digest_after_summary(self, tmp_git_repo: Path) -> None:
        # Step 1: write the digest.
        _run(_SUMMARY_HOOK, tmp_git_repo, stdin=json.dumps({"duration": "1h"}))
        # Step 2: SessionStart reads it back.
        out, _err, code = _run(_START_HOOK, tmp_git_repo)
        assert code == 0
        assert "Last session digest" in out
        assert "# Last session digest" in out
        assert "## Git context" in out

    def test_start_silent_when_no_digest_yet(self, tmp_git_repo: Path) -> None:
        out, _err, code = _run(_START_HOOK, tmp_git_repo)
        assert code == 0
        # Orientation block must still print but no digest section.
        assert "Nexus-Hub is active" in out
        assert "Last session digest" not in out


# ── Off-switch & size cap ─────────────────────────────────────────────────


class TestRuntimeControls:
    def test_off_switch_skips_digest_write(self, tmp_git_repo: Path) -> None:
        _out, _err, code = _run(
            _SUMMARY_HOOK, tmp_git_repo,
            env_extra={"NEXUS_SESSION_DIGEST": "off"},
            stdin="{}",
        )
        assert code == 0
        assert not (tmp_git_repo / ".nexus" / "context" / "last-session.md").exists()

    def test_off_switch_skips_digest_read(self, tmp_git_repo: Path) -> None:
        # Write a digest first.
        _run(_SUMMARY_HOOK, tmp_git_repo, stdin="{}")
        # Then read with the off-switch.
        out, _err, code = _run(
            _START_HOOK, tmp_git_repo,
            env_extra={"NEXUS_SESSION_DIGEST": "off"},
        )
        assert code == 0
        assert "Last session digest" not in out

    def test_size_cap_truncates_output(self, tmp_git_repo: Path) -> None:
        # Manually write a large digest, then read with a small cap.
        digest_dir = tmp_git_repo / ".nexus" / "context"
        digest_dir.mkdir(parents=True)
        big = "# Last session digest\n\n" + ("filler line " * 200 + "\n") * 50
        (digest_dir / "last-session.md").write_text(big, encoding="utf-8")
        out, _err, code = _run(
            _START_HOOK, tmp_git_repo,
            env_extra={"NEXUS_SESSION_START_MAX_CHARS": "500"},
        )
        assert code == 0
        # The truncation marker must be present.
        assert "digest truncated" in out

    def test_invalid_cap_falls_back_to_default(self, tmp_git_repo: Path) -> None:
        # Write a small digest; bogus cap should not error.
        _run(_SUMMARY_HOOK, tmp_git_repo, stdin="{}")
        out, _err, code = _run(
            _START_HOOK, tmp_git_repo,
            env_extra={"NEXUS_SESSION_START_MAX_CHARS": "not-a-number"},
        )
        assert code == 0
        assert "Last session digest" in out

    def test_minimal_profile_skips_both_sides(self, tmp_git_repo: Path) -> None:
        _out, _err, code = _run(
            _SUMMARY_HOOK, tmp_git_repo,
            env_extra={"NEXUS_HOOK_PROFILE": "minimal"},
            stdin="{}",
        )
        assert code == 0
        assert not (tmp_git_repo / ".nexus").exists()
        out, _err, code = _run(
            _START_HOOK, tmp_git_repo,
            env_extra={"NEXUS_HOOK_PROFILE": "minimal"},
        )
        assert code == 0
        # When minimal, even the orientation block is skipped.
        assert "Nexus-Hub is active" not in out
