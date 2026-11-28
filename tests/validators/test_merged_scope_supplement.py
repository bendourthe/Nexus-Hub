"""Derived merged-scope supplements in disposable repositories.

Synthetic captures, signed records, and hosting replies below prove local behavior
only. They are not genuine production authority or release evidence. Unlike the
reviewed v4.14.2 descriptor, nothing here is substituted: the file lists come from
the merge itself.
"""

from __future__ import annotations

import copy

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import (  # noqa: F401
    SESSION,
    Minor,
    _no_transport_overrides,
)

# Fixture imports initialize the repository script path before runtime modules.
# isort: split
import check_plan_completion as ck
import completion_minor as cm

MINOR = "v0.5"
VERSION = "v0.5.2"
DEFAULT = {
    "member": ("docs/extra.md", "src/extra.txt"),
    "coordinator": ("CHANGELOG.md", "data/skills.json"),
}


def _member(record):
    return next(m for m in cm.ordered_members(record) if m["version"] == VERSION)


@pytest.fixture
def derived_case(tmp_path, monkeypatch, minor_git_seed, request):
    files = {**DEFAULT, **(getattr(request, "param", None) or {})}
    fx = Minor(tmp_path, monkeypatch, minor_git_seed)
    created = fx.create()
    assert created.returncode == 0, created.stdout + created.stderr
    base = _git(fx.work, "rev-parse", "HEAD")
    record = fx.record()
    member = _member(record)
    member["start_head"] = base
    member["coordinator_paths"] = []
    member["implementation"] = {
        "base_head": base,
        "worktree": str(tmp_path / "former-worker"),
        "branch": member["source_branch"],
        "depends_on": [],
        "read_paths": [],
        "write_paths": ["src/owned.txt"],
        "started": ck._now(),
    }
    fx.write_record(record, resign=True)  # Disposable fixture authority only.
    _git(fx.work, "checkout", "-q", "-b", member["source_branch"])
    for path in ("src/owned.txt", *files["member"], *files["coordinator"]):
        dest = fx.work / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("derived fixture output\n", encoding="utf-8")
    fx.commit("claimed, unclaimed and coordinator files")
    second = _git(fx.work, "rev-parse", "HEAD")
    _git(fx.work, "checkout", "-q", "develop")
    _git(
        fx.work,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "merge disposable member",
        member["source_branch"],
    )
    merge = _git(fx.work, "rev-parse", "HEAD")
    fx.publish("develop")
    fx.state["pr_by_branch"] = {
        member["source_branch"]: {
            "state": "MERGED",
            "checks": [{"name": "ci", "bucket": "pass"}],
            "merge_commit": merge,
        }
    }
    fx.save_state()
    monkeypatch.chdir(fx.work)
    return fx, {"merge": merge, "base": base, "second": second, "files": files}


def _cli(capsys, *args):
    capsys.readouterr()
    rc = ck.main(list(args))
    output = capsys.readouterr()
    return rc, output.out, output.err


def _args(case, session=SESSION, merge=None):
    return [
        "--minor",
        MINOR,
        "--member",
        VERSION,
        "--merge",
        merge or case["merge"],
        "--session",
        session,
    ]


def _render(capsys, case, **kwargs):
    rc, out, err = _cli(
        capsys,
        "record",
        "render",
        "--action",
        "supplement-scope",
        *_args(case, **kwargs),
    )
    return rc, out, err


def _status(fx, case, record=None):
    value = record if record is not None else fx.record()
    return cm._historical_claim_status(
        fx.rctx(), _member(value), case["merge"], value, ck=ck
    )


def _grant(fx, case, capsys):
    rc, out, err = _render(capsys, case)
    assert rc == 0, out + err
    fx.capture(SESSION, out.splitlines()[0])
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(case))
    assert rc == 0, out + err
    return fx.record()


def test_gap_is_derived_from_the_merge_and_separates_coordinator_files(derived_case):
    fx, case = derived_case
    record = fx.record()
    gap = cm.merged_scope_gap(ck, fx.rctx(), record, _member(record), case["merge"])
    assert [r[0] for r in gap["rows"]] == list(case["files"]["member"])
    assert [r[0] for r in gap["coordinator_rows"]] == list(case["files"]["coordinator"])
    assert gap["blocked"] == []
    assert "src/owned.txt" not in {
        r[0] for r in [*gap["rows"], *gap["coordinator_rows"]]
    }
    assert (
        gap["first_parent"] == case["base"] and gap["second_parent"] == case["second"]
    )
    assert _status(fx, case) == "unmet"


def test_preview_is_read_only_and_names_every_file(derived_case, capsys):
    fx, case = derived_case
    before, runs = fx.record_path().read_bytes(), sorted(
        p.name for p in fx.runs.rglob("*")
    )
    rc, out, err = _cli(
        capsys,
        "record",
        "scope-gap",
        "--minor",
        MINOR,
        "--member",
        VERSION,
        "--merge",
        case["merge"],
    )
    assert rc == 0, out + err
    assert "member contribution (2)" in out and "coordinator contribution (2)" in out
    for path in (*case["files"]["member"], *case["files"]["coordinator"]):
        assert path in out
    assert out.strip().splitlines()[-1] == "VERDICT supplementable"
    assert (
        fx.record_path().read_bytes() == before
        and sorted(p.name for p in fx.runs.rglob("*")) == runs
    )


