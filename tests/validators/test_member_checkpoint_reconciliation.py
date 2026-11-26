"""Fixed .9 checkpoint adoption using disposable Git, keys, and native captures only."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from .test_v4159_t027_disposition import ab, ap, ck, cm, git, trial  # noqa: F401
from .test_codex_transcript_approval import Transcript


ADOPTED = "catalog/agents/planner.md"
PLUGIN = ".claude-plugin/plugin.json"


def commit(root: Path, path: str, text: str = "private checkpoint\n") -> str:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    git(root, "add", "--", path)
    git(root, "commit", "-q", "-m", "private checkpoint")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def checkpoint(trial, monkeypatch):
    base = git(trial.root, "rev-parse", "HEAD")
    git(trial.root, "update-ref", "refs/remotes/origin/develop", base)
    trial.controllerctx = trial.ctx
    worker = trial.root.parent / "worker"
    git(trial.root, "worktree", "add", "-q", "-b", cm.T027_BRANCH, str(worker), base)
    trial.root = worker
    trial.ctx = ck.Context(str(worker / cm.T027_PLAN), ck.Budget(120))
    member = trial.record["members"][0]
    member["implementation"] = {"worktree": str(trial.root), "branch": cm.T027_BRANCH,
        "base_head": base, "started": ck._now(), "depends_on": [], "read_paths": [],
        "write_paths": [cm.T027_PLAN]}
    trial.record["approvals_hmac"] = ck._sign(trial.record, trial.key)
    trial.path.write_text(json.dumps(trial.record), encoding="utf-8")
    trial.record = ck.MinorSnapshot(dict(trial.record), trial.path, trial.path.read_bytes(), trial.ctx)
    trial.base, trial.member = base, member
    trial.head = commit(trial.root, ADOPTED)
    trial.scope = {"write_paths": [cm.CHECKPOINT_FUTURE]}
    monkeypatch.setattr(ck, "_gh_json", lambda *_args, **_kwargs: ck.GH_NOT_FOUND)
    return trial


def page(fixture, **changes):
    args = {"token": "v4.15", "version": "v4.15.9", "head": fixture.head, "scope": fixture.scope}
    args.update(changes)
    return cm.checkpoint_page(ck, fixture.controllerctx, record=fixture.record, **args)


def accept(fixture, monkeypatch, *, key="checkpoint-round"):
    value = copy.deepcopy(page(fixture))
    clock = 1000.0 + 10 * len(fixture.record.get(cm.CHECKPOINT_FIELD, []))
    monkeypatch.setattr(ab, "_clock", lambda: clock)
    pending = ab.render(fixture.runs, key, fixture.key, action=cm.CHECKPOINT_ACTION,
        scope="v4.15", page=value, session="fixture-owner", allow_short_reply=False)
    reply = pending["paste_lines"][0]
    captures = fixture.runs / "prompts" / (hashlib.sha256(b"fixture-owner").hexdigest() + ".jsonl")
    captures.parent.mkdir(exist_ok=True)
    rows = [{"session": "fixture-owner", "prompt": ab.digest("private ordinary request"), "at": clock - 1, "event_id": "initial-" + key},
        {"session": "fixture-owner", "prompt": ab.digest(reply), "at": clock + 1, "event_id": key, "permission_mode": "bypassPermissions"}]
    with captures.open("a", encoding="utf-8") as handle:
        handle.write("".join(json.dumps(row) + "\n" for row in rows))
    consumed, _ = ab.consume(fixture.runs, key, fixture.key, action=cm.CHECKPOINT_ACTION,
        live_page=value, session="fixture-owner", required_session="fixture-owner")
    entry = {"page": value, "accepted": {"at": ck._now(), "page_sha256": cm._amendment_digest(value),
        "round_nonce": consumed["nonce"], "code": consumed["code"], "rendered_at": consumed["rendered_at"],
        "text": ab.pasted(consumed), "allow_short_reply": False, "authorization_context": consumed["capture"]}}
    fixture.record.setdefault(cm.CHECKPOINT_FIELD, []).append(entry)
    fixture.record["approvals_hmac"] = ck._sign(fixture.record, fixture.key)
    return entry


def test_checkpoint_exception_paths_and_approval_line_remain_exact():
    assert cm.CHECKPOINT_EXCEPTIONS == {
        "docs/handbooks/_sources/distribution/evidence.json",
        "docs/handbooks/_sources/overview/evidence.json",
        "docs/releases/v4/v4.15/development/v4.15.9-coordinator-deltas.md",
        "tests/integrations/test_copilot_hermes_native.py",
        "tests/integrations/test_kimi_native.py",
    }
    assert ap.plain_line("reconcile-member-checkpoint", "v4.15", "ABCDEFGH") == (
        "Accept current v4.15.9 checkpoint and prospective T020 file (approval ABCDEFGH)")


def test_checkpoint_manifest_is_exact_raw_blob_mode_status(checkpoint):
    value = page(checkpoint)
    assert value["checkpoint_rows"] == cm._checkpoint_rows(checkpoint.ctx, checkpoint.base, checkpoint.head)
    row, = value["checkpoint_rows"]
    assert row == [ADOPTED, "000000", "100644", "0" * 40,
        git(checkpoint.root, "rev-parse", f"HEAD:{ADOPTED}"), "A"]
    assert value["head"] == checkpoint.head
    assert value["tree"] == git(checkpoint.root, "rev-parse", "HEAD^{tree}")
    assert value["base"] == value["integration_tip"] == checkpoint.base
    assert value["prospective"] == [cm.CHECKPOINT_FUTURE]


@pytest.mark.parametrize("changes", [{"token": "v4.16"}, {"version": "v4.15.8"},
    {"head": "0" * 40}, {"scope": {"write_paths": [ADOPTED]}},
    {"scope": {"write_paths": [cm.CHECKPOINT_FUTURE, ADOPTED]}}, {"scope": {"write_paths": ["catalog/"]}}])
def test_exact_member_head_and_future_scope_required(checkpoint, changes):
    with pytest.raises((ck.Malformed, cm.MinorMalformed)):
        page(checkpoint, **changes)


@pytest.mark.parametrize("path", sorted(cm.CHECKPOINT_EXCEPTIONS))
def test_five_exact_exceptions_can_be_adopted(checkpoint, path):
    checkpoint.head = commit(checkpoint.root, path)
    assert path in [row[0] for row in page(checkpoint)["checkpoint_rows"]]


@pytest.mark.parametrize("path", ["catalog/hooks/private.py", ".github/workflows/private.yml",
    "configs/permissions.json", "private/secret.txt", "docs/handbooks/_sources/other/evidence.json"])
def test_sensitive_or_undeclared_paths_refuse(checkpoint, path):
    checkpoint.head = commit(checkpoint.root, path)
    with pytest.raises(ck.Malformed, match="outside-bounds"):
        page(checkpoint)


def test_plugin_is_visible_outstanding_and_never_adopted(checkpoint):
    checkpoint.head = commit(checkpoint.root, PLUGIN, "{}\n")
    value = page(checkpoint)
    assert [row[0] for row in value["remaining_uncovered"]] == [PLUGIN]
    assert PLUGIN not in [row[0] for row in value["checkpoint_rows"]]


@pytest.mark.parametrize("drift", ["working", "staged", "assume-unchanged", "skip-worktree"])
def test_dirty_or_hidden_index_refuses(checkpoint, drift):
    if drift in {"assume-unchanged", "skip-worktree"}:
        git(checkpoint.root, "update-index", "--" + drift, "--", ADOPTED)
    else:
        (checkpoint.root / ADOPTED).write_text("changed after checkpoint\n", encoding="utf-8")
        if drift == "staged":
            git(checkpoint.root, "add", "--", ADOPTED)
    with pytest.raises(ck.Malformed, match="not-clean"):
        page(checkpoint)


@pytest.mark.parametrize("flag", ["assume-unchanged", "skip-worktree"])
def test_implementation_coverage_refuses_hidden_edits_after_acceptance(checkpoint, monkeypatch, flag):
    accept(checkpoint, monkeypatch)
    assert cm._implementation_paths(checkpoint.ctx, checkpoint.member, record=checkpoint.record, ck=ck) == "met"
    git(checkpoint.root, "update-index", "--" + flag, "--", ADOPTED)
    (checkpoint.root / ADOPTED).write_text("hidden after acceptance\n", encoding="utf-8")
    assert cm._implementation_paths(checkpoint.ctx, checkpoint.member, record=checkpoint.record, ck=ck) == "cannot-verify"


def test_stale_record_generation_refuses(checkpoint):
    checkpoint.path.write_bytes(checkpoint.path.read_bytes() + b" ")
    with pytest.raises(ck.MinorConflict, match="record-changed"):
        page(checkpoint)


def test_unavailable_worker_and_fresh_conflict_refuse(checkpoint, monkeypatch):
    def unavailable(*_args):
        raise cm.MinorMalformed("checkpoint-worker-unverified")
    monkeypatch.setattr(cm, "_checkpoint_worker", unavailable)
    with pytest.raises((ck.Malformed, cm.MinorMalformed), match="worker-unverified"):
        page(checkpoint)
    monkeypatch.setattr(cm, "_checkpoint_worker", lambda *_args: checkpoint.ctx)
    monkeypatch.setattr(cm, "_coordinator_conflict", lambda *_args: True)
    with pytest.raises(ck.Malformed, match="active-conflict"):
        page(checkpoint)


def test_accepted_bytes_are_separate_from_future_permissions(checkpoint, monkeypatch):
    before = copy.deepcopy(checkpoint.record["members"])
    accept(checkpoint, monkeypatch)
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, checkpoint.record)
    rows, future = cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member, checkpoint.base, "HEAD")
    assert set(rows) == {ADOPTED} and future == [cm.CHECKPOINT_FUTURE]
    assert cm._permitted_implementation_writes(ck, checkpoint.record, checkpoint.member) == []
    assert checkpoint.record["members"] == before
    checkpoint.head = commit(checkpoint.root, cm.CHECKPOINT_FUTURE, "legitimate T020 work\n")
    assert cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member, checkpoint.base, "HEAD") == (rows, future)


@pytest.mark.parametrize("drift", ["blob", "mode", "delete"])
def test_later_checkpoint_transition_drift_refuses(checkpoint, monkeypatch, drift):
    accept(checkpoint, monkeypatch)
    if drift == "blob":
        commit(checkpoint.root, ADOPTED, "new bytes require new approval\n")
    elif drift == "mode":
        git(checkpoint.root, "update-index", "--chmod=+x", "--", ADOPTED)
        git(checkpoint.root, "commit", "-q", "-m", "private mode change")
    else:
        git(checkpoint.root, "rm", "-q", "--", ADOPTED)
        git(checkpoint.root, "commit", "-q", "-m", "private deletion")
    with pytest.raises(cm.MinorMalformed, match="contribution-changed"):
        cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member, checkpoint.base, "HEAD")


@pytest.mark.parametrize("field,value", [("head", "1" * 40), ("base", "2" * 40),
    ("tree", "3" * 40), ("original_sha256", "4" * 64), ("prospective", [ADOPTED])])
def test_receipt_tampering_refuses(checkpoint, monkeypatch, field, value):
    entry = accept(checkpoint, monkeypatch)
    entry["page"][field] = value
    assert not cm.checkpoint_entry_valid(ck, checkpoint.ctx, checkpoint.record)


@pytest.mark.parametrize("module", [ck, cm, ab])
def test_mixed_protocol_refuses_but_legacy_signature_is_unchanged(checkpoint, monkeypatch, module):
    legacy = ck._sign(checkpoint.record, checkpoint.key)
    accept(checkpoint, monkeypatch)
    monkeypatch.setattr(module, "CHECKPOINT_PROTOCOL", 0)
    with pytest.raises(ck.MinorConflict, match="incompatible"):
        ck._sign(checkpoint.record, checkpoint.key)
    restored = dict(checkpoint.record)
    restored.pop(cm.CHECKPOINT_FIELD)
    assert ck._sign(restored, checkpoint.key) == legacy


def test_no_unleased_append_or_history_rewrite(checkpoint, monkeypatch):
    before = copy.deepcopy(dict(checkpoint.record))
    accept(checkpoint, monkeypatch)
    with pytest.raises(ck.MinorConflict, match="append-not-captured"):
        cm.check_checkpoint_write(ck, checkpoint.ctx, before, checkpoint.record)
    before = copy.deepcopy(dict(checkpoint.record))
    checkpoint.record[cm.CHECKPOINT_FIELD][0]["accepted"]["text"] = "Continue"
    with pytest.raises(ck.MinorConflict, match="history-changed"):
        cm.check_checkpoint_write(ck, checkpoint.ctx, before, checkpoint.record)


def test_private_native_cli_render_consume_coverage_and_replay(checkpoint, monkeypatch, capsys):
    """Real argument parser, page, transcript verifier, lease, and atomic record writer.

    The record loader and controller context are supplied by the private fixture;
    hosting calls are stubbed. This does not prove production authorization.
    """
    native_load_minor = cm.load_minor
    private_origin = checkpoint.root.parent / "private-origin.git"
    git(checkpoint.controllerctx.root, "clone", "-q", "--bare", "--shared", str(checkpoint.controllerctx.root), str(private_origin))
    git(checkpoint.controllerctx.root, "remote", "add", "origin", str(private_origin))
    home = checkpoint.root.parent / "private-home"
    home.mkdir()
    (checkpoint.runs / ".secret").write_bytes(checkpoint.key)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.delenv("NEXUS_RUNNER_LAUNCH", raising=False)
    session = "01a14365-125e-7213-b5e9-9a0702a651c8"
    canonical = checkpoint.runs / (ck.record_key(checkpoint.controllerctx.root, "bendourthe/nexus-hub", "minor:v4.15") + ".json")
    checkpoint.path.rename(canonical)
    checkpoint.path = canonical
    checkpoint.record["session_id"] = session
    checkpoint.record["members"][0]["implementation"]["read_paths"] = [cm.T027_EVIDENCE]
    checkpoint.record["approvals_hmac"] = ck._sign(checkpoint.record, checkpoint.key)
    checkpoint.path.write_text(json.dumps(checkpoint.record), encoding="utf-8")
    def load(*_args):
        raw = checkpoint.path.read_bytes()
        return ck.MinorSnapshot(json.loads(raw), checkpoint.path, raw, checkpoint.controllerctx)
    monkeypatch.setattr(cm, "repo_context", lambda *_args: checkpoint.controllerctx)
    monkeypatch.setattr(cm, "record_file", lambda *_args: checkpoint.path)
    monkeypatch.setattr(cm, "_record_for_add_class", load)
    monkeypatch.setattr(ck, "_host_cwds", lambda *_args: {str(checkpoint.controllerctx.root)})
    log = Transcript(home, checkpoint.controllerctx.root, float(int(time.time()) - 10), session=session)
    log.now += 1
    monkeypatch.setattr(ab, "_clock", lambda: log.now)
    scopefile = home / "scope.json"
    scopefile.write_text(json.dumps(checkpoint.scope), encoding="utf-8")
    common = ["--minor", "v4.15", "--member", "v4.15.9", "--head", checkpoint.head,
        "--scope", str(scopefile), "--session", session, "--repo", str(checkpoint.controllerctx.root)]
    before = json.loads(checkpoint.path.read_bytes())
    ownerargs = ["--minor", "v4.15", "--member", "v4.15.9", "--session", session,
        "--repo", str(checkpoint.controllerctx.root)]
    assert ck.main(["record", "render", "--action", "correct-read", *ownerargs,
        "--path", cm.T027_EVIDENCE, "--host-transcript", str(log.path)]) == 0
    capsys.readouterr()
    key = cm._round_key(checkpoint.controllerctx, "v4.15")
    pending = json.loads(ab.pending_path(checkpoint.runs, key).read_bytes())
    log.user(pending["paste_lines"][0])
    assert ck.main(["record", "correct-read", *ownerargs, "--path", cm.T027_EVIDENCE]) == 0
    corrected = load()
    correction = copy.deepcopy(corrected["members"][0][cm._READ_CORRECTION_FIELD])
    assert correction and cm._read_correction_entry_valid(ck, corrected, corrected["members"][0], correction[0], verify_capture=True)
    assert corrected["members"][0]["implementation"] == before["members"][0]["implementation"]
    pathsfile = home / "old-paths.json"
    pathsfile.write_text(json.dumps({"write_paths": [ADOPTED]}), encoding="utf-8")
    for action, flags, reason in (("permit-member-paths", ["--paths", str(pathsfile)], "member-paths-bound-permissions"),
        ("withdraw-implementation", [], "withdraw-bound-entries")):
        assert ck.main(["record", "render", "--action", action, *ownerargs, *flags]) != 0
        output = capsys.readouterr()
        assert reason in output.err + output.out
        assert ck.main(["record", action, *ownerargs, *flags]) != 0
        output = capsys.readouterr()
        assert reason in output.out + output.err
    before = json.loads(checkpoint.path.read_bytes())
    log.now += 1
    assert ck.main(["record", "render", "--action", cm.CHECKPOINT_ACTION,
        *common, "--host-transcript", str(log.path)]) == 0
    capsys.readouterr()
    key = cm._round_key(checkpoint.controllerctx, "v4.15")
    pending = json.loads(ab.pending_path(checkpoint.runs, key).read_bytes())
    log.user(pending["paste_lines"][0])
    assert ck.main(["record", cm.CHECKPOINT_ACTION, *common]) == 0
    assert capsys.readouterr().out == "RECONCILED v4.15.9 checkpoint (current adoption; original claims unchanged)\n"
    after = load()
    assert after["members"] == before["members"]
    assert after["members"][0][cm._READ_CORRECTION_FIELD] == correction
    assert after["approvals"]["spend_caps"] == before["approvals"]["spend_caps"]
    entry, = after[cm.CHECKPOINT_FIELD]
    assert entry["accepted"]["authorization_context"]["origin"] == "codex-host-transcript"
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, after)
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, ck.project(after, "v4.15.9"))
    rows, future = cm._checkpoint_effective(ck, checkpoint.ctx, after, after["members"][0], checkpoint.base, "HEAD")
    assert set(rows) == {ADOPTED} and future == [cm.CHECKPOINT_FUTURE]
    assert ck.main(["record", cm.CHECKPOINT_ACTION, *common]) != 0
    assert hashlib.sha256(checkpoint.path.read_bytes()).hexdigest() == after.loaded_sha256
    log.now += 1
    assert ck.main(["record", "render", "--action", cm.T027_ACTION, *ownerargs,
        "--gap", "DF-67", "--host-transcript", str(log.path)]) == 0
    pending = json.loads(ab.pending_path(checkpoint.runs, key).read_bytes())
    log.user(pending["paste_lines"][0])
    assert ck.main(["record", cm.T027_ACTION, *ownerargs, "--gap", "DF-67"]) == 0
    combined = load()
    assert combined[cm.CHECKPOINT_FIELD] == after[cm.CHECKPOINT_FIELD]
    assert combined["members"] == after["members"]
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, combined)
    assert cm.t027_entry_valid(ck, checkpoint.ctx, combined)
    payload = ck._hmac_payload(combined)
    assert payload["member_checkpoint_domain"] == "nexus-v4159-member-checkpoint-v1"
    assert payload["v415_t027_domain"] == "nexus-v4159-t027-unmeasured-v1"
    assert payload["transcript_approval_domain"] == "nexus-native-transcript-approval-v1"
    assert ck._sign(combined, checkpoint.key) == combined["approvals_hmac"]
    assert cm._sign(ck, combined, checkpoint.key) == combined["approvals_hmac"]
    assert cm._verified(ck, checkpoint.controllerctx, "v4.15", combined)
    state = native_load_minor(ck, checkpoint.controllerctx, "v4.15", session)
    assert state.record is not None and state.forced is None
    monkeypatch.setattr(cm, "_record_for_action", load)
    next_session = "01a14365-125e-7213-b5e9-9a0702a651c9"
    next_log = Transcript(home, checkpoint.controllerctx.root, log.now + 1, session=next_session)
    next_log.now += 1
    monkeypatch.setattr(ab, "_clock", lambda: next_log.now)
    resume = ["--minor", "v4.15", "--session", next_session, "--repo", str(checkpoint.controllerctx.root)]
    assert ck.main(["record", "render", "--action", "resume", *resume, "--host-transcript", str(next_log.path)]) == 0
    pending = json.loads(ab.pending_path(checkpoint.runs, key).read_bytes())
    next_log.user(pending["paste_lines"][0])
    assert ck.main(["record", "resume", *resume]) == 0
    resumed = load()
    assert resumed["session_id"] == next_session and len(resumed["continuations"]) == 1
    assert resumed[cm.CHECKPOINT_FIELD] == after[cm.CHECKPOINT_FIELD]
    assert resumed["members"][0][cm._READ_CORRECTION_FIELD] == correction
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, resumed)
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, ck.project(resumed, "v4.15.9"))
    target = checkpoint.root.parent / "next-controller"
    git(checkpoint.controllerctx.root, "worktree", "add", "-q", "-b", "private-next-controller", str(target), checkpoint.base)
    monkeypatch.setattr(cm, "load_minor", lambda *_args, **_kwargs: SimpleNamespace(record=load(), forced=None))
    monkeypatch.setattr(cm, "_ls_remote_tip", lambda *_args: checkpoint.base)
    assert ck.main(["record", "controller-handoff", "--minor", "v4.15", "--session", next_session,
        "--repo", str(checkpoint.controllerctx.root), "--to", str(target), "--head", checkpoint.base,
        "--expected-generation", "0", "--apply"]) == 0
    transferred = load()
    assert transferred["implementation_controller"]["repo_root"] == str(target)
    assert transferred["implementation_controller"]["generation"] == 1
    assert transferred[cm.CHECKPOINT_FIELD] == after[cm.CHECKPOINT_FIELD]
    assert transferred[cm.T027_FIELD] == combined[cm.T027_FIELD]
    assert transferred["members"][0][cm._READ_CORRECTION_FIELD] == correction
    targetctx = ck.RepoContext(target, ck.Budget(120))
    assert cm.checkpoint_entry_valid(ck, targetctx, transferred)
    assert cm.checkpoint_entry_valid(ck, targetctx, ck.project(transferred, "v4.15.9"))
    assert cm.t027_entry_valid(ck, targetctx, transferred)
    state = native_load_minor(ck, targetctx, "v4.15", next_session)
    assert state.record is not None and state.forced is None
    for module, field in ((ck, "CHECKPOINT_PROTOCOL"), (cm, "CHECKPOINT_PROTOCOL"),
        (ab, "CHECKPOINT_PROTOCOL"), (ck, "T027_DISPOSITION_PROTOCOL"), (cm, "T027_DISPOSITION_PROTOCOL")):
        with monkeypatch.context() as mismatch:
            mismatch.setattr(module, field, 0)
            with pytest.raises(ck.MinorConflict, match="incompatible"):
                ck._sign(transferred, checkpoint.key)
            with pytest.raises(ck.MinorConflict, match="incompatible"):
                cm._sign(ck, transferred, checkpoint.key)


def test_unrelated_progress_and_session_handoff_keep_receipt_valid(checkpoint, monkeypatch):
    accept(checkpoint, monkeypatch)
    checkpoint.record["session_id"] = "later-owner"
    checkpoint.record["implementation_controller"] = {"repo_root": str(checkpoint.controllerctx.root), "generation": 2}
    checkpoint.member["start_head"] = checkpoint.base
    checkpoint.member["approvals"]["classes"].append({"class": "push-merge"})
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, checkpoint.record)


def test_projected_snapshot_must_retain_authenticated_parent(checkpoint, monkeypatch):
    accept(checkpoint, monkeypatch)
    projected = ck.project(checkpoint.record, "v4.15.9")
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, projected)
    assert not cm.checkpoint_entry_valid(ck, checkpoint.ctx, dict(projected))
    projected["checkpoint_member"] = copy.deepcopy(projected["checkpoint_member"])
    projected["checkpoint_member"]["implementation"]["write_paths"].append("catalog/")
    assert not cm.checkpoint_entry_valid(ck, checkpoint.ctx, projected)


def test_new_checkpoint_keeps_old_receipt_but_never_falls_back(checkpoint, monkeypatch):
    first = copy.deepcopy(accept(checkpoint, monkeypatch))
    checkpoint.path.write_text(json.dumps(checkpoint.record), encoding="utf-8")
    checkpoint.record = ck.MinorSnapshot(dict(checkpoint.record), checkpoint.path, checkpoint.path.read_bytes(), checkpoint.controllerctx)
    checkpoint.head = commit(checkpoint.root, ADOPTED, "fresh current checkpoint\n")
    # A new render sees the latest committed bytes and retains immutable history.
    second = accept(checkpoint, monkeypatch, key="second-checkpoint")
    assert checkpoint.record[cm.CHECKPOINT_FIELD][0] == first
    assert second["page"]["head"] == checkpoint.head
    assert cm.checkpoint_entry_valid(ck, checkpoint.ctx, checkpoint.record)
    assert cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member,
        checkpoint.base, "HEAD")[0][ADOPTED][4] == git(checkpoint.root, "rev-parse", f"HEAD:{ADOPTED}")


@pytest.mark.parametrize("ordinary,exceptions,allowed", [(35, True, True), (36, False, False), (36, True, False)])
def test_manifest_count_limits(checkpoint, ordinary, exceptions, allowed):
    paths = [f"catalog/agents/private-{index}.md" for index in range(ordinary - 1)]
    if exceptions:
        paths.extend(sorted(cm.CHECKPOINT_EXCEPTIONS))
    for path in paths:
        target = checkpoint.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("private limit fixture\n", encoding="utf-8")
    git(checkpoint.root, "add", ".")
    git(checkpoint.root, "commit", "-q", "-m", "private bounded manifest")
    checkpoint.head = git(checkpoint.root, "rev-parse", "HEAD")
    if allowed:
        assert len(page(checkpoint)["checkpoint_rows"]) == 40
    else:
        with pytest.raises(ck.Malformed, match="outside-bounds"):
            page(checkpoint)


def test_real_worker_branch_drift_refuses(checkpoint):
    git(checkpoint.root, "checkout", "-q", "-b", "private-wrong-branch")
    with pytest.raises(ck.Malformed, match="branch-changed"):
        page(checkpoint)


@pytest.mark.parametrize("field,value", [("state", "OPEN"), ("headRefName", "other"),
    ("baseRefName", "main"), ("headRefOid", "0" * 40), ("mergeCommit", {"oid": "1" * 40})])
def test_historical_source_fields_must_be_authenticated(checkpoint, monkeypatch, field, value):
    accept(checkpoint, monkeypatch)
    pr = {"state": "MERGED", "headRefName": cm.T027_BRANCH, "baseRefName": "develop",
        "headRefOid": checkpoint.head, "mergeCommit": {"oid": checkpoint.head}}
    calls = []
    def hosted(*args):
        calls.append(args)
        return pr
    monkeypatch.setattr(ck, "_gh_json", hosted)
    assert cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member,
        checkpoint.base, checkpoint.head)[0]
    assert calls[0][1] == "bendourthe/Nexus-Hub"
    pr[field] = value
    with pytest.raises(cm.ObservationUnavailable, match="source-unverified"):
        cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member,
            checkpoint.base, checkpoint.head)


def test_effective_use_rechecks_active_conflicts(checkpoint, monkeypatch):
    accept(checkpoint, monkeypatch)
    monkeypatch.setattr(cm, "_coordinator_conflict", lambda *_args: True)
    with pytest.raises(cm.MinorMalformed, match="active-conflict"):
        cm._checkpoint_effective(ck, checkpoint.ctx, checkpoint.record, checkpoint.member, checkpoint.base, "HEAD")


def test_real_private_squash_uses_verified_pr_head_not_merge_ancestry(checkpoint, monkeypatch):
    accept(checkpoint, monkeypatch)
    controller = checkpoint.controllerctx.root
    git(controller, "merge", "--squash", cm.T027_BRANCH)
    git(controller, "commit", "-q", "-m", "private squash integration")
    merged = git(controller, "rev-parse", "HEAD")
    assert cm._ancestor(checkpoint.controllerctx, checkpoint.head, merged) == "unmet"
    pr = {"state": "MERGED", "headRefName": cm.T027_BRANCH, "baseRefName": "develop",
        "headRefOid": checkpoint.head, "mergeCommit": {"oid": merged}}
    monkeypatch.setattr(ck, "_gh_json", lambda *_args: pr)
    rows, future = cm._checkpoint_effective(ck, checkpoint.controllerctx, checkpoint.record,
        checkpoint.member, checkpoint.base, merged)
    assert set(rows) == {ADOPTED} and future == [cm.CHECKPOINT_FUTURE]
    pr["headRefOid"] = checkpoint.base
    with pytest.raises(cm.ObservationUnavailable, match="source-unverified"):
        cm._checkpoint_effective(ck, checkpoint.controllerctx, checkpoint.record,
            checkpoint.member, checkpoint.base, merged)


def test_native_archive_refreeze_preserves_checkpoint_after_worker_retirement(checkpoint, monkeypatch):
    """Exercise the actual archive mover, link proof, commit, and signed refreeze.

    Release eligibility is outside this fixture; no release eligibility gate is
    substituted with a passing mock or claimed as covered here.
    """
    import minor_close as close
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    checkpoint.record["approvals"]["classes"] = [{"class": "archive-minor"}]
    checkpoint.record["approvals_hmac"] = ck._sign(checkpoint.record, checkpoint.key)
    checkpoint.path.write_text(json.dumps(checkpoint.record), encoding="utf-8")
    checkpoint.record = ck.MinorSnapshot(dict(checkpoint.record), checkpoint.path, checkpoint.path.read_bytes(), checkpoint.controllerctx)
    accept(checkpoint, monkeypatch)
    before = copy.deepcopy(checkpoint.record[cm.CHECKPOINT_FIELD])
    controller = checkpoint.controllerctx
    git(controller.root, "merge", "--squash", cm.T027_BRANCH)
    git(controller.root, "commit", "-q", "-m", "private integration before archive")
    merge = git(controller.root, "rev-parse", "HEAD")
    pr = {"state": "MERGED", "headRefName": cm.T027_BRANCH, "baseRefName": "develop",
        "headRefOid": checkpoint.head, "mergeCommit": {"oid": merge}}
    monkeypatch.setattr(ck, "_gh_json", lambda *_args: pr)
    git(controller.root, "worktree", "remove", str(checkpoint.root))
    assert not checkpoint.root.exists()
    canonical = checkpoint.runs / (ck.record_key(controller.root, "bendourthe/nexus-hub", "minor:v4.15") + ".json")
    canonical.write_text(json.dumps(checkpoint.record), encoding="utf-8")
    record = ck.MinorSnapshot(dict(checkpoint.record), canonical, canonical.read_bytes(), controller)
    monkeypatch.setattr(cm, "record_file", lambda *_args: canonical)
    files = git(controller.root, "ls-files", "-z").split("\0")
    files = [path for path in files if path]
    tree, dest = "docs/releases/v4/v4.15", "docs/archives/v4/v4.15"
    checker = Path(ck.__file__).resolve().parents[1] / "catalog/skills/code-cleanup/docs-layout-refactor/scripts/link-baseline.py"
    assert checker.is_file()
    close._apply_archive(controller, "v4.15", tree, dest, files, checker)
    with ck.minor_transaction(record):
        close.refreeze(controller, record, canonical, "v4.15")
    member = record["members"][0]
    assert member["plan_path"].startswith(dest + "/")
    assert record[cm.CHECKPOINT_FIELD] == before
    assert cm.checkpoint_entry_valid(ck, controller, record)
    assert cm.checkpoint_entry_valid(ck, controller, ck.project(record, "v4.15.9"))
    rows, future = cm._checkpoint_effective(ck, controller, record, member, checkpoint.base, merge)
    assert set(rows) == {ADOPTED} and future == [cm.CHECKPOINT_FUTURE]
    forged = copy.deepcopy(dict(record))
    forged["members"][0]["archived"]["close_commit"] = checkpoint.base
    forged["approvals_hmac"] = ck._sign(forged, checkpoint.key)
    assert not cm.checkpoint_entry_valid(ck, controller, forged)
    saved = canonical.read_bytes()
    with pytest.raises(ck.MinorConflict, match="checkpoint-history-changed"):
        with ck.minor_transaction(record):
            ck._write_record(canonical, forged)
    assert canonical.read_bytes() == saved
    archived_plan = controller.root / member["plan_path"]
    archived_plan.write_text(archived_plan.read_text(encoding="utf-8") + "\nUnapproved changed acceptance scope.\n", encoding="utf-8")
    git(controller.root, "add", "--", member["plan_path"])
    git(controller.root, "commit", "-q", "-m", "private unapproved prose drift")
    forged = copy.deepcopy(dict(record))
    forged["members"][0]["plan_sha256"] = ck.plan_hash_text(archived_plan.read_text(encoding="utf-8"))
    forged["members"][0]["archived"]["close_commit"] = git(controller.root, "rev-parse", "HEAD")
    forged["approvals_hmac"] = ck._sign(forged, checkpoint.key)
    assert not cm.checkpoint_entry_valid(ck, controller, forged)
    with pytest.raises(ck.MinorConflict, match="checkpoint-history-changed"):
        with ck.minor_transaction(record):
            ck._write_record(canonical, forged)
    assert canonical.read_bytes() == saved
