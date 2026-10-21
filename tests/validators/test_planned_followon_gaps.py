"""Planned follow-on gaps: an exact frozen recording task may migrate, a new defect may not.

A frozen plan task of the form `File <scope> as a known gap <ledger>` produces one
canonical known-gaps entry (`cm.planned_followon_entry`), bound to the frozen plan
hash and the task hash. The suite proves, against the real modules and the real
frozen v4.14.1 plan:

- recognition (`cm.planned_followon`, `cm.migration_gate`): both real recording tasks
  are recognized, and every deviation (another task's anchor, an edited or appended
  body, a non-DF kind, a sensitive item, another section, an unbound member, a changed
  plan, a duplicated or misplaced task) is denied, with the authority left unchanged;
- migration verification (`cm.verify_migration`): the migrated copy must stay OPEN and
  canonical in the next minor, and the inherited frozen-id path is unchanged;
- archive (`cm.archived_followon_plan` via `planned_followon`): after a real archive
  repair, only the signed member start head can recover the original plan text;
- write preflight (`mc.plan_migration`): only `user-deferred` is accepted, and a closed
  or non-canonical copy, new or reused, is refused before anything is written.

Every repository is a throwaway under `tmp_path` built by the shared `Close` fixture
(local bare remote, `gh` stand-in, isolated runs directory). Git runs through the
shared `_git` helper; the repo conftest starts every child with CREATE_NO_WINDOW.
"""

from __future__ import annotations

import copy
import dataclasses
import re
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from .test_check_plan_completion import (  # noqa: F401  (autouse fixture re-exported)
    _git,
    _isolated_git_config,
)
from .test_completion_minor_record import (  # noqa: F401  (autouse fixture re-exported)
    _no_transport_overrides,
)
from .test_gap_migration_and_archive import Close

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_plan_completion as ck
import completion_minor as cm
import minor_close as mc

VERSION = "v4.14.1"
NAME = "v4.14.1-adoption-effort-allocation.md"
ACTIVE = "docs/releases/v4/v4.14"
ARCHIVE = "docs/archives/v4/v4.14"
PLAN_REL = f"{ACTIVE}/plans/{NAME}"
GAPS = f"{ACTIVE}/known-gaps.md"
GAPS15 = "docs/releases/v4/v4.15/known-gaps.md"
FROZEN = "2eb59610176121b531129c48f9c324fbb8001fbbe18f5a3bc8159776f479120e"
FROZEN_TEXT = (REPO_ROOT / PLAN_REL).read_text(encoding="utf-8")
INHERITED = [f"v4.14#DF-{n}" for n in range(1, 84)]
INHERITED_ENTRY = "#### DF-1: Original inherited item\n\n- **Reason**: inherited from v4.13\n\n"
EVIDENCE = "Frozen v4.14.1 recording task"
DATE = "2026-10-19"
ALTERED = "planned-followon-copy-altered"

Edit = Callable[[str, str], tuple[str, str]]


def frozen_plan(text: str = FROZEN_TEXT, rel: str = PLAN_REL) -> cm.Plan:
    return cm.Plan(rel, VERSION, (4, 14, 1), "queued", "adoption-effort-allocation", text)


def canonical(task: str) -> tuple[str, str]:
    entry = cm.planned_followon_entry(ck, frozen_plan(), task, FROZEN)
    assert entry is not None, task
    return entry


def gaps(items: str, version: str = VERSION, subsection: str = "Open Items") -> str:
    """A v4.14 ledger with one patch section whose DF summary row matches its items."""
    df_open = sum(1 for i in cm.parse_ledger(items) if i.kind == "DF" and i.state == "open")
    return (
        "# Known Gaps - v4.14\n\n**Project**: demo\n**Status**: in-progress\n**Last updated**: 2026-10-01\n\n"
        f"## {version}\n\n### Summary\n\n| Category | Open | Resolved |\n|---|---|---|\n"
        f"| Deferred (DF) | {df_open} | 0 |\n\n### {subsection}\n\n{items}"
        "### Resolved\n\n| ID | Title | Resolved in | Notes |\n|---|---|---|---|\n"
    )


