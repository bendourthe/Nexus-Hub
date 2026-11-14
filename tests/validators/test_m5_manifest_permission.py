"""M5 manifest and bounded v4.15 outputs; all captures and authority are disposable fixtures."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from .member_declarations import write_wrapper
from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import (  # noqa: F401
    SESSION,
    Minor,
    _no_transport_overrides,
)

# Fixture imports initialize the scripts path before the native modules below.
# isort: split

import approval_binding
import check_plan_completion as ck
import completion_minor as cm
import pytest

MINOR = "v0.5"
VERSION = "v0.5.10"
PREVIOUS = "v0.5.2"
PATH = "MANIFEST.sha256"
FIELD = "manifest_coordinator_permissions"
V415_FIELD = "v415_coordinator_permissions"
V415_READ_FIELD = "v415_ci_read_corrections"
V415_READ_CHECKPOINT = "6a45a253c242a97e09bc953a764c024687042b67"


@pytest.fixture(params=["v4.15.0", "v4.15.2"], ids=["started-zero", "dormant-two"])
def v415_outputs_case(request, tmp_path, monkeypatch, minor_git_seed):
    fx = Minor(tmp_path, monkeypatch, minor_git_seed)
    _git(fx.work, "checkout", "-q", "develop")
    version = request.param
    # Fixture plans for the five original members; never the live plan files, whose text may be edited.
    rel = f"docs/releases/v4/v4.15/plans/{version}-fixture.md"
    for patch in range(5):
        target = fx.work / f"docs/releases/v4/v4.15/plans/v4.15.{patch}-fixture.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# Plan - fixture\n\n**Version**: v4.15.{patch}\n**Slug**: fixture\n**Status**: queued\n\n"
                          "## Phase 1: Build\n\n- [ ] T001 Fixture task src/owned.txt\n", encoding="utf-8")
    for path, text in ((rel, (fx.work / rel).read_text(encoding="utf-8")),
                       ("MANIFEST.sha256", "disposable baseline manifest\n"),
                       ("scripts/lib/installer/legacy_fingerprints.json", "{}\n"),
                       ("docs/README.md", "# Baseline coordinator index\n")):
        target = fx.work / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(fx.work, "remote", "set-url", "--push", "origin", "https://github.com/bendourthe/Nexus-Hub.git")
    fx.commit("original v415 fixture source")
    fx.publish("develop")
    base = _git(fx.work, "rev-parse", "HEAD")
    plan = next(p for p in cm.scan_plans(fx.work, 4, 15) if p.version == version)
    worker = tmp_path / "v415-worker"
    branch = "feat/" + version + "-native-permission-fixture"
    _git(fx.work, "worktree", "add", "-q", "-b", branch, str(worker), base)
    member = {"version": version, "plan_path": rel, "plan_sha256": ck.plan_hash_text(plan.text),
              "source_branch": branch, "target_branch": "develop", "release_version": version, "tag": version,
              "approvals": {"classes": []}, "implementation": {
                  "base_head": base, "worktree": str(worker.resolve()), "branch": branch,
                  "depends_on": [], "read_paths": ["src/input.txt"], "write_paths": ["src/owned.txt"],
                  "started": ck._now()}}
    if version == "v4.15.0":
        member.update(start_head=base, coordinator_paths=["docs/README.md"], started=ck._now())
    ctx = fx.rctx()
    record = {"schema": ck.SCHEMA_MINOR, "scope": "minor", "minor": "v4.15", "repo": "bendourthe/Nexus-Hub",
              "remote_url": ctx.remote_url,
              "repo_root": str(fx.work.resolve()), "worktree": str(fx.work.resolve()), "session_id": SESSION,
              "nonce": "fixture-v415-permission", "start_head": base, "created": ck._now(), "members": [member],
              "approvals": {"classes": [{"class": "archive-minor"}], "target_branch": "develop",
                            "remote_url": ctx.remote_url, "push_remote_url": ctx.push_remote_url, "repo": "bendourthe/Nexus-Hub"},
              "excluded": [], "blockers": [], "pause": None, "completed": None}
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=True) or b"")
    path = fx.rctx().scoped_record_path("minor:v4.15")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")  # Disposable fixture authority only.
    assert cm._verified(ck, fx.rctx(), "v4.15", record)
    return fx, worker, base, version, path


def test_v415_output_page_is_exact_and_does_not_expand_original_scope(v415_outputs_case):
    fx, _worker, _base, version, path = v415_outputs_case
    record = ck.read_record(fx.rctx(), path)
    member = _member(record, version)
    with pytest.raises(cm.MinorMalformed, match="coordinator-path-outside-plan"):
        cm._coordinator_claims(ck, fx.rctx(), record, member, {"write_paths": ["MANIFEST.sha256"]})
    before = path.read_bytes()
    page = cm.v415_output_permission_page(ck, fx.rctx(), "v4.15", record, version,
                                         {"write_paths": ["scripts/lib/installer/legacy_fingerprints.json", "MANIFEST.sha256"]})
    assert page["write_paths"] == ["MANIFEST.sha256", "scripts/lib/installer/legacy_fingerprints.json"]
    assert page["original_read_paths"] == member["implementation"]["read_paths"]
    assert page["original_write_paths"] == member["implementation"]["write_paths"]
    assert page["coordinator_paths"] == member.get("coordinator_paths", [])
    assert page["start_head"] == member.get("start_head")
    assert V415_FIELD not in member and path.read_bytes() == before


def _v415_args(case, *, session=SESSION, paths=None):
    fx, _worker, _base, version, _path = case
    outputs = fx.tmp / "v415-outputs.json"
    outputs.write_text(json.dumps({"write_paths": paths if paths is not None else [
        "MANIFEST.sha256", "scripts/lib/installer/legacy_fingerprints.json"]}), encoding="utf-8")
    return ["--minor", "v4.15", "--member", version, "--session", session,
            "--repo", str(fx.work), "--outputs", str(outputs)]


def _v415_render(case, capsys, *, session=SESSION, paths=None, flags=()):
    fx = case[0]
    fx.capture(session, "fixture prior v415 output decision", at=0.0)
    code, out, err = _cli(capsys, "record", "render", "--action", "permit-outputs",
                          *_v415_args(case, session=session, paths=paths), *flags)
    assert code == 0, out + err
    return out.splitlines()[0]


def _v415_grant(case, capsys, *, paths=None):
    line = _v415_render(case, capsys, paths=paths)
    case[0].capture(SESSION, line)
    code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(case, paths=paths))
    assert code == 0, out + err
    return json.loads(case[4].read_text(encoding="utf-8"))


def _v415_signed_write(case, record):
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(case[4], record)


@pytest.fixture
def v415_ci_case(v415_outputs_case):
    """Patch only a disposable installed copy's checkpoint to its real fixture commit."""
    fx, worker, base, version, path = v415_outputs_case
    assert version == "v4.15.4"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["implementation_controller"] = {"repo_root": str(fx.work.resolve()),
                                            "git_common_dir": cm._common_dir(fx.rctx(), fx.work)}
    _member(record, version)["implementation"]["read_paths"] = ["scripts/ci/profiles.py", "src/input.txt"]
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")
    (worker / "scripts/ci").mkdir(parents=True, exist_ok=True)
    installed = fx.tmp / "ci-installed-scripts"
    installed.mkdir()
    source = Path(__file__).resolve().parents[2] / "scripts"
    for name in ("check_plan_completion.py", "completion_minor.py", "approval_binding.py", "approval_page.py",
                 "repo_host.py", "completion_budget.py", "nexus_process.py"):
        text = (source / name).read_text(encoding="utf-8")
        if name == "completion_minor.py":
            text = text.replace(V415_READ_CHECKPOINT, base)
        (installed / name).write_text(text, encoding="utf-8")
    # The private copy has no row for this fixture's plans; declare them beside it, test-side only.
    declared = write_wrapper(installed)

    def run(*args):
        return subprocess.run([sys.executable, "-B", str(declared), *args],
                              cwd=fx.work, env=fx.env, capture_output=True, text=True, timeout=90, check=False)

    def probe(expression):
        setup = ("import argparse,json,sys; "
                 f"sys.path.insert(0,{str(Path(__file__).resolve().parent)!r}); "
                 "import check_plan_completion as ck; import completion_minor as cm; "
                 "import member_declarations; member_declarations.apply_to(cm); "
                 f"rctx=cm.minor_context(ck,{str(fx.work)!r}); "
                 "record=ck.read_record(rctx,cm.record_file(ck,rctx,'v4.15')); "
                 "member=next(m for m in record['members'] if m['version']=='v4.15.4'); ")
        return subprocess.run([sys.executable, "-B", "-c", setup + expression], cwd=installed,
                              env=fx.env, capture_output=True, text=True, timeout=90, check=False)

    return v415_outputs_case, run, probe


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_read_page_binds_only_the_frozen_reservation(v415_ci_case):
    case, _run, probe = v415_ci_case
    before = case[4].read_bytes()
    result = probe("print(json.dumps(cm.v415_ci_read_correction_page(ck,rctx,'v4.15',record,'v4.15.4')))")
    assert result.returncode == 0, result.stdout + result.stderr
    page = json.loads(result.stdout)
    assert page["path"] == "scripts/ci/profiles.py" and page["checkpoint"] == case[2]
    assert page["original_read_paths"] == ["scripts/ci/profiles.py", "src/input.txt"]
    assert page["start_head"] is None and page["member"] == "v4.15.4"
    assert case[4].read_bytes() == before


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_effective_reads_without_a_capture_remain_original(v415_ci_case):
    case, _run, probe = v415_ci_case
    before = case[4].read_bytes()
    result = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,member)))")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == ["scripts/ci/profiles.py", "src/input.txt"]
    assert case[4].read_bytes() == before


