"""The minor verdict, the member gate, and the closing pull request (v4.13.6 Phase 5).

Covers T035-T044 in throwaway repositories with a local bare remote and the
committed `gh` stand-in:

- `check-minor` precedence (tampered, paused, blocked, predicates), a blocker in
  plan 2 of 3, a paused minor, a plan added after approval, a member that no
  longer resolves, and budget exhaustion;
- the member gate: `record member-start` refusing a stale fetch, an unfinished
  previous member, and a missing back-merge, and `check-minor` refusing a member
  whose recorded base predates the previous release;
- `minor.close-pr` with a red check, the local fix, and the back-merge, the `n/a`
  close, and `cleanup.merged` keyed on the minor's last merge;
- a two-plan walk from the record to `MINOR COMPLETE v0.5` through both releases,
  the migration, the archive, the closing pull request, and the final cleanup pass;
- resuming in a new session with the resume paste;
- the runner and the turn-end gate on a schema-2 record, the gate parametrized
  over both hook implementations.

No case touches the network.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
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
from .test_gap_migration_and_archive import BG2, CLOSE, GAPS05, LINK_CHECKER, V05, WN3, Close, ledger, section
from .test_run_plan import Env

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
HOOKS = REPO_ROOT / "catalog" / "hooks"
sys.path.insert(0, str(SCRIPTS))
import check_plan_completion as ck  # noqa: E402
import completion_minor as cm  # noqa: E402

EVIDENCE_SECTIONS = [s for s in ck.REQUIRED_SECTIONS if s != "Full-suite testing and stabilization"]
GREEN = [{"name": "ci", "bucket": "pass"}]
RED = [{"name": "ci", "bucket": "fail"}]


class Walk(Close):
    """The two-plan v0.5 fixture (v0.5.2 alpha, v0.5.10 omega) driven through a minor run."""

    def forge_minor(self, *, bound: tuple[str, ...] = ("v0.5#WN-3",), archive: bool = True,
                    extra: tuple[str, ...] = ("cleanup-merged", "minor-close-pr"),
                    named: tuple[str, ...] = ()) -> dict:
        record = self.forge(bound=bound, archive=archive, named=named)
        record["approvals"]["classes"] += [{"class": name} for name in extra]
        self.write_record(record, resign=True)
        return record

    def verdict(self, session: str | None = None) -> cm.MinorVerdict:
        return cm.check_minor(ck, self.rctx(), "v0.5", session)

    def check(self, *args: str) -> subprocess.CompletedProcess:
        return self.run("check-minor", "v0.5", *args)

    def member_start(self, version: str, session: str = SESSION, head: str | None = None) -> subprocess.CompletedProcess:
        """The runbook's gate step: the new member branch is cut from the local `origin/develop`."""
        base = head or _git(self.work, "rev-parse", "origin/develop").strip()
        return self.run("record", "member-start", "--minor", "v0.5", "--member", version, "--session", session,
                        "--head", base)

    def both_released(self, *, start: bool = True) -> None:
        if start:
            assert _first(self.member_start("v0.5.2")).startswith("STARTED")
        self.release_member("v0.5.2", "alpha")
        if start:
            assert _first(self.member_start("v0.5.10")).startswith("STARTED")
        self.release_member("v0.5.10", "omega")

    def merge_close(self, *files: tuple[str, str], checks: list[dict] | None = None) -> str:
        """Cut `chore/close-v0.5` from origin/develop, commit `files`, merge it into develop, publish."""
        _git(self.work, "checkout", "-q", "-b", "chore/close-v0.5", "origin/develop")
        for rel, text in files:
            self.write(rel, text)
        self.commit("close v0.5")
        _git(self.work, "checkout", "-q", "develop")
        _git(self.work, "merge", "-q", "--ff-only", "chore/close-v0.5")
        self.publish("develop")
        merge = self.head()
        self.pr("chore/close-v0.5", "MERGED", GREEN if checks is None else checks, merge)
        _git(self.work, "branch", "-q", "-D", "chore/close-v0.5")
        return merge

    def gh(self, **updates: object) -> None:
        self.state.update(updates)
        self.save_state()

    def pr(self, branch: str, state: str, checks: list[dict], merge: str | None = None) -> None:
        entry: dict = {"state": state, "checks": checks}
        if merge:
            entry["merge_commit"] = merge
        self.state.setdefault("pr_by_branch", {})[branch] = entry
        self.save_state()

    def release_member(self, version: str, slug: str, *, back_merge: bool = True) -> None:
        """The member's work lands on main through its merged pull request, then the release."""
        rel = f"{V05}/plans/{version}-{slug}.md"
        self.write(rel, self.read(rel).replace("- [ ] T001", "- [x] T001"))
        self.write(f"src/{slug}.txt", f"{slug}\n")
        self.write(f"tests/test_{slug}.py", "def test_part():\n    assert True\n")
        body = "".join(f"## {name}\n\nDone.\n\n" for name in EVIDENCE_SECTIONS)
        body += f"## Full-suite testing and stabilization\n\n`pytest -q`: 3 passed, including tests/test_{slug}.py.\n"
        self.write(f"{V05}/development/{version}-last-phase-evidence.md", "# Evidence\n\n" + body)
        changelog = self.work / "CHANGELOG.md"
        old = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n"
        self.write("CHANGELOG.md", old + f"\n## [{version.lstrip('v')}] - 2026-09-29\n")
        self.commit(f"release {version}")
        head = self.head()
        _git(self.work, "tag", version)
        self.publish("main", version)
        self.state["releases"][version] = False
        self.pr(f"feat/{version}-{slug}", "MERGED", GREEN, head)
        if back_merge:
            self.integrate()

    def gaps_ledger(self) -> None:
        self.write(GAPS05, ledger("v0.5", section("v0.5.2", 1, WN3), status="finalized"))
        self.commit("ledgers")
        self.integrate()