def entry_text(gid: str, task: str, edit: Edit = lambda t, b: (t, b)) -> str:
    title, body = edit(*canonical(task))
    return f"#### {gid}{title}\n\n{body}\n\n"


def item(text: str, gid: str) -> cm.GapItem:
    found = [i for i in cm.parse_ledger(text) if i.gid == gid]
    assert len(found) == 1, gid
    return found[0]


def followon(task: str = "T004", gid: str = "DF-84", *, version: str = VERSION,
             subsection: str = "Open Items", edit: Edit = lambda t, b: (t, b)) -> cm.GapItem:
    return item(gaps(entry_text(gid, task, edit), version, subsection), gid)


def recount(text: str) -> str:
    """Keep a hand-edited ledger's `**Open items**` header true, so only the edit is judged."""
    total = sum(1 for i in cm.parse_ledger(text) if i.state == "open")
    return re.sub(r"^\*\*Open items\*\*: \d+", f"**Open items**: {total}", text, count=1, flags=re.MULTILINE)


def resolve_copy(text: str, gid: str) -> str:
    return recount(re.sub(rf"^(#### {gid}: .*)$", r"\1 - RESOLVED", text, count=1, flags=re.MULTILINE))


def append_defect(text: str, gid: str) -> str:
    line = f"- **Migration evidence**: {EVIDENCE}\n"
    assert text.count(line) == 1
    return text.replace(line, line + "\n**Defect**: actual new broken implementation\n")


def change_reason(text: str, gid: str) -> str:
    assert text.count("(reason: user-deferred)") == 1
    return text.replace("(reason: user-deferred)", "(reason: vendor-feature)")


