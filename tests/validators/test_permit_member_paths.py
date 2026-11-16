"""permit-member-paths: one captured decision appends exact files to an admitted member's write list.

Every record, secret and capture below is a disposable fixture under a temporary home.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .test_check_plan_completion import _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, _no_transport_overrides  # noqa: F401
from .test_completion_minor_verdict import Walk, ck, cm
from .test_parallel_member_implementation import (  # noqa: F401  (parallel is a fixture)
    admit,
    claims,
    commit_worker,
    merge_worker,
    parallel,
    project,
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
    for requested in ("src/omega.txt", "Src/Omega.txt", "lib/nested/out.txt", "shared/input.txt", "src/published.txt"):
        refused(permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA, requested])), "member-paths-active-conflict")
    assert parallel.record_path().read_bytes() == before
    assert permit(parallel, "v0.5.2", paths_file(parallel, [EXTRA])).returncode == ck.EXIT_BLOCKED  # no decision yet, but no conflict



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
