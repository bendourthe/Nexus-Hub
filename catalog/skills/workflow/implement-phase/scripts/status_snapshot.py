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

``--record`` (a minor run record path or key) adds ``idle_lanes``: members the run
signed or amended in that have no worker, blocked lanes whose prerequisite has
been released, and lanes blocked on a user action for over an hour. They are
measured by ``lane_health.py`` from the record and its heartbeats, never typed in.

Read-only: runs ``git`` read commands only and writes nothing but stdout.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
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

_STATE_SPEC = importlib.util.spec_from_file_location("nexus_continuation_state", Path(__file__).with_name("continuation_state.py"))
_STATE = importlib.util.module_from_spec(_STATE_SPEC)
_STATE_SPEC.loader.exec_module(_STATE)


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


NOT_ESTIMATED = "not estimated (no task list)"


def running_items(overlay: dict, now: datetime, rate) -> list[dict]:
    items = []
    for item in overlay.get("running", []):
        for key in ("elapsed", "remaining"):
            if key in item:
                raise ValueError(
                    f"overlay cannot set a running item's {key}; it is measured"
                )
        entry = {k: item[k] for k in ("id", "name", "state", "url", "handle", "status", "observed_at",
                                     "resume_when", "evidence", "result_verified", "started_at") if k in item}
        entry["done"], entry["total"] = item.get("done"), item.get("total")
        started = item.get("started_at")
        if not started:
            # A running item has started, so its elapsed time is always measurable.
            raise ValueError(
                f"running item {item.get('name')!r} needs started_at; its elapsed time is measured"
            )
        entry["elapsed"] = duration(
            (
                now - datetime.fromisoformat(started.replace("Z", "+00:00"))
            ).total_seconds()
            / 86400
        )
        if entry["done"] is not None and entry["total"] is not None:
            # Work with tasks gets the same measured estimate as a version row.
            entry["remaining"] = estimate(entry["total"] - entry["done"], rate)
        else:
            entry["remaining"] = NOT_ESTIMATED
        items.append(entry)
    return items


