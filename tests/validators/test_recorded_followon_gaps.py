"""Recorded follow-on gaps: a frozen task that records known gaps outside the exact template.

Frozen plans written before the `File <scope> as a known gap <ledger>` template still carry
tasks whose whole job is to record future work as a known gap. `cm.recorded_followon_task`
recognizes such a task only from its frozen wording, and `cm.planned_followon` then accepts an
entry that binds the plan hash, the task hash, the task's real phase and the plan file, names a
scope the frozen plan states verbatim, and is the only entry with that task and title. The
suite runs against the real frozen v4.14.2 plan and proves recognition, every deviation that
must stay non-deferrable, and that the exact-template path is unchanged.
"""

from __future__ import annotations

import re
import sys
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

VERSION = "v4.14.2"
NAME = "v4.14.2-adoption-harness-decisions-design-rules-and-cache-stability.md"
ACTIVE = "docs/releases/v4/v4.14"
PLAN_REL = f"{ACTIVE}/plans/{NAME}"
GAPS = f"{ACTIVE}/known-gaps.md"
FROZEN = "5e5d95b9f3dc65d0fbbbf5ee3f40defc65cd6a30caebaf8361b70a532413d892"
FROZEN_TEXT = (REPO_ROOT / PLAN_REL).read_text(encoding="utf-8")
INHERITED = [f"v4.14#DF-{n}" for n in range(1, 84)]
INHERITED_ENTRY = "#### DF-1: Original inherited item\n\n- **Reason**: inherited from v4.13\n\n"
HOOK = "the parked write-containment hook"
REFACTOR = "the refactor-first rule"
ENUMERATE = "the enumerate-every-copy rule"


def plan(text: str = FROZEN_TEXT) -> cm.Plan:
    return cm.Plan(PLAN_REL, VERSION, (4, 14, 2), "queued", "adoption-harness", text)


def bound(task: str) -> tuple[str, str]:
    found = cm.recorded_followon_task(ck, plan(), task, FROZEN)
    assert found is not None, task
    return found


def entry(gid: str, task: str, scope: str, *, phase: str | None = None, task_hash: str | None = None,
          frozen: str = FROZEN, name: str = NAME, reason: str = "the evaluation kept the rule as guidance",
          step: str = "revisit once a stronger instrument exists.", extra: str = "") -> str:
    real_phase, real_hash = bound(task) if cm.recorded_followon_task(ck, plan(), task, FROZEN) else ("1", "0" * 64)
    body = "\n\n".join([
        "**Disposition**: planned-follow-on (OPEN)",
        f"**Source phase**: {VERSION} Phase {phase or real_phase} {task}",
        f"**Plan reference**: {name}",
        f"**Frozen plan sha256**: {frozen}",
        f"**Frozen task sha256**: {task_hash or real_hash}",
        f"**Reason**: {reason}",
        f"**Suggested next step**: {step}",
    ])
    return f"#### {gid}: Planned follow-on: {scope}\n\n{body}{extra}\n\n"


def gaps(items: str) -> str:
    df_open = sum(1 for i in cm.parse_ledger(items) if i.kind == "DF" and i.state == "open")
    return (
        "# Known Gaps - v4.14\n\n**Project**: demo\n**Status**: in-progress\n**Last updated**: 2026-10-21\n\n"
        f"## {VERSION}\n\n### Summary\n\n| Category | Open | Resolved |\n|---|---|---|\n"
        f"| Deferred (DF) | {df_open} | 0 |\n\n### Open Items\n\n{items}"
        "### Resolved\n\n| ID | Title | Resolved in | Notes |\n|---|---|---|---|\n"
    )