@pytest.fixture()
def walk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Walk:
    return Walk(tmp_path, monkeypatch)


def _first(result: subprocess.CompletedProcess) -> str:
    return result.stdout.splitlines()[0] if result.stdout else ""


# --------------------------------------------------------------------------- precedence


def test_tampered_wins_over_pause_and_blockers(walk: Walk) -> None:
    record = walk.forge_minor()
    record["pause"] = {"at": ck._now()}
    record["blockers"] = [{"category": "no-progress", "open": True, "version": "v0.5.2"}]
    walk.write_record(record, resign=True)
    rel = f"{V05}/plans/v0.5.10-omega.md"
    walk.write(rel, walk.read(rel) + "\nAn instruction appended after approval.\n")
    verdict = walk.verdict()
    assert (verdict.line, verdict.code) == ("BLOCKED: record-tampered", ck.EXIT_BLOCKED)
    assert verdict.members == [] and verdict.minor == []


def test_paused_minor_wins_over_blockers_and_prints_no_lines(walk: Walk) -> None:
    record = walk.forge_minor()
    record["pause"] = {"at": ck._now()}
    record["blockers"] = [{"category": "no-progress", "open": True, "version": "v0.5.2"}]
    walk.write_record(record, resign=False)  # pause and blockers are unsigned (WN-8)
    result = walk.check()
    assert result.returncode == ck.EXIT_PAUSED
    assert result.stdout.splitlines() == ["PAUSED"]


def test_a_member_that_no_longer_resolves_is_tampered(walk: Walk) -> None:
    walk.forge_minor()
    (walk.work / f"{V05}/plans/v0.5.10-omega.md").unlink()
    assert walk.verdict().line == "BLOCKED: record-tampered"


def test_blocker_in_plan_2_of_3_stops_the_whole_run(walk: Walk) -> None:
    walk.plan("v0.5.1", "first")
    walk.commit("third plan")
    walk.integrate()
    walk.forge_minor()
    blocked = walk.run("record", "block", "--minor", "v0.5", "--member", "v0.5.2",
                       "--category", "unreproducible-red-check", "--evidence", "ci red, not reproducible")
    assert (blocked.returncode, _first(blocked)) == (3, "BLOCKED: unreproducible-red-check (v0.5.2)")
    result = walk.check()
    assert result.returncode == 3
    assert result.stdout.splitlines() == ["BLOCKED: unreproducible-red-check (v0.5.2)"]
    # No further phase: the next member cannot pass its gate while the blocker is open.
    later = walk.member_start("v0.5.10")
    assert (later.returncode, _first(later)) == (3, "BLOCKED: unreproducible-red-check (v0.5.2)")
    assert "start_head" not in next(m for m in walk.record()["members"] if m["version"] == "v0.5.10")


def test_a_blocker_the_approvals_already_answer_is_rejected(walk: Walk) -> None:
    walk.forge_minor()
    result = walk.run("record", "block", "--minor", "v0.5", "--member", "v0.5.2", "--category",
                      "approval-not-covered", "--evidence", "x", "--approval-class", "push-merge")
    assert result.returncode == ck.EXIT_MALFORMED
    assert walk.record()["blockers"] == []


def test_a_plan_added_after_approval_is_never_absorbed(walk: Walk) -> None:
    walk.forge_minor()
    walk.plan("v0.5.11", "late")
    walk.commit("a plan added after the approval")
    verdict = walk.verdict()
    assert (verdict.line, verdict.code) == ("BLOCKED: new-member-not-approved (v0.5.11)", ck.EXIT_BLOCKED)
    assert [m["version"] for m in walk.record()["members"]] == ["v0.5.2", "v0.5.10"]
    # A Status edit is not a release: the late plan still blocks (review finding 3).
    walk.plan("v0.5.11", "late", status="complete")
    walk.commit("late plan marked complete")
    assert walk.verdict().line == "BLOCKED: new-member-not-approved (v0.5.11)"
    walk.ship("v0.5.11")  # tag local and remote, Release published
    assert not walk.verdict().line.startswith("BLOCKED")


