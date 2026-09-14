"""The progress table and the next-plan handoff are derived, never hand-written.

The selection rule carries the interesting assertion. "Next plan" means the next
one to WORK ON, not the oldest file with unticked boxes: plans from shipped
cycles keep open checkboxes forever, some predating the convention and some
closed without anyone ticking them. An unfiltered scan proposed v3.0.0 while the
repository sat at v4.11.0, which is archaeology rather than a queue.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/plan_status.py"
_spec = importlib.util.spec_from_file_location("plan_status", SCRIPT)
ps = importlib.util.module_from_spec(_spec)
sys.modules["plan_status"] = ps
_spec.loader.exec_module(ps)

PLAN = """# Plan - Example

**Version**: v9.1.0
**Slug**: example

## Current model map

| Tier | Anthropic | OpenAI |
|---|---|---|
| frontier | `a-frontier` | `o-frontier` |
| strong | `a-strong` | `o-strong` |

**Model map status**: fresh as of 2026-09-13; sources cited below.

## Phase 1: First

**Recommended model tier**: standard
**Recommended effort level**: low

- [x] T001 done
- [x] T002 done

## Phase 2: Second

**Recommended model tier**: frontier
**Recommended effort level**: max

- [x] T003 done
- [ ] T004 open

## Phase 3: Third

**Recommended model tier**: strong
**Recommended effort level**: high

- [ ] T005 open
"""


@pytest.fixture
def plan(tmp_path: Path) -> "ps.Plan":
    target = tmp_path / "v9.1.0-example.md"
    target.write_text(PLAN, encoding="utf-8")
    return ps.Plan(target)


def test_phase_status_is_derived_from_the_checkboxes(plan) -> None:
    table = ps.progress_table(plan)
    assert "| 1. First | complete | 2/2 |" in table
    assert "| 2. Second | in progress | 1/2 |" in table
    assert "| 3. Third | not started | 0/1 |" in table
    assert "1 of 3 phases complete; 3 of 5 tasks." in table


def test_the_recommendation_is_the_hardest_phase_not_the_average(plan) -> None:
    """in-full runs every phase, so the setting must carry the worst one."""
    tier, effort = plan.hardest()
    assert (tier, effort) == ("frontier", "max"), (
        "the plan contains standard/low, frontier/max and strong/high; a single "
        "recommendation for a full run must be the maximum of each"
    )


def test_the_handoff_names_the_command_and_one_setting(plan) -> None:
    text = ps.handoff(plan)
    assert "/implement v9.1.0 in-full" in text
    assert "frontier tier at max effort" in text
    assert "| Anthropic | `a-frontier` | max |" in text
    assert "| OpenAI | `o-frontier` | max |" in text


def test_a_plan_without_a_model_map_offers_no_invented_id(tmp_path: Path) -> None:
    """A confidently wrong model id is worse than none."""
    stripped = PLAN[: PLAN.index("## Current model map")] + PLAN[PLAN.index("## Phase 1"):]
    target = tmp_path / "v9.1.0-nomap.md"
    target.write_text(stripped, encoding="utf-8")
    text = ps.handoff(ps.Plan(target))
    assert "frontier tier at max effort" in text
    assert "no concrete model id" in text
    assert "`a-frontier`" not in text


def _repo(tmp_path: Path, released: str, plans: dict[str, str]) -> Path:
    (tmp_path / ".claude-plugin").mkdir(parents=True)
    (tmp_path / ".claude-plugin/plugin.json").write_text(
        json.dumps({"version": released}), encoding="utf-8"
    )
    for name, body in plans.items():
        directory = tmp_path / "docs/releases/v9/v9.1/plans"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(body, encoding="utf-8")
    return tmp_path


def test_a_shipped_cycle_is_not_proposed_as_next(tmp_path: Path) -> None:
    """The defect the first version had: it offered v3.0.0 at v4.11.0."""
    old = PLAN.replace("**Version**: v9.1.0", "**Version**: v1.0.0")
    root = _repo(tmp_path, "9.1.0", {"v1.0.0-ancient.md": old})
    assert ps.next_plan(root) is None, (
        "a plan below the released version has open boxes because nobody ticked "
        "them, not because it is queued"
    )


def test_the_lowest_queued_version_at_or_above_the_release_wins(tmp_path: Path) -> None:
    later = PLAN.replace("**Version**: v9.1.0", "**Version**: v9.3.0")
    root = _repo(
        tmp_path, "9.1.0",
        {"v9.1.0-example.md": PLAN, "v9.3.0-later.md": later},
    )
    chosen = ps.next_plan(root)
    assert chosen is not None and chosen.version == "v9.1.0"


def test_a_clear_queue_says_so_rather_than_guessing(tmp_path: Path) -> None:
    done = PLAN.replace("- [ ] T004 open", "- [x] T004 done").replace(
        "- [ ] T005 open", "- [x] T005 done"
    )
    root = _repo(tmp_path, "9.1.0", {"v9.1.0-done.md": done})
    assert ps.next_plan(root) is None
    assert ps.main(["--next", "--root", str(root)]) == ps.EXIT_NO_PLAN


def test_a_missing_plan_file_is_an_error_not_an_empty_table(tmp_path: Path) -> None:
    assert ps.main(["--plan", str(tmp_path / "nope.md")]) == ps.EXIT_UNREADABLE


def test_the_real_repository_parses(tmp_path: Path) -> None:
    """The script must work on this repository's actual plans, not only fixtures."""
    plans = ps.find_plans(ROOT)
    assert plans, "no plans found; the glob no longer matches this repository"
    parsed = [ps.Plan(p) for p in plans[:20]]
    assert any(p.phases for p in parsed), "no plan yielded phases"
