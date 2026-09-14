#!/usr/bin/env python3
"""Report a plan's phase progress, and the handoff for whatever comes next.

Two jobs that share one parser, because both read the same thing - a plan file's
phase headings, task checkboxes, and per-phase model-routing fields.

**Progress.** `--plan <file>` prints the table that closes a phase: the plan, its
target version, and every phase with its task counts. A reader should be able to
see where a multi-session plan actually stands without opening it.

**Handoff.** `--next` finds the next plan with open tasks and prints the command
to run it, plus ONE tier and effort level.

The single-recommendation rule matters and is not an average. `/implement <plan>
in-full` runs every phase in one invocation, so the recommendation has to carry
the HARDEST phase: the maximum tier and the maximum effort found anywhere in the
plan. Recommending a phase-by-phase mix would be correct advice for a command
nobody is running, and picking the modal value would under-provision the phase
most likely to need the headroom.

Concrete model ids come from the plan's own `## Current model map`, which `/plan`
dates and cites when it writes the plan. This script never invents one: a map
that is absent or stale is reported as such, because a confidently wrong model
id is worse than none.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_NO_PLAN = 1
EXIT_UNREADABLE = 2

# Ordered weakest to strongest so `max()` is meaningful.
TIERS = ("fast", "standard", "strong", "frontier")
EFFORTS = ("low", "medium", "high", "max")

PHASE_RE = re.compile(r"^## Phase (\d+):\s*(.+?)\s*$", re.MULTILINE)
TIER_RE = re.compile(r"^\*\*Recommended model tier\*\*:\s*(\S+)", re.MULTILINE)
EFFORT_RE = re.compile(r"^\*\*Recommended effort level\*\*:\s*(\S+)", re.MULTILINE)
TASK_RE = re.compile(r"^- \[([ xX])\]\s+(T\d+)\b", re.MULTILINE)
VERSION_RE = re.compile(r"^\*\*Version\*\*:\s*(\S+)", re.MULTILINE)
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*(\S+)", re.MULTILINE)
MAP_ROW_RE = re.compile(r"^\|\s*(fast|standard|strong|frontier)\s*\|(.+)\|\s*$", re.MULTILINE)
MAP_HEADER_RE = re.compile(r"^\|\s*Tier\s*\|(.+)\|\s*$", re.MULTILINE)
MAP_STATUS_RE = re.compile(r"^\*\*Model map status\*\*:\s*(.+?)\s*$", re.MULTILINE)


class Plan:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.version = self._one(VERSION_RE, "unknown")
        self.slug = self._one(SLUG_RE, path.stem)
        self.title = self._title()
        self.phases = self._phases()

    def _one(self, pattern: re.Pattern[str], default: str) -> str:
        found = pattern.search(self.text)
        return found.group(1) if found else default

    def _title(self) -> str:
        for line in self.text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return self.path.stem

    def _phases(self) -> list[dict]:
        marks = list(PHASE_RE.finditer(self.text))
        phases = []
        for index, match in enumerate(marks):
            end = marks[index + 1].start() if index + 1 < len(marks) else len(self.text)
            body = self.text[match.start():end]
            tasks = TASK_RE.findall(body)
            done = sum(1 for mark, _ in tasks if mark.lower() == "x")
            tier = TIER_RE.search(body)
            effort = EFFORT_RE.search(body)
            phases.append({
                "number": int(match.group(1)),
                "title": match.group(2),
                "done": done,
                "total": len(tasks),
                "tier": tier.group(1) if tier else None,
                "effort": effort.group(1) if effort else None,
            })
        return phases

    # -- aggregates ---------------------------------------------------------
    @property
    def open_tasks(self) -> int:
        return sum(p["total"] - p["done"] for p in self.phases)

    @property
    def total_tasks(self) -> int:
        return sum(p["total"] for p in self.phases)

    @property
    def phases_complete(self) -> int:
        return sum(1 for p in self.phases if p["total"] and p["done"] == p["total"])

    def hardest(self) -> tuple[str | None, str | None]:
        """The MAX tier and effort in the plan, which is what in-full needs."""
        tiers = [p["tier"] for p in self.phases if p["tier"] in TIERS]
        efforts = [p["effort"] for p in self.phases if p["effort"] in EFFORTS]
        tier = max(tiers, key=TIERS.index) if tiers else None
        effort = max(efforts, key=EFFORTS.index) if efforts else None
        return tier, effort

    def model_map(self) -> tuple[list[str], dict[str, list[str]], str | None]:
        header = MAP_HEADER_RE.search(self.text)
        providers = (
            [c.strip() for c in header.group(1).split("|") if c.strip()] if header else []
        )
        rows = {
            m.group(1): [c.strip() for c in m.group(2).split("|") if c.strip()]
            for m in MAP_ROW_RE.finditer(self.text)
        }
        status = MAP_STATUS_RE.search(self.text)
        return providers, rows, status.group(1) if status else None


def progress_table(plan: Plan) -> str:
    lines = [
        f"**Plan**: {plan.title}",
        f"**Target version**: {plan.version}",
        "",
        "| Phase | Status | Tasks |",
        "|---|---|---|",
    ]
    for phase in plan.phases:
        if phase["total"] and phase["done"] == phase["total"]:
            status = "complete"
        elif phase["done"]:
            status = "in progress"
        else:
            status = "not started"
        lines.append(
            f"| {phase['number']}. {phase['title']} | {status} | "
            f"{phase['done']}/{phase['total']} |"
        )
    lines.append("")
    lines.append(
        f"**{plan.phases_complete} of {len(plan.phases)} phases complete; "
        f"{plan.total_tasks - plan.open_tasks} of {plan.total_tasks} tasks.**"
    )
    return "\n".join(lines)


def find_plans(root: Path) -> list[Path]:
    return sorted(root.glob("docs/releases/**/plans/*.md"))


def version_key(version: str) -> list[int]:
    parts = re.findall(r"\d+", version)
    return [int(p) for p in parts] or [0]


def released_version(root: Path) -> list[int]:
    """The canonical version, so closed cycles are not proposed as 'next'."""
    manifest = root / ".claude-plugin/plugin.json"
    try:
        import json
        return version_key(json.loads(manifest.read_text(encoding="utf-8"))["version"])
    except (OSError, KeyError, ValueError):
        return [0]


def next_plan(root: Path) -> Plan | None:
    """The next plan to WORK ON, which is not simply the oldest with open boxes.

    A plan from a shipped cycle can carry unticked tasks forever: some predate
    the checkbox convention, others were closed without anyone ticking them. The
    first version of this selector proposed v3.0.0 while the repository sat at
    v4.11.0, which is not a queue, it is archaeology.

    So a candidate must be at or above the released version. Within that, the
    lowest version wins, because the queue runs forward.
    """
    floor = released_version(root)
    candidates = []
    for path in find_plans(root):
        try:
            plan = Plan(path)
        except OSError:
            continue
        if not (plan.total_tasks and plan.open_tasks):
            continue
        if version_key(plan.version) < floor:
            continue
        candidates.append(plan)
    if not candidates:
        return None
    return min(candidates, key=lambda p: (version_key(p.version), p.path.as_posix()))


def handoff(plan: Plan) -> str:
    tier, effort = plan.hardest()
    providers, rows, status = plan.model_map()

    lines = [
        f"**Next plan**: {plan.title}",
        f"**Target version**: {plan.version}",
        f"**Open**: {plan.open_tasks} of {plan.total_tasks} tasks across "
        f"{len(plan.phases)} phases",
        "",
        "Run this in a fresh session:",
        "",
        "```",
        f"/implement {plan.version} in-full",
        "```",
        "",
    ]

    if tier and effort:
        lines += [
            f"**Use {tier} tier at {effort} effort for the whole run.**",
            "",
            f"`in-full` executes every phase in one invocation, so the setting has "
            f"to carry the hardest phase rather than the average one. {tier}/{effort} "
            f"is the maximum this plan asks for anywhere.",
            "",
        ]
    else:
        lines += [
            "**Tier and effort: not recorded in this plan.** Assess at "
            "implementation time and default upward on any uncertainty.",
            "",
        ]

    if tier and providers and rows.get(tier):
        cells = rows[tier]
        lines += ["Per platform, at that tier:", "", "| Platform | Model | Effort |", "|---|---|---|"]
        for name, model in zip(providers, cells):
            lines.append(f"| {name} | {model} | {effort or 'assess'} |")
        lines.append("")
        if status:
            lines.append(f"Model map: {status}")
            lines.append("")
        lines.append(
            "Cursor, OpenCode and Copilot have no scriptable model switch; set "
            "those in the picker before starting."
        )
    elif tier:
        lines.append(
            "This plan records no `## Current model map`, so no concrete model id "
            "is offered. Resolve the tier on your platform rather than guessing an id."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, help="plan file to report progress for")
    parser.add_argument("--next", action="store_true",
                        help="find the next plan with open tasks and print its handoff")
    parser.add_argument("--root", type=Path, default=Path("."),
                        help="repository root for --next")
    args = parser.parse_args(argv)

    if not args.plan and not args.next:
        parser.error("pass --plan <file> or --next")

    if args.plan:
        if not args.plan.is_file():
            print(f"plan_status: no plan at {args.plan}", file=sys.stderr)
            return EXIT_UNREADABLE
        print(progress_table(Plan(args.plan)))
        if args.next:
            print()

    if args.next:
        plan = next_plan(args.root)
        if plan is None:
            print("**No plan with open tasks.** The queue is clear.")
            return EXIT_NO_PLAN
        print(handoff(plan))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
