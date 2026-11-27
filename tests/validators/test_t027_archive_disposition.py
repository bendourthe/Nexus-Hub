"""Archive consumers honor only the exact authenticated unmeasured task disposition."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import minor_close as close


@pytest.mark.parametrize("consumer", ["minor", "member"])
@pytest.mark.parametrize(
    ("version", "text", "accepted", "refused"),
    [
        ("v4.15.9", "- [ ] T027 measured trial\n", True, False),
        ("v4.15.9", "- [ ] T027 measured trial\n", False, True),
        ("v4.15.9", "- [ ] T027 measured trial\n- [ ] T028 other duty\n", True, True),
        ("v4.15.8", "- [ ] T027 another task\n", True, True),
        ("v4.15.9", "- [x] T027 completed task\n", False, False),
    ],
)
def test_archive_consumers_keep_other_unchecked_tasks_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    consumer: str, version: str, text: str, accepted: bool, refused: bool,
) -> None:
    plan = close.cm.Plan("docs/plan.md", version, (4, 15, 9), "in-progress", "fixture", text)
    member = {"version": version}
    record = {"members": [member]}
    rctx = SimpleNamespace(root=tmp_path, budget=close.ck.Budget(10))
    monkeypatch.setattr(close.ck, "Context", lambda *_args: SimpleNamespace(text=text))
    monkeypatch.setattr(close.ck, "project", lambda *_args: {"version": version})

    def disposition(_ck: object, ctx: object, projected: object, *, task_id: str) -> bool:
        assert ctx.text == text
        assert projected == {"version": version}
        return accepted and task_id == "T027" and version == "v4.15.9"

    monkeypatch.setattr(close.cm, "t027_task_deferred", disposition, raising=False)
    monkeypatch.setattr(close.cm, "scan_plans", lambda *_args: [plan])
    monkeypatch.setattr(close.cm, "effective_members", lambda *_args: [member])
    monkeypatch.setattr(close.cm, "hosting_repo", lambda *_args: "bendourthe/Nexus-Hub")
    monkeypatch.setattr(close.cm, "shipped", lambda *_args: "met")
    monkeypatch.setattr(
        close.cm, "evaluate_member",
        lambda *_args: SimpleNamespace(exhausted=False, lines=[("task.T027", "deferred")]),
    )
    result = (close.plan_refusals(rctx, "v4.15", record) if consumer == "minor"
              else close._member_incomplete_refusals(rctx, record, member, plan))
    assert bool(result) is refused


def test_unverifiable_disposition_keeps_archive_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = close.cm.Plan("docs/plan.md", "v4.15.9", (4, 15, 9), "in-progress", "fixture", "- [ ] T027 trial\n")
    rctx = SimpleNamespace(root=tmp_path, budget=close.ck.Budget(10))
    monkeypatch.setattr(close.ck, "Context", lambda *_args: SimpleNamespace(text=plan.text))
    monkeypatch.setattr(close.ck, "project", lambda *_args: {})

    def unavailable(*_args: object, **_kwargs: object) -> bool:
        raise ValueError("unverifiable receipt")

    monkeypatch.setattr(close.cm, "t027_task_deferred", unavailable, raising=False)
    assert close._has_unaccepted_tasks(rctx, {"members": []}, plan)


def test_migration_rejects_an_unapproved_destination_before_loading_ledgers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rctx = SimpleNamespace(root=tmp_path, budget=close.ck.Budget(10))
    monkeypatch.setattr(close.cm, "amendment_gap_grants", lambda _record: [
        {"id": "v4.15#DF-80", "reason": "user-deferred", "target_version": "v4.17.0"},
    ])

    def should_not_read(*_args: object) -> None:
        pytest.fail("unapproved destination must refuse before planning ledger writes")

    monkeypatch.setattr(close.cm, "load_ledgers", should_not_read)
    with pytest.raises(close.Refused) as refused:
        close.plan_migration(rctx, "v4.15", {}, "v4.15#DF-80", "user-deferred", "fixture", "2026-11-22")
    assert refused.value.reason == "migration-destination-not-approved"


@pytest.mark.parametrize(
    ("reason", "destination", "refusal"),
    [
        ("vendor-feature", "v4.16.0", "migration-reason-not-approved"),
        ("user-credential", "v4.16.0", "migration-reason-not-approved"),
        ("user-deferred", "v4.17.0", "migration-destination-not-approved"),
    ],
)
def test_signed_trial_terms_refuse_before_any_ledger_planning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    reason: str, destination: str, refusal: str,
) -> None:
    source_path, target_path = tmp_path / "source.md", tmp_path / "target.md"
    source_path.write_text("source sentinel", encoding="utf-8")
    target_path.write_text("target sentinel", encoding="utf-8")
    item = SimpleNamespace(gid="DF-80", state="open")
    ledger = SimpleNamespace(minor=(4, 15), problems=[], items=[item], rel="source.md")
    rctx = SimpleNamespace(root=tmp_path, budget=close.ck.Budget(10))
    monkeypatch.setattr(close.cm, "T027_FIELD", "fixture_disposition", raising=False)
    monkeypatch.setattr(close.cm, "amendment_gap_grants", lambda *_args: [])
    monkeypatch.setattr(close.cm, "historical_supplements", lambda *_args: [])
    monkeypatch.setattr(close.cm, "load_ledgers", lambda *_args: ([ledger], []))
    monkeypatch.setattr(close.cm, "migration_gate", lambda *_args: ("met", "t027-unmeasured"))

    def should_not_plan(*_args: object) -> None:
        pytest.fail("signed trial terms must refuse before ledger planning")

    monkeypatch.setattr(close, "_target_ledger", should_not_plan)
    record = {"fixture_disposition": {"page": {"gap": {
        "migration_reason": "user-deferred", "target_version": destination,
    }}}}
    with pytest.raises(close.Refused) as refused:
        close.plan_migration(rctx, "v4.15", record, "v4.15#DF-80", reason, "fixture", "2026-11-22")
    assert refused.value.reason == refusal
    assert source_path.read_text(encoding="utf-8") == "source sentinel"
    assert target_path.read_text(encoding="utf-8") == "target sentinel"
