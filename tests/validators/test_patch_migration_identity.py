"""Patch-qualified history distinguishes identical bodies without hiding duplicates."""

from types import SimpleNamespace

import pytest

from .test_gap_migration_and_archive import cm, mc


def sample(tmp_path):
    source_text = "# Gaps\n\n"
    for version in ["v1.2.1", "v1.2.2"]:
        source_text += f"## {version}\n\n### Open Items\n\n#### DF-17 - Same obligation - MIGRATED to v2.0.0\n\n- **Reason**: Unchanged. Out of scope.\n\n"
    items, problems = cm.parse_ledger_full(source_text)
    assert not problems
    source = cm.Ledger(
        tmp_path / "source",
        "docs/archives/v1/v1.2/known-gaps.md",
        (1, 2),
        "archive",
        source_text,
        items,
    )
    target_text = "# Gaps\n\n## v2.0.0\n\n### Open Items\n\n### Resolved\n\n"
    for gid, item in zip(["DF-65", "DF-72"], items):
        target_text = mc._insert_entry(
            target_text,
            "v2.0.0",
            item,
            gid,
            item.body,
            [
                f"- **Migrated from**: {item.section}#DF-17 on 2026-10-31 (reason: user-deferred)"
            ],
        )
    target_items, problems = cm.parse_ledger_full(target_text)
    assert not problems
    target = cm.Ledger(
        tmp_path / "target",
        "docs/releases/v2/v2.0/known-gaps.md",
        (2, 0),
        "active",
        target_text,
        target_items,
    )
    return source, target


def verify(source, target, item):
    return cm.verify_migration(
        SimpleNamespace(migration_proof_lines={}),
        None,
        "v2.0",
        [source, target],
        source,
        item,
    )


def test_identical_bodies_have_distinct_recorded_patch_origins(tmp_path):
    source, target = sample(tmp_path)
    assert source.items[0].body == source.items[1].body
    for item in source.items:
        reason, _found = cm.migration_copy_status(
            [source, target], "v2.0.0", source, item
        )
        assert reason == "migration-target-ambiguous"
        assert verify(source, target, item) == ("met", "in-scope-copy")


@pytest.mark.parametrize(
    "change",
    [
        "duplicate-exact-origin",
        "missing-qualified-origin",
        "aliased-source-section",
        "changed-body",
        "unique-source-id",
    ],
)
def test_exact_patch_repair_does_not_weaken_other_identity_checks(tmp_path, change):
    source, target = sample(tmp_path)
    if change == "duplicate-exact-origin":
        target.text = target.text.replace("v1.2.2#DF-17", "v1.2.1#DF-17")
    elif change == "missing-qualified-origin":
        target.text = target.text.replace("v1.2.1#DF-17", "v1.2#DF-17")
    elif change == "aliased-source-section":
        source.text = source.text.replace("## v1.2.2", "## v1.2.1 detail")
        source.items = cm.parse_ledger(source.text)
    elif change == "unique-source-id":
        source.text = source.text.split("## v1.2.2")[0]
        source.items = cm.parse_ledger(source.text)
    else:
        source.items[0].body += "Different obligation.\n"
    target.items = cm.parse_ledger(target.text)
    assert verify(source, target, source.items[0])[0] != "met"
