"""Isolated signed authorities qualify only the published v4.14 carry reconciliation."""

from __future__ import annotations

import json

import pytest

from .test_gap_migration_and_archive import Close, _git, ck, cm
from .test_planned_followon_gaps import (
    _isolated_git_config,  # noqa: F401
    _no_transport_overrides,  # noqa: F401
)

SOURCE = "docs/releases/v4/v4.14/known-gaps.md"
DESTINATION = "docs/releases/v4/v4.15/known-gaps.md"
PLAN = "docs/archives/v4/v4.14/plans/v4.14.8-plain-english-replies-and-source-labels.md"
SOURCE_TEXT = "## v4.14.8\n\n### Open Items\n\n#### BG-30: Reviewed carry - MIGRATED to v4.15.0\n\n- **Reason**: Existing reviewed work\n\n"
DESTINATION_TEXT = (
    "## v4.15.0\n\n### Open Items\n\n#### BG-3: Reviewed carry\n\n- **Reason**: Existing reviewed work\n\n"
    "- **Migrated from**: v4.14.8#BG-30 on 2026-11-04 (reason: user-deferred)\n"
    "- **Migration evidence**: Published disposition\n\n"
)


@pytest.fixture
def reconciliation(tmp_path, monkeypatch):
    """Synthetic Git history and signed records, exclusively in the temporary run store."""
    repo = Close(tmp_path, monkeypatch)
    repo.write(SOURCE, SOURCE_TEXT)
    repo.write(DESTINATION, DESTINATION_TEXT)
    members = []
    for patch in range(7):
        rel = f"docs/releases/v4/v4.14/plans/v4.14.{patch}-fixture.md"
        text = f"# Fixture\n\n**Version**: v4.14.{patch}\n\n- [x] T001 Preserve fixture src/file.txt\n"
        repo.write(rel, text)
        members.append({"version": f"v4.14.{patch}", "plan_path": rel, "plan_sha256": ck.plan_hash_text(text)})
    repo.write(PLAN, "# Fixture\n\n**Version**: v4.14.8\n\n- [x] T001 Preserve fixture src/file.txt\n")
    repo.commit("synthetic published carry")
    _git(repo.work, "tag", "v4.14.8")
    monkeypatch.setattr(cm, "shipped", lambda *args: "met")
    _git(repo.work, "remote", "set-url", "--push", "origin", "https://github.com/bendourthe/Nexus-Hub.git")
    rctx = repo.rctx()
    minor_path = rctx.scoped_record_path("minor:v4.14")
    last_path = rctx.scoped_record_path("plan:" + PLAN)
    binding = dict(cm.V414_CARRY_RECONCILIATION)
    binding.update(minor_key=minor_path.stem, last_key=last_path.stem, start=repo.head(),
                   release=repo.head(), plan_hash=ck.plan_hash_text(repo.read(PLAN)))
    monkeypatch.setattr(cm, "V414_CARRY_RECONCILIATION", binding)
    minor = {
        "schema": 2, "scope": "minor", "minor": "v4.14", "repo": "bendourthe/Nexus-Hub",
        "repo_root": str(repo.work.resolve()), "worktree": str(repo.work.resolve()),
        "nonce": binding["minor_nonce"], "start_head": repo.head(), "members": members,
        "approvals": {"page_sha256": binding["minor_page"], "classes": []},
    }
    last = {
        "schema": 1, "repo": "bendourthe/Nexus-Hub", "repo_root": str(repo.work.resolve()),
        "worktree": str(repo.work.resolve()), "nonce": binding["last_nonce"],
        "plan": PLAN, "plan_sha256": binding["plan_hash"],
        "approvals": {"page_sha256": binding["last_page"], "repo": "bendourthe/Nexus-Hub",
                      "source_branch": binding["branch"], "target_branch": "develop",
                      "classes": [{"class": "carry-gaps"}]},
        "blockers": [], "pause": None,
    }
    secret = ck._secret(create=True)
    minor["approvals_hmac"] = ck._sign(minor, secret)
    repo.runs.mkdir(exist_ok=True)
    minor_path.write_text(json.dumps(minor), encoding="utf-8")

    def save_last(sign=True):
        if sign:
            last["approvals_hmac"] = ck._sign(last, secret)
        last_path.write_text(json.dumps(last), encoding="utf-8")

    save_last()
    return repo, rctx, minor, last, save_last