class FollowOn(Close):
    """A repository holding the frozen v4.14.1 plan and its two recorded follow-ons.

    The start head holds only the inherited DF-1; T004 and T005 then file DF-84 and
    DF-85, so both are created during the run, as a recording task's entry is.
    """

    def __init__(self, tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        super().__init__(tmp, monkeypatch)
        self.write(PLAN_REL, FROZEN_TEXT)
        self.write(GAPS, gaps(INHERITED_ENTRY))
        self.commit("v4.14 start")
        self.start = self.head()
        self.write(GAPS, gaps(INHERITED_ENTRY + entry_text("DF-84", "T004") + entry_text("DF-85", "T005")))
        self.commit("v4.14.1 T004 and T005 file their planned follow-ons")
        self.integrate()

    def authority(self, **member: object) -> dict:
        """A schema-2 minor record as `record create` freezes it (left unsigned: callers verify)."""
        entry = {"version": VERSION, "plan_path": PLAN_REL, "plan_sha256": FROZEN, "start_head": self.start,
                 "source_branch": f"feat/{VERSION}-adoption-effort-allocation", "target_branch": "develop"}
        entry.update(member)
        return {
            "schema": ck.SCHEMA_MINOR, "scope": "minor", "minor": "v4.14", "repo": "acme/demo",
            "start_head": self.start, "nonce": "nonce-v4.14", "members": [entry],
            "approvals": {"target_branch": "develop", "spend_caps": {"usd": 20}, "classes": [
                {"class": "gap-migration", "bound": list(INHERITED), "named": []},
                {"class": "minor-close-pr", "bound": 3},
            ]},
        }

    def allowed(self, record: dict, gap: cm.GapItem) -> bool:
        return cm.planned_followon(self.rctx(), record, (4, 14), gap)

    def remove(self, rel: str) -> None:
        """Delete a file and its emptied parents: an empty active-tree folder still counts as present."""
        path = self.work / rel
        path.unlink()
        for parent in path.parents:
            if parent == self.work or any(parent.iterdir()):
                break
            parent.rmdir()

    def variant(self, files: dict[str, str]) -> str:
        """Commit `files` over the tree, restore it in a second commit, return the first commit."""
        before = {rel: self.read(rel) if (self.work / rel).exists() else None for rel in files}
        for rel, text in files.items():
            self.write(rel, text)
        self.commit("variant")
        sha = self.head()
        for rel, text in before.items():
            self.write(rel, text) if text is not None else self.remove(rel)
        self.commit("restore")
        return sha

    def archive(self) -> tuple[dict, str]:
        """Move the minor's tree with the real repair planner; the record re-frozen on the moved plan."""
        moved_plan, moved_gaps = f"{ARCHIVE}/plans/{NAME}", f"{ARCHIVE}/known-gaps.md"
        repairs = mc.plan_repairs(self.work, [(PLAN_REL, PLAN_REL, moved_plan), (GAPS, GAPS, moved_gaps)],
                                  ACTIVE, ARCHIVE)
        (self.work / ARCHIVE).parent.mkdir(parents=True, exist_ok=True)
        _git(self.work, "mv", ACTIVE, ARCHIVE)
        for repair in repairs:
            self.write(repair.new_rel, repair.repaired)
        self.commit("archive v4.14")
        archived = self.read(moved_plan)
        record = self.authority(plan_path=moved_plan, plan_sha256=ck.plan_hash_text(archived))
        record["approvals"]["classes"].append({"class": "archive-minor"})
        return record, archived

    def migrate(self, record: dict, gid: str = "DF-84", reason: str = "user-deferred") -> mc.MigrationPlan:
        return mc.plan_migration(self.rctx(), "v4.14", record, f"v4.14#{gid}", reason, EVIDENCE, DATE)

    def migrated(self) -> dict:
        record = self.authority()
        mc.apply_migration(self.migrate(record))
        return record

    def verify(self, record: dict, gid: str = "DF-84") -> tuple[str, str]:
        ledgers, _ = cm.load_ledgers(self.work)
        source = next(ledger for ledger in ledgers if ledger.rel == GAPS)
        return cm.verify_migration(self.rctx(), record, "v4.14", ledgers, source, item(source.text, gid))


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FollowOn:
    return FollowOn(tmp_path, monkeypatch)


def spy(rctx: ck.RepoContext) -> list[list[str]]:
    """Record every command the context runs, still running it for real."""
    calls: list[list[str]] = []
    real = rctx.run

    def run(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        calls.append(list(argv))
        return real(argv, cwd)

    rctx.run = run  # type: ignore[method-assign]
    return calls


# --------------------------------------------------------------------------- recognition


def test_the_frozen_plan_hash_is_the_recorded_v4141_hash() -> None:
    assert ck.plan_hash_text(FROZEN_TEXT) == FROZEN


@pytest.mark.parametrize("task, scope", [("T004", "the lower-direction modifier"),
                                         ("T005", "the raise-direction measurement")])
def test_a_real_frozen_recording_task_is_recognized(repo: FollowOn, task: str, scope: str) -> None:
    gap = item(repo.read(GAPS), {"T004": "DF-84", "T005": "DF-85"}[task])
    assert gap.title == ": Planned follow-on: " + scope
    assert gap.body.strip().startswith("**Disposition**: planned-follow-on (OPEN)")
    assert repo.allowed(repo.authority(), gap) is True
    assert cm.migration_gate(repo.rctx(), repo.authority(), (4, 14), gap.gid, gap) == ("met", "planned-follow-on")


@pytest.mark.parametrize("build", [
    pytest.param(lambda: followon(edit=lambda t, b: (t, b.replace(" T004", " T005"))), id="wrong-task-borrowing"),
    pytest.param(lambda: followon(edit=lambda t, b: (t, b.replace("**Reason**: ", "**Reason**: actual new defect; "))),
                 id="altered-scope-body"),
    pytest.param(lambda: followon(edit=lambda t, b: (t, b + "\n\n**New defect**: implementation fails its contract")),
                 id="appended-new-defect"),
    pytest.param(lambda: followon(gid="BG-1"), id="new-bug-kind"),
    pytest.param(lambda: followon(subsection="Security follow-ups"), id="security"),
    pytest.param(lambda: followon(edit=lambda t, b: (t, b + "\n\n- **Severity**: high")), id="high-severity"),
    pytest.param(lambda: followon(version="v4.14.2"), id="wrong-ledger-section"),
])
def test_a_deviating_item_is_denied(repo: FollowOn, build: Callable[[], cm.GapItem]) -> None:
    gap = build()
    assert repo.allowed(repo.authority(), gap) is False
    assert cm.migration_gate(repo.rctx(), repo.authority(), (4, 14), gap.gid, gap) == (
        "unmet", "migration-not-approved")


@pytest.mark.parametrize("member", [
    pytest.param({"plan_sha256": "0" * 64}, id="wrong-hash"),
    pytest.param({"version": "v4.14.9"}, id="unbound-member"),
])
def test_an_authority_that_does_not_bind_the_plan_is_denied(repo: FollowOn, member: dict) -> None:
    assert repo.allowed(repo.authority(**member), followon()) is False


def test_a_plan_changed_after_freezing_is_denied(repo: FollowOn) -> None:
    repo.write(PLAN_REL, FROZEN_TEXT + "\nA new unapproved instruction.\n")
    assert repo.allowed(repo.authority(), followon()) is False


@pytest.mark.parametrize("task, mutate", [
    pytest.param("T003", lambda text: text, id="non-recording-task"),
    pytest.param("T004", lambda text: text + "\n- [ ] T004 File arbitrary scope as a known gap " + GAPS + "\n",
                 id="duplicate-task"),
    pytest.param("T004", lambda text: text.replace(f"as a known gap {GAPS}", "as a known gap " + GAPS15),
                 id="wrong-task-ledger-placement"),
])
def test_no_canonical_entry_for_a_non_canonical_task(task: str, mutate: Callable[[str], str]) -> None:
    text = mutate(FROZEN_TEXT)
    assert cm.planned_followon_entry(ck, frozen_plan(text), task, ck.plan_hash_text(text)) is None


def test_the_member_projection_is_recognized(repo: FollowOn) -> None:
    view = ck.project(repo.authority(), VERSION)
    assert view is not None and view["scope"] == "member" and view["version"] == VERSION
    assert repo.allowed(view, followon()) is True


def test_recognition_changes_no_authority_or_budget(repo: FollowOn) -> None:
    record = repo.authority()
    before = copy.deepcopy(record)
    assert repo.allowed(record, followon()) is True
    assert cm.migration_gate(repo.rctx(), record, (4, 14), "DF-84", followon())[0] == "met"
    assert record == before


# --------------------------------------------------------------------------- migration verification


def test_a_migrated_follow_on_verifies_and_stays_open(repo: FollowOn) -> None:
    record = repo.migrated()
    assert repo.verify(record) == ("met", "approved-migration")
    copied = item(repo.read(GAPS15), "DF-1")
    assert copied.state == "open" and copied.title == ": Planned follow-on: the lower-direction modifier"


@pytest.mark.parametrize("alter", [
    pytest.param(resolve_copy, id="falsely-resolved"),
    pytest.param(append_defect, id="appended-defect"),
    pytest.param(change_reason, id="reason-changed"),
])
def test_an_altered_destination_is_denied(repo: FollowOn, alter: Callable[[str, str], str]) -> None:
    record = repo.migrated()
    repo.write(GAPS15, alter(repo.read(GAPS15), "DF-1"))
    assert repo.verify(record) == ("unmet", ALTERED)


def test_a_copy_beyond_the_next_minor_is_denied(repo: FollowOn) -> None:
    record = repo.migrated()
    repo.write("docs/releases/v4/v4.16/known-gaps.md", repo.read(GAPS15).replace("v4.15", "v4.16"))
    repo.remove(GAPS15)
    repo.write(GAPS, repo.read(GAPS).replace("MIGRATED to v4.15.0", "MIGRATED to v4.16.0"))
    assert repo.verify(record) == ("unmet", "migration-target-not-next-minor")


def test_an_ordinary_new_defect_is_denied_and_nothing_is_written(repo: FollowOn) -> None:
    defect = entry_text("DF-86", "T004", lambda t, b: (t, b + "\n\n**Defect**: failed own task"))
    repo.write(GAPS, gaps(INHERITED_ENTRY + entry_text("DF-84", "T004") + entry_text("DF-85", "T005") + defect))
    record, before = repo.authority(), repo.read(GAPS)
    gap = item(before, "DF-86")
    assert cm.migration_gate(repo.rctx(), record, (4, 14), "DF-86", gap) == ("unmet", "migration-not-approved")
    with pytest.raises(mc.Refused) as refused:
        repo.migrate(record, "DF-86")
    assert refused.value.reason == "migration-not-approved"
    assert repo.read(GAPS) == before and not (repo.work / GAPS15).exists()


def test_the_inherited_frozen_id_path_is_unchanged(repo: FollowOn) -> None:
    record = repo.authority()
    gap = item(repo.read(GAPS), "DF-1")
    assert cm.migration_gate(repo.rctx(), record, (4, 14), "DF-1", gap) == ("met", "approved")
    # The planned-follow-on reason rule never narrows an ordinary frozen id.
    assert repo.migrate(record, "DF-1", "vendor-feature").new_gid == "DF-1"


def test_migration_leaves_the_83_ids_and_budgets_unchanged(repo: FollowOn) -> None:
    record = repo.authority()
    before = copy.deepcopy(record)
    mc.apply_migration(repo.migrate(record))
    assert repo.verify(record) == ("met", "approved-migration")
    assert record == before
    assert len(record["approvals"]["classes"][0]["bound"]) == 83


# --------------------------------------------------------------------------- archive


def test_a_real_archive_repair_keeps_the_original_body(repo: FollowOn) -> None:
    record, archived = repo.archive()
    gap = item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")
    assert ck.plan_hash_text(archived) != FROZEN
    assert (gap.title, gap.body.strip()) == canonical("T004")
    rctx = repo.rctx()
    calls = spy(rctx)
    assert cm.planned_followon(rctx, record, (4, 14), gap) is True
    shows = [argv for argv in calls if "show" in argv]
    assert shows and all(argv[-1].startswith(repo.start + ":") for argv in shows)


def test_the_real_projection_preserves_the_exact_anchor(repo: FollowOn) -> None:
    record, _ = repo.archive()
    view = ck.project(record, VERSION)
    assert view is not None and view["version"] == VERSION and view["member_start_head"] == repo.start
    assert repo.allowed(view, item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")) is True


def _project_wrong_version(record: dict) -> dict:
    view = ck.project(record, VERSION)
    assert view is not None
    return {**view, "version": "v4.14.9"}


def _without_member_start(record: dict) -> dict:
    del record["members"][0]["start_head"]
    return record


@pytest.mark.parametrize("change, history_read", [
    pytest.param(lambda r, repo: _project_wrong_version(r), False, id="wrong-projected-member-version"),
    pytest.param(lambda r, repo: _without_member_start(r), False, id="missing-signed-member-start"),
    pytest.param(lambda r, repo: r["members"][0].update(start_head="HEAD~1") or r, False, id="non-oid-signed-start"),
    pytest.param(lambda r, repo: r["members"][0].update(start_head=repo.head()) or r, True, id="other-real-commit"),
    pytest.param(lambda r, repo: r["members"][0].update(start_head="b" * 40) or r, True, id="unknown-commit"),
    pytest.param(lambda r, repo: r["approvals"].update(classes=r["approvals"]["classes"][:-1]) or r, False,
                 id="missing-archive-authority"),
    pytest.param(lambda r, repo: r["members"][0].update(plan_path=PLAN_REL) or r, False,
                 id="wrong-current-plan-path"),
])
def test_an_archive_authority_without_the_signed_anchor_is_denied(
    repo: FollowOn, change: Callable[[dict, FollowOn], dict], history_read: bool,
) -> None:
    record, _ = repo.archive()
    gap = item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")
    rctx = repo.rctx()
    calls = spy(rctx)
    assert cm.planned_followon(rctx, change(record, repo), (4, 14), gap) is False
    assert any("show" in argv for argv in calls) is history_read


def test_an_active_tree_still_present_is_denied_without_reading_history(repo: FollowOn) -> None:
    record, _ = repo.archive()
    repo.write(f"{ACTIVE}/README.md", "# v4.14\n")
    rctx = repo.rctx()
    calls = spy(rctx)
    assert cm.planned_followon(rctx, record, (4, 14), item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")) is False
    assert not any("show" in argv for argv in calls)


def test_a_changed_archived_task_is_denied(repo: FollowOn) -> None:
    record, archived = repo.archive()
    changed = archived.replace("File the lower-direction modifier", "File a different opportunity")
    assert changed != archived
    repo.write(f"{ARCHIVE}/plans/{NAME}", changed)
    record["members"][0]["plan_sha256"] = ck.plan_hash_text(changed)
    assert repo.allowed(record, item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")) is False


@pytest.mark.parametrize("files", [
    pytest.param({PLAN_REL: FROZEN_TEXT + "\nChanged requirements.\n"}, id="changed-history"),
    pytest.param({f"docs/v4/v4.14/plans/{NAME}": FROZEN_TEXT}, id="ambiguous-history"),
])
def test_a_start_head_without_one_exact_original_is_denied(repo: FollowOn, files: dict[str, str]) -> None:
    anchor = repo.variant(files)
    record, _ = repo.archive()
    gap = item(repo.read(f"{ARCHIVE}/known-gaps.md"), "DF-84")
    assert repo.allowed(record, gap) is True  # control: the signed start still recovers it
    record["members"][0]["start_head"] = anchor
    assert repo.allowed(record, gap) is False


@pytest.mark.parametrize("edit", [
    pytest.param(lambda t, b: (t, b + "\n\n**Historical head**: " + "c" * 40), id="altered-historical-body"),
    pytest.param(lambda t, b: (t, re.sub(r"(Frozen task sha256\*\*: )[0-9a-f]+", r"\g<1>" + "0" * 64, b)),
                 id="wrong-original-task-hash"),
])
def test_an_altered_entry_is_denied_after_archive(repo: FollowOn, edit: Edit) -> None:
    record, _ = repo.archive()
    assert repo.allowed(record, followon(edit=edit)) is False


# --------------------------------------------------------------------------- write preflight


@pytest.mark.parametrize("reused", [False, True], ids=["new-copy", "reused-copy"])
def test_an_open_canonical_copy_is_accepted(repo: FollowOn, reused: bool) -> None:
    record = repo.authority()
    if reused:
        source = repo.read(GAPS)
        mc.apply_migration(repo.migrate(record))
        repo.write(GAPS, source)  # the source write was lost; the target copy exists
    plan = repo.migrate(record)
    assert plan.reused is reused and plan.new_gid == "DF-1"
    assert cm.planned_followon_copy("v4.14", plan.item, item(plan.target_after, "DF-1"))


@pytest.mark.parametrize("reason", ["vendor-feature", "user-credential"])
def test_a_wrong_reason_is_refused_before_any_copy(
    repo: FollowOn, monkeypatch: pytest.MonkeyPatch, reason: str,
) -> None:
    def never(*_args: object, **_kwargs: object) -> mc.MigrationPlan:
        raise AssertionError("the copy was computed before the reason was checked")

    monkeypatch.setattr(mc, "_migration_texts", never)
    with pytest.raises(mc.Refused) as refused:
        repo.migrate(repo.authority(), reason=reason)
    assert refused.value.reason == "planned-followon-reason-invalid"
    assert not (repo.work / GAPS15).exists()


@pytest.mark.parametrize("reused, alter", [
    pytest.param(False, resolve_copy, id="new-closed-copy"),
    pytest.param(True, resolve_copy, id="reused-closed-copy"),
    pytest.param(False, append_defect, id="new-appended-body"),
    pytest.param(True, append_defect, id="reused-noncanonical-copy"),
])
def test_a_closed_or_noncanonical_copy_is_refused(
    repo: FollowOn, monkeypatch: pytest.MonkeyPatch, reused: bool, alter: Callable[[str, str], str],
) -> None:
    record = repo.authority()
    if reused:
        source = repo.read(GAPS)
        mc.apply_migration(repo.migrate(record))
        repo.write(GAPS15, alter(repo.read(GAPS15), "DF-1"))
        repo.write(GAPS, source)
    else:
        real = mc._migration_texts

        def defective(*args: object, **kwargs: object) -> mc.MigrationPlan:
            plan = real(*args, **kwargs)
            return dataclasses.replace(plan, target_after=alter(plan.target_after, plan.new_gid))

        monkeypatch.setattr(mc, "_migration_texts", defective)
    before = [(repo.work / rel).read_bytes() if (repo.work / rel).exists() else None for rel in (GAPS, GAPS15)]
    with pytest.raises(mc.Refused) as refused:
        repo.migrate(record)
    assert refused.value.reason == ALTERED
    assert [(repo.work / rel).read_bytes() if (repo.work / rel).exists() else None for rel in (GAPS, GAPS15)] == before
