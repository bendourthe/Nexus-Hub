"""permit-member-paths and correct-read: captured decisions that change one admitted member's reservations.

permit-member-paths appends exact files to an admitted member's write list; correct-read releases one
exact literal recorded read file of an unpublished member until its own publication start.

Every record, secret and capture below is a disposable fixture under a temporary home.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, _no_transport_overrides  # noqa: F401
from .test_completion_minor_verdict import Walk, ck, cm
from .test_parallel_member_implementation import (  # noqa: F401  (parallel is a fixture)
    admit,
    claims,
    commit_worker,
    merge_worker,
    parallel,
    project,
    publication,
    worker,
)

EXTRA = "src/extra.txt"


def paths_file(repo: Walk, paths: object) -> Path:
    path = repo.tmp / f"paths-{len(list(repo.tmp.glob('paths-*.json')))}.json"
    path.write_text(json.dumps({"write_paths": paths} if isinstance(paths, list) else paths), encoding="utf-8")
    return path


def permit_args(repo: Walk, version: str, file: Path, *, session: str = SESSION) -> list[str]:
    return ["--minor", "v0.5", "--member", version, "--session", session, "--repo", str(repo.work), "--paths", str(file)]


def render(repo: Walk, version: str, file: Path):
    return repo.render(SESSION, "--action", "permit-member-paths", "--member", version, "--paths", str(file))


def permit(repo: Walk, version: str, file: Path, *extra: str, session: str = SESSION):
    return repo.run("record", "permit-member-paths", *permit_args(repo, version, file, session=session), *extra)


def grant(repo: Walk, version: str, paths: list[str]):
    file = paths_file(repo, paths)
    repo.paste(SESSION, "--action", "permit-member-paths", "--member", version, "--paths", str(file))
    return permit(repo, version, file)


def member(repo: Walk, version: str = "v0.5.2") -> dict:
    return next(m for m in repo.record()["members"] if m["version"] == version)


def identity(repo: Walk, version: str = "v0.5.2") -> str:
    return project(repo, version)[1]["predicates"]["implementation.identity"]


def admitted(repo: Walk) -> tuple[Path, dict]:
    root = worker(repo, "v0.5.2")
    assert admit(repo, "v0.5.2", root).returncode == 0
    commit_worker(root, "src/alpha.txt", "own work\n")
    return root, member(repo)["implementation"]


def refused(result, reason: str) -> None:
    assert result.returncode != 0 and reason in result.stdout + result.stderr, result.stdout + result.stderr


def test_captured_decision_appends_sorted_union_and_clears_the_outside_path(parallel: Walk) -> None:
    root, before = admitted(parallel)
    commit_worker(root, EXTRA, "outside the frozen list\n")
    assert identity(parallel) == "unmet"
    omega_before = member(parallel, "v0.5.10")
    other = {k: v for k, v in parallel.record().items() if k not in ("members", "approvals_hmac")}
    result = grant(parallel, "v0.5.2", [EXTRA])
    assert result.returncode == 0 and result.stdout.startswith("PERMITTED v0.5.2"), result.stdout + result.stderr
    after = member(parallel)
    assert after["implementation"]["write_paths"] == sorted([*before["write_paths"], EXTRA])
    assert {k: v for k, v in after["implementation"].items() if k != "write_paths"} == {
        k: v for k, v in before.items() if k != "write_paths"}
    entry = after["member_path_permissions"][0]
    assert entry["page"]["write_paths"] == [EXTRA] and entry["page"]["original_write_paths"] == before["write_paths"]
    assert entry["accepted"]["authorization_context"]["origin"] == "host-hook-capture"
    assert member(parallel, "v0.5.10") == omega_before
    assert {k: v for k, v in parallel.record().items() if k not in ("members", "approvals_hmac")} == other
    assert parallel.load().record is not None
    assert identity(parallel) == "met"


def test_worker_resume_keeps_working_after_an_append(parallel: Walk) -> None:
    root, original = admitted(parallel)
    assert grant(parallel, "v0.5.2", [EXTRA]).returncode == 0
    base = original["base_head"]
    stored = parallel.record_path().read_bytes()
    original_claims = {k: original[k] for k in ("depends_on", "read_paths", "write_paths")}
    extended = {**original_claims, "write_paths": sorted([*original["write_paths"], EXTRA])}
    for value in (original_claims, extended):
        resumed = admit(parallel, "v0.5.2", root, value, base=base)
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert parallel.record_path().read_bytes() == stored
    changed = claims(parallel, "v0.5.2", writes=("src/other.txt",))
    assert "implementation-already-started" in admit(parallel, "v0.5.2", root, changed, base=base).stdout
    assert identity(parallel) == "met"
    worker_ctx, status, _retired = cm._worker_context(ck, parallel.rctx(), parallel.record(), member(parallel), parallel.rctx().budget)
    assert worker_ctx is not None and status == "met"


def test_append_is_idempotent_and_keeps_existing_order(parallel: Walk) -> None:
    _root, before = admitted(parallel)
    assert grant(parallel, "v0.5.2", [EXTRA]).returncode == 0
    stored = parallel.record_path().read_bytes()
    again = permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA, before["write_paths"][0]]))
    assert again.returncode == 0 and "already present" in again.stdout
    assert parallel.record_path().read_bytes() == stored
    refused(render(parallel, "v0.5.2", paths_file(parallel, [EXTRA])), "member-paths-already-present")
    # A mixed request adds only the new file, and a path sorting before the old ones keeps their order.
    assert grant(parallel, "v0.5.2", ["docs/early.txt", EXTRA]).returncode == 0
    writes = member(parallel)["implementation"]["write_paths"]
    assert writes == sorted({*before["write_paths"], EXTRA, "docs/early.txt"})
    assert [p for p in writes if p in before["write_paths"]] == before["write_paths"]
    assert [e["page"]["write_paths"] for e in member(parallel)["member_path_permissions"]] == [[EXTRA], ["docs/early.txt"]]


def test_member_without_implementation_or_unknown_is_refused(parallel: Walk) -> None:
    admitted(parallel)
    before = parallel.record_path().read_bytes()
    refused(permit(parallel, "v0.5.10", paths_file(parallel, [EXTRA])), "member-paths-member-not-admitted")
    refused(permit(parallel, "v0.5.99", paths_file(parallel, [EXTRA])), "member-paths-unknown-member")
    assert parallel.record_path().read_bytes() == before


def test_merged_member_is_refused(parallel: Walk) -> None:
    root, _ = admitted(parallel)
    merge_worker(parallel, root, "v0.5.2")
    before = parallel.record_path().read_bytes()
    refused(permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA])), "member-paths-member-finished")
    assert parallel.record_path().read_bytes() == before


def literal_refusal(repo: Walk, value: object, reason: str) -> None:
    """Pure input validation, in process: the same helper the render and consume paths call."""
    with pytest.raises(ck.Malformed, match=reason):
        cm._member_paths_literals(ck, repo.rctx(), "v0.5", value)


def test_input_validation_names_each_refusal(parallel: Walk) -> None:
    assert cm._member_paths_literals(ck, parallel.rctx(), "v0.5", {"write_paths": [EXTRA, "docs/a.txt"]}) == [EXTRA, "docs/a.txt"]
    for entry in ("src/dir/", "src/*.py", "src/[ab].py", "/etc/passwd", "C:/outside", "../outside", "src/../x.txt",
                  "src\\file", "", " src/x.txt", "src//x.txt", 7):
        literal_refusal(parallel, {"write_paths": [EXTRA, entry]}, "member-paths-not-literal")
    for value in ([EXTRA, EXTRA], [EXTRA, "SRC/Extra.txt"]):
        literal_refusal(parallel, {"write_paths": value}, "member-paths-duplicate")
    for bad in ({"write_paths": []}, {"write_paths": "src/x.txt"}, {"paths": ["src/x.txt"]},
                {"write_paths": ["src/x.txt"], "more": 1}, ["src/x.txt"]):
        literal_refusal(parallel, bad, "member-paths-invalid-input")
    for path in (".github/workflows/ci.yml", ".env", "config/credentials.json", "catalog/hooks/settings.json"):
        literal_refusal(parallel, {"write_paths": [path]}, "member-paths-sensitive")
    for path in ("CHANGELOG.md", "docs/todos.md", "docs/releases/v0/v0.5/known-gaps.md", "VERSION"):
        literal_refusal(parallel, {"write_paths": [path]}, "member-paths-coordinator-reserved")
    with pytest.raises(ck.Malformed, match="member-paths-unreadable-input"):
        cm._member_paths_input(ck, str(parallel.tmp / "absent.json"))


def test_cli_refuses_non_literal_sensitive_and_reserved_files_without_mutation(parallel: Walk) -> None:
    admitted(parallel)
    before = parallel.record_path().read_bytes()
    refused(permit(parallel, "v0.5.2", paths_file(parallel, ["src/dir/"])), "member-paths-not-literal")
    refused(permit(parallel, "v0.5.2", paths_file(parallel, [".github/workflows/ci.yml"])), "member-paths-sensitive")
    refused(permit(parallel, "v0.5.2", paths_file(parallel, ["CHANGELOG.md"])), "member-paths-coordinator-reserved")
    refused(permit(parallel, "v0.5.2", parallel.tmp / "absent.json"), "member-paths-unreadable-input")
    refused(render(parallel, "v0.5.2", paths_file(parallel, [EXTRA, EXTRA])), "member-paths-duplicate")
    assert parallel.record_path().read_bytes() == before


def test_overlap_with_another_active_member_is_refused(parallel: Walk) -> None:
    admitted(parallel)
    omega = worker(parallel, "v0.5.10")
    spec = claims(parallel, "v0.5.10", reads=("shared/input.txt",), writes=("src/omega.txt", "lib/"))
    assert admit(parallel, "v0.5.10", omega, spec).returncode == 0
    record = parallel.record()
    next(m for m in record["members"] if m["version"] == "v0.5.10")["coordinator_paths"] = ["src/published.txt"]
    parallel.write_record(record, resign=True)
    before = parallel.record_path().read_bytes()
    for requested in ("src/omega.txt", "Src/Omega.txt", "lib/nested/out.txt", "src/published.txt"):
        refused(permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA, requested])), "member-paths-active-conflict")
        refused(render(parallel, "v0.5.2", paths_file(parallel, [EXTRA, requested])), "member-paths-active-conflict")
    assert parallel.record_path().read_bytes() == before
    assert permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA])).returncode == ck.EXIT_BLOCKED  # no decision yet, but no conflict


def test_read_overlap_is_allowed_only_for_a_later_member(parallel: Walk) -> None:
    alpha = worker(parallel, "v0.5.2")
    early = claims(parallel, "v0.5.2", reads=("early/input.txt",))
    assert admit(parallel, "v0.5.2", alpha, early).returncode == 0
    omega = worker(parallel, "v0.5.10")
    late = claims(parallel, "v0.5.10", reads=("shared/input.txt",), writes=("src/omega.txt",))
    assert admit(parallel, "v0.5.10", omega, late).returncode == 0
    before = parallel.record_path().read_bytes()
    # v0.5.10 is published after v0.5.2, so it only reads shared/input.txt for now: render and record both accept the request.
    assert render(parallel, "v0.5.2", paths_file(parallel, ["shared/input.txt"])).returncode == 0
    assert permit(parallel, "v0.5.2", paths_file(parallel, ["shared/input.txt"])).returncode == ck.EXIT_BLOCKED
    assert parallel.record_path().read_bytes() == before
    # v0.5.2 is published before v0.5.10, so v0.5.10 may not take a path v0.5.2 still reads or writes.
    for requested in ("early/input.txt", "src/alpha.txt"):
        refused(render(parallel, "v0.5.10", paths_file(parallel, [requested])), "member-paths-active-conflict")
        refused(permit(parallel, "v0.5.10", paths_file(parallel, [requested])), "member-paths-active-conflict")
    assert grant(parallel, "v0.5.2", ["shared/input.txt"]).returncode == 0
    assert "shared/input.txt" in member(parallel)["implementation"]["write_paths"]


def test_merged_member_no_longer_holds_paths(parallel: Walk) -> None:
    alpha = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", reads=("early/input.txt",))).returncode == 0
    commit_worker(alpha, "src/alpha.txt", "own work\n")
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega).returncode == 0
    refused(permit(parallel, "v0.5.10", paths_file(parallel, ["src/alpha.txt"])), "member-paths-active-conflict")
    merge_worker(parallel, alpha, "v0.5.2")
    _git(parallel.work, "merge", "-q", "--ff-only", "origin/develop")
    _git(omega, "merge", "-q", "--ff-only", "origin/develop")
    for requested in ("src/alpha.txt", "early/input.txt"):
        assert render(parallel, "v0.5.10", paths_file(parallel, [requested])).returncode == 0
        assert permit(parallel, "v0.5.10", paths_file(parallel, [requested])).returncode == ck.EXIT_BLOCKED
    assert grant(parallel, "v0.5.10", ["src/alpha.txt"]).returncode == 0



def test_missing_wrong_or_replayed_decision_is_refused(parallel: Walk) -> None:
    admitted(parallel)
    before = parallel.record_path().read_bytes()
    file = paths_file(parallel, [EXTRA])
    # No round was rendered.
    assert permit(parallel, "v0.5.2", file).returncode == ck.EXIT_BLOCKED
    # A round rendered for different files does not cover these files.
    other = paths_file(parallel, ["src/other-file.txt"])
    parallel.paste(SESSION, "--action", "permit-member-paths", "--member", "v0.5.2", "--paths", str(other))
    assert permit(parallel, "v0.5.2", file).returncode == ck.EXIT_BLOCKED
    # A mismatched --text is not the captured decision.
    parallel.paste(SESSION, "--action", "permit-member-paths", "--member", "v0.5.2", "--paths", str(file))
    wrong = permit(parallel, "v0.5.2", file, "--text", "Approve something else")
    assert wrong.returncode == ck.EXIT_BLOCKED and "approval-not-captured" in wrong.stdout
    assert parallel.record_path().read_bytes() == before
    # The mismatched --text spent that round (as in permit-outputs), so a fresh round is needed.
    assert permit(parallel, "v0.5.2", file).returncode == ck.EXIT_BLOCKED
    parallel.paste(SESSION, "--action", "permit-member-paths", "--member", "v0.5.2", "--paths", str(file))
    # The matching captured decision records once; the same round cannot be replayed for new files.
    assert permit(parallel, "v0.5.2", file).returncode == 0
    replay = permit(parallel, "v0.5.2", paths_file(parallel, ["src/replay.txt"]))
    assert replay.returncode == ck.EXIT_BLOCKED
    assert "src/replay.txt" not in member(parallel)["implementation"]["write_paths"]


def test_decision_must_be_captured_in_the_owning_session(parallel: Walk) -> None:
    admitted(parallel)
    before = parallel.record_path().read_bytes()
    file = paths_file(parallel, [EXTRA])
    parallel.capture("intruder", "/implement v0.5", at=0.0)
    parallel.render("intruder", "--action", "permit-member-paths", "--member", "v0.5.2", "--paths", str(file))
    other = permit(parallel, "v0.5.2", file, session="intruder")
    assert other.returncode != 0
    assert parallel.record_path().read_bytes() == before


def test_tampered_record_is_refused(parallel: Walk) -> None:
    admitted(parallel)
    record = parallel.record()
    member_ = next(m for m in record["members"] if m["version"] == "v0.5.2")
    member_["implementation"]["write_paths"].append(EXTRA)
    parallel.write_record(record, resign=False)
    before = parallel.record_path().read_bytes()
    result = permit(parallel, "v0.5.2", paths_file(parallel, ["src/other-file.txt"]))
    assert result.returncode != 0 and "src/other-file.txt" not in parallel.record_path().read_text(encoding="utf-8")
    assert parallel.record_path().read_bytes() == before


def test_write_guard_rejects_unleased_edits_and_rewritten_history(parallel: Walk) -> None:
    _root, _ = admitted(parallel)
    before = parallel.record()
    assert grant(parallel, "v0.5.2", [EXTRA]).returncode == 0
    after = parallel.record()
    rctx = parallel.rctx()
    cm.check_member_paths_write(ck, rctx, after, after)

    def broken(mutate):
        record = json.loads(json.dumps(after))
        mutate(next(m for m in record["members"] if m["version"] == "v0.5.2"))
        return record

    for mutate in (
        lambda m: m.pop("member_path_permissions"),
        lambda m: m["member_path_permissions"].clear(),
        lambda m: m["member_path_permissions"][0]["page"].update(write_paths=["src/elsewhere.txt"]),
    ):
        with pytest.raises(ck.MinorConflict, match="member-paths-not-append-only"):
            cm.check_member_paths_write(ck, rctx, after, broken(mutate))
    with pytest.raises(ck.MinorConflict, match="member-paths-claims-changed"):
        cm.check_member_paths_write(ck, rctx, after, broken(lambda m: m["implementation"]["write_paths"].append("src/more.txt")))
    # Appending history without the consumed leased decision is never accepted.
    with pytest.raises(ck.MinorConflict, match="member-paths-append-not-captured"):
        cm.check_member_paths_write(ck, rctx, before, after)


# --------------------------------------------------------------------------- correct-read

LEDGER = "docs/releases/v0/v0.5/known-gaps.md"
SHARED = "shared/input.txt"
PLAN = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"


def read_render(repo: Walk, version: str, path: str, *extra: str):
    return repo.render(SESSION, "--action", "correct-read", "--member", version, "--path", path, *extra)


def read_correct(repo: Walk, version: str, path: str, *extra: str, session: str = SESSION):
    return repo.run("record", "correct-read", "--minor", "v0.5", "--member", version, "--session", session,
                    "--repo", str(repo.work), "--path", path, *extra)


def release_read(repo: Walk, version: str, path: str):
    repo.paste(SESSION, "--action", "correct-read", "--member", version, "--path", path)
    return read_correct(repo, version, path)


def real_case(repo: Walk) -> tuple[Path, Path]:
    """v0.5.10 records a read of the ledger that v0.5.2's own publication must write (the v4.15.5 versus v4.15.3 shape)."""
    alpha, omega = worker(repo, "v0.5.2"), worker(repo, "v0.5.10")
    assert admit(repo, "v0.5.2", alpha).returncode == 0
    assert admit(repo, "v0.5.10", omega, claims(repo, "v0.5.10", reads=(LEDGER, "docs/guide.md"))).returncode == 0
    return alpha, omega


