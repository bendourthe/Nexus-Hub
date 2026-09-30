"""Adversarial tests for scripts/cleanup_merged.py, the merged-and-idle cleanup executor.

Every case drives real git repositories: a working clone whose `origin` URL names
`https://github.com/acme/demo.git` (so the push route verifies) and a bare local
repository that the test runner routes pushes, fetches, and `ls-remote` to. The
`gh` stand-in (tests/fixtures/gh_stub/) answers pull requests, protected branches,
the default branch, and repository activity. The runner is instrumented in process,
so every git argv the executor issues is recorded, and each test asserts that none
contains `-D`, a bare `--force`, or `worktree remove --force`.

Idle time is controlled with `GIT_COMMITTER_DATE` (reflog entries take the
committer date) and `os.utime` (worktree files), both three days in the past,
while "pushed one hour ago" comes from the stand-in's activity answer.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT / "tests" / "fixtures" / "gh_stub"))
from launcher import gh_stub_dir

# A real executable `gh` stand-in: the resolver never runs a Windows .cmd or .bat.
GH_STUB = gh_stub_dir()
URL = "https://github.com/acme/demo.git"
OLD = time.time() - 3 * 24 * 3600
OLD_ISO = dt.datetime.fromtimestamp(OLD, dt.timezone.utc).isoformat().replace("+00:00", "Z")

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="drives real git repositories")

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import check_plan_completion as ck
import cleanup_merged as cm

REAL_EXEC = cm._exec


def _subcommand(argv: list[str]) -> str:
    index = 1
    while index < len(argv) and argv[index] in ("-C", "-c"):
        index += 2
    return argv[index] if index < len(argv) else ""


class Fixture:
    """A working clone, its bare remote, the gh stand-in state, and the recorded argv."""

    def __init__(self, tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.tmp = tmp
        self.bare = tmp / "remote.git"
        self.work = tmp / "work"
        self.runs = tmp / "runs"
        self.state_file = tmp / "gh_state.json"
        self.argv: list[list[str]] = []
        self.before: list[tuple[Callable[[list[str]], bool], Callable[[], None]]] = []
        self.state: dict = {"prs": [], "protected": [], "default_branch": "main", "activity": {}}
        empty = tmp / "gitconfig"
        empty.write_text("", encoding="utf-8")
        monkeypatch.setenv("PATH", str(GH_STUB) + os.pathsep + os.environ.get("PATH", ""))
        monkeypatch.setenv("GH_STUB_STATE", str(self.state_file))
        monkeypatch.setenv("GH_STUB_PYTHON", sys.executable)
        monkeypatch.setenv("NEXUS_HUB_RUNS_DIR", str(self.runs))
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
        monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
        for name in ("GH_HOST", "GIT_SSH", "GIT_SSH_COMMAND", "GIT_SSL_NO_VERIFY", "SSL_CERT_FILE"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(cm, "_exec", self.exec)
        self.env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com",
                        GIT_AUTHOR_DATE=f"{int(OLD)} +0000", GIT_COMMITTER_DATE=f"{int(OLD)} +0000")
        self.git(tmp, "init", "-q", "--bare", "-b", "main", str(self.bare))
        self.git(tmp, "init", "-q", "-b", "main", str(self.work))
        (self.work / ".gitignore").write_text(".env\nnode_modules/\n", encoding="utf-8")
        (self.work / "README.md").write_text("demo\n", encoding="utf-8")
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-qm", "init")
        self.git(self.work, "remote", "add", "origin", URL)
        self.push("main")
        self.git(self.work, "checkout", "-q", "-b", "develop")
        self.push("develop")
        self.save()

    # ---------------------------------------------------------------- plumbing

    def route(self, argv: list[str]) -> list[str]:
        if _subcommand(argv) in ("push", "fetch", "ls-remote"):
            return [argv[0], "-c", f"url.{self.bare.as_uri()}.insteadOf={URL}", *argv[1:]]
        return argv

    def exec(self, argv: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
        self.argv.append(list(argv))
        for match, action in list(self.before):
            if match(argv):
                action()
        return REAL_EXEC(self.route(argv), cwd)

    def git(self, cwd: Path, *args: str, recent: bool = False) -> str:
        env = dict(self.env)
        if recent:
            for key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
                env.pop(key)
        argv = self.route(["git", "-C", str(cwd), *args])
        proc = subprocess.run(argv, env=env, capture_output=True, text=True, check=True, timeout=60)
        return proc.stdout.strip()

    def push(self, branch: str, cwd: Path | None = None) -> None:
        self.git(cwd or self.work, "push", "-q", "origin", f"refs/heads/{branch}:refs/heads/{branch}")

    def sha(self, ref: str, cwd: Path | None = None) -> str:
        return self.git(cwd or self.work, "rev-parse", ref)

    def remote_sha(self, branch: str) -> str:
        return self.git(self.tmp, "--git-dir", str(self.bare), "rev-parse", "--verify", "-q",
                        f"refs/heads/{branch}") if self.remote_has(branch) else ""

    def remote_has(self, branch: str) -> bool:
        out = subprocess.run(["git", "--git-dir", str(self.bare), "for-each-ref", "--format=%(refname)",
                              f"refs/heads/{branch}"], capture_output=True, text=True, check=True).stdout
        return f"refs/heads/{branch}" in out.split()

    def local_has(self, branch: str) -> bool:
        return f"refs/heads/{branch}" in self.git(self.work, "for-each-ref", "--format=%(refname)",
                                                  f"refs/heads/{branch}").split()

    def save(self) -> None:
        self.state_file.write_text(json.dumps(self.state), encoding="utf-8")

    def pr(self, branch: str, sha: str, state: str = "MERGED", cross: bool = False, base: str = "develop") -> None:
        self.state["prs"].append({"number": len(self.state["prs"]) + 1, "headRefName": branch,
                                  "headRefOid": sha, "baseRefName": base, "state": state,
                                  "isCrossRepository": cross})
        self.state["activity"].setdefault(branch, [OLD_ISO])
        self.save()

    def age(self, path: Path) -> None:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d != ".git"]
            for name in [*files, *dirs]:
                if name != ".git":
                    os.utime(Path(root) / name, (OLD, OLD))

    # ---------------------------------------------------------------- scenarios

    def branch(self, name: str, *, merge: str = "merge", push: bool = True, pr: bool = True,
               recent: bool = False) -> str:
        """A feature branch off develop with one commit; merged into develop and pushed."""
        self.git(self.work, "checkout", "-q", "-b", name, "develop", recent=recent)
        (self.work / f"{name.replace('/', '_')}.txt").write_text(name + "\n", encoding="utf-8")
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-qm", "work " + name, recent=recent)
        tip = self.sha("HEAD")
        if push:
            self.push(name)
        self.git(self.work, "checkout", "-q", "develop")
        if merge == "merge":
            self.git(self.work, "merge", "-q", "--no-ff", "-m", "merge " + name, name)
        elif merge == "squash":
            self.git(self.work, "merge", "-q", "--squash", name)
            self.git(self.work, "commit", "-qm", "squash " + name)
        self.push("develop")
        if pr:
            self.pr(name, tip)
        return tip

    def worktree(self, name: str, directory: str | None = None) -> Path:
        """A merged branch checked out in its own worktree, every file aged."""
        self.branch(name)
        path = self.tmp / (directory or name.replace("/", "_"))
        self.git(self.work, "worktree", "add", "-q", str(path), name)
        self.age(path)
        return path

    def live_record(self, **names: object) -> Path:
        self.runs.mkdir(exist_ok=True)
        record = {"schema": 1, "repo_root": str(self.work),
                  "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **names}
        path = self.runs / (hashlib.sha256(json.dumps(names).encode()).hexdigest() + ".json")
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def run(self, *args: str, capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, tuple[str, str]], str]:
        capsys.readouterr()
        code = cm.main(["--repo", str(self.work), *args])
        out = capsys.readouterr().out
        verdicts = {}
        for line in out.splitlines():
            if line.startswith(("REMOVE ", "KEEP ")):
                action, rest = line.split(" ", 1)
                if action == "REMOVE":
                    verdicts[rest] = ("REMOVE", "")
                else:
                    item, _, check = rest.rpartition(" ")
                    if item.endswith(" " + cm.REMOVAL_FAILED):
                        item, check = item[: -len(cm.REMOVAL_FAILED) - 1], cm.REMOVAL_FAILED + " " + check
                    verdicts[item] = ("KEEP", check)
        return code, verdicts, out

    def assert_no_forcing(self) -> None:
        for argv in self.argv:
            if Path(argv[0]).stem.lower() != "git":
                continue
            assert "-D" not in argv, argv
            assert not any(a == "--force" or (a.startswith("--force") and not a.startswith("--force-with-lease"))
                           for a in argv), argv
            if _subcommand(argv) == "worktree" and "remove" in argv:
                assert "-f" not in argv and "--force" not in argv, argv


@pytest.fixture
def fx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    fixture = Fixture(tmp_path, monkeypatch)
    yield fixture
    fixture.assert_no_forcing()


# --------------------------------------------------------------------------- the nine-item fixture


def test_nine_item_fixture_removes_only_the_verified_items(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/merged")
    moved = fx.branch("feat/moved")
    fx.git(fx.work, "checkout", "-q", "feat/moved")
    (fx.work / "late.txt").write_text("late\n", encoding="utf-8")
    fx.git(fx.work, "add", "-A")
    fx.git(fx.work, "commit", "-qm", "after merge")
    fx.push("feat/moved")
    fx.git(fx.work, "checkout", "-q", "develop")
    fx.git(fx.work, "update-ref", "refs/heads/feat/moved", moved)
    fx.branch("feat/squash", merge="squash")
    fx.branch("feat/ahead")
    fx.git(fx.work, "checkout", "-q", "feat/ahead")
    (fx.work / "more.txt").write_text("more\n", encoding="utf-8")
    fx.git(fx.work, "add", "-A")
    fx.git(fx.work, "commit", "-qm", "local only")
    fx.git(fx.work, "checkout", "-q", "develop")
    fx.git(fx.work, "branch", "feat/empty", "develop")
    untracked = fx.worktree("feat/wt-untracked")
    (untracked / "notes.txt").write_text("mine\n", encoding="utf-8")
    fx.age(untracked)
    env_tree = fx.worktree("feat/wt-env")
    (env_tree / ".env").write_text("SECRET=1\n", encoding="utf-8")
    fx.age(env_tree)
    owned = fx.worktree("feat/wt-owned")
    fx.live_record(worktree=str(owned))
    fx.branch("feat/recent")
    fx.state["activity"]["feat/recent"] = [
        (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z")]
    fx.save()

    code, verdicts, out = fx.run("--apply", capsys=capsys)

    assert code == 0, out
    removed = {k for k, (action, _) in verdicts.items() if action == "REMOVE"}
    assert removed == {"branch:feat/merged", "branch:feat/squash", "remote:origin/feat/merged",
                       "remote:origin/feat/squash"}
    expected = {
        "branch:feat/moved": "head-mismatch", "remote:origin/feat/moved": "head-mismatch",
        "branch:feat/ahead": "local-ahead", "remote:origin/feat/ahead": "local-ahead",
        "branch:feat/empty": "no-merged-pr",
        f"worktree:{untracked.as_posix()}": "untracked",
        f"worktree:{env_tree.as_posix()}": "ignored-not-allowlisted",
        f"worktree:{owned.as_posix()}": "owned-by-run",
        "branch:feat/recent": "recently-active", "remote:origin/feat/recent": "recently-active",
        "branch:develop": "protected", "branch:main": "protected",
        "branch:feat/wt-untracked": "checked-out", "remote:origin/feat/wt-untracked": "checked-out",
    }
    for item, check in expected.items():
        assert verdicts.get(item) == ("KEEP", check), (item, out)
    assert (env_tree / ".env").read_text(encoding="utf-8") == "SECRET=1\n"
    assert not fx.local_has("feat/merged") and not fx.remote_has("feat/merged")
    assert not fx.local_has("feat/squash") and not fx.remote_has("feat/squash")
    assert fx.local_has("feat/moved") and fx.remote_has("feat/moved")
    squash_delete = [a for a in fx.argv if _subcommand(a) == "update-ref" and "refs/heads/feat/squash" in a]
    assert squash_delete and squash_delete[0][-1] == fx.state["prs"][2]["headRefOid"]


def test_dry_run_is_the_default_and_removes_nothing(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/merged")
    code, verdicts, _ = fx.run(capsys=capsys)
    assert code == 0
    assert verdicts["branch:feat/merged"] == ("REMOVE", "")
    assert fx.local_has("feat/merged") and fx.remote_has("feat/merged")
    assert not any(_subcommand(a) in ("push", "update-ref") or "remove" in a for a in fx.argv)


# --------------------------------------------------------------------------- all passing


def test_all_checks_pass_removes_worktree_branch_and_remote(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    path = fx.worktree("feat/done")
    (path / "node_modules" / "pkg").mkdir(parents=True)
    (path / "node_modules" / "pkg" / "index.js").write_text("x\n", encoding="utf-8")
    fx.age(path)
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 0, out
    for item in (f"worktree:{path.as_posix()}", "branch:feat/done", "remote:origin/feat/done"):
        assert verdicts[item] == ("REMOVE", ""), out
    assert not path.exists()
    assert not fx.local_has("feat/done") and not fx.remote_has("feat/done")
    assert any(_subcommand(a) == "worktree" and "prune" in a for a in fx.argv)


# --------------------------------------------------------------------------- each check failing alone


def _mutate_protected(fx: Fixture) -> None:
    fx.state["protected"] = ["feat/x"]
    fx.save()


def _mutate_default(fx: Fixture) -> None:
    fx.state["default_branch"] = "feat/x"
    fx.save()


def _mutate_open(fx: Fixture) -> None:
    fx.pr("feat/x", fx.sha("feat/x"), state="OPEN")


def _mutate_no_pr(fx: Fixture) -> None:
    fx.state["prs"] = []
    fx.save()


def _mutate_closed(fx: Fixture) -> None:
    fx.state["prs"][0]["state"] = "CLOSED"
    fx.save()


def _mutate_cross(fx: Fixture) -> None:
    fx.state["prs"][0]["isCrossRepository"] = True
    fx.save()


def _mutate_idle_unknown(fx: Fixture) -> None:
    fx.state["activity"]["feat/x"] = []
    fx.save()


def _mutate_recent_push(fx: Fixture) -> None:
    fx.state["activity"]["feat/x"] = [dt.datetime.now(dt.timezone.utc).isoformat()]
    fx.save()


def _mutate_prs_fail(fx: Fixture) -> None:
    fx.state["prs_fail"] = True
    fx.save()


def _mutate_api_fail(fx: Fixture) -> None:
    fx.state["api_fail"] = True
    fx.save()


def _mutate_owned_branch(fx: Fixture) -> None:
    fx.live_record(approvals={"source_branch": "feat/x"})


def _mutate_lock_owned(fx: Fixture) -> None:
    record = fx.live_record(approvals={"source_branch": "feat/x"})
    data = json.loads(record.read_text(encoding="utf-8"))
    data["created"] = "2020-01-01T00:00:00+00:00"  # stale record ...
    record.write_text(json.dumps(data), encoding="utf-8")
    record.with_name(record.stem + ".runner.lock").write_text("", encoding="utf-8")  # ... held by a live runner


def _mutate_head_mismatch(fx: Fixture) -> None:
    fx.state["prs"][0]["headRefOid"] = fx.sha("develop")
    fx.save()


BRANCH_CASES = {
    "protected": (_mutate_protected, "protected"),
    "default-branch": (_mutate_default, "protected"),
    "open-pr": (_mutate_open, "open-pr"),
    "no-pr": (_mutate_no_pr, "no-merged-pr"),
    "closed-unmerged": (_mutate_closed, "no-merged-pr"),
    "cross-repository": (_mutate_cross, "no-merged-pr"),
    "head-mismatch": (_mutate_head_mismatch, "head-mismatch"),
    "idle-unknown": (_mutate_idle_unknown, "idle-unknown"),
    "recent-push": (_mutate_recent_push, "recently-active"),
    "pr-list-fails": (_mutate_prs_fail, "gh-unavailable"),
    "api-fails": (_mutate_api_fail, "gh-unavailable"),
    "owned-by-record": (_mutate_owned_branch, "owned-by-run"),
    "owned-by-runner-lock": (_mutate_lock_owned, "owned-by-run"),
}


@pytest.mark.parametrize("case", sorted(BRANCH_CASES))
def test_each_branch_check_failing_alone_keeps_the_branch(
    case: str, fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/x")
    mutate, check = BRANCH_CASES[case]
    mutate(fx)
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 0, out
    assert verdicts["branch:feat/x"] == ("KEEP", check), out
    assert verdicts["remote:origin/feat/x"] == ("KEEP", check), out
    assert fx.local_has("feat/x") and fx.remote_has("feat/x")


def test_recent_local_reflog_keeps_the_branch(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x", recent=True)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/x"] == ("KEEP", "recently-active"), out
    assert fx.local_has("feat/x")


def test_a_truncated_pull_request_list_falls_back_to_per_branch_queries(
    fx: Fixture, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADV-3: a repository with PR_LIMIT or more merged pull requests must still clean up.

    The bulk list is a full page here (two unrelated merged pull requests at a
    limit of 2), which previously made every item unknown for good.
    """
    fx.branch("feat/merged")
    fx.pr("old/one", "0" * 40)
    fx.pr("old/two", "1" * 40)
    monkeypatch.setattr(cm, "PR_LIMIT", 2)
    code, verdicts, out = fx.run(capsys=capsys)
    assert code == 0, out
    assert verdicts["branch:feat/merged"] == ("REMOVE", ""), out
    assert any("--head=feat/merged" in a for a in fx.argv)


