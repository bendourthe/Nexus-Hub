#!/usr/bin/env python3
"""Classify parallel worker lanes of a minor run as active, stalled, finished or unknown.

`check` (the default) is read-only: it reads the run record, each lane's heartbeat file,
and its worktree's last commit time and dirty state, then prints a table, the resume
instruction for every stalled lane, and a JSON document. It never kills, restarts, signs
or edits anything. `beat` appends one heartbeat line to the calling lane's own file and
touches nothing else.

Heartbeat files live next to the run record: `<runs-dir>/<record-key>.lanes/<member>.heartbeat`
(default runs dir `~/.nexus-hub/runs`, record key is the record file name without `.json`).
Each line is `<UTC ISO time> <member> <phase> <state>`. When that file is absent, `check` falls back to the
legacy `<temp>/lanes/<member>-heartbeat.log` (lines `<UTC ISO time> <phase> <state>`). A heartbeat state starting with `blocked` (for example `blocked:publication-gate`) makes the lane
`blocked`, never `stalled`, and the text after the colon is shown as `detail`; a later non-blocked heartbeat clears it.
A lane is `ready` when its
heartbeat state is `ready` or only publication/gate tasks remain open; file mtimes of a dirty worktree count as activity.

`check` also lists idle members, which the stalled list cannot see: `unadmitted` (a signed or
amended member with no worker lane and no release tag), `resumable` (a blocked lane whose
named prerequisite version is tagged or finished) and `needs-user` (blocked longer than
`--needs-user-minutes`, default 60, on anything other than an unreleased member).
`notice --repo <path>` prints one line for the newest live minor record of that repository
when it has idle members, and nothing otherwise; the session-start hooks call it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_STALE_MINUTES = 30
DEFAULT_NEEDS_USER_MINUTES = 60
VERSION_TOKEN_RE = re.compile(r"v\d+\.\d+\.\d+")
IDLE_KINDS = ("unadmitted", "resumable", "needs-user")
READY_STATES = {"ready", "implementation-ready"}
FINISHED_STATES = {"done", "finished"}
# Open tasks that wait on publication or the whole-plan gate do not make a lane unfinished.
WAITING_TASK_RE = re.compile(
    r"publish|publication|integration|full local gate|testing and stabilization|stabilization|release",
    re.IGNORECASE)
PHASE_RE = re.compile(r"^## Phase (\d+):\s*(.+?)\s*$", re.MULTILINE)
TASK_RE = re.compile(r"^- \[([ xX])\]\s+T\d+\b(.*)$", re.MULTILINE)


def default_runs_dir() -> Path:
    return Path.home() / ".nexus-hub" / "runs"


def parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _run_git(worktree: Path, *args: str) -> str | None:
    """Run git hidden on Windows; None when git fails or the path is not a repository."""
    try:
        done = subprocess.run(
            ["git", "-C", str(worktree), *args], capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=30, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def resolve_record(record: str | None, runs_dir: Path) -> Path:
    if record:
        direct = Path(record)
        if direct.is_file():
            return direct
        keyed = runs_dir / (record if record.endswith(".json") else record + ".json")
        if keyed.is_file():
            return keyed
        raise SystemExit(f"lane_health: no run record {record}")
    candidates = sorted((p for p in runs_dir.glob("*.json") if "cleanup" not in p.name),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            if "members" in json.loads(path.read_text(encoding="utf-8")):
                return path
        except (OSError, ValueError):
            continue
    raise SystemExit("lane_health: no minor run record found; pass --record")


def find_members(node: object, found: dict[str, dict] | None = None) -> dict[str, dict]:
    """Every nested object carrying `version` and `implementation`, first seen wins."""
    found = {} if found is None else found
    if isinstance(node, dict):
        if isinstance(node.get("version"), str) and isinstance(node.get("implementation"), dict):
            found.setdefault(node["version"], node)
        for value in node.values():
            find_members(value, found)
    elif isinstance(node, list):
        for value in node:
            find_members(value, found)
    return found


def last_heartbeat(path: Path, member: str) -> tuple[datetime, str, str] | None:
    """Last `<time> <member> <phase> <state>` line; also accepts the legacy `<time> <phase> <state>`."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        parts = line.split()
        stamp = parse_time(parts[0]) if parts else None
        if not stamp:
            continue
        if len(parts) >= 4 and parts[1] == member:
            return stamp, parts[2], parts[3]
        if len(parts) >= 3 and parts[1] != member:
            return stamp, parts[1], parts[2]
    return None