def effective(repo: Walk, version: str) -> list[str]:
    record = repo.record()
    return cm.effective_read_paths(ck, repo.rctx(), record, next(m for m in record["members"] if m["version"] == version))


def test_correct_read_real_case_conflict_then_admitted_then_restored(
        parallel: Walk, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    alpha, omega = real_case(parallel)
    assert "coordinator-scope-conflict" in publication(parallel, "v0.5.2", [LEDGER, "CHANGELOG.md"]).stdout
    raw = member(parallel, "v0.5.10")["implementation"]
    other = {k: v for k, v in parallel.record().items() if k not in ("members", "approvals_hmac")}
    result = release_read(parallel, "v0.5.10", LEDGER)
    assert result.returncode == 0 and result.stdout.startswith("CORRECTED v0.5.10"), result.stdout + result.stderr
    after = member(parallel, "v0.5.10")
    assert after["implementation"] == raw and LEDGER in after["implementation"]["read_paths"]
    entry = after["member_read_corrections"][0]
    assert entry["page"]["path"] == LEDGER and entry["page"]["original_read_paths"] == raw["read_paths"]
    assert entry["accepted"]["authorization_context"]["origin"] == "host-hook-capture"
    assert member(parallel, "v0.5.2") == next(m for m in parallel.record()["members"] if m["version"] == "v0.5.2")
    assert {k: v for k, v in parallel.record().items() if k not in ("members", "approvals_hmac")} == other
    assert parallel.load().record is not None
    assert effective(parallel, "v0.5.10") == ["docs/guide.md"]
    stored = parallel.record_path().read_bytes()
    again = read_correct(parallel, "v0.5.10", LEDGER)
    assert again.returncode == 0 and again.stdout.startswith("ALREADY"), again.stdout
    assert parallel.record_path().read_bytes() == stored
    refused(read_render(parallel, "v0.5.10", LEDGER), "read-correction-already-present")
    started = publication(parallel, "v0.5.2", [LEDGER, "CHANGELOG.md"])
    assert started.returncode == 0, started.stdout + started.stderr
    assert member(parallel, "v0.5.2")["coordinator_paths"] == sorted([LEDGER, "CHANGELOG.md"])
    # v0.5.10's own ordered start is refused while v0.5.2 is unmerged, then restores the raw reads once it is merged.
    _stub_gate(monkeypatch)
    commit_worker(alpha, LEDGER, "# ledger\n")
    commit_worker(alpha, "CHANGELOG.md", "# changelog\n")
    code, out = start_in_process(parallel, capsys)
    assert code == ck.EXIT_BLOCKED and "read-correction-restore-unverified" in out, out
    assert "start_head" not in member(parallel, "v0.5.10")
    merge_worker(parallel, alpha, "v0.5.2")
    _git(parallel.work, "merge", "-q", "--ff-only", "origin/develop")
    _git(omega, "merge", "-q", "--ff-only", "origin/develop")
    code, out = start_in_process(parallel, capsys)
    assert code == 0, out
    final = member(parallel, "v0.5.10")
    assert final["start_head"] and final["implementation"] == raw and len(final["member_read_corrections"]) == 1
    assert effective(parallel, "v0.5.10") == raw["read_paths"]
    assert parallel.load().record is not None
    refused(read_render(parallel, "v0.5.10", LEDGER), "read-correction-already-present")


def start_in_process(repo: Walk, capsys: pytest.CaptureFixture) -> tuple[int, str]:
    args = ck.build_parser().parse_args(["record", "member-start", "--minor", "v0.5", "--member", "v0.5.10", "--session", SESSION,
                                         "--repo", str(repo.work), "--head", repo.head()])
    code = cm.cmd_record_member_start(ck, args)
    return code, capsys.readouterr().out


def _stub_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """The previous member's release evidence is outside this test; the restore rule is what runs."""
    real = cm.evaluate_member

    def evaluate(*args, **kwargs):
        result = real(*args, **kwargs)
        result.lines = [(pid, "met") for pid, _status in result.lines]
        return result

    monkeypatch.setattr(cm, "evaluate_member", evaluate)
    monkeypatch.setattr(cm, "member_gate", lambda *a, **k: "met")
    monkeypatch.setattr(cm, "_previous_in", lambda *a, **k: "met")


def test_correct_read_applies_in_both_admission_directions(parallel: Walk) -> None:
    alpha = worker(parallel, "v0.5.2")
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED,))).returncode == 0
    wants_shared = claims(parallel, "v0.5.2", writes=("src/alpha.txt", SHARED))
    assert "implementation-scope-conflict" in admit(parallel, "v0.5.2", alpha, wants_shared).stdout
    assert release_read(parallel, "v0.5.10", SHARED).returncode == 0
    assert admit(parallel, "v0.5.2", alpha, wants_shared).returncode == 0
    # The corrected member resumes with its original claims against the other member's write of the released file.
    resumed = admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED,)), base=member(parallel, "v0.5.10")["implementation"]["base_head"])
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert member(parallel, "v0.5.10")["implementation"]["read_paths"] == [SHARED]


