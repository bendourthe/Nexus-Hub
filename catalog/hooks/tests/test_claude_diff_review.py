"""
Smoke tests for catalog/hooks/claude-diff-review.sh

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_claude_diff_review.py -v

The hook is bash; tests stub the `claude` CLI by creating a fake binary on PATH
that emits a fixed response, then invoke the hook in a temporary git repo with
a staged diff.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

_HOOK_FILE = Path(__file__).parent.parent / "claude-diff-review.sh"


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
    raise RuntimeError("bash not found on PATH; cannot run claude-diff-review tests")


_BASH = _bash_path()


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with one staged change."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)

    src = repo / "hello.txt"
    src.write_text("hello world\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.txt"], cwd=repo, check=True)

    return repo


def _make_stub_claude(stub_dir: Path, response: str) -> None:
    """Create a fake `claude` binary in stub_dir that prints `response` and exits 0."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # On Windows, create a .cmd shim so PATH lookup finds it as `claude`.
        (stub_dir / "claude.cmd").write_text(
            f"@echo off\r\n{_response_to_echo_lines(response)}",
            encoding="utf-8",
        )
        # Also create a no-extension bash script for Git Bash subshell PATH lookup.
        sh_path = stub_dir / "claude"
        sh_path.write_text(
            "#!/usr/bin/env bash\ncat <<'EOF'\n" + response + "\nEOF\n",
            encoding="utf-8",
        )
        sh_path.chmod(0o755)
    else:
        sh_path = stub_dir / "claude"
        sh_path.write_text(
            "#!/usr/bin/env bash\ncat <<'EOF'\n" + response + "\nEOF\n",
            encoding="utf-8",
        )
        sh_path.chmod(0o755)


def _response_to_echo_lines(response: str) -> str:
    out = []
    for line in response.split("\n"):
        if line == "":
            out.append("echo.")
        else:
            safe = line.replace("&", "^&").replace("<", "^<").replace(">", "^>")
            out.append(f"echo {safe}")
    return "\r\n".join(out) + "\r\n"


def _run_hook(repo: Path, env: dict[str, str] | None = None) -> tuple[str, str, int]:
    """Run the hook from inside `repo`, returning (stdout, stderr, returncode)."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        [_BASH, str(_HOOK_FILE)],
        cwd=repo,
        env=full_env,
        capture_output=True,
        text=True,
    )
    return result.stdout, result.stderr, result.returncode


# ── Tests ──────────────────────────────────────────────────────────────────


class TestSyntax:
    def test_hook_parses_with_bash_n(self) -> None:
        """The hook must be syntactically valid bash."""
        result = subprocess.run(
            [_BASH, "-n", str(_HOOK_FILE)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"bash -n failed: {result.stderr}"


class TestBypassEnvVar:
    def test_disable_env_var_short_circuits(self, tmp_git_repo: Path) -> None:
        """DEVAI_DIFF_REVIEW_DISABLE=1 must exit 0 immediately, regardless of state."""
        env = {"DEVAI_DIFF_REVIEW_DISABLE": "1", "PATH": ""}
        _stdout, _stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0


class TestEmptyDiff:
    def test_no_staged_changes_exits_zero(self, tmp_git_repo: Path) -> None:
        """With nothing staged, the hook must exit 0 silently."""
        # Unstage without using HEAD (the fixture repo has no commits yet, so HEAD does not exist).
        subprocess.run(["git", "rm", "--cached", "hello.txt"], cwd=tmp_git_repo, check=True)
        env = {"PATH": os.environ.get("PATH", "")}
        _stdout, _stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0


class TestNoClaudeCli:
    def test_missing_claude_cli_exits_zero_with_warning(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        """When claude is absent from PATH, the hook must warn and allow."""
        empty_path_dir = tmp_path / "empty_path"
        empty_path_dir.mkdir()
        # PATH must contain git itself, otherwise the hook exits earlier on the git call.
        # Find git's directory and isolate just that on PATH.
        git_path = shutil.which("git")
        assert git_path
        path_with_only_git = str(Path(git_path).parent)
        env = {"PATH": path_with_only_git}
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
        assert "claude CLI not found" in stderr or "claude cli not found" in stderr.lower()


class TestMergeStateSkip:
    def test_merge_in_progress_skips_review(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        """When MERGE_HEAD exists, the hook must skip review and exit 0 even with a stub claude that would BLOCK."""
        git_dir = tmp_git_repo / ".git"
        (git_dir / "MERGE_HEAD").write_text("fakehash\n", encoding="utf-8")

        stub_dir = tmp_path / "stub"
        _make_stub_claude(stub_dir, "VERDICT: BLOCK\n\nWould block but should be skipped.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, _stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0


class TestDiffSizeCap:
    def test_oversized_diff_skips_with_warning(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        """A diff above DEVAI_DIFF_REVIEW_MAX_BYTES must be skipped."""
        big_file = tmp_git_repo / "big.txt"
        big_file.write_text("X" * 5000 + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "big.txt"], cwd=tmp_git_repo, check=True)

        stub_dir = tmp_path / "stub"
        _make_stub_claude(stub_dir, "VERDICT: BLOCK\n\nShould be skipped due to size cap.")
        env = {
            "PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "DEVAI_DIFF_REVIEW_MAX_BYTES": "100",
        }
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
        assert "skipping review" in stderr


class TestVerdictParsing:
    def test_verdict_pass_allows_silently(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_claude(stub_dir, "VERDICT: PASS\n\nAll clean.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
        assert "BLOCK" not in stderr

    def test_verdict_warn_allows_with_findings_on_stderr(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_claude(
            stub_dir,
            "VERDICT: WARN\n\nFound a console.log on line 12 of foo.js.",
        )
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
        assert "WARN" in stderr
        assert "console.log" in stderr

    def test_verdict_block_refuses_commit(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_claude(
            stub_dir,
            "VERDICT: BLOCK\n\nFound an AWS access key on line 42 of secrets.py.",
        )
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 1
        assert "BLOCK" in stderr
        assert "AWS access key" in stderr

    def test_unparseable_verdict_fails_open(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_claude(stub_dir, "I am Claude and I have many opinions.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
        assert "unparseable" in stderr.lower() or "warning" in stderr.lower()


class TestRebaseStateSkip:
    def test_rebase_in_progress_skips_review(
        self, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        git_dir = tmp_git_repo / ".git"
        (git_dir / "REBASE_HEAD").write_text("fakehash\n", encoding="utf-8")

        stub_dir = tmp_path / "stub"
        _make_stub_claude(stub_dir, "VERDICT: BLOCK\n\nShould skip during rebase.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, _stderr, code = _run_hook(tmp_git_repo, env)
        assert code == 0
