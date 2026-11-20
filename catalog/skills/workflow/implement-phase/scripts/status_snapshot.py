#!/usr/bin/env python3
"""Measure a progress snapshot from the repository; the agent supplies only words.

`status_report.py` renders a snapshot. When an agent assembled that snapshot by
hand it could leave Elapsed and Remaining as ``unknown`` even though both are
measurable, and the report then showed a table of unknowns. This producer reads
the numbers from git and the plan files, so measuring is the default path:

- Tasks: every ``- [ ] T001`` / ``- [x] T001`` line in the plan, read from the
  plan branch when it exists (its ticks are committed there).
- Elapsed: the plan branch's own commits, first commit to now, or to the last
  commit once the plan is released. A plan with no commits of its own has not
  started and shows ``N/A``. A deleted branch is found through its merge commit.
- Remaining: open tasks times days per task, where days per task comes from the
  interval between consecutive release tags divided by that release's task
  count (median, with the middle half as the range). A released plan shows
  ``N/A``. With fewer than three measured releases the plan's own pace is used,
  and only a repository with no history at all prints ``N/A (no history yet)``.

The optional ``--overlay`` JSON carries what git cannot know: goals, decisions,
running items (with a ``started_at`` time, from which elapsed is computed), a
state or dependency per version, and the next-release condition. It cannot set
a task count, an elapsed or a remaining value for a version row.

Read-only: runs ``git`` read commands only and writes nothing but stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK_RE = re.compile(r"^\s*- \[([ xX])\]\s+T\d+\b", re.MULTILINE)
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)")
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
HISTORY = 10  # most recent releases used for the rate
ROW_KEYS = ("done", "total", "elapsed", "remaining")
_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        creationflags=_FLAGS,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def vkey(version: str) -> tuple[int, ...]:
    match = VERSION_RE.match(version)
    return tuple(int(p) for p in match.groups()) if match else (0, 0, 0)


def count_tasks(text: str) -> tuple[int, int]:
    marks = TASK_RE.findall(text)
    return sum(1 for m in marks if m.lower() == "x"), len(marks)


def duration(days: float) -> str:
    hours = days * 24
    if hours < 1:
        return f"{max(1, round(hours * 60))} min"
    if hours < 24:
        return f"{round(hours)} h"
    return f"{days:.1f} d"


def estimate(tasks: int, rate: tuple[float, float, float] | None) -> str:
    if not tasks:
        return "N/A"
    if rate is None:
        return "N/A (no history yet)"
    mid, low, high = (tasks * r for r in rate)
    unit = "h" if high < 1 else "d"
    scale = 24 if unit == "h" else 1

    def fmt(value: float) -> str:
        return f"{max(value * scale, 0.1 if unit == 'd' else 1):.{1 if unit == 'd' else 0}f}"

    if fmt(low) == fmt(high):
        return f"~{fmt(mid)} {unit}"
    return f"~{fmt(mid)} {unit} ({fmt(low)}-{fmt(high)} {unit})"


class Repo:
    def __init__(self, root: Path, integration: str) -> None:
        self.root = root
        base = (
            f"origin/{integration}"
            if git(root, "rev-parse", "--verify", "-q", f"origin/{integration}")
            else integration
        )
        self.base = base
        self.main_line = set(git(root, "rev-list", "--first-parent", base).split())
        self.refs = git(
            root,
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
            "refs/remotes/origin",
        ).splitlines()
        tags = git(
            root,
            "for-each-ref",
            "--sort=creatordate",
            "--format=%(refname:short) %(creatordate:iso-strict)",
            "refs/tags/v*",
        ).splitlines()
        self.tags = [
            (n, datetime.fromisoformat(d))
            for n, d in (t.split(" ", 1) for t in tags)
            if TAG_RE.match(n)
        ]
        self.tag_names = {n for n, _ in self.tags}

    def branch(self, version: str) -> str | None:
        pattern = re.compile(rf"^(origin/)?feat/{re.escape(version)}-")
        found = sorted(r for r in self.refs if pattern.match(r))
        return found[0] if found else None

    def own_commits(self, tip: str) -> list[str]:
        own = []
        for commit in git(self.root, "rev-list", "--first-parent", tip).split():
            if commit in self.main_line:
                break
            own.append(commit)
        return own

    def commits_for(self, version: str, branch: str | None) -> list[str]:
        if branch:
            own = self.own_commits(branch)
            if own:
                return own
        merges = git(
            self.root,
            "log",
            "--first-parent",
            "--merges",
            "--format=%H",
            f"--grep=feat/{version}-",
            "--fixed-strings",
            self.base,
        ).split()
        own: list[str] = []
        for merge in merges:
            own.extend(self.own_commits(f"{merge}^2"))
        return own

    def when(self, commit: str) -> datetime:
        return datetime.fromisoformat(
            git(self.root, "show", "-s", "--format=%cI", commit)
        )

    def plan_text(self, path: Path, branch: str | None) -> str:
        if branch:
            relative = path.relative_to(self.root).as_posix()
            shown = git(self.root, "show", f"{branch}:{relative}")
            if shown:
                return shown
        return path.read_text(encoding="utf-8", errors="replace")


def plan_files(root: Path, pattern: str) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for tree in ("docs/releases", "docs/archives", "docs/archive"):
        for path in sorted((root / tree).glob(f"**/plans/{pattern}")):
            version = VERSION_RE.match(path.name)
            key = f"v{'.'.join(version.groups())}" if version else None
            if key and key not in found:
                found[key] = path
    return found


def release_rate(
    repo: Repo, all_plans: dict[str, Path]
) -> tuple[float, float, float] | None:
    samples = []
    for (prev, prev_at), (name, at) in zip(repo.tags, repo.tags[1:]):
        path = all_plans.get(name)
        if path is None:
            continue
        _, total = count_tasks(path.read_text(encoding="utf-8", errors="replace"))
        days = (at - prev_at).total_seconds() / 86400
        if total and days > 0:
            samples.append(days / total)
    samples = samples[-HISTORY:]
    if len(samples) < 3:
        return None
    q1, mid, q3 = statistics.quantiles(samples, n=4, method="inclusive")
    return statistics.median(samples), q1, q3


def measure_row(
    repo: Repo, version: str, path: Path, now: datetime, rate, overlay: dict
) -> dict:
    branch = repo.branch(version)
    released = version in repo.tag_names
    # A released plan's final ticks live on the integration branch, not its old branch.
    done, total = count_tasks(repo.plan_text(path, repo.base if released else branch))
    commits = repo.commits_for(version, branch)
    started = repo.when(commits[-1]) if commits else None
    end = repo.when(commits[0]) if (commits and released) else now
    pace = None
    if rate is None and started and done:
        per_task = (end - started).total_seconds() / 86400 / done
        pace = (per_task, per_task, per_task)
    if released:
        state, remaining = "released", "N/A"
    else:
        state = "implementing" if commits else "not started"
        remaining = estimate(total - done, rate or pace)
    return {
        "name": version,
        "goals": plan_title(path),
        "done": done,
        "total": total,
        "state": overlay.get("states", {}).get(version, state),
        "elapsed": (
            duration((end - started).total_seconds() / 86400) if started else "N/A"
        ),
        "remaining": remaining,
        "dependency": overlay.get("dependencies", {}).get(version, "none"),
        "_started": started,
        "_open": 0 if released else total - done,
    }


def plan_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            title = re.sub(
                r"^((Implementation )?Plan\s*[-:]+\s*)?(v\d+\.\d+\.\d+\s*[-:]*\s*)?",
                "",
                line[2:].strip(),
            )
            return title or path.stem
    return path.stem


def running_items(overlay: dict, now: datetime, rate) -> list[dict]:
    items = []
    for item in overlay.get("running", []):
        entry = {k: item[k] for k in ("name", "state", "url") if k in item}
        entry["done"], entry["total"] = item.get("done"), item.get("total")
        started = item.get("started_at")
        if started:
            entry["elapsed"] = duration(
                (
                    now - datetime.fromisoformat(started.replace("Z", "+00:00"))
                ).total_seconds()
                / 86400
            )
        else:
            entry["elapsed"] = item.get("elapsed", "N/A")
        if "remaining" in item:
            entry["remaining"] = item["remaining"]
        elif entry["done"] is not None and entry["total"] is not None:
            # Work with tasks gets the same measured estimate as a version row.
            entry["remaining"] = estimate(entry["total"] - entry["done"], rate)
        else:
            entry["remaining"] = "N/A"
        items.append(entry)
    return items


def build(
    root: Path, scope: str, overlay: dict, integration: str, now: datetime
) -> dict:
    for key in ROW_KEYS:
        if any(key in row for row in overlay.get("rows", [])):
            raise ValueError(
                f"overlay cannot set {key}; it is measured from the repository"
            )
    repo = Repo(root, integration)
    single = re.fullmatch(r"v\d+\.\d+\.\d+", scope) is not None
    if not single and not re.fullmatch(r"v\d+\.\d+", scope):
        raise ValueError("scope must be vX.Y or vX.Y.Z")
    members = plan_files(root, f"{scope}-*.md" if single else f"{scope}.*-*.md")
    if not single:
        members = {v: p for v, p in members.items() if v.startswith(scope + ".")}
    if not members:
        raise ValueError(f"no plan found for {scope}")
    rate = release_rate(repo, plan_files(root, "v*.md"))
    rows = [
        measure_row(repo, v, members[v], now, rate, overlay)
        for v in sorted(members, key=vkey)
    ]
    starts = [r["_started"] for r in rows if r["_started"]]
    open_tasks = sum(r["_open"] for r in rows)
    lanes = max(1, sum(1 for r in rows if r["_started"] and r["_open"]))
    pending = [
        r for r in rows if r["state"] != "released" and r["name"] not in repo.tag_names
    ]
    released = sorted((n for n in repo.tag_names), key=vkey)
    whole_rate = None if rate is None else tuple(x / lanes for x in rate)
    for row in rows:
        row.pop("_started")
        row.pop("_open")
    goals = overlay.get("goals") or [
        {
            "goal": f"Complete {scope}",
            "scope": "run",
            "done_when": f"all {len(rows)} {'plan' if len(rows) == 1 else 'members'} released",
            "state": f"{len(rows) - len(pending)} of {len(rows)} released",
        }
    ]
    snapshot = {
        "run_id": overlay.get("run_id", f"{scope}-run"),
        "scope": scope,
        "active": overlay.get("active", bool(pending)),
        "observed_at": now.isoformat(timespec="seconds"),
        "source": "measured by status_snapshot.py from git and plan files",
        "last_released": released[-1] if released else "none released yet",
        "versions_left": len(pending),
        "elapsed": (
            duration((now - min(starts)).total_seconds() / 86400) if starts else "N/A"
        ),
        "remaining": estimate(open_tasks, whole_rate) if pending else "N/A",
        "estimate_basis": (
            "open tasks x days per task from recent release tags"
            if rate
            else "plan's own pace"
        ),
        "rows": rows,
        "goals": goals,
        "decisions": overlay.get("decisions", []),
        "running": running_items(overlay, now, rate),
        "next_release": None,
    }
    if pending:
        nxt = pending[0]
        snapshot["next_release"] = {
            "version": nxt["name"],
            "remaining": nxt["remaining"],
            "condition": overlay.get("next_release_condition", "none"),
            "confidence": "medium" if rate else "low",
            "basis": snapshot["estimate_basis"],
        }
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--scope", required=True, help="vX.Y for a minor, vX.Y.Z for one plan"
    )
    parser.add_argument(
        "--overlay",
        type=Path,
        help="JSON with goals, decisions, running, states, dependencies",
    )
    parser.add_argument("--integration-branch", default="develop")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        overlay = (
            json.loads(args.overlay.read_text(encoding="utf-8-sig"))
            if args.overlay
            else {}
        )
        snapshot = build(
            args.repo.resolve(),
            args.scope,
            overlay,
            args.integration_branch,
            datetime.now(timezone.utc),
        )
    except (OSError, ValueError) as exc:
        print(f"status snapshot unavailable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(snapshot, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
