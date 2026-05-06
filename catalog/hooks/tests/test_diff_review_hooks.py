"""
Smoke tests for the four platform-parallel pre-commit diff-review hooks:

    catalog/hooks/claude-diff-review.sh
    catalog/hooks/gemini-diff-review.sh
    catalog/hooks/codex-diff-review.sh
    catalog/hooks/opencode-diff-review.sh

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_diff_review_hooks.py -v

Each hook is bash and is independent of the others - it calls only its own CLI.
Tests stub the matching CLI by creating a fake binary on PATH that emits a
fixed response, then invoke the hook in a temporary git repo with a staged
diff. Every test is parametrized over all four (hook, cli) pairs so any
behavior change in one hook fails its row only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).parent.parent

# (hook filename, CLI binary name) for each platform variant.
_HOOK_VARIANTS = [
    ("claude-diff-review.sh", "claude"),
    ("gemini-diff-review.sh", "gemini"),
    ("codex-diff-review.sh", "codex"),
    ("opencode-diff-review.sh", "opencode"),
]
_VARIANT_IDS = [v[1] for v in _HOOK_VARIANTS]


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
    raise RuntimeError("bash not found on PATH; cannot run diff-review hook tests")


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


def _make_stub_cli(stub_dir: Path, cli_name: str, response: str) -> None:
    """Create a fake CLI binary in `stub_dir` that prints `response` and exits 0."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    sh_path = stub_dir / cli_name
    sh_path.write_text(
        "#!/usr/bin/env bash\ncat <<'EOF'\n" + response + "\nEOF\n",
        encoding="utf-8",
    )
    sh_path.chmod(0o755)