def test_correct_read_refuses_anything_but_an_exact_literal_recorded_read(parallel: Walk) -> None:
    alpha = worker(parallel, "v0.5.2")
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", reads=(SHARED,))).returncode == 0
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=("docs/guide.md", "lib/"), writes=("src/omega.txt", "out/result.txt"))).returncode == 0
    before = parallel.record_path().read_bytes()
    cases = {
        "src/omega.txt": "read-correction-write-path",
        "out/result.txt": "read-correction-write-path",
        "lib/": "read-correction-not-literal",
        "lib/deep/file.txt": "read-correction-directory-read",
        "docs/other.md": "read-correction-not-a-read",
        "docs/*.md": "read-correction-not-literal",
        "../x": "read-correction-not-literal",
        "docs\\guide.md": "read-correction-not-literal",
        "": "read-correction-not-literal",
        " docs/guide.md": "read-correction-not-literal",
        "DOCS/GUIDE.MD": "read-correction-not-a-read",
        SHARED: "read-correction-not-a-read",
    }
    for path, reason in cases.items():
        refused(read_render(parallel, "v0.5.10", path), reason)
        refused(read_correct(parallel, "v0.5.10", path), reason)
    refused(read_render(parallel, "v0.5.99", "docs/guide.md"), "read-correction-unknown-member")
    assert parallel.record_path().read_bytes() == before
    # A write claim of the same member and a member without implementation refuse as well.
    record = parallel.record()
    next(m for m in record["members"] if m["version"] == "v0.5.10").pop("implementation")
    parallel.write_record(record, resign=True)
    refused(read_render(parallel, "v0.5.10", "docs/guide.md"), "read-correction-member-not-admitted")