def _v415_ci_args(case, *, session=SESSION):
    return ["--minor", "v4.15", "--member", "v4.15.4", "--session", session, "--repo", str(case[0].work)]


def _v415_ci_grant(v415_ci_case):
    case, run, _probe = v415_ci_case
    case[0].capture(SESSION, "fixture separate CI reservation decision", at=0.0)
    rendered = run("record", "render", "--action", "correct-ci-read", *_v415_ci_args(case))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    case[0].capture(SESSION, rendered.stdout.splitlines()[0])
    granted = run("record", "correct-ci-read", *_v415_ci_args(case))
    assert granted.returncode == 0, granted.stdout + granted.stderr
    return json.loads(case[4].read_text(encoding="utf-8"))


def _v415_ci_add_two(case, *, writes=None):
    fx, _worker, base, _version, path = case
    plan = next(p for p in cm.scan_plans(fx.work, 4, 15) if p.version == "v4.15.2")
    branch = "feat/v4.15.2-native-ci-fixture"
    worker = fx.tmp / "ci-two-worker"
    _git(fx.work, "worktree", "add", "-q", "-b", branch, str(worker), base)
    record = json.loads(path.read_text(encoding="utf-8"))
    record["members"].append({"version": "v4.15.2", "plan_path": plan.rel, "plan_sha256": ck.plan_hash_text(plan.text),
        "source_branch": branch, "target_branch": "develop", "release_version": "v4.15.2", "tag": "v4.15.2",
        "approvals": {"classes": []}})
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")
    claims = fx.tmp / "ci-two-claims.json"
    claims.write_text(json.dumps({"depends_on": [], "read_paths": [],
                                 "write_paths": writes or ["scripts/ci/profiles.py"]}), encoding="utf-8")
    return ["record", "member-implement-start", "--minor", "v4.15", "--member", "v4.15.2", "--session", SESSION,
            "--repo", str(fx.work), "--worktree", str(worker), "--head", base, "--claims", str(claims)]


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_captured_correction_allows_normal_admission_and_raw_claim_resume(v415_ci_case):
    case, run, probe = v415_ci_case
    admission = _v415_ci_add_two(case)
    original = copy.deepcopy(_member(json.loads(case[4].read_text(encoding="utf-8")), "v4.15.4")["implementation"])
    blocked = run(*admission)
    assert blocked.returncode == ck.EXIT_BLOCKED and "implementation-scope-conflict" in blocked.stdout
    granted = _v415_ci_grant(v415_ci_case)
    assert _member(granted, "v4.15.4")["implementation"] == original
    assert _member(granted, "v4.15.4").get("start_head") is None
    admitted = run(*admission)
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    before = case[4].read_bytes()
    claims = case[0].tmp / "ci-four-original-claims.json"
    claims.write_text(json.dumps({k: original[k] for k in ("depends_on", "read_paths", "write_paths")}), encoding="utf-8")
    resumed = run("record", "member-implement-start", *_v415_ci_args(case), "--worktree", str(case[1]),
                  "--head", case[2], "--claims", str(claims))
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert case[4].read_bytes() == before
    effective = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,member)))")
    assert effective.returncode == 0, effective.stdout + effective.stderr
    assert json.loads(effective.stdout) == ["src/input.txt"]
    coordinator = probe("print(cm._coordinator_conflict(ck,rctx,record,next(m for m in record['members'] if m['version']=='v4.15.2'),['scripts/ci/profiles.py'],rctx._git_out('rev-parse','HEAD')))")
    assert coordinator.returncode == 0 and coordinator.stdout.strip() == "False", coordinator.stdout + coordinator.stderr


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_v415_ci_hidden_index_edits_do_not_release_reads_or_allow_admission(v415_ci_case, flag):
    case, run, probe = v415_ci_case
    admission = _v415_ci_add_two(case)
    granted = _v415_ci_grant(v415_ci_case)
    original = copy.deepcopy(_member(granted, "v4.15.4"))
    rel = "scripts/lib/installer/legacy_fingerprints.json"
    target = case[1] / rel
    _git(case[1], "update-index", flag, "--", rel)
    target.write_text('{"unreviewed_hidden_fixture_edit":true}\n', encoding="utf-8")
    assert not _git(case[1], "status", "--porcelain")
    flags = _git(case[1], "ls-files", "-v", "--", rel)
    content, before = target.read_bytes(), case[4].read_bytes()
    effective = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,member)))")
    result = run(*admission)
    assert effective.returncode == 0, effective.stdout + effective.stderr
    assert json.loads(effective.stdout) == original["implementation"]["read_paths"], (
        effective.stdout + result.stdout + result.stderr)
    assert result.returncode == ck.EXIT_BLOCKED and "implementation-scope-conflict" in result.stdout
    assert case[4].read_bytes() == before and target.read_bytes() == content
    assert _git(case[1], "ls-files", "-v", "--", rel) == flags
    assert _member(json.loads(before), "v4.15.4") == original


@pytest.mark.parametrize("rc,flags,expected", [
    (0, "H tracked.txt\0", True), (0, "H path\nh filename.txt\0", True), (0, "", True),
    (0, "h tracked.txt\0", False), (0, "S tracked.txt\0", False), (0, "s tracked.txt\0", False),
    (1, "H tracked.txt\0", False), (-1, "", False), (0, None, False),
    (0, "H tracked.txt", False), (0, "H \0", False), (0, "H tracked.txt\0\0", False),
])
def test_v415_index_flags_visibility_is_nul_delimited_and_fail_closed(rc, flags, expected):
    calls = []

    def run(argv):
        calls.append(argv)
        return rc, flags

    ctx = SimpleNamespace(root=Path("fixture-root"), git="fixture-git", run=run)
    assert cm.v415_index_flags_visible(ctx) is expected
    assert calls == [["fixture-git", "-C", str(ctx.root), "ls-files", "-v", "-z"]]