def idle_lanes(record: str, runs_dir: Path | None, repo: Path, now: datetime) -> list[dict]:
    """Idle members of one minor run record, from the sibling lane_health.py."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "lane_health", Path(__file__).with_name("lane_health.py")
    )
    lane_health = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lane_health)
    path = lane_health.resolve_record(record, runs_dir or lane_health.default_runs_dir())
    data = json.loads(path.read_text(encoding="utf-8"))
    tags = lane_health.release_tags(repo)
    lanes = lane_health.light_lanes(data, path, now, tags)
    return lane_health.classify_idle(
        lanes, lane_health.record_versions(data), tags.__contains__, now
    )


def native_scripts_dir() -> Path:
    """Use repository helpers only for the exact resolved catalog source path."""
    here = Path(__file__).resolve()
    if here.parts[-6:] == ('catalog', 'skills', 'workflow', 'implement-phase', 'scripts', 'status_snapshot.py'):
        return here.parents[5] / 'scripts'
    return Path.home() / '.nexus-hub/scripts'


def native_owner_projection(record_path: Path, root: Path, scope: str, observation: dict,
                            previous: dict | None, remaining_tasks: int, observer_session: str | None = None) -> dict:
    """Read the native issued-request owner even when no sidecar was supplied."""
    from types import SimpleNamespace
    path = native_scripts_dir() / 'run_plan.py'
    if not path.is_file() or path.is_symlink():
        raise ValueError('native owner projection requires the matching controller helper')
    spec = importlib.util.spec_from_file_location('_nexus_owner_controller', path)
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    frame = {'observation': observation, 'disposition': previous or {}}
    if not record_path.exists():
        import check_plan_completion as ck
        resolved = ck.precreate_owner_context(observer_session or '')
        if resolved is None:
            raise ValueError('pre-create projection requires the owning session and sealed native context')
        context, expected_path, metadata = resolved
        if context.version != scope or expected_path.resolve() != record_path.resolve():
            raise ValueError('pre-create projection scope does not match the report')
        native = controller.precreate_owner_observation(SimpleNamespace(minor=False, label=str(context.plan), repo_root=root),
            record_path, metadata, frame)
        return native if native is not None else observation
    record = controller._bounded_json(record_path)
    minor = record.get('schema') == 2
    if minor and record.get('minor') != scope:
        raise ValueError('native owner projection scope does not match the report')
    if not minor:
        import check_plan_completion as ck
        context, record = ck.resolve_plan_controller(record_path)
        if context.version != scope:
            raise ValueError('native plan owner scope does not match the report')
    native = controller.native_owner_observation(SimpleNamespace(minor=minor, label=scope, repo_root=root, observer_session=observer_session),
        record_path, record, frame, remaining_tasks=remaining_tasks)
    if native is not None and (native.get('owner_replies') or native.get('owner_recovery')):
        try:
            _STATE.reconcile(native, previous)
        except ValueError as exc:
            if ('unfinished implementation requires' not in str(exc)
                    and 'task marks alone do not establish verified completion' not in str(exc)):
                raise
            pending = native.get('owner_replies') or native['owner_recovery']
            raise ValueError(pending[0]['reason']) from exc
    return native if native is not None else observation


def build(
    root: Path,
    scope: str,
    overlay: dict,
    integration: str,
    now: datetime,
    idle: list[dict] | None = None,
    record_path: Path | None = None,
    observer_session: str | None = None,
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
    pending = [
        r for r in rows if r["state"] != "released" and r["name"] not in repo.tag_names
    ]
    released = sorted((n for n in repo.tag_names), key=vkey)
    # Historical branch starts do not prove independent work can overlap.
    whole_rate = rate
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
            "open tasks x historical days per task; one effective lane (no verified overlap schedule)"
            if rate
            else "plan's own pace"
        ),
        "rows": rows,
        "goals": goals,
        "decisions": overlay.get("decisions", []),
        "running": running_items(overlay, now, rate),
        "next_release": None,
    }
    if idle is not None:
        snapshot["idle_lanes"] = idle
    if pending:
        nxt = pending[0]
        snapshot["next_release"] = {
            "version": nxt["name"],
            "remaining": nxt["remaining"] + " implementation only; validation/release time additional",
            "condition": overlay.get("next_release_condition", "none"),
            "confidence": "low",
            "basis": snapshot["estimate_basis"] + "; validation/release duration not measured",
        }
    for key in ("continuation", "manual_actions", "questions", "work", "external_conditions", "native_goal",
                "paused", "completion", "resolutions", "condition_resolutions", "previous_continuation", "objective"):
        if key in overlay:
            snapshot[key] = copy.deepcopy(overlay[key])
    observation = copy.deepcopy(snapshot.get("continuation", {}))
    if not isinstance(observation, dict):
        raise ValueError("continuation must contain structured observations")
    if "remaining_tasks" in observation and observation["remaining_tasks"] != open_tasks:
        raise ValueError("overlay cannot set remaining_tasks; it is measured from the repository")
    observation["remaining_tasks"] = open_tasks
    observation.setdefault("objective", snapshot.get("objective") or "; ".join(g["goal"] for g in goals))
    for key in ("work", "native_goal", "external_conditions", "paused", "completion", "resolutions", "condition_resolutions"):
        if key in snapshot:
            observation[key] = copy.deepcopy(snapshot[key])
    requests = _STATE._items(observation, "requests")
    observation["requests"] = requests
    for key, kind in (("manual_actions", "action"), ("questions", "question"), ("decisions", "decision")):
        requests.extend(dict(item, kind=kind) for item in _STATE._items(snapshot, key)
                        if _STATE._string(item, "id") not in {_STATE._string(r, "id") for r in requests})
    jobs = _STATE._items(observation, "jobs")
    observation["jobs"] = jobs
    jobs.extend({**item, "status": item.get("status", item["state"])} for item in snapshot["running"]
                if item.get("id") not in {_STATE._string(j, "id") for j in jobs})
    if record_path is not None:
        observation.pop("authority_bridge", None)
        observation = native_owner_projection(record_path, root, scope, observation,
                                              snapshot.get('previous_continuation'), open_tasks, observer_session)
        if observation.get("authority_bridge"):
            for key in ("external_conditions", "condition_resolutions"):
                snapshot[key] = copy.deepcopy(observation.get(key, []))
    snapshot["continuation_observation"] = copy.deepcopy(observation)
    if observation.get("authority_bridge"):
        snapshot["authority_bridge"] = copy.deepcopy(observation["authority_bridge"])
    snapshot["continuation"] = _STATE.reconcile(observation, snapshot.get("previous_continuation"))
    return snapshot


def continuation_overlay(path: Path, repo: Path, scope: str, record_path: Path | None = None, observer_session: str | None = None) -> dict:
    """Read a bound controller frame without executing it or changing run state."""
    if path.is_symlink():
        raise ValueError("controller continuation cannot be a symbolic link")
    with path.open(encoding="utf-8") as stream:
        raw = stream.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError("controller continuation exceeds 1 MiB")
    frame = json.loads(raw)
    if not isinstance(frame, dict) or frame.get("contract") != "implementation-continuation-v1":
        raise ValueError("controller continuation has an unsupported contract")
    binding = frame.get("binding")
    if not isinstance(binding, dict) or not isinstance(binding.get("repo_root"), str):
        raise ValueError("controller continuation repository binding does not match")
    controller_root = Path(binding['repo_root']).resolve()
    if controller_root != repo.resolve():
        if record_path is None:
            raise ValueError('sibling report requires the fully verified native controller record')
        import check_plan_completion as ck
        try:
            record = json.loads(record_path.read_text(encoding='utf-8'))
            if record.get('schema') == 2:
                context, verified = ck.resolve_minor_controller(record_path, record['session_id'],
                    minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
            elif record.get('schema') == 1 and callable(getattr(ck, 'resolve_plan_controller', None)):
                context, verified = ck.resolve_plan_controller(record_path, record['session_id'])
            else:
                raise ValueError('matching native owner helper is unavailable for this report')
            reporter = ck.RepoContext(repo.resolve(), ck.Budget(10))
            if (verified != record or controller_root != context.root.resolve()
                    or ck._minor_module()._common_dir(reporter, repo.resolve())
                        != ck._minor_module()._common_dir(context, context.root)):
                raise ValueError('report checkout does not share the verified controller Git common directory')
        except (OSError, KeyError, TypeError, ck.Malformed, ck._minor_module().ObservationUnavailable) as exc:
            raise ValueError('native controller could not verify this sibling report binding') from exc
    bound_scope = binding.get("scope")
    matches = bound_scope == scope
    if isinstance(bound_scope, str) and Path(bound_scope).is_absolute():
        target = Path(bound_scope).resolve()
        matches = target.is_relative_to(controller_root) and target.suffix == ".md" and target.name.startswith(scope + "-")
    if not matches:
        raise ValueError("controller continuation scope binding does not match")
    if record_path is not None:
        if record_path.exists():
            record = json.loads(record_path.read_text(encoding='utf-8'))
        elif observer_session:
            import check_plan_completion as ck
            resolved = ck.precreate_owner_context(observer_session)
            if resolved is None or resolved[1].resolve() != record_path.resolve():
                raise ValueError('pre-create continuation has no matching native context')
            record = resolved[2]
        else:
            raise ValueError('pre-create continuation requires the owning session')
        if (binding.get('session_id') != record.get('session_id')
                or binding.get('run_nonce') != record.get('nonce')):
            # Reuse the controller's full native-ancestry verifier. The read-only
            # report keeps old jobs/objective and never writes the native owner.
            from types import SimpleNamespace
            helper = native_scripts_dir() / 'run_plan.py'
            spec = importlib.util.spec_from_file_location('_nexus_session_migration', helper)
            controller = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(controller)
            frame = controller.read_continuation(SimpleNamespace(minor=record.get('schema') == 2,
                label=scope, repo_root=controller_root), record_path, record)
            if frame is None:
                raise ValueError('canonical controller observation unavailable for native migration')
            binding = frame['binding']
        if (binding.get("session_id") != record.get("session_id") or binding.get("run_nonce", "") != record.get("nonce", "")
                or not isinstance(binding.get("record_path"), str)
                or Path(binding["record_path"]).resolve() != record_path.resolve()):
            raise ValueError("controller continuation session, nonce or record binding does not match")
    captured = frame.get("captured_at")
    if type(captured) not in (int, float) or not math.isfinite(captured) or captured <= 0:
        raise ValueError("controller continuation requires a finite capture time")
    if not isinstance(frame.get("observation"), dict) or not isinstance(frame.get("disposition"), dict):
        raise ValueError("controller continuation requires observation and disposition objects")
    return {"continuation": frame["observation"], "previous_continuation": frame["disposition"]}


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
    parser.add_argument(
        "--record", help="minor run record path or key; adds measured idle lanes"
    )
    parser.add_argument("--runs-dir", type=Path, help="default ~/.nexus-hub/runs")
    parser.add_argument("--continuation", type=Path, help="bound controller observation frame; read-only")
    parser.add_argument("--observer-session", "--session", dest="observer_session", help="internal host session for report visibility or sealed pre-create context; grants no authority")
    args = parser.parse_args()
    if args.runs_dir:
        os.environ['NEXUS_HUB_RUNS_DIR'] = str(args.runs_dir.resolve())
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        overlay = (
            json.loads(args.overlay.read_text(encoding="utf-8-sig"))
            if args.overlay
            else {}
        )
        now = datetime.now(timezone.utc)
        record_path = None
        if args.record or args.observer_session:
            sys.path.insert(0, str(native_scripts_dir()))
        if args.record:
            spec = importlib.util.spec_from_file_location("nexus_lane_health", Path(__file__).with_name("lane_health.py"))
            lanes = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lanes)
            record_path = lanes.resolve_record(args.record, args.runs_dir or lanes.default_runs_dir())
        elif args.observer_session:
            import check_plan_completion as ck
            resolved = ck.precreate_owner_context(args.observer_session, allow_resume=True)
            if resolved is None:
                raise ValueError('no sealed native pre-create or resume context for this session')
            record_path = resolved[1]
        continuation_path = args.continuation or (record_path.with_name(record_path.stem + ".continuation.json") if record_path else None)
        if continuation_path is not None and (args.continuation or continuation_path.is_file()):
            observed = continuation_overlay(continuation_path, args.repo.resolve(), args.scope, record_path, args.observer_session)
            if "continuation" in overlay or "previous_continuation" in overlay:
                raise ValueError("overlay cannot replace the bound controller continuation")
            overlay.update(observed)
        idle = (
            idle_lanes(args.record, args.runs_dir, args.repo.resolve(), now)
            if args.record and re.fullmatch(r'v\d+\.\d+', args.scope)
            else None
        )
        snapshot = build(
            args.repo.resolve(),
            args.scope,
            overlay,
            args.integration_branch,
            now,
            idle,
            record_path,
            args.observer_session,
        )
    except (OSError, ValueError, TypeError, KeyError, SystemExit) as exc:
        print(f"status snapshot unavailable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(snapshot, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