def test_correct_read_refuses_a_member_with_a_publication_start(parallel: Walk) -> None:
    alpha = worker(parallel, "v0.5.2")
    assert admit(parallel, "v0.5.2", alpha, claims(parallel, "v0.5.2", reads=(SHARED,))).returncode == 0
    assert publication(parallel, "v0.5.2").returncode == 0
    before = parallel.record_path().read_bytes()
    refused(read_render(parallel, "v0.5.2", SHARED), "read-correction-member-started")
    refused(read_correct(parallel, "v0.5.2", SHARED), "read-correction-member-started")
    assert parallel.record_path().read_bytes() == before


def test_correct_read_refuses_paused_completed_and_tampered_records(parallel: Walk) -> None:
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED,))).returncode == 0
    record = parallel.record()
    next(m for m in record["members"] if m["version"] == "v0.5.10")["implementation"]["read_paths"].append("docs/extra.md")
    parallel.write_record(record, resign=False)
    before = parallel.record_path().read_bytes()
    result = read_render(parallel, "v0.5.10", SHARED)
    assert result.returncode != 0
    result = read_correct(parallel, "v0.5.10", SHARED)
    assert result.returncode != 0 and "member_read_corrections" not in parallel.record_path().read_text(encoding="utf-8")
    assert parallel.record_path().read_bytes() == before


