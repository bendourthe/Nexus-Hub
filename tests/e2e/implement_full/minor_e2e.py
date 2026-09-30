"""End-to-end harness for a minor-scope run (v4.13.6): `/implement v0.5` on stand-ins.

    python tests/e2e/implement_full/minor_e2e.py --out <dir>

One run = one fixture repository driven by the real runner (`run_plan.py v0.5`)
and the scripted stub agent (`stub_agent.py`, E2E_SCENARIO=minor) until
`check-minor v0.5` is terminal. No model is called and no network is used. The
fixture holds everything Definition of Done 8 names:

- origin is the SSH alias `git@github-work:acme/demo.git`; `ssh -G` is a stand-in
  that maps the alias to github.com, and git's transport alone is routed to a local
  bare mirror, so the checker verifies the alias route, never the mirror;
- two member plans, v0.5.2 and v0.5.10, and one open gap (v0.5#WN-3) the
  approval lists as migratable;
- `feat/v0.4.3-other`: merged, pushed an hour ago, checked out in a worktree that a
  live run record of another session names (must be kept);
- `feat/v0.4.1-squash`: squash-merged and idle for three days (must be removed
  without forcing);
- `feat/v0.4.2-env`: merged and idle, checked out in a worktree holding a gitignored
  `.env` (the worktree must be kept and the file never deleted);
- the stateful `gh` stand-in (gh_e2e.py), seeded with those three pull requests.

The JSON result names the run root; the test reads the repository, the mirror,
the stand-in state, and the stub's step log from there.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "gh_stub"))
from launcher import fixed_ssh_env, make_stub

SSH_URL = "git@github-work:acme/demo.git"
SSH_HOSTS = {"github-work": "github.com"}
MINOR = "v0.5"
V05 = "docs/releases/v0/v0.5"
OLD = time.time() - 3 * 24 * 3600
OTHER_BRANCH = "feat/v0.4.3-other"
SQUASH_BRANCH = "feat/v0.4.1-squash"
ENV_BRANCH = "feat/v0.4.2-env"
ENV_TEXT = "DEMO_SETTING=keep-me\n"
LINK_CHECKER = REPO / "catalog" / "skills" / "code-cleanup" / "docs-layout-refactor" / "scripts" / "link-baseline.py"
# Stripped from every child: any of them is a transport override the checker refuses to verify.
TRANSPORT_OVERRIDES = ("GIT_SSH", "GIT_SSH_COMMAND", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT", "GH_HOST",
                       "http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                       "NEXUS_RUNNER_LAUNCH")


def _plan(version: str, slug: str) -> str:
    return (
        f"# Plan -- {slug}\n\n**Version**: {version}\n**Slug**: {slug}\n**Status**: queued\n\n"
        f"**Goal**: ship the {slug} part.\n\n## Phase 1: Build\n\n- [ ] T001 Build part src/{slug}.txt\n"
    )


GAPS = (
    "# Known Gaps - v0.5\n\n**Project**: demo\n**Status**: finalized\n**Last updated**: 2026-09-01\n\n"
    "## v0.5.2\n\n### Summary\n\n| Category | Open | Resolved |\n|---|---|---|\n"
    "| Bugs / regressions (BG) | 0 | 0 |\n| Warnings (WN) | 1 | 0 |\n\n### Open Items\n\n"
    "#### WN-3: The probe flakes on a cold cache\n\n"
    "- **Source phase**: Phase 2\n- **Plan reference**: [plan](plans/v0.5.2-alpha.md)\n"
    "- **Reason**: vendor API missing\n- **Suggested next step**: wait for the vendor\n\n"
    "### Resolved\n\n| ID | Title | Resolved in | Notes |\n|---|---|---|---|\n"
)


class Fixture:
    """The repository, its bare mirror, and the seeded host state."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.mirror = root / "remote.git"
        self.work = root / "work"
        self.runs = root / "home" / ".nexus-hub" / "runs"
        self.state: dict = {"prs": {}, "releases": {}, "activity": {}}
        self.old = dict(os.environ, GIT_AUTHOR_DATE=f"{int(OLD)} +0000", GIT_COMMITTER_DATE=f"{int(OLD)} +0000")

    def git(self, cwd: Path, *args: str, old: bool = True) -> str:
        proc = subprocess.run(["git", *args], cwd=cwd, env=self.old if old else None, capture_output=True,
                              text=True, check=True)
        return proc.stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def commit(self, message: str, old: bool = True) -> None:
        self.git(self.work, "add", "-A", old=old)
        self.git(self.work, "commit", "-q", "-m", message, old=old)

    def merged_branch(self, name: str, *, squash: bool = False, old: bool = True) -> str:
        """A branch off develop with one commit, pushed, merged into develop, with its merged pull request."""
        self.git(self.work, "checkout", "-q", "-b", name, "develop", old=old)
        self.write(f"work/{name.replace('/', '_')}.txt", name + "\n")
        self.commit("work " + name, old=old)
        tip = self.git(self.work, "rev-parse", "HEAD")
        self.git(self.work, "push", "-q", "origin", name, old=old)
        self.git(self.work, "checkout", "-q", "develop", old=old)
        if squash:
            self.git(self.work, "merge", "-q", "--squash", name, old=old)
            self.commit("squash " + name, old=old)
        else:
            self.git(self.work, "merge", "-q", "--no-ff", "-m", "merge " + name, name, old=old)
        self.git(self.work, "push", "-q", "origin", "develop", old=old)
        self.state["prs"][name] = {"number": len(self.state["prs"]) + 1, "state": "MERGED", "base": "develop",
                                   "head": tip, "merge_commit": self.git(self.work, "rev-parse", "HEAD")}
        when = dt.datetime.fromtimestamp(OLD if old else time.time() - 3600, dt.timezone.utc)
        self.state["activity"][name] = [when.isoformat().replace("+00:00", "Z")]
        return tip

    def worktree(self, name: str, directory: str, old: bool = True) -> Path:
        path = self.root / directory
        self.git(self.work, "worktree", "add", "-q", str(path), name, old=old)
        return path