@pytest.mark.parametrize("error", [OSError("unreadable index"), cm.ObservationUnavailable("index")])
def test_v415_index_flags_visibility_refuses_unavailable_observation(error):
    def unavailable(_argv):
        raise error

    ctx = SimpleNamespace(root=Path("fixture-root"), git="fixture-git", run=unavailable)
    assert cm.v415_index_flags_visible(ctx) is False


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.2"], indirect=True)
@pytest.mark.parametrize("actor", ["controller", "source-worker"])
@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_v415_outputs_hidden_prewrite_refuses_new_render_and_consume(v415_outputs_case, capsys, actor, flag):
    fx, worker, _base, _version, path = v415_outputs_case
    line = _v415_render(v415_outputs_case, capsys)
    fx.capture(SESSION, line)
    root = fx.work if actor == "controller" else worker
    _git(root, "update-index", flag, "--", "MANIFEST.sha256")
    target = root / "MANIFEST.sha256"
    target.write_text("unreviewed hidden original-scope prewrite\n", encoding="utf-8")
    assert not _git(root, "status", "--porcelain")
    flags, content, before = _git(root, "ls-files", "-v", "--", "MANIFEST.sha256"), target.read_bytes(), path.read_bytes()
    rendered, out, err = _cli(capsys, "record", "render", "--action", "permit-outputs", *_v415_args(v415_outputs_case))
    if rendered == 0:
        fx.capture(SESSION, out.splitlines()[0])  # Real capture even on the pre-fix vulnerable path.
    consumed, consumed_out, consumed_err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert rendered != 0 and consumed != 0, out + err + consumed_out + consumed_err
    assert path.read_bytes() == before and target.read_bytes() == content
    assert _git(root, "ls-files", "-v", "--", "MANIFEST.sha256") == flags


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_v415_ci_controller_hidden_prewrite_refuses_new_grant(v415_ci_case, flag):
    case, run, _probe = v415_ci_case
    fx = case[0]
    rel = "scripts/ci/profiles.py"
    target = fx.work / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture tracked controller profile baseline\n", encoding="utf-8")
    fx.commit("fixture track controller profile before capture")
    fx.publish("develop")
    fx.capture(SESSION, "fixture new read correction decision", at=0.0)
    rendered = run("record", "render", "--action", "correct-ci-read", *_v415_ci_args(case))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    fx.capture(SESSION, rendered.stdout.splitlines()[0])
    _git(fx.work, "update-index", flag, "--", rel)
    target.write_text("unreviewed hidden controller profile prewrite\n", encoding="utf-8")
    assert not _git(fx.work, "status", "--porcelain")
    flags, content, before = _git(fx.work, "ls-files", "-v", "--", rel), target.read_bytes(), case[4].read_bytes()
    rendered = run("record", "render", "--action", "correct-ci-read", *_v415_ci_args(case))
    if rendered.returncode == 0:
        fx.capture(SESSION, rendered.stdout.splitlines()[0])
    consumed = run("record", "correct-ci-read", *_v415_ci_args(case))
    assert rendered.returncode != 0 and consumed.returncode != 0, rendered.stdout + rendered.stderr + consumed.stdout + consumed.stderr
    assert case[4].read_bytes() == before and target.read_bytes() == content
    assert _git(fx.work, "ls-files", "-v", "--", rel) == flags


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.2"], indirect=True)
@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_v415_outputs_history_ignores_later_flags_but_new_scope_audit_refuses(v415_outputs_case, capsys, flag):
    fx, _worker, _base, version, path = v415_outputs_case
    granted = _v415_grant(v415_outputs_case, capsys)
    member = _member(granted, version)
    _git(fx.work, "update-index", flag, "--", "docs/README.md")
    before, flags = path.read_bytes(), _git(fx.work, "ls-files", "-v", "--", "docs/README.md")
    assert cm._v415_output_permission_valid(ck, fx.rctx(), granted, member, member[V415_FIELD][0])
    assert not cm._v415_original_scope(ck, fx.rctx(), granted, member, ["MANIFEST.sha256"])
    assert path.read_bytes() == before
    assert _git(fx.work, "ls-files", "-v", "--", "docs/README.md") == flags


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
@pytest.mark.parametrize("change", ["dirty", "later-commit", "broad-read", "write-reservation", "other-write"])
def test_v415_ci_correction_never_releases_other_or_unreviewed_scope(v415_ci_case, change):
    case, run, _probe = v415_ci_case
    admission = _v415_ci_add_two(case, writes=["src/owned.txt"] if change == "other-write" else None)
    if change in ("broad-read", "write-reservation"):
        record = json.loads(case[4].read_text(encoding="utf-8"))
        implementation = _member(record, "v4.15.4")["implementation"]
        implementation["read_paths" if change == "broad-read" else "write_paths"].append(
            "scripts/ci/" if change == "broad-read" else "scripts/ci/profiles.py")
        implementation["read_paths"] = sorted(implementation["read_paths"])
        implementation["write_paths"] = sorted(implementation["write_paths"])
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        case[4].write_text(json.dumps(record), encoding="utf-8")
    _v415_ci_grant(v415_ci_case)
    if change in ("dirty", "later-commit"):
        path = case[1] / "src/owned.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("a later source epoch\n", encoding="utf-8")
        if change == "later-commit":
            _git(case[1], "add", "src/owned.txt")
            _git(case[1], "commit", "-q", "-m", "later fixture source beyond reviewed checkpoint")
    before = case[4].read_bytes()
    result = run(*admission)
    assert result.returncode == ck.EXIT_BLOCKED and "implementation-scope-conflict" in result.stdout
    assert case[4].read_bytes() == before


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
@pytest.mark.parametrize("change", ["missing", "foreign", "dirty-worker", "stale-record", "wrong-member", "production-checkpoint"])
def test_v415_ci_capture_freshness_and_compiled_identity_refuse(v415_ci_case, change):
    case, run, _probe = v415_ci_case
    fx = case[0]
    fx.capture(SESSION, "fixture fresh read reservation decision", at=0.0)
    rendered = run("record", "render", "--action", "correct-ci-read", *_v415_ci_args(case))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    if change != "missing":
        fx.capture("foreign-session" if change == "foreign" else SESSION, rendered.stdout.splitlines()[0])
    if change == "dirty-worker":
        (case[1] / "unreviewed.txt").write_text("dirty source\n", encoding="utf-8")
    elif change in ("stale-record", "wrong-member"):
        record = json.loads(case[4].read_text(encoding="utf-8"))
        if change == "stale-record":
            record["fixture_stale_marker"] = "changed after rendering"
        else:
            _member(record, "v4.15.4")["plan_sha256"] = "0" * 64
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        case[4].write_text(json.dumps(record), encoding="utf-8")
    before = case[4].read_bytes()
    if change == "production-checkpoint":
        result = fx.run("record", "correct-ci-read", *_v415_ci_args(case))
    else:
        result = run("record", "correct-ci-read", *_v415_ci_args(case))
    assert result.returncode != 0, result.stdout + result.stderr
    assert case[4].read_bytes() == before
    assert V415_READ_FIELD not in _member(json.loads(before), "v4.15.4")


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
@pytest.mark.parametrize("hide", ["new-field", "empty-list", "member", "unrelated-state"])
def test_v415_ci_captured_append_cannot_hide_or_expand_transition(v415_ci_case, hide):
    case, run, probe = v415_ci_case
    case[0].capture(SESSION, "fixture private writer injection control", at=0.0)
    rendered = run("record", "render", "--action", "correct-ci-read", *_v415_ci_args(case))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    case[0].capture(SESSION, rendered.stdout.splitlines()[0])
    before = case[4].read_bytes()
    mutation = {"new-field": "target.pop(cm.V415_CI_READ_CORRECTION,None)",
                "empty-list": "target[cm.V415_CI_READ_CORRECTION]=[]",
                "member": "value['members'].remove(target)",
                "unrelated-state": "value['unapproved_authority']='injected'"}[hide]
    result = probe("\noriginal=ck._write_record\ndef injected(path,value):\n"
        "    target=next(m for m in value['members'] if m['version']=='v4.15.4')\n"
        f"    {mutation}\n"
        "    value['approvals_hmac']=ck._sign(value,ck._secret(create=False) or b'')\n"
        "    return original(path,value)\nck._write_record=injected\n"
        f"args=argparse.Namespace(minor='v4.15',member='v4.15.4',session={SESSION!r},repo={str(case[0].work)!r},text=None)\n"
        "cm.cmd_record_correct_ci_read(ck,args)\n")
    assert result.returncode != 0 and "v415-ci-read-" in result.stderr, result.stdout + result.stderr
    assert case[4].read_bytes() == before


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_retained_history_and_original_implementation_are_immutable(v415_ci_case):
    case, _run, probe = v415_ci_case
    _v415_ci_grant(v415_ci_case)
    before = case[4].read_bytes()
    for mutation in ("member.pop(cm.V415_CI_READ_CORRECTION)", "record['members'].remove(member)",
                     "member[cm.V415_CI_READ_CORRECTION][0]['page']['path']='scripts/'",
                     "member['implementation']['read_paths'].remove('scripts/ci/profiles.py')",
                     "member['implementation']['depends_on'].append('v4.15.2')",
                     "member['start_head']=record['start_head']",
                     "member['coordinator_paths']=['src/unapproved-coordinator.txt']"):
        result = probe("\n@cm.minor_writer\ndef mutate(ck,args):\n"
            f"    {mutation}\n"
            "    record['approvals_hmac']=ck._sign(record,ck._secret(create=False) or b'')\n"
            "    ck._write_record(cm.record_file(ck,rctx,'v4.15'),record)\n"
            f"mutate(ck,argparse.Namespace(repo={str(case[0].work)!r},minor='v4.15',session={SESSION!r}))\n")
        assert result.returncode != 0 and "v415-ci-read-" in result.stderr, result.stdout + result.stderr
        assert case[4].read_bytes() == before


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_post_start_candidate_restores_every_raw_read(v415_ci_case):
    case, _run, probe = v415_ci_case
    _v415_ci_grant(v415_ci_case)
    before = case[4].read_bytes()
    result = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,{**member,'start_head':record['start_head']})))")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == ["scripts/ci/profiles.py", "src/input.txt"]
    restore = probe("print(cm._v415_ci_read_restore(ck,rctx,record,member,record['start_head']))")
    assert restore.returncode == 0 and restore.stdout.strip() == "False", restore.stdout + restore.stderr
    assert case[4].read_bytes() == before


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_history_survives_native_resume_without_reopening_capture(v415_ci_case):
    case, run, probe = v415_ci_case
    granted = _v415_ci_grant(v415_ci_case)
    original = copy.deepcopy(_member(granted, "v4.15.4"))
    session = "v415-ci-native-continued-owner"
    case[0].capture(session, "fixture native read correction continuation", at=0.0)
    args = ["--minor", "v4.15", "--session", session, "--repo", str(case[0].work)]
    rendered = run("record", "render", "--action", "resume", *args)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    case[0].capture(session, rendered.stdout.splitlines()[0])
    resumed = run("record", "resume", *args)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    current = json.loads(case[4].read_text(encoding="utf-8"))
    assert current["session_id"] == session
    assert _member(current, "v4.15.4") == original
    result = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,member)))")
    assert result.returncode == 0 and json.loads(result.stdout) == ["src/input.txt"], result.stdout + result.stderr


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.4"], indirect=True)
def test_v415_ci_ordered_native_start_restores_reads_after_two_independent_merges(v415_ci_case):
    case, run, probe = v415_ci_case
    fx, four_worker, base, _version, path = case
    admission = _v415_ci_add_two(case)
    granted = _v415_ci_grant(v415_ci_case)
    original = copy.deepcopy(_member(granted, "v4.15.4"))
    admitted = run(*admission)
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    two = _member(json.loads(path.read_text(encoding="utf-8")), "v4.15.2")
    two_worker = Path(two["implementation"]["worktree"])
    profile = two_worker / "scripts/ci/profiles.py"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("FINAL_INTEGRATED_PROFILE = True\n", encoding="utf-8")
    _git(two_worker, "add", "scripts/ci/profiles.py")
    _git(two_worker, "commit", "-q", "-m", "fixture independent two profile contribution")
    _git(fx.work, "merge", "--no-ff", "-q", two["source_branch"], "-m", "fixture merge independent two")
    merge_two = _git(fx.work, "rev-parse", "HEAD")
    three_worker = fx.tmp / "ci-three-worker"
    three_branch = "feat/v4.15.3-native-ci-fixture"
    _git(fx.work, "worktree", "add", "-q", "-b", three_branch, str(three_worker), merge_two)
    path_three = three_worker / "src/three.txt"
    path_three.parent.mkdir(parents=True, exist_ok=True)
    path_three.write_text("independent third contribution\n", encoding="utf-8")
    _git(three_worker, "add", "src/three.txt")
    _git(three_worker, "commit", "-q", "-m", "fixture independent three contribution")
    _git(fx.work, "merge", "--no-ff", "-q", three_branch, "-m", "fixture merge independent three")
    tip = _git(fx.work, "rev-parse", "HEAD")
    _git(fx.work, "tag", "v4.15.3", tip)
    fx.publish("develop", "v4.15.3")
    _git(four_worker, "merge", "--no-ff", "-q", "origin/develop", "-m", "fixture refresh four from integrated profile")
    record = json.loads(path.read_text(encoding="utf-8"))
    plan = next(p for p in cm.scan_plans(fx.work, 4, 15) if p.version == "v4.15.3")
    record["members"].append({"version": "v4.15.3", "plan_path": plan.rel, "plan_sha256": ck.plan_hash_text(plan.text),
        "source_branch": three_branch, "target_branch": "develop", "tag": "v4.15.3", "release_version": "v4.15.3",
        "approvals": {"classes": []}, "start_head": merge_two, "implementation": {
            "base_head": merge_two, "worktree": str(three_worker.resolve()), "branch": three_branch,
            "read_paths": [], "write_paths": ["src/three.txt"], "depends_on": [], "started": ck._now()}})
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")
    fx.state["pr_by_branch"] = {two["source_branch"]: {"state": "MERGED", "merge_commit": merge_two},
                                three_branch: {"state": "MERGED", "merge_commit": tip}}
    for missing in (two["source_branch"], three_branch):
        fx.state["pr_by_branch"][missing]["state"] = "OPEN"
        fx.save_state()
        denied = probe(f"print(cm._v415_ci_read_restore(ck,rctx,record,member,{tip!r}))")
        assert denied.returncode == 0 and denied.stdout.strip() == "False", denied.stdout + denied.stderr
        fx.state["pr_by_branch"][missing]["state"] = "MERGED"
    fx.save_state()
    # Unrelated full release predicates are fixed fixture inputs. Actual merge ancestry,
    # original contribution scopes, the back-merge tag, restored reads and writer stay native.
    started = probe("\nfrom types import SimpleNamespace\n"
        "cm.evaluate_member=lambda *a,**kw: SimpleNamespace(lines=[('fixture.previous-release','met')],exhausted=False,share_exhausted=False)\n"
        "cm.member_gate=lambda *a,**kw: 'met'\n"
        f"args=argparse.Namespace(minor='v4.15',member='v4.15.4',session={SESSION!r},repo={str(fx.work)!r},head={tip!r},coordinator_claims=None)\n"
        "raise SystemExit(cm.cmd_record_member_start(ck,args))\n")
    assert started.returncode == 0, started.stdout + started.stderr
    current = _member(json.loads(path.read_text(encoding="utf-8")), "v4.15.4")
    assert current["implementation"] == original["implementation"]
    assert current[V415_READ_FIELD] == original[V415_READ_FIELD] and current["start_head"] == tip
    effective = probe("print(json.dumps(cm.effective_read_paths(ck,rctx,record,member,member)))")
    assert effective.returncode == 0 and json.loads(effective.stdout) == original["implementation"]["read_paths"]
    assert (four_worker / "scripts/ci/profiles.py").read_text(encoding="utf-8") == "FINAL_INTEGRATED_PROFILE = True\n"
    assert base != tip
    old = current["plan_path"]
    dest = old.replace("docs/releases/", "docs/archives/")
    old_text = (fx.work / old).read_text(encoding="utf-8")
    archive_text = old_text.replace("docs/releases/v4/v4.15/", "docs/archives/v4/v4.15/")
    target = fx.work / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    (fx.work / old).unlink()
    target.write_text(archive_text, encoding="utf-8")
    fx.commit("fixture signed member archive identity after native start")
    archive_commit = _git(fx.work, "rev-parse", "HEAD")
    archive_hash = ck.plan_hash_text(archive_text)
    record = json.loads(path.read_text(encoding="utf-8"))
    current = _member(record, "v4.15.4")
    current["archived"] = {"from": old, "original_sha256": current["plan_sha256"], "plan_path": dest,
        "plan_sha256": archive_hash, "moved": [[old, dest, _git(fx.work, "rev-parse", f"HEAD:{dest}")]]}
    for refreeze in (False, True):
        if refreeze:
            current.update(plan_path=dest, plan_sha256=archive_hash)
            current["archived"]["close_commit"] = archive_commit
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        path.write_text(json.dumps(record), encoding="utf-8")
        retained = probe("print(cm._v415_ci_read_valid(ck,rctx,record,member,member[cm.V415_CI_READ_CORRECTION][0]))")
        assert retained.returncode == 0 and retained.stdout.strip() == "True", retained.stdout + retained.stderr
        assert current["implementation"] == original["implementation"]
        assert current[V415_READ_FIELD] == original[V415_READ_FIELD]