def legacy_heartbeat_path(member: str, legacy_dir: Path | None = None) -> Path:
    """Transitional location used before run-scoped files: `<temp>/lanes/<member>-heartbeat.log`."""
    return (legacy_dir or Path(tempfile.gettempdir()) / "lanes") / f"{member}-heartbeat.log"


def newest_file_mtime(worktree: Path) -> datetime | None:
    """Newest mtime among modified tracked and untracked (not ignored) files; .git is never read."""
    listing = _run_git(worktree, "ls-files", "-m", "-o", "--exclude-standard")
    newest = None
    for name in (listing or "").splitlines():
        try:
            stamp = (worktree / name).stat().st_mtime
        except OSError:
            continue
        newest = stamp if newest is None or stamp > newest else newest
    return datetime.fromtimestamp(newest, timezone.utc) if newest is not None else None


def plan_progress(worktree: Path, plan_path: str) -> tuple[int | None, str, bool, bool]:
    """Return (last fully completed phase, its title, every phase complete, only waiting tasks open)."""
    try:
        body = (worktree / plan_path).read_text(encoding="utf-8")
    except OSError:
        return None, "", False, False
    marks = list(PHASE_RE.finditer(body))
    last, title, all_done = None, "", bool(marks)
    open_titles: list[str] = []
    ticked = 0
    for index, match in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(body)
        tasks = TASK_RE.findall(body[match.end():end])
        open_titles += [text for mark, text in tasks if mark == " "]
        ticked += sum(1 for mark, _ in tasks if mark != " ")
        if tasks and all(mark != " " for mark, _ in tasks):
            if all_done:
                last, title = int(match.group(1)), match.group(2)
        else:
            all_done = False
    waiting = bool(ticked) and bool(open_titles) and all(WAITING_TASK_RE.search(t) for t in open_titles)
    return last, title, all_done, waiting


def is_merged(repo_root: Path | None, member: dict) -> bool:
    """True when the member's release tag exists or its own commits are already in the target."""
    if repo_root is None or not repo_root.is_dir():
        return False
    tag = member.get("tag")
    if tag and _run_git(repo_root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}") is not None:
        return True
    impl, target = member["implementation"], member.get("target_branch") or "develop"
    head = _run_git(repo_root, "rev-parse", "-q", "--verify", f"refs/heads/{impl.get('branch')}")
    base = impl.get("base_head")
    if not head or head == base:
        return False
    for ref in (f"origin/{target}", target):
        if _run_git(repo_root, "merge-base", "--is-ancestor", head, ref) is not None:
            return True
    return False