def age(path: Path) -> None:
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in [*files, *dirs]:
            os.utime(Path(root) / name, (OLD, OLD))


def build_fixture(root: Path) -> Fixture:
    fx = Fixture(root)
    fx.runs.mkdir(parents=True)
    fx.git(root, "init", "--bare", "-q", "-b", "main", str(fx.mirror))
    fx.work.mkdir()
    fx.git(fx.work, "init", "-q", "-b", "main")
    # A deep temporary directory otherwise exceeds Windows' 260-character path limit
    # inside the mirror's incoming-object directory; the setting is ignored elsewhere.
    fx.git(root, "--git-dir", str(fx.mirror), "config", "core.longpaths", "true")
    fx.git(fx.work, "config", "core.longpaths", "true")
    fx.git(fx.work, "config", "user.email", "e2e@example.invalid")
    fx.git(fx.work, "config", "user.name", "E2E")
    # Built through the mirror's path; origin is switched to the SSH alias at the end.
    fx.git(fx.work, "remote", "add", "origin", str(fx.mirror))
    files = {
        f"{V05}/plans/v0.5.2-alpha.md": _plan("v0.5.2", "alpha"),
        f"{V05}/plans/v0.5.10-omega.md": _plan("v0.5.10", "omega"),
        f"{V05}/known-gaps.md": GAPS,
        ".gitignore": ".env\n",
        "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n",
        "README.md": "# Demo\n\nSee the [v0.5 plans](docs/releases/v0/v0.5/plans/v0.5.2-alpha.md).\n",
    }
    for rel, text in files.items():
        fx.write(rel, text)
    fx.commit("start")
    fx.git(fx.work, "push", "-q", "origin", "main")
    fx.git(fx.work, "branch", "develop")
    fx.git(fx.work, "push", "-q", "origin", "develop")
    fx.merged_branch(SQUASH_BRANCH, squash=True)
    fx.merged_branch(ENV_BRANCH)
    env_tree = fx.worktree(ENV_BRANCH, "env-wt")
    (env_tree / ".env").write_text(ENV_TEXT, encoding="utf-8")
    age(env_tree)
    fx.merged_branch(OTHER_BRANCH, old=False)
    other_tree = fx.worktree(OTHER_BRANCH, "other-wt", old=False)
    # Another session's live per-plan run record names that branch and worktree.
    other = {"schema": 1, "repo_root": str(fx.work), "repo": "acme/demo", "session_id": "other-session",
             "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "plan": "docs/releases/v0/v0.4/plans/v0.4.3-other.md", "source_branch": OTHER_BRANCH,
             "worktree": str(other_tree)}
    (fx.runs / "other-session-run.json").write_text(json.dumps(other), encoding="utf-8")
    fx.git(fx.work, "remote", "set-url", "origin", SSH_URL)
    (root / "gh-state.json").write_text(json.dumps(fx.state), encoding="utf-8")
    return fx


