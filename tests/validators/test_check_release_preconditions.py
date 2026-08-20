"""Tests for scripts/check_release_preconditions.py.

The pre-tag assertion exists because of a specific incident: in the v3.17.5
release a `git checkout main` failed on a locked directory, HEAD stayed on an
unrelated branch, and the tag was created there and published. So the tests are
built around real git repositories with a real remote, because the failure mode
is a git state, not a function argument.

Two directions are asserted throughout, and the second is the one that matters
for a release gate:

- It must BLOCK a wrong HEAD. A gate that misses the bad state is the bug.
- It must PASS a legitimate release, including from a differently-named release
  branch. An over-strict assertion that blocks a real release trains people to
  bypass it, which is how the whole class of defect in v3.17.6 started.

The branch reporter is asserted never to propose deleting a protected branch or
one with an open PR, because it runs inside a release flow where a wrong
suggestion is most likely to be acted on without thinking.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_release_preconditions.py"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="these tests drive real git repositories"
)


def module():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    return importlib.import_module("check_release_preconditions")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A clone with a real `origin`, a main and develop branch, and history.

    A bare repo stands in for the remote so `origin/<branch>` refs are genuine
    rather than simulated: the assertion compares against a remote-tracking ref,
    and faking that would test the mock.
    """
    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", "-b", "main", str(origin)], check=True
    )

    work = tmp_path / "work"
    subprocess.run(
        ["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True
    )
    git(work, "config", "user.email", "t@example.com")
    git(work, "config", "user.name", "T")

    (work / "README.md").write_text("base\n", encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "base")
    git(work, "branch", "-M", "main")
    git(work, "push", "-q", "-u", "origin", "main")

    git(work, "checkout", "-q", "-b", "develop")
    git(work, "push", "-q", "-u", "origin", "develop")
    git(work, "checkout", "-q", "main")
    return work


# ---------------------------------------------------------------------------
# --pre-tag
# ---------------------------------------------------------------------------


def test_head_on_release_branch_and_synced_passes(repo: Path) -> None:
    """The legitimate release case must not be blocked."""
    assert module().check_pre_tag("main", cwd=repo) == []


def test_head_on_another_branch_aborts(repo: Path) -> None:
    """The v3.17.5 incident: a failed checkout leaves HEAD elsewhere."""
    git(repo, "checkout", "-q", "develop")
    problems = module().check_pre_tag("main", cwd=repo)
    assert len(problems) == 1
    assert "develop" in problems[0]
    assert "main" in problems[0]


def test_detached_head_aborts(repo: Path) -> None:
    """A detached HEAD is a distinct way to end up tagging the wrong commit."""
    git(repo, "checkout", "-q", "--detach", "HEAD")
    problems = module().check_pre_tag("main", cwd=repo)
    assert len(problems) == 1
    assert "detached" in problems[0].lower()


def test_head_ahead_of_origin_aborts(repo: Path) -> None:
    """A local commit not yet pushed must not be tagged.

    Tagging here publishes a tag for a commit the remote does not have, so the
    tag cannot be reproduced from the repository.
    """
    (repo / "extra.txt").write_text("x\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "unpushed")
    problems = module().check_pre_tag("main", cwd=repo)
    assert len(problems) == 1
    assert "does not match" in problems[0]


def test_head_behind_origin_aborts(repo: Path) -> None:
    """A stale local branch must not be tagged either."""
    git(repo, "checkout", "-q", "-b", "temp")
    (repo / "remote-only.txt").write_text("y\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "remote side")
    git(repo, "push", "-q", "origin", "temp:main")
    git(repo, "checkout", "-q", "main")
    git(repo, "fetch", "-q", "origin")
    problems = module().check_pre_tag("main", cwd=repo)
    assert len(problems) == 1
    assert "does not match" in problems[0]


def test_non_default_release_branch_passes(repo: Path) -> None:
    """The expected branch is configurable, not hardcoded to main.

    An assertion that only ever accepted `main` would block a project releasing
    from any other branch, and a gate that blocks legitimate work gets bypassed.
    """
    git(repo, "checkout", "-q", "-b", "release/2026")
    git(repo, "push", "-q", "-u", "origin", "release/2026")
    assert module().check_pre_tag("release/2026", cwd=repo) == []
    # ... and still rejects the default in that configuration.
    assert module().check_pre_tag("main", cwd=repo) != []


def test_missing_remote_ref_aborts(repo: Path) -> None:
    """An unpushed release branch cannot be confirmed against the remote."""
    git(repo, "checkout", "-q", "-b", "never-pushed")
    problems = module().check_pre_tag("never-pushed", cwd=repo)
    assert len(problems) == 1
    assert "does not exist locally" in problems[0]


def test_cli_pre_tag_exit_codes(repo: Path) -> None:
    """The CLI must exit 1 on a bad HEAD and 0 on a good one."""
    bad = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(repo),
            "--pre-tag",
            "--release-branch",
            "develop",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
    assert "BLOCKED" in bad.stderr

    good = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(repo), "--pre-tag"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert good.returncode == 0, good.stderr
    assert "OK" in good.stdout


def test_not_a_git_repo_exits_2(tmp_path: Path) -> None:
    """An environment problem is distinct from a failed precondition."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--pre-tag"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert result.returncode == 2, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# --branches
# ---------------------------------------------------------------------------


@pytest.fixture
def repo_with_branches(repo: Path) -> Path:
    """Adds one merged branch and one unmerged branch to the fixture."""
    git(repo, "checkout", "-q", "develop")

    git(repo, "checkout", "-q", "-b", "feat/merged")
    (repo / "merged.txt").write_text("m\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "merged work")
    git(repo, "push", "-q", "-u", "origin", "feat/merged")

    git(repo, "checkout", "-q", "develop")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge feat/merged", "feat/merged")
    git(repo, "push", "-q", "origin", "develop")

    git(repo, "checkout", "-q", "-b", "feat/unmerged")
    (repo / "unmerged.txt").write_text("u\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "unmerged work")
    git(repo, "push", "-q", "-u", "origin", "feat/unmerged")

    git(repo, "checkout", "-q", "develop")
    git(repo, "fetch", "-q", "origin")
    return repo


def test_reports_merged_but_not_unmerged(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = module()
    monkeypatch.setattr(mod, "open_pr_branches", lambda: set())
    candidates, _ = mod.merged_branch_candidates("develop", cwd=repo_with_branches)
    assert "feat/merged" in candidates
    assert "feat/unmerged" not in candidates


def test_never_proposes_a_protected_branch(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main and develop are merged into develop by construction; both must be excluded."""
    mod = module()
    monkeypatch.setattr(mod, "open_pr_branches", lambda: set())
    candidates, _ = mod.merged_branch_candidates("develop", cwd=repo_with_branches)
    for protected in ("main", "develop", "master", "HEAD"):
        assert protected not in candidates


def test_never_proposes_a_branch_with_an_open_pr(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A merged branch whose PR is still open is excluded.

    A branch can be merged and still have an open PR (a second PR from the same
    head, or a PR retargeted after merge), and deleting it would close that PR.
    """
    mod = module()
    monkeypatch.setattr(mod, "open_pr_branches", lambda: {"feat/merged"})
    candidates, with_open_pr = mod.merged_branch_candidates(
        "develop", cwd=repo_with_branches
    )
    assert "feat/merged" not in candidates
    assert with_open_pr == {"feat/merged"}


def test_branch_report_never_deletes(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reporter is read-only; the branch set must be identical afterwards."""
    mod = module()
    monkeypatch.setattr(mod, "open_pr_branches", lambda: set())
    before = git(repo_with_branches, "branch", "-r")
    mod.report_branches("develop", repo_with_branches)
    assert git(repo_with_branches, "branch", "-r") == before


def test_open_pr_branches_returns_empty_when_gh_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No gh means no exclusions, which is the cautious direction.

    This function only ever REMOVES branches from a deletion-candidate list, so an
    empty answer can make the report more conservative, never less.
    """
    mod = module()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    assert mod.open_pr_branches() == set()


def test_closed_unmerged_pr_branches_reports_surviving_refs(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The category delete_branch_on_merge does not cover.

    GitHub deletes a branch when its PR MERGES and does nothing when a PR is
    closed unmerged, so with that setting enabled these are the only branches
    that still accumulate -- and the merged report cannot see them.
    """
    mod = module()
    monkeypatch.setattr(
        mod.shutil,
        "which",
        lambda name: "/usr/bin/gh" if name == "gh" else "/usr/bin/git",
    )

    class FakeProc:
        stdout = '[{"headRefName": "feat/unmerged", "mergedAt": null}]'

    real_run = mod.subprocess.run

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["gh", "pr", "list"]:
            return FakeProc()
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.closed_unmerged_pr_branches(cwd=repo_with_branches) == ["feat/unmerged"]


def test_closed_but_merged_pr_is_not_reported(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A merged PR is the case GitHub already handles; do not double-report it."""
    mod = module()
    monkeypatch.setattr(
        mod.shutil,
        "which",
        lambda name: "/usr/bin/gh" if name == "gh" else "/usr/bin/git",
    )

    class FakeProc:
        stdout = '[{"headRefName": "feat/merged", "mergedAt": "2026-08-20T00:00:00Z"}]'

    real_run = mod.subprocess.run

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["gh", "pr", "list"]:
            return FakeProc()
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.closed_unmerged_pr_branches(cwd=repo_with_branches) == []


def test_closed_pr_for_a_deleted_branch_is_not_reported(
    repo_with_branches: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only refs that still exist are worth reporting as cleanup candidates."""
    mod = module()
    monkeypatch.setattr(
        mod.shutil,
        "which",
        lambda name: "/usr/bin/gh" if name == "gh" else "/usr/bin/git",
    )

    class FakeProc:
        stdout = '[{"headRefName": "gone/long-ago", "mergedAt": null}]'

    real_run = mod.subprocess.run

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["gh", "pr", "list"]:
            return FakeProc()
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.closed_unmerged_pr_branches(cwd=repo_with_branches) == []


def test_closed_unmerged_returns_empty_without_gh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No gh keeps the report quiet rather than wrong."""
    mod = module()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    assert mod.closed_unmerged_pr_branches() == []


# ---------------------------------------------------------------------------
# description drift
# ---------------------------------------------------------------------------


def test_drift_against_the_declaration_is_reported() -> None:
    mod = module()
    findings = mod.description_drift("256 curated skills", {"skills": 273})
    assert len(findings) == 1
    assert "256" in findings[0] and "273" in findings[0]
    assert "README.md" in findings[0]


def test_matching_counts_report_nothing() -> None:
    mod = module()
    assert mod.description_drift("273 skills", {"skills": 273}) == []


def test_description_with_no_numeric_claim_reports_nothing() -> None:
    """A description that claims no counts is not nagged into claiming some."""
    mod = module()
    assert mod.description_drift("A skill harness", {"skills": 273}) == []


def test_only_nouns_the_description_mentions_are_checked() -> None:
    """A declaration richer than the description must not manufacture findings."""
    mod = module()
    findings = mod.description_drift(
        "273 skills", {"skills": 273, "commands": 18, "hooks": 31}
    )
    assert findings == []


def test_declared_counts_read_the_readme_not_a_file_glob(tmp_path: Path) -> None:
    """The declaration is the comparison target, not a derived count.

    A glob over catalog/commands/*.md includes permanent aliases and
    catalog/hooks/ mixes hooks with helpers, so globbing this repository yields
    21 and 34 where it declares 18 and 31. Emitting a derived number would be
    worse than none: it is the number someone pastes into the description.
    """
    readme = (
        "Nexus-Hub is the catalog: **273 skills**, 18 commands, 31 hooks, 23 agents.\n"
    )
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    assert module().declared_counts(tmp_path) == {
        "skills": 273,
        "commands": 18,
        "hooks": 31,
        "agents": 23,
    }


def test_declared_counts_self_gate_without_a_readme(tmp_path: Path) -> None:
    """On a repository that declares nothing, the check must no-op, not guess."""
    assert module().declared_counts(tmp_path) == {}


def test_stale_declaration_is_caught(tmp_path: Path) -> None:
    """If README itself drifted, say so before trusting it as the target."""
    (tmp_path / "README.md").write_text("256 skills\n", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    entries = ",".join(["{}"] * 273)
    (data / "skills.json").write_text('{"skills": [' + entries + "]}", encoding="utf-8")
    findings = module().declared_vs_actual(tmp_path)
    assert len(findings) == 1
    assert "256" in findings[0] and "273" in findings[0]


def test_declaration_matching_the_catalog_reports_nothing(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("2 skills\n", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "skills.json").write_text('{"skills": [{}, {}]}', encoding="utf-8")
    assert module().declared_vs_actual(tmp_path) == []


def test_this_repo_declaration_matches_its_catalog() -> None:
    """Guard the live repository: README's skills figure must match skills.json."""
    assert module().declared_vs_actual(REPO_ROOT) == []