def test_correct_read_without_a_genuine_decision_changes_nothing(parallel: Walk) -> None:
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED, "docs/guide.md"))).returncode == 0
    before = parallel.record_path().read_bytes()
    assert read_correct(parallel, "v0.5.10", SHARED).returncode == ck.EXIT_BLOCKED
    parallel.paste(SESSION, "--action", "correct-read", "--member", "v0.5.10", "--path", "docs/guide.md")
    assert read_correct(parallel, "v0.5.10", SHARED).returncode == ck.EXIT_BLOCKED
    parallel.paste(SESSION, "--action", "correct-read", "--member", "v0.5.10", "--path", SHARED)
    wrong = read_correct(parallel, "v0.5.10", SHARED, "--text", "Approve something else")
    assert wrong.returncode == ck.EXIT_BLOCKED and "approval-not-captured" in wrong.stdout
    assert parallel.record_path().read_bytes() == before
    # A synthesized approval is not a capture: the owner session never sent the line.
    parallel.capture("intruder", "/implement v0.5", at=0.0)
    parallel.render("intruder", "--action", "correct-read", "--member", "v0.5.10", "--path", SHARED)
    assert read_correct(parallel, "v0.5.10", SHARED, session="intruder").returncode != 0
    assert parallel.record_path().read_bytes() == before
    # The same round cannot be replayed for another file.
    parallel.paste(SESSION, "--action", "correct-read", "--member", "v0.5.10", "--path", SHARED)
    assert read_correct(parallel, "v0.5.10", SHARED).returncode == 0
    assert read_correct(parallel, "v0.5.10", "docs/guide.md").returncode == ck.EXIT_BLOCKED
    assert effective(parallel, "v0.5.10") == ["docs/guide.md"]