def test_an_unsigned_excluded_edit_is_tampered(walk: Walk) -> None:
    """Review finding 3: `excluded` is signed, so it cannot hide a late plan."""
    walk.forge_minor()
    walk.plan("v0.5.11", "late")
    walk.commit("late plan")
    record = walk.record()
    record.setdefault("excluded", []).append({"version": "v0.5.11", "reason": "status-complete"})
    walk.write_record(record, resign=False)
    assert walk.verdict().line == "BLOCKED: record-tampered"


def test_a_forged_completed_is_tampered_and_a_signed_one_still_takes_blockers(walk: Walk) -> None:
    """Review finding 4: `completed` is signed; a completed record still accepts a blocker."""
    record = walk.forge_minor()
    record["completed"] = {"at": ck._now(), "head": "x"}
    walk.write_record(record, resign=False)
    assert walk.verdict().line == "BLOCKED: record-tampered"
    blocked = walk.run("record", "block", "--minor", "v0.5", "--session", SESSION, "--category", "no-progress",
                       "--evidence", "e")
    assert (blocked.returncode, _first(blocked)) == (3, "BLOCKED: record-tampered")
    assert walk.record()["blockers"] == []  # nothing was written to a tampered record
    walk.write_record(record, resign=True)  # as check-minor writes it at MINOR COMPLETE
    blocked = walk.run("record", "block", "--minor", "v0.5", "--session", SESSION, "--category", "no-progress",
                       "--evidence", "e")
    assert (blocked.returncode, _first(blocked)) == (3, "BLOCKED: no-progress")
    assert walk.verdict().line == "BLOCKED: no-progress"


def test_budget_exhaustion_reads_cannot_verify_never_met(walk: Walk) -> None:
    walk.forge_minor()
    walk.gh(sleep=6)
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_plan_completion.py"), "check-minor", "v0.5"],
        cwd=walk.work, env={**walk.env, "NEXUS_CHECK_MINOR_BUDGET_SECONDS": "3"},
        capture_output=True, text=True, check=False, timeout=120,
    )
    first = _first(result)
    assert result.returncode == ck.EXIT_INCOMPLETE, result.stdout + result.stderr
    assert first.startswith("INCOMPLETE:") and "member.v0.5.10" in first.split()
    assert "budget exhausted" in result.stderr
    assert time.monotonic() - started < 60


@pytest.mark.parametrize(("value", "expected"), [("500", 120.0), ("abc", 120.0), ("0", 1.0), ("nan", 120.0), ("30", 30.0)])
def test_the_budget_can_only_be_lowered(monkeypatch: pytest.MonkeyPatch, value: str, expected: float) -> None:
    monkeypatch.setenv("NEXUS_CHECK_MINOR_BUDGET_SECONDS", value)
    assert cm.check_minor_seconds() == expected


# --------------------------------------------------------------------------- member gate


def test_member_start_refuses_a_stale_fetch(walk: Walk) -> None:
    walk.forge_minor()
    walk.write("notes.txt", "moved\n")
    walk.commit("develop moved")
    _git(walk.work, "push", "-q", str(walk.remote), "HEAD:refs/heads/develop")  # no fetch
    result = walk.member_start("v0.5.2")
    assert result.stdout.splitlines() == ["BLOCKED: member-gate (v0.5.2)", "reason: fetch-stale"]
    _git(walk.work, "fetch", "-q", "origin")
    assert _first(walk.member_start("v0.5.2")).startswith("STARTED v0.5.2 start_head=")


def test_member_start_is_signed_and_a_hand_edit_is_tampered(walk: Walk) -> None:
    walk.forge_minor()
    started = walk.member_start("v0.5.2")
    assert started.returncode == 0, started.stdout + started.stderr
    tip = _git(walk.work, "rev-parse", "origin/develop").strip()
    member = next(m for m in walk.record()["members"] if m["version"] == "v0.5.2")
    assert member["start_head"] == tip and member["started"]
    assert walk.verdict().line != "BLOCKED: record-tampered"
    assert walk.member_start("v0.5.2").returncode == 0  # idempotent for the same tip
    record = walk.record()
    record["members"][0]["start_head"] = "0" * 40
    walk.write_record(record, resign=False)
    assert walk.verdict().line == "BLOCKED: record-tampered"


