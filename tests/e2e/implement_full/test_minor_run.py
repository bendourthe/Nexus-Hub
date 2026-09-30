"""A two-plan minor run end to end on stand-ins (v4.13.6 T057, Definition of Done 8).

`minor_e2e.py` builds the fixture, lets the scripted stub agent take the first turn
(`/implement v0.5` and the exact approval paste), then drives the real runner
(`run_plan.py v0.5`) until `check-minor v0.5` is terminal. One module-scoped run
backs every assertion below, one test per item of Definition of Done 8:

1. an SSH-alias remote, verified through the stubbed `ssh -G`;
2. another session's merged but recently active branch and worktree, kept;
3. a squash-merged branch, removed without forcing;
4. a worktree holding a gitignored `.env`, kept, with the file untouched;
5. one gap migrated to the next minor, and the run still completing;
6. both releases;
7. the closing pull request;
8. the archive;
9. `check-minor` after the archive printing `MINOR COMPLETE`.

It proves the fixture, the checker, the executor, and the runner compose; it does
not measure a model. No network and no paid API are used.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "minor_e2e.py"
sys.path.insert(0, str(HERE))
import minor_e2e as m


class Run:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.root = Path(result["root"])
        self.work = Path(result["work"])
        self.mirror = Path(result["mirror"])

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.work), *args], capture_output=True, text=True,
                              check=True).stdout.strip()

    def mirror_git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "--git-dir", str(self.mirror), *args], capture_output=True, text=True,
                              check=False)

    def mirror_file(self, ref: str, rel: str) -> str | None:
        proc = self.mirror_git("show", f"{ref}:{rel}")
        return proc.stdout if proc.returncode == 0 else None

    def steps(self) -> list[dict]:
        return [json.loads(line) for line in (self.root / "minor-steps.jsonl").read_text(encoding="utf-8").splitlines()]

    def step(self, name: str) -> dict:
        found = [s for s in self.steps() if s["step"] == name]
        assert len(found) == 1, (name, [s["step"] for s in self.steps()])
        return found[0]

    def cleanup_lines(self) -> dict[str, str]:
        """{item: "REMOVE" or the KEEP check id} from the final cleanup pass."""
        verdicts = {}
        for line in self.step("cleanup")["stdout"].splitlines():
            action, _, rest = line.partition(" ")
            if action == "REMOVE":
                verdicts[rest] = "REMOVE"
            elif action == "KEEP":
                item, _, check = rest.rpartition(" ")
                verdicts[item] = check
        return verdicts

    def gh_state(self) -> dict:
        return json.loads((self.root / "gh-state.json").read_text(encoding="utf-8"))

    def gh_calls(self) -> list[list[str]]:
        return [json.loads(line) for line in (self.root / "gh.log").read_text(encoding="utf-8").splitlines()]

    def record(self) -> dict:
        runs = Path(self.result["runs"])
        records = [json.loads(p.read_text(encoding="utf-8")) for p in runs.glob("*.json")]
        found = [r for r in records if r.get("schema") == 2 and r.get("scope") == "minor"]
        assert len(found) == 1
        return found[0]


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory) -> Run:
    base = tmp_path_factory.mktemp("minor")
    empty = base / "empty.gitconfig"
    empty.write_text("", encoding="utf-8")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1")
    proc = subprocess.run([sys.executable, str(HARNESS), "--out", str(base / "out")], capture_output=True,
                          text=True, timeout=1800, env=env, check=False)
    assert proc.stdout.strip(), proc.stderr
    result = json.loads(proc.stdout)
    assert proc.returncode == 0, json.dumps(result, indent=2) + proc.stderr
    return Run(result)


def test_the_run_is_driven_by_the_runner_in_runbook_order(run: Run) -> None:
    assert run.result["first_turn_exit"] == 0
    assert run.result["runner_exit"] == 0
    assert run.result["cycles"] >= 2  # the runner resumed the session between members
    assert [s["step"] for s in run.steps()] == [
        "render", "record-create", "member-start v0.5.2", "member-start v0.5.10",
        "migrate", "archive", "cleanup", "check-minor",
    ]
    assert run.step("record-create")["stdout"].startswith("RECORDED minor v0.5 ")
    assert all(s["rc"] == 0 for s in run.steps())


def test_1_ssh_alias_remote_is_the_verified_route(run: Run) -> None:
    assert run.git("remote", "get-url", "origin") == m.SSH_URL
    assert run.git("remote", "get-url", "--push", "origin") == m.SSH_URL
    record = run.record()
    assert record["repo"] == "acme/demo"
    assert record["approvals"]["push_remote_url"] == m.SSH_URL
    lines = run.result["check_stdout"].splitlines()
    for version in ("v0.5.2", "v0.5.10"):
        assert f"{version}:approval.remote met" in lines


def test_2_other_sessions_recent_worktree_and_branch_are_kept(run: Run) -> None:
    other = Path(run.result["other_worktree"])
    verdicts = run.cleanup_lines()
    assert verdicts[f"worktree:{other.as_posix()}"] == "owned-by-run"
    assert verdicts[f"branch:{m.OTHER_BRANCH}"] == "checked-out"
    assert verdicts[f"remote:origin/{m.OTHER_BRANCH}"] == "checked-out"
    assert (other / ".git").exists()
    assert run.git("branch", "--list", m.OTHER_BRANCH)
    assert run.mirror_git("rev-parse", "--verify", "-q", f"refs/heads/{m.OTHER_BRANCH}").returncode == 0


def test_3_squash_merged_branch_is_removed_without_forcing(run: Run) -> None:
    verdicts = run.cleanup_lines()
    assert verdicts[f"branch:{m.SQUASH_BRANCH}"] == "REMOVE"
    assert verdicts[f"remote:origin/{m.SQUASH_BRANCH}"] == "REMOVE"
    assert not run.git("branch", "--list", m.SQUASH_BRANCH)
    assert run.mirror_git("rev-parse", "--verify", "-q", f"refs/heads/{m.SQUASH_BRANCH}").returncode != 0
    calls = [json.loads(line) for line in (run.root / "git.log").read_text(encoding="utf-8").splitlines()]
    assert any("update-ref" in c and f"refs/heads/{m.SQUASH_BRANCH}" in c for c in calls)
    for call in calls:
        assert "-D" not in call, call
        assert "--force" not in call, call  # `--force-with-lease=<ref>:<sha>` is a different token
        assert not ("worktree" in call and "-f" in call), call


def test_4_gitignored_env_file_is_never_deleted(run: Run) -> None:
    env_tree = Path(run.result["env_worktree"])
    verdicts = run.cleanup_lines()
    assert verdicts[f"worktree:{env_tree.as_posix()}"] == "ignored-not-allowlisted"
    assert verdicts[f"branch:{m.ENV_BRANCH}"] == "checked-out"
    assert (env_tree / ".env").read_text(encoding="utf-8") == m.ENV_TEXT


def test_5_one_gap_migrated_and_the_run_still_completes(run: Run) -> None:
    assert run.step("migrate")["stdout"].startswith("MIGRATED v0.5#WN-3 -> v0.6#WN-")
    target = run.mirror_file("refs/heads/develop", "docs/releases/v0/v0.6/known-gaps.md")
    assert target is not None and "**Migrated from**: v0.5#WN-3" in target
    source = run.mirror_file("refs/heads/develop", "docs/archives/v0/v0.5/known-gaps.md")
    assert source is not None
    assert "#### WN-3: The probe flakes on a cold cache - MIGRATED to v0.6.0" in source
    assert "**Open items**: 0" in source
    assert "gaps.minor met" in run.result["check_stdout"].splitlines()
    assert run.result["complete"] is True


def test_6_both_releases_are_published(run: Run) -> None:
    releases = run.gh_state()["releases"]
    for version in ("v0.5.2", "v0.5.10"):
        assert releases[version] == {"isDraft": False}
        assert run.mirror_git("merge-base", "--is-ancestor", f"refs/tags/{version}", "refs/heads/main").returncode == 0
        assert f"member.{version} met" in run.result["check_stdout"].splitlines()
    # The run retired each member's own merged branch.
    for branch in ("feat/v0.5.2-alpha", "feat/v0.5.10-omega"):
        assert run.mirror_git("rev-parse", "--verify", "-q", f"refs/heads/{branch}").returncode != 0


def test_7_one_closing_pull_request_is_merged_into_develop(run: Run) -> None:
    close = f"chore/close-{m.MINOR}"
    pr = run.gh_state()["prs"][close]
    assert pr["state"] == "MERGED" and pr["base"] == "develop"
    assert run.mirror_git("merge-base", "--is-ancestor", pr["merge_commit"], "refs/heads/develop").returncode == 0
    creates = [c for c in run.gh_calls() if c[:2] == ["pr", "create"] and close in c]
    assert len(creates) == 1
    assert "minor.close-pr met" in run.result["check_stdout"].splitlines()


def test_8_the_minor_is_archived_on_develop(run: Run) -> None:
    assert run.step("archive")["stdout"].startswith("ARCHIVED v0.5 docs/releases/v0/v0.5 -> docs/archives/v0/v0.5 ")
    tree = run.mirror_git("ls-tree", "-r", "--name-only", "refs/heads/develop").stdout.splitlines()
    assert "docs/archives/v0/v0.5/plans/v0.5.2-alpha.md" in tree
    assert "docs/archives/v0/v0.5/plans/v0.5.10-omega.md" in tree
    assert "docs/archives/v0/v0.5/development/v0.5-minor-close-evidence.md" in tree
    assert not any(path.startswith("docs/releases/v0/v0.5/") for path in tree)
    readme = run.mirror_file("refs/heads/develop", "README.md")
    assert readme is not None and "docs/archives/v0/v0.5/plans/v0.5.2-alpha.md" in readme  # link repaired
    assert "archive.minor met" in run.result["check_stdout"].splitlines()


def test_9_check_minor_after_the_archive_prints_minor_complete(run: Run) -> None:
    nonce = run.record()["nonce"]
    head = run.git("rev-parse", "HEAD")
    assert run.result["check_exit"] == 0
    assert run.result["verdict"] == f"MINOR COMPLETE v0.5 {head} {nonce}"
    assert run.result["runner_stdout"].splitlines()[-1] == run.result["verdict"]
    assert "cleanup.merged met" in run.result["check_stdout"].splitlines()