def test_missing_gh_keeps_everything(fx: Fixture, capsys: pytest.CaptureFixture[str],
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    fx.branch("feat/x")
    real = cm.repo_host.absolute_tool
    monkeypatch.setattr(cm.repo_host, "absolute_tool", lambda name, root: None if name == "gh" else real(name, root))
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/x"] == ("KEEP", "gh-unavailable"), out
    assert fx.local_has("feat/x") and fx.remote_has("feat/x")


def test_unreadable_remote_keeps_everything(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    shutil.move(str(fx.bare), str(fx.tmp / "gone.git"))
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/x"] == ("KEEP", "remote-unreadable"), out
    assert fx.local_has("feat/x")


WORKTREE_CASES = ("dirty", "untracked", "ignored-not-allowlisted", "locked", "missing", "owned-by-run",
                  "recently-active")


@pytest.mark.parametrize("case", WORKTREE_CASES)
def test_each_worktree_check_failing_alone_keeps_the_worktree(
    case: str, fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    path = fx.worktree("feat/w")
    if case == "dirty":
        (path / "README.md").write_text("changed\n", encoding="utf-8")
    elif case == "untracked":
        (path / "new.txt").write_text("n\n", encoding="utf-8")
    elif case == "ignored-not-allowlisted":
        (path / ".env").write_text("K=V\n", encoding="utf-8")
    elif case == "locked":
        fx.git(fx.work, "worktree", "lock", str(path))
    elif case == "missing":
        shutil.rmtree(path)
    elif case == "owned-by-run":
        fx.live_record(worktree=str(path))
    if case != "missing":
        fx.age(path)
    if case == "recently-active":
        os.utime(path / "README.md", None)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", case), out
    assert verdicts["branch:feat/w"] == ("KEEP", "checked-out"), out
    assert verdicts["remote:origin/feat/w"] == ("KEEP", "checked-out"), out
    if case != "missing":
        assert path.is_dir()
        if case == "ignored-not-allowlisted":
            assert (path / ".env").read_text(encoding="utf-8") == "K=V\n"


def test_detached_worktree_is_kept(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/d")
    path = fx.tmp / "detached"
    fx.git(fx.work, "worktree", "add", "-q", "--detach", str(path), "feat/d")
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "detached"), out
    assert path.is_dir()


def test_current_worktree_is_kept(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    path = fx.worktree("feat/here")
    capsys.readouterr()
    cm.main(["--repo", str(path), "--apply"])
    out = capsys.readouterr().out
    assert f"KEEP worktree:{path.as_posix()} current-worktree" in out.splitlines()
    assert path.is_dir()


# --------------------------------------------------------------------------- races and failures


def test_remote_tip_moving_after_the_reread_is_refused_by_the_lease(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/race")
    other = fx.tmp / "other"
    fx.git(fx.tmp, "clone", "-q", "-b", "feat/race", str(fx.bare), str(other))
    fx.git(other, "remote", "set-url", "origin", URL)

    def advance() -> None:
        (other / "race.txt").write_text("r\n", encoding="utf-8")
        fx.git(other, "add", "-A")
        fx.git(other, "commit", "-qm", "pushed during cleanup")
        fx.git(other, "push", "-q", "origin", "feat/race")

    fx.before.append((lambda a: _subcommand(a) == "push" and "--delete" in a, advance))
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 1, out
    assert verdicts["remote:origin/feat/race"] == ("KEEP", "removal-failed push-refused"), out
    assert fx.remote_sha("feat/race") == fx.sha("HEAD", cwd=other)
    assert verdicts["branch:feat/race"] == ("REMOVE", ""), out


def test_a_removal_failure_mid_pass_continues_and_reports(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/a")
    fx.branch("feat/b")

    def move() -> None:
        fx.git(fx.work, "update-ref", "refs/heads/feat/a", fx.sha("develop"))

    fx.before.append((lambda a: _subcommand(a) == "update-ref" and "refs/heads/feat/a" in a, move))
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 1, out
    assert verdicts["branch:feat/a"] == ("KEEP", "removal-failed ref-changed"), out
    assert verdicts["branch:feat/b"] == ("REMOVE", ""), out
    assert fx.local_has("feat/a") and not fx.local_has("feat/b")


def test_state_change_before_removal_is_caught_by_the_reread(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/a")
    fx.branch("feat/b")

    def open_pr() -> None:
        if not any(p["headRefName"] == "feat/b" and p["state"] == "OPEN" for p in fx.state["prs"]):
            fx.pr("feat/b", fx.sha("feat/b"), state="OPEN")

    # The first removal happens after the whole dry evaluation, so an OPEN pull request
    # opened then must be seen by feat/b's re-read.
    fx.before.append((lambda a: _subcommand(a) == "update-ref", open_pr))
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/b"] == ("KEEP", "open-pr"), out
    assert fx.local_has("feat/b")


def test_a_second_concurrent_run_exits_3(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    host = cm.Host(fx.work, "develop")
    lock = cm._lock_path(host)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("{}", encoding="utf-8")
    code, _verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 3
    assert out.splitlines()[0] == "BLOCKED: cleanup-running"
    assert fx.local_has("feat/x") and fx.remote_has("feat/x")
    os.utime(lock, (OLD, OLD))  # a stale lock is replaced
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 0 and verdicts["branch:feat/x"] == ("REMOVE", ""), out
    assert not lock.exists()


def test_fork_with_two_remotes_never_touches_the_other_remote(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    fx.git(fx.work, "remote", "add", "upstream", "https://github.com/other/demo.git")
    fx.git(fx.work, "update-ref", "refs/remotes/upstream/feat/x", fx.sha("feat/x"))
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["remote:upstream/feat/x"] == ("KEEP", "remote-mismatch"), out
    assert not any(_subcommand(a) == "push" and "upstream" in a for a in fx.argv)
    assert verdicts["remote:origin/feat/x"] == ("REMOVE", ""), out


def test_push_route_to_another_remote_is_refused(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    fx.git(fx.work, "remote", "add", "upstream", "https://github.com/other/demo.git")
    fx.git(fx.work, "config", "remote.pushDefault", "upstream")
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["remote:origin/feat/x"] == ("KEEP", "remote-mismatch"), out
    assert fx.remote_has("feat/x")


def test_names_with_spaces_and_leading_dashes(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    tip = fx.sha("feat/x")
    fx.git(fx.work, "update-ref", "refs/heads/-dash", tip)
    fx.push("-dash")
    fx.pr("-dash", tip)
    spaced = fx.worktree("feat/spaced", directory="my work tree")
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 0, out
    for item in ("branch:-dash", "remote:origin/-dash", f"worktree:{spaced.as_posix()}", "branch:feat/spaced"):
        assert verdicts[item] == ("REMOVE", ""), (item, out)
    assert not fx.local_has("-dash") and not fx.remote_has("-dash") and not spaced.exists()


# --------------------------------------------------------------------------- receipt and predicate


PLAN_REL = "docs/releases/v0/v0.1/plans/v0.1.0-demo.md"


def _signed_record(fx: Fixture, classes: list[str]) -> Path:
    plan = fx.work / PLAN_REL
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# Plan\n\n**Version**: v0.1.0\n**Slug**: demo\n\n## Tasks\n\n- [ ] T001 do docs/x.md\n",
                    encoding="utf-8")
    ctx = ck.Context(str(plan), ck.Budget(60.0))
    record = {
        "schema": 1, "plan": PLAN_REL, "plan_sha256": ctx.plan_hash(), "repo_root": str(ctx.root),
        "remote_url": URL, "repo": "acme/demo", "session_id": "s1", "worktree": str(ctx.root),
        "start_head": fx.sha("HEAD"), "nonce": "0" * 32,
        "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "approvals": {"repo": "acme/demo", "source_branch": "feat/plan", "target_branch": "develop",
                      "cleanup": {"branches": [], "worktrees": []},
                      "classes": [{"class": c, "text": "line"} for c in classes]},
        "deferrable_gap_types": [], "cleanup": {"branches": [], "worktrees": []}, "blockers": [], "pause": None,
    }
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=True) or b"")
    path = ctx.record_paths()[0]
    ck._write_record(path, record)
    return path


def _routed(fx: Fixture) -> Callable[[list[str], Path | None], tuple[int, str]]:
    def run(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        rc, out, _ = fx.exec(argv, cwd)
        return rc, out

    return run


def test_receipt_is_written_sealed_and_satisfies_the_predicate(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    record_path = _signed_record(fx, ["cleanup-merged"])
    code, verdicts, out = fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL), "--session", "s1", capsys=capsys)
    assert code == 0, out
    assert verdicts["branch:feat/x"] == ("REMOVE", "")
    receipt = cm.receipt_path(record_path)
    body = json.loads(receipt.read_text(encoding="utf-8"))
    assert body["kind"] == cm.RECEIPT_KIND and body["integration_tip"] == fx.sha("develop")
    assert {"kind": "branch", "name": "feat/x", "remote": "", "path": ""} in body["removed"]
    git = shutil.which("git") or "git"
    merge = fx.sha("develop")
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "develop") == "met"
    # A removed item that reappears reopens nothing but makes the receipt untrue.
    fx.git(fx.work, "branch", "feat/x", "develop")
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "develop") == "unmet"
    fx.git(fx.work, "update-ref", "-d", "refs/heads/feat/x")
    # A merge the receipt's integration tip does not contain: the pass ran too early.
    fx.git(fx.work, "checkout", "-q", "-b", "later", "develop")
    (fx.work / "later.txt").write_text("l\n", encoding="utf-8")
    fx.git(fx.work, "add", "-A")
    fx.git(fx.work, "commit", "-qm", "later merge")
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, fx.sha("later"), "develop") == "unmet"
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "f" * 32, merge, "develop") == "unmet"
    body["removed"] = []
    receipt.write_text(json.dumps(body), encoding="utf-8")
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "develop") == "unmet"


def test_naming_another_sessions_plan_keeps_its_owned_items(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    """BG-4 (ADV-7): only the calling session's own verified record is exempt from ownership.

    Session s1's live record owns feat/plan, which is merged and idle. A caller that
    names that plan without being s1 must still keep feat/plan as owned-by-run.
    """
    fx.branch("feat/plan")
    _signed_record(fx, ["cleanup-merged"])
    plan = str(fx.work / PLAN_REL)
    for session in ((), ("--session", "s2")):
        code, verdicts, out = fx.run("--dry-run", "--plan", plan, *session, capsys=capsys)
        assert code == 0, out
        assert verdicts["branch:feat/plan"] == ("KEEP", "owned-by-run"), (session, out)
    code, verdicts, out = fx.run("--dry-run", "--plan", plan, "--session", "s1", capsys=capsys)
    assert verdicts["branch:feat/plan"] == ("REMOVE", ""), out


def test_a_receipt_needs_the_records_own_session(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    record_path = _signed_record(fx, ["cleanup-merged"])
    code, _verdicts, out = fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL),
                                  "--session", "s2", capsys=capsys)
    assert code == 3
    assert out.splitlines()[:2] == ["BLOCKED: approval-not-covered", "reason: record-bound-to-another-session"]
    assert fx.local_has("feat/x") and not cm.receipt_path(record_path).exists()


def test_receipt_needs_the_cleanup_merged_approval(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    record_path = _signed_record(fx, ["push-merge"])
    code, _verdicts, out = fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL), "--session", "s1", capsys=capsys)
    assert code == 3
    assert out.splitlines()[:2] == ["BLOCKED: approval-not-covered", "reason: no-cleanup-merged-approval"]
    assert fx.local_has("feat/x") and not cm.receipt_path(record_path).exists()


def test_receipt_flag_requires_apply_and_a_scope(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    assert cm.main(["--repo", str(fx.work), "--receipt"]) == 2
    assert cm.main(["--repo", str(fx.work), "--apply", "--receipt"]) == 2


def test_checker_reports_cleanup_merged_only_with_the_class(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/plan")
    fx.git(fx.work, "push", "-q", "origin", "--delete", "feat/plan")  # auto-deleted on merge
    record_path = _signed_record(fx, ["cleanup-merged"])
    fx.state.update(pr_state="MERGED", merge_commit=fx.sha("develop"))
    fx.save()
    ctx = ck.Context(str(fx.work / PLAN_REL), ck.Budget(60.0))
    record = ck.load_record(ctx, None).record
    status = dict(ck.evaluate(ctx, record)[0])
    assert status["cleanup.merged"] == "unmet"  # no receipt yet
    fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL), "--session", "s1", capsys=capsys)
    assert cm.receipt_path(record_path).is_file()
    status = dict(ck.evaluate(ctx, ck.load_record(ctx, None).record)[0])
    assert status["cleanup.merged"] == "met"
    record_without = dict(record, approvals=dict(record["approvals"], classes=[{"class": "push-merge"}]))
    assert "cleanup.merged" not in dict(ck.evaluate(ctx, record_without)[0])


# --------------------------------------------------------------------------- units


@pytest.mark.parametrize(
    ("path", "allowed"),
    [("node_modules/", True), ("web/node_modules/", True), ("__pycache__/", True), (".venv/", True),
     ("dist/", True), ("build/", True), (".pytest_cache/", True), ("src/build/", True),
     # Only an ignored DIRECTORY entry whose own name is allowlisted; a component match is not enough.
     ("__pycache__/x.pyc", False), ("src/build/.env", False), ("node_modules/.env", False),
     ("build/x", False), (".env", False), ("x.pyc", False), ("build", False), ("secrets/key.pem", False)],
)
def test_ignored_allowlist(path: str, allowed: bool) -> None:
    assert cm._allowlisted(path) is allowed


def test_paginated_json_is_concatenated() -> None:
    assert cm._parse_json_stream('[{"a": 1}]\n[{"b": 2}]') == [{"a": 1}, {"b": 2}]
    assert cm._parse_json_stream("not json") is None


def test_receipt_seal_uses_its_own_domain() -> None:
    body = {"kind": cm.RECEIPT_KIND}
    plain = hmac.new(b"k", ck._canonical(body), hashlib.sha256).hexdigest()
    assert cm._seal(body, b"k") != plain


# --------------------------------------------------------------------------- adversarial review regressions


def _make_dir_link(link: Path, target: Path) -> None:
    """A junction on Windows (what `npm link` makes), a symlink on POSIX; skip if the host refuses."""
    if os.name == "nt":
        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True,
                              check=False)
        if made.returncode != 0:
            pytest.skip("this host cannot create a junction")
        return
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        pytest.skip("this host cannot create a symlink")


