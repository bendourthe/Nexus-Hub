#!/usr/bin/env python3
"""Render portable status and select cadence from evidence; never write run state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit

CONTRACT = "portable-status-v1"
EVENTS = ("start", "resume", "request", "checkpoint", "turn-end", "progress")
RESOURCES = ("SKILL.md", "references/progress-reporting.md", "references/status-formats.md",
             "references/status-snapshot.json", "scripts/status_report.py", "scripts/status_snapshot.py",
             "scripts/continuation_state.py")

_STATE_SPEC = importlib.util.spec_from_file_location("nexus_continuation_state", Path(__file__).with_name("continuation_state.py"))
_STATE = importlib.util.module_from_spec(_STATE_SPEC)
_STATE_SPEC.loader.exec_module(_STATE)


FILLED, EMPTY = "\u25b0", "\u25b1"
VALUE_SEP = "   \u00b7   "  # three literal spaces each side, as specified; no entities
GOALS_ICON, WAIT_ICON, RUN_ICON = "\U0001F3AF", "\U0001F64B", "\U0001F504"
RELEASE_ICON, PROGRESS_ICON = "\U0001F680", "\U0001F4CA"
IDLE_ICON = "\u26a0\ufe0f"
IDLE_KINDS = ("unadmitted", "resumable", "needs-user")
CELL_MAX = 48
OPTION_MAX = 72  # decision options must stay readable in full
# A token with any of these is shown as a code span: hosts (Codex, Claude Code) read
# backslash-paren and dollar pairs as math and read * _ [ ] as emphasis or links.
_LITERAL = re.compile(r"[$*_\[\]\\`&<>]")


def shorten(value: str, limit: int) -> str:
    """Drop trailing parentheticals first, then cut at a word boundary; never mid-parenthesis."""
    while len(value) > limit:
        match = re.search(r"\s*\([^()]*\)\s*$", value)
        if not match or match.start() == 0:
            break
        value = value[: match.start()]
    if len(value) <= limit:
        return value
    cut = value[: limit - 3]
    if " " in cut and value[limit - 3] != " ":
        cut = cut.rsplit(" ", 1)[0]
    if cut.count("(") > cut.count(")"):
        cut = cut[: cut.rindex("(")]
    return cut.rstrip() + "..."


def _literal(token: str) -> str:
    """Wrap a token hosts could read as math or emphasis in a code span; edge punctuation stays outside."""
    if not _LITERAL.search(token):
        return token
    head, core, tail = re.fullmatch(r"([(\"']*)(.*?)([).,;:\"']*)", token).groups()
    return f"{head}`{core.replace(chr(96), chr(39))}`{tail}"


def text(value: object, limit: int | None = None) -> str:
    """Keep evidence on one line, neutralize Markdown, HTML, math and table syntax, cap length."""
    value = " ".join(str(value).split())
    value = "".join(c for c in value if ord(c) >= 32 and ord(c) != 127)
    if limit is not None:
        value = shorten(value, limit)
    return " ".join(_literal(t) for t in value.split(" ")).replace("|", "\\|")


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("observed_at requires a timezone")
    return result


_UNKNOWN = re.compile(r"\bunknown\b", re.IGNORECASE)
NO_TASKS = "no task list"
_MEASURE = "measure it with scripts/status_snapshot.py; N/A means not started or already released"


def measured(value: object, where: str) -> None:
    """Elapsed and remaining are measured or N/A, never a placeholder."""
    if isinstance(value, str) and _UNKNOWN.search(value):
        raise ValueError(f"{where} is 'unknown'; {_MEASURE}")


def counts(row: dict, required: bool = False) -> tuple[int | None, int | None]:
    if "done" not in row or "total" not in row:
        raise ValueError("counts require explicit done and total")
    done, total = row["done"], row["total"]
    if done is None and total is None:
        if required:
            raise ValueError(f"version {row.get('name')} has no task counts; {_MEASURE}")
        return None, None
    if type(done) is not int or type(total) is not int or not 0 <= done <= total:
        raise ValueError("counts require integers with 0 <= done <= total, or two nulls")
    return done, total


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise TypeError("snapshot must be an object")
    for key in ("run_id", "scope", "observed_at", "source", "elapsed", "remaining", "estimate_basis"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"snapshot requires nonempty {key}")
    timestamp(data["observed_at"])
    if type(data.get("active")) is not bool:
        raise ValueError("active must be a boolean")
    if not isinstance(data.get("last_released"), str) or not data["last_released"].strip():
        raise ValueError("last_released must name a version or say 'none released yet'")
    measured(data["elapsed"], "total elapsed")
    measured(data["remaining"], "total remaining")
    release = data.get("next_release")
    if release is not None:
        required = ("version", "remaining", "condition", "confidence", "basis")
        if not isinstance(release, dict) or any(not isinstance(release.get(k), str) or not release[k].strip() for k in required):
            raise ValueError("next_release requires nonempty version, remaining, condition, confidence and basis")
        if release["confidence"] not in ("low", "medium", "high"):
            raise ValueError("release confidence must be low, medium or high")
        measured(release["remaining"], "next release ETA")
    left = data.get("versions_left")
    if type(left) is not int or left < 0:
        raise ValueError("versions_left must be a nonnegative integer")
    fields = {"rows": ("name", "goals", "state", "elapsed", "remaining", "dependency"),
              "goals": ("goal", "scope", "done_when", "state"),
              "decisions": ("id", "title", "detail"),
              "running": ("name", "state", "elapsed", "remaining")}
    for key, required in fields.items():
        items = data.get(key)
        if not isinstance(items, list) or (key in ("rows", "goals") and not items):
            raise ValueError(f"{key} must be a list; rows and goals cannot be empty")
        for item in items:
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in required):
                raise ValueError(f"{key} item requires strings: {', '.join(required)}")
            if key in ("rows", "running"):
                counts(item, required=key == "rows")
                measured(item["elapsed"], f"{item['name']} elapsed")
                measured(item["remaining"], f"{item['name']} remaining")
            if key == "running":
                # N/A means not started or released; a running item is neither.
                for field in ("elapsed", "remaining"):
                    if item[field].strip().upper() == "N/A":
                        raise ValueError(f"running item {item['name']} {field} is N/A; {_MEASURE}")
            if key == "running" and item.get("url") is not None:
                url = item["url"]
                if not isinstance(url, str) or any(c.isspace() or ord(c) < 32 for c in url):
                    raise ValueError("running URLs require a whitespace-free HTTP(S) URL")
                parts = urlsplit(url)
                if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
                    raise ValueError("running URLs require HTTP(S), a host and no credentials")
            if key == "decisions":
                if item.get("reply") is not None and (not isinstance(item["reply"], str) or not item["reply"].strip()):
                    raise ValueError("decision reply must be a nonempty string when present")
                options = item.get("options")
                if options is not None and (not isinstance(options, list) or any(
                    not isinstance(o, dict) or not all(isinstance(o.get(k), str) and o[k].strip() for k in ("option", "effect"))
                    for o in options
                )):
                    raise ValueError("decision options require option/effect entries when present")
    ids = [d["id"] for d in data["decisions"]]
    if len(set(ids)) != len(ids):
        raise ValueError("decision ids must be unique")
    idle = data.get("idle_lanes")
    if idle is not None:
        if not isinstance(idle, list) or any(
            not isinstance(i, dict) or i.get("kind") not in IDLE_KINDS
            or not all(isinstance(i.get(k), str) and i[k].strip() for k in ("member", "detail"))
            for i in idle
        ):
            raise ValueError("idle_lanes items require member, detail and a known kind")
    continuation(data)


def continuation(data: dict) -> dict:
    """Use the same disposition as the controller; report text never grants authority."""
    observation = copy.deepcopy(data.get("continuation_observation", data.get("continuation", {})))
    if not isinstance(observation, dict):
        raise ValueError("continuation must contain structured observations")
    observation.setdefault("objective", data.get("objective") or "; ".join(g["goal"] for g in data["goals"]))
    done, total = aggregate(data)
    observation["remaining_tasks"] = total - done if total is not None else 0
    for key in ("work", "native_goal", "external_conditions", "resolutions", "condition_resolutions", "paused", "completion"):
        if key in data:
            observation[key] = copy.deepcopy(data[key])
    requests = _STATE._items(observation, "requests")
    observation["requests"] = requests
    known = {_STATE._string(r, "id") for r in requests}
    for source, kind in (("manual_actions", "action"), ("questions", "question"), ("decisions", "decision")):
        for item in _STATE._items(data, source):
            _STATE._string(item, "id")
            if item["id"] not in known:
                requests.append(dict(item, kind=kind))
                known.add(item["id"])
    jobs = _STATE._items(observation, "jobs")
    observation["jobs"] = jobs
    known_jobs = {_STATE._string(j, "id") for j in jobs}
    for item in data["running"]:
        if item.get("id") not in known_jobs:
            jobs.append({**item, "status": item.get("status", item["state"])})
    state = _STATE.reconcile(observation, data.get("previous_continuation"))
    if "continuation_observation" in data and state != data.get("continuation"):
        raise ValueError("producer observation does not match its canonical continuation")
    return state


def state_heading(state: dict) -> str:
    if state["state"] in {"waiting_owner_action", "waiting_decision"}:
        return f"Waiting for you: {text(state['reason'])}"
    if state["state"] in {"waiting_job", "blocked_external"}:
        return f"Waiting for {text(state['reason'])}"
    if state["state"] == "paused":
        return "Explicitly paused by the owner"
    if state["state"] == "verified_complete":
        return f"Verified complete: {text(state['reason'])}"
    return ""


def pending_decisions(state: dict) -> list[dict]:
    """The rendered and receipted choices come from the same pending requests."""
    return [dict(request, detail=request.get("detail") or request["title"])
            for request in state["requests"] if request["kind"] == "decision" and not request.get("native_reconciliation")]


def estimate_parts(data: dict, state: dict) -> list[str]:
    """Explain waiting assumptions without replacing measured counts or estimates."""
    if state["state"] == "verified_complete":
        return []
    parts = []
    if data["remaining"].strip().upper().startswith("N/A"):
        parts.append("No duration estimate is available for the outstanding obligations. N/A does not mean the objective is complete.")
    condition = ""
    if state["state"] == "paused":
        condition = "the owner's explicit resume"
    elif state["state"] == "waiting_owner_action":
        request = next(r for kind in ("action", "question") for r in state["requests"] if r["kind"] == kind and not r.get("native_reconciliation"))
        condition = (f"{request['title']} ({request['expected_result']})" if request["kind"] == "action"
                     else f"your answer to {request['title']}")
    elif state["state"] == "waiting_decision":
        condition = f"your decision on {state['reason']}"
    elif state["state"] == "waiting_job":
        job = state["jobs"][0]
        condition = f"{job['name']}: {job['resume_when']}"
    elif state["state"] == "blocked_external":
        dependency = state["external_conditions"][0]
        condition = f"{dependency['title']}: {dependency['resume_when']}"
    if condition:
        parts.append(f"Whole-objective time estimates are conditional on {text(condition)}; they exclude any unbounded waiting time.")
    return parts


def required_parts(state: dict) -> list[str]:
    """Full steps and exact handles are never shortened to fit a table cell."""
    parts = []
    if state.get('objective_complete') is False:
        parts.extend(['---', '### Objective reconciliation',
            'The signed native scope is recovered. The controller must still recover any additional user goal wording; the complete original objective is not yet verified.'])
    native = state["native_goal"]
    if native.get("status") in {"blocked", "stalled"}:
        capability = "reported available" if native.get("resume_supported") is True else "unavailable or unverified"
        parts.extend(["---", "### Native goal observation",
                      f"Observed {text(native['status'])} at {text(native['observed_at'])}; resume API: {capability}.",
                      "Native state reconciliation remains required. This marker does not stop other authorized work."])
    actions = [r for r in state["requests"] if (r["kind"] == "action" or r.get("manual_capture") is True) and not r.get("native_reconciliation")]
    if actions:
        parts.extend(["---", "### Required actions"])
        for index, action in enumerate(actions, 1):
            if action.get("review_page"):
                review = str(action['review_page']).replace('\r\n', '\n').replace('\r', '\n')
                review = ''.join(char for char in review if char == '\n' or 32 <= ord(char) != 127)
                longest = max((len(match.group()) for match in re.finditer(r'`+', review)), default=0)
                fence = '`' * max(3, longest + 1)
                parts.extend(['Native scope review:', fence + 'text\n' + review + '\n' + fence])
            parts.extend([f"#### {index}. {text(action['title'])}",
                          "Prerequisites: " + "; ".join(text(s) for s in action["prerequisites"]),
                          "\n".join(f"{n}. {text(step)}" for n, step in enumerate(action["steps"], 1)),
                          f"Expected result: {text(action['expected_result'])}",
                          f"Acknowledgment: {text(action['acknowledgment'])}"])
    questions = [r for r in state["requests"] if r["kind"] == "question" and not r.get("native_reconciliation")]
    if questions:
        parts.extend(["---", "### Source questions", "\n".join(
            f"{n}. {text(question.get('question') or question['title'])}" for n, question in enumerate(questions, 1))])
    internal = [request['native_reconciliation'] for request in state['requests'] if request.get('native_reconciliation')]
    if internal:
        parts.extend(['---', '### Controller reconciliation'])
        for item in internal:
            parts.extend([text(item['reason']), 'Evidence: ' + text(item['evidence']),
                'Resume when: ' + text(item['resume_when']), 'Provenance: ' + text(item['provenance_sha256'])])
    if state["jobs"]:
        parts.extend(["---", "### Process observations"])
        for job in state["jobs"]:
            identity = job.get("handle") or job["url"]
            if job.get("handle") and job.get("url") and job["url"] not in str(job.get("evidence")):
                identity = f"{identity} ({job['url']})"
            parts.extend([f"- {text(job['name'])}: {text(identity)}; observed {text(job['status'])} at {text(job['observed_at'])}.",
                          f"  Evidence: {text(job['evidence'])}", f"  Resume when: {text(job['resume_when'])}"])
    if state["external_conditions"]:
        parts.extend(["---", "### External conditions"])
        for item in state["external_conditions"]:
            parts.extend([f"- {text(item['title'])}: {text(item['evidence'])}",
                          f"  Observed: {text(item['observed_at'])}; resume when: {text(item['resume_when'])}"])
    return parts


def progress_parts(done: int | None, total: int | None) -> tuple[str, str]:
    """Return the bar-and-percent text and the done/total text."""
    if done is None:  # only a running item without tasks, such as a CI job
        return NO_TASKS, NO_TASKS
    if total == 0:
        return "N/A", "0/0"
    percent = (100 * done + total // 2) // total
    filled = min(10, (10 * done) // total)
    return f"{FILLED * filled}{EMPTY * (10 - filled)} {percent}%", f"{done}/{total}"


def aggregate(data: dict) -> tuple[int | None, int | None]:
    values = [counts(row) for row in data["rows"]]
    if any(done is None for done, _ in values):
        return None, None
    return sum(d for d, _ in values), sum(t for _, t in values)


def cell(value: object) -> str:
    return text(value, CELL_MAX)


def table(headers: tuple[str, ...], rows: list[list[str]]) -> str:
    """Pad every column to its widest cell so the source text lines up."""
    widths = [max(3, *(len(r[i]) for r in [list(headers), *rows])) for i in range(len(headers))]
    def line(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    return "\n".join([line(headers), "| " + " | ".join("-" * w for w in widths) + " |", *map(line, rows)])


def running_label(row: dict) -> str:
    label = cell(row["name"])
    if row.get("url"):
        return f"[{label}]({quote(row['url'], safe=':/?=&%#@')})"
    return label


def keycap(value: str) -> str:
    return "".join(c + "\ufe0f\u20e3" for c in value) if value.isdigit() else ""


def remaining_with_dependency(row: dict) -> str:
    dep = row["dependency"].strip()
    if dep.lower() == "none":
        return cell(row["remaining"])
    return cell(f"{row['remaining']} ({dep if dep.lower().startswith('after ') else 'after ' + dep})")


def authority_parts(data: dict) -> list[str]:
    """Never truncate the distinction between captured permission and observed execution."""
    rows = data.get("authority_bridge", [])
    if not isinstance(rows, list) or len(rows) > 16:
        raise ValueError("native permission observations must be a bounded list")
    labels = {".6-release-notes": "Release6 notes", ".6-repo-description": "Repository description",
              ".9-t027-budget": "T027 budget", "maintenance-bootstrap-publication": "Maintenance publication"}
    parts = ["---", "### Native permissions"] if rows else []
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"receipt_id", "kind", "capture", "permission", "enforcement", "execution"}
                or not isinstance(row["kind"], str) or row["kind"] not in labels
                or row["capture"] != "verified" or row["permission"] != "captured"
                or row["enforcement"] not in {"guarded-consumer-required", "inactive:no-Claude;no-pre-call-billing-limiter", *{"blocked:attribution:" + reason for reason in ("guard-inactive", "repository-overrides-guard", "guard-missing-or-modified", "guard-version-differs", "guard-interpreter-unavailable", "hook-missing-or-modified", "preflight-unverified")}}
                or row["execution"] not in {"not observed", "ambiguous", "completed", "prepared; release not observed", "published notes verified", "push observed; PR and merge not observed", "PR observed; merge not observed", "merge observed"}
                or not isinstance(row["receipt_id"], str) or re.fullmatch(r"[0-9a-f]{64}", row["receipt_id"]) is None):
            raise ValueError("native permission observation is incomplete")
        enforcement = "inactive (no Claude; billing guard unavailable)" if row["kind"] == ".9-t027-budget" else "guarded consumer required"
        if row["enforcement"].startswith("blocked:attribution:"):
            enforcement = "blocked (attribution " + row["enforcement"].split(":", 2)[2].replace("-", " ") + "; review authorized guard repair, then retry same push consumer)"
        parts.append(f"- {labels[row['kind']]}: capture verified; permission captured; enforcement {enforcement}; effect {row['execution']}.")
    return parts


def render(data: dict, mode: str) -> str:
    validate(data)
    state = continuation(data)
    data = copy.deepcopy(data)
    active_jobs = {job["id"] for job in state["jobs"]}
    data["running"] = [job for job in data["running"] if job.get("id") in active_jobs]
    data["decisions"] = pending_decisions(state)
    if mode not in ("compact", "full"):
        raise ValueError("mode must be compact or full")
    done, total = aggregate(data)
    released = text(data["last_released"])
    bar, tasks = progress_parts(done, total)
    if mode == "compact":
        return _compact(data, bar, tasks, released, state) + ("\n\n" + "\n".join(authority_parts(data)) if data.get("authority_bridge") else "")
    rows = []
    for r in data["rows"]:
        rbar, rtasks = progress_parts(*counts(r))
        rows.append([f"**{cell(r['name'])}**", cell(r["goals"]), rbar, rtasks, cell(r["elapsed"]), remaining_with_dependency(r)])
    rows.append(["**Total**", "", f"**{bar}**", f"**{tasks}**", f"**{cell(data['elapsed'])}**", f"**{cell(data['remaining'])}**"])
    parts = [*( [state_heading(state)] if state_heading(state) else []), "## Progress Update", f"### {RELEASE_ICON} Release status", release_table(data, bar, tasks, released),
             *estimate_parts(data, state),
             f"### {PROGRESS_ICON} Version progress",
             table(("Version", "Goals", "Progress", "Tasks", "Elapsed", "Remaining"), rows),
             *idle_parts(data, full=True),
             *required_parts(state),
             *authority_parts(data),
             "---", f"### {GOALS_ICON} Goals",
             table(("Goal", "Scope", "Done when", "State"),
                   [[cell(g[k]) for k in ("goal", "scope", "done_when", "state")] for g in data["goals"]]),
             "---", f"### {WAIT_ICON} Decisions waiting"]
    if not data["decisions"]:
        parts.append("No decisions waiting.")
    for number, decision in enumerate(data["decisions"], 1):
        parts.extend(decision_parts(decision, with_detail=True, number=number))
    parts.extend(["---", f"### {RUN_ICON} Running"])
    if not data["running"]:
        parts.append(empty_running(state))
    else:
        run_rows = []
        for r in data["running"]:
            rbar, rtasks = progress_parts(*counts(r))
            run_rows.append([running_label(r), rbar, rtasks, cell(r["state"]), cell(r["elapsed"]), cell(r["remaining"])])
        parts.append(table(("Item", "Progress", "Tasks", "State", "Elapsed", "Remaining"), run_rows))
    parts.extend([f"State: {state['state'].replace('_', ' ')}", f"*Source: {text(data['source'], 100)}*"])
    return "\n\n".join(parts) + "\n"


def idle_parts(data: dict, full: bool) -> list[str]:
    """Idle lanes warning: members with no worker, or blocked lanes that can move; empty when none."""
    idle = data.get("idle_lanes") or []
    if not idle:
        return []
    head = ["---", f"### {IDLE_ICON} Idle lanes",
            f"{len(idle)} {'member is' if len(idle) == 1 else 'members are'} idle: dispatch eligible "
            "members (implement-phase runbook, Refill available slots)."]
    if full:
        return [*head, table(("Member", "Kind", "Detail"),
                             [[cell(i["member"]), cell(i["kind"]), cell(i["detail"])] for i in idle])]
    return [*head, "\n".join(f"- {text(i['member'])} ({text(i['kind'])}): {text(i['detail'])}" for i in idle)]


def decision_parts(decision: dict, with_detail: bool, number: int = 1) -> list[str]:
    """One decision as a heading, optional explanation bullet, options table and optional reply line."""
    icon = keycap(str(number))
    parts = [f"#### {icon + ' ' if icon else ''}Decision #{number}: {text(decision['title'])}"]
    if with_detail:
        parts.append(f"- {text(decision['detail'])}")
    options = decision.get("options") or []
    if options:
        parts.append(table(("Option", "What it means", "Effect"),
                           [[cell(o["option"]), text(o.get("meaning") or "-", OPTION_MAX), text(o["effect"], OPTION_MAX)] for o in options]))
    else:
        parts.append("Options not supplied")
    if decision.get("reply") and options:
        parts.append(text(decision["reply"]))
    return parts


def release_table(data: dict, bar: str, tasks: str, released: str) -> str:
    """The four-row release table that opens both the compact and the full report."""
    release = data.get("next_release") or {"version": "none (all released)", "remaining": "N/A"}
    left = data["versions_left"]
    left_label = f"{left} {'version' if left == 1 else 'versions'} left"
    progress_text = f"progress: {bar} ({tasks} tasks)"
    whole = f"{progress_text}{VALUE_SEP}ETA: {cell(data['remaining'])}"
    rows = [("Last release", "", released), ("Next release", "", cell(release["version"])),
            ("Next release ETA", "", text(release["remaining"])),
            (f"Full {cell(data['scope'])} implementation", f" ({left_label})", whole)]
    output = "\n".join(["| | |", "|---|---|", *(f"| **{bold}**{suffix} | {value} |" for bold, suffix, value in rows)])
    condition = release.get("condition", "none")
    if condition.lower() != "none":
        output += f"\n\nNext release estimate applies {text(condition) if condition.lower().startswith('after ') else 'after ' + text(condition)}."
    return output


def _compact(data: dict, bar: str, tasks: str, released: str, state: dict) -> str:
    goals = "\n".join(f"- {text(g['goal'])} - {text(g['done_when'])} ({text(g['state'])})" for g in data["goals"]) or "None."
    decisions = "\n\n".join("\n\n".join(decision_parts(d, with_detail=False, number=number)) for number, d in enumerate(data["decisions"], 1)) or "No decisions waiting."
    running = "\n".join(_running_bullet(r) for r in data["running"]) or empty_running(state)
    parts = [*([state_heading(state)] if state_heading(state) else []), "## Progress Update", release_table(data, bar, tasks, released),
             *estimate_parts(data, state),
             *idle_parts(data, full=False),
             *required_parts(state),
             "---", f"### {GOALS_ICON} Goals", goals,
             "---", f"### {WAIT_ICON} Decisions waiting", decisions,
             "---", f"### {RUN_ICON} Running", running,
             f"State: {state['state'].replace('_', ' ')}",
             '*Full report: /progress, or ask for "full progress".*']
    return "\n\n".join(parts) + "\n"


def empty_running(state: dict) -> str:
    if state["jobs"]:
        return "The existing process is listed under Process observations."
    if state["state"] == "working":
        return "No separate process is running; authorized work is available."
    return "No process is running; the waiting or terminal condition is shown above."


def _running_bullet(row: dict) -> str:
    known = counts(row)[0] is not None
    bar = f" {progress_parts(*counts(row))[0]}" if known else ""
    return f"- {running_label(row)}{bar}: {text(row['state'])}"


def fingerprint(data: dict) -> str:
    stable = copy.deepcopy(data)
    state = continuation(data)
    stable["continuation"] = state
    for key in ("observed_at", "elapsed", "source", "continuation_observation", "previous_continuation"):
        stable.pop(key, None)
    for lane in stable.get("idle_lanes", []):
        if lane["kind"] == "needs-user":
            lane["detail"] = re.sub(r"^blocked [0-9]+ min on (?=\S)", "blocked <age> min on ", lane["detail"])
    for key in ("rows", "running"):
        for row in stable[key]:
            row.pop("elapsed", None)
    if state["state"] in {"waiting_owner_action", "waiting_decision", "waiting_job", "blocked_external", "paused"}:
        # Own-pace projections can drift while nothing becomes actionable. Real
        # releases, counts, conditions and capability observations remain hashed.
        stable.pop("remaining", None)
        stable.pop("estimate_basis", None)
        for key in ("rows", "running"):
            for row in stable[key]:
                row.pop("remaining", None)
        if stable.get("next_release"):
            stable["next_release"].pop("remaining", None)
            stable["next_release"].pop("basis", None)
    return _STATE.semantic_fingerprint(stable)


def select_report(data: dict, previous: dict | None, event: str, interval: int = 300) -> dict:
    """A checkpoint is a phase/material transition, not an individual tool call."""
    validate(data)
    if event not in EVENTS or type(interval) is not int or interval <= 0:
        raise ValueError("invalid event or interval")
    now = timestamp(data["observed_at"])
    decisions = pending_decisions(continuation(data))
    same = isinstance(previous, dict) and all(previous.get(k) == v for k, v in
        (("contract", CONTRACT), ("run_id", data["run_id"]), ("scope", data["scope"])))
    if same:
        try:
            same = (
                isinstance(previous.get("fingerprint"), str)
                and re.fullmatch(r"[0-9a-f]{64}", previous["fingerprint"]) is not None
                and isinstance(previous.get("decisions"), list)
                and timestamp(previous["observed_at"]) <= now
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            same = False
    mode = "none"
    current_hash = fingerprint(data)
    if event == "request":
        mode = "full"
    elif event != "progress":
        # A release-inventory flag cannot retire outstanding proof or owner work.
        # validate() already required a reconciled waiting, working or terminal state.
        if not same or (
            decisions != previous.get("decisions") and decisions
        ):
            mode = "full"
        elif current_hash != previous.get("fingerprint"):
            mode = "full" if event in ("start", "resume") else "compact"
    receipt = previous
    if mode != "none":
        receipt = {"contract": CONTRACT, "run_id": data["run_id"], "scope": data["scope"],
                   "observed_at": data["observed_at"], "fingerprint": current_hash, "decisions": decisions}
    return {"mode": mode, "report": render(data, mode) if mode != "none" else "", "receipt": receipt}


def audit(source: Path, roots: list[Path]) -> list[str]:
    """Check explicit skill roots, including legacy roots that can shadow a repair."""
    issues = []
    for root in roots:
        candidates = [p for p in (root / "implement-phase", root / "workflow/implement-phase") if p.is_dir()]
        if not candidates:
            issues.append(f"missing reporting skill: {root}")
        for candidate in candidates:
            for relative in RESOURCES:
                expected, installed = source / relative, candidate / relative
                if not expected.is_file():
                    issues.append(f"missing source: {expected}")
                elif not installed.is_file():
                    issues.append(f"missing installed resource: {installed}")
                elif installed.read_bytes() != expected.read_bytes():
                    issues.append(f"stale installed resource: {installed}")
    return issues


def read_json(path: str) -> dict:
    if path == "-":
        value = sys.stdin.read(1_048_577)
    else:
        with Path(path).open(encoding="utf-8-sig") as stream:
            value = stream.read(1_048_577)
    if len(value) > 1_048_576:
        raise ValueError("status input exceeds 1 MiB")
    return json.loads(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="evidence snapshot JSON, default stdin")
    parser.add_argument("--previous", help="last emitted receipt JSON, read only")
    parser.add_argument("--event", choices=EVENTS, default="request")
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--json", action="store_true", help="include emission receipt for existing session history")
    parser.add_argument("--audit-roots", nargs="+", type=Path, help="read-only audit of explicit installed skill roots")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        if args.audit_roots:
            issues = audit(args.source, args.audit_roots)
            print(json.dumps({"contract": CONTRACT, "issues": issues}, indent=2))
            return 1 if issues else 0
        result = select_report(read_json(args.input), read_json(args.previous) if args.previous else None, args.event, args.interval)
        print(json.dumps(result, ensure_ascii=True) if args.json else result["report"], end="\n" if args.json else "")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"status report unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
