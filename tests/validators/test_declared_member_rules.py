"""Per-member rules are declared data keyed by plan path and frozen hash, never version branches.

Renaming a member (a new version in its plan and run record) must leave every verdict
unchanged once its declaration row follows it, and a missing or altered declaration must
fail closed. The fixtures declare their own rows; nothing here reads the live plan files.
"""
from __future__ import annotations

import json
import re

import pytest

from .member_declarations import fixture_rules
from .test_check_plan_completion import (
    V415_HASHES,
    _git,
    _v415_qualification_case,
    _v415_task_repo,
)
from .test_completion_minor_record import REPO_ROOT, SESSION, Minor, ck, cm

OLD = "docs/releases/v4/v4.17/development/phase-1-evidence.md"
CORRECTED = "docs/releases/v4/v4.15/development/v4.15.2-phase1-evidence.md"
PLANS = "docs/releases/v4/v4.15/plans/"


def _declare(monkeypatch, *rows: dict) -> None:
    monkeypatch.setattr(cm, "MEMBER_DECLARATIONS", {(r["plan_path"], r["plan_sha256"]): r for r in rows})


def _plan_text(version: str) -> str:
    return (f"# Plan - fixture\n\n**Version**: {version}\n**Slug**: renamed\n**Status**: queued\n\n## Phase 1: Build\n\n"
            f"- [ ] T001 [US1] Fixture task {OLD}\n")


def _authority_case(minor: Minor, monkeypatch, version: str, *, declare: bool = True):
    """A verified one-member v4.15 record whose plan carries `version`, with its own declaration row."""
    rel = f"{PLANS}{version}-renamed.md"
    text = _plan_text(version)
    (minor.work / rel).parent.mkdir(parents=True, exist_ok=True)
    (minor.work / rel).write_text(text, encoding="utf-8")
    evidence = minor.work / CORRECTED
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("# Baseline evidence, no in-run work\n", encoding="utf-8")
    _git(minor.work, "remote", "set-url", "--push", "origin", "https://github.com/bendourthe/Nexus-Hub.git")
    minor.commit("fixture plan " + version)
    ctx = minor.rctx()
    plan = cm.scan_plans(ctx.root, 4, 15)[0]
    digest = ck.plan_hash_text(text)
    member = {"version": version, "plan_path": rel, "plan_sha256": digest,
              "source_branch": f"feat/{version}-renamed", "target_branch": "develop",
              "release_version": version, "tag": version, "approvals": {"classes": []}}
    record = {"schema": ck.SCHEMA_MINOR, "scope": "minor", "minor": "v4.15", "repo": "bendourthe/Nexus-Hub",
              "repo_root": str(ctx.root), "worktree": str(ctx.root), "session_id": SESSION, "nonce": "declared-rules",
              "members": [member], "start_head": _git(minor.work, "rev-parse", "HEAD"),
              "approvals": {"classes": [{"class": "archive-minor"}], "target_branch": "develop"}}
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=True) or b"")
    if declare:
        _declare(monkeypatch, fixture_rules("v4.15.2", plan_path=rel, plan_sha256=digest))
    return minor, record, member, plan, rel


@pytest.fixture
def declared_minor(tmp_path, monkeypatch, minor_git_seed):
    return Minor(tmp_path, monkeypatch, minor_git_seed)


def _verdict(minor: Minor, record: dict, member: dict, plan, *, work: bool) -> tuple[bool, str]:
    """(authority issued, task T001 verdict) for a member whose evidence was moved to its corrected name."""
    if work:
        (minor.work / CORRECTED).write_text("# Genuine in-run corrected task work\n", encoding="utf-8")
        (minor.work / plan.rel).write_text(plan.text.replace("- [ ] T001", "- [x] T001"), encoding="utf-8")
        minor.commit("actual corrected task implementation")
        plan = cm.scan_plans(minor.work, 4, 15)[0]
    authority = cm.v415_task_authority(ck, minor.rctx(), record, member, plan)
    status = dict(cm.evaluate_member(ck, minor.rctx(), record, member, plan, []).lines)["task.T001"]
    return authority is not None, status


