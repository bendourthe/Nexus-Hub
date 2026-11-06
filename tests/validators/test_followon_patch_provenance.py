"""A follow-on copy retains the exact patch provenance accepted by the carry reader."""

from __future__ import annotations

from dataclasses import replace

import pytest

from .test_planned_followon_gaps import (
    GAPS15,
    VERSION,
    FollowOn,
    _isolated_git_config,  # noqa: F401 (autouse fixture re-exported)
    _no_transport_overrides,  # noqa: F401 (autouse fixture re-exported)
    cm,
    followon,
    item,
)


def copy_pair(label: str) -> tuple[cm.GapItem, cm.GapItem]:
    source = followon()
    body = source.body.strip() + (
        f"\n\n- **Migrated from**: {label}#DF-84 on 2026-11-05 (reason: user-deferred)"
        "\n- **Migration evidence**: Frozen recording task"
    )
    return source, replace(source, gid="DF-1", body=body)


@pytest.mark.parametrize("label", ["v4.14", VERSION])
def test_exact_minor_or_owned_patch_copy_is_accepted(label: str) -> None:
    source, copied = copy_pair(label)
    assert cm.planned_followon_copy("v4.14", source, copied)


@pytest.mark.parametrize("label", ["v4.14.0", "v4.14.2", "v4.15.1"])
def test_another_patch_cannot_borrow_the_recording_task(label: str) -> None:
    source, copied = copy_pair(label)
    assert not cm.planned_followon_copy("v4.14", source, copied)


@pytest.mark.parametrize("change", [
    "wrong-section", "wrong-source-phase", "duplicate-source-phase", "changed-body",
    "changed-title", "duplicate-provenance", "hidden-provenance", "changed-reason",
])
def test_patch_provenance_keeps_the_canonical_copy_constraints(change: str) -> None:
    source, copied = copy_pair(VERSION)
    if change == "wrong-section":
        source = replace(source, section="v4.14.2")
    elif change == "wrong-source-phase":
        source = replace(source, body=source.body.replace("v4.14.1 Phase", "v4.14.2 Phase"))
        copied = replace(copied, body=copied.body.replace("v4.14.1 Phase", "v4.14.2 Phase"))
    elif change == "duplicate-source-phase":
        extra = "\n\n**Source phase**: v4.14.1 Phase 1 T004"
        source = replace(source, body=source.body.strip() + extra)
        copied = replace(copied, body=copied.body.replace("\n\n- **Migrated from**", extra + "\n\n- **Migrated from**"))
    elif change == "changed-body":
        copied = replace(copied, body=copied.body.replace("**Reason**:", "**Reason**: changed"))
    elif change == "changed-title":
        copied = replace(copied, title=copied.title + " changed")
    elif change == "duplicate-provenance":
        copied = replace(copied, body=copied.body + "\n- **Migrated from**: v4.14.1#DF-84")
    elif change == "hidden-provenance":
        copied = replace(copied, body=copied.body.replace("\n\n- **Migrated from**", "\n\n<!--\n- **Migrated from**") + "\n-->")
    else:
        copied = replace(copied, body=copied.body.replace("reason: user-deferred", "reason: vendor-feature"))
    assert not cm.planned_followon_copy("v4.14", source, copied)


def test_real_migration_accepts_the_same_unchanged_patch_copy_in_both_readers(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = FollowOn(tmp_path, monkeypatch)
    record = repo.migrated()
    text = repo.read(GAPS15).replace("**Migrated from**: v4.14#", f"**Migrated from**: {VERSION}#")
    repo.write(GAPS15, text)
    ledgers, unreadable = cm.load_ledgers(repo.work)
    assert not unreadable
    source = next(ledger for ledger in ledgers if ledger.minor == (4, 14))
    assert cm.plan_migration_met(ledgers, source, item(source.text, "DF-84"))
    assert repo.verify(record) == ("met", "approved-migration")