@pytest.mark.parametrize("handbook_paths", [
    [],
    ["docs/handbooks/handbooks.json", "docs/handbooks/README.md"],
    [f"docs/handbooks/{name}.html{suffix}" for name in ("overview", "distribution", "completion")
     for suffix in ("", ".build.json")],
    [f"docs/handbooks/_sources/{name}/{leaf}" for name in ("overview", "distribution", "completion")
     for leaf in ("model.json", "source.md", "design.css", "evidence.json", "native-composition.html")],
    ["docs/releases/v4/v4.15/development/evidence/{version}-handbooks/" + leaf
     for leaf in ("render.md", "build.json", "render.log", "desktop.png")],
], ids=["manifests", "handbook-index", "handbook-pages", "handbook-sources", "member-evidence"])
def test_v415_genuine_permission_preserves_claims_and_activates_only_at_native_start(
        v415_outputs_case, capsys, handbook_paths):
    fx, worker, base, version, path = v415_outputs_case
    before = json.loads(path.read_text(encoding="utf-8"))
    original = copy.deepcopy(_member(before, version))
    requested = ["MANIFEST.sha256", "scripts/lib/installer/legacy_fingerprints.json",
                 *(p.format(version=version) for p in handbook_paths)]
    granted = _v415_grant(v415_outputs_case, capsys, paths=requested)
    member = _member(granted, version)
    assert member["implementation"] == original["implementation"]
    assert member.get("start_head") == original.get("start_head")
    assert cm._v415_output_permission_valid(ck, fx.rctx(), granted, member, member[V415_FIELD][0])
    additions = member[V415_FIELD][0]["page"]["write_paths"]
    assert additions == sorted(requested)
    assert granted["approvals"] == before["approvals"]
    assert member.get("coordinator_paths", []) == ([*original["coordinator_paths"], *additions]
                                                 if version == "v4.15.0" else [])
    target = worker / PATH
    saved = target.read_bytes()
    target.write_text("fixture changed after permission\n", encoding="utf-8")
    ctx = ck.Context(str(worker / member["plan_path"]), ck.Budget(60))
    assert cm._implementation_paths(ctx, member, base) == ("met" if version == "v4.15.0" else "unmet")
    target.write_bytes(saved)
    if version == "v4.15.2":
        claims = fx.tmp / "v415-coordinator-claims.json"
        claims.write_text(json.dumps({"write_paths": additions}), encoding="utf-8")
        code, out, err = _cli(capsys, "record", "member-start", "--minor", "v4.15", "--member", version,
                              "--session", SESSION, "--repo", str(fx.work), "--head", base,
                              "--coordinator-claims", str(claims))
        assert code == 0, out + err
        active = json.loads(path.read_text(encoding="utf-8"))
        assert _member(active, version)["start_head"] == base
        assert _member(active, version)["coordinator_paths"] == additions
        assert _member(active, version)[V415_FIELD] == member[V415_FIELD]
        assert _member(active, version)["implementation"] == original["implementation"]
    else:
        assert member["coordinator_paths"][:len(original["coordinator_paths"])] == original["coordinator_paths"]
        claims = fx.tmp / "started-v415-coordinator-claims.json"
        before_retry = path.read_bytes()
        for proposed, accepted in ((member["coordinator_paths"], True),
                                   (member["coordinator_paths"][1:], False),
                                   ([*member["coordinator_paths"], "CHANGELOG.md"], False),
                                   (["docs/README.md", "docs/handbooks/completion.html"], False)):
            claims.write_text(json.dumps({"write_paths": proposed}), encoding="utf-8")
            code, out, err = _cli(capsys, "record", "member-start", "--minor", "v4.15", "--member", version,
                                  "--session", SESSION, "--repo", str(fx.work), "--head", base,
                                  "--coordinator-claims", str(claims))
            assert (code == 0) is accepted, out + err
            assert path.read_bytes() == before_retry