def test_skipping_member_start_never_reaches_minor_complete(walk: Walk) -> None:
    """Review finding 2: the gate is not opt-in; a member after the first needs a recorded start."""
    walk.forge_minor(bound=(), archive=False, extra=())
    walk.both_released(start=False)
    verdict = walk.verdict()
    assert not verdict.line.startswith("MINOR COMPLETE")
    assert verdict.ids() == ["v0.5.10:member.gate"]
    assert {m.version: m.gate for m in verdict.members} == {"v0.5.2": "n/a", "v0.5.10": "unmet"}


def test_member_start_requires_head(walk: Walk) -> None:
    walk.forge_minor()
    result = walk.run("record", "member-start", "--minor", "v0.5", "--member", "v0.5.2", "--session", SESSION)
    assert result.returncode == 2 and "--head" in result.stderr


def test_a_start_head_that_is_not_under_the_merged_branch_is_blocked(walk: Walk) -> None:
    """Review finding 2: the recorded base must be an ancestor of the member's merge commit."""
    walk.forge_minor(bound=(), archive=False, extra=())
    walk.both_released()
    assert walk.verdict().line.startswith("MINOR COMPLETE")
    _git(walk.work, "checkout", "-q", "--orphan", "elsewhere")
    walk.commit("an unrelated history")
    unrelated = walk.head()
    _git(walk.work, "checkout", "-q", "-f", "main")
    record = walk.record()
    record["completed"] = None
    walk.write_record(record, resign=True)
    walk.pr("feat/v0.5.10-omega", "MERGED", GREEN, unrelated)
    assert walk.verdict().line == "BLOCKED: member-gate (v0.5.10)"


def test_member_gate_blocks_a_member_recorded_on_a_stale_base(walk: Walk) -> None:
    record = walk.forge_minor()
    stale = record["start_head"]
    walk.release_member("v0.5.2", "alpha")
    record = walk.record()
    omega = next(m for m in record["members"] if m["version"] == "v0.5.10")
    omega["start_head"] = stale  # predates the v0.5.2 release tag
    walk.write_record(record, resign=True)
    verdict = walk.verdict()
    assert (verdict.line, verdict.code) == ("BLOCKED: member-gate (v0.5.10)", ck.EXIT_BLOCKED)
    omega["start_head"] = walk.head()
    walk.write_record(record, resign=True)
    assert not walk.verdict().line.startswith("BLOCKED")


# --------------------------------------------------------------------------- closing pull request


def _close_status(walk: Walk, notices: list[str]) -> str:
    rctx = walk.rctx()
    record = walk.record()
    loaded = cm.load_ledgers_at(rctx, "refs/remotes/origin/develop")
    assert loaded is not None
    return cm.close_pr_status(ck, rctx, record, "v0.5", "acme/demo", loaded[0], notices)


ARCHIVE_FILE = ("docs/archives/v0/v0.5/moved.md", "archived\n")


def test_close_pr_red_check_local_fix_and_back_merge(walk: Walk) -> None:
    walk.forge_minor(bound=())  # only the archive remains: the close carries only the archive
    walk.both_released()
    notices: list[str] = []
    assert _close_status(walk, notices) == "unmet"  # no closing pull request yet
    walk.pr("chore/close-v0.5", "OPEN", RED)
    assert _close_status(walk, notices) == "unmet"  # a red required check, not merged
    walk.merge_close(ARCHIVE_FILE, checks=RED)
    assert _close_status(walk, notices) == "unmet"  # merged over a red check still is not green
    _git(walk.work, "checkout", "-q", "main")
    walk.write("fix.txt", "narrow fix\n")
    walk.commit("fix the reproduced failure")  # the local fix, re-pushed within the bound
    walk.publish("main")
    _git(walk.work, "checkout", "-q", "develop")
    _git(walk.work, "merge", "-q", "--no-ff", "-m", "merge the fix", "main")
    walk.publish("develop")
    walk.pr("chore/close-v0.5", "MERGED", GREEN, walk.state["pr_by_branch"]["chore/close-v0.5"]["merge_commit"])
    assert _close_status(walk, notices) == "met"
    _git(walk.work, "checkout", "-q", "main")
    walk.write("release-note.txt", "on main only\n")
    walk.commit("a commit develop lacks")
    walk.publish("main")
    assert _close_status(walk, notices) == "unmet"  # main not back-merged
    _git(walk.work, "checkout", "-q", "develop")
    _git(walk.work, "merge", "-q", "--no-ff", "-m", "back-merge main", "main")
    walk.publish("develop")
    assert _close_status(walk, notices) == "met"
    record = walk.record()
    record["approvals"]["classes"] = [c for c in record["approvals"]["classes"] if c["class"] != "minor-close-pr"]
    walk.write_record(record, resign=True)
    assert _close_status(walk, notices) == "unmet"
    assert "minor.close-pr needs the minor-close-pr approval" in notices


