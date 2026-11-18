"""The claims pre-check compares a draft with every admitted member, amended ones included."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "catalog/skills/workflow/implement-phase/scripts/claims_precheck.py"


@pytest.fixture(scope="module")
def cp():
    spec = importlib.util.spec_from_file_location("claims_precheck_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def member(version: str, reads=(), writes=(), coordinator=()) -> dict:
    return {"version": version, "implementation": {"base_head": "abc", "read_paths": list(reads), "write_paths": list(writes)},
            "coordinator_paths": list(coordinator)}


@pytest.fixture
def record() -> dict:
    """Top-level members plus an amended member that only exists under amendment pages."""
    return {
        "minor": "v1.0",
        "members": [member("v1.0.1", reads=["docs/guides/"], writes=["src/a.py", "Scripts/Tool.py"]),
                    member("v1.0.2", writes=["src/b/"], coordinator=["docs/extra.md"])],
        "minor_amendments": [{"page": {"members": [member("v1.0.3", reads=["src/read_only.py"], writes=["src/amended.py"])]},
                              "accepted": {}}],
        "minor_amendment_members": {"v1.0.3": {"descriptor": True, "version": "v1.0.3"}},
    }


def draft(reads=(), writes=(), deps=()) -> dict:
    return {"depends_on": list(deps), "read_paths": list(reads), "write_paths": list(writes)}


def kinds(report) -> set[tuple[str, str]]:
    return {(c["member"], c["kind"]) for c in report["conflicts"]}


def test_finds_members_at_any_depth_including_amended(cp, record):
    assert sorted(cp.find_members(record)) == ["v1.0.1", "v1.0.2", "v1.0.3"]


def test_conflict_with_amended_member_not_in_top_level_list(cp, record):
    report = cp.run(record, draft(writes=["src/amended.py"]), None)
    assert kinds(report) == {("v1.0.3", "draft-write/write")} and not report["ok"]
    report = cp.run(record, draft(writes=["src/read_only.py"]), None)
    assert kinds(report) == {("v1.0.3", "draft-write/read")}


def test_every_checker_rule_direction(cp, record):
    assert kinds(cp.run(record, draft(writes=["docs/guides/new.md"]), None)) == {("v1.0.1", "draft-write/read")}
    assert kinds(cp.run(record, draft(writes=["x.py"], reads=["src/a.py"]), None)) == {("v1.0.1", "draft-read/write")}
    assert kinds(cp.run(record, draft(writes=["docs/extra.md"]), None)) == {("v1.0.2", "draft-write/coordinator")}
    assert kinds(cp.run(record, draft(writes=["src/b/inner.py"]), None)) == {("v1.0.2", "draft-write/write")}
    assert kinds(cp.run(record, draft(writes=["src/other.py"], reads=["src/read_only.py"]), None)) == set()


def test_case_insensitive_and_directory_prefix_like_the_checker(cp, record):
    assert kinds(cp.run(record, draft(writes=["scripts/tool.py"]), None)) == {("v1.0.1", "draft-write/write")}
    assert kinds(cp.run(record, draft(writes=["src/"]), None)) >= {("v1.0.1", "draft-write/write"), ("v1.0.3", "draft-write/write")}


def test_each_conflicting_pair_is_printed_and_exit_is_one(cp, record, tmp_path, capsys):
    rec, drf = tmp_path / "record.json", tmp_path / "draft.json"
    rec.write_text(json.dumps(record), encoding="utf-8")
    drf.write_text(json.dumps(draft(writes=["src/a.py", "src/amended.py", "src/ok.py"])), encoding="utf-8")
    assert cp.main(["--record", str(rec), "--claims", str(drf)]) == 1
    out = capsys.readouterr().out
    assert "CONFLICT draft-write/write: src/a.py <-> v1.0.1 src/a.py" in out
    assert "CONFLICT draft-write/write: src/amended.py <-> v1.0.3 src/amended.py" in out
    assert "src/ok.py" not in out.split("REFUSED")[0]
    assert "REFUSED" in out


def test_member_flag_excludes_the_drafts_own_version(cp, record):
    own = draft(writes=["src/a.py"])
    assert not cp.run(record, own, None)["ok"]
    report = cp.run(record, own, "v1.0.1")
    assert report["ok"] and "v1.0.1" not in report["members_compared"]


def test_clean_draft_passes_and_record_is_untouched(cp, record, tmp_path, capsys):
    rec, drf = tmp_path / "record.json", tmp_path / "draft.json"
    rec.write_text(json.dumps(record), encoding="utf-8")
    drf.write_text(json.dumps(draft(writes=["src/new.py"], reads=["src/shared_ok.py"])), encoding="utf-8")
    before = hashlib.sha256(rec.read_bytes()).hexdigest()
    assert cp.main(["--record", str(rec), "--claims", str(drf), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert hashlib.sha256(rec.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("bad, code", [
    ({"depends_on": [], "read_paths": [], "write_paths": ["a.py"], "extra": 1}, "invalid-implementation-claims"),
    (draft(writes=["a.py", "A.PY"]), "duplicate-implementation-claim"),
    (draft(writes=[]), "empty-implementation-write-scope"),
    (draft(writes=["src/*.py"]), "non-literal-path"),
    (draft(writes=["../outside.py"]), "non-literal-path"),
    (draft(writes=["CHANGELOG.md"]), "coordinator-owned-path"),
    (draft(writes=["docs/releases/v1/known-gaps.md"]), "coordinator-owned-path"),
    (draft(writes=["docs/decisions/"]), "shared-folder-write"),
])
def test_draft_hygiene_errors_mirror_checker_refusals(cp, record, bad, code):
    report = cp.run(record, bad, None)
    assert not report["ok"] and code in {f["code"] for f in report["findings"] if f["level"] == "error"}


def test_exact_file_in_a_decisions_folder_is_fine_but_a_leaf_directory_only_warns(cp, record):
    ok = cp.run(record, draft(writes=["docs/decisions/implemented/policy/2026-01-01-x.md"]), None)
    assert ok["ok"] and not ok["findings"]
    leaf = cp.run(record, draft(writes=["src/leaf/"]), None)
    assert leaf["ok"] and {f["code"] for f in leaf["findings"]} == {"directory-write"}


def test_ci_follow_up_warnings_and_their_satisfaction(cp, record):
    findings = cp.run(record, draft(writes=["tests/skills/test_new.py", "templates/ai-instructions/base-x.md",
                                            "scripts/installer.sh"]), None)["findings"]
    text = " ".join(f["detail"] for f in findings if f["code"] == "ci-follow-up")
    assert "scripts/ci/profiles.py" in text and "legacy fingerprints" in text and "distribution handbook" in text
    claimed = draft(writes=["tests/skills/test_new.py", "scripts/ci/profiles.py"])
    assert not [f for f in cp.run(record, claimed, None)["findings"] if f["code"] == "ci-follow-up"]


def test_unreadable_input_is_a_usage_error(cp, tmp_path):
    drf = tmp_path / "draft.json"
    drf.write_text("{}", encoding="utf-8")
    assert cp.main(["--record", str(tmp_path / "nope.json"), "--claims", str(drf)]) == 2
    assert cp.main(["--record", str(drf), "--claims", str(drf), "--member", "4.15"]) == 2


def test_overlap_and_coordinator_rules_match_native_checker(cp):
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import completion_minor as native
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    paths = ["docs/", "docs/a.md", "DOCS/A.md", "docs", "docs/decisions/", "docs/decisions/x.md", "src/a.py", "src/"]
    for left in paths:
        for right in paths:
            assert cp.overlap(left, right) == native._overlap(left, right), (left, right)
    for name in ["CHANGELOG.md", "docs/known-gaps.md", "VERSION", "docs/releases/v4/v4.15/known-gaps.md"]:
        assert native._coordinator_name(name) and cp.coordinator_owned(name), name
    assert not native._coordinator_name("src/a.py") and not cp.coordinator_owned("src/a.py")


def _train_record() -> dict:
    def m(version, branch, reads=(), writes=(), coordinator=()):
        return {**member(version, reads, writes, coordinator), "source_branch": branch}
    shared = ["CHANGELOG.md", "docs/releases/v1/v1.0/known-gaps.md", "docs/todos.md"]
    return {"minor": "v1.0", "repo": "o/r", "members": [
        m("v1.0.0", "feat/a", writes=["src/a.py"], coordinator=shared),
        m("v1.0.2", "feat/c", writes=["src/c.py"], coordinator=shared),
        m("v1.0.3", "feat/d", writes=["src/d.py"]),
        m("v1.0.5", "feat/f", reads=["docs/releases/v1/v1.0/known-gaps.md"], writes=["src/f.py"])]}


def test_merged_members_are_skipped_like_the_native_checker(cp):
    rec = _train_record()

    def lookup(record, claim, base):
        return claim["source_branch"] in {"feat/a", "feat/c"}

    ok = draft(writes=["src/new.py"], reads=["docs/todos.md"])
    report = cp.run(rec, ok, "v1.0.3", lookup=lookup)
    assert report["merged_skipped"] == ["v1.0.0", "v1.0.2"] and report["conflicts"] == []
    assert report["members_compared"] == ["v1.0.5"]
    # offline: no lookup, so merged members stay active (stricter)
    strict = cp.run(rec, ok, "v1.0.3", check_merged=False)
    assert {c["member"] for c in strict["conflicts"]} == {"v1.0.0", "v1.0.2"}
    # an explicit merged set skips without any lookup
    explicit = cp.run(rec, ok, "v1.0.3", merged={"v1.0.0", "v1.0.2"}, check_merged=False)
    assert explicit["conflicts"] == [] and explicit["merged_skipped"] == ["v1.0.0", "v1.0.2"]


def test_coordinator_claim_reports_only_active_member_conflicts_and_no_owned_path_error(cp):
    rec = _train_record()
    paths = ["CHANGELOG.md", "docs/releases/v1/v1.0/known-gaps.md", "docs/todos.md"]
    report = cp.run(rec, paths, "v1.0.3", merged={"v1.0.0", "v1.0.2"}, check_merged=False, coordinator=True)
    assert [(c["member"], c["kind"], c["path"]) for c in report["conflicts"]] == [
        ("v1.0.5", "coordinator-write/read", "docs/releases/v1/v1.0/known-gaps.md")]
    assert not any(f["code"] == "coordinator-owned-path" for f in report["findings"])
    # the same paths as an ordinary worker draft ARE refused as coordinator-owned
    worker = cp.run(rec, draft(writes=paths), "v1.0.3", merged={"v1.0.0", "v1.0.2"}, check_merged=False)
    assert any(f["code"] == "coordinator-owned-path" for f in worker["findings"])
    assert cp.run(rec, {"write_paths": []}, None, coordinator=True, check_merged=False)["ok"] is False