def test_v415_output_scope_rejects_nonartifact_aliases_and_duplicates_without_write(v415_outputs_case):
    fx, _worker, _base, version, path = v415_outputs_case
    before = path.read_bytes()
    for paths in ([], [PATH, PATH], [PATH, PATH.lower()], ["docs/handbooks/"], ["docs/handbooks/*.html"],
                  ["../MANIFEST.sha256"], ["scripts/ci/profiles.py"], ["scripts/approval_binding.py"],
                  ["scripts/lib/installer/producer.py"], ["docs/handbooks/_sources/completion/build_presentation.py"],
                  ["docs/handbooks/_sources/foreign/source.md"], ["docs/handbooks.json"],
                  ["catalog/hooks/settings.json"], ["configs/permissions/new.json"]):
        with pytest.raises(ck.Malformed):
            cm.v415_output_permission_page(ck, fx.rctx(), "v4.15", ck.read_record(fx.rctx(), path), version,
                                           {"write_paths": paths})
        assert path.read_bytes() == before


def test_v415_output_permission_preserves_absent_empty_prefix(v415_outputs_case, capsys):
    _fx, _worker, _base, version, path = v415_outputs_case
    record = json.loads(path.read_text(encoding="utf-8"))
    _member(record, version).pop("coordinator_paths", None)
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")  # Disposable original-prefix shape.
    granted = _v415_grant(v415_outputs_case, capsys)
    member = _member(granted, version)
    if version == "v4.15.0":
        assert member["coordinator_paths"] == member[V415_FIELD][0]["page"]["write_paths"]
    else:
        assert "coordinator_paths" not in member


@pytest.mark.parametrize("v415_outputs_case", ["v4.15.0"], indirect=True)
def test_v415_started_retry_preserves_large_original_coordinator_membership(v415_outputs_case):
    fx, _worker, base, version, path = v415_outputs_case
    record = json.loads(path.read_text(encoding="utf-8"))
    member = _member(record, version)
    member["coordinator_paths"] = sorted({p for p in cm._coordinator_paths(fx.rctx(), "v4.15")
                                          if not p.endswith("/") and not cm._sensitive_write(fx.rctx(), p, [])})
    assert len(member["coordinator_paths"]) >= 20
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")
    # Use the public CLI for both the captured grant and the later normal retry.
    args = _v415_args(v415_outputs_case)
    fx.capture(SESSION, "fixture large original coordinator scope", at=0.0)
    rendered = fx.run("record", "render", "--action", "permit-outputs", *args)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    fx.capture(SESSION, rendered.stdout.splitlines()[0])
    granted = fx.run("record", "permit-outputs", *args)
    assert granted.returncode == 0, granted.stdout + granted.stderr
    before = path.read_bytes()
    current = json.loads(before)
    claims = fx.tmp / "large-v415-coordinator-claims.json"
    claims.write_text(json.dumps({"write_paths": _member(current, version)["coordinator_paths"]}), encoding="utf-8")
    started = time.monotonic()
    retried = fx.run("record", "member-start", "--minor", "v4.15", "--member", version, "--session", SESSION,
                     "--repo", str(fx.work), "--head", base, "--coordinator-claims", str(claims))
    elapsed = time.monotonic() - started
    assert retried.returncode == 0, retried.stdout + retried.stderr
    assert path.read_bytes() == before
    print(f"native-large-coordinator-retry {len(member['coordinator_paths'])} original paths {elapsed:.2f}s")


def test_v415_output_permission_refuses_reparse_ancestor_without_touching_outside(v415_outputs_case, capsys):
    fx, _worker, _base, _version, path = v415_outputs_case
    outside = fx.tmp / "outside-handbook-fixture"
    outside.mkdir()
    content = outside / "completion.html"
    content.write_bytes(b"outside fixture bytes must remain private\r\n")
    before_content, before_record = content.read_bytes(), path.read_bytes()
    alias = fx.work / "docs/handbooks"
    assert alias.parent.is_relative_to(fx.work)
    if os.name == "nt":
        linked = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(outside)],
                                capture_output=True, text=True, check=False)
        assert linked.returncode == 0, linked.stdout + linked.stderr
    else:
        alias.symlink_to(outside, target_is_directory=True)
    code, out, err = _cli(capsys, "record", "render", "--action", "permit-outputs",
                          *_v415_args(v415_outputs_case, paths=["docs/handbooks/completion.html"]))
    assert code != 0 and "implementation-path-alias" in out + err
    assert content.read_bytes() == before_content and path.read_bytes() == before_record


@pytest.mark.parametrize("committed", [False, True])
def test_v415_original_scope_rechecks_worker_prewrite_before_consume(v415_outputs_case, capsys, committed):
    fx, worker, _base, _version, path = v415_outputs_case
    before = path.read_bytes()
    line = _v415_render(v415_outputs_case, capsys)
    (worker / PATH).write_text("unclaimed fixture output before capture\n", encoding="utf-8")
    if committed:
        _git(worker, "add", PATH)
        _git(worker, "commit", "-q", "-m", "unclaimed fixture output")
    fx.capture(SESSION, line)
    code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and "original-scope-unverified" in out + err
    assert path.read_bytes() == before


def test_v415_capture_missing_foreign_stale_and_replay_never_write(v415_outputs_case, capsys):
    fx, _worker, _base, version, path = v415_outputs_case
    before = path.read_bytes()
    line = _v415_render(v415_outputs_case, capsys)
    code, _out, _err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and path.read_bytes() == before
    fx.capture("foreign-v415-owner", line)
    code, _out, _err = _cli(capsys, "record", "permit-outputs",
                            *_v415_args(v415_outputs_case, session="foreign-v415-owner"))
    assert code != 0 and path.read_bytes() == before
    fx.capture(SESSION, "Decline")
    code, _out, _err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and path.read_bytes() == before
    fx.capture(SESSION, line)
    changed = json.loads(before)
    changed["blockers"].append({"category": "no-progress", "open": False})
    path.write_text(json.dumps(changed), encoding="utf-8")  # Fixture-only generation change.
    stale = path.read_bytes()
    code, _out, _err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and path.read_bytes() == stale
    granted = _v415_grant(v415_outputs_case, capsys)
    accepted = path.read_bytes()
    code, _out, _err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and path.read_bytes() == accepted
    assert len(_member(granted, version)[V415_FIELD]) == 1


def test_v415_controller_prewrite_cannot_be_legalized_by_captured_permission(v415_outputs_case, capsys):
    fx, _worker, _base, version, path = v415_outputs_case
    line = _v415_render(v415_outputs_case, capsys)
    before = path.read_bytes()
    (fx.work / PATH).write_text("unclaimed coordinator prewrite\n", encoding="utf-8")
    fx.capture(SESSION, line)
    code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and "original-scope-unverified" in out + err
    assert path.read_bytes() == before
    if version == "v4.15.0":
        fx.commit("unclaimed started coordinator contribution")
        code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
        assert code != 0 and "original-scope-unverified" in out + err
        assert path.read_bytes() == before


def test_v415_native_writer_preserves_history_and_rejects_unrelated_capture_mutation(v415_outputs_case, monkeypatch, capsys):
    fx, _worker, _base, version, path = v415_outputs_case
    before = path.read_bytes()
    line = _v415_render(v415_outputs_case, capsys)
    fx.capture(SESSION, line)
    actual_write = ck._write_record
    def unrelated(target, record):
        if _member(record, version).get(V415_FIELD):
            assert ck._MINOR_LEASE.get().get("v415_output_append")
            record["approvals"]["classes"].append({"class": "unrelated-fixture-authority"})
            record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        return actual_write(target, record)
    monkeypatch.setattr(ck, "_write_record", unrelated)
    code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and "unrelated-record-change" in out + err
    assert path.read_bytes() == before
    monkeypatch.setattr(ck, "_write_record", actual_write)
    granted = _v415_grant(v415_outputs_case, capsys)
    accepted = path.read_bytes()
    for change in (lambda r: _member(r, version).pop(V415_FIELD),
                   lambda r: r["members"].remove(_member(r, version)),
                   lambda r: _member(r, version)[V415_FIELD][0]["accepted"].update(text="changed"),
                   lambda r: _member(r, version)[V415_FIELD].append(copy.deepcopy(_member(r, version)[V415_FIELD][0])),
                   lambda r: _member(r, version)["implementation"]["write_paths"].append("src/unapproved.txt"),
                   lambda r: _member(r, version).setdefault("coordinator_paths", []).append("docs/handbooks/foreign.html")):
        record = ck.read_record(fx.rctx(), path)
        change(record)
        with pytest.raises(ck.MinorConflict):
            _v415_signed_write(v415_outputs_case, record)
        assert path.read_bytes() == accepted
    assert _member(granted, version)["implementation"]["write_paths"] == ["src/owned.txt"]