def test_a_close_pr_matched_by_name_alone_is_not_met(walk: Walk) -> None:
    """Review finding 1: a merged close branch that carries neither the migration nor the archive."""
    walk.gaps_ledger()
    walk.forge_minor()
    walk.both_released()
    walk.merge_close(("trivial.txt", "x\n"))
    notices: list[str] = []
    assert _close_status(walk, notices) == "unmet"
    assert any("does not carry" in n for n in notices)


def test_a_close_merge_not_on_the_target_branch_is_not_met(walk: Walk) -> None:
    walk.forge_minor(bound=())
    walk.both_released()
    _git(walk.work, "checkout", "-q", "-b", "chore/close-v0.5", "origin/develop")
    walk.write(*ARCHIVE_FILE)
    walk.commit("close, never merged into develop")
    walk.pr("chore/close-v0.5", "MERGED", GREEN, walk.head())
    notices: list[str] = []
    assert _close_status(walk, notices) == "unmet"
    assert any("not on the target branch" in n for n in notices)


def test_an_uncommitted_migration_never_completes_the_minor(walk: Walk) -> None:
    """Review finding 1: gaps.minor reads the integration branch, not the working tree."""
    walk.gaps_ledger()
    walk.forge_minor(archive=False, extra=("minor-close-pr",))
    walk.both_released()
    walk.merge_close(("trivial.txt", "x\n"))
    migrated = walk.migrate()  # in the working tree only, never committed
    assert migrated.returncode == 0, migrated.stdout + migrated.stderr
    verdict = walk.verdict()
    assert not verdict.line.startswith("MINOR COMPLETE")
    lines = dict(verdict.minor)
    assert lines["gaps.minor"] == "unmet" and lines["minor.close-pr"] == "unmet"


def test_nothing_to_migrate_and_no_archive_is_an_na_close(walk: Walk) -> None:
    record = walk.forge_minor(bound=(), archive=False)
    rctx = walk.rctx()
    assert cm.close_pr_status(ck, rctx, record, "v0.5", "acme/demo", [], []) == "n/a"
    # The last merge is then the last member's own pull request, in version order.
    assert cm.last_merge_branch(record, "v0.5", "n/a") == "feat/v0.5.10-omega"
    walk.pr("feat/v0.5.10-omega", "MERGED", GREEN, walk.head())
    path = cm.record_file(ck, rctx, "v0.5")
    assert cm.cleanup_minor_status(ck, rctx, record, path, "v0.5", "acme/demo", "n/a") == "unmet"  # no receipt
    record["approvals"]["classes"] = [c for c in record["approvals"]["classes"] if c["class"] != "cleanup-merged"]
    assert cm.cleanup_minor_status(ck, rctx, record, path, "v0.5", "acme/demo", "n/a") == "n/a"
    lines = dict(walk.verdict().minor)
    assert lines["minor.close-pr"] == "n/a" and lines["archive.minor"] == "n/a"


def test_a_frozen_id_fixed_instead_of_migrated_needs_no_close(walk: Walk) -> None:
    """Review finding 6: the close depends on what is still unresolved, not on the frozen list alone."""
    walk.gaps_ledger()
    record = walk.forge_minor(archive=False)
    rctx = walk.rctx()
    ledgers = cm.load_ledgers_at(rctx, "refs/remotes/origin/develop")[0]
    assert cm.close_required(record, ledgers)  # WN-3 is still open on develop
    walk.write(GAPS05, walk.read(GAPS05).replace("#### WN-3: The probe flakes on a cold cache",
                                                 "#### WN-3: The probe flakes on a cold cache - RESOLVED"))
    walk.commit("fix WN-3")
    walk.integrate()
    ledgers = cm.load_ledgers_at(rctx, "refs/remotes/origin/develop")[0]
    assert not cm.close_required(record, ledgers)
    assert cm.close_pr_status(ck, rctx, record, "v0.5", "acme/demo", ledgers, []) == "n/a"


def test_a_sensitive_gap_not_named_is_never_deferred(walk: Walk) -> None:
    """Review finding 7: a security or high-severity gap blocks the member unless named."""
    walk.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, BG2, bg_open=1), status="finalized"))
    walk.commit("security gap")
    walk.integrate()

    def gaps_version() -> str:
        record = walk.record()
        ctx = ck.Context(str(walk.work / f"{V05}/plans/v0.5.2-alpha.md"), ck.Budget(60))
        return dict(ck.evaluate(ctx, ck.project(record, "v0.5.2"))[0])["gaps.version"]

    walk.forge_minor(bound=("v0.5#BG-2",))
    assert gaps_version() == "unmet"
    walk.forge_minor(bound=("v0.5#BG-2",), named=("v0.5#BG-2",))
    assert gaps_version() == "deferred"


# --------------------------------------------------------------------------- the two-plan walk