def test_r1_link_inside_an_allowlisted_directory_keeps_the_worktree(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = fx.tmp / "outside_pkg"
    outside.mkdir()
    (outside / "src.js").write_text("LINKED SOURCE\n", encoding="utf-8")
    path = fx.worktree("feat/junc")
    (path / "node_modules").mkdir()
    _make_dir_link(path / "node_modules" / "pkg", outside)
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "link-present"), out
    assert (outside / "src.js").read_text(encoding="utf-8") == "LINKED SOURCE\n"
    assert path.is_dir()


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_r2_index_flags_that_hide_edits_keep_the_worktree(
    flag: str, fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    path = fx.worktree("feat/hidden")
    fx.git(path, "update-index", flag, "feat_hidden.txt")
    (path / "feat_hidden.txt").write_text("PRECIOUS EDIT\n", encoding="utf-8")
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "hidden-changes"), out
    assert (path / "feat_hidden.txt").read_text(encoding="utf-8") == "PRECIOUS EDIT\n"


def test_r3_a_worktree_nested_inside_another_keeps_the_outer_one(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    outer = fx.worktree("feat/outer")
    fx.branch("feat/inner")
    (outer / "node_modules").mkdir()
    inner = outer / "node_modules" / "inner"
    fx.git(fx.work, "worktree", "add", "-q", str(inner), "feat/inner")
    (inner / "wip.txt").write_text("UNCOMMITTED\n", encoding="utf-8")
    fx.age(outer)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{outer.as_posix()}"] == ("KEEP", "contains-worktree"), out
    assert (inner / "wip.txt").read_text(encoding="utf-8") == "UNCOMMITTED\n"


def test_r3_a_nested_repository_keeps_the_worktree(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    path = fx.worktree("feat/vendored")
    nested = path / "node_modules" / "lib"
    nested.mkdir(parents=True)
    fx.git(nested, "init", "-q")
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "contains-worktree"), out
    assert (nested / ".git").is_dir()


def test_r4_an_env_under_a_build_named_component_is_not_allowlisted(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    path = fx.worktree("feat/nested")
    (path / "src" / "build").mkdir(parents=True)
    (path / "src" / "build" / ".env").write_text("SECRET=1\n", encoding="utf-8")
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "ignored-not-allowlisted"), out
    assert (path / "src" / "build" / ".env").read_text(encoding="utf-8") == "SECRET=1\n"


@pytest.mark.parametrize("name", [".env", ".env.local", "server.PEM", "id_rsa", "credentials.json", "Secrets.yml"])
def test_r5_a_secret_like_file_inside_node_modules_keeps_the_worktree(
    name: str, fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    path = fx.worktree("feat/nm")
    (path / "node_modules" / "pkg").mkdir(parents=True)
    (path / "node_modules" / "pkg" / name).write_text("SECRET=1\n", encoding="utf-8")
    fx.age(path)
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "sensitive-ignored"), out
    assert (path / "node_modules" / "pkg" / name).is_file()


def test_r6_a_pull_request_merged_into_another_base_is_kept(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/x", pr=False)
    fx.pr("feat/x", fx.sha("feat/x"), base="release/next")
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/x"] == ("KEEP", "merged-elsewhere"), out
    assert verdicts["remote:origin/feat/x"] == ("KEEP", "merged-elsewhere"), out
    assert fx.local_has("feat/x") and fx.remote_has("feat/x")


def test_r6_a_pull_request_merged_into_the_default_branch_counts(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/x", pr=False)
    fx.pr("feat/x", fx.sha("feat/x"), base="main")
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts["branch:feat/x"] == ("REMOVE", ""), out


def test_r7_no_receipt_when_the_pass_could_not_see(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    fx.branch("feat/x")
    record_path = _signed_record(fx, ["cleanup-merged"])
    fx.state["prs_fail"] = True
    fx.save()
    code, verdicts, out = fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL), "--session", "s1", capsys=capsys)
    assert code == 3
    assert out.splitlines()[0] == "BLOCKED: cannot-verify"
    assert verdicts["branch:feat/x"] == ("KEEP", "gh-unavailable")
    assert not cm.receipt_path(record_path).exists()


def test_r7_receipt_binds_the_idle_window_and_the_target_branch(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/x")
    record_path = _signed_record(fx, ["cleanup-merged"])
    code, _verdicts, out = fx.run("--apply", "--receipt", "--plan", str(fx.work / PLAN_REL), "--session", "s1", capsys=capsys)
    assert code == 0, out
    receipt = cm.receipt_path(record_path)
    body = json.loads(receipt.read_text(encoding="utf-8"))
    assert body["idle_hours"] == 24.0 and body["integration_branch"] == "develop"
    git = shutil.which("git") or "git"
    merge = fx.sha("develop")
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "develop") == "met"
    assert cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "main") == "unmet"
    key = ck._secret(create=False) or b""
    for field_name, value in (("idle_hours", 1.0), ("idle_hours", float("nan")), ("integration_branch", "main")):
        forged = {k: v for k, v in body.items() if k != "seal"}
        forged[field_name] = value
        forged["seal"] = cm._seal(dict(forged), key)
        receipt.write_text(json.dumps(forged), encoding="utf-8")
        status = cm.receipt_status(fx.work, git, _routed(fx), record_path, "0" * 32, merge, "develop")
        assert status == "unmet", field_name


@pytest.mark.parametrize("value", ["0", "23.9", "-1", "nan", "inf", "x"])
def test_r8_idle_hours_below_24_or_not_finite_is_refused(value: str, fx: Fixture) -> None:
    fx.branch("feat/x")
    with pytest.raises(SystemExit) as raised:
        cm.main(["--repo", str(fx.work), "--apply", "--idle-hours", value])
    assert raised.value.code == 2
    assert fx.local_has("feat/x")


def test_r9_a_name_with_a_shell_metacharacter_is_never_passed_to_a_tool(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    name = "feat/x&mkdir,pwned"
    fx.git(fx.work, "branch", name, "develop")
    fx.push(name)
    fx.pr(name, fx.sha("develop"))
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert verdicts[f"branch:{name}"] == ("KEEP", "unsafe-name"), out
    assert verdicts[f"remote:origin/{name}"] == ("KEEP", "unsafe-name"), out
    assert not any(name in arg for argv in fx.argv for arg in argv)
    assert not list(fx.tmp.rglob("pwned"))


@pytest.mark.skipif(os.name != "nt", reason="batch files exist only on Windows")
def test_r9_the_resolver_never_returns_a_batch_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shims = tmp_path / "shims"
    shims.mkdir()
    for ext in (".cmd", ".bat"):
        (shims / f"nexus-probe-tool{ext}").write_text("@echo off\r\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(shims) + os.pathsep + os.environ.get("PATH", ""))
    assert cm.repo_host.absolute_tool("nexus-probe-tool", None) is None


def test_r10_an_unreadable_run_record_keeps_everything_and_refuses_apply(
    fx: Fixture, capsys: pytest.CaptureFixture[str]
) -> None:
    fx.branch("feat/x")
    fx.runs.mkdir(exist_ok=True)
    (fx.runs / "broken.json").write_text("{not json", encoding="utf-8")
    code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 3
    assert out.splitlines()[0] == "BLOCKED: records-unreadable"
    assert verdicts["branch:feat/x"] == ("KEEP", "records-unreadable")
    assert fx.local_has("feat/x") and fx.remote_has("feat/x")


def test_r11_the_worktree_holding_the_process_cwd_is_kept(
    fx: Fixture, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fx.worktree("feat/mine")
    (path / "sub").mkdir()
    monkeypatch.chdir(path / "sub")
    _code, verdicts, out = fx.run("--apply", capsys=capsys)
    monkeypatch.chdir(fx.tmp)
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "current-worktree"), out
    assert path.is_dir()


@pytest.mark.skipif(os.name != "nt", reason="the rename probe runs only on Windows")
def test_r11_an_open_handle_keeps_the_worktree_whole(fx: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    path = fx.worktree("feat/open")
    held = path / "feat_open.txt"
    with open(held, encoding="utf-8"):
        code, verdicts, out = fx.run("--apply", capsys=capsys)
    assert code == 0, out
    assert verdicts[f"worktree:{path.as_posix()}"] == ("KEEP", "in-use"), out
    assert held.is_file() and (path / ".gitignore").is_file()
    assert not list(fx.tmp.glob("*.cleanup-probe-*"))