def test_page_shows_member_and_coordinator_contribution_separately(
    derived_case, capsys
):
    fx, case = derived_case
    rc, page, err = _cli(capsys, "record", "render", "--action", "supplement-scope", "--page", *_args(case))
    assert rc == 0, page + err
    assert "Member contribution" in page and "Coordinator contribution" in page
    assert "computed by the tool" in page
    for path in (*case["files"]["member"], *case["files"]["coordinator"]):
        assert path in page


def test_cli_capture_grants_the_exact_derived_lists_and_releases_the_claim_audit(
    derived_case, capsys
):
    fx, case = derived_case
    before = fx.record()
    granted = _grant(fx, case, capsys)
    entries = _member(granted)["historical_scope_supplements"]
    assert len(entries) == 1
    bounds = entries[0]["page"]["merge_bounds"]
    assert [r[0] for r in bounds["rows"]] == list(case["files"]["member"])
    assert [r[0] for r in bounds["coordinator_rows"]] == list(
        case["files"]["coordinator"]
    )
    assert _status(fx, case, granted) == "met"
    assert {
        k: v for k, v in _member(granted).items() if k != "historical_scope_supplements"
    } == _member(before)
    assert (
        cm._merged_on_base(ck, fx.rctx(), granted, _member(granted), case["merge"])
        is True
    )
    assert (
        cm._merged_on_base(ck, fx.rctx(), before, _member(before), case["merge"])
        is False
    )


def test_supplement_never_covers_a_later_change(derived_case, capsys):
    fx, case = derived_case
    granted = _grant(fx, case, capsys)
    (fx.work / "src/extra.txt").write_text("a later change\n", encoding="utf-8")
    (fx.work / "src/brand-new.txt").write_text("a later file\n", encoding="utf-8")
    fx.commit("later work is not retrospectively approved")
    later = _git(fx.work, "rev-parse", "HEAD")
    assert (
        cm._historical_claim_status(fx.rctx(), _member(granted), later, granted, ck=ck)
        != "met"
    )


@pytest.mark.parametrize(
    "merge", ["*", "abc123", "0" * 40, "HEAD", "refs/heads/develop", "A" * 40]
)
def test_wildcards_short_names_and_unknown_commits_are_refused(
    derived_case, capsys, merge
):
    fx, case = derived_case
    before = fx.record_path().read_bytes()
    rc, out, err = _render(capsys, case, merge=merge)
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before


def test_only_the_recorded_pull_request_merge_is_accepted(derived_case, capsys):
    fx, case = derived_case
    for other in (case["second"], case["base"]):
        rc, out, err = _render(capsys, case, merge=other)
        assert rc != 0, out + err
    rc, out, err = _cli(
        capsys,
        "record",
        "scope-gap",
        "--minor",
        MINOR,
        "--member",
        VERSION,
        "--merge",
        case["second"],
    )
    assert rc != 0 and "REFUSED merged-scope-not-a-merge-commit" in out


def test_unknown_member_and_empty_gap_are_refused(derived_case, capsys):
    fx, case = derived_case
    rc, out, err = _cli(
        capsys,
        "record",
        "render",
        "--action",
        "supplement-scope",
        "--minor",
        MINOR,
        "--member",
        "v0.5.99",
        "--merge",
        case["merge"],
        "--session",
        SESSION,
    )
    assert rc != 0, out + err
    record = fx.record()
    _member(record)["implementation"]["write_paths"] = [
        "src/",
        "docs/",
        "CHANGELOG.md",
        "data/",
    ]
    fx.write_record(record, resign=True)
    rc, out, err = _render(capsys, case)
    assert rc != 0 and "nothing-to-supplement" in out + err


@pytest.mark.parametrize(
    "derived_case",
    [{"member": ("src/extra.txt", ".github/workflows/ci.yml")}],
    indirect=True,
)
def test_sensitive_files_can_never_be_supplemented(derived_case, capsys):
    fx, case = derived_case
    before = fx.record_path().read_bytes()
    rc, out, err = _render(capsys, case)
    assert rc != 0 and "merged-scope-protected-path" in out + err
    rc, out, err = _cli(
        capsys,
        "record",
        "scope-gap",
        "--minor",
        MINOR,
        "--member",
        VERSION,
        "--merge",
        case["merge"],
    )
    assert rc != 0 and "sensitive .github/workflows/ci.yml" in out
    assert out.strip().splitlines()[-1].startswith("VERDICT refused")
    assert fx.record_path().read_bytes() == before