def test_two_plan_minor_walks_to_minor_complete(walk: Walk) -> None:
    walk.gaps_ledger()
    walk.forge_minor()
    first = walk.verdict()
    assert first.code == ck.EXIT_INCOMPLETE and "v0.5.2:task.T001" in first.ids()

    assert _first(walk.member_start("v0.5.2")).startswith("STARTED v0.5.2")
    early = walk.member_start("v0.5.10")
    assert early.stdout.splitlines() == ["BLOCKED: member-gate (v0.5.10)", "reason: previous-member-incomplete (v0.5.2)"]

    walk.release_member("v0.5.2", "alpha", back_merge=False)
    alpha = next(m for m in walk.verdict().members if m.version == "v0.5.2")
    assert alpha.status == "met", alpha.lines
    assert dict(alpha.lines)["gaps.version"] == "deferred"  # WN-3 waits for the minor close
    stale = walk.member_start("v0.5.10")
    assert stale.stdout.splitlines() == ["BLOCKED: member-gate (v0.5.10)", "reason: back-merge-missing"]

    walk.integrate()
    assert _first(walk.member_start("v0.5.10")).startswith("STARTED v0.5.10")
    walk.release_member("v0.5.10", "omega")
    before_close = walk.verdict()
    assert set(before_close.ids()) == {"gaps.minor", "minor.close-pr", "cleanup.merged", "archive.minor"}

    # The minor close: one branch from the post-release develop, migration, archive.
    _git(walk.work, "checkout", "-q", "-b", "chore/close-v0.5", "origin/develop")
    migrated = walk.migrate()
    assert migrated.returncode == 0, migrated.stdout + migrated.stderr
    walk.commit("migrate v0.5#WN-3")
    archived = walk.close("archive", "--minor", "v0.5", "--apply", "--link-checker", str(LINK_CHECKER))
    assert archived.returncode == 0, archived.stdout + archived.stderr
    walk.pr("chore/close-v0.5", "OPEN", RED)
    assert "minor.close-pr" in walk.verdict().ids()
    walk.write("fix.txt", "narrow fix\n")
    walk.commit("fix the reproduced failure")
    _git(walk.work, "checkout", "-q", "develop")
    _git(walk.work, "merge", "-q", "--ff-only", "chore/close-v0.5")
    walk.publish("develop")
    walk.pr("chore/close-v0.5", "MERGED", GREEN, walk.head())
    _git(walk.work, "branch", "-q", "-D", "chore/close-v0.5")  # fixture reset, not the executor

    cleanup = subprocess.run(
        [sys.executable, str(SCRIPTS / "cleanup_merged.py"), "--apply", "--receipt", "--minor", "v0.5",
         "--repo", str(walk.work)],
        cwd=walk.work, env=walk.env, capture_output=True, text=True, check=False, timeout=300,
    )
    assert cleanup.returncode in (0, 1), cleanup.stdout + cleanup.stderr
    assert "BLOCKED" not in cleanup.stdout

    done = walk.check()
    assert done.returncode == 0, done.stdout + done.stderr
    nonce = walk.record()["nonce"]
    assert _first(done) == f"MINOR COMPLETE v0.5 {walk.head()} {nonce}"
    assert walk.record()["completed"]
    again = walk.check()
    assert (again.returncode, _first(again)) == (0, _first(done))
    assert cm.covering_minor(ck, walk.rctx(), "v0.5.2") is None  # the record's authority has ended


# --------------------------------------------------------------------------- resume


def test_resume_in_a_new_session_needs_the_resume_paste(walk: Walk) -> None:
    walk.forge_minor()
    other = walk.verdict("session-two")
    assert other.line == "INCOMPLETE: record.minor"
    assert any("paste its resume line" in n for n in other.notices)
    line = walk.paste("session-two", "--action", "resume")
    resumed = walk.run("record", "resume", "--minor", "v0.5", "--session", "session-two")
    assert (resumed.returncode, _first(resumed)) == (0, "RESUMED minor v0.5 session bound"), line
    assert walk.record()["session_id"] == "session-two"
    assert walk.verdict("session-two").line != "INCOMPLETE: record.minor"


# --------------------------------------------------------------------------- runner


