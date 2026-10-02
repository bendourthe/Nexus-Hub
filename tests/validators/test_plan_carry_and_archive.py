"""A one-plan run records the gaps it leaves open and, as its minor's last plan, archives it.

The run goal's last two steps ("record every gap still open in the next version's
known-gaps section" and "when this is the last plan in its version folder, archive
that folder and delete any folder left empty") are checker predicates owned by the
completion contract's "Single-plan carry and archive" section: `gaps.carried`,
`archive.minor`, and `archive.empty-dirs`. These tests drive the real checker and
the real `minor_close.py carry` and `archive --plan` writers against a throwaway
repository with a real run record.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from .test_check_plan_completion import (  # noqa: F401  (autouse fixture)
    EVIDENCE_REL,
    PLAN_REL,
    SECTIONS,
    SESSION,
    Fixture,
    _git,
    _isolated_git_config,
)
from .test_gap_migration_and_archive import BG2, LINK_CHECKER, WN3, ledger, section

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSE = REPO_ROOT / "scripts" / "minor_close.py"
GAPS = "docs/releases/v0/v0.2/known-gaps.md"
NEXT_GAPS = "docs/releases/v0/v0.3/known-gaps.md"
SIBLING = "docs/releases/v0/v0.2/plans/v0.2.1-next.md"
ARCHIVED_PLAN = "docs/archives/v0/v0.2/plans/v0.2.0-demo.md"
PLAN = """# Plan -- Demo

**Version**: v0.2.0
**Slug**: demo
**Status**: {status}

## Phase 1: Build