@pytest.mark.parametrize("work", [False, True], ids=["no-work", "genuine-work"])
def test_renamed_member_keeps_every_verdict(tmp_path_factory, monkeypatch, minor_git_seed, work):
    verdicts = {}
    for version in ("v4.15.2", "v4.15.9"):
        monkeypatch.undo()
        minor = Minor(tmp_path_factory.mktemp(version.replace(".", "")), monkeypatch, minor_git_seed)
        minor, record, member, plan, _rel = _authority_case(minor, monkeypatch, version)
        verdicts[version] = _verdict(minor, record, member, plan, work=work)
    assert verdicts["v4.15.2"] == verdicts["v4.15.9"] == (True, "met" if work else "unmet")


def test_declaration_for_another_plan_identity_is_refused(declared_minor, monkeypatch):
    minor, record, member, plan, rel = _authority_case(declared_minor, monkeypatch, "v4.15.2")
    assert cm.v415_task_authority(ck, minor.rctx(), record, member, plan) is not None
    # The same rules under a renumbered path, or under a different frozen hash, do not apply.
    _declare(monkeypatch, fixture_rules("v4.15.2", plan_path=rel.replace("v4.15.2-", "v4.15.3-"),
                                        plan_sha256=member["plan_sha256"]))
    assert cm.v415_task_authority(ck, minor.rctx(), record, member, plan) is None
    _declare(monkeypatch, fixture_rules("v4.15.2", plan_path=rel, plan_sha256="0" * 64))
    assert cm.v415_task_authority(ck, minor.rctx(), record, member, plan) is None


def test_missing_declaration_fails_closed_without_remapping_evidence(declared_minor, monkeypatch):
    minor, record, member, plan, _rel = _authority_case(declared_minor, monkeypatch, "v4.15.2", declare=False)
    _declare(monkeypatch)
    assert _verdict(minor, record, member, plan, work=True) == (False, "unmet")


def test_a_declaration_that_is_not_an_original_member_grants_no_authority(declared_minor, monkeypatch):
    minor, record, member, plan, rel = _authority_case(declared_minor, monkeypatch, "v4.15.2")
    row = {k: v for k, v in fixture_rules("v4.15.2", plan_path=rel, plan_sha256=member["plan_sha256"]).items()
           if k != "original"}
    _declare(monkeypatch, row)
    assert cm.v415_task_authority(ck, minor.rctx(), record, member, plan) is None


@pytest.mark.parametrize("damage", ["none", "wrong-hash", "wrong-member", "wrong-file"])
def test_mint_requires_a_declaration_bound_to_hash_and_member(tmp_path, damage):
    ck_, ctx, _start, authority = _v415_task_repo(tmp_path, "v4.15.2")
    args = {"root": ctx.root, "repo": "bendourthe/Nexus-Hub", "minor": "v4.15", "member": ctx.version,
            "original_sha256": V415_HASHES["v4.15.2"], "plan_rel": ctx.rel, "plan_sha256": ctx.plan_hash(),
            "rules": authority.rules}
    assert ck_._v415_task_authority(**args) is not None
    if damage == "none":
        args["rules"] = None
    elif damage == "wrong-hash":
        args["rules"] = {**authority.rules, "plan_sha256": "0" * 64}
    elif damage == "wrong-member":
        args["member"] = "v4.15.9"
    else:
        args["rules"] = {**authority.rules, "plan_path": PLANS + "other-plan.md"}
    assert ck_._v415_task_authority(**args) is None


def test_task_literals_come_from_the_declaration_not_the_member_version(tmp_path):
    ck_, ctx, start, authority = _v415_task_repo(tmp_path, "v4.15.2")
    target = ctx.root / CORRECTED
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("real implementation\n")
    _git(ctx.root, "add", ".")
    _git(ctx.root, "commit", "-qm", "work")
    assert ck_._task_status(ctx, True, OLD, start, task_id="T001", task_authority=authority) == "met"
    from dataclasses import replace
    altered = replace(authority, rules={**authority.rules, "task_targets": []})
    assert ck_._task_status(ctx, True, OLD, start, task_id="T001", task_authority=altered) == "unmet"
    unbound = replace(authority, rules={**authority.rules, "plan_sha256": "0" * 64})
    assert ck_._task_status(ctx, True, OLD, start, task_id="T001", task_authority=unbound) == "unmet"


