"""Archive each released member of a minor-scope run (completion contract, "Member archive").

Covers `minor_close.py archive-member` and the checker rules it relies on:

- the ownership rule (`cm.member_moves`): the exact `<version>-` prefix boundary, the
  frozen plan, receipts, history, research, and analysis move, and every shared file stays;
- dry run and apply: per-prefix link and mention repair (a shared known-gaps mention is
  left as it is), one commit, the signed `archived` identity, and an idempotent re-run;
- every refusal id, the rollback on a failed link check, and the record restored when
  the commit fails after the identity was signed;
- `archive.member` (n/a, unmet, met), `gaps.version` (the fail-open regression) and
  `evidence.file` for an archived member, the member-start gate, and a mixed-state verdict.

Every repository is a throwaway with a local bare remote and the committed `gh` stand-in,
built by the shared Walk fixture with an isolated runs directory; no case touches the
network or the real home.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .test_check_plan_completion import (  # noqa: F401  (autouse fixture re-exported)
    _git,
    _isolated_git_config,
)
from .test_completion_minor_record import (  # noqa: F401  (autouse fixture re-exported)
    SESSION,
    _no_transport_overrides,
)
from .test_completion_minor_verdict import Walk, _first
from .test_gap_migration_and_archive import (
    GAPS05,
    LINK_CHECKER,
    V05,
    WN3,
    ledger,
    section,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_plan_completion as ck
import completion_minor as cm
import minor_close as mc

ARCHIVE = "docs/archives/v0/v0.5"
ALPHA = f"{V05}/plans/v0.5.2-alpha.md"
OMEGA = f"{V05}/plans/v0.5.10-omega.md"
EVIDENCE = f"{V05}/development/v0.5.2-last-phase-evidence.md"
ALPHA_TEXT = (
    "# Plan -- alpha\n\n**Version**: v0.5.2\n**Slug**: alpha\n**Status**: queued\n\n"
    f"Receipts go to {EVIDENCE}; open gaps stay in {GAPS05}.\n\n"
    "See [the survey](../research/v0.5.2-survey.md) and [the comparison](../comparisons/shared.md).\n\n"
    "## Phase 1: Build\n\n- [ ] T001 Build part src/alpha.txt\n"
)
OWNED = {
    f"{V05}/development/v0.5.2-notes/detail.md": "# Detail\n",
    f"{V05}/development/history/v0.5.2-session.md": "# Session\n",
    f"{V05}/research/v0.5.2-survey.md": "# Survey\n",
    f"{V05}/analysis/v0.5.2-data.md": "# Data\n",
}
SHARED = {
    f"{V05}/development/v0.5.10-scratch.md": "# Omega scratch\n",
    f"{V05}/development/shared-notes.md": "# Shared\n",
    f"{V05}/comparisons/shared.md": "# Comparison\n",
    f"{V05}/comparisons/v0.5.2-against-x.md": "# Kept with the comparisons\n",
    f"{V05}/handbooks/v0.5.2-guide.md": "# Kept with the handbooks\n",
    f"{V05}/v0.5-minor-close-evidence.md": "# Close evidence\n",
}


def moved(rel: str) -> str:
    return ARCHIVE + rel[len(V05):]


class Members(Walk):
    """The Walk fixture with every kind of member-owned and shared record under v0.5."""

    def setup(self, *, archive_member: bool = True, omega: str | None = None, release: bool = True,
              items: str = WN3, wn_open: int = 1, tasks: str = "", during: dict[str, str] | None = None, todos: str = "") -> None:
        self.write(ALPHA, ALPHA_TEXT + tasks)
        if omega is not None:
            self.write(OMEGA, omega)
        for rel, text in {**OWNED, **SHARED}.items():
            self.write(rel, text)
        self.write("docs/todos.md", "# Todos\n\n- [alpha](releases/v0/v0.5/plans/v0.5.2-alpha.md)\n" + todos)
        self.write(GAPS05, ledger("v0.5", section("v0.5.2", wn_open, items), status="finalized"))
        self.commit("member records")
        self.integrate()
        extra = ("cleanup-merged", "minor-close-pr", *(("archive-member",) if archive_member else ()))
        self.forge_minor(extra=extra)
        for rel, text in (during or {}).items():  # work done during the run, landing with the release
            self.write(rel, text)
        if release:
            self.release_member("v0.5.2", "alpha")
            _git(self.work, "checkout", "-q", "-b", "chore/archive-v0.5.2", "origin/develop")

    def archive_member(self, *extra: str, member: str = "v0.5.2", checker: Path = LINK_CHECKER):
        return self.close("archive-member", "--minor", "v0.5", "--member", member, "--session", SESSION,
                          "--link-checker", str(checker), *extra)

    def member(self, version: str = "v0.5.2") -> dict:
        return next(m for m in self.record()["members"] if m["version"] == version)

    def merge_archive(self) -> None:
        _git(self.work, "checkout", "-q", "develop")
        _git(self.work, "merge", "-q", "--ff-only", "chore/archive-v0.5.2")
        self.publish("develop")

    def lines(self, version: str = "v0.5.2") -> dict[str, str]:
        verdict = self.verdict()
        return dict(next(m for m in verdict.members if m.version == version).lines)

    def force_archive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Archive past the `member-incomplete` refusal, to prove the checker rules behind it."""
        monkeypatch.setattr(mc, "_member_incomplete_refusals", lambda *args: [])
        code = mc.main(["archive-member", "--minor", "v0.5", "--member", "v0.5.2", "--session", SESSION,
                        "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(self.work)])
        assert code == mc.EXIT_OK

    def back_merge_main(self) -> None:
        """Bring main up to develop, as a release's back-merge leaves them, then return to develop."""
        _git(self.work, "checkout", "-q", "main")
        _git(self.work, "merge", "-q", "--ff-only", "develop")
        self.publish("main")


@pytest.fixture()
def members(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, minor_git_seed: Path) -> Members:
    return Members(tmp_path, monkeypatch, minor_git_seed)


SURVEY = f"{V05}/research/v0.5.2-survey.md"
UNTOUCHED = f"- [x] T002 Refresh the survey {SURVEY}\n"  # checked, but its file predates the run
WORKED = f"- [x] T003 Record the receipt {EVIDENCE}\n"  # the release commit writes this file


# --------------------------------------------------------------------------- ownership


def test_member_moves_follow_the_exact_prefix_and_leave_shared_files() -> None:
    tracked = [
        ALPHA, OMEGA, EVIDENCE, GAPS05,
        f"{V05}/development/v0.5.20-other.md", f"{V05}/development/v0.5.10-other.md",
        f"{V05}/development/v0.5.2-notes/a.md", f"{V05}/development/v0.5.2-notes/b/c.md",
        f"{V05}/development/history/v0.5.2-s.md", f"{V05}/development/history/v0.5.1-s.md",
        f"{V05}/research/v0.5.2-r.md", f"{V05}/analysis/v0.5.2-a.md",
        f"{V05}/comparisons/v0.5.2-c.md", f"{V05}/handbooks/v0.5.2-h.md",
        f"{V05}/v0.5-minor-close-evidence.md", f"{V05}/docs-cleanup-report.md",
        f"{V05}/development/v0.5.2.md", f"{V05}/development/last-phase-evidence.md",
    ]
    olds = [ALPHA, EVIDENCE, f"{V05}/development/v0.5.2-notes", f"{V05}/development/history/v0.5.2-s.md",
            f"{V05}/research/v0.5.2-r.md", f"{V05}/analysis/v0.5.2-a.md"]
    assert cm.member_moves("v0.5.2", V05, tracked, ALPHA) == [(old, moved(old)) for old in sorted(olds)]
    # v0.5.1- is a different member from v0.5.10- and v0.5.2-.
    assert cm.member_moves("v0.5.1", V05, tracked) == [
        (f"{V05}/development/history/v0.5.1-s.md", moved(f"{V05}/development/history/v0.5.1-s.md"))]
    assert cm.member_moves("v0.5.3", V05, tracked) == []


# --------------------------------------------------------------------------- dry run and apply


def test_dry_run_lists_every_move_and_changes_nothing(members: Members) -> None:
    members.setup()
    head = members.head()
    result = members.archive_member()
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert f"WOULD MOVE {ALPHA} -> {moved(ALPHA)}" in lines
    assert f"WOULD MOVE {V05}/development/v0.5.2-notes -> {ARCHIVE}/development/v0.5.2-notes" in lines
    assert lines[-1].startswith(f"WOULD ARCHIVE MEMBER v0.5.2 {V05} -> {ARCHIVE} prefixes=6 ")
    assert members.head() == head and _git(members.work, "status", "--porcelain").strip() == ""
    assert "archived" not in members.member()


def test_apply_moves_the_owned_records_repairs_references_and_signs_the_identity(members: Members) -> None:
    members.setup()
    gaps_before = members.read(GAPS05)
    frozen = members.member()["plan_sha256"]
    result = members.archive_member("--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    last = result.stdout.splitlines()[-1]
    assert last.startswith(f"ARCHIVED MEMBER v0.5.2 {V05} -> {ARCHIVE} commit=") and last.endswith("newly_broken=0")
    for rel in (ALPHA, EVIDENCE, *OWNED):
        assert not (members.work / rel).exists() and (members.work / moved(rel)).is_file(), rel
    for rel in (OMEGA, GAPS05, *SHARED):
        assert (members.work / rel).is_file(), rel
    assert not (members.work / f"{V05}/research").exists() and not (members.work / f"{V05}/analysis").exists()
    plan = members.read(moved(ALPHA))
    # Per-prefix mention repair: the moved receipt is re-pointed, the shared ledger is not.
    assert f"Receipts go to {moved(EVIDENCE)}; open gaps stay in {GAPS05}." in plan
    assert "[the survey](../research/v0.5.2-survey.md)" in plan  # both ends moved together
    assert "[the comparison](../../../../releases/v0/v0.5/comparisons/shared.md)" in plan
    assert members.read("docs/todos.md") == "# Todos\n\n- [alpha](archives/v0/v0.5/plans/v0.5.2-alpha.md)\n"
    # The shared ledger stays; only its link to the moved plan is re-pointed.
    assert members.read(GAPS05) == gaps_before.replace(
        "[plan](plans/v0.5.2-alpha.md)", "[plan](../../../archives/v0/v0.5/plans/v0.5.2-alpha.md)")
    assert _git(members.work, "log", "-1", "--format=%s").strip() == "docs(archives): archive released member v0.5.2 of v0.5"
    assert _git(members.work, "status", "--porcelain").strip() == ""
    member = members.member()
    archived = member["archived"]
    assert (member["plan_path"], member["plan_sha256"]) == (ALPHA, frozen)  # the frozen identity is kept
    assert archived["plan_path"] == moved(ALPHA) and archived["plan_sha256"] == ck.plan_hash_text(plan)
    assert (archived["from"], archived["original_sha256"]) == (ALPHA, frozen) and archived["at"]
    pairs = [entry[:2] for entry in archived["moved"]]
    assert [EVIDENCE, moved(EVIDENCE)] in pairs and ["docs/todos.md", "docs/todos.md"] in pairs
    assert all(len(entry) == 3 and len(entry[2]) == 40 for entry in archived["moved"])  # signed new-side blob ids
    state = members.load()
    assert state.forced is None and state.record is not None


def test_a_rerun_after_apply_is_idempotent(members: Members) -> None:
    members.setup()
    assert members.archive_member("--apply").returncode == 0
    head = members.head()
    again = members.archive_member("--apply")
    assert again.returncode == 0, again.stdout + again.stderr
    assert again.stdout.strip() == f"ALREADY ARCHIVED MEMBER v0.5.2 {moved(ALPHA)}"
    assert members.head() == head


# --------------------------------------------------------------------------- refusals


OMEGA_LINKS_ALPHA = (
    "# Plan -- omega\n\n**Version**: v0.5.10\n**Slug**: omega\n**Status**: queued\n\n"
    "Builds on [alpha's receipt](../development/v0.5.2-last-phase-evidence.md).\n\n"
    "## Phase 1: Build\n\n- [ ] T001 Build part src/omega.txt\n"
)


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("no-class", "REFUSED: approval-not-covered (the minor record does not carry archive-member)"),
        ("last-member", "REFUSED: use-minor-close (v0.5.10)"),
        ("not-a-member", "REFUSED: not-a-member (v0.5.7)"),
        ("unreleased", "REFUSED: member-not-released (v0.5.2:integration.merged)"),
        ("branch", "REFUSED: not-on-archive-branch (chore/archive-v0.5.10)"),
        ("dirty", "REFUSED: dirty-worktree (commit or stash first; rollback needs a clean tree)"),
        ("collision", f"REFUSED: archive-collision ({ARCHIVE}/research/v0.5.2-survey.md)"),
        ("cross-reference", f"REFUSED: member-plan-cross-reference ({OMEGA})"),
        ("attributes", f"REFUSED: attributes-differ ({V05}/analysis/v0.5.2-data.md)"),
        ("member-worktree", "REFUSED: member-worktree-dirty (v0.5.2)"),
    ],
)
def test_every_refusal_leaves_the_tree_and_record_unchanged(
    members: Members, tmp_path: Path, setup: str, expected: str,
) -> None:
    member = "v0.5.2"
    members.setup(archive_member=setup != "no-class", omega=OMEGA_LINKS_ALPHA if setup == "cross-reference" else None,
                  release=setup != "unreleased")
    if setup == "unreleased":
        _git(members.work, "checkout", "-q", "-b", "chore/archive-v0.5.2")
    elif setup == "last-member":
        member = "v0.5.10"
    elif setup == "not-a-member":
        member = "v0.5.7"
    elif setup == "branch":
        _git(members.work, "checkout", "-q", "-b", "chore/archive-v0.5.10")
    elif setup == "dirty":
        members.write("scratch.txt", "uncommitted\n")
    elif setup == "collision":
        members.write(f"{ARCHIVE}/research/v0.5.2-survey.md", "older\n")
        members.commit("collide")
    elif setup == "attributes":
        members.write(".gitattributes", "docs/archives/** -text\n")
        members.commit("archive attributes")
    elif setup == "member-worktree":
        _git(members.work, "worktree", "add", "-q", "-b", "feat/v0.5.2-alpha", str(tmp_path / "alpha-wt"), "HEAD")
        (tmp_path / "alpha-wt" / EVIDENCE).write_text("# Edited in the member's worktree\n", encoding="utf-8")
    tree_before = _git(members.work, "ls-files")
    record_before = members.record()
    result = members.archive_member("--apply", member=member)
    assert result.returncode == 3, result.stdout + result.stderr
    assert expected in result.stdout.splitlines(), result.stdout
    assert _git(members.work, "ls-files") == tree_before
    assert members.record() == record_before


def test_a_failed_link_check_rolls_the_member_archive_back(members: Members, tmp_path: Path) -> None:
    members.setup()
    stub = tmp_path / "broken-checker.py"
    stub.write_text(
        "import json, pathlib, sys\n"
        "if sys.argv[1] == 'baseline':\n"
        "    pathlib.Path(sys.argv[sys.argv.index('--out') + 1]).write_text('')\n"
        "else:\n"
        "    print(json.dumps({'totals': {'newly_broken': 1}})); sys.exit(1)\n",
        encoding="utf-8",
    )
    head, tree = members.head(), _git(members.work, "ls-files")
    result = members.archive_member("--apply", checker=stub)
    assert result.returncode == 3 and result.stdout.strip() == "REFUSED: link-check-failed (1 newly broken)"
    assert members.head() == head and _git(members.work, "ls-files") == tree
    assert _git(members.work, "status", "--porcelain").strip() == ""
    assert "archived" not in members.member() and members.load().forced is None


def test_a_failed_commit_restores_the_tree_and_unsigns_the_identity(
    members: Members, monkeypatch: pytest.MonkeyPatch,
) -> None:
    members.setup()
    head, tree = members.head(), _git(members.work, "ls-files")
    real = mc._git

    def failing(rctx: ck.RepoContext, *args: str) -> tuple[int, str]:
        return (1, "") if args[:1] == ("commit",) else real(rctx, *args)

    monkeypatch.setattr(mc, "_git", failing)
    code = mc.main(["archive-member", "--minor", "v0.5", "--member", "v0.5.2", "--session", SESSION,
                    "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(members.work)])
    assert code == mc.EXIT_REFUSED
    assert members.head() == head and _git(members.work, "ls-files") == tree
    assert "archived" not in members.member() and members.load().forced is None


# --------------------------------------------------------------------------- predicates


def test_archive_member_is_n_a_without_the_class_and_adds_no_line(members: Members) -> None:
    members.setup(archive_member=False)
    record = members.load().record
    assert cm.archive_member_status(ck, members.rctx(), record, members.member()) == "n/a"
    assert "archive.member" not in members.lines()


def test_archive_member_is_met_only_once_the_archive_reaches_the_integration_branch(members: Members) -> None:
    members.setup()
    assert members.lines()["archive.member"] == "unmet"
    assert members.archive_member("--apply").returncode == 0
    rctx = members.rctx()
    assert cm.archive_member_status(ck, rctx, members.load().record, members.member()) == "unmet"
    members.merge_archive()
    record = members.load().record
    assert cm.archive_member_status(ck, rctx, record, members.member()) == "met"
    assert cm.archive_member_status(ck, rctx, record, members.member("v0.5.10")) == "unmet"
    # A hand-edited, unsigned archived identity is tampering, never a met predicate.
    edited = members.record()
    edited["members"][0]["archived"]["plan_sha256"] = "0" * 64
    members.write_record(edited, resign=False)
    assert members.load().forced == ck.TAMPERED


def test_a_mixed_state_minor_verifies_and_reads_the_archived_member(members: Members) -> None:
    members.setup()
    assert members.archive_member("--apply").returncode == 0
    members.merge_archive()
    verdict = members.verdict()
    assert verdict.code == ck.EXIT_INCOMPLETE, verdict.line
    alpha = next(m for m in verdict.members if m.version == "v0.5.2")
    lines = dict(alpha.lines)
    assert alpha.status == "met", alpha.lines
    assert lines["evidence.file"] == "met" and lines["archive.member"] == "met"
    assert lines["gaps.version"] == "deferred"  # WN-3 still waits for the minor close
    assert "v0.5.2:archive.member" not in verdict.ids() and "v0.5.10:archive.member" in verdict.ids()


def test_an_archived_member_reads_its_minor_ledger_never_an_empty_archive_folder(
    members: Members, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fail-open regression: the archive folder has no ledger, so reading it read every gap as met."""
    items = WN3 + "#### WN-4: A new defect the run must fix\n\n- **Reason**: found in review\n\n"
    members.setup(items=items, wn_open=2)
    refused = members.archive_member("--apply")
    assert "REFUSED: member-incomplete (v0.5.2:gaps.version)" in refused.stdout.splitlines(), refused.stdout
    members.force_archive(monkeypatch)
    members.merge_archive()
    assert not (members.work / f"{ARCHIVE}/known-gaps.md").exists()
    assert members.lines()["gaps.version"] == "unmet"
    members.write(f"{ARCHIVE}/known-gaps.md", members.read(GAPS05))
    assert members.lines()["gaps.version"] == "cannot-verify"  # two ledgers for one minor


def test_evidence_is_found_in_the_active_tree_for_an_archived_member(members: Members) -> None:
    members.setup()
    assert members.archive_member("--apply").returncode == 0
    evidence = members.read(moved(EVIDENCE))
    (members.work / moved(EVIDENCE)).unlink()
    ctx = ck.Context(str(members.work / moved(ALPHA)), ck.Budget(20))
    view = ck.project(members.load().record, "v0.5.2")
    assert ck._evidence_file(ctx) is None and ck._evidence_file(ctx, view) is None
    members.write(f"{V05}/development/last-phase-evidence.md", evidence + "\nPlan: v0.5.2-alpha.md\n")
    assert ck._evidence_file(ctx, view) == evidence + "\nPlan: v0.5.2-alpha.md\n"
    assert ck._evidence_file(ctx) is None  # a plan in an archive folder without a signed identity reads as before


def test_the_member_start_gate_never_waits_for_the_member_archive(members: Members) -> None:
    members.setup(release=False)
    assert _first(members.member_start("v0.5.2")).startswith("STARTED v0.5.2")
    members.release_member("v0.5.2", "alpha")
    assert members.lines()["archive.member"] == "unmet"
    started = members.member_start("v0.5.10")
    assert _first(started).startswith("STARTED v0.5.10"), started.stdout


# --------------------------------------------------------------------------- review regressions


@pytest.mark.parametrize(
    ("tasks", "expected"),
    [(UNTOUCHED, "REFUSED: member-incomplete (v0.5.2:task.T002)"),
     ("- [ ] T004 Later work src/later.txt\n", "REFUSED: member-incomplete (v0.5.2:unchecked-task)")],
    ids=["unmet-task", "unchecked-task"],
)
def test_an_incomplete_member_is_never_archived(members: Members, tasks: str, expected: str) -> None:
    members.setup(tasks=tasks)
    tree = _git(members.work, "ls-files")
    result = members.archive_member("--apply")
    assert result.returncode == 3 and expected in result.stdout.splitlines(), result.stdout
    assert _git(members.work, "ls-files") == tree and "archived" not in members.member()


def test_the_archive_commit_never_satisfies_a_task(members: Members, monkeypatch: pytest.MonkeyPatch) -> None:
    """The repro: an untouched checked task whose path the archive rewrites and creates stays unmet."""
    members.setup(tasks=UNTOUCHED + WORKED)
    before = members.lines()
    assert (before["task.T002"], before["task.T003"]) == ("unmet", "met")
    members.force_archive(monkeypatch)
    members.merge_archive()
    plan = members.read(moved(ALPHA))
    assert f"T002 Refresh the survey {moved(SURVEY)}" in plan and f"T003 Record the receipt {moved(EVIDENCE)}" in plan
    after = members.lines()
    # T002 only ever changed in the archive commit; T003's real work is found at its original path.
    assert (after["task.T002"], after["task.T003"], after["task.T001"]) == ("unmet", "met", "met")


def test_a_reused_archive_branch_with_another_commit_is_refused(members: Members) -> None:
    members.setup()
    members.write("notes.txt", "unrelated work\n")
    members.commit("unrelated")
    result = members.archive_member("--apply")
    assert result.returncode == 3, result.stdout
    assert f"REFUSED: branch-not-archive-only ({members.head()[:12]})" in result.stdout.splitlines()
    assert "archived" not in members.member()


def test_an_unmerged_branch_editing_a_moved_file_is_refused(members: Members) -> None:
    members.setup()
    _git(members.work, "checkout", "-q", "-b", "feat/v0.5.10-omega", "origin/develop")
    members.write(SURVEY, "# Survey, edited by the next member\n")
    members.commit("omega edits alpha's survey")
    members.publish("feat/v0.5.10-omega")
    _git(members.work, "checkout", "-q", "chore/archive-v0.5.2")
    result = members.archive_member("--apply")
    assert result.returncode == 3, result.stdout
    assert "REFUSED: unmerged-branch-touches-tree (feat/v0.5.10-omega)" in result.stdout.splitlines()


def _audit(members: Members, base: str, *files: tuple[str, str]) -> str:
    """The claim audit of a later member (v0.5.10, claiming src/omega.txt) whose work lands after `base`."""
    for rel, text in files:
        members.write(rel, text)
    members.commit("omega work")
    member = {"version": "v0.5.10", "start_head": base,
              "implementation": {"write_paths": ["src/omega.txt"], "base_head": base}}
    return cm._historical_claim_status(members.rctx(), member, members.head(), members.load().record)


def test_the_claim_audit_leaves_out_only_another_members_verified_archive_commit(members: Members) -> None:
    members.setup()
    base = _git(members.work, "rev-parse", "origin/develop").strip()
    assert members.archive_member("--apply").returncode == 0
    members.merge_archive()
    assert _audit(members, base, ("src/omega.txt", "omega\n")) == "met"


@pytest.mark.parametrize("rel", ["docs/todos.md", GAPS05, moved(SURVEY)], ids=["todos", "known-gaps", "moved-file"])
def test_the_claim_audit_still_covers_a_shared_or_moved_path_another_commit_writes(members: Members, rel: str) -> None:
    members.setup()
    base = _git(members.work, "rev-parse", "origin/develop").strip()
    assert members.archive_member("--apply").returncode == 0
    members.merge_archive()
    text = members.read(rel) + "\nEdited by the later member.\n"
    assert _audit(members, base, ("src/omega.txt", "omega\n"), (rel, text)) == "unmet"


def test_a_signed_identity_whose_commit_never_landed_exempts_nothing(members: Members) -> None:
    """A crash between signing and committing: the signed `moved` set matches no commit."""
    members.setup()
    base = _git(members.work, "rev-parse", "origin/develop").strip()
    record = members.record()
    record["members"][0]["archived"] = {
        "plan_path": moved(ALPHA), "plan_sha256": "0" * 64, "from": ALPHA,
        "original_sha256": record["members"][0]["plan_sha256"], "at": ck._now(),
        "moved": [[ALPHA, moved(ALPHA), "1" * 40], ["docs/todos.md", "docs/todos.md", "2" * 40],
                  [GAPS05, GAPS05, "3" * 40]],
    }
    members.write_record(record, resign=True)
    todos = members.read("docs/todos.md") + "\nEdited by the later member.\n"
    assert _audit(members, base, ("src/omega.txt", "omega\n"), ("docs/todos.md", todos)) == "unmet"


OMEGA_NOTES = f"{V05}/research/v0.5.10-notes.md"
OMEGA_REVIEW = f"{V05}/research/2026-01-05-v0.5.10-review.md"
OMEGA_WITH_NOTES = (
    "# Plan -- omega\n\n**Version**: v0.5.10\n**Slug**: omega\n**Status**: queued\n\n"
    "## Phase 1: Build\n\n- [ ] T001 Build part src/omega.txt\n"
    f"- [x] T002 Re-read the notes {OMEGA_NOTES}\n"
    f"- [x] T003 Write the dated review {V05}/research/YYYY-MM-DD-v0.5.10-review.md\n"
)
NOTES_RUN = f"{V05}/development/v0.5.2-notes/run.md"
FOLDER = f"- [x] T004 Collect the run notes {V05}/development/v0.5.2-notes/\n"  # a folder path, worked
GLOB = "- [x] T005 Add the extension tests extensions/*/tests/*.py\n"  # a glob path, worked


def test_the_final_archive_composes_with_a_member_archived_on_release(members: Members) -> None:
    """The early-archived member stays put, the close moves the rest, neither archive commit is task
    work, and folder, glob, and dated task paths keep their git pathspec meaning throughout."""
    members.write(OMEGA_NOTES, "# Notes\n")
    members.write(OMEGA_REVIEW, "# An old review\n")  # dated, but predates the run
    members.setup(omega=OMEGA_WITH_NOTES, tasks=FOLDER + GLOB,
                  during={NOTES_RUN: "# Run notes\n", "extensions/demo/tests/test_demo.py": "def test_x():\n    pass\n"})
    frozen = {m["version"]: (m["plan_path"], m["plan_sha256"]) for m in members.record()["members"]}
    worked = ("met", "met")
    assert (members.lines()["task.T004"], members.lines()["task.T005"]) == worked  # before the archive
    assert members.archive_member("--apply").returncode == 0
    # The shared evidence has not moved, so the archived plan still names the shared ledger in the active tree.
    assert f"open gaps stay in {GAPS05}." in members.read(moved(ALPHA))
    assert f"T004 Collect the run notes {moved(V05 + '/development/v0.5.2-notes')}/" in members.read(moved(ALPHA))
    members.merge_archive()
    assert (members.lines()["task.T004"], members.lines()["task.T005"]) == worked  # after the member archive
    members.back_merge_main()
    members.release_member("v0.5.10", "omega")
    omega = members.lines("v0.5.10")
    assert (omega["task.T002"], omega["task.T003"]) == ("unmet", "unmet")  # checked, never worked
    _git(members.work, "checkout", "-q", "-b", "chore/close-v0.5", "origin/develop")
    assert members.migrate().returncode == 0
    members.commit("migrate v0.5#WN-3")
    closed = members.close("archive", "--minor", "v0.5", "--apply", "--link-checker", str(LINK_CHECKER))
    assert closed.returncode == 0, closed.stdout + closed.stderr
    assert closed.stdout.strip().endswith("newly_broken=0") and not (members.work / V05).exists()
    # The early-archived plan is mention-eligible at its own minor's close.
    assert f"open gaps stay in {moved(GAPS05)}." in members.read(moved(ALPHA))
    state = members.load()
    assert state.forced is None and state.record is not None
    head = members.head()
    for member in state.record["members"]:
        old_path, old_hash = frozen[member["version"]]
        assert member["plan_path"] == moved(old_path)
        archived = member["archived"]
        assert (archived["from"], archived["original_sha256"], archived["close_commit"]) == (old_path, old_hash, head)
    assert (members.lines()["task.T004"], members.lines()["task.T005"]) == worked  # after the close
    omega = members.lines("v0.5.10")
    # The close commit re-pointed T002 and T003 at the archive and created those paths; that is not task work.
    assert f"{moved(V05)}/research/YYYY-MM-DD-v0.5.10-review.md" in members.read(moved(OMEGA))
    assert (omega["task.T001"], omega["task.T002"], omega["task.T003"]) == ("met", "unmet", "unmet")


OMEGA_X = (
    "# Plan -- omega\n\n**Version**: v0.5.10\n**Slug**: omega\n**Status**: queued\n\n"
    "## Phase 1: Build\n\n- [x] T001 Build part src/omega.txt\n"
    "- [x] T002 Update the tracker docs/todos.md\n"
    f"- [x] T003 Tidy the history folder {V05}/development/history/\n"
)


def test_another_members_archive_commit_never_satisfies_a_running_members_task(members: Members) -> None:
    """X (v0.5.10) starts before Y (v0.5.2) is archived; Y's archive commit rewrites the shared tracker and
    deletes a file under a shared folder, which must never read as X's checked, unworked tasks."""
    members.setup(omega=OMEGA_X, release=False)
    assert _first(members.member_start("v0.5.2")).startswith("STARTED v0.5.2")
    members.release_member("v0.5.2", "alpha")
    assert _first(members.member_start("v0.5.10")).startswith("STARTED v0.5.10")
    _git(members.work, "checkout", "-q", "-b", "chore/archive-v0.5.2", "origin/develop")
    assert members.archive_member("--apply").returncode == 0
    members.merge_archive()
    members.write("src/omega.txt", "omega\n")
    members.commit("omega work")
    omega = members.lines("v0.5.10")
    assert (omega["task.T001"], omega["task.T002"], omega["task.T003"]) == ("met", "unmet", "unmet")


def test_a_forged_commit_with_the_archive_file_list_is_never_an_archive(members: Members) -> None:
    members.setup()
    base = _git(members.work, "rev-parse", "origin/develop").strip()
    assert members.archive_member("--apply").returncode == 0
    real = members.head()
    archives = cm.signed_archives(members.load().record)
    assert cm.is_archive_commit(members.rctx(), real, 1, archives)
    _git(members.work, "checkout", "-q", "-b", "forged", base)
    _git(members.work, "cherry-pick", "-n", real)  # the same file list
    members.write(moved(SURVEY), "# Forged content\n")
    members.commit("forged archive")
    forged = members.head()
    assert not cm.is_archive_commit(members.rctx(), forged, 1, archives)
    _git(members.work, "checkout", "-q", "-B", "chore/archive-v0.5.2", forged)  # throwaway repository
    refusals = mc._archive_branch_refusals(members.rctx(), members.load().record, "v0.5.2")
    assert [r.line() for r in refusals] == [f"REFUSED: branch-not-archive-only ({forged[:12]})"]
    assert _audit(members, base, ("src/omega.txt", "omega\n")) == "unmet"  # never left out of a claim audit


@pytest.mark.parametrize("edited", [False, True], ids=["clean-merge", "merge-with-an-extra-change"])
def test_an_archive_landing_through_a_merge_commit_is_left_out_only_when_clean(members: Members, edited: bool) -> None:
    members.setup()
    base = _git(members.work, "rev-parse", "origin/develop").strip()
    assert members.archive_member("--apply").returncode == 0
    _git(members.work, "checkout", "-q", "develop")
    _git(members.work, "merge", "-q", "--no-ff", "--no-commit", "chore/archive-v0.5.2")
    if edited:
        members.write("docs/todos.md", members.read("docs/todos.md") + "\nChanged in the merge.\n")
    members.commit("Merge the v0.5.2 member archive")
    members.publish("develop")
    assert len(_git(members.work, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3
    assert _audit(members, base, ("src/omega.txt", "omega\n")) == ("unmet" if edited else "met")


@pytest.mark.parametrize("worked", [False, True], ids=["unworked-tracker-task", "worked-tracker-task"])
def test_an_archive_merged_after_a_concurrent_tracker_edit_is_not_task_work(members: Members, worked: bool) -> None:
    """The archive forks, develop edits the shared tracker, a member starts, then the archive lands as a
    --no-ff merge whose tracker blob neither side wrote: the clean automatic merge, not task work."""
    members.setup(omega=OMEGA_X, todos="".join(f"\n## Area {n}\n\n- an item\n" for n in range(6)))
    assert members.archive_member("--apply").returncode == 0
    _git(members.work, "checkout", "-q", "develop")
    members.write("docs/todos.md", members.read("docs/todos.md") + "\n- a concurrent tracker line\n")
    members.commit("develop edits the tracker")
    members.publish("develop")
    assert _first(members.member_start("v0.5.10")).startswith("STARTED v0.5.10")
    _git(members.work, "merge", "-q", "--no-ff", "-m", "Merge the v0.5.2 member archive", "chore/archive-v0.5.2")
    members.publish("develop")
    merge = members.head()
    assert cm.merge_status(members.rctx(), merge, 2, cm.signed_archives(members.load().record)) == "archive"
    work = [("src/omega.txt", "omega\n")]
    if worked:
        work.append(("docs/todos.md", members.read("docs/todos.md") + "\n- omega's own tracker line\n"))
    for rel, text in work:
        members.write(rel, text)
    members.commit("omega work")
    omega = members.lines("v0.5.10")
    assert (omega["task.T001"], omega["task.T002"]) == ("met", "met" if worked else "unmet")


def test_an_archive_commit_changed_before_it_lands_is_refused_and_unsealed(
    members: Members, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
) -> None:
    """Another process (or a hook) changes a staged archive file just before the commit: the commit no
    longer carries the signed archive, so it is undone, the tree restored, and the identity removed."""
    members.setup()
    head, tree = members.head(), _git(members.work, "ls-files")
    real = mc._git

    def interloper(rctx: ck.RepoContext, *args: str) -> tuple[int, str]:
        if args[:1] == ("commit",):
            members.write(moved(SURVEY), "# Changed after the archive was signed\n")
            real(rctx, "add", "--", moved(SURVEY))
        return real(rctx, *args)

    monkeypatch.setattr(mc, "_git", interloper)
    code = mc.main(["archive-member", "--minor", "v0.5", "--member", "v0.5.2", "--session", SESSION,
                    "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(members.work)])
    assert code == mc.EXIT_REFUSED
    assert capsys.readouterr().out.strip().startswith("REFUSED: archive-commit-unverified")
    assert members.head() == head and _git(members.work, "ls-files") == tree
    assert _git(members.work, "status", "--porcelain").strip() == ""
    assert members.read(SURVEY) == OWNED[SURVEY]
    assert "archived" not in members.member() and members.load().forced is None


def test_an_archive_merge_with_its_own_edit_to_a_shared_file_is_uncertain(members: Members) -> None:
    """The side is only the verified archive commit, but the merge hand-edits the shared tracker, so its
    tree is not the clean automatic merge: a task on the tracker is cannot-verify, never met from archive
    content, while a real edit on an unrelated path still counts."""
    members.setup(omega=OMEGA_X)
    assert members.archive_member("--apply").returncode == 0
    _git(members.work, "checkout", "-q", "develop")
    assert _first(members.member_start("v0.5.10")).startswith("STARTED v0.5.10")
    _git(members.work, "merge", "-q", "--no-ff", "--no-commit", "chore/archive-v0.5.2")
    members.write("docs/todos.md", members.read("docs/todos.md") + "\nEdited inside the merge.\n")
    members.commit("Merge the v0.5.2 member archive")
    members.publish("develop")
    merge = members.head()
    assert cm.merge_status(members.rctx(), merge, 2, cm.signed_archives(members.load().record)) == "uncertain"
    members.write("src/omega.txt", "omega\n")
    members.commit("omega work")
    omega = members.lines("v0.5.10")
    assert (omega["task.T001"], omega["task.T002"]) == ("met", "cannot-verify")


def _archive_in_process(members: Members, monkeypatch: pytest.MonkeyPatch, wrapper) -> int:
    monkeypatch.setattr(mc, "_git", wrapper)
    return mc.main(["archive-member", "--minor", "v0.5", "--member", "v0.5.2", "--session", SESSION,
                    "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(members.work)])


def test_an_archive_commit_git_cannot_read_back_is_kept_with_its_identity(
    members: Members, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
) -> None:
    """Git fails (or the budget runs out) right after a correct commit: nothing is undone, the refusal is
    cannot-verify, and the kept commit is the verified archive the signed identity names."""
    members.setup()
    head = members.head()
    real = mc._git

    def failing(rctx: ck.RepoContext, *args: str) -> tuple[int, str]:
        return (-1, "") if args[:1] == ("rev-parse",) and "HEAD^" in args else real(rctx, *args)

    assert _archive_in_process(members, monkeypatch, failing) == mc.EXIT_REFUSED
    assert capsys.readouterr().out.strip().startswith("REFUSED: cannot-verify (the archive commit was made")
    kept = members.head()
    assert kept != head and _git(members.work, "rev-parse", "HEAD^").strip() == head
    assert "archived" in members.member() and members.load().forced is None
    assert cm.is_archive_commit(members.rctx(), kept, 1, cm.signed_archives(members.load().record))


def test_an_archive_commit_on_an_unexpected_parent_is_rolled_back(
    members: Members, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
) -> None:
    members.setup()
    head, tree = members.head(), _git(members.work, "ls-files")
    real = mc._git

    def interloper(rctx: ck.RepoContext, *args: str) -> tuple[int, str]:
        if args[:1] == ("commit",):  # another process commits first, leaving the staged archive alone
            _rc, sha = real(rctx, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "another process commits first")
            real(rctx, "update-ref", "HEAD", sha.strip())
        return real(rctx, *args)

    assert _archive_in_process(members, monkeypatch, interloper) == mc.EXIT_REFUSED
    assert capsys.readouterr().out.strip().startswith("REFUSED: archive-commit-unverified")
    assert members.head() == head and _git(members.work, "ls-files") == tree
    assert _git(members.work, "status", "--porcelain").strip() == ""
    assert "archived" not in members.member() and members.load().forced is None


def test_an_archive_commit_rewritten_after_it_landed_is_never_read_as_archived(members: Members) -> None:
    """An amended archive commit no longer carries the signed archive: the member's archive and every
    task line on its paths read cannot-verify, never met."""
    members.setup(omega=OMEGA_X)
    assert members.archive_member("--apply").returncode == 0
    members.write("docs/todos.md", members.read("docs/todos.md") + "\nAmended in.\n")
    _git(members.work, "add", "docs/todos.md")
    _git(members.work, "commit", "-q", "--amend", "--no-edit")
    members.merge_archive()
    assert members.lines()["archive.member"] == "cannot-verify"
    omega = members.lines("v0.5.10")
    assert (omega["task.T001"], omega["task.T002"]) == ("unmet", "cannot-verify")