def test_correct_read_renders_one_question_and_page(parallel: Walk) -> None:
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED,))).returncode == 0
    question = read_render(parallel, "v0.5.10", SHARED, "--question")
    assert question.returncode == 0, question.stderr
    data = json.loads(question.stdout)
    assert data["question"] == "Temporarily release only the displayed exact read file of the displayed member for v0.5?"
    assert data["action_scope"]["path"] == SHARED and data["action_scope"]["member"] == "v0.5.10"
    assert "Exact file: `" + SHARED + "`" in data["review_page"] or SHARED in data["review_page"]
    line = read_render(parallel, "v0.5.10", SHARED).stdout.splitlines()[0]
    assert line.startswith("Correct the displayed one-file read reservation in /implement v0.5 (approval ")


def test_correct_read_blocks_permit_member_paths_and_keeps_history_append_only(parallel: Walk) -> None:
    omega = worker(parallel, "v0.5.10")
    assert admit(parallel, "v0.5.10", omega, claims(parallel, "v0.5.10", reads=(SHARED, "docs/guide.md"))).returncode == 0
    before = parallel.record()
    assert release_read(parallel, "v0.5.10", SHARED).returncode == 0
    after = parallel.record()
    refused(render(parallel, "v0.5.10", paths_file(parallel, [EXTRA])), "member-paths-bound-permissions")
    rctx = parallel.rctx()
    cm.check_read_correction_write(ck, rctx, after, after)

    def broken(mutate):
        record = json.loads(json.dumps(after))
        mutate(next(m for m in record["members"] if m["version"] == "v0.5.10"))
        return record

    for mutate in (
        lambda m: m.pop("member_read_corrections"),
        lambda m: m["member_read_corrections"].clear(),
        lambda m: m["member_read_corrections"][0]["page"].update(path="docs/guide.md"),
    ):
        with pytest.raises(ck.MinorConflict, match="read-correction-not-append-only"):
            cm.check_read_correction_write(ck, rctx, after, broken(mutate))
    with pytest.raises(ck.MinorConflict, match="read-correction-claims-changed"):
        cm.check_read_correction_write(ck, rctx, after, broken(lambda m: m["implementation"]["read_paths"].append("x/y.txt")))
    # Starting the member outside the native publication start never restores silently.
    with pytest.raises(ck.MinorConflict, match="read-correction-restore-not-native"):
        cm.check_read_correction_write(ck, rctx, after, broken(lambda m: m.update(start_head="a" * 40)))
    # Appending history without the consumed leased decision is never accepted.
    with pytest.raises(ck.MinorConflict, match="read-correction-append-not-captured"):
        cm.check_read_correction_write(ck, rctx, before, after)
    # An entry that no longer matches the unchanged claims releases nothing.
    tampered = json.loads(json.dumps(after))
    next(m for m in tampered["members"] if m["version"] == "v0.5.10")["member_read_corrections"][0]["page"]["path"] = "docs/guide.md"
    assert cm._read_correction_paths(ck, tampered, next(m for m in tampered["members"] if m["version"] == "v0.5.10")) == set()


def test_correct_read_never_renders_a_schema_one_approval(parallel: Walk) -> None:
    before = parallel.record_path().read_bytes()
    for args in (("--action", "correct-read"), ("--path", SHARED)):
        result = parallel.run("record", "render", PLAN, "--session", SESSION, *args)
        assert result.returncode == 2 and "require --minor" in result.stderr, result.stderr
    absent = parallel.run("record", "correct-read", "--member", "v0.5.10", "--session", SESSION, "--path", SHARED)
    assert absent.returncode == 2 and "--minor" in absent.stderr
    wrong_flag = parallel.render(SESSION, "--action", "permit-member-paths", "--member", "v0.5.10", "--path", SHARED)
    assert wrong_flag.returncode == 2 and "--path requires --action correct-read" in wrong_flag.stderr
    assert parallel.record_path().read_bytes() == before
