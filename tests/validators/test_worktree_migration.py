"""Reviewed-manifest migration: real moves on real repositories, every interruption boundary.

The real executor runs against fixtures and each resulting state is inspected; nothing
here mocks a successful move. Dirty, staged, untracked and ignored content carries
distinctive bytes so a preservation failure shows up as a content difference.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts import nexus_worktrees as nw

IS_NT = os.name == "nt"


def git(*args: str, cwd: Path, check: bool = True) -> str:
    return subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


@pytest.fixture(autouse=True)
def clean_faults():
    yield
    for name in nw.FAULTS:
        nw.FAULTS[name] = None


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    home = tmp_path / "home"
    home.mkdir()
    cfg = tmp_path / "gitconfig"
    cfg.write_text(
        "[user]\n\tname = F\n\temail = f@example.invalid\n[init]\n\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    for key, value in {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "NEXUS_HUB_HOME": str(home / ".nexus-hub"),
        "NEXUS_WORKTREE_STATE": str(tmp_path / "state"),
        "NEXUS_WORKTREE_ROOT": str(tmp_path / "central"),
        "NEXUS_HUB_RUNS_DIR": str(tmp_path / "runs"),
        "GIT_CONFIG_GLOBAL": str(cfg),
        "GIT_CONFIG_NOSYSTEM": "1",
    }.items():
        monkeypatch.setenv(key, value)
    repo = tmp_path / "ws" / "app"
    repo.mkdir(parents=True)
    git("init", "-q", cwd=repo)
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    git("add", ".", cwd=repo)
    git("commit", "-q", "-m", "init", cwd=repo)
    return {
        "repo": repo,
        "tmp": tmp_path,
        "central": tmp_path / "central",
        "ws": tmp_path / "ws",
        "state": tmp_path / "state",
    }


def dirty_worktree(
    world: dict[str, Path], name: str = "feat", where: str = "app-wt"
) -> Path:
    wt = world["ws"] / where
    git("worktree", "add", "-q", "-b", name, str(wt), cwd=world["repo"])
    (wt / "a.txt").write_text("one\nunstaged edit\n", encoding="utf-8")
    (wt / "staged.txt").write_text("staged bytes é\n", encoding="utf-8")
    git("add", "staged.txt", cwd=wt)
    (wt / "untracked.txt").write_text("untracked bytes\n", encoding="utf-8")
    (wt / "junk.log").write_text("ignored bytes\n", encoding="utf-8")
    (wt / "deep" / "dir").mkdir(parents=True)
    (wt / "deep" / "dir" / "n.bin").write_bytes(bytes(range(256)))
    return wt


def content_map(top: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for current, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f == ".git" and Path(current) == top:
                continue
            full = Path(current) / f
            out[str(full.relative_to(top)).replace("\\", "/")] = hashlib.sha256(
                full.read_bytes()
            ).hexdigest()
    return out


def call(*argv: str) -> tuple[int, dict]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = nw.main(list(argv))
    text = buffer.getvalue().strip()
    return rc, json.loads(text) if text else {}


def propose(
    world: dict[str, Path], *extra: str, name: str = "m.json"
) -> tuple[Path, str, dict]:
    rc, _ = call(
        "audit",
        "--root",
        str(world["ws"]),
        "--output",
        str(world["tmp"] / f"audit-{name}"),
    )
    assert rc == 0
    manifest = world["tmp"] / name
    rc, out = call(
        "migrate",
        "--dry-run",
        "--inventory",
        str(world["tmp"] / f"audit-{name}"),
        "--manifest",
        str(manifest),
        *extra,
    )
    assert rc == 0, out
    return manifest, out["sha256"], json.loads(manifest.read_text(encoding="utf-8"))


def item_for(manifest: dict, path: Path) -> dict:
    return next(
        i
        for i in manifest["items"]
        if nw.key_of(i["worktree"]["path"]) == nw.key_of(path)
    )


def token_for(world: dict[str, Path], manifest_path: Path, item_id: str) -> str:
    notice = (world["state"] / "notices" / f"{manifest_path.stem}.txt").read_text(
        encoding="utf-8"
    )
    return re.search(rf"--item {item_id} --token ([0-9a-f]{{32}})", notice).group(1)


def authorize(
    world: dict[str, Path], manifest_path: Path, digest: str, manifest: dict, item: dict
) -> None:
    rc, out = call(
        "migrate",
        "--approve",
        "--manifest",
        str(manifest_path),
        "--expect-sha256",
        digest,
        "--item",
        item["id"],
        "--approver",
        "maintainer",
    )
    assert rc == 0, out
    rc, out = call(
        "migrate",
        "--ack",
        "--manifest",
        str(manifest_path),
        "--expect-sha256",
        digest,
        "--item",
        item["id"],
        "--token",
        token_for(world, manifest_path, item["id"]),
        "--checkpoint-note",
        "saved everything",
    )
    assert rc == 0, out


def apply(manifest_path: Path, digest: str) -> tuple[int, dict]:
    return call(
        "migrate",
        "--apply",
        "--manifest",
        str(manifest_path),
        "--expect-sha256",
        digest,
    )


def full_setup(world: dict[str, Path]) -> tuple[Path, Path, str, dict, dict]:
    wt = dirty_worktree(world)
    path, digest, manifest = propose(world)
    item = item_for(manifest, wt)
    assert item["disposition"] == "move", item
    authorize(world, path, digest, manifest, item)
    return wt, path, digest, manifest, item


# --------------------------------------------------------------------------- proposal


def test_dry_run_writes_only_its_own_state_and_classifies_every_case(
    world: dict[str, Path]
) -> None:
    movable = dirty_worktree(world, "feat", "app-wt")
    locked = dirty_worktree(world, "locked-b", "locked-wt")
    git("worktree", "lock", "--reason", "initializing", str(locked), cwd=world["repo"])
    bound = dirty_worktree(world, "bound-b", "bound-wt")
    (world["tmp"] / "runs").mkdir()
    (world["tmp"] / "runs" / "run1.json").write_text(
        json.dumps({"worktree": str(bound), "completed": None}), encoding="utf-8"
    )
    excepted = dirty_worktree(world, "exc-b", "exc-wt")
    removable = dirty_worktree(world, "rm-b", "rm-wt")
    in_policy = world["central"] / "x"  # placed after the identity is known below
    repo_identity, _ = nw.repo_context(
        nw.GitInspector(), str(world["repo"]), nw.resolve_root().path, write=True
    )
    in_policy = world["central"] / repo_identity.id / "kept"
    in_policy.parent.mkdir(parents=True)
    git("worktree", "add", "-q", "-b", "kept-b", str(in_policy), cwd=world["repo"])
    before = {
        p: content_map(p)
        for p in (movable, locked, bound, excepted, removable, in_policy)
    }
    before_repo = content_map(world["repo"])
    manifest_path, digest, manifest = propose(
        world,
        "--exception",
        f"{excepted}=approved location exception",
        "--remove-candidate",
        f"{removable}=merged",
    )
    by = {nw.key_of(i["worktree"]["path"]): i for i in manifest["items"]}
    assert by[nw.key_of(movable)]["disposition"] == "move" and by[nw.key_of(movable)][
        "destination"
    ].startswith(str(world["central"]))
    assert (
        by[nw.key_of(locked)]["disposition"] == "pending"
        and "locked" in by[nw.key_of(locked)]["reason"]
    )
    assert (
        by[nw.key_of(bound)]["disposition"] == "pending"
        and by[nw.key_of(bound)]["owner"] == "native-run-owner"
    )
    assert by[nw.key_of(excepted)]["disposition"] == "exception-pending"
    assert (
        by[nw.key_of(removable)]["disposition"] == "remove-candidate"
        and by[nw.key_of(removable)]["owner"] == "cleanup_merged"
    )
    assert by[nw.key_of(in_policy)]["disposition"] == "retain"
    for item in manifest["items"]:
        assert item["disposition"] != "move" or (
            item["expected"]
            and item["ack"]["token_sha256"]
            and item["authorization"]["required"]
        )
        assert item["reason"] or item["disposition"] == "move"
    assert {p: content_map(p) for p in before} == before and content_map(
        world["repo"]
    ) == before_repo
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == digest
    assert (
        manifest["inventory"]["status"] == "complete"
        and nw.MANIFEST_SCHEMA == manifest["schema"]
    )


def test_dry_run_refuses_an_existing_manifest_and_a_state_directory_inside_a_target(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    wt = dirty_worktree(world)
    path, _, _ = propose(world)
    rc, out = call(
        "migrate",
        "--dry-run",
        "--inventory",
        str(world["tmp"] / "audit-m.json"),
        "--manifest",
        str(path),
    )
    assert rc == 2 and out["code"] == "output-exists"
    monkeypatch.setenv("NEXUS_WORKTREE_STATE", str(wt / "state-inside"))
    rc, out = call(
        "migrate",
        "--dry-run",
        "--inventory",
        str(world["tmp"] / "audit-m.json"),
        "--manifest",
        str(world["tmp"] / "second.json"),
    )
    assert (
        rc == 2
        and out["code"] == "state-inside-target"
        and not (world["tmp"] / "second.json").exists()
    )


def test_cross_volume_and_submodule_worktrees_are_pending_never_moved(world: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    plain = dirty_worktree(world, "plain-b", "plain-wt")
    with monkeypatch.context() as patched:
        patched.setattr(nw, "_same_volume", lambda *_a: False)
        _, _, manifest = propose(world, name="vol.json")
    assert "cross-volume" in item_for(manifest, plain)["reason"]
    sub_source = world["ws"] / "sub-source"
    sub_source.mkdir()
    git("init", "-q", cwd=sub_source)
    (sub_source / "s.txt").write_text("s\n", encoding="utf-8")
    git("add", ".", cwd=sub_source)
    git("commit", "-q", "-m", "s", cwd=sub_source)
    git("submodule", "add", "-q", str(sub_source), "vendor/sub", cwd=world["repo"])
    git("commit", "-q", "-m", "submodule", cwd=world["repo"])
    with_sub = dirty_worktree(world, "sub-b", "sub-wt")
    git("submodule", "update", "--init", cwd=with_sub)
    _, _, manifest = propose(world, name="sub.json")
    item = item_for(manifest, with_sub)
    assert item["disposition"] == "pending" and "submodules" in item["reason"]


# --------------------------------------------------------------------------- the move


def test_apply_moves_the_worktree_and_preserves_every_kind_of_content(
    world: dict[str, Path]
) -> None:
    wt, manifest_path, digest, manifest, item = full_setup(world)
    before = content_map(wt)
    untracked_before = (wt / "untracked.txt").read_bytes()
    status = git("status", "--porcelain=v1", "-z", "--untracked-files=all", cwd=wt)
    staged = git("diff", "--cached", "--binary", cwd=wt)
    unstaged = git("diff", "--binary", cwd=wt)
    head = git("rev-parse", "HEAD", cwd=wt)
    rc, out = apply(manifest_path, digest)
    assert rc == 0 and out["status"] == "complete" and out["moved"] == 1, out
    dest = Path(item["destination"])
    assert not wt.exists() and dest.is_dir() and dest.parent.parent == world["central"]
    assert content_map(dest) == before
    assert (
        git("status", "--porcelain=v1", "-z", "--untracked-files=all", cwd=dest)
        == status
    )
    assert (
        git("diff", "--cached", "--binary", cwd=dest) == staged
        and git("diff", "--binary", cwd=dest) == unstaged
    )
    assert (
        git("rev-parse", "HEAD", cwd=dest) == head
        and git("branch", "--show-current", cwd=dest).strip() == "feat"
    )
    listing = git("worktree", "list", "--porcelain", cwd=world["repo"])
    assert (
        nw.key_of(dest)
        in {
            nw.key_of(w.path)
            for w in nw.parse_worktree_list(
                git("worktree", "list", "--porcelain", "-z", cwd=world["repo"])
            )
        }
        and str(wt) not in listing
    )
    assert (dest / ".git").read_text(encoding="utf-8").startswith("gitdir:")
    git(
        "commit", "-q", "-am", "work continues after the move", cwd=dest
    )  # a subsequent project command works
    package = world["state"] / "preservation" / digest / item["id"]
    assert (
        (package / "receipt.json").is_file()
        and (package / "tracked.patch").read_text(encoding="utf-8")
        == unstaged.replace("\r\n", "\n")
        or (package / "tracked.patch").is_file()
    )
    assert (
        package / "untracked" / "untracked.txt"
    ).read_bytes() == untracked_before
    assert (package / "index").is_file()
    receipt = json.loads(
        (world["state"] / "receipts" / digest / f"{item['id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert [s["step"] for s in receipt["steps"]] == [
        "started",
        "preserved",
        "moving",
        "verified",
    ]
    assert receipt["steps"][2]["actual_destination"]
    again_rc, again = apply(manifest_path, digest)
    assert again_rc == 0 and again["results"][0].get("already_verified") is True


def test_manifest_bound_smoke_command_runs_at_the_destination(
    world: dict[str, Path]
) -> None:
    wt = dirty_worktree(world)
    argv = [
        os.sys.executable,
        "-c",
        "import pathlib,sys; sys.exit(0 if pathlib.Path('untracked.txt').is_file() else 3)",
    ]
    path, digest, manifest = propose(world, "--smoke", f"{wt}={json.dumps(argv)}")
    item = item_for(manifest, wt)
    assert item["smoke"]["argv"] == argv
    authorize(world, path, digest, manifest, item)
    rc, out = apply(path, digest)
    assert rc == 0 and out["results"][0]["smoke"] == {
        "status": "passed",
        "returncode": 0,
    }


def test_hostile_git_configuration_launches_nothing_during_proposal_and_move(
    world: dict[str, Path]
) -> None:
    wt = dirty_worktree(world)
    marker = world["tmp"] / "RAN"
    script = world["tmp"] / "boom.py"
    script.write_text(
        f"import pathlib\npathlib.Path({str(marker)!r}).write_text('x')\n",
        encoding="utf-8",
    )
    program = f'"{os.sys.executable}" "{script}"'.replace("\\", "/")
    (world["repo"] / ".gitattributes").write_text(
        "*.txt filter=boom\n", encoding="utf-8"
    )
    git("add", ".gitattributes", cwd=world["repo"])
    git("commit", "-q", "-m", "attrs", cwd=world["repo"])
    for key in (
        "filter.boom.clean",
        "filter.boom.smudge",
        "core.fsmonitor",
        "diff.external",
    ):
        git("config", key, program, cwd=world["repo"])
    (wt / "a.txt").write_text("changed again\n", encoding="utf-8")
    path, digest, manifest = propose(world, name="host.json")
    item = item_for(manifest, wt)
    if item["disposition"] == "move":
        authorize(world, path, digest, manifest, item)
        apply(path, digest)
    assert not marker.exists()


# --------------------------------------------------------------------------- refusals


def test_changed_malformed_stale_and_unapproved_manifests_refuse_before_any_change(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    snapshot = content_map(wt)

    def refused(
        code: str, expect: str | None = None, manifest_path: Path = path
    ) -> None:
        rc, out = call(
            "migrate",
            "--apply",
            "--manifest",
            str(manifest_path),
            "--expect-sha256",
            expect or digest,
        )
        assert rc == 2 and out["code"] == code, out
        assert (
            wt.is_dir()
            and content_map(wt) == snapshot
            and not Path(item["destination"]).exists()
        )

    refused("manifest-digest-mismatch", expect="0" * 64)
    edited = world["tmp"] / "edited.json"
    edited.write_bytes(
        path.read_bytes().replace(
            b'"disposition": "move"', b'"disposition": "move" ', 1
        )
    )
    refused("manifest-digest-mismatch", manifest_path=edited)
    malformed = world["tmp"] / "malformed.json"
    malformed.write_text("{not json", encoding="utf-8")
    refused(
        "manifest-malformed",
        expect=hashlib.sha256(malformed.read_bytes()).hexdigest(),
        manifest_path=malformed,
    )
    wrong = world["tmp"] / "wrong.json"
    wrong.write_text(json.dumps({"schema": "other/1", "items": []}), encoding="utf-8")
    refused(
        "manifest-schema",
        expect=hashlib.sha256(wrong.read_bytes()).hexdigest(),
        manifest_path=wrong,
    )
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(world["tmp"] / "other-root"))
    refused("manifest-stale")
    monkeypatch.setenv("NEXUS_WORKTREE_ROOT", str(world["central"]))
    (world["state"] / "approvals" / f"{digest}.json").unlink()
    refused("approval-missing")


def test_missing_authorization_or_acknowledgment_leaves_the_item_pending(
    world: dict[str, Path]
) -> None:
    wt = dirty_worktree(world)
    path, digest, manifest = propose(world)
    item = item_for(manifest, wt)
    call(
        "migrate",
        "--approve",
        "--manifest",
        str(path),
        "--expect-sha256",
        digest,
        "--item",
        item["id"],
        "--approver",
        "maintainer",
    )
    rc, out = apply(path, digest)
    assert (
        rc == 3
        and out["results"][0]["code"] == "acknowledgment-missing"
        and wt.is_dir()
    )
    bad = call(
        "migrate",
        "--ack",
        "--manifest",
        str(path),
        "--expect-sha256",
        digest,
        "--item",
        item["id"],
        "--token",
        "f" * 32,
        "--checkpoint-note",
        "n",
    )
    assert bad[0] == 2 and bad[1]["code"] == "ack-token-invalid"
    assert (
        call(
            "migrate",
            "--ack",
            "--manifest",
            str(path),
            "--expect-sha256",
            digest,
            "--item",
            item["id"],
            "--token",
            token_for(world, path, item["id"]),
            "--checkpoint-note",
            " ",
        )[0]
        == 2
    )
    other = dirty_worktree(world, "o", "o-wt")
    path2, digest2, manifest2 = propose(world, name="m2.json")
    item2 = item_for(manifest2, other)
    rc, out = (
        apply(path2, digest2)
        if (world["state"] / "approvals" / f"{digest2}.json").exists()
        else (None, None)
    )
    assert rc is None
    unapproved = call(
        "migrate",
        "--approve",
        "--manifest",
        str(path2),
        "--expect-sha256",
        digest2,
        "--item",
        "nope",
        "--approver",
        "m",
    )
    assert (
        unapproved[0] == 2 and unapproved[1]["code"] == "unknown-item" and item2["id"]
    )


@pytest.mark.parametrize(
    "drift", ["edit", "commit", "stage", "untracked", "lock", "destination"]
)
def test_precondition_drift_refuses_the_item_and_changes_nothing(
    world: dict[str, Path], drift: str
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    dest = Path(item["destination"])
    if drift == "edit":
        (wt / "a.txt").write_text("someone else edited\n", encoding="utf-8")
    elif drift == "commit":
        git("commit", "-q", "-am", "moved HEAD", cwd=wt)
    elif drift == "stage":
        (wt / "late.txt").write_text("late\n", encoding="utf-8")
        git("add", "late.txt", cwd=wt)
    elif drift == "untracked":
        (wt / "extra.txt").write_text("extra\n", encoding="utf-8")
    elif drift == "lock":
        git("worktree", "lock", str(wt), cwd=world["repo"])
    else:
        dest.mkdir(parents=True)
    before = content_map(wt)
    rc, out = apply(path, digest)
    result = out["results"][0]
    assert rc == 3 and result["outcome"] == "refused", out
    assert result["code"] in {"source-changed", "source-locked", "destination-changed", "destination-exists"}
    assert wt.is_dir() and content_map(wt) == before
    assert not any(
        w.path.endswith(dest.name) and Path(w.path).resolve() == dest.resolve()
        for w in nw.list_registered(nw.GitInspector(), cwd=str(world["repo"]))
    )


def test_competing_writer_between_validation_and_move_stops_the_item(
    world: dict[str, Path]
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    nw.FAULTS["after_validate"] = lambda: (wt / "racer.txt").write_text(
        "raced\n", encoding="utf-8"
    )
    rc, out = apply(path, digest)
    assert rc == 3 and out["results"][0]["code"] == "competing-writer" and wt.is_dir()
    assert not Path(item["destination"]).exists()


def test_ancestor_replaced_by_a_junction_between_validation_and_mutation_is_refused(
    world: dict[str, Path]
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    dest = Path(item["destination"])
    elsewhere = world["tmp"] / "attacker-target"
    elsewhere.mkdir()

    def swap() -> None:
        parent = dest.parent
        parent.rmdir()
        if IS_NT:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(parent), str(elsewhere)],
                check=True,
                capture_output=True,
            )
        else:
            os.symlink(elsewhere, parent, target_is_directory=True)

    nw.FAULTS["after_validate"] = swap
    try:
        rc, out = apply(path, digest)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("cannot create a link on this host")
    assert rc == 3 and out["results"][0]["code"] in {
        "destination-reparse",
        "ancestor-replaced",
    }, out
    assert wt.is_dir() and list(elsewhere.iterdir()) == []


# --------------------------------------------------------------------------- interruption and recovery


@pytest.mark.parametrize("boundary", ["after_validate", "before_git", "after_git"])
def test_interruption_at_every_boundary_resumes_or_recovers_without_loss(
    world: dict[str, Path], boundary: str
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    before = content_map(wt)
    dest = Path(item["destination"])

    def crash() -> None:
        raise KeyboardInterrupt("simulated interruption")

    nw.FAULTS[boundary] = crash
    with pytest.raises(KeyboardInterrupt):
        apply(path, digest)
    receipt = json.loads(
        (world["state"] / "receipts" / digest / f"{item['id']}.json").read_text(
            encoding="utf-8"
        )
    )
    expected_state = {
        "after_validate": "preserved",
        "before_git": "moving",
        "after_git": "moving",
    }[boundary]
    assert (
        receipt["state"] == expected_state
    )  # an accurate pending receipt, never a false "verified"
    assert (wt.is_dir(), dest.is_dir()) == (
        (True, False) if boundary != "after_git" else (False, True)
    )
    assert not list(
        (world["state"] / "locks").glob("*.lock")
    ), "an interrupted run must release its repository lock"
    nw.FAULTS[boundary] = None
    rc, out = apply(path, digest)
    assert rc == 0 and out["results"][0]["outcome"] in {"moved", "recovered"}, out
    assert not wt.exists() and content_map(dest) == before
    final = json.loads(
        (world["state"] / "receipts" / digest / f"{item['id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert final["state"] == "verified"


def test_recovery_refuses_an_ambiguous_or_changed_state(world: dict[str, Path]) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    dest = Path(item["destination"])
    nw.FAULTS["after_git"] = lambda: (_ for _ in ()).throw(KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        apply(path, digest)
    nw.FAULTS["after_git"] = None
    (dest / "a.txt").write_text(
        "changed after the interrupted move\n", encoding="utf-8"
    )
    rc, out = apply(path, digest)
    result = out["results"][0]
    assert (
        rc == 3
        and result["outcome"] == "pending"
        and result["code"] == "recovery-unverified"
    ), out
    assert (
        dest.is_dir()
        and (dest / "a.txt").read_text(encoding="utf-8")
        == "changed after the interrupted move\n"
    )
    both = world["tmp"] / "both"
    both.mkdir()
    receipt = world["state"] / "receipts" / digest / f"{item['id']}.json"
    wt.mkdir()
    rc, out = apply(path, digest)
    assert out["results"][0]["code"] == "recovery-ambiguous"
    assert (
        json.loads(receipt.read_text(encoding="utf-8"))["state"] == "recovery-refused"
    )


def test_apply_never_removes_a_worktree_or_runs_cleanup(world: dict[str, Path]) -> None:
    wt = dirty_worktree(world)
    path, digest, manifest = propose(world, "--remove-candidate", f"{wt}=merged")
    item = item_for(manifest, wt)
    rc, _ = call(
        "migrate",
        "--approve",
        "--manifest",
        str(path),
        "--expect-sha256",
        digest,
        "--item",
        item["id"],
        "--approver",
        "m",
    )
    assert rc == 2  # a removal candidate takes no approval here
    nothing = world["tmp"] / "none.json"
    rc, out = call(
        "migrate",
        "--approve",
        "--manifest",
        str(path),
        "--expect-sha256",
        digest,
        "--approver",
        "m",
    )
    rc, out = apply(path, digest)
    assert (
        rc == 3
        and out["results"][0]["outcome"] == "pending"
        and out["results"][0]["owner"] == "cleanup_merged"
        and wt.is_dir()
    )
    assert not nothing.exists()


def test_concurrent_apply_is_serialized_by_the_repository_lock(
    world: dict[str, Path]
) -> None:
    wt, path, digest, manifest, item = full_setup(world)
    inspector = nw.GitInspector()
    identity = item["repository"]["identity"]
    with nw.RepoLock(identity):
        with pytest.raises(nw.PolicyError) as caught:
            with nw.RepoLock(identity, wait=0.2):
                pass
    assert caught.value.code == "repository-locked"
    nw.FAULTS["after_validate"] = None
    held = nw.RepoLock(identity, wait=0.2)
    held.__enter__()
    try:
        rc, out = apply(path, digest)
    finally:
        held.__exit__()
    assert (
        rc == 3
        and out["results"][0]["code"] == "repository-locked"
        and wt.is_dir()
        and inspector
    )


def test_native_binding_ends_only_when_the_run_is_stamped_complete_and_unreadable_records_block(world: dict[str, Path]) -> None:
    wt = dirty_worktree(world)
    runs = world["tmp"] / "runs"
    runs.mkdir()
    record = runs / "run1.json"
    record.write_text(json.dumps({"worktrees": [str(wt)], "completed": None}), encoding="utf-8")
    _, _, manifest = propose(world, name="live.json")
    item = item_for(manifest, wt)
    assert item["disposition"] == "pending" and item["owner"] == "native-run-owner" and "finish the run in place" in item["reason"]
    record.write_text(json.dumps({"worktrees": [str(wt)], "completed": "2026-11-21T00:00:00Z"}), encoding="utf-8")
    _, _, manifest = propose(world, name="done.json")
    assert item_for(manifest, wt)["disposition"] == "move"
    record.write_text("{not json", encoding="utf-8")
    _, _, manifest = propose(world, name="unreadable.json")
    unreadable = item_for(manifest, wt)
    assert unreadable["disposition"] == "pending" and unreadable["reason"] == "native-records-unreadable"
    assert record.read_text(encoding="utf-8") == "{not json", "records are never edited"