def _run_hook(
    hook_filename: str, repo: Path, env: dict[str, str] | None = None
) -> tuple[str, str, int]:
    """Run the hook from inside `repo`, returning (stdout, stderr, returncode)."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        [_BASH, str(_HOOKS_DIR / hook_filename)],
        cwd=repo,
        env=full_env,
        capture_output=True,
        text=True,
    )
    return result.stdout, result.stderr, result.returncode


# ── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestSyntax:
    def test_hook_parses_with_bash_n(self, hook: str, cli: str) -> None:
        """Each hook must be syntactically valid bash."""
        result = subprocess.run(
            [_BASH, "-n", str(_HOOKS_DIR / hook)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"bash -n failed for {hook}: {result.stderr}"


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestBypassEnvVar:
    def test_disable_env_var_short_circuits(
        self, hook: str, cli: str, tmp_git_repo: Path
    ) -> None:
        """DEVAI_DIFF_REVIEW_DISABLE=1 must exit 0 immediately for every variant."""
        env = {"DEVAI_DIFF_REVIEW_DISABLE": "1", "PATH": ""}
        _stdout, _stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestEmptyDiff:
    def test_no_staged_changes_exits_zero(
        self, hook: str, cli: str, tmp_git_repo: Path
    ) -> None:
        """With nothing staged, every hook must exit 0 silently."""
        # Unstage without HEAD (the fixture repo has no commits yet).
        subprocess.run(["git", "rm", "--cached", "hello.txt"], cwd=tmp_git_repo, check=True)
        env = {"PATH": os.environ.get("PATH", "")}
        _stdout, _stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestNoCli:
    def test_missing_cli_exits_zero_with_warning(
        self, hook: str, cli: str, tmp_git_repo: Path
    ) -> None:
        """When the matching CLI is absent from PATH, the hook must warn and allow."""
        git_path = shutil.which("git")
        assert git_path
        path_with_only_git = str(Path(git_path).parent)
        env = {"PATH": path_with_only_git}
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0
        # Each hook references its own CLI name in the warning.
        assert f"{cli} CLI not found" in stderr or f"{cli} cli not found" in stderr.lower()


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestMergeStateSkip:
    def test_merge_in_progress_skips_review(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        """When MERGE_HEAD exists, every hook must skip even with a stub CLI that would BLOCK."""
        git_dir = tmp_git_repo / ".git"
        (git_dir / "MERGE_HEAD").write_text("fakehash\n", encoding="utf-8")

        stub_dir = tmp_path / "stub"
        _make_stub_cli(stub_dir, cli, "VERDICT: BLOCK\n\nWould block but should be skipped.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, _stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestRebaseStateSkip:
    def test_rebase_in_progress_skips_review(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        git_dir = tmp_git_repo / ".git"
        (git_dir / "REBASE_HEAD").write_text("fakehash\n", encoding="utf-8")

        stub_dir = tmp_path / "stub"
        _make_stub_cli(stub_dir, cli, "VERDICT: BLOCK\n\nShould skip during rebase.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, _stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestDiffSizeCap:
    def test_oversized_diff_skips_with_warning(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        """A diff above DEVAI_DIFF_REVIEW_MAX_BYTES must be skipped for every variant."""
        big_file = tmp_git_repo / "big.txt"
        big_file.write_text("X" * 5000 + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "big.txt"], cwd=tmp_git_repo, check=True)

        stub_dir = tmp_path / "stub"
        _make_stub_cli(stub_dir, cli, "VERDICT: BLOCK\n\nShould be skipped due to size cap.")
        env = {
            "PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "DEVAI_DIFF_REVIEW_MAX_BYTES": "100",
        }
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0
        assert "skipping review" in stderr


@pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
class TestVerdictParsing:
    def test_verdict_pass_allows_silently(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_cli(stub_dir, cli, "VERDICT: PASS\n\nAll clean.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0
        assert "BLOCK" not in stderr

    def test_verdict_warn_allows_with_findings_on_stderr(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_cli(
            stub_dir, cli, "VERDICT: WARN\n\nFound a console.log on line 12 of foo.js."
        )
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0
        assert "WARN" in stderr
        assert "console.log" in stderr

    def test_verdict_block_refuses_commit(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_cli(
            stub_dir,
            cli,
            "VERDICT: BLOCK\n\nFound an AWS access key on line 42 of secrets.py.",
        )
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 1
        assert "BLOCK" in stderr
        assert "AWS access key" in stderr

    def test_unparseable_verdict_fails_open(
        self, hook: str, cli: str, tmp_git_repo: Path, tmp_path: Path
    ) -> None:
        stub_dir = tmp_path / "stub"
        _make_stub_cli(stub_dir, cli, "I am an AI and I have many opinions.")
        env = {"PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"}
        _stdout, stderr, code = _run_hook(hook, tmp_git_repo, env)
        assert code == 0
        assert "unparseable" in stderr.lower() or "warning" in stderr.lower()


# ── Independence test ──────────────────────────────────────────────────────


class TestPlatformIndependence:
    """Each hook must depend ONLY on its own CLI - never call any sibling CLI."""

    @pytest.mark.parametrize(("hook", "cli"), _HOOK_VARIANTS, ids=_VARIANT_IDS)
    def test_hook_does_not_reference_other_clis(self, hook: str, cli: str) -> None:
        """The hook source must not contain `command -v <other-cli>` or invoke other CLIs."""
        source = (_HOOKS_DIR / hook).read_text(encoding="utf-8")
        other_clis = {c for _, c in _HOOK_VARIANTS} - {cli}
        for other in other_clis:
            # Allow incidental mentions in comments (e.g., "Independent of the X variant"),
            # but no `command -v X` checks or `X -p` / `X exec` / `X run` invocations.
            assert f"command -v {other}" not in source, (
                f"{hook} must not check for {other} CLI"
            )
            assert f"\n{other} -p" not in source and f" {other} -p" not in source, (
                f"{hook} must not invoke {other} CLI"
            )
            assert f"$({other} " not in source, f"{hook} must not invoke {other} CLI"