def _stub_bin(bin_dir: Path, name: str, target: Path) -> Path:
    copy = bin_dir / f"_{target.name}"
    shutil.copyfile(target, copy)
    return make_stub(bin_dir, name, copy, sys.executable)


def run(out: Path, max_cycles: int) -> dict:
    root = out / f"minor-{time.strftime('%Y%m%d-%H%M%S')}"
    root.mkdir(parents=True)
    fx = build_fixture(root)
    bin_dir = root / "bin"
    bin_dir.mkdir()
    stubs = {
        name: _stub_bin(bin_dir, name, HERE / script)
        for name, script in (("gh", "gh_e2e.py"), ("git", "git_e2e.py"), ("claude", "stub_agent.py"),
                             ("ssh", "ssh_e2e.py"))
    }
    real_git = shutil.which("git")
    assert real_git is not None, "git is required by the fixture"
    env = {k: v for k, v in os.environ.items() if k not in TRANSPORT_OVERRIDES}
    env.update(
        PATH=str(bin_dir) + os.pathsep + env.get("PATH", ""),
        GH_E2E_STATE=str(root / "gh-state.json"),
        GH_E2E_LOG=str(root / "gh.log"),
        NEXUS_HUB_RUNS_DIR=str(fx.runs),
        E2E_SCENARIO="minor",
        E2E_CHECKER=str(REPO / "scripts" / "check_plan_completion.py"),
        E2E_MINOR_LOG=str(root / "minor-steps.jsonl"),
        E2E_GIT_LOG=str(root / "git.log"),
        E2E_LINK_CHECKER=str(LINK_CHECKER),
        E2E_REAL_GIT=real_git,
        E2E_STUB_REMOTE_MIRROR=str(fx.mirror),
        E2E_STUB_REMOTE_URLS=SSH_URL,
        SSH_E2E_HOSTS=json.dumps(SSH_HOSTS),
        # Every checker, gate, and runner child resolves the ssh stand-in as git's ssh,
        # whichever ssh the host's git shell would prefer (see fixed_ssh/sitecustomize.py).
        **fixed_ssh_env(stubs["ssh"], env),
        NEXUS_RUNNER_BACKOFF="0",
        GH_PROMPT_DISABLED="1",
        GIT_TERMINAL_PROMPT="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    sys.path.insert(0, str(REPO / "scripts"))
    import run_plan

    first = run_plan.TEMPLATES["claude"][0](f"/implement {MINOR}")
    first[0] = shutil.which(first[0], path=env["PATH"]) or first[0]
    started = time.monotonic()
    first_proc = subprocess.run(first, cwd=fx.work, env=env, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=900, check=False)
    (root / "first-turn.out").write_text(first_proc.stdout + "\n--- stderr ---\n" + first_proc.stderr,
                                         encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_plan.py"), MINOR, "--platform", "claude",
         "--max-cycles", str(max_cycles)],
        cwd=fx.work, env=env, capture_output=True, text=True, timeout=3600, check=False,
    )
    (root / "runner.out").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    check = subprocess.run([sys.executable, env["E2E_CHECKER"], "check-minor", MINOR], cwd=fx.work, env=env,
                           capture_output=True, text=True, check=False, timeout=600)
    verdict = check.stdout.splitlines()[0] if check.stdout else ""
    return {
        "root": str(root),
        "work": str(fx.work),
        "mirror": str(fx.mirror),
        "runs": str(fx.runs),
        "env_worktree": str(root / "env-wt"),
        "other_worktree": str(root / "other-wt"),
        "first_turn_exit": first_proc.returncode,
        "runner_exit": proc.returncode,
        "runner_stdout": proc.stdout.strip()[-400:],
        "runner_stderr_tail": proc.stderr.strip()[-800:],
        "cycles": sum(1 for line in proc.stderr.splitlines() if line.startswith("cycle ")),
        "check_exit": check.returncode,
        "verdict": verdict,
        "check_stdout": check.stdout,
        "complete": verdict.startswith(f"MINOR COMPLETE {MINOR} "),
        "seconds": round(time.monotonic() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-cycles", type=int, default=6)
    args = parser.parse_args()
    result = run(Path(args.out).resolve(), args.max_cycles)
    print(json.dumps(result, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