def inspect_lane(version: str, member: dict, lane_dir: Path, now: datetime,
                 threshold: timedelta, repo_root: Path | None = None,
                 legacy_dir: Path | None = None) -> dict:
    impl = member["implementation"]
    worktree = Path(str(impl.get("worktree", "")))
    present = bool(impl.get("worktree")) and worktree.is_dir()
    beat = last_heartbeat(lane_dir / f"{version}.heartbeat", version)
    legacy = False
    if beat is None:
        beat = last_heartbeat(legacy_heartbeat_path(version, legacy_dir), version)
        legacy = beat is not None
    commit_at, head, dirty = None, None, None
    if present and _run_git(worktree, "rev-parse", "--git-dir") is not None:
        stamp = _run_git(worktree, "log", "-1", "--format=%cI")
        commit_at = parse_time(stamp) if stamp else None
        head = _run_git(worktree, "rev-parse", "--short", "HEAD")
        status = _run_git(worktree, "status", "--porcelain")
        dirty = None if status is None else bool(status)
    phase, title, all_done, waiting = (plan_progress(worktree, member.get("plan_path", ""))
                                       if present else (None, "", False, False))
    file_at = newest_file_mtime(worktree) if dirty else None
    signals = {"heartbeat": beat[0] if beat else None, "commit": commit_at, "file-mtime": file_at}
    known = {name: t for name, t in signals.items() if t}
    signal = max(known, key=known.get) if known else "none"
    last = known[signal] if known else None
    merged = is_merged(repo_root, member)
    beat_state = beat[2].lower() if beat else ""
    detail = None
    if merged or beat_state in FINISHED_STATES or (all_done and dirty is False):
        state = "finished"
    elif beat_state.startswith("blocked"):
        state = "blocked"
        detail = beat[2].partition(":")[2] or None
    elif beat_state in READY_STATES or (waiting and dirty is False):
        state = "ready"
    elif last is None or (not present and not beat):
        state = "unknown"
    elif not present:
        state = "unknown" if now - last > threshold else "active"
    else:
        state = "stalled" if now - last > threshold else "active"
    idle = int((now - last).total_seconds() // 60) if last else None
    lane = {
        "member": version, "state": state, "branch": impl.get("branch"),
        "worktree": str(worktree) if impl.get("worktree") else None,
        "worktree_present": present, "merged": merged, "signal": signal, "detail": detail,
        "legacy_heartbeat": legacy, "plan": member.get("plan_path"),
        "last_heartbeat": beat[0].isoformat() if beat else None,
        "heartbeat_phase": beat[1] if beat else None,
        "heartbeat_state": beat[2] if beat else None,
        "last_commit": commit_at.isoformat() if commit_at else None, "head": head,
        "last_file_change": file_at.isoformat() if file_at else None,
        "dirty": dirty, "idle_minutes": idle, "last_completed_phase": phase,
        "last_completed_phase_title": title,
    }
    if state == "stalled":
        lane["resume"] = resume_instruction(lane)
    return lane


def record_versions(data: dict) -> list[str]:
    """Every member version the record signs or amends in, in record order."""
    seen: list[str] = []
    for key in ("members", "minor_amendment_members"):
        for entry in data.get(key) or []:
            version = entry.get("version") if isinstance(entry, dict) else entry
            if isinstance(version, str) and VERSION_TOKEN_RE.fullmatch(version) and version not in seen:
                seen.append(version)
    return seen


def tag_exists(repo_root: Path | None, version: str) -> bool:
    return (repo_root is not None and repo_root.is_dir()
            and _run_git(repo_root, "rev-parse", "-q", "--verify", f"refs/tags/{version}") is not None)


def _vkey(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version[1:].split("."))


def classify_idle(lanes: list[dict], versions: list[str], shipped, now: datetime,
                  needs_user_minutes: float = DEFAULT_NEEDS_USER_MINUTES) -> list[dict]:
    """Idle members; `shipped(version)` says whether that version has a release tag."""
    by_member = {lane["member"]: lane for lane in lanes}

    def done(version: str) -> bool:
        return shipped(version) or by_member.get(version, {}).get("state") == "finished"

    idle: list[dict] = []
    for version in versions:
        if version not in by_member and not shipped(version):
            idle.append({"member": version, "kind": "unadmitted",
                         "detail": "in the minor record with no worker lane"})
    for lane in lanes:
        if lane["state"] != "blocked":
            continue
        blocker = lane.get("detail") or lane.get("heartbeat_state") or "unnamed blocker"
        named = [v for v in VERSION_TOKEN_RE.findall(blocker) if v != lane["member"]]
        if named and all(done(v) for v in named):
            idle.append({"member": lane["member"], "kind": "resumable",
                         "detail": f"{', '.join(named)} released; blocker {blocker} is stale"})
            continue
        if named:
            continue  # waits on an unreleased member, which is not a user action
        since = parse_time(lane["last_heartbeat"]) if lane.get("last_heartbeat") else None
        minutes = int((now - since).total_seconds() // 60) if since else lane.get("idle_minutes")
        if minutes is not None and minutes >= needs_user_minutes:
            idle.append({"member": lane["member"], "kind": "needs-user",
                         "detail": f"blocked {minutes} min on {blocker}"})
    return sorted(idle, key=lambda item: (_vkey(item["member"]), IDLE_KINDS.index(item["kind"])))


def record_repo_root(data: dict) -> Path | None:
    """The record's repository root, falling back to the implementation controller's root."""
    controller = data.get("implementation_controller") or {}
    for value in (data.get("repo_root"), controller.get("repo_root")):
        if isinstance(value, str) and value and Path(value).is_dir():
            return Path(value)
    root = data.get("repo_root")
    return Path(root) if isinstance(root, str) and root else None


def release_tags(repo_root: Path) -> set[str]:
    return set((_run_git(repo_root, "tag", "-l", "v*") or "").split())


def light_lanes(data: dict, record: Path, now: datetime, tags: set[str]) -> list[dict]:
    """Heartbeat-only lanes for the session-start notice: no worktree git calls, so it stays fast."""
    lane_dir = record.parent / f"{record.stem}.lanes"
    lanes = []
    for version in sorted(find_members(data), key=_vkey):
        beat = last_heartbeat(lane_dir / f"{version}.heartbeat", version)
        state_text = beat[2] if beat else ""
        blocked = state_text.lower().startswith("blocked")
        state = "finished" if version in tags else "blocked" if blocked else "other"
        lanes.append({"member": version, "state": state,
                      "detail": (state_text.partition(":")[2] or None) if blocked else None,
                      "heartbeat_state": state_text or None,
                      "last_heartbeat": beat[0].isoformat() if beat else None,
                      "idle_minutes": int((now - beat[0]).total_seconds() // 60) if beat else None})
    return lanes


def inspect_record(data: dict, record: Path, now: datetime, stale_minutes: float,
                   needs_user_minutes: float, repo_root: Path | None = None,
                   legacy_dir: Path | None = None) -> tuple[list[dict], list[dict]]:
    """Lanes and idle members of one record."""
    lane_dir = record.parent / f"{record.stem}.lanes"
    root = repo_root or record_repo_root(data)
    threshold = timedelta(minutes=stale_minutes)
    lanes = [inspect_lane(v, m, lane_dir, now, threshold, root, legacy_dir)
             for v, m in sorted(find_members(data).items())]
    idle = classify_idle(lanes, record_versions(data), lambda v: tag_exists(root, v), now,
                         needs_user_minutes)
    return lanes, idle


def resume_instruction(lane: dict) -> str:
    done = lane["last_completed_phase"]
    after = f"after Phase {done} ({lane['last_completed_phase_title']})" if done else "from the first open phase"
    dirty = "It has uncommitted edits: keep them and finish or commit them. " if lane["dirty"] else ""
    return (
        f"Resume lane {lane['member']}: work only in worktree {lane['worktree']} on branch "
        f"{lane['branch']} (last commit {lane['head']}). Prompt for the session: \"You are the worker "
        f"for {lane['member']}. First run lane_health.py. Continue plan {lane['plan']} {after} from "
        f"the last local commit. {dirty}Do not push, merge or release; return the worker contract "
        f"when implementation-ready.\"")


def check(args: argparse.Namespace) -> int:
    runs_dir = Path(args.runs_dir) if args.runs_dir else default_runs_dir()
    record = resolve_record(args.record, runs_dir)
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"lane_health: cannot read {record}: {exc}")
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    legacy_dir = Path(args.legacy_dir) if args.legacy_dir else None
    repo_root = Path(args.repo) if args.repo else None
    lanes, idle_members = inspect_record(data, record, now, args.stale_minutes,
                                         args.needs_user_minutes, repo_root, legacy_dir)
    report = {"record": record.stem, "checked": now.isoformat(),
              "stale_minutes": args.stale_minutes, "lanes": lanes,
              "stalled": [lane["member"] for lane in lanes if lane["state"] == "stalled"],
              "idle": idle_members}
    if args.json_only:
        print(json.dumps(report, indent=2))
        return 0
    print(f"Lane health for record {record.stem[:12]} (stalled after {args.stale_minutes} min idle)")
    print(f"{'member':<10} {'state':<9} {'idle':>6}  {'signal':<10} {'dirty':<5} {'last phase':<10} {'branch':<30} detail")
    for lane in lanes:
        idle = "-" if lane["idle_minutes"] is None else f"{lane['idle_minutes']}m"
        dirty = {True: "yes", False: "no", None: "?"}[lane["dirty"]]
        phase = "-" if lane["last_completed_phase"] is None else f"Phase {lane['last_completed_phase']}"
        print(f"{lane['member']:<10} {lane['state']:<9} {idle:>6}  {lane['signal']:<10} {dirty:<5} "
              f"{phase:<10} {lane['branch']:<30} {lane['detail'] or ''}".rstrip())
    for lane in lanes:
        if lane["state"] == "stalled":
            print(f"\nSTALLED {lane['member']}: {lane['resume']}")
    for item in idle_members:
        print(f"IDLE {item['member']} {item['kind']}: {item['detail']}")
    print("\n" + json.dumps(report))
    return 0


def _common_dir(path: Path) -> str | None:
    found = _run_git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return str(Path(found).resolve()).casefold() if found else None


def notice_line(data: dict, idle: list[dict]) -> str:
    minor = data.get("minor") or data.get("scope") or "run"
    listed = ", ".join(f"{item['member']} {item['kind']}" for item in idle)
    noun = "member" if len(idle) == 1 else "members"
    return (f"Minor {minor}: {len(idle)} idle {noun} ({listed}). Dispatch eligible members "
            f"(implement-phase runbook, Refill available slots).")


def _records(args: argparse.Namespace, runs_dir: Path) -> list[Path]:
    if args.record:
        return [resolve_record(args.record, runs_dir)]
    return sorted((p for p in runs_dir.glob("*.json") if "cleanup" not in p.name),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def _owns(data: dict, want: str) -> bool:
    controller = (data.get("implementation_controller") or {}).get("git_common_dir")
    if isinstance(controller, str) and controller and str(Path(controller).resolve()).casefold() == want:
        return True
    root = record_repo_root(data)
    return root is not None and root.is_dir() and _common_dir(root) == want


def notice(args: argparse.Namespace) -> int:
    """One line for the newest live minor record of --repo with idle members; silent otherwise."""
    try:
        repo = Path(args.repo)
        want = _common_dir(repo)
        if want is None:
            return 0
        runs_dir = Path(args.runs_dir) if args.runs_dir else default_runs_dir()
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        for path in _records(args, runs_dir):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if (not isinstance(data, dict) or "minor" not in data or data.get("completed")
                    or data.get("pause") or not _owns(data, want)):
                continue
            tags = release_tags(repo)
            idle = classify_idle(light_lanes(data, path, now, tags), record_versions(data),
                                 tags.__contains__, now, args.needs_user_minutes)
            if idle:
                print(notice_line(data, idle))
            return 0
    except (OSError, ValueError, SystemExit):
        return 0
    return 0


def beat(args: argparse.Namespace) -> int:
    runs_dir = Path(args.runs_dir) if args.runs_dir else default_runs_dir()
    record = resolve_record(args.record, runs_dir)
    lane_dir = record.parent / f"{record.stem}.lanes"
    lane_dir.mkdir(parents=True, exist_ok=True)
    clean = lambda text: re.sub(r"\s+", "-", text.strip()) or "-"  # noqa: E731
    stamp = (parse_time(args.now) if args.now else datetime.now(timezone.utc))
    line = f"{stamp.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} " \
           f"{clean(args.member)} {clean(args.phase)} {clean(args.state)}\n"
    with open(lane_dir / f"{clean(args.member)}.heartbeat", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")
    for name in ("check", "beat", "notice"):
        p = sub.add_parser(name)
        p.add_argument("--record", help="run record path or key (default: newest minor record)")
        p.add_argument("--runs-dir", help="default ~/.nexus-hub/runs")
        p.add_argument("--now", help="override the clock (ISO time), for tests")
        if name in ("check", "notice"):
            p.add_argument("--needs-user-minutes", type=float, default=DEFAULT_NEEDS_USER_MINUTES)
        if name == "check":
            p.add_argument("--legacy-dir", help="legacy heartbeat folder, default <temp>/lanes")
            p.add_argument("--stale-minutes", type=float, default=DEFAULT_STALE_MINUTES)
            p.add_argument("--json", dest="json_only", action="store_true", help="JSON only")
            p.add_argument("--repo", help="repository for tag lookups (default: the record's root)")
        elif name == "notice":
            p.add_argument("--repo", required=True, help="repository whose live minor record to read")
        else:
            p.add_argument("--member", required=True)
            p.add_argument("--phase", required=True, help="e.g. start, phase-2, wait")
            p.add_argument("--state", required=True, help="e.g. started, ended, waiting, ready")
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] not in ("check", "beat", "notice", "-h", "--help"):
        raw.insert(0, "check")
    args = parser.parse_args(raw)
    if args.cmd == "notice":
        return notice(args)
    return beat(args) if args.cmd == "beat" else check(args)


if __name__ == "__main__":
    sys.exit(main())