def verify(case):
    repo, rctx, minor, _last, _save = case
    ledgers, unreadable = cm.load_ledgers(repo.work)
    assert not unreadable
    source = next(ledger for ledger in ledgers if ledger.minor == (4, 14))
    return cm.verify_migration(rctx, minor, "v4.14", ledgers, source, source.items[0])


def test_existing_signed_published_carry_is_recognized_without_record_changes(reconciliation):
    repo = reconciliation[0]
    before = {p.name: p.read_bytes() for p in repo.runs.glob("*.json")}
    assert verify(reconciliation) == ("met", "approved-migration")
    assert before == {p.name: p.read_bytes() for p in repo.runs.glob("*.json")}


@pytest.mark.parametrize("change", [
    "nonce", "page", "branch", "repo", "plan", "plan-hash", "signature", "approval", "paused", "blocked", "root",
])
def test_changed_last_authority_is_refused(reconciliation, change):
    _repo, _rctx, _minor, last, save = reconciliation
    if change == "nonce":
        last["nonce"] = "replacement"
    elif change in {"page", "branch", "repo"}:
        last["approvals"][{"page": "page_sha256", "branch": "source_branch", "repo": "repo"}[change]] = "changed"
    elif change == "plan":
        last["plan"] = "docs/archives/v4/v4.14/plans/replacement.md"
    elif change == "plan-hash":
        last["plan_sha256"] = "0" * 64
    elif change == "signature":
        last["approvals_hmac"] = "invalid"
    elif change == "approval":
        last["approvals"]["classes"] = []
    elif change == "paused":
        last["pause"] = {"reason": "fixture"}
    elif change == "blocked":
        last["blockers"] = [{"open": True, "category": "fixture"}]
    else:
        last["repo_root"] += "-other"
        last["worktree"] = last["repo_root"]
    save(sign=change != "signature")
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("change", ["minor-nonce", "minor-page", "minor-start", "minor-signature", "member", "publication", "ownership", "missing-tag", "wrong-tag"])
def test_original_authority_and_publication_remain_required(reconciliation, monkeypatch, change):
    repo, _rctx, minor, _last, _save = reconciliation
    if change == "publication":
        monkeypatch.setattr(cm, "shipped", lambda *args: "unmet")
    elif change == "missing-tag":
        _git(repo.work, "tag", "-d", "v4.14.8")
    elif change == "wrong-tag":
        repo.write("changed.txt", "another commit")
        repo.commit("different tag target")
        _git(repo.work, "tag", "-f", "v4.14.8")
    elif change == "ownership":
        original = cm._common_dir
        monkeypatch.setattr(cm, "_common_dir", lambda ctx, root: "" if root == repo.work else original(ctx, root))
    elif change == "member":
        repo.write(minor["members"][0]["plan_path"], "changed frozen member")
    elif change == "minor-signature":
        minor["approvals_hmac"] = "invalid"
    else:
        if change == "minor-page":
            minor["approvals"]["page_sha256"] = "0" * 64
        else:
            minor[{"minor-nonce": "nonce", "minor-start": "start_head"}[change]] = "changed"
        minor["approvals_hmac"] = ck._sign(minor, ck._secret(create=False))
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("change", ["joint-body", "title", "wrong-section", "sensitive", "closed-copy", "duplicate-copy", "unknown-id", "missing-blob"])
def test_mutable_matching_copies_cannot_replace_the_published_oracle(reconciliation, monkeypatch, change):
    repo, _rctx, _minor, _last, _save = reconciliation
    if change == "missing-blob":
        monkeypatch.setattr(cm, "_ledger_blob", lambda *args, **kwargs: ("cannot-verify", ""))
        with pytest.raises(cm.ObservationUnavailable, match="migration.publication"):
            verify(reconciliation)
        return
    elif change in {"joint-body", "title", "unknown-id"}:
        old, new = {"joint-body": ("Existing reviewed work", "Joint mutation"), "title": ("Reviewed carry", "Altered title"),
                    "unknown-id": ("BG-30", "BG-99")}[change]
        for rel in (SOURCE, DESTINATION):
            repo.write(rel, repo.read(rel).replace(old, new))
    elif change == "wrong-section":
        repo.write(SOURCE, repo.read(SOURCE).replace("v4.14.8", "v4.14.6"))
    elif change == "sensitive":
        for rel in (SOURCE, DESTINATION):
            repo.write(rel, repo.read(rel).replace("### Open Items", "### Security"))
    elif change == "closed-copy":
        repo.write(DESTINATION, repo.read(DESTINATION).replace("BG-3: Reviewed carry", "BG-3: Reviewed carry - RESOLVED"))
    else:
        repo.write(DESTINATION, repo.read(DESTINATION) + repo.read(DESTINATION))
    assert verify(reconciliation)[0] != "met"


