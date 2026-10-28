"""M5-only future manifest permission; all captures and authority are disposable fixtures."""
from __future__ import annotations

import copy
from types import SimpleNamespace

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, Minor, _no_transport_overrides  # noqa: F401

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
        return SimpleNamespace(lines=[
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
    monkeypatch.setattr(cm, "evaluate_member", lambda *a: SimpleNamespace(lines=[("release.tag", "unmet")]))
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