def test_agent_cannot_self_approve_or_replay(derived_case, capsys):
    fx, case = derived_case
    rc, out, err = _render(capsys, case)
    assert rc == 0, out + err
    before = fx.record_path().read_bytes()
    rc, out, err = _cli(
        capsys, "record", "supplement-scope", *_args(case), "--text", "Approve"
    )
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before
    fx.capture(SESSION, out_line := _render(capsys, case)[1].splitlines()[0])
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(case))
    assert rc == 0, out + err
    after = fx.record_path().read_bytes()
    fx.capture(SESSION, out_line)
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(case))
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == after


def test_forged_or_altered_entries_never_count(derived_case, capsys):
    fx, case = derived_case
    granted = _grant(fx, case, capsys)
    assert _status(fx, case, granted) == "met"
    for section, name in (
        ("page", "merge_bounds"),
        ("page", "member"),
        ("accepted", "code"),
        ("accepted", "text"),
    ):
        changed = copy.deepcopy(granted)
        target = _member(changed)["historical_scope_supplements"][0][section]
        target[name] = "forged"
        changed["approvals_hmac"] = ck._sign(changed, ck._secret(create=False) or b"")
        assert _status(fx, case, changed) != "met", (section, name)
    widened = copy.deepcopy(granted)
    bounds = _member(widened)["historical_scope_supplements"][0]["page"]["merge_bounds"]
    bounds["coordinator_rows"].append(["README.md", *bounds["rows"][0][1:]])
    widened["approvals_hmac"] = ck._sign(widened, ck._secret(create=False) or b"")
    assert _status(fx, case, widened) != "met"
    forged = copy.deepcopy(fx.record())
    _member(forged)["historical_scope_supplements"] = [{"page": {}, "accepted": {}}]
    before = fx.record_path().read_bytes()
    forged["approvals_hmac"] = ck._sign(forged, ck._secret(create=False) or b"")
    with pytest.raises(ck.MinorConflict):
        ck._write_record(fx.record_path(), forged)
    assert fx.record_path().read_bytes() == before


def test_second_supplement_for_the_same_member_is_refused(derived_case, capsys):
    fx, case = derived_case
    _grant(fx, case, capsys)
    rc, out, err = _render(capsys, case)
    assert rc != 0 and "already-supplemented" in out + err


def test_amended_member_supplement_is_recorded_signed_and_preserved(tmp_path, monkeypatch, minor_git_seed, capsys):
    from .test_minor_scope_amendment import amend_fixture

    fx = Minor(tmp_path, monkeypatch, minor_git_seed)
    amend_fixture(fx)
    version = "v0.5.11"
    base = _git(fx.work, "rev-parse", "HEAD")
    record = fx.record()
    member = record["minor_amendment_members"][0]
    member["implementation"] = {
        "base_head": base, "worktree": str(tmp_path / "former-worker"), "branch": member["source_branch"],
        "depends_on": [], "read_paths": [], "write_paths": ["src/owned.txt"], "started": ck._now(),
    }
    record["approvals_hmac"] = cm._sign(ck, record, ck._secret(create=False) or b"")
    fx.record_path().write_text(__import__("json").dumps(record), encoding="utf-8")
    _git(fx.work, "checkout", "-q", "-b", member["source_branch"])
    for path in ("src/owned.txt", "src/extra.txt", "CHANGELOG.md"):
        dest = fx.work / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("amended fixture output\n", encoding="utf-8")
    fx.commit("amended member output")
    _git(fx.work, "checkout", "-q", "develop")
    _git(fx.work, "merge", "-q", "--no-ff", "-m", "merge amended member", member["source_branch"])
    merge = _git(fx.work, "rev-parse", "HEAD")
    fx.publish("develop")
    fx.state["pr_by_branch"] = {member["source_branch"]: {
        "state": "MERGED", "checks": [{"name": "ci", "bucket": "pass"}], "merge_commit": merge}}
    fx.save_state()
    monkeypatch.chdir(fx.work)

    def status(value):
        found = next(m for m in cm.ordered_members(value) if m["version"] == version)
        return cm._historical_claim_status(fx.rctx(), found, merge, value, ck=ck)

    assert status(fx.record()) == "unmet"
    argv = ["--minor", MINOR, "--member", version, "--merge", merge, "--session", SESSION]
    rc, out, err = _cli(capsys, "record", "render", "--action", "supplement-scope", *argv)
    assert rc == 0, out + err
    fx.capture(SESSION, out.splitlines()[0])
    rc, out, err = _cli(capsys, "record", "supplement-scope", *argv)
    assert rc == 0, out + err
    granted = fx.record()
    assert "historical_scope_supplements" not in granted["members"][0]
    entry = granted["minor_amendment_members"][0]["historical_scope_supplements"][0]
    assert [r[0] for r in entry["page"]["merge_bounds"]["rows"]] == ["src/extra.txt"]
    assert [r[0] for r in entry["page"]["merge_bounds"]["coordinator_rows"]] == ["CHANGELOG.md"]
    assert status(granted) == "met"
    assert cm.load_minor(ck, fx.rctx(), MINOR, SESSION, minor_protocol=cm.MINOR_AMENDMENT_PROTOCOL,
                         execution_protocol=cm.MINOR_EXECUTION_PROTOCOL).forced is None
