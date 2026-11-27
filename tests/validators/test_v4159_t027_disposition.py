"""Exact unmeasured T027 disposition in private Git and capture fixtures only."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import approval_binding as ab
import approval_page as ap
import check_plan_completion as ck
import completion_minor as cm

from .test_codex_transcript_approval import Transcript
from .test_minor_execution_permission import (
    ExecutionMinor, SESSION, _isolated_git_config, _no_transport_overrides, _private_native_home,
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).strip()


@pytest.fixture
def trial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "develop")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    plan = (ROOT / cm.T027_PLAN).read_text(encoding="utf-8")
    ledger = "# Known Gaps\n\n## v4.15.9\n\n### Open Items\n\n#### DF-67: " + cm.T027_TITLE + "\n\n" + cm.T027_GAP_BODY
    for rel, text in ((cm.T027_PLAN, plan), (cm.T027_EVIDENCE, cm.T027_EVIDENCE_TEXT), (cm.T027_LEDGER, ledger)):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "private fixture")
    ctx = ck.Context(str(root / cm.T027_PLAN), ck.Budget(120))
    runs = tmp_path / "private-runs"
    runs.mkdir()
    key = b"private-fixture-key"
    monkeypatch.setattr(ck, "_secret", lambda **_kwargs: key)
    monkeypatch.setattr(ck, "_runs_dir", lambda: runs)
    monkeypatch.setattr(ck, "_approved_remote_status", lambda *_args: "met")
    monkeypatch.setattr(cm, "_controller_valid", lambda *_args: True)
    monkeypatch.setattr(cm, "_worker_context", lambda *_args, **_kwargs: (ctx, "met", False))
    member = {"version": "v4.15.9", "plan_path": cm.T027_PLAN, "plan_sha256": cm.T027_PLAN_HASH,
              "source_branch": "feat/v4.15.9-adoption-agent-cost-and-delegation", "target_branch": "develop",
              "approvals": {"classes": [], "cleanup": {"branches": [], "worktrees": []}}}
    raw = {"schema": 2, "scope": "minor", "minor": "v4.15", "repo": "bendourthe/Nexus-Hub",
           "nonce": "a" * 32, "created": "2026-11-22T00:00:00+00:00", "session_id": "fixture-owner",
           "repo_root": str(root), "worktree": str(root), "members": [member], "excluded": [],
           "start_head": git(root, "rev-parse", "HEAD"), "blockers": [], "pause": None,
           "approvals": {"push_remote_url": "https://github.com/bendourthe/Nexus-Hub.git", "classes": [],
                         "spend_caps": {"anthropic": getattr(request, "param", 0), "openai": 0, "google": 0}}}
    raw["approvals_hmac"] = ck._sign(raw, key)
    path = runs / "private-record.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    record = ck.MinorSnapshot(raw, path, path.read_bytes(), ctx)
    return SimpleNamespace(root=root, ctx=ctx, record=record, path=path, runs=runs, key=key)


def open_round(trial, monkeypatch: pytest.MonkeyPatch):
    page = cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")
    monkeypatch.setattr(ab, "_clock", lambda: 1000.0)
    pending = ab.render(trial.runs, "private-round", trial.key, action=cm.T027_ACTION, scope="v4.15",
                        page=page, session="fixture-owner", allow_short_reply=False)
    reply = pending["paste_lines"][0]
    capture_path = trial.runs / "prompts" / (hashlib.sha256(b"fixture-owner").hexdigest() + ".jsonl")
    capture_path.parent.mkdir()
    rows = [{"session": "fixture-owner", "prompt": ab.digest("ordinary fixture request"), "at": 999.0, "event_id": "initial"},
            {"session": "fixture-owner", "prompt": ab.digest(reply), "at": 1001.0, "event_id": "reply", "permission_mode": "bypassPermissions"}]
    capture_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return page


def accepted(trial, monkeypatch: pytest.MonkeyPatch):
    page = open_round(trial, monkeypatch)
    pending, _ = ab.consume(trial.runs, "private-round", trial.key, action=cm.T027_ACTION,
                            live_page=page, session="fixture-owner", required_session="fixture-owner")
    result = {"format": 1, "page": page, "accepted": {"at": ck._now(), "page_sha256": cm._amendment_digest(page),
              "round_nonce": pending["nonce"], "code": pending["code"], "rendered_at": pending["rendered_at"],
              "text": ab.pasted(pending), "allow_short_reply": False, "authorization_context": pending["capture"]}}
    trial.record[cm.T027_FIELD] = result
    trial.record["approvals_hmac"] = ck._sign(trial.record, trial.key)
    return result


def test_exact_committed_unmeasured_proof_accepts(trial):
    page = cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")
    assert page["outcome"] == "unmeasured"
    assert page["gap"]["target_version"] == "v4.16.0"
    assert page["paid_use_authorized"] is False


@pytest.mark.parametrize("token,version,gid", [("v4.16", "v4.15.9", "DF-67"), ("v4.15", "v4.15.8", "DF-67"),
                                                 ("v4.15", "v4.15.9", "WN-67"), ("v4.15", "v4.15.9", "DF-067")])
def test_scope_or_gap_cannot_be_expanded(trial, token, version, gid):
    with pytest.raises((ck.Malformed, cm.MinorMalformed)):
        cm.t027_page(ck, trial.ctx, trial.record, token, version, gid)


@pytest.mark.parametrize("rel", [cm.T027_PLAN, cm.T027_EVIDENCE, cm.T027_LEDGER])
def test_uncommitted_proof_refuses(trial, rel):
    path = trial.root / rel
    path.write_text(path.read_text(encoding="utf-8") + "\nChanged after commit.\n", encoding="utf-8")
    with pytest.raises(ck.Malformed, match="uncommitted"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


@pytest.mark.parametrize("replacement", ["measured", "no evidence", "Codex surrogate passed"])
def test_committed_measurement_or_surrogate_is_not_the_disposition(trial, replacement):
    (trial.root / cm.T027_EVIDENCE).write_text(replacement, encoding="utf-8")
    git(trial.root, "add", ".")
    git(trial.root, "commit", "-q", "-m", "changed proof")
    with pytest.raises(cm.MinorMalformed, match="unmeasured"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_checked_t027_refuses(trial):
    path = trial.root / cm.T027_PLAN
    path.write_text(path.read_text(encoding="utf-8").replace("- [ ] T027", "- [x] T027"), encoding="utf-8")
    git(trial.root, "add", ".")
    git(trial.root, "commit", "-q", "-m", "checked task")
    with pytest.raises(cm.MinorMalformed, match="unchecked"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


@pytest.mark.parametrize("trial", [10], indirect=True)
def test_original_signed_nonzero_cap_is_retained_without_spending(trial, monkeypatch):
    before = copy.deepcopy(dict(trial.record))
    assert ck._sign(trial.record, trial.key) == trial.record["approvals_hmac"]
    entry = accepted(trial, monkeypatch)
    assert entry["page"]["spend_caps"] == before["approvals"]["spend_caps"]
    assert entry["page"]["paid_use_authorized"] is False
    assert entry["page"]["claude_sessions"] == "prohibited"
    assert cm.t027_entry_valid(ck, trial.ctx, trial.record)
    assert trial.record["approvals"] == before["approvals"]
    assert [(tid, checked) for tid, checked, _ in trial.ctx.tasks if tid == "T027"] == [("T027", False)]


@pytest.mark.parametrize("trial", [-1, float("inf"), float("-inf"), float("nan"), True, "10", 1_000_000], indirect=True)
def test_invalid_original_caps_refuse(trial):
    with pytest.raises(ck.Malformed, match="spending cap"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_native_cli_retains_previously_granted_budget_without_executing_trial(tmp_path, monkeypatch):
    """Fresh CLI processes use real readers/writers; only fixture declarations differ."""
    fx = ExecutionMinor(tmp_path, monkeypatch)
    rel = fx.plan("v4.15.9", "adoption-agent-cost-and-delegation")
    plan = fx.work / rel
    # Retain a second member to verify the cap is shared, not multiplied.
    for other in plan.parent.glob("*.md"):
        if other != plan and not other.name.startswith("v4.15.0-"):
            other.unlink()
    text = plan.read_text(encoding="utf-8").replace(
        "- [ ] T001 Implement src/adoption-agent-cost-and-delegation.txt",
        "- [ ] T027 Keep effort trial unmeasured " + cm.T027_EVIDENCE)
    plan.write_text(text, encoding="utf-8")
    for path, content in ((cm.T027_EVIDENCE, cm.T027_EVIDENCE_TEXT),
                          (cm.T027_LEDGER, "# Known Gaps\n\n## v4.15.9\n\n### Open Items\n\n#### DF-67: " + cm.T027_TITLE + "\n\n" + cm.T027_GAP_BODY)):
        target = fx.work / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    fx.commit("private unmeasured task declaration")
    fx.integrate()
    plan_hash = ck.plan_hash_text(text)
    monkeypatch.setattr(cm, "T027_PLAN_HASH", plan_hash)
    # Reuse the declared checker wrapper pattern. No controller, authorization,
    # operational reader, capture consumer or writer is replaced.
    driver = tmp_path / "retained-budget-checker.py"
    driver.write_text(
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        f"sys.path.insert(0, {str(ROOT / 'tests/validators')!r})\n"
        "import completion_minor, member_declarations\n"
        "member_declarations.apply_to(completion_minor)\n"
        f"completion_minor.T027_PLAN_HASH = {plan_hash!r}\n"
        f"sys.argv[0] = {str(ROOT / 'scripts/check_plan_completion.py')!r}\n"
        "runpy.run_path(sys.argv[0], run_name='__main__')\n", encoding="utf-8")
    fx.env.pop("PYTHONPATH", None)
    fx.env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")

    def run(*args):
        return subprocess.run([sys.executable, "-B", str(driver), *args], cwd=fx.work, env=fx.env,
                              capture_output=True, text=True, timeout=90,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    fx.run = run
    approvals = fx.approvals({"class": "spend", "bound": {"anthropic": 10}})
    spec = json.loads(approvals.read_text(encoding="utf-8"))
    spec["spend_caps"] = {"anthropic": 10, "openai": 0, "google": 0}
    approvals.write_text(json.dumps(spec), encoding="utf-8")
    fx.paste(SESSION, "--approvals", str(approvals))
    created = run("record", "create", "--minor", "v4.15", "--session", SESSION, "--approvals", str(approvals))
    assert created.returncode == 0, created.stdout + created.stderr
    granted = copy.deepcopy(fx.record()["approvals"])
    assert granted["spend_caps"] == spec["spend_caps"]
    other_projection = ck.project(fx.record(), "v4.15.0")
    assert other_projection["approvals"]["spend_caps"] == granted["spend_caps"]
    worker = fx.worker("v4.15.9")
    claims = tmp_path / "retained-budget-claims.json"
    claims.write_text(text.split("```json\n", 1)[1].split("\n```", 1)[0], encoding="utf-8")
    admitted = run("record", "member-implement-start", "--minor", "v4.15", "--session", SESSION,
                   "--member", "v4.15.9", "--worktree", str(worker), "--head", git(worker, "rev-parse", "HEAD"),
                   "--claims", str(claims))
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    before = fx.record()
    task_bytes = (worker / rel).read_bytes()
    evidence_bytes = (worker / cm.T027_EVIDENCE).read_bytes()
    action = ("--member", "v4.15.9", "--gap", "DF-67")
    rendered = fx.render(SESSION, "--action", cm.T027_ACTION, *action)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    unchanged = fx.record_path().read_bytes()
    missing = run("record", cm.T027_ACTION, "--minor", "v4.15", "--session", SESSION, *action)
    assert missing.returncode != 0
    assert fx.record_path().read_bytes() == unchanged
    fx.capture(SESSION, rendered.stdout.splitlines()[0])
    accepted_result = run("record", cm.T027_ACTION, "--minor", "v4.15", "--session", SESSION, *action)
    assert accepted_result.returncode == 0, accepted_result.stdout + accepted_result.stderr
    after = fx.record()
    assert after["approvals"] == before["approvals"] == granted
    other_after = ck.project(after, "v4.15.0")
    assert {key: value for key, value in other_after.items() if key != cm.T027_FIELD} == other_projection
    assert not cm.t027_task_deferred(ck, ck.Context(str(fx.work / other_after["plan_path"]), ck.Budget(20)), other_after)
    assert {key: value for key, value in after.items() if key not in {cm.T027_FIELD, "approvals_hmac"}} == {
        key: value for key, value in before.items() if key != "approvals_hmac"}
    page = after[cm.T027_FIELD]["page"]
    assert page["spend_caps"] == granted["spend_caps"]
    assert page["paid_use_authorized"] is False and page["claude_sessions"] == "prohibited"
    assert page["outcome"] == "unmeasured"
    assert (worker / rel).read_bytes() == task_bytes
    assert (worker / cm.T027_EVIDENCE).read_bytes() == evidence_bytes
    assert "- [ ] T027" in text
    repeated = run("record", cm.T027_ACTION, "--minor", "v4.15", "--session", SESSION, *action)
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert fx.record() == after


def test_real_private_capture_and_historical_resume(trial, monkeypatch):
    entry = accepted(trial, monkeypatch)
    assert cm.t027_entry_valid(ck, trial.ctx, trial.record)
    trial.record["session_id"] = "later-owner"
    trial.record["implementation_controller"] = {"repo_root": str(trial.root), "generation": 2}
    assert cm.t027_entry_valid(ck, trial.ctx, trial.record)
    assert entry["page"]["owner_session"] == "fixture-owner"


def test_signature_participation_and_legacy_compatibility(trial, monkeypatch):
    original = ck._sign(trial.record, trial.key)
    base_payload = ck._hmac_payload(trial.record)
    accepted(trial, monkeypatch)
    assert ck._sign(trial.record, trial.key) != original
    restored = dict(trial.record)
    restored.pop(cm.T027_FIELD)
    assert ck._hmac_payload(restored) == base_payload
    assert ck._sign(restored, trial.key) == original


@pytest.mark.parametrize("field,value", [("member", "v4.15.8"), ("task", "T028"), ("outcome", "passed"),
                                       ("paid_use_authorized", True), ("plan_sha256", "b" * 64)])
def test_changed_disposition_refuses(trial, monkeypatch, field, value):
    entry = accepted(trial, monkeypatch)
    entry["page"][field] = value
    assert not cm.t027_entry_valid(ck, trial.ctx, trial.record)


def test_only_t027_becomes_deferred_and_its_checkbox_stays_unchecked(trial, monkeypatch):
    accepted(trial, monkeypatch)
    view = ck.project(trial.record, "v4.15.9")
    assert cm.t027_task_deferred(ck, trial.ctx, view)
    assert [(tid, checked) for tid, checked, _ in trial.ctx.tasks if tid == "T027"] == [("T027", False)]
    neighbor = copy.deepcopy(view)
    neighbor["version"] = "v4.15.8"
    assert not cm.t027_task_deferred(ck, trial.ctx, neighbor)
    assert trial.record["approvals"]["spend_caps"] == {"anthropic": 0, "openai": 0, "google": 0}


def test_exact_gap_is_authorized_but_not_migrated_by_the_decision(trial, monkeypatch):
    accepted(trial, monkeypatch)
    item = cm._t027_gap_item((trial.root / cm.T027_LEDGER).read_text(encoding="utf-8"), "DF-67")
    assert cm.migration_gate(trial.ctx, trial.record, (4, 15), "DF-67", item) == ("met", "t027-unmeasured")
    assert cm.migration_gate(trial.ctx, trial.record, (4, 15), "DF-68", None)[0] != "met"
    assert item.state == "open" and item.target is None


def test_writer_rejects_history_replacement_and_removal(trial, monkeypatch):
    accepted(trial, monkeypatch)
    old = copy.deepcopy(trial.record)
    changed = copy.deepcopy(old)
    changed.pop(cm.T027_FIELD)
    with pytest.raises(ck.MinorConflict, match="history"):
        cm.check_t027_write(ck, trial.ctx, old, changed)
    changed = copy.deepcopy(old)
    changed[cm.T027_FIELD]["page"]["task"] = "T028"
    with pytest.raises(ck.MinorConflict, match="history"):
        cm.check_t027_write(ck, trial.ctx, old, changed)


def test_missing_capture_receipt_never_supplies_authority(trial, monkeypatch):
    accepted(trial, monkeypatch)
    for receipt in (trial.runs / "consumed-prompts").glob("*.json"):
        receipt.unlink()
    assert not cm.t027_entry_valid(ck, trial.ctx, trial.record)


def test_plain_action_is_fixed_and_wrong_minor_refuses():
    assert "only v4.15.9 T027 as unmeasured" in ap.plain_line(cm.T027_ACTION, "v4.15", "ABCDEFGH")
    with pytest.raises(ap.PageError):
        ap.plain_line(cm.T027_ACTION, "v4.16", "ABCDEFGH")


def test_command_consumes_once_and_preserves_every_other_field(trial, monkeypatch, capsys):
    before = copy.deepcopy(dict(trial.record))
    open_round(trial, monkeypatch)
    monkeypatch.setattr(cm, "repo_context", lambda *_args: trial.ctx)
    monkeypatch.setattr(cm, "_round_key", lambda *_args: "private-round")
    monkeypatch.setattr(cm, "_record_for_add_class", lambda *_args: trial.record)
    args = SimpleNamespace(minor="v4.15", member="v4.15.9", session="fixture-owner", gap="DF-67", text=None)
    lease = {"path": trial.path.resolve(), "expected": trial.record.loaded_sha256, "ctx": trial.ctx}
    token = ck._MINOR_LEASE.set(lease)
    try:
        assert cm.cmd_defer_t027.__wrapped__(ck, args) == 0
        first = trial.path.read_bytes()
        assert cm.cmd_defer_t027.__wrapped__(ck, args) == 0
        assert trial.path.read_bytes() == first
    finally:
        ck._MINOR_LEASE.reset(token)
    after = json.loads(first)
    assert {k: v for k, v in after.items() if k not in {cm.T027_FIELD, "approvals_hmac"}} == {k: v for k, v in before.items() if k != "approvals_hmac"}
    assert "unmeasured" in capsys.readouterr().out


def test_transcript_t027_handler_preserves_both_signed_histories(trial, monkeypatch):
    before = copy.deepcopy(dict(trial.record))
    plan_bytes = (trial.root / cm.T027_PLAN).read_bytes()
    home = trial.root.parent / "transcript-home"
    home.mkdir()
    (trial.runs / ".secret").write_bytes(trial.key)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    log = Transcript(home, trial.root, time.time() - 10, session="fixture-owner")
    page = cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")
    pending = ab.render(trial.runs, "private-round", trial.key, action=cm.T027_ACTION,
        scope="v4.15", page=page, session="fixture-owner", allow_short_reply=False,
        host_transcript=log.path, allowed_cwds={str(trial.root.resolve())})
    log.now = time.time() - 1
    log.user(pending["paste_lines"][0])
    monkeypatch.setattr(cm, "repo_context", lambda *_args: trial.ctx)
    monkeypatch.setattr(cm, "_round_key", lambda *_args: "private-round")
    monkeypatch.setattr(cm, "_record_for_add_class", lambda *_args: trial.record)
    args = SimpleNamespace(minor="v4.15", member="v4.15.9", session="fixture-owner", gap="DF-67", text=None)
    lease = {"path": trial.path.resolve(), "expected": trial.record.loaded_sha256, "ctx": trial.ctx}
    token = ck._MINOR_LEASE.set(lease)
    try:
        assert cm.cmd_defer_t027.__wrapped__(ck, args) == 0
        first = trial.path.read_bytes()
        assert cm.cmd_defer_t027.__wrapped__(ck, args) == 0
        assert trial.path.read_bytes() == first
    finally:
        ck._MINOR_LEASE.reset(token)
    after = json.loads(first)
    entry = after[cm.T027_FIELD]
    capture = entry["accepted"]["authorization_context"]
    decisions = after["approvals"]["transcript_decisions"]
    assert len(decisions) == 1
    assert decisions[0]["capture"] == capture
    assert decisions[0]["action"] == cm.T027_ACTION
    assert decisions[0]["page"] == page
    assert capture["origin"] == "codex-host-transcript"
    assert ab.capture_context_valid(capture, session="fixture-owner")
    assert ab.consumed_capture_valid(trial.runs, capture, pending["rendered_at"])
    assert ab.transcript_decisions_valid(after)
    assert cm.t027_entry_valid(ck, trial.ctx, after)
    assert after["approvals_hmac"] == ck._sign(after, trial.key)
    payload = ck._hmac_payload(after)
    assert payload["transcript_approval_domain"] == "nexus-native-transcript-approval-v1"
    assert payload["v415_t027_domain"] == "nexus-v4159-t027-unmeasured-v1"
    restored = copy.deepcopy(after)
    restored.pop(cm.T027_FIELD)
    restored.pop("approvals_hmac")
    restored["approvals"].pop("transcript_decisions")
    assert restored == {key: value for key, value in before.items() if key != "approvals_hmac"}
    assert (trial.root / cm.T027_PLAN).read_bytes() == plan_bytes
    assert [(tid, checked) for tid, checked, _ in trial.ctx.tasks if tid == "T027"] == [("T027", False)]
    view = ck.project(after, "v4.15.9")
    assert cm.t027_task_deferred(ck, trial.ctx, view, task_id="T027")
    assert not cm.t027_task_deferred(ck, trial.ctx, view, task_id="T028")
    item = cm._t027_gap_item((trial.root / cm.T027_LEDGER).read_text(encoding="utf-8"), "DF-67")
    assert cm.migration_gate(trial.ctx, after, (4, 15), "DF-67", item) == ("met", "t027-unmeasured")
    assert cm.migration_gate(trial.ctx, after, (4, 15), "DF-68", None)[0] != "met"
    assert item.state == "open" and item.target is None
    removed = copy.deepcopy(after)
    removed["approvals"].pop("transcript_decisions")
    with pytest.raises(ValueError, match="append-only"):
        ab.check_continuation_write(trial.runs, after, removed)
    removed = copy.deepcopy(after)
    removed.pop(cm.T027_FIELD)
    with pytest.raises(ck.MinorConflict, match="history"):
        cm.check_t027_write(ck, trial.ctx, after, removed)


def test_current_gap_cannot_be_removed_to_hide_the_deferred_work(trial, monkeypatch):
    accepted(trial, monkeypatch)
    view = ck.project(trial.record, "v4.15.9")
    (trial.root / cm.T027_LEDGER).write_text("# Known Gaps\n", encoding="utf-8")
    assert not cm.t027_task_deferred(ck, trial.ctx, view)


def test_untracked_replacement_evidence_cannot_supply_proof(trial, monkeypatch):
    accepted(trial, monkeypatch)
    view = ck.project(trial.record, "v4.15.9")
    git(trial.root, "rm", cm.T027_EVIDENCE)
    git(trial.root, "commit", "-q", "-m", "remove tracked proof")
    (trial.root / cm.T027_EVIDENCE).parent.mkdir(parents=True, exist_ok=True)
    (trial.root / cm.T027_EVIDENCE).write_text(cm.T027_EVIDENCE_TEXT, encoding="utf-8")
    assert not cm.t027_task_deferred(ck, trial.ctx, view)


@pytest.mark.parametrize("gap_status,gap_count,open_gap,expected", [("deferred", 1, True, 1), ("met", 0, False, 1), ("deferred", 2, False, 3)])
def test_evaluation_keeps_deferral_visible_and_release_requirements(trial, monkeypatch, gap_status, gap_count, open_gap, expected):
    accepted(trial, monkeypatch)
    view = ck.project(trial.record, "v4.15.9")
    monkeypatch.setattr(ck, "_gaps_status", lambda *_args: (gap_status, gap_count))
    monkeypatch.setattr(cm, "t027_gap_open", lambda *_args: open_gap)
    monkeypatch.setattr(ck, "_task_status", lambda *_args, **_kwargs: "unmet")
    monkeypatch.setattr(ck, "_evidence_file", lambda *_args: None)
    for name in ("_tests_status", "_pr_merged", "_pr_checks", "_tag_status", "_changelog_status", "_version_sync", "_release_status", "_main_contains", "_branches_gone", "_worktrees_gone"):
        monkeypatch.setattr(ck, name, lambda *_args: "unmet")
    results, count = ck.evaluate(trial.ctx, view)
    statuses = dict(results)
    assert statuses["task.T027"] == "deferred" and statuses["task.T028"] == "unmet"
    assert statuses["release.tag"] == statuses["release.github"] == statuses["release.main"] == "unmet"
    assert count == expected


def test_stale_record_does_not_render_an_approval(trial):
    trial.path.write_bytes(trial.path.read_bytes() + b" ")
    with pytest.raises(ck.MinorConflict, match="record-changed"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_unverified_route_refuses(trial, monkeypatch):
    monkeypatch.setattr(ck, "_approved_remote_status", lambda *_args: "unmet")
    with pytest.raises(ck.Malformed, match="route-unverified"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_duplicate_gap_refuses(trial):
    path = trial.root / cm.T027_LEDGER
    path.write_text(path.read_text(encoding="utf-8") + "\n#### DF-67: " + cm.T027_TITLE + "\n\n" + cm.T027_GAP_BODY, encoding="utf-8")
    git(trial.root, "add", ".")
    git(trial.root, "commit", "-q", "-m", "duplicate gap")
    with pytest.raises(cm.MinorMalformed, match="gap-not-exact"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_changed_caps_invalidate_the_exact_disposition(trial, monkeypatch):
    accepted(trial, monkeypatch)
    trial.record["approvals"]["spend_caps"]["openai"] = 1
    assert not cm.t027_entry_valid(ck, trial.ctx, trial.record)


def test_archived_paths_keep_historical_proof_without_rewriting_it(trial, monkeypatch):
    entry = copy.deepcopy(accepted(trial, monkeypatch))
    target = trial.root / "docs/archives/v4"
    target.mkdir(parents=True)
    git(trial.root, "mv", "docs/releases/v4/v4.15", "docs/archives/v4/v4.15")
    git(trial.root, "commit", "-q", "-m", "archive private fixture")
    rel = cm.T027_PLAN.replace("docs/releases/", "docs/archives/")
    member = trial.record["members"][0]
    member["archived"] = {"from": cm.T027_PLAN, "original_sha256": cm.T027_PLAN_HASH,
                          "plan_path": rel, "plan_sha256": cm.T027_PLAN_HASH}
    member["plan_path"] = rel
    ctx = ck.Context(str(trial.root / rel), ck.Budget(120))
    view = ck.project(trial.record, "v4.15.9")
    assert cm.t027_task_deferred(ck, ctx, view)
    assert trial.record[cm.T027_FIELD] == entry


def test_exact_carry_destination_is_enforced(trial, monkeypatch):
    accepted(trial, monkeypatch)
    ledgers, unreadable = cm.load_ledgers(trial.root)
    assert not unreadable
    ledger = next(item for item in ledgers if item.rel == cm.T027_LEDGER)
    item = replace(ledger.items[0], state="migrated", target="v4.17.0")
    assert cm.verify_migration(trial.ctx, trial.record, "v4.15", ledgers, ledger, item) == ("unmet", "t027-destination-not-approved")


def test_mixed_t027_reader_bundles_refuse_without_changing_legacy_signatures(trial, monkeypatch):
    original = ck._sign(trial.record, trial.key)
    accepted(trial, monkeypatch)
    monkeypatch.setattr(cm, "T027_DISPOSITION_PROTOCOL", 0)
    with pytest.raises(ck.MinorConflict, match="consumer-incompatible"):
        ck._sign(trial.record, trial.key)
    restored = dict(trial.record)
    restored.pop(cm.T027_FIELD)
    assert ck._sign(restored, trial.key) == original


def test_staged_proof_drift_refuses_even_when_working_bytes_match_head(trial):
    path = trial.root / cm.T027_EVIDENCE
    path.write_text("staged contradiction", encoding="utf-8")
    git(trial.root, "add", cm.T027_EVIDENCE)
    path.write_text(cm.T027_EVIDENCE_TEXT, encoding="utf-8")
    with pytest.raises(ck.Malformed, match="uncommitted"):
        cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")


def test_changed_migrated_source_body_does_not_get_permission(trial, monkeypatch):
    accepted(trial, monkeypatch)
    item = cm._t027_gap_item((trial.root / cm.T027_LEDGER).read_text(encoding="utf-8"), "DF-67")
    altered = replace(item, state="migrated", target="v4.16.0", body="altered obligation")
    assert not cm.t027_gap_grant(ck, trial.ctx, trial.record, "v4.15#DF-67", altered)


def test_native_page_discloses_the_exact_unmeasured_effect(trial):
    page = cm.t027_page(ck, trial.ctx, trial.record, "v4.15", "v4.15.9", "DF-67")
    pending = ab.render(trial.runs, "page-only", trial.key, action=cm.T027_ACTION, scope="v4.15", page=page, session="fixture-owner")
    data = ap.render_data(pending, scope="v4.15", blocker=None, display=None)
    rendered = ap.render_page(data)
    assert "checkbox remains unchecked" in rendered
    assert "No spending or cap increase" in rendered
    assert "v4.16.0" in rendered and "v4.15#DF-67" in rendered


def test_archive_consumer_must_name_the_exact_deferred_task(trial, monkeypatch):
    accepted(trial, monkeypatch)
    view = ck.project(trial.record, "v4.15.9")
    assert cm.t027_task_deferred(ck, trial.ctx, view, task_id="T027")
    assert not cm.t027_task_deferred(ck, trial.ctx, view, task_id="T028")


def test_changed_frozen_plan_cannot_use_its_old_disposition(trial, monkeypatch):
    accepted(trial, monkeypatch)
    path = trial.root / cm.T027_PLAN
    path.write_text(path.read_text(encoding="utf-8") + "\nChanged acceptance requirements.\n", encoding="utf-8")
    ctx = ck.Context(str(path), ck.Budget(120))
    assert not cm.t027_task_deferred(ck, ctx, ck.project(trial.record, "v4.15.9"))
