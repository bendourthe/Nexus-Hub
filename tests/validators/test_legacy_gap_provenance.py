"""Legacy recording tasks need immutable publication proof; unknown debt stays unknown."""
from __future__ import annotations

import copy
import dataclasses

import pytest

from .test_gap_migration_and_archive import Close, GAPS05, ledger, section
from .test_check_plan_completion import _isolated_git_config  # noqa: F401
from .test_completion_minor_record import _no_transport_overrides  # noqa: F401

import check_plan_completion as ck
import completion_minor as cm
import minor_close as mc

PLAN = "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"
TITLE = "Large worker trial requires another host"
ENTRY = (
    f"#### DF-2 - {TITLE}\n\n"
    "- **Source phase**: v0.5.2 Phase 1, T003 (planned follow-on record, not an implementation of the trial).\n"
    "- **Plan reference**: [trial](plans/v0.5.2-alpha.md), T003.\n"
    "- **Reason**: The required paired trial cannot run on this host.\n"
    "- **Owner**: Maintainer with the larger host.\n"
    "- **Suggested next step**: Run the paired trial on the larger host.\n"
    "- **Scope disposition**: The plan's provisional DF-1 maps to DF-2 because inherited DF-1 already exists.\n\n"
)
FROZEN_PLAN = (
    "# Trial\n\n**Version**: v0.5.2\n**Status**: queued\n**Slug**: alpha\n\n"
    "## Phase 1: Preflight\n\n#### 1.1 - Record the deferred trial\n\n"
    f"- [x] T003 Create the v0.5 ledger with the large worker deferral {GAPS05}\n\n"
    "**Objective**: Record the trial that needs another host.\n\n**Prompt**:\n"
    f"> Create `{GAPS05}` in the heading format. Add `DF-1 - {TITLE}`. Reason: host unavailable. "
    "Suggested next step: run the trial on the larger host. Confirm the ledger parses.\n"
)


def test_immutable_ledger_cache_is_context_local_defensive_and_budget_bound(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, ENTRY)))
    repo.commit("publication")
    oid = repo.head()
    ctx = repo.rctx()
    calls = []
    run = ctx.run
    monkeypatch.setattr(ctx, "run", lambda argv, cwd=None: (calls.append(argv), run(argv, cwd))[1])
    assert cm.items_at(ctx, oid, (0, 5), "DF-2")[0] == "met"
    count = len(calls)
    found = cm.items_at(ctx, oid, (0, 5), "DF-2")[1]
    found[0].body = "changed by caller"
    assert cm.existed_at(ctx, oid, (0, 5), "DF-2") == "met"
    assert cm.items_at(ctx, oid, (0, 5), "DF-2")[1][0].body != "changed by caller"
    assert len(calls) == count
    assert cm.items_at(repo.rctx(), oid, (0, 5), "DF-2")[1][0].body != "changed by caller"
    assert cm.items_at(ctx, "0" * 40, (0, 5), "DF-2")[0] == "cannot-verify"
    # Symbolic refs must see later commits rather than reuse an immutable snapshot.
    assert cm.items_at(ctx, "HEAD", (0, 5), "DF-2")[0] == "met"
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, "")))
    repo.commit("remove item")
    assert cm.items_at(ctx, "HEAD", (0, 5), "DF-2")[0] == "unmet"
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, "- DF-2: Existing debt in an unsupported row\n")))
    repo.commit("malformed history")
    assert cm.items_at(ctx, repo.head(), (0, 5), "DF-2")[0] == "cannot-verify"
    ctx.budget = ck.Budget(0)
    assert cm.items_at(ctx, oid, (0, 5), "DF-2")[0] == "cannot-verify"


def test_failed_history_read_is_retried(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, ENTRY)))
    repo.commit("publication")
    ctx, oid = repo.rctx(), repo.head()
    run = ctx.run
    monkeypatch.setattr(ctx, "run", lambda argv, cwd=None: (-1, ""))
    assert cm.items_at(ctx, oid, (0, 5), "DF-2")[0] == "cannot-verify"
    monkeypatch.setattr(ctx, "run", run)
    assert cm.items_at(ctx, oid, (0, 5), "DF-2")[0] == "met"