def test_unchanged_task_case_refuses_a_missing_or_altered_declaration(tmp_path, monkeypatch):
    from dataclasses import replace
    ck_, ctx, _start, authority, _evidence, _comparison = _v415_qualification_case(tmp_path, monkeypatch)
    assert ck_._v415_case(ctx, "T114", authority) == ".github/workflows/ci.yml"
    for rules in (None, {**authority.rules, "plan_sha256": "0" * 64}, {**authority.rules, "no_change": {}}):
        with pytest.raises(ck_.Malformed, match="qualification-(authority|task)-unavailable"):
            ck_._v415_case(ctx, "T114", replace(authority, rules=rules))


def test_execution_eligibility_is_declared_per_plan_identity(monkeypatch):
    row = next(r for r in cm._DECLARED_MEMBER_ROWS if r.get("execution", {}).get("kind") == "hook-registration")
    path, sha = row["plan_path"], row["plan_sha256"]
    kind, role, paths = cm.execution_capability(path, sha)
    assert (kind, role) == ("hook-registration", "implementation") and paths == ("catalog/hooks/settings.json",)
    cm._execution_recipe_valid(path, sha, row["execution"]["recipe"])
    for args in ((path.replace("v4.15.5-", "v4.15.9-"), sha), (path, "0" * 64), (None, sha), (path, None)):
        with pytest.raises(cm.MinorMalformed, match="minor-execution-member-ineligible"):
            cm.execution_capability(*args)
    altered = json.loads(json.dumps(row["execution"]["recipe"]))
    altered["hooks"]["PreToolUse"] = [{"matcher": "Bash", "hooks": []}]
    with pytest.raises(cm.MinorMalformed, match="minor-execution-recipe-outside-eligibility"):
        cm._execution_recipe_valid(path, sha, altered)
    monkeypatch.setattr(cm, "MEMBER_DECLARATIONS", {})
    with pytest.raises(cm.MinorMalformed, match="minor-execution-member-ineligible"):
        cm.execution_capability(path, sha)


def test_production_declarations_are_keyed_by_their_own_identity():
    assert len(cm._DECLARED_MEMBER_ROWS) == len(cm.MEMBER_DECLARATIONS)
    for (path, sha), row in cm.MEMBER_DECLARATIONS.items():
        assert (path, sha) == (row["plan_path"], row["plan_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", sha) and path.rsplit("/", 1)[-1].endswith(".md")
        assert cm.declared_rules(path, sha) is row
        assert cm.declared_rules(path, "0" * 64) is None and cm.declared_rules(path + "x", sha) is None


MEMBER_VERSION = re.compile(r"v\d+\.\d+\.\d+")


def test_member_versions_live_only_in_the_declaration_data():
    scripts = REPO_ROOT / "scripts"
    for name in ("check_plan_completion.py", "approval_page.py"):
        text = (scripts / name).read_text(encoding="utf-8")
        assert not re.search(r"v4\.15\.\d+", text), name
    lines = (scripts / "completion_minor.py").read_text(encoding="utf-8").splitlines()
    regions = []
    for opener, closer in (("_DECLARED_MEMBER_ROWS = (", "MEMBER_DECLARATIONS = "), ("V414_CARRY_RECONCILIATION = {", "}")):
        first = next(i for i, line in enumerate(lines) if line.startswith(opener))
        regions.append(range(first, next(i for i in range(first, len(lines)) if lines[i].startswith(closer)) + 1))
    outside = [line for i, line in enumerate(lines)
               if not any(i in region for region in regions) and re.search(r"v4\.15\.\d+", line)]
    assert outside == [], outside