- [{a}] T001 Build part A src/a.txt
- [{b}] T002 Build part B src/b.txt
"""


def _close(fx: Fixture, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CLOSE), *args], cwd=fx.work, env=fx.env,
                          capture_output=True, text=True, check=False)


def _build(tmp: Path, *classes: dict, sibling: bool = True, items: str = WN3, wn: int = 1, bg: int = 0) -> Fixture:
    """A finished one-plan run whose v0.2.0 section still holds open gaps."""
    fx = Fixture(tmp)
    _git(tmp, "init", "--bare", "-q", "-b", "main", str(fx.remote))
    fx.work.mkdir()
    for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@example.invalid"),
                 ("config", "user.name", "Test"), ("remote", "add", "origin", str(fx.remote)),
                 ("remote", "set-url", "--push", "origin", "https://github.com/acme/demo.git")):
        _git(fx.work, *args)
    fx.write(PLAN_REL, PLAN.format(status="in-progress", a=" ", b=" "))
    fx.write(GAPS, ledger("v0.2", section("v0.2.0", wn, items, bg_open=bg)))
    if sibling:
        fx.write(SIBLING, PLAN.format(status="queued", a=" ", b=" ")
                 .replace("v0.2.0", "v0.2.1").replace("demo", "next"))
    fx.write("CHANGELOG.md", "# Changelog\n")
    _git(fx.work, "add", "-A")
    _git(fx.work, "commit", "-q", "-m", "start")
    approvals = fx.approvals(*classes)
    fx.paste(SESSION, "--approvals", str(approvals))
    created = fx.run("record", "create", PLAN_REL, "--session", SESSION, "--approvals", str(approvals))
    assert created.returncode == 0, created.stderr + created.stdout
    fx.write("src/a.txt", "a\n")
    fx.write("src/b.txt", "b\n")
    fx.write(PLAN_REL, PLAN.format(status="shipped", a="x", b="x"))
    fx.write("CHANGELOG.md", "# Changelog\n\n## [0.2.0] - 2026-09-25\n")
    body = "".join(f"## {name}\n\nDone.\n\n" for name in SECTIONS)
    body += "## Full-suite testing and stabilization\n\n`pytest -q`: 3 passed, including tests/test_a.py.\n"
    fx.write(EVIDENCE_REL, "# Evidence\n\n" + body)
    fx.write("tests/test_a.py", "def test_a():\n    assert True\n")
    _commit_and_ship(fx)
    return fx


def _commit_and_ship(fx: Fixture, message: str = "work") -> None:
    _git(fx.work, "add", "-A")
    _git(fx.work, "commit", "-q", "-m", message)
    _git(fx.work, "push", "-q", str(fx.remote), "main")
    _git(fx.work, "tag", "-f", "v0.2.0")
    _git(fx.work, "push", "-q", "-f", str(fx.remote), "v0.2.0")


def _predicates(fx: Fixture, plan: str = PLAN_REL) -> dict[str, str]:
    result = fx.run("check", plan, "--session", SESSION, "--json")
    return json.loads(result.stdout.splitlines()[1])["predicates"]


def _read(fx: Fixture, rel: str) -> str:
    return (fx.work / rel).read_text(encoding="utf-8")


CARRY = {"class": "carry-gaps"}


# --------------------------------------------------------------------------- not the last plan


def test_an_open_gap_blocks_until_it_is_carried_to_the_next_patch(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY)
    before = _predicates(fx)
    assert before["gaps.version"] == "unmet" and before["gaps.carried"] == "unmet"
    assert before["archive.minor"] == "n/a" and before["archive.empty-dirs"] == "n/a"
    carried = _close(fx, "carry", "--plan", PLAN_REL, "--session", SESSION, "--date", "2026-10-02")
    assert carried.returncode == 0, carried.stdout + carried.stderr
    assert carried.stdout.splitlines() == [f"CARRIED v0.2#WN-3 -> v0.2.1 {GAPS}"]
    text = _read(fx, GAPS)
    head, tail = text.split("## v0.2.1", 1)
    assert "WN-3" not in head.split("### Open Items", 1)[1].split("### Resolved")[0]
    assert "#### WN-3: The probe flakes on a cold cache" in tail
    assert "- **Carried from**: v0.2.0 on 2026-10-02" in tail
    assert "**Open items**: 1" in text  # the item still counts, now in v0.2.1
    _commit_and_ship(fx, "carry")
    after = _predicates(fx)
    assert after["gaps.version"] == "met" and after["gaps.carried"] == "met"
    result = fx.check()
    assert result.stdout.startswith("PLAN COMPLETE "), result.stdout


def test_a_deleted_gap_is_never_carried(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY)
    fx.write(GAPS, ledger("v0.2", section("v0.2.0", 0, "")))
    _commit_and_ship(fx, "drop the gap")
    assert _predicates(fx)["gaps.carried"] == "unmet"


def test_carry_needs_the_carry_gaps_approval(tmp_path: Path) -> None:
    fx = _build(tmp_path)
    refused = _close(fx, "carry", "--plan", PLAN_REL, "--session", SESSION)
    assert refused.returncode == 3
    assert refused.stdout.splitlines()[0].startswith("REFUSED: approval-not-covered")
    assert "WN-3" in _read(fx, GAPS).split("## v0.2.0", 1)[1]


def test_a_security_gap_is_carried_only_when_named(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY, items=BG2, wn=0, bg=1)
    refused = _close(fx, "carry", "--plan", PLAN_REL, "--session", SESSION)
    assert refused.stdout.splitlines()[0] == "REFUSED: security-not-named (v0.2#BG-2)"
    (tmp_path / "named").mkdir()
    named = _build(tmp_path / "named", {"class": "carry-gaps", "named": ["v0.2#BG-2"]}, items=BG2, wn=0, bg=1)
    done = _close(named, "carry", "--plan", PLAN_REL, "--session", SESSION)
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith("CARRIED v0.2#BG-2 -> v0.2.1")


# --------------------------------------------------------------------------- the last plan


def test_the_last_plan_moves_every_open_gap_to_the_next_minor(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY, sibling=False)
    assert _predicates(fx)["gaps.carried"] == "unmet"
    moved = _close(fx, "carry", "--plan", PLAN_REL, "--session", SESSION, "--date", "2026-10-02")
    assert moved.returncode == 0, moved.stdout + moved.stderr
    assert moved.stdout.splitlines() == [f"MIGRATED v0.2#WN-3 -> v0.3#WN-1 (v0.3.0) {NEXT_GAPS}"]
    assert "#### WN-3: The probe flakes on a cold cache - MIGRATED to v0.3.0" in _read(fx, GAPS)
    assert "- **Migrated from**: v0.2#WN-3 on 2026-10-02 (reason: user-deferred)" in _read(fx, NEXT_GAPS)
    _commit_and_ship(fx, "carry")
    after = _predicates(fx)
    assert after["gaps.version"] == "met" and after["gaps.carried"] == "met"
    # The last plan must also archive its minor; without archive-minor that stays unmet.
    assert after["archive.minor"] == "unmet"
    assert fx.check().stdout.startswith("INCOMPLETE: ")


def test_archive_needs_the_last_plan(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY, {"class": "archive-minor"})
    refused = _close(fx, "archive", "--minor", "v0.2", "--plan", PLAN_REL, "--session", SESSION, "--apply",
                     "--link-checker", str(LINK_CHECKER))
    assert refused.stdout.splitlines()[0] == "REFUSED: not-last-plan (v0.2.0)"


def test_the_last_plan_archives_its_minor_and_the_record_follows_the_plan(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY, {"class": "archive-minor"}, {"class": "minor-close-pr"}, sibling=False)
    assert _close(fx, "carry", "--plan", PLAN_REL, "--session", SESSION).returncode == 0
    text = _read(fx, GAPS).replace("**Status**: in-progress", "**Status**: finalized")
    fx.write(GAPS, text)
    _commit_and_ship(fx, "carry and finalize")
    _git(fx.work, "push", "-q", str(fx.remote), "main:develop")
    _git(fx.work, "fetch", "-q", "origin")
    _git(fx.work, "checkout", "-q", "-b", "chore/close-v0.2")
    archived = _close(fx, "archive", "--minor", "v0.2", "--plan", PLAN_REL, "--session", SESSION, "--apply",
                      "--link-checker", str(LINK_CHECKER))
    assert archived.returncode == 0, archived.stdout + archived.stderr
    lines = archived.stdout.splitlines()
    assert f"RE-POINTED run record -> {ARCHIVED_PLAN}" in lines
    # The archived minor's folder is gone; v0 stays, because it now holds v0.3's ledger.
    assert not (fx.work / "docs/releases/v0/v0.2").exists(), "the archived minor's folder was left behind"
    assert (fx.work / NEXT_GAPS).is_file()
    assert lines[-1].startswith("ARCHIVED v0.2 docs/releases/v0/v0.2 -> docs/archives/v0/v0.2 ")
    # The record now names the archived plan, still verifies, and the checker finds it there.
    before_merge = _predicates(fx, ARCHIVED_PLAN)
    assert before_merge["approval.remote"] == "met", before_merge
    assert before_merge["gaps.carried"] == "met" and before_merge["archive.empty-dirs"] == "met"
    assert before_merge["archive.minor"] == "unmet"  # the closing pull request has not merged
    _git(fx.work, "push", "-q", str(fx.remote), "chore/close-v0.2:develop")
    _git(fx.work, "fetch", "-q", "origin")
    assert _predicates(fx, ARCHIVED_PLAN)["archive.minor"] == "met"


def test_an_empty_folder_left_under_releases_is_unmet(tmp_path: Path) -> None:
    fx = _build(tmp_path, CARRY, {"class": "archive-minor"}, sibling=False)
    (fx.work / "docs/releases/v0/v0.9").mkdir(parents=True)
    assert _predicates(fx)["archive.empty-dirs"] == "unmet"


def test_removing_empty_folders_climbs_until_a_folder_holds_something(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import minor_close

    (tmp_path / "docs/releases/v9/v9.1/plans").mkdir(parents=True)
    (tmp_path / "docs/releases/v8/v8.2").mkdir(parents=True)
    (tmp_path / "docs/releases/v8/v8.2/known-gaps.md").write_text("# Gaps\n", encoding="utf-8")
    removed = minor_close.remove_empty_dirs(tmp_path)
    assert removed == ["docs/releases/v9/v9.1/plans", "docs/releases/v9/v9.1", "docs/releases/v9"]
    assert (tmp_path / "docs/releases/v8/v8.2/known-gaps.md").is_file()
    assert (tmp_path / "docs/releases").is_dir()  # the canonical root itself is kept


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_carry_keeps_summary_counts_in_step_on_any_line_ending(newline: str) -> None:
    """A ledger checked out with CRLF endings (Windows) still has its counts checked and updated."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import completion_minor as cm
    import minor_close

    text = ledger("v0.2", section("v0.2.0", 1, WN3)).replace("\n", newline)
    (item,) = cm.parse_ledger(text)
    moved = minor_close.carry_within(text, item, "v0.2.1", "v0.2.0", "2026-10-02")
    summaries = moved.split("### Summary")
    assert "| Warnings (WN) | 0 | 0 |" in summaries[1]  # v0.2.0 no longer holds it
    assert "| Warnings (WN) | 1 | 0 |" in summaries[2]  # v0.2.1 does
    wrong = text.replace("| Warnings (WN) | 1 |", "| Warnings (WN) | 5 |")
    with pytest.raises(minor_close.Refused) as refused:
        minor_close.carry_within(wrong, item, "v0.2.1", "v0.2.0", "2026-10-02")
    assert refused.value.reason == "summary-mismatch"