def test_legacy_recording_task_requires_bound_identity_and_unchanged_published_body(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    repo.write(PLAN, FROZEN_PLAN)
    inherited = "#### DF-1 - Existing unrelated follow-up\n\n- **Reason**: existing debt.\n\n"
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, inherited)))
    repo.commit("approved start")
    start = repo.head()
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 0, inherited + ENTRY)))
    repo.commit("record planned deferral")
    repo.integrate()
    repo.ship("v0.5.2")
    record = repo.forge(bound=("v0.5#DF-2",), start_head=start)
    gap = next(i for i in cm.parse_ledger(repo.read(GAPS05)) if i.gid == "DF-2")
    assert cm.migration_gate(repo.rctx(), record, (0, 5), gap.gid, gap) == ("met", "planned-follow-on")
    for altered in [
        dataclasses.replace(gap, kind="BG"),
        dataclasses.replace(gap, subsection="Security follow-ups"),
        dataclasses.replace(gap, body=gap.body + "\n- **Severity**: high"),
        dataclasses.replace(gap, body=gap.body + "\nNew defect."),
        dataclasses.replace(gap, body=gap.body.replace("Phase 1, T003", "Phase 1, T004")),
        dataclasses.replace(gap, body=gap.body.replace("provisional DF-1 maps to DF-2", "provisional DF-1 maps to DF-3")),
        dataclasses.replace(gap, title=" - Another opportunity"),
        dataclasses.replace(gap, section="v0.5.10"),
    ]:
        assert cm.migration_gate(repo.rctx(), record, (0, 5), gap.gid, altered)[0] != "met"
    unbound = copy.deepcopy(record)
    unbound["approvals"]["classes"][0]["bound"] = []
    assert cm.migration_gate(repo.rctx(), unbound, (0, 5), gap.gid, gap)[0] != "met"
    unknown = copy.deepcopy(record)
    unknown["start_head"] = "0" * 40
    assert cm.migration_gate(repo.rctx(), unknown, (0, 5), gap.gid, gap)[0] == "cannot-verify"
    with monkeypatch.context() as patch:
        patch.setattr(cm, "completion_anchor", lambda *args, _decline_evaluation=None: ("cannot-verify", None))
        assert cm.migration_gate(repo.rctx(), record, (0, 5), gap.gid, gap)[0] == "cannot-verify"
    with pytest.raises(mc.Refused):
        mc.plan_migration(repo.rctx(), "v0.5", record, "v0.5#DF-2", "vendor-feature", "proof", "2026-10-30")
    migration = mc.plan_migration(repo.rctx(), "v0.5", record, "v0.5#DF-2", "user-deferred", "frozen recording task", "2026-10-30")
    repo.write(migration.source.rel, migration.source_after)
    repo.write(migration.target_rel, migration.target_after)
    ledgers, unreadable = cm.load_ledgers(repo.work)
    assert not unreadable
    source_ledger = next(ledger for ledger in ledgers if ledger.rel == GAPS05)
    migrated = next(i for i in source_ledger.items if i.gid == gap.gid)
    for view in (record, ck.project(record, "v0.5.2")):
        assert cm.verify_migration(repo.rctx(), view, "v0.5", ledgers, source_ledger, migrated) == ("met", "approved-migration")
    copies = cm.parse_ledger(migration.target_after)
    assert cm.planned_followon_copy("v0.5", migrated, copies[0], source_rel=GAPS05, target_rel=migration.target_rel)
    assert not cm.planned_followon_copy("v0.5", migrated, dataclasses.replace(copies[0], body=copies[0].body + "\nChanged"), source_rel=GAPS05, target_rel=migration.target_rel)
    # An instruction appended after the frozen task is never authenticated by the publication alone.
    repo.write(PLAN, FROZEN_PLAN + "\n- [ ] T003 Create another opportunity\n")
    assert cm.migration_gate(repo.rctx(), record, (0, 5), gap.gid, gap)[0] != "met"


def test_wrapped_provenance_cannot_hide_a_second_destination(tmp_path):
    from .test_gap_migration_and_archive import WN3, GAPS06
    source_text = ledger("v0.5", section("v0.5.2", 1, WN3))
    source_items, problems = cm.parse_ledger_full(source_text)
    assert not problems
    source = cm.Ledger(tmp_path / GAPS05, GAPS05, (0, 5), "active", source_text, source_items)
    copies = (
        "#### WN-1: First destination\n\n"
        "- **Migrated from**: v0.5#WN-3 on 2026-10-30 (reason: vendor-feature)\n\n"
        "#### WN-2: Second destination\n\n"
        "**Migrated from**:\n v9.9#WN-9 **Migrated from**: v0.5#WN-3 on 2026-10-30 (reason: vendor-feature)\n\n"
    )
    target_text = ledger("v0.6", section("v0.6.0", 2, copies))
    target_items, problems = cm.parse_ledger_full(target_text)
    assert not problems
    target = cm.Ledger(tmp_path / GAPS06, GAPS06, (0, 6), "active", target_text, target_items)
    cache = {}
    for _ in range(2):
        assert cm.migration_copy_status([source, target], "v0.6.0", source, source_items[0], proof_cache=cache)[0] == "migration-target-ambiguous"


@pytest.mark.parametrize("extra_change", [False, True])
def test_archived_plan_replay_uses_the_same_navigation_repair(tmp_path, extra_change):
    from types import SimpleNamespace

    target = tmp_path / "docs/archives/v0/v0.4/development/feasibility.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Original feasibility\n", encoding="utf-8")
    href = "../archives/v0/v0.4/development/feasibility.md"
    original = FROZEN_PLAN + "\n[Earlier record](" + href + ")\n"
    repaired = original.replace(href, "../../v0.4/development/feasibility.md")
    repaired = repaired.replace(
        "deferral " + GAPS05,
        "deferral " + GAPS05.replace("docs/releases/", "docs/archives/", 1),
    )
    if extra_change:
        repaired += "\nChanged study scope.\n"
    rel = "docs/archives/v0/v0.5/plans/v0.5.2-alpha.md"
    plan = cm.Plan(rel, "v0.5.2", (0, 5, 2), "complete", "alpha", repaired)
    start = "1" * 40

    def run(argv):
        assert argv[:4] == ["git", "-C", str(tmp_path), "show"]
        return (0, original) if argv[-1] == start + ":" + PLAN else (1, "")

    context = SimpleNamespace(root=tmp_path, git="git", run=run)
    record = {"scope": "minor", "approvals": {"classes": [{"class": "archive-minor"}]}}
    member = {
        "plan_path": rel,
        "plan_sha256": ck.plan_hash_text(repaired),
        "start_head": start,
    }
    found = cm.archived_followon_plan(context, record, member, plan, ck)
    if extra_change:
        assert found is None
    else:
        assert found is not None and found.text == original