def test_archived_layout_and_crlf_have_the_same_narrow_meaning(reconciliation):
    repo = reconciliation[0]
    archived = SOURCE.replace("releases", "archives")
    repo.write(archived, repo.read(SOURCE).replace("\n", "\r\n"))
    (repo.work / SOURCE).unlink()
    assert verify(reconciliation) == ("met", "approved-migration")


def test_two_valid_authorities_in_different_git_repositories_are_refused(reconciliation, monkeypatch):
    repo, rctx, minor, last, _save = reconciliation
    other = repo.tmp / "independent"
    other.mkdir()
    _git(other, "init", "-q")
    _git(other, "remote", "add", "origin", "https://github.com/bendourthe/Nexus-Hub.git")
    plan = other / PLAN
    plan.parent.mkdir(parents=True)
    plan.write_text(repo.read(PLAN), encoding="utf-8")
    last["repo_root"] = last["worktree"] = str(other.resolve())
    last["approvals_hmac"] = ck._sign(last, ck._secret(create=False))
    binding = dict(cm.V414_CARRY_RECONCILIATION)
    binding["last_key"] = ck.record_key(other.resolve(), last["repo"].lower(), "plan:" + PLAN)
    monkeypatch.setattr(cm, "V414_CARRY_RECONCILIATION", binding)
    (repo.runs / (binding["last_key"] + ".json")).write_text(json.dumps(last), encoding="utf-8")
    ctx = ck.Context(str(plan), rctx.budget)
    state = ck._load_schema1(ctx, last, None, ck.RecordState())
    assert state.record is last and state.forced is None
    assert cm._verified(ck, rctx, "v4.14", minor)
    source_common, other_common = cm._common_dir(rctx, repo.work), cm._common_dir(rctx, other)
    assert source_common and other_common and source_common != other_common
    assert verify(reconciliation)[0] != "met"


def test_git_replacement_cannot_substitute_the_published_oracle(reconciliation):
    repo, rctx, _minor, _last, _save = reconciliation
    published = cm.V414_CARRY_RECONCILIATION["release"]
    for rel in (SOURCE, DESTINATION):
        repo.write(rel, repo.read(rel).replace("Existing reviewed work", "Joint replacement mutation"))
    repo.commit("synthetic replacement oracle")
    _git(repo.work, "replace", published, repo.head())
    status, substituted = cm._ledger_blob(rctx, published, SOURCE)
    assert status == "met" and "Joint replacement mutation" in substituted
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("approvals", [[{"class": "carry-gaps"}], "malformed", 7, None])
def test_malformed_unsigned_auxiliary_approval_is_refused(reconciliation, approvals):
    _repo, _rctx, _minor, last, save = reconciliation
    last["approvals"] = approvals
    save(sign=False)
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("classes", [7, None, {"class": "carry-gaps"}, "carry-gaps"])
def test_malformed_unsigned_auxiliary_classes_are_refused(reconciliation, classes):
    _repo, _rctx, _minor, last, save = reconciliation
    last["approvals"]["classes"] = classes
    save(sign=False)
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("codepoint", [0, 0xD800, 0xDFFF])
def test_malformed_unsigned_auxiliary_root_is_refused(reconciliation, codepoint):
    _repo, _rctx, _minor, last, save = reconciliation
    last["repo_root"] += chr(codepoint)
    last["worktree"] = last["repo_root"]
    save(sign=False)
    assert ck._sign(last, ck._secret(create=False)) == last["approvals_hmac"]
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("signature", [None, 7, ["bad"], "\u00e9" * 64])
def test_malformed_auxiliary_signature_is_refused(reconciliation, signature):
    _repo, _rctx, _minor, last, save = reconciliation
    last["approvals_hmac"] = signature
    save(sign=False)
    assert verify(reconciliation)[0] != "met"


@pytest.mark.parametrize("blockers", [None, 7, {}, [None], [{"open": True}]])
def test_malformed_mutable_auxiliary_blockers_are_refused(reconciliation, blockers):
    _repo, _rctx, _minor, last, save = reconciliation
    last["blockers"] = blockers
    save(sign=False)
    assert ck._sign(last, ck._secret(create=False)) == last["approvals_hmac"]
    assert verify(reconciliation)[0] != "met"