class Recorded(Close):
    """A repository holding the frozen v4.14.2 plan; recorded entries are created during the run."""

    def __init__(self, tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        super().__init__(tmp, monkeypatch)
        self.write(PLAN_REL, FROZEN_TEXT)
        self.write(GAPS, gaps(INHERITED_ENTRY))
        self.commit("v4.14 start")
        self.start = self.head()

    def record_entries(self, items: str) -> str:
        text = gaps(INHERITED_ENTRY + items)
        self.write(GAPS, text)
        self.commit("v4.14.2 records its follow-ons")
        self.integrate()
        return text

    def authority(self, **member: object) -> dict:
        row = {"version": VERSION, "plan_path": PLAN_REL, "plan_sha256": FROZEN, "start_head": self.start,
               "source_branch": f"feat/{VERSION}-adoption-harness", "target_branch": "develop"}
        row.update(member)
        return {
            "schema": ck.SCHEMA_MINOR, "scope": "minor", "minor": "v4.14", "repo": "acme/demo",
            "start_head": self.start, "nonce": "nonce-v4.14", "members": [row],
            "approvals": {"target_branch": "develop", "spend_caps": {"usd": 20}, "classes": [
                {"class": "gap-migration", "bound": list(INHERITED), "named": []},
                {"class": "minor-close-pr", "bound": 3},
            ]},
        }

    def allowed(self, text: str, gid: str, **member: object) -> bool:
        found = [i for i in cm.parse_ledger(text) if i.gid == gid]
        assert len(found) == 1, gid
        return cm.planned_followon(self.rctx(), self.authority(**member), (4, 14), found[0])

    def gate(self, text: str, gid: str) -> tuple[str, str]:
        found = [i for i in cm.parse_ledger(text) if i.gid == gid][0]
        return cm.migration_gate(self.rctx(), self.authority(), (4, 14), gid, found)


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Recorded:
    return Recorded(tmp_path, monkeypatch)


def test_the_frozen_plan_hash_is_the_recorded_v4142_hash() -> None:
    assert ck.plan_hash_text(FROZEN_TEXT) == FROZEN


@pytest.mark.parametrize("task, phase", [("T002", "1"), ("T023", "5")])
def test_only_the_frozen_recording_tasks_qualify(task: str, phase: str) -> None:
    assert bound(task)[0] == phase
    qualifying = [m[1] for m in re.finditer(r"^- \[[ xX]\] (T\d{3,}) ", FROZEN_TEXT, re.MULTILINE)
                  if cm.recorded_followon_task(ck, plan(), m[1], FROZEN)]
    assert qualifying == ["T002", "T023"]


def test_a_task_line_recording_into_the_ledger_is_recognized(repo: Recorded) -> None:
    text = repo.record_entries(entry("DF-84", "T002", HOOK))
    assert repo.allowed(text, "DF-84") is True
    assert repo.gate(text, "DF-84") == ("met", "planned-follow-on")


def test_a_prompt_that_records_gaps_allows_one_entry_per_named_scope(repo: Recorded) -> None:
    text = repo.record_entries(entry("DF-84", "T023", REFACTOR) + entry("DF-85", "T023", ENUMERATE))
    assert repo.allowed(text, "DF-84") is True
    assert repo.allowed(text, "DF-85") is True


@pytest.mark.parametrize("items, gid", [
    pytest.param(lambda: entry("DF-84", "T002", "an unrelated new defect in the grader"), "DF-84", id="scope-not-in-plan"),
    pytest.param(lambda: entry("DF-84", "T002", "hook"), "DF-84", id="scope-too-short"),
    pytest.param(lambda: entry("DF-84", "T001", "Record predecessor states"), "DF-84", id="non-recording-task"),
    pytest.param(lambda: entry("DF-84", "T026", "Known-gaps reconciliation"), "DF-84", id="reconciliation-task"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, phase="2"), "DF-84", id="wrong-phase"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, task_hash="1" * 64), "DF-84", id="wrong-task-hash"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, frozen="2" * 64), "DF-84", id="wrong-plan-hash"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, name="another-plan.md"), "DF-84", id="wrong-plan-reference"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, reason=" "), "DF-84", id="empty-reason"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, step="no closing period"), "DF-84", id="step-without-period"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, extra="\n\n**Defect**: actual new breakage"), "DF-84",
                 id="appended-field"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK, extra="\n\n- **Severity**: high"), "DF-84", id="high-severity"),
    pytest.param(lambda: entry("BG-1", "T002", HOOK), "BG-1", id="bug-kind"),
    pytest.param(lambda: entry("DF-84", "T002", HOOK) + entry("DF-85", "T002", HOOK), "DF-84", id="duplicate-title"),
])
def test_a_deviating_entry_stays_non_deferrable(repo: Recorded, items, gid: str) -> None:
    text = repo.record_entries(items())
    assert repo.allowed(text, gid) is False
    assert repo.gate(text, gid) == ("unmet", "migration-not-approved")


@pytest.mark.parametrize("member", [
    pytest.param({"plan_sha256": "0" * 64}, id="unbound-hash"),
    pytest.param({"version": "v4.14.9"}, id="unbound-member"),
])
def test_an_authority_that_does_not_bind_the_plan_is_denied(repo: Recorded, member: dict) -> None:
    text = repo.record_entries(entry("DF-84", "T002", HOOK))
    assert repo.allowed(text, "DF-84", **member) is False


def test_a_plan_changed_after_freezing_is_denied(repo: Recorded) -> None:
    text = repo.record_entries(entry("DF-84", "T002", HOOK))
    repo.write(PLAN_REL, FROZEN_TEXT + "\nA new unapproved instruction.\n")
    assert repo.allowed(text, "DF-84") is False


def test_the_exact_template_tasks_are_unchanged() -> None:
    v4141 = REPO_ROOT / ACTIVE / "plans" / "v4.14.1-adoption-effort-allocation.md"
    text = v4141.read_text(encoding="utf-8")
    original = cm.Plan(str(v4141.relative_to(REPO_ROOT)).replace("\\", "/"), "v4.14.1", (4, 14, 1), "queued", "x", text)
    frozen = ck.plan_hash_text(text)
    assert cm.planned_followon_entry(ck, original, "T004", frozen) is not None
    # A templated task keeps its derived reason: the free-text form never applies to it.
    assert cm.recorded_followon_task(ck, original, "T004", frozen) is None
    assert cm.planned_followon_entry(ck, plan(), "T002", FROZEN) is None