@pytest.mark.parametrize("hide", ["new-field", "empty-list", "member"])
def test_v415_first_captured_append_cannot_hide_its_authority_transition(v415_outputs_case, monkeypatch, capsys, hide):
    fx, _worker, _base, version, path = v415_outputs_case
    before = path.read_bytes()
    line = _v415_render(v415_outputs_case, capsys)
    fx.capture(SESSION, line)
    actual = ck._write_record
    def hidden(target, record):
        if ck._MINOR_LEASE.get().get("v415_output_append"):
            member = _member(record, version)
            if hide == "new-field":
                member.pop(V415_FIELD)
            elif hide == "empty-list":
                member[V415_FIELD] = []
            else:
                record["members"].remove(member)
            record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        return actual(target, record)
    monkeypatch.setattr(ck, "_write_record", hidden)
    code, out, err = _cli(capsys, "record", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0, out + err
    assert path.read_bytes() == before


def test_v415_permission_bootstrap_preserves_approval_block_and_refuses_other_blockers(v415_outputs_case, capsys):
    fx, _worker, _base, version, path = v415_outputs_case
    record = json.loads(path.read_text(encoding="utf-8"))
    record["blockers"] = [{"category": "approval-not-covered", "open": True, "version": version}]
    path.write_text(json.dumps(record), encoding="utf-8")  # Blockers are fixture-only mutable metadata.
    granted = _v415_grant(v415_outputs_case, capsys)
    assert granted["blockers"] == record["blockers"]
    assert cm.load_minor(ck, fx.rctx(), "v4.15", SESSION).forced[1] == ck.EXIT_BLOCKED
    for blocker in ({"category": "no-progress", "open": True}, {"category": "platform-unavailable", "open": True}):
        granted["blockers"].append(blocker)
        path.write_text(json.dumps(granted), encoding="utf-8")
        before = path.read_bytes()
        code, _out, _err = _cli(capsys, "record", "render", "--action", "permit-outputs",
                                *_v415_args(v415_outputs_case, paths=["docs/handbooks/completion.html"]))
        assert code == ck.EXIT_BLOCKED and path.read_bytes() == before
        granted["blockers"].pop()


def test_v415_malformed_retained_provenance_refuses_without_exception(v415_outputs_case, capsys):
    fx, _worker, _base, version, path = v415_outputs_case
    good = _v415_grant(v415_outputs_case, capsys)
    before = path.read_bytes()
    for section, field, value in (("accepted", "text", None), ("accepted", "round_nonce", None),
                                  ("accepted", "rendered_at", True), ("accepted", "authorization_context", None),
                                  ("page", "extra", True), ("page", "original_read_paths", []),
                                  ("page", "implementation_sha256", "0" * 64),
                                  ("page", "controller", {"repo_root": str(fx.work), "extra": True})):
        record = copy.deepcopy(good)
        member = _member(record, version)
        member[V415_FIELD][0][section][field] = value
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        assert not cm._v415_output_permission_valid(ck, fx.rctx(), record, member, member[V415_FIELD][0])
        assert path.read_bytes() == before


@pytest.mark.parametrize("kind", ["read", "write"])
def test_v415_output_permission_rechecks_other_registered_worker_conflicts(v415_outputs_case, capsys, kind):
    fx, _worker, base, _version, path = v415_outputs_case
    record = json.loads(path.read_text(encoding="utf-8"))
    plan = next(p for p in cm.scan_plans(fx.work, 4, 15) if p.version == "v4.15.4")
    other_root = fx.tmp / "other-v415-worker"
    branch = "feat/v4.15.4-other-fixture"
    _git(fx.work, "worktree", "add", "-q", "-b", branch, str(other_root), base)
    other = {"version": plan.version, "plan_path": plan.rel, "plan_sha256": ck.plan_hash_text(plan.text),
             "source_branch": branch, "target_branch": "develop", "release_version": plan.version, "tag": plan.version,
             "approvals": {"classes": []}, "implementation": {
                 "base_head": base, "worktree": str(other_root.resolve()), "branch": branch, "depends_on": [],
                 "read_paths": [PATH] if kind == "read" else [],
                 "write_paths": ["src/other.txt"] if kind == "read" else [PATH], "started": ck._now()}}
    record["members"].append(other)
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    path.write_text(json.dumps(record), encoding="utf-8")
    before = path.read_bytes()
    code, out, err = _cli(capsys, "record", "render", "--action", "permit-outputs", *_v415_args(v415_outputs_case))
    assert code != 0 and "active-conflict" in out + err
    assert path.read_bytes() == before
    assert cm._worker_context(ck, fx.rctx(), record, other, ck.Budget(60), canonical_merged=False)[1] == "met"


def test_v415_permission_survives_native_resume_handoff_and_capture_retention(v415_outputs_case, capsys):
    fx, _worker, base, version, path = v415_outputs_case
    granted = _v415_grant(v415_outputs_case, capsys)
    preserved = copy.deepcopy(_member(granted, version)[V415_FIELD])
    session = "v415-permission-resumed-owner"
    fx.capture(session, "fixture native continuation request", at=0.0)
    code, out, err = _cli(capsys, "record", "render", "--action", "resume", "--minor", "v4.15",
                          "--session", session, "--repo", str(fx.work))
    assert code == 0, out + err
    fx.capture(session, out.splitlines()[0])
    code, out, err = _cli(capsys, "record", "resume", "--minor", "v4.15", "--session", session, "--repo", str(fx.work))
    assert code == 0, out + err
    for folder, pattern in (("prompts", "*.jsonl"), ("consumed-prompts", "*.json")):
        for receipt in (fx.runs / folder).glob(pattern):
            receipt.unlink()  # Only disposable fixture retention.
    resumed = ck.read_record(fx.rctx(), path)
    assert cm._v415_output_permission_valid(ck, fx.rctx(), resumed, _member(resumed, version), preserved[0])
    destination = fx.tmp / "v415-next-controller"
    _git(fx.work, "worktree", "add", "-q", "-b", "v415-next-controller", str(destination), base)
    code, out, err = _cli(capsys, "record", "controller-handoff", "--minor", "v4.15", "--session", session,
                          "--repo", str(fx.work), "--to", str(destination), "--head", base,
                          "--expected-generation", "0", "--apply")
    assert code == 0 and out.startswith("TRANSFERRED "), out + err
    ctx = ck.RepoContext(destination, ck.Budget(60))
    transferred = ck.read_record(ctx, path)
    assert _member(transferred, version)[V415_FIELD] == preserved
    assert cm._v415_output_permission_valid(ck, ctx, transferred, _member(transferred, version), preserved[0])
    assert transferred["session_id"] == session


def test_v415_permission_public_cli_from_isolated_installed_helpers(v415_outputs_case):
    fx, worker, base, version, path = v415_outputs_case
    installed = fx.tmp / "isolated-installed-scripts"
    installed.mkdir()
    source = Path(__file__).resolve().parents[2] / "scripts"
    for name in ("check_plan_completion.py", "completion_minor.py", "approval_binding.py", "approval_page.py",
                 "repo_host.py", "completion_budget.py", "nexus_process.py"):
        shutil.copy2(source / name, installed / name)
    declared = write_wrapper(installed)
    args = _v415_args(v415_outputs_case)
    def public(*operation):
        return subprocess.run([sys.executable, "-B", str(declared), *operation, *args],
                              cwd=fx.work, env=fx.env, capture_output=True, text=True, timeout=45, check=False)
    before = path.read_bytes()
    fx.capture(SESSION, "fixture installed helper decision", at=0.0)
    rendered = public("record", "render", "--action", "permit-outputs")
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    refused = public("record", "permit-outputs")
    assert refused.returncode != 0 and path.read_bytes() == before
    fx.capture(SESSION, rendered.stdout.splitlines()[0])
    accepted = public("record", "permit-outputs")
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    record = ck.read_record(fx.rctx(), path)
    member = _member(record, version)
    assert cm._v415_output_permission_valid(ck, fx.rctx(), record, member, member[V415_FIELD][0])
    for state in ("unmerged", "historical-retired"):
        if state == "historical-retired":
            fx.state["pr_by_branch"] = {member["source_branch"]: {"state": "MERGED", "merge_commit": base, "checks": []}}
            fx.save_state()
            assert worker.parent == fx.tmp
            _git(fx.work, "worktree", "remove", str(worker))  # Clean disposable fixture tree only.
        started = time.monotonic()
        checked = subprocess.run([sys.executable, "-B", str(declared), "check-member",
                                  "--minor", "v4.15", "--member", version, "--session", SESSION,
                                  "--repo", str(fx.work), "--json"],
                                 cwd=fx.work, env=fx.env, capture_output=True, text=True, timeout=45, check=False)
        elapsed = time.monotonic() - started
        assert checked.returncode == ck.EXIT_INCOMPLETE, checked.stdout + checked.stderr
        assert json.loads(checked.stdout.splitlines()[-1])["predicates"]["implementation.identity"] == "met"
        print(f"native-check-member {version} {state} {elapsed:.2f}s")


def _member(record, version=VERSION):
    return next(m for m in record["members"] if m["version"] == version)


def _cli(capsys, *args):
    capsys.readouterr()
    code = ck.main(list(args))
    output = capsys.readouterr()
    return code, output.out, output.err


def _args(fx, session=SESSION):
    return ["--minor", MINOR, "--member", VERSION, "--session", session, "--repo", str(fx.work)]


@pytest.fixture
def permit_case(tmp_path, monkeypatch, minor_git_seed):
    fx = Minor(tmp_path, monkeypatch, minor_git_seed)
    _git(fx.work, "checkout", "-q", "develop")
    (fx.work / PATH).write_text("fixture manifest baseline\n", encoding="utf-8")
    fx.commit("tracked disposable manifest")
    fx.publish("develop")
    created = fx.create()
    assert created.returncode == 0, created.stdout + created.stderr
    record = fx.record()
    member = _member(record)
    base = _git(fx.work, "rev-parse", "HEAD")
    worker = tmp_path / "worker"
    _git(fx.work, "worktree", "add", "-q", "-b", member["source_branch"], str(worker), base)
    member["implementation"] = {
        "base_head": base, "worktree": str(worker), "branch": member["source_branch"],
        "depends_on": [], "read_paths": [], "write_paths": ["src/owned.txt"], "started": ck._now(),
    }
    fx.write_record(record, resign=True)  # This is fixture-only signed state, never real authority.
    descriptor = {"repo": "acme/demo", "minor": MINOR, "member": VERSION, "path": PATH}
    monkeypatch.setattr(cm, "M5_MANIFEST_PERMISSION", descriptor, raising=False)
    return fx, worker, base


def _render(case, capsys, session=SESSION):
    fx, _worker, _base = case
    fx.capture(session, "fixture prior host prompt", at=0.0)
    code, out, err = _cli(capsys, "record", "render", "--action", "permit-manifest", *_args(fx, session))
    assert code == 0, out + err
    return out.splitlines()[0]


def _grant(case, capsys):
    fx, _worker, _base = case
    line = _render(case, capsys)
    fx.capture(SESSION, line)  # Synthetic host capture in the disposable runs directory.
    code, out, err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert code == 0, out + err
    return fx.record()


def _valid(fx, record=None):
    record = record if record is not None else fx.record()
    member = _member(record)
    return cm._manifest_permission_valid(ck, fx.rctx(), record, member, member[FIELD][0])


def _worker_context(case):
    fx, worker, _base = case
    return ck.Context(str(worker / _member(fx.record())["plan_path"]), ck.Budget(60))


def _publish_previous(case, monkeypatch):
    fx, _worker, _base = case
    fx.ship(PREVIOUS)  # Minor.ship records isDraft=False for a published Release.
    assert ck._tag_status(fx.rctx(), PREVIOUS) == "met"
    assert ck._release_status(fx.rctx(), "acme/demo", PREVIOUS) == "met"
    assert cm._tag_in(fx.rctx(), PREVIOUS, case[2]) == "met"
    # Other predecessor duties are fixture doubles. These release predicates and
    # the ordinary member-start tag/back-merge checks still use the real fixture.
    def predecessor(ck_module, rctx, record, member, plan, notices):
        return SimpleNamespace(exhausted=False, share_exhausted=False, lines=[
            ("release.tag", ck._tag_status(rctx, PREVIOUS)),
            ("release.github", ck._release_status(rctx, "acme/demo", PREVIOUS)),
        ])
    monkeypatch.setattr(cm, "evaluate_member", predecessor)


def _activate(case, capsys):
    fx, _worker, base = case
    claims = fx.tmp / "coordinator-claims.json"
    claims.write_text('{"write_paths": ["MANIFEST.sha256"]}', encoding="utf-8")
    return _cli(capsys, "record", "member-start", *_args(fx), "--head", base,
                "--coordinator-claims", str(claims))


def _signed_write(fx, record):
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(fx.record_path(), record)


def test_genuine_fixture_capture_is_dormant_until_normal_publication(permit_case, monkeypatch, capsys):
    fx, worker, base = permit_case
    before = fx.record()
    original = approval_binding.canonical(_member(before)["implementation"])
    granted = _grant(permit_case, capsys)
    assert len(_member(granted)[FIELD]) == 1 and _valid(fx)
    assert approval_binding.canonical(_member(granted)["implementation"]) == original
    assert not _member(granted).get("start_head") and PATH not in _member(granted).get("coordinator_paths", [])
    assert {k: v for k, v in granted.items() if k not in ("members", "approvals_hmac")} == {
        k: v for k, v in before.items() if k not in ("members", "approvals_hmac")
    }
    target = worker / PATH
    saved = target.read_bytes()
    target.write_bytes(b"unclaimed fixture output\n")
    assert cm._implementation_paths(_worker_context(permit_case), _member(granted), base) == "unmet"
    target.write_bytes(saved)
    # The permission alone cannot skip the unreleased predecessor.
    monkeypatch.setattr(cm, "evaluate_member", lambda *a: SimpleNamespace(exhausted=False, share_exhausted=False, lines=[("release.tag", "unmet")]))
    code, _out, _err = _activate(permit_case, capsys)
    assert code != 0 and not _member(fx.record()).get("start_head")
    _publish_previous(permit_case, monkeypatch)
    code, out, err = _activate(permit_case, capsys)
    assert code == 0, out + err
    active = fx.record()
    assert _member(active)["coordinator_paths"] == [PATH]
    assert _member(active)["start_head"] == base and _valid(fx, active)
    assert approval_binding.canonical(_member(active)["implementation"]) == original
    target.write_bytes(b"authorized fixture regeneration\n")
    assert cm._implementation_paths(_worker_context(permit_case), _member(active), base) == "met"
    assert ck._tag_status(fx.rctx(), VERSION) == "unmet"
    assert ck._release_status(fx.rctx(), "acme/demo", VERSION) == "unmet"


def test_uncaptured_stale_foreign_and_replay_rounds_refuse(permit_case, capsys):
    fx, _worker, _base = permit_case
    before = fx.record()
    line = _render(permit_case, capsys)
    code, _out, _err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert code != 0 and fx.record() == before
    fx.capture("foreign-fixture-session", line, at=0.0)
    code, _out, _err = _cli(capsys, "record", "permit-manifest", *_args(fx, "foreign-fixture-session"))
    assert code != 0 and fx.record() == before
    fx.capture(SESSION, line)
    changed = fx.record()
    changed.setdefault("blockers", []).append({"category": "no-progress", "open": False})
    fx.write_record(changed, resign=False)  # Unsigned blocker metadata still changes raw generation.
    code, _out, _err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert code != 0 and FIELD not in _member(fx.record())
    granted = _grant(permit_case, capsys)
    code, _out, _err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert code != 0 and fx.record() == granted


def test_original_scope_refuses_dirty_and_committed_manifest_before_capture(permit_case, capsys):
    fx, worker, _base = permit_case
    before = fx.record()
    (worker / PATH).write_text("already unclaimed\n", encoding="utf-8")
    code, _out, _err = _cli(capsys, "record", "render", "--action", "permit-manifest", *_args(fx))
    assert code != 0 and fx.record() == before
    _git(worker, "add", PATH)
    _git(worker, "commit", "-q", "-m", "unclaimed disposable manifest")
    code, _out, _err = _cli(capsys, "record", "render", "--action", "permit-manifest", *_args(fx))
    assert code != 0 and fx.record() == before


def test_original_scope_is_rechecked_before_coordinator_activation(permit_case, monkeypatch, capsys):
    fx, worker, _base = permit_case
    granted = _grant(permit_case, capsys)
    _publish_previous(permit_case, monkeypatch)
    (worker / PATH).write_text("written before activation\n", encoding="utf-8")
    code, out, err = _activate(permit_case, capsys)
    assert code != 0 and "manifest-permission-original-scope-unverified" in out + err
    assert fx.record() == granted
    _git(worker, "add", PATH)
    _git(worker, "commit", "-q", "-m", "premature fixture manifest")
    code, out, err = _activate(permit_case, capsys)
    assert code != 0 and "manifest-permission-original-scope-unverified" in out + err
    assert fx.record() == granted


def test_active_manifest_claim_conflicts_and_dormant_permission_reserves_nothing(permit_case, monkeypatch, capsys):
    fx, _worker, base = permit_case
    granted = _grant(permit_case, capsys)
    assert PATH not in _member(granted)["implementation"]["write_paths"]
    assert PATH not in _member(granted).get("coordinator_paths", [])
    _publish_previous(permit_case, monkeypatch)
    record = fx.record()
    previous = _member(record, PREVIOUS)
    other = fx.tmp / "other-worker"
    _git(fx.work, "worktree", "add", "-q", "-b", previous["source_branch"], str(other), base)
    previous["implementation"] = {"base_head": base, "worktree": str(other), "branch": previous["source_branch"],
        "depends_on": [], "read_paths": [], "write_paths": [PATH], "started": ck._now()}
    fx.write_record(record, resign=True)
    code, out, _err = _activate(permit_case, capsys)
    assert code != 0 and "coordinator-scope-conflict" in out
    # Conflict evaluation in the competing member's direction proves that the
    # dormant permission itself reserves nothing. Retirement is not simulated.
    assert not cm._coordinator_conflict(ck, fx.rctx(), record, previous, [PATH], base)


def test_permission_bounds_provenance_and_non_string_text_fail_closed(permit_case, capsys):
    fx, _worker, _base = permit_case
    good = _grant(permit_case, capsys)
    for section, field, value in [
        ("page", "member", "v0.5.2"), ("page", "path", "./MANIFEST.sha256"),
        ("page", "path", ".github/workflows/ci.yml"), ("page", "implementation_sha256", "0" * 64),
        ("page", "plan_sha256", "0" * 64), ("page", "extra", True),
        ("accepted", "text", None), ("accepted", "rendered_at", True),
        ("accepted", "authorization_context", {"origin": "invented"}),
    ]:
        record = copy.deepcopy(good)
        _member(record)[FIELD][0][section][field] = value
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        assert not _valid(fx, record), (section, field, value)
    record = copy.deepcopy(good)
    _member(record)["implementation"]["write_paths"].append("src/other.txt")
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    assert not _valid(fx, record)


def test_prefix_and_append_permit_are_enforced_by_native_writer(permit_case, monkeypatch, capsys):
    fx, _worker, _base = permit_case
    before = fx.record()
    monkeypatch.setattr(approval_binding, "_clock", lambda: 1)
    granted = _grant(permit_case, capsys)
    assert type(_member(granted)[FIELD][0]["accepted"]["rendered_at"]) is int
    for alias in (1.0, True):
        snapshot = ck.read_record(fx.rctx(), fx.record_path())
        _member(snapshot)[FIELD][0]["accepted"]["rendered_at"] = alias
        assert snapshot == granted  # Ordinary Python equality misses both changes.
        with pytest.raises(ck.MinorConflict):
            _signed_write(fx, snapshot)
        assert fx.record() == granted
    for mutate in (
        lambda r: _member(r).pop(FIELD),
        lambda r: _member(r)[FIELD].append(copy.deepcopy(_member(r)[FIELD][0])),
        lambda r: _member(r)[FIELD][0]["accepted"].update(text="changed"),
        lambda r: r["members"].remove(_member(r)),
        lambda r: _member(r)[FIELD][0]["accepted"].update(rendered_at=True),
    ):
        snapshot = ck.read_record(fx.rctx(), fx.record_path())
        mutate(snapshot)
        with pytest.raises(ck.MinorConflict):
            _signed_write(fx, snapshot)
        assert fx.record() == granted
    # Restore only disposable fixture bytes, then prove that even an authentic
    # copied entry cannot be appended by another native writer without its permit.
    fx.write_record(before, resign=True)
    snapshot = ck.read_record(fx.rctx(), fx.record_path())
    _member(snapshot)[FIELD] = copy.deepcopy(_member(granted)[FIELD])
    with pytest.raises(ck.MinorConflict):
        _signed_write(fx, snapshot)
    assert FIELD not in _member(fx.record())


def test_permission_survives_later_resume_and_capture_retention(permit_case, capsys):
    fx, _worker, _base = permit_case
    granted = _grant(permit_case, capsys)
    preserved = approval_binding.canonical(_member(granted)[FIELD])
    new_session = "fixture-resumed-session"
    fx.capture(new_session, "fixture prior resume request", at=0.0)
    code, out, err = _cli(capsys, "record", "render", "--action", "resume", "--minor", MINOR,
                          "--session", new_session, "--repo", str(fx.work))
    assert code == 0, out + err
    fx.capture(new_session, out.splitlines()[0])
    code, out, err = _cli(capsys, "record", "resume", "--minor", MINOR, "--session", new_session,
                          "--repo", str(fx.work))
    assert code == 0, out + err
    for folder, pattern in (("prompts", "*.jsonl"), ("consumed-prompts", "*.json")):
        for file in (fx.runs / folder).glob(pattern):
            file.unlink()  # Disposable fixture capture retention only.
    assert _valid(fx)
    assert approval_binding.canonical(_member(fx.record())[FIELD]) == preserved
    resumed = fx.record()
    record_path = fx.record_path()
    target = fx.tmp / "next-controller"
    _git(fx.work, "worktree", "add", "-q", "-b", "next-controller", str(target), "origin/develop")
    head = _git(target, "rev-parse", "HEAD")
    assert head == permit_case[2]
    # All fixture pull requests remain open. The real native handoff validates
    # the fresh integration tip, registered target, frozen plans and signed state.
    code, out, err = _cli(capsys, "record", "controller-handoff", "--minor", MINOR,
                          "--session", new_session, "--repo", str(fx.work), "--to", str(target),
                          "--head", head, "--expected-generation", "0", "--apply")
    assert code == 0 and out.startswith("TRANSFERRED "), out + err
    target_ctx = ck.RepoContext(target, ck.Budget(60))
    moved = ck.read_record(target_ctx, record_path)
    assert isinstance(moved, ck.MinorSnapshot)
    cm.require_controller(ck, target_ctx, moved, record_path)
    assert moved["implementation_controller"]["repo_root"] == str(target)
    assert moved["implementation_controller"]["generation"] == 1
    assert moved["session_id"] == new_session
    assert approval_binding.canonical(_member(moved)[FIELD]) == preserved
    assert cm._manifest_permission_valid(ck, target_ctx, moved, _member(moved), _member(moved)[FIELD][0])
    assert {k: v for k, v in moved.items() if k not in ("implementation_controller", "approvals_hmac")} == {
        k: v for k, v in resumed.items() if k not in ("implementation_controller", "approvals_hmac")
    }
    state = cm.load_minor(ck, ck.RepoContext(target, ck.Budget(60)), MINOR, new_session)
    assert state.forced is None and state.record is not None


@pytest.mark.parametrize("committed", [False, True])
def test_original_scope_is_rechecked_after_render_before_consume(permit_case, capsys, committed):
    fx, worker, _base = permit_case
    before = fx.record_path().read_bytes()
    line = _render(permit_case, capsys)
    (worker / PATH).write_text("late unclaimed manifest\n", encoding="utf-8")
    if committed:
        _git(worker, "add", PATH)
        _git(worker, "commit", "-q", "-m", "late unclaimed disposable manifest")
    fx.capture(SESSION, line)
    code, _out, _err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert code != 0 and fx.record_path().read_bytes() == before


def test_captured_command_cannot_append_unrelated_authority(permit_case, monkeypatch, capsys):
    fx, _worker, _base = permit_case
    before = fx.record_path().read_bytes()
    line = _render(permit_case, capsys)
    fx.capture(SESSION, line)
    actual_write = ck._write_record
    intercepted = []
    def add_unrelated_authority(path, record):
        if _member(record).get(FIELD):
            # This runs inside the genuine command's append permit and lease.
            # The injection is confined to disposable signed fixture state.
            assert ck._MINOR_LEASE.get().get("manifest_permission_append")
            record["approvals"]["classes"].append({"class": "unrelated-fixture-authority"})
            record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
            intercepted.append(True)
        return actual_write(path, record)
    monkeypatch.setattr(ck, "_write_record", add_unrelated_authority)
    code, out, err = _cli(capsys, "record", "permit-manifest", *_args(fx))
    assert intercepted == [True]
    assert code != 0 and "manifest-permission-unrelated-record-change" in out + err
    assert fx.record_path().read_bytes() == before


def test_approval_page_shows_exact_dormant_scope_and_publication_order(permit_case, capsys):
    fx, _worker, _base = permit_case
    before = fx.record_path().read_bytes()
    fx.capture(SESSION, "fixture prior page request", at=0.0)
    code, out, err = _cli(capsys, "record", "render", "--action", "permit-manifest", "--page", *_args(fx))
    assert code == 0, out + err
    assert VERSION in out and PATH in out and "acme/demo" in out
    assert "one dormant publication duty" in out
    assert "original worker claims stay unchanged" in out
    assert "no immediate file write or release" in out
    assert "preceding release, its back-merge" in out
    assert "clean original scope and no active claim conflict" in out
    assert "Decline leaves this publication file unapproved" in out
    assert fx.record_path().read_bytes() == before


def test_parser_overrides_and_unpatched_production_descriptor_refuse(permit_case, capsys):
    fx, _worker, _base = permit_case
    before = fx.record_path().read_bytes()
    for flag, value in (("--path", PATH), ("--class", "release"), ("--merge", "0" * 40)):
        with pytest.raises(SystemExit) as stopped:
            _cli(capsys, "record", "permit-manifest", *_args(fx), flag, value)
        assert stopped.value.code == ck.EXIT_MALFORMED
        assert flag in capsys.readouterr().err
        assert fx.record_path().read_bytes() == before
    # The existing isolated CLI launcher imports the production descriptor in a
    # fresh interpreter. The in-process fixture override cannot authorize it.
    fx.capture(SESSION, "fixture production-scope refusal request", at=0.0)
    refused = fx.run("record", "render", "--action", "permit-manifest", *_args(fx))
    assert refused.returncode == ck.EXIT_MALFORMED
    assert "manifest-permission-outside-reviewed-member" in refused.stdout + refused.stderr
    assert fx.record_path().read_bytes() == before
