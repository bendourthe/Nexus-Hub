"""Tests for the plan-queue enumeration script.

Two of these guard failure modes that have actually occurred in this repository:
a lexical directory walk ordering ``v3.10`` before ``v3.5``, and a scan scoped to
the current minor missing plans that live several minors ahead.

The rest guard the reporting contract that the ranking in later phases depends
on: an unreadable plan is reported rather than dropped, a missing Status line is
a note rather than a failure, and an open task count is never presented as queue
membership.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from enumerate_plan_queue import enumerate_plans, main, render_table


def write_plan(
    root: Path,
    version_dir: str,
    filename: str,
    *,
    status: str | None = "Authored; implementation not started.",
    open_tasks: int = 0,
    done_tasks: int = 0,
    touched: str = "docs/releases/example.md",
) -> Path:
    """Create a minimal but realistic plan file under a version directory."""
    plans = (
        root / "docs" / "releases" / version_dir.split(".")[0] / version_dir / "plans"
    )
    plans.mkdir(parents=True, exist_ok=True)
    lines = ["# Plan", ""]
    if status is not None:
        lines += [f"**Status**: {status}", ""]
    for i in range(open_tasks):
        lines.append(f"- [ ] T{i + 1:03d} [US1] Open task `{touched}`")
    for i in range(done_tasks):
        lines.append(f"- [x] T{open_tasks + i + 1:03d} [US1] Done task `{touched}`")
    # An exit-checklist item beginning with "The" must not be counted as a task.
    lines += ["", "- [ ] The phase's observable gate passed."]
    path = plans / filename
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_versions_sort_numerically_not_lexically(tmp_path: Path) -> None:
    # A lexical sort places v4.10 before v4.9. This is the trap Step 6.5
    # documents and the reason the script parses versions into integers.
    write_plan(tmp_path, "v4.9", "v4.9.0-nine.md")
    write_plan(tmp_path, "v4.10", "v4.10.0-ten.md")
    write_plan(tmp_path, "v4.5", "v4.5.0-five.md")

    versions = [p.version for p in enumerate_plans(tmp_path)]

    assert versions == ["v4.5.0", "v4.9.0", "v4.10.0"]


def test_plans_several_minors_ahead_are_found(tmp_path: Path) -> None:
    # A scan scoped to the in-flight minor cannot see these.
    write_plan(tmp_path, "v4.1", "v4.1.0-current.md")
    write_plan(tmp_path, "v4.13", "v4.13.0-far-ahead.md")

    slugs = [p.slug for p in enumerate_plans(tmp_path)]

    assert "far-ahead" in slugs


def test_major_versions_sort_numerically(tmp_path: Path) -> None:
    write_plan(tmp_path, "v3.20", "v3.20.0-three.md")
    write_plan(tmp_path, "v4.2", "v4.2.0-four.md")

    assert [p.version for p in enumerate_plans(tmp_path)] == ["v3.20.0", "v4.2.0"]


@pytest.mark.parametrize(
    ("open_tasks", "done_tasks"),
    [(0, 0), (5, 0), (0, 5), (3, 7)],
)
def test_task_counts(tmp_path: Path, open_tasks: int, done_tasks: int) -> None:
    write_plan(
        tmp_path,
        "v4.1",
        "v4.1.0-counts.md",
        open_tasks=open_tasks,
        done_tasks=done_tasks,
    )

    plan = enumerate_plans(tmp_path)[0]

    assert (plan.open_tasks, plan.done_tasks) == (open_tasks, done_tasks)


def test_exit_checklist_item_is_not_counted_as_a_task(tmp_path: Path) -> None:
    # "- [ ] The phase's observable gate passed." starts with T. Without the
    # trailing-space requirement in the task pattern it inflates every count.
    write_plan(tmp_path, "v4.1", "v4.1.0-checklist.md", open_tasks=2)

    assert enumerate_plans(tmp_path)[0].open_tasks == 2


def test_touched_paths_are_extracted_and_deduplicated(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "v4.1",
        "v4.1.0-touched.md",
        open_tasks=3,
        touched="docs/releases/v4/x.md",
    )

    plan = enumerate_plans(tmp_path)[0]

    assert plan.touched == ["docs/releases/v4/x.md"]


def test_missing_status_is_a_note_not_an_error(tmp_path: Path) -> None:
    # Most historical plans carry no Status line. Treating that as a parse
    # failure would make every real run exit 1 and the exit code worthless.
    write_plan(tmp_path, "v4.1", "v4.1.0-nostatus.md", status=None, open_tasks=2)

    plan = enumerate_plans(tmp_path)[0]

    assert plan.error is None
    assert plan.note is not None
    assert main(["--root", str(tmp_path)]) == 0


def test_declared_status_is_reported(tmp_path: Path) -> None:
    write_plan(tmp_path, "v4.1", "v4.1.0-status.md", status="Shipped 2026-01-01.")

    assert enumerate_plans(tmp_path)[0].status == "Shipped 2026-01-01."


def test_unreadable_plan_is_reported_never_omitted(tmp_path: Path) -> None:
    # An omitted plan is invisible in every downstream ranking.
    write_plan(tmp_path, "v4.1", "v4.1.0-good.md")
    bad = tmp_path / "docs" / "releases" / "v4" / "v4.1" / "plans" / "v4.1.1-bad.md"
    bad.write_bytes(b"\xff\xfe\x00 invalid utf-8 \xc3\x28")

    plans = enumerate_plans(tmp_path)
    slugs = {p.slug for p in plans}

    assert "bad" in slugs, "an unreadable plan must still appear in the queue"
    assert any(p.error for p in plans)
    assert main(["--root", str(tmp_path)]) == 1


def test_legacy_filename_without_version_prefix_is_kept(tmp_path: Path) -> None:
    # Plans predating the versioned filename convention are real queue members.
    write_plan(tmp_path, "v3.9", "adoption-no-mistakes.md")

    plans = enumerate_plans(tmp_path)

    assert len(plans) == 1
    assert plans[0].slug == "adoption-no-mistakes"
    assert plans[0].version == "v3.9"


def test_empty_tree_succeeds(tmp_path: Path) -> None:
    (tmp_path / "docs" / "releases").mkdir(parents=True)

    assert enumerate_plans(tmp_path) == []
    assert main(["--root", str(tmp_path)]) == 0


def test_absent_releases_tree_succeeds(tmp_path: Path) -> None:
    assert enumerate_plans(tmp_path) == []
    assert main(["--root", str(tmp_path)]) == 0


def test_missing_root_is_a_usage_error(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path / "nope")]) == 2


def test_table_states_that_counts_are_not_membership(tmp_path: Path) -> None:
    # The rendered output must carry the finding, because a caller reading only
    # the table would otherwise rank a shipped plan by its residual open count.
    write_plan(tmp_path, "v4.1", "v4.1.0-x.md", open_tasks=1)

    rendered = render_table(enumerate_plans(tmp_path))

    assert "NOT queue membership" in rendered


def test_json_output_is_wellformed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    write_plan(tmp_path, "v4.1", "v4.1.0-json.md", open_tasks=2, done_tasks=1)
    main(["--root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["plans"][0]["version"] == "v4.1.0"
    assert payload["plans"][0]["open_tasks"] == 2
    assert payload["plans"][0]["done_tasks"] == 1