STUB_MINOR_CHECKER = r'''
import json, os, sys
state = json.load(open(os.environ["STUB_STATE"], encoding="utf-8"))
counter_file = os.environ["STUB_COUNTER"]
count = int(open(counter_file).read()) if os.path.exists(counter_file) else 0
with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as h:
    h.write(json.dumps(["checker", *sys.argv[1:]]) + "\n")
args = sys.argv[1:]
if args[:3] == ["record", "path", "--minor"]:
    print(state.get("record") or "/nonexistent")
    sys.exit(0 if state.get("record") else 1)
if args[:2] == ["record", "block"]:
    if state.get("block_fails"):
        print("BLOCKED: record-tampered"); sys.exit(3)
    print("BLOCKED: " + args[args.index("--category") + 1]); sys.exit(3)
if args[0] == "check-minor":
    if state.get("terminal"):
        print(state["terminal"][0]); sys.exit(state["terminal"][1])
    if count >= state.get("complete_at", 99):
        print("MINOR COMPLETE v0.5 head nonce"); sys.exit(0)
    print("INCOMPLETE: v0.5.2:task.T001 gaps.minor"); sys.exit(1)
if args[0] == "score-minor":
    print(f"{count if state.get('progress', True) else 0} head -"); sys.exit(0)
print("unexpected " + " ".join(args)); sys.exit(2)
'''


@pytest.fixture
def runner(tmp_path: Path) -> Env:
    env = Env(tmp_path)
    env.checker.write_text(STUB_MINOR_CHECKER, encoding="utf-8")
    return env


def test_runner_drives_a_minor_through_check_minor(runner: Env) -> None:
    result = runner.run("v0.5", "--platform", "codex")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "MINOR COMPLETE v0.5 head nonce"
    checks = runner.calls("checker")
    assert ["record", "path", "--minor", "v0.5"] in checks
    assert ["check-minor", "v0.5"] in checks and ["score-minor", "v0.5"] in checks
    assert not any(c[0] in ("check", "score") for c in checks)
    assert runner.calls("cli")[1][4] == "Continue /implement v0.5. The completion checker still reports it incomplete."


def test_runner_no_progress_applies_to_the_minor_score(runner: Env) -> None:
    runner.state.update(progress=False, complete_at=99)
    result = runner.run("v0.5", "--platform", "codex")
    assert result.returncode == 3 and "BLOCKED: no-progress" in result.stdout
    blocks = [c for c in runner.calls("checker") if c[:2] == ["record", "block"]]
    assert blocks and blocks[0][2:4] == ["--minor", "v0.5"] and "no-progress" in blocks[0]


def test_runner_goal_names_the_minor_verdict(runner: Env) -> None:
    runner.run("v0.5", "--platform", "claude")
    prompt = runner.calls("cli")[0][2]
    # v4.13.6 Phase 6: the approval page's goal line, naming the checker's tool result, no nonce.
    assert "first output line starts with MINOR COMPLETE v0.5" in prompt and "n0nce" not in prompt


def test_runner_terminal_minor_verdict_launches_nothing(runner: Env) -> None:
    runner.state["terminal"] = ["BLOCKED: member-gate (v0.5.10)", 3]
    result = runner.run("v0.5", "--platform", "codex")
    assert (result.returncode, result.stdout.strip()) == (3, "BLOCKED: member-gate (v0.5.10)")
    assert runner.calls("cli") == []


def test_runner_never_reports_a_blocker_it_could_not_write(runner: Env) -> None:
    """Review finding 4: a refused `record block` is not reported as the runner's blocker."""
    runner.state.update(progress=False, complete_at=99, block_fails=True)
    result = runner.run("v0.5", "--platform", "codex")
    assert result.returncode == 3
    assert result.stdout.strip().splitlines()[-1] == "BLOCKED: record-tampered"
    assert "BLOCKED: no-progress" not in result.stdout
    assert "blocker was not recorded" in result.stderr


@pytest.mark.parametrize("token", ["v0.5.x", "v0", "v00.5"])
def test_runner_refuses_a_malformed_scope(runner: Env, token: str) -> None:
    assert runner.run(token, "--platform", "codex").returncode == 2


# --------------------------------------------------------------------------- turn-end gate, both hooks


