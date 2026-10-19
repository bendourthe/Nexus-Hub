"""Parallel admission through real Git worktrees and the public completion CLI.

Hosting replies are the existing local gh fixture, not proof of a production release.
Synthetic signing below is limited to these disposable test run records.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, _no_transport_overrides  # noqa: F401
from .test_completion_minor_verdict import Walk, ck, cm

VERSIONS = {"v0.5.2": "alpha", "v0.5.10": "omega"}


@pytest.fixture
def parallel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Walk:
    fixture = Walk(tmp_path, monkeypatch)
    fixture.forge_minor(bound=())
    return fixture


def worker(repo: Walk, version: str) -> Path:
    path = repo.tmp / ("worker-" + version)
    branch = "feat/" + version + "-" + VERSIONS[version]
    _git(repo.work, "worktree", "add", "-q", "-b", branch, str(path), "origin/develop")
    return path


def claims(
    repo: Walk,
    version: str,
    *,
    reads: tuple[str, ...] = (),
    writes: tuple[str, ...] | None = None,
    depends: tuple[str, ...] = (),
) -> dict:
    slug = VERSIONS[version]
    return {
        "depends_on": list(depends),
        "read_paths": list(reads),
        "write_paths": list(
            writes
            or (f"src/{slug}.txt", f"docs/releases/v0/v0.5/plans/{version}-{slug}.md")
        ),
    }


def claim_file(repo: Walk, value: dict) -> Path:
    path = repo.tmp / f"claims-{len(list(repo.tmp.glob('claims-*.json')))}.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def admit(
    repo: Walk,
    version: str,
    root: Path,
    value: dict | None = None,
    *,
    session: str = SESSION,
    base: str | None = None,
):
    head = base or _git(root, "rev-parse", "HEAD").strip()
    return repo.run(
        "record",
        "member-implement-start",
        "--minor",
        "v0.5",
        "--member",
        version,
        "--session",
        session,
        "--repo",
        str(repo.work),
        "--worktree",
        str(root),
        "--head",
        head,
        "--claims",
        str(claim_file(repo, value or claims(repo, version))),
    )


def project(repo: Walk, version: str, **kwargs):
    result = repo.run(
        "check-member",
        "--minor",
        "v0.5",
        "--member",
        version,
        "--session",
        kwargs.get("session", SESSION),
        "--repo",
        str(kwargs.get("root", repo.work)),
        "--json",
    )
    body = (
        json.loads(result.stdout.splitlines()[-1])
        if result.stdout.rstrip().endswith("}")
        else {}
    )
    return result, body


def publication(repo: Walk, version: str, paths: list[str] | None = None):
    args = [
        "record",
        "member-start",
        "--minor",
        "v0.5",
        "--member",
        version,
        "--session",
        SESSION,
        "--repo",
        str(repo.work),
        "--head",
        _git(repo.work, "rev-parse", "origin/develop").strip(),
    ]
    if paths is not None:
        args += ["--coordinator-claims", str(claim_file(repo, {"write_paths": paths}))]
    return repo.run(*args)


def commit_worker(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _git(root, "add", "--", rel)
    _git(root, "commit", "-q", "-m", "worker change")
    return _git(root, "rev-parse", "HEAD").strip()


def merge_worker(repo: Walk, root: Path, version: str) -> str:
    head = _git(root, "rev-parse", "HEAD").strip()
    _git(repo.work, "branch", "-f", "develop", head)
    repo.publish("develop")
    repo.pr(
        "feat/" + version + "-" + VERSIONS[version],
        "MERGED",
        [{"name": "ci", "bucket": "pass"}],
        head,
    )
    return head


def test_two_workers_admitted_before_either_release_and_parent_approval_preserved(
    parallel: Walk,
) -> None:
    before = parallel.record()
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    for version, root in (("v0.5.2", alpha), ("v0.5.10", omega)):
        result = admit(parallel, version, root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.startswith("IMPLEMENTING " + version)
    after = parallel.record()
    assert not parallel.state["releases"]
    assert [m["implementation"]["worktree"] for m in after["members"]] == [
        str(alpha.resolve()),
        str(omega.resolve()),
    ]
    assert all("start_head" not in m for m in after["members"])
    assert after["approvals"] == before["approvals"]
    for key in ("nonce", "session_id", "created", "start_head"):
        assert after[key] == before[key]
    assert all(
        m["plan_sha256"] == before["members"][i]["plan_sha256"]
        for i, m in enumerate(after["members"])
    )
    assert parallel.load().record is not None
    assert publication(parallel, "v0.5.10").returncode == ck.EXIT_BLOCKED


def test_parent_projection_reads_live_worker_and_never_creates_child_record(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    rel = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"
    commit_worker(root, rel, (root / rel).read_text().replace("[ ]", "[x]"))
    commit_worker(root, "src/alpha.txt", "implemented\n")
    before = parallel.record_path().read_bytes()
    result, body = project(parallel, "v0.5.2")
    assert result.returncode == ck.EXIT_INCOMPLETE
    assert body["predicates"]["implementation.identity"] == "met"
    assert body["predicates"]["task.T001"] == "met"
    assert body["predicates"]["approval.remote"] == "met"
    assert (
        body["base_head"]
        == parallel.record()["members"][0]["implementation"]["base_head"]
    )
    assert parallel.record_path().read_bytes() == before
    assert len(list(parallel.runs.glob("*.json"))) == 1
    assert (
        project(parallel, "v0.5.2", session="other")[0].returncode == ck.EXIT_MALFORMED
    )
    assert project(parallel, "v0.5.2", root=root)[0].returncode == ck.EXIT_MALFORMED


@pytest.mark.parametrize(
    ("left", "right", "reads"),
    [
        (("src/shared.txt",), ("src/shared.txt",), ()),
        (("src/",), ("src/nested/output.txt",), ()),
        (("src/Shared.txt",), ("src/shared.txt",), ()),
        (("src/shared.txt",), ("src/omega.txt",), ("src/shared.txt",)),
    ],
)
def test_write_write_directory_case_and_write_read_conflicts(
    parallel: Walk, left, right, reads
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    assert (
        admit(
            parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", writes=left)
        ).returncode
        == 0
    )
    before = parallel.record_path().read_bytes()
    refused = admit(
        parallel,
        "v0.5.10",
        omega,
        claims(parallel, "v0.5.10", reads=reads, writes=right),
    )
    assert (
        refused.returncode == ck.EXIT_BLOCKED
        and "implementation-scope-conflict" in refused.stdout
    )
    assert parallel.record_path().read_bytes() == before


def test_malformed_alias_and_coordinator_paths_refused_without_mutation(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    before = parallel.record_path().read_bytes()
    for path in (
        "../outside",
        "/outside",
        "C:/outside",
        "src\\file",
        "src//file",
        "src/../file",
        "src/*.py",
        "src/[ab].py",
        "src/file.",
        "src/CON.txt",
        ".git/config",
        "docs/todos.md",
        "CHANGELOG.md",
        "docs/",
        "docs/releases/v0/v0.5/known-gaps.md",
    ):
        refused = admit(
            parallel, "v0.5.2", root, claims(parallel, "v0.5.2", writes=(path,))
        )
        assert refused.returncode == ck.EXIT_BLOCKED, (
            path,
            refused.stdout,
            refused.stderr,
        )
        assert parallel.record_path().read_bytes() == before


def test_read_write_conflict_is_symmetric_and_read_read_is_allowed(
    parallel: Walk,
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    assert (
        admit(
            parallel,
            "v0.5.2",
            alpha,
            claims(parallel, "v0.5.2", reads=("src/shared.txt",)),
        ).returncode
        == 0
    )
    refused = admit(
        parallel,
        "v0.5.10",
        omega,
        claims(parallel, "v0.5.10", writes=("src/shared.txt",)),
    )
    assert (
        refused.returncode == ck.EXIT_BLOCKED
        and "implementation-scope-conflict" in refused.stdout
    )
    allowed = admit(
        parallel,
        "v0.5.10",
        omega,
        claims(parallel, "v0.5.10", reads=("src/shared.txt",)),
    )
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr


def test_dependency_requires_actual_merge_on_worker_base_but_not_release(
    parallel: Walk,
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.2", alpha).returncode == 0
    depends = claims(parallel, "v0.5.10", depends=("v0.5.2",))
    early = admit(parallel, "v0.5.10", omega, depends)
    assert "implementation-dependency-unmerged" in early.stdout
    commit_worker(alpha, "src/alpha.txt", "dependency\n")
    merge_worker(parallel, alpha, "v0.5.2")
    assert (
        "implementation-dependency-unmerged"
        in admit(parallel, "v0.5.10", omega, depends).stdout
    )
    _git(omega, "merge", "-q", "--ff-only", "origin/develop")
    ready = admit(parallel, "v0.5.10", omega, depends)
    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert not parallel.state["releases"]


def test_unknown_self_and_cyclic_dependencies_refused(parallel: Walk) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    for dependency in ("v0.5.2", "v0.5.99"):
        result = admit(
            parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", depends=(dependency,))
        )
        assert "invalid-implementation-dependency" in result.stdout
    assert admit(parallel, "v0.5.2", alpha).returncode == 0
    record = parallel.record()
    record["members"][0]["implementation"]["depends_on"] = ["v0.5.10"]
    parallel.write_record(record, resign=True)  # fixture-only signed malformed graph
    result = admit(
        parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", depends=("v0.5.2",))
    )
    assert "cyclic-implementation-dependency" in result.stdout


def test_reservation_survives_worker_completion_and_hosting_only_merge(
    parallel: Walk,
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    shared = ("src/shared.txt",)
    assert (
        admit(
            parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", writes=shared)
        ).returncode
        == 0
    )
    commit = commit_worker(alpha, "src/shared.txt", "done but not integrated\n")
    same = claims(parallel, "v0.5.10", writes=shared)
    assert (
        "implementation-scope-conflict"
        in admit(parallel, "v0.5.10", omega, same).stdout
    )
    parallel.pr(
        "feat/v0.5.2-alpha", "MERGED", [{"name": "ci", "bucket": "pass"}], commit
    )
    assert (
        "implementation-scope-conflict"
        in admit(parallel, "v0.5.10", omega, same).stdout
    )
    merge_worker(parallel, alpha, "v0.5.2")
    _git(omega, "merge", "-q", "--ff-only", "origin/develop")
    assert admit(parallel, "v0.5.10", omega, same).returncode == 0


def test_resume_is_exact_and_live_branch_and_frozen_prose_are_rechecked(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    base = parallel.record()["members"][0]["implementation"]["base_head"]
    commit_worker(root, "src/alpha.txt", "work\n")
    assert admit(parallel, "v0.5.2", root, base=base).returncode == 0
    changed = claims(parallel, "v0.5.2", writes=("src/other.txt",))
    assert (
        "implementation-already-started"
        in admit(parallel, "v0.5.2", root, changed, base=base).stdout
    )
    _git(root, "checkout", "-q", "--detach")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "cannot-verify"
    )
    _git(root, "checkout", "-q", "feat/v0.5.2-alpha")
    rel = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"
    commit_worker(
        root, rel, (root / rel).read_text() + "\nAn unapproved instruction.\n"
    )
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "cannot-verify"
    )


def test_forged_binding_signature_and_copied_controller_are_rejected(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    good = parallel.record()
    for transform in (
        lambda r: r.pop("implementation_controller"),
        lambda r: r["implementation_controller"].update(repo_root=str(root)),
        lambda r: r["members"][0]["implementation"].update(write_paths=["src/"]),
    ):
        record = json.loads(json.dumps(good))
        transform(record)
        parallel.write_record(record, resign=False)
        result, _body = project(parallel, "v0.5.2")
        assert result.stdout.startswith("BLOCKED: record-tampered")
    parallel.write_record(good, resign=False)
    other = worker(parallel, "v0.5.10")
    otherctx = ck.RepoContext(other, ck.Budget(30))
    copied = cm.record_file(ck, otherctx, "v0.5")
    forged = json.loads(json.dumps(good))
    forged["repo_root"] = str(
        other.resolve()
    )  # legacy unsigned fields cannot move the new signed binding
    forged["worktree"] = str(other.resolve())
    copied.write_text(json.dumps(forged), encoding="utf-8")
    result = parallel.run(
        "check-member",
        "--minor",
        "v0.5",
        "--member",
        "v0.5.2",
        "--session",
        SESSION,
        "--repo",
        str(other),
    )
    assert result.stdout.startswith("BLOCKED: record-tampered")


def test_unknown_unregistered_and_dirty_worktrees_are_refused(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert (
        admit(parallel, "v0.5.2", root, session="another").returncode
        == ck.EXIT_MALFORMED
    )
    assert (
        admit(parallel, "v0.5.99", root, claims(parallel, "v0.5.2")).returncode
        == ck.EXIT_MALFORMED
    )
    clone = parallel.tmp / "clone"
    _git(parallel.tmp, "clone", "-q", str(parallel.remote), str(clone))
    _git(clone, "checkout", "-q", "-b", "feat/v0.5.2-alpha", "origin/develop")
    assert (
        "implementation-worktree-unverified" in admit(parallel, "v0.5.2", clone).stdout
    )
    (root / "src").mkdir()
    (root / "src/alpha.txt").write_text("uncommitted\n")
    assert (
        "implementation-base-not-clean-head" in admit(parallel, "v0.5.2", root).stdout
    )
    (root / "src/alpha.txt").unlink()


def test_refreshed_base_excludes_predecessor_delta_but_not_own_unclaimed_delta(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    original = parallel.record()["members"][0]["implementation"]["base_head"]
    commit_worker(
        parallel.work, "src/predecessor.txt", "unrelated integrated prerequisite\n"
    )
    parallel.integrate()
    _git(root, "merge", "-q", "--ff-only", "origin/develop")
    commit_worker(root, "src/alpha.txt", "own work\n")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"] == "met"
    )
    assert publication(parallel, "v0.5.2").returncode == 0
    member = parallel.record()["members"][0]
    assert (
        member["implementation"]["base_head"] == original
        and member["start_head"] != original
    )
    commit_worker(root, "src/unclaimed.txt", "outside reservation\n")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )


def test_merged_member_uses_canonical_evidence_after_worker_removal(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    rel = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"
    commit_worker(root, rel, (root / rel).read_text().replace("[ ]", "[x]"))
    commit_worker(root, "src/alpha.txt", "implemented\n")
    merge_worker(parallel, root, "v0.5.2")
    _git(parallel.work, "merge", "-q", "--ff-only", "origin/develop")
    _git(parallel.work, "worktree", "remove", str(root))
    result, body = project(parallel, "v0.5.2")
    assert result.returncode == ck.EXIT_INCOMPLETE
    assert body["predicates"]["implementation.identity"] == "met"
    assert body["predicates"]["task.T001"] == "met"


def test_publication_exempts_only_cleanup_and_requires_predecessor_gate(
    parallel: Walk, monkeypatch
) -> None:
    parallel.release_member("v0.5.2", "alpha")
    record = parallel.record()
    record["members"][0]["approvals"]["cleanup"]["branches"] = ["feat/v0.5.2-alpha"]
    parallel.write_record(record, resign=True)
    _git(parallel.work, "branch", "feat/v0.5.2-alpha")
    assert publication(parallel, "v0.5.10").returncode == 0
    record = parallel.record()
    record["members"][1].pop("start_head")
    parallel.write_record(record, resign=True)
    real_evaluate = cm.evaluate_member
    for predicate in (
        "task.T001",
        "evidence.file",
        "tests.evidence",
        "gaps.version",
        "integration.merged",
        "integration.checks",
        "release.tag",
        "release.changelog",
        "release.github",
        "release.main",
        "release.version-sync",
        "approval.remote",
    ):
        for bad in ("unmet", "cannot-verify"):

            def missing(*args, _bad=bad, _predicate=predicate, **kwargs):
                result = real_evaluate(*args, **kwargs)
                result.lines = [
                    (pid, _bad if pid == _predicate else value)
                    for pid, value in result.lines
                ]
                return result

            monkeypatch.setattr(cm, "evaluate_member", missing)
            args = ck.build_parser().parse_args(
                [
                    "record",
                    "member-start",
                    "--minor",
                    "v0.5",
                    "--member",
                    "v0.5.10",
                    "--session",
                    SESSION,
                    "--repo",
                    str(parallel.work),
                    "--head",
                    parallel.head(),
                ]
            )
            assert cm.cmd_record_member_start(ck, args) == ck.EXIT_BLOCKED, (
                predicate,
                bad,
            )
    monkeypatch.setattr(cm, "evaluate_member", real_evaluate)


def test_coordinator_claims_are_publication_only_signed_and_conflict_checked(
    parallel: Walk,
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.2", alpha).returncode == 0
    assert (
        admit(
            parallel,
            "v0.5.10",
            omega,
            claims(parallel, "v0.5.10", reads=("CHANGELOG.md",)),
        ).returncode
        == 0
    )
    assert (
        "coordinator-scope-conflict"
        in publication(parallel, "v0.5.2", ["CHANGELOG.md"]).stdout
    )
    assert (
        "invalid-coordinator-claims"
        in publication(parallel, "v0.5.2", ["src/outside-plan.txt"]).stdout
    )
    assert (
        "invalid-coordinator-claims"
        in publication(parallel, "v0.5.2", [".github/workflows/ci.yml"]).stdout
    )
    assert (
        "invalid-coordinator-claims"
        in publication(parallel, "v0.5.2", ["configs/permissions.json"]).stdout
    )


def test_explicit_coordinator_paths_allow_only_recorded_publication_delta(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    commit_worker(root, "CHANGELOG.md", "# Coordinated release metadata\n")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )
    assert publication(parallel, "v0.5.2").returncode == ck.EXIT_BLOCKED
    allowed = publication(parallel, "v0.5.2", ["CHANGELOG.md"])
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert parallel.record()["members"][0]["coordinator_paths"] == ["CHANGELOG.md"]
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"] == "met"
    )
    assert (
        "coordinator-claims-already-recorded"
        in publication(parallel, "v0.5.2", ["DEVLOG.md"]).stdout
    )


def test_aggregate_metadata_sensitive_scopes_and_unknown_claim_shapes_are_rejected(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    rctx = parallel.rctx()
    for path in (
        "data/skills.json",
        "data/SKILL_INDEX.md",
        "data/marketplace.json",
        "data/bundles.json",
        "docs/README.md",
        "docs/DEVLOG.md",
        ".claude-plugin/plugin.json",
        "package-lock.json",
        ".github/workflows/ci.yml",
        ".github/",
        "configs/permissions/",
        "configs/",
        ".env",
        "secrets/keys.json",
    ):
        with pytest.raises(cm.MinorMalformed):
            cm._claims(rctx, "v0.5", root, claims(parallel, "v0.5.2", writes=(path,)))
    for value in (
        {},
        {"depends_on": [], "read_paths": [], "write_paths": []},
        {"depends_on": [], "read_paths": [], "write_paths": ["src/a", "src/A"]},
        {"depends_on": [], "read_paths": ["../escape"], "write_paths": ["src/a"]},
    ):
        with pytest.raises(cm.MinorMalformed):
            cm._claims(rctx, "v0.5", root, value)
    # The fixed sensitive boundaries do not reject ordinary tests or already approved hook implementation.
    cm._claims(
        rctx,
        "v0.5",
        root,
        claims(
            parallel,
            "v0.5.2",
            writes=("catalog/hooks/opt-in-guard.py", "tests/test_permission_guard.py"),
        ),
    )


def test_publication_refuses_predecessor_that_skipped_its_own_ordered_gate(
    parallel: Walk,
) -> None:
    parallel.plan("v0.5.1", "first")
    parallel.commit("add predecessor in fixture")
    parallel.integrate()
    parallel.forge_minor(bound=())
    parallel.release_member("v0.5.1", "first")
    parallel.release_member(
        "v0.5.2", "alpha"
    )  # hosting says released; native publication admission was skipped
    refused = publication(parallel, "v0.5.10")
    assert (
        refused.returncode == ck.EXIT_BLOCKED
        and "previous-member-incomplete" in refused.stdout
    )


def two_parent_merge(
    repo: Walk, root: Path, *, resolution_path: str | None = None
) -> str:
    _git(repo.work, "checkout", "-q", "develop")
    _git(repo.work, "merge", "-q", "--no-ff", "--no-commit", "feat/v0.5.2-alpha")
    if resolution_path:
        path = repo.work / resolution_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("added while resolving the merge\n", encoding="utf-8")
        _git(repo.work, "add", "--", resolution_path)
    _git(repo.work, "commit", "-q", "-m", "merge worker")
    repo.publish("develop")
    merge = repo.head()
    repo.pr("feat/v0.5.2-alpha", "MERGED", [{"name": "ci", "bucket": "pass"}], merge)
    _git(repo.work, "worktree", "remove", str(root))
    return merge


def test_two_parent_merge_ignores_unrelated_target_changes_after_publication_base(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    assert publication(parallel, "v0.5.2").returncode == 0
    commit_worker(root, "src/alpha.txt", "worker output\n")
    commit_worker(
        parallel.work, "src/unrelated-target.txt", "another already integrated change\n"
    )
    parallel.integrate()
    merge = two_parent_merge(parallel, root)
    assert (
        len(_git(parallel.work, "rev-list", "--parents", "-n", "1", merge).split()) == 3
    )
    result, body = project(parallel, "v0.5.2")
    assert result.returncode == ck.EXIT_INCOMPLETE
    assert body["predicates"]["implementation.identity"] == "met"


@pytest.mark.parametrize(
    "resolution", [False, True], ids=["worker-post-gate", "merge-resolution"]
)
def test_merged_unclaimed_delta_never_retires_scope_after_worker_removal(
    parallel: Walk, resolution: bool
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    assert publication(parallel, "v0.5.2").returncode == 0
    commit_worker(root, "src/alpha.txt", "worker output\n")
    if not resolution:
        commit_worker(root, "src/unclaimed.txt", "outside signed reservation\n")
    merge = two_parent_merge(
        parallel, root, resolution_path="src/unclaimed.txt" if resolution else None
    )
    result, body = project(parallel, "v0.5.2")
    assert result.returncode == ck.EXIT_INCOMPLETE
    assert body["predicates"]["implementation.identity"] == "unmet"
    assert not cm._merged_on_base(
        ck, parallel.rctx(), parallel.record(), parallel.record()["members"][0], merge
    )


def test_published_worker_can_refresh_target_without_widening_ownership(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", root).returncode == 0
    assert publication(parallel, "v0.5.2").returncode == 0
    original = parallel.record()["members"][0]["start_head"]
    commit_worker(root, "src/alpha.txt", "own work\n")
    commit_worker(
        parallel.work, "src/unrelated-target.txt", "strict synchronization update\n"
    )
    parallel.integrate()
    _git(root, "merge", "-q", "--no-ff", "-m", "refresh target", "origin/develop")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"] == "met"
    )
    assert parallel.record()["members"][0]["start_head"] == original
    commit_worker(root, "src/unclaimed.txt", "still outside ownership\n")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )


@pytest.mark.parametrize("output", ["src/secrets.json", "src/known-gaps.md"])
def test_directory_claim_cannot_create_unapproved_sensitive_or_coordinator_files(
    parallel: Walk, output: str
) -> None:
    root = worker(parallel, "v0.5.2")
    broad = claims(parallel, "v0.5.2", writes=("src/",))
    assert admit(parallel, "v0.5.2", root, broad).returncode == 0
    commit_worker(root, output, '{"fixture": "not a real secret"}\n')
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )
    merge_worker(parallel, root, "v0.5.2")
    _git(parallel.work, "merge", "-q", "--ff-only", "origin/develop")
    _git(parallel.work, "worktree", "remove", str(root))
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )


def test_symlink_worktree_alias_is_refused(parallel: Walk) -> None:
    root = worker(parallel, "v0.5.2")
    alias = parallel.tmp / "worker-alias"
    try:
        alias.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip(
            "This account cannot create symlinks; the Linux qualification exercises this boundary"
        )
    assert "invalid-implementation-worktree" in admit(parallel, "v0.5.2", alias).stdout


def test_missing_active_worker_remains_unverifiable_and_keeps_reservation(
    parallel: Walk,
) -> None:
    alpha, omega = worker(parallel, "v0.5.2"), worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.2", alpha).returncode == 0
    _git(parallel.work, "worktree", "remove", str(alpha))
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "cannot-verify"
    )
    refused = admit(parallel, "v0.5.10", omega)
    assert (
        refused.returncode == ck.EXIT_BLOCKED
        and "active-implementation-unverified" in refused.stdout
    )


def test_coordinator_can_complete_only_original_plan_source_paths(
    parallel: Walk,
) -> None:
    root = worker(parallel, "v0.5.2")
    plan = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"
    assert (
        admit(
            parallel, "v0.5.2", root, claims(parallel, "v0.5.2", writes=(plan,))
        ).returncode
        == 0
    )
    commit_worker(root, "src/alpha.txt", "pending coordinator task from frozen plan\n")
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"]
        == "unmet"
    )
    assert (
        "invalid-coordinator-claims"
        in publication(parallel, "v0.5.2", ["alpha.txt"]).stdout
    )
    assert publication(parallel, "v0.5.2", ["src/alpha.txt"]).returncode == 0
    assert (
        project(parallel, "v0.5.2")[1]["predicates"]["implementation.identity"] == "met"
    )


def test_nested_claim_symlink_escape_is_rejected(
    parallel: Walk, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = worker(parallel, "v0.5.2")
    outside = parallel.tmp / "outside-owned-root"
    outside.mkdir()
    target = outside / "escape.py"
    target.write_text("outside the worker\n", encoding="utf-8")
    try:
        (root / "src").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip(
            "This account cannot create symlinks; Linux qualification exercises the claimed-path boundary"
        )
    proposed = claims(parallel, "v0.5.2", writes=("src/escape.py",))
    before = parallel.record_path().read_bytes()
    refused = admit(parallel, "v0.5.2", root, proposed)
    assert (
        refused.returncode == ck.EXIT_BLOCKED
        and "implementation-path-alias" in refused.stdout
    )
    assert parallel.record_path().read_bytes() == before
    assert target.read_text(encoding="utf-8") == "outside the worker\n"
    # Negative control: removing the literal-path guard admits the same escaped claim inventory.
    # This process-local mutation never changes the CLI source or a production record.
    monkeypatch.setattr(cm, "_literal_path", lambda _root, value: value)
    unguarded = cm._claims(parallel.rctx(), "v0.5", root, proposed)
    assert unguarded["write_paths"] == ["src/escape.py"]
