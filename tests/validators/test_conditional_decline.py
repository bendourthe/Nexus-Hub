"""Conditional decline uses captured, bounded native authority, never a skip flag."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_plan_completion as ck
import approval_binding
import completion_minor as cm


@pytest.fixture
def decline(tmp_path, monkeypatch, request):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "empty-config"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    work, remote = tmp_path / "work", tmp_path / "remote.git"
    work.mkdir()

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(work), *args], text=True
        ).strip()

    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    git("init", "-q", "-b", "develop")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    plan = "docs/releases/v0/v0.2/plans/v0.2.0-demo.md"
    evidence = "docs/releases/v0/v0.2/development/result.json"
    proof_reference = " Cite `result.json`." if getattr(request, "param", False) else ""
    text = (
        "# Plan\n\n**Version**: v0.2.0\n**Slug**: demo\n\n## Phase 1\n\n"
        "- [x] T001 Admit candidate src/catalog.json\n\n**Prompt**:\n"
        "> Run only if at least one slot passed every gate. Update `src/catalog.json`."
        f"{proof_reference}\n\n"
        "- [x] T002 Record decision docs/decision.md\n\n**Prompt**:\n"
        "> On a full decline, stop after the merge: no tag, per the owner's release decision.\n"
    )
    for rel, value in ((plan, text), ("src/catalog.json", "{}\n")):
        path = work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "baseline")
    start = git("rev-parse", "HEAD")
    git("checkout", "-qb", "feat/demo")
    proof = work / evidence
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text('{"gate":"HOLD","admittedSlots":[]}\n', encoding="utf-8")
    (work / "docs/decision.md").write_text(
        "Declined: runtime gate HOLD.\n", encoding="utf-8"
    )
    git("add", ".")
    git("commit", "-qm", "record decline")
    head = git("rev-parse", "HEAD")
    git("checkout", "-q", "develop")
    git("merge", "--no-ff", "-qm", "merge", "feat/demo")
    merge = git("rev-parse", "HEAD")
    git("remote", "add", "origin", str(remote))
    git("push", "-q", "origin", "develop")
    ctx = ck.Context(str(work / plan), ck.Budget(20))
    view = {
        "schema": 2,
        "start_head": start,
        "plan_sha256": ctx.plan_hash(),
        "approvals": {
            "repo": "acme/demo",
            "source_branch": "feat/demo",
            "target_branch": "develop",
            "tag": "v0.2.0",
        },
    }
    request = {
        "outcome": "declined",
        "plan_sha256": ctx.plan_hash(),
        "condition": "Runtime gate HOLD; zero slots admitted.",
        "tasks": ["T001"],
        "head": head,
        "merge": merge,
        "evidence": [
            {"path": evidence, "sha256": hashlib.sha256(proof.read_bytes()).hexdigest()}
        ],
    }
    pr = {
        "state": "MERGED",
        "headRefName": "feat/demo",
        "baseRefName": "develop",
        "headRefOid": head,
        "mergeCommit": {"oid": merge},
    }
    monkeypatch.setattr(ck, "_approved_remote_status", lambda *a: "met")
    monkeypatch.setattr(ck, "_pr_checks", lambda *a: "met")
    monkeypatch.setattr(
        ck,
        "_gh_json",
        lambda ctx, repo, *a: ck.GH_NOT_FOUND if a[0] == "release" else pr,
    )
    return SimpleNamespace(
        ctx=ctx, view=view, request=request, git=git, work=work, pr=pr
    )


def test_decline_binds_protected_inputs_and_committed_proof(decline):
    result = ck.conditional_request(decline.ctx, decline.view, decline.request)
    assert result["protected_paths"] == ["src/catalog.json"]
    assert result["task_sha256"]["T001"]
    assert result["request"] == decline.request


@pytest.mark.parametrize(
    "change",
    [
        "unconditional",
        "unchecked",
        "duplicate",
        "no-evidence",
        "wrong-digest",
        "traversal",
        "wrong-plan",
        "wrong-head",
        "wrong-merge",
    ],
)
def test_invalid_disposition_is_refused(decline, change):
    req = json.loads(json.dumps(decline.request))
    if change == "unconditional":
        req["tasks"] = ["T002"]
    elif change == "unchecked":
        decline.ctx.tasks = [("T001", False, "src/catalog.json")]
    elif change == "duplicate":
        req["tasks"] *= 2
    elif change == "no-evidence":
        req["evidence"] = []
    elif change == "wrong-digest":
        req["evidence"][0]["sha256"] = "0" * 64
    elif change == "traversal":
        req["evidence"][0]["path"] = "../outside.json"
    elif change == "wrong-plan":
        req["plan_sha256"] = "0" * 64
    elif change == "wrong-head":
        req["head"] = "0" * 40
    elif change == "wrong-merge":
        req["merge"] = "0" * 40
    with pytest.raises(ValueError):
        ck.conditional_request(decline.ctx, decline.view, req)


def test_decline_cannot_hide_changed_catalog(decline):
    (decline.work / "src/catalog.json").write_text(
        '{"admitted":true}\n', encoding="utf-8"
    )
    decline.git("add", ".")
    decline.git("commit", "-qm", "changed catalog")
    with pytest.raises(ValueError, match="protected"):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


@pytest.mark.parametrize("decline", [True], indirect=True)
def test_bound_release_proof_is_not_an_unchanged_application_input(decline):
    assert "Cite `result.json`" in decline.ctx.text
    result = ck.conditional_request(decline.ctx, decline.view, decline.request)
    assert result["protected_paths"] == ["src/catalog.json"]


@pytest.mark.parametrize("state", ["unmet", "cannot-verify"])
def test_decline_keeps_remote_and_green_check_requirements(decline, monkeypatch, state):
    monkeypatch.setattr(ck, "_pr_checks", lambda *a: state)
    with pytest.raises(ValueError):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


def test_decline_rejects_a_release_tag(decline):
    decline.git("tag", "v0.2.0")
    with pytest.raises(ValueError, match="tag"):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


def test_local_restore_cannot_hide_admission_in_approved_merge(decline):
    path = decline.work / "src/catalog.json"
    path.write_text('{"admitted":true}\n', encoding="utf-8")
    decline.git("add", ".")
    decline.git("commit", "-qm", "admit candidate")
    merge = decline.git("rev-parse", "HEAD")
    decline.git("push", "-q", "origin", "develop")
    decline.request.update(head=merge, merge=merge)
    decline.pr.update(headRefOid=merge, mergeCommit={"oid": merge})
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="protected"):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


def test_index_removal_cannot_hide_a_protected_basename(decline):
    path = decline.work / "src/binding.json"
    path.write_text('{"admitted":true}\n', encoding="utf-8")
    decline.git("add", ".")
    decline.git("commit", "-qm", "add referenced binding")
    merge = decline.git("rev-parse", "HEAD")
    decline.git("push", "-q", "origin", "develop")
    decline.request.update(head=merge, merge=merge)
    decline.pr.update(headRefOid=merge, mergeCommit={"oid": merge})
    decline.ctx.text = decline.ctx.text.replace(
        "Update `src/catalog.json`.", "Update `src/catalog.json` and `binding.json`."
    )
    assert "`binding.json`" in decline.ctx.text
    decline.request["plan_sha256"] = decline.ctx.plan_hash()
    decline.view["plan_sha256"] = decline.ctx.plan_hash()
    decline.git("rm", "--cached", "-q", "src/binding.json")
    with pytest.raises(ValueError, match="protected"):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


def test_later_approved_member_can_update_the_same_protected_catalog(decline, monkeypatch):
    binding = ck.conditional_request(decline.ctx, decline.view, decline.request)
    decline.view['approvals']['conditional_outcome'] = ck.conditional_capture(
        {'page': {'conditional_outcome': binding}, 'pasted': 'Approve fixture'})
    prior_merge = decline.request['merge']
    path = decline.work / 'src/catalog.json'
    path.write_text('{"laterApprovedModel":true}\n', encoding='utf-8')
    decline.git('add', '.')
    decline.git('commit', '-qm', 'later approved member')
    later = decline.git('rev-parse', 'HEAD')
    decline.git('push', '-q', 'origin', 'develop')
    decline.view['successors'] = [{'version': 'v0.2.1', 'source_branch': 'feat/later',
                                  'target_branch': 'develop', 'start_head': prior_merge}]
    original = ck._gh_json
    def gh(ctx, repo, *args):
        if args[:3] == ('pr', 'view', 'feat/later'):
            return {'state': 'MERGED', 'headRefName': 'feat/later', 'baseRefName': 'develop',
                    'headRefOid': later, 'mergeCommit': {'oid': later}}
        return original(ctx, repo, *args)
    monkeypatch.setattr(ck, '_gh_json', gh)
    successors = decline.view.pop('successors')
    assert ck.conditional_status(decline.ctx, decline.view)[0] == 'cannot-verify'
    decline.view['successors'] = successors
    successors[0]['target_branch'] = 'main'
    assert ck.conditional_status(decline.ctx, decline.view)[0] == 'cannot-verify'
    successors[0]['target_branch'] = 'develop'
    monkeypatch.setattr(ck, '_pr_checks', lambda ctx, repo, branch, *a: 'unmet' if branch == 'feat/later' else 'met')
    assert ck.conditional_status(decline.ctx, decline.view)[0] == 'cannot-verify'
    monkeypatch.setattr(ck, '_pr_checks', lambda *a: 'met')
    assert ck.conditional_status(decline.ctx, decline.view)[0] == 'met'
    path.write_text('{}\n', encoding='utf-8')
    assert ck.conditional_status(decline.ctx, decline.view)[0] == 'cannot-verify'


def test_no_disposition_preserves_ordinary_release_behavior(decline, monkeypatch):
    assert ck.conditional_status(decline.ctx, decline.view) == ("n/a", None)
    for name in (
        "_tag_status",
        "_changelog_status",
        "_release_status",
        "_main_contains",
    ):
        monkeypatch.setattr(ck, name, lambda *args: "unmet")
    results = dict(ck.evaluate(decline.ctx, decline.view)[0])
    for name in ("release.tag", "release.changelog", "release.github", "release.main"):
        assert results[name] == "unmet"
    assert "release.disposition" not in results


def test_captured_decline_cannot_authorize_a_release(decline, monkeypatch):
    monkeypatch.setattr(
        approval_binding, "full_access_authorization", lambda *args: True
    )
    decline.view["approvals"]["classes"] = [{"class": "release"}]
    decline.view["approvals"]["conditional_outcome"] = {"request": decline.request}
    with pytest.raises(ValueError, match="does not authorize a release"):
        approval_binding.authorization(decline.view, "release", {})


def test_release_appearing_after_capture_invalidates_decline(decline, monkeypatch):
    binding = ck.conditional_request(decline.ctx, decline.view, decline.request)
    decline.view["approvals"]["conditional_outcome"] = ck.conditional_capture(
        {"page": {"conditional_outcome": binding}, "pasted": "Approve fixture"}
    )
    original = ck._gh_json
    monkeypatch.setattr(
        ck,
        "_gh_json",
        lambda ctx, repo, *args: (
            {"tagName": "v0.2.0"}
            if args[0] == "release"
            else original(ctx, repo, *args)
        ),
    )
    assert ck.conditional_status(decline.ctx, decline.view)[0] == "cannot-verify"


def test_signed_disposition_is_rechecked_after_capture(decline):
    binding = ck.conditional_request(decline.ctx, decline.view, decline.request)
    receipt = ck.conditional_capture(
        {"page": {"conditional_outcome": binding}, "pasted": "Approve fixture"}
    )
    decline.view["approvals"]["conditional_outcome"] = receipt
    assert ck.conditional_status(decline.ctx, decline.view)[0] == "met"
    receipt["protected_paths"] = []
    assert ck.conditional_status(decline.ctx, decline.view)[0] == "cannot-verify"


def test_unsigned_blocker_answer_is_not_disposition_authority(decline):
    decline.view["blockers"] = [
        {"open": False, "answer_text": "Approve", "request": decline.request}
    ]
    assert ck.conditional_status(decline.ctx, decline.view) == ("n/a", None)


def test_evidence_requiring_native_archive_link_repair_is_refused(decline):
    path = "docs/decline-proof.md"
    target = decline.work / path
    target.write_text(
        "[plan](releases/v0/v0.2/plans/v0.2.0-demo.md)\n", encoding="utf-8"
    )
    decline.git("add", ".")
    decline.git("commit", "-qm", "record linked proof")
    merge = decline.git("rev-parse", "HEAD")
    decline.git("push", "-q", "origin", "develop")
    decline.request.update(
        head=merge,
        merge=merge,
        evidence=[
            {
                "path": path,
                "sha256": hashlib.sha256(
                    ck._conditional_blob(decline.ctx, merge, path)
                ).hexdigest(),
            }
        ],
    )
    decline.pr.update(headRefOid=merge, mergeCommit={"oid": merge})
    with pytest.raises(ValueError, match="archive repair"):
        ck.conditional_request(decline.ctx, decline.view, decline.request)


@pytest.mark.parametrize("technical_blocker", [False, True])
def test_native_capture_archive_and_recheck(tmp_path, monkeypatch, technical_blocker):
    from .test_completion_minor_record import Minor, SESSION, _git
    from .test_gap_migration_and_archive import LINK_CHECKER

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "empty-config"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    minor = Minor(tmp_path, monkeypatch)
    tree = "docs/releases/v0/v0.5"
    rel = tree + "/plans/v0.5.2-alpha.md"
    (minor.work / (tree + "/plans/v0.5.10-omega.md")).unlink()
    plan = (
        "# Plan\n\n**Version**: v0.5.2\n**Slug**: alpha\n**Status**: queued\n\n## Phase 1\n\n"
        "- [ ] T001 Admit candidate src/catalog.json\n\n**Prompt**:\n"
        "> Run only if at least one slot passed every gate. Update `src/catalog.json`.\n\n"
        "- [ ] T002 Record decision docs/decision.md\n\n**Prompt**:\n"
        "> On a full decline, stop after the merge: no tag, per the owner's release decision.\n"
    )

    def write(path, text):
        target = minor.work / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    write(rel, plan)
    write("src/catalog.json", "{}\n")
    minor.commit("freeze conditional plan")
    _git(minor.work, "checkout", "-q", "develop")
    _git(minor.work, "merge", "--ff-only", "-q", "main")
    minor.publish("main", "develop")
    created = minor.create()
    assert created.returncode == 0, created.stdout + created.stderr
    original = minor.record()
    member = original["members"][0]
    branch = member["source_branch"]
    _git(minor.work, "checkout", "-qb", branch)
    write(rel, plan.replace("- [ ]", "- [x]"))
    proof = tree + "/development/result.json"
    write(proof, '{"gate":"HOLD","admittedSlots":[]}\n')
    write("docs/decision.md", "Declined at runtime gate.\n")
    write("tests/test_decline.py", "def test_record():\n    assert 2 + 2 == 4\n")
    write(
        tree + "/known-gaps.md",
        "# Gaps\n\n**Status**: finalized\n**Open items**: 0\n\n## v0.5.2\n\n### Resolved\n",
    )
    sections = "".join("## " + s + "\n\nDone.\n\n" for s in ck.REQUIRED_SECTIONS)
    sections = sections.replace(
        "## Full-suite testing and stabilization\n\nDone.",
        "## Full-suite testing and stabilization\n\n`pytest -q`: 3 passed, including tests/test_decline.py.",
    )
    write(
        tree + "/development/v0.5.2-last-phase-evidence.md", "# Evidence\n\n" + sections
    )
    minor.commit("record failed admission gate")
    head = _git(minor.work, "rev-parse", "HEAD")
    _git(minor.work, "checkout", "-q", "develop")
    _git(minor.work, "merge", "--no-ff", "-qm", "merge trial", branch)
    merge = _git(minor.work, "rev-parse", "HEAD")
    minor.publish("develop")
    minor.state["pr_by_branch"] = {
        branch: {
            "state": "MERGED",
            "merge_commit": merge,
            "headRefName": branch,
            "baseRefName": "develop",
            "headRefOid": head,
            "checks": [{"name": "ci", "bucket": "pass"}],
        }
    }
    minor.save_state()
    ctx = ck.Context(str(minor.work / rel), ck.Budget(60))
    request = {
        "outcome": "declined",
        "plan_sha256": member["plan_sha256"],
        "condition": "Runtime gate HOLD; zero admitted slots.",
        "tasks": ["T001"],
        "head": head,
        "merge": merge,
        "evidence": [
            {
                "path": proof,
                "sha256": hashlib.sha256(
                    ck._conditional_blob(ctx, merge, proof)
                ).hexdigest(),
            }
        ],
    }
    request_file = tmp_path / "disposition.json"
    request_file.write_text(json.dumps(request), encoding="utf-8")
    extra = ["--conditional-outcome", str(request_file)] if technical_blocker else []
    decision = (
        ["--category", "platform-unavailable"]
        if technical_blocker
        else [
            "--category",
            "approval-not-covered",
            "--approval-class",
            "conditional-outcome",
            "--request",
            json.dumps(request),
        ]
    )
    blocked = minor.run(
        "record",
        "block",
        "--minor",
        "v0.5",
        "--member",
        "v0.5.2",
        "--session",
        SESSION,
        *decision,
        "--evidence",
        "frozen full decline",
    )
    assert blocked.returncode == ck.EXIT_BLOCKED, blocked.stdout + blocked.stderr
    if technical_blocker:
        request_file.write_text("null", encoding="utf-8")
        invalid = minor.render(
            SESSION,
            "--action",
            "answer",
            "--blocker",
            "0",
            "--member",
            "v0.5.2",
            *extra,
        )
        assert invalid.returncode == ck.EXIT_MALFORMED
        assert "JSON object" in invalid.stderr + invalid.stdout
        request_file.write_text(json.dumps(request), encoding="utf-8")
    shown = minor.render(
        SESSION,
        "--action",
        "answer",
        "--blocker",
        "0",
        "--member",
        "v0.5.2",
        "--page",
        *extra,
    )
    assert shown.returncode == 0, shown.stdout + shown.stderr
    assert "The named admission tasks stay unrun" in shown.stdout
    assert proof in shown.stdout and "src/catalog.json" in shown.stdout
    attempt = minor.run(
        "record",
        "answer",
        "--minor",
        "v0.5",
        "--member",
        "v0.5.2",
        "--session",
        SESSION,
        "--blocker",
        "0",
        *extra,
    )
    assert attempt.returncode != 0
    assert "conditional_outcome" not in minor.record()["members"][0]["approvals"]
    minor.paste(
        SESSION, "--action", "answer", "--blocker", "0", "--member", "v0.5.2", *extra
    )
    accepted = minor.run(
        "record",
        "answer",
        "--minor",
        "v0.5",
        "--member",
        "v0.5.2",
        "--session",
        SESSION,
        "--blocker",
        "0",
        *extra,
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    captured = minor.record()
    receipt = captured["members"][0]["approvals"]["conditional_outcome"]
    assert receipt["capture"]["origin"] == "native-answer"
    assert captured["nonce"] == original["nonce"]
    assert captured["approvals_hmac"] == ck._sign(captured, ck._secret(False))
    assert ck.conditional_status(ctx, ck.project(captured, "v0.5.2"))[0] == "met"
    replay = minor.run(
        "record",
        "answer",
        "--minor",
        "v0.5",
        "--member",
        "v0.5.2",
        "--session",
        SESSION,
        "--blocker",
        "0",
    )
    assert replay.returncode != 0
    _git(minor.work, "checkout", "-qb", "chore/close-v0.5")
    result = subprocess.run(
        [
            sys.executable,
            str(Path(ck.__file__).with_name("minor_close.py")),
            "archive",
            "--minor",
            "v0.5",
            "--repo",
            str(minor.work),
            "--session",
            SESSION,
            "--link-checker",
            str(LINK_CHECKER),
            "--apply",
        ],
        env=minor.env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    archived = minor.record()
    moved = archived["members"][0]["plan_path"]
    assert moved.startswith("docs/archives/")
    assert (
        archived["members"][0]["approvals"]["conditional_outcome"]["origin"]
        == receipt["origin"]
    )
    post = ck.Context(str(minor.work / moved), ck.Budget(60))
    assert ck.conditional_status(post, ck.project(archived, "v0.5.2"))[0] == "met"
    close_head = _git(minor.work, "rev-parse", "HEAD")
    _git(minor.work, "checkout", "-q", "develop")
    _git(minor.work, "merge", "--ff-only", "-q", "chore/close-v0.5")
    minor.publish("develop")
    minor.state["pr_by_branch"]["chore/close-v0.5"] = {
        "state": "MERGED",
        "merge_commit": close_head,
        "headRefName": "chore/close-v0.5",
        "baseRefName": "develop",
        "headRefOid": close_head,
        "checks": [{"name": "ci", "bucket": "pass"}],
    }
    minor.save_state()
    ledgers, unreadable = cm.load_ledgers(minor.work)
    assert not unreadable
    assert (
        cm.close_pr_status(ck, minor.rctx(), archived, "v0.5", "acme/demo", ledgers, [])
        == "met"
    )
    minor.state["pr_by_branch"]["chore/close-v0.5"]["merge_commit"] = original[
        "start_head"
    ]
    minor.save_state()
    assert (
        cm.close_pr_status(ck, minor.rctx(), archived, "v0.5", "acme/demo", ledgers, [])
        == "unmet"
    )