def _hook_resolvers() -> tuple[str | None, str | None]:
    spec = importlib.util.spec_from_file_location("hook_conftest", HOOKS / "tests" / "conftest.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module._resolve_bash(), module._resolve_powershell()


GATE_STUB = r'''
import json, os, sys
with open(os.environ["GATE_STUB_LOG"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\n")
    handle.write(json.dumps(["budget", os.environ.get("NEXUS_CHECK_MINOR_BUDGET_SECONDS", "")]) + "\n")
if sys.argv[1] == "check-minor":
    import time
    time.sleep(float(os.environ.get("GATE_STUB_SLEEP", "0")))
    print(os.environ.get("GATE_STUB_LINE", "INCOMPLETE: v0.5.2:task.T001 gaps.minor"))
    met, head = os.environ.get("GATE_STUB_SCORE", "3 abc -").split()[:2]
    if "--json" in sys.argv and not os.environ.get("GATE_STUB_NO_JSON"):
        print(json.dumps({"verdict": "x", "met": int(met), "head": head}))
    sys.exit(int(os.environ.get("GATE_STUB_RC", "1")))
if sys.argv[1] == "score-minor":
    print("unexpected second evaluation"); sys.exit(2)
if sys.argv[1] in ("check", "score"):
    print("unexpected per-plan call"); sys.exit(2)
sys.exit(3)
'''


class GateHome:
    def __init__(self, tmp: Path) -> None:
        self.root = tmp / "home"
        scripts = self.root / ".nexus-hub" / "scripts"
        self.runs = self.root / ".nexus-hub" / "runs"
        self.repo = tmp / "repo"
        self.log = tmp / "gate.log"
        scripts.mkdir(parents=True)
        self.runs.mkdir(parents=True)
        self.repo.mkdir()
        shutil.copy(SCRIPTS / "completion_gate.py", scripts / "completion_gate.py")
        (scripts / "check_plan_completion.py").write_text(GATE_STUB, encoding="utf-8")
        record = {"schema": 2, "scope": "minor", "minor": "v0.5", "session_id": SESSION, "repo_root": str(self.repo)}
        (self.runs / "minor.json").write_text(json.dumps(record), encoding="utf-8")

    def env(self, **extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("NEXUS_", "GATE_STUB"))}
        env.update(HOME=str(self.root), USERPROFILE=str(self.root), GATE_STUB_LOG=str(self.log))
        env.update(extra)
        return env

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(params=["sh", "ps1"])
def gate(request, tmp_path: Path):
    bash, powershell = _hook_resolvers()
    home = GateHome(tmp_path)
    if request.param == "sh" and bash is None:
        pytest.skip("no bash able to execute a hook script")
    if request.param == "ps1" and powershell is None:
        pytest.skip("no PowerShell interpreter")

    def _run(**env: str) -> subprocess.CompletedProcess:
        if request.param == "sh":
            argv = [bash, str(HOOKS / "completion-gate.sh")]
        else:
            argv = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HOOKS / "completion-gate.ps1")]
        payload = json.dumps({"hook_event_name": "Stop", "session_id": SESSION, "stop_hook_active": False})
        return subprocess.run(argv, input=payload, text=True, capture_output=True, cwd=str(home.repo),
                              env=home.env(**env), timeout=120, check=False)

    return home, _run


def test_gate_refuses_the_stop_of_an_incomplete_minor(gate) -> None:
    home, run = gate
    result = run()
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["decision"] == "block" and "v0.5.2:task.T001 gaps.minor" in out["reason"]
    calls = [c for c in home.calls() if c[0] != "budget"]
    # One evaluation: the verdict and the score come from the same --json run (review finding 5).
    assert calls == [["check-minor", "v0.5", "--repo", str(home.repo), "--session", SESSION, "--json"]]
    budgets = {c[1] for c in home.calls() if c[0] == "budget"}
    assert budgets and all(b and float(b) <= 25 for b in budgets)  # inside the gate's budget, less the reserve


@pytest.mark.parametrize(("line", "rc"), [("MINOR COMPLETE v0.5 h n", "0"), ("BLOCKED: member-gate (v0.5.10)", "3"), ("PAUSED", "4")])
def test_gate_allows_the_stop_on_a_terminal_minor_verdict(gate, line: str, rc: str) -> None:
    home, run = gate
    result = run(GATE_STUB_LINE=line, GATE_STUB_RC=rc)
    assert (result.returncode, result.stdout.strip()) == (0, "")


def test_gate_no_progress_blocks_the_minor_record(gate) -> None:
    home, run = gate
    decisions = [run().stdout.strip() for _ in range(4)]  # the first call is progress against no state
    assert decisions[-1] == ""  # the fourth stop is allowed once the blocker is written
    blocks = [c for c in home.calls() if c[:2] == ["record", "block"]]
    assert blocks and blocks[0][2:4] == ["--minor", "v0.5"] and "no-progress" in blocks[0]


def test_gate_never_counts_a_refusal_without_a_score(gate) -> None:
    """Review finding 5: an unreadable score is not evidence of no progress."""
    home, run = gate
    for _ in range(4):
        assert json.loads(run(GATE_STUB_NO_JSON="1").stdout)["decision"] == "block"
    assert [c for c in home.calls() if c[:2] == ["record", "block"]] == []


def test_gate_slow_evaluation_with_progress_writes_no_blocker(gate) -> None:
    """Review finding 5 (ported probe): a slow check whose score rises is progress, not a stall."""
    home, run = gate
    for i in range(3):
        result = run(GATE_STUB_SLEEP="4", GATE_STUB_SCORE=f"{10 + i} head{i} -")
        assert json.loads(result.stdout)["decision"] == "block"
    assert [c for c in home.calls() if c[:2] == ["record", "block"]] == []
    state = json.loads(next(home.runs.glob("*.gate.json")).read_text(encoding="utf-8"))
    assert state["refusals"] == 0 and state["met"] == 12
