"""Migration proof keeps native path semantics without work for unrelated archive prefixes."""
from dataclasses import replace
from pathlib import Path

import pytest

from .test_gap_migration_and_archive import cm, ledger, mc, section


def _copy_case(body: str, copied_body: str | None = None):
    copied_body = body if copied_body is None else copied_body
    source_text = ledger("v4.14", section("v4.14.0", 0,
        "#### WN-1: Fixture work - MIGRATED to v4.15.0\n\n" + body + "\n\n"))
    target_text = ledger("v4.15", section("v4.15.0", 1,
        "#### WN-2: Fixture work\n\n" + copied_body +
        "\n\n- **Migrated from**: v4.14#WN-1 on 2026-11-05 (reason: user-deferred)\n\n"))
    source_items, source_problems = cm.parse_ledger_full(source_text)
    target_items, target_problems = cm.parse_ledger_full(target_text)
    assert not source_problems and not target_problems
    source_rel = "docs/archives/v4/v4.14/known-gaps.md"
    target_rel = "docs/releases/v4/v4.15/known-gaps.md"
    source = cm.Ledger(Path(source_rel), source_rel, (4,14), "archive", source_text, source_items)
    target = cm.Ledger(Path(target_rel), target_rel, (4,15), "active", target_text, target_items)
    return source, target


@pytest.mark.parametrize("tree", cm.ACTIVE_TREES)
@pytest.mark.parametrize("separator", ["/", "\\"])
def test_native_archive_mention_forms_still_reconcile(tree, separator):
    active = tree.format(M=4, m=14)
    archived = "docs/archives/v4/v4.14"
    body = "Evidence root: " + active.replace("/", separator) + separator + "development" + separator + "proof.md"
    copied, count = mc.rewrite_mentions(body, active, archived, markdown=True)
    assert count == 1
    source, target = _copy_case(body, copied)
    assert cm.migration_copy_status([source,target], "v4.15.0", source, source.items[0])[0] == "migration-copy-complete"
    source, target = _copy_case(body, copied + "\nAdditional destination context.")
    assert cm.migration_copy_status([source,target], "v4.15.0", source, source.items[0])[0] == "migration-copy-complete"
    source, target = _copy_case(body, copied.replace("Evidence root:", "Changed root:", 1))
    assert cm.migration_copy_status([source,target], "v4.15.0", source, source.items[0])[0] != "migration-copy-complete"


def test_unrelated_archived_ledgers_do_not_add_mention_rewrite_work(monkeypatch):
    source, target = _copy_case("Preserve this fixture's complete body.")
    original = mc.rewrite_mentions
    calls = []
    def measured(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs)
    monkeypatch.setattr(mc, "rewrite_mentions", measured)
    assert cm.migration_copy_status([source,target], "v4.15.0", source, source.items[0])[0] == "migration-copy-complete"
    baseline = len(calls)
    unrelated = [replace(source, path=Path(f"docs/archives/v3/v3.{number}/known-gaps.md"),
                         rel=f"docs/archives/v3/v3.{number}/known-gaps.md",
                         minor=(3,number), text="", items=[]) for number in range(50)]
    calls.clear()
    assert cm.migration_copy_status([source,target,*unrelated], "v4.15.0", source, source.items[0])[0] == "migration-copy-complete"
    assert len(calls) <= baseline, "Unrelated archived minors caused additional full Markdown rewrites"
