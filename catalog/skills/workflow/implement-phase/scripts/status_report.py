#!/usr/bin/env python3
"""Render portable status and select cadence from evidence; never write run state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit

CONTRACT = "portable-status-v1"
EVENTS = ("start", "resume", "request", "checkpoint", "turn-end", "progress")
RESOURCES = ("SKILL.md", "references/progress-reporting.md", "references/status-formats.md",
             "references/status-snapshot.json", "scripts/status_report.py")


FILLED, EMPTY = "\u25b0", "\u25b1"
DOT2 = " \u00b7 "
GOALS_ICON, WAIT_ICON, RUN_ICON = "\U0001F3AF", "\U0001F64B", "\U0001F504"
RELEASE_ICON, PROGRESS_ICON = "\U0001F680", "\U0001F4CA"
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


def counts(row: dict) -> tuple[int | None, int | None]:
    if "done" not in row or "total" not in row:
        raise ValueError("counts require explicit done and total, including nulls when unknown")
    done, total = row["done"], row["total"]
    if done is None and total is None:
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
    if data.get("last_released") is not None and not isinstance(data["last_released"], str):
        raise ValueError("last_released must be a string or null (unknown)")
    release = data.get("next_release")
    if release is not None:
        required = ("version", "remaining", "condition", "confidence", "basis")
        if not isinstance(release, dict) or any(not isinstance(release.get(k), str) or not release[k].strip() for k in required):
            raise ValueError("next_release requires nonempty version, remaining, condition, confidence and basis")
        if release["confidence"] not in ("low", "medium", "high", "unknown"):
            raise ValueError("release confidence must be low, medium, high or unknown")
    left = data.get("versions_left")
    if left is not None and (type(left) is not int or left < 0):
        raise ValueError("versions_left must be a nonnegative integer or null")
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
                counts(item)
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


def progress_parts(done: int | None, total: int | None) -> tuple[str, str]:
    """Return the bar-and-percent text and the done/total text."""
    if done is None:
        return "unknown", "unknown"
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


def render(data: dict, mode: str) -> str:
    validate(data)
    if mode not in ("compact", "full"):
        raise ValueError("mode must be compact or full")
    done, total = aggregate(data)
    released = text(data.get("last_released") or "unknown")
    bar, tasks = progress_parts(done, total)
    if mode == "compact":
        return _compact(data, bar, tasks, released)
    rows = []
    for r in data["rows"]:
        rbar, rtasks = progress_parts(*counts(r))
        rows.append([f"**{cell(r['name'])}**", cell(r["goals"]), rbar, rtasks, cell(r["elapsed"]), remaining_with_dependency(r)])
    rows.append(["**Total**", "", f"**{bar}**", f"**{tasks}**", f"**{cell(data['elapsed'])}**", f"**{cell(data['remaining'])}**"])
    release = data.get("next_release") or {"confidence": "unknown", "basis": "release estimate not supplied"}
    parts = ["## Status Update", f"### {RELEASE_ICON} Release status", release_table(data, bar, tasks, released),
             f"### {PROGRESS_ICON} Version progress",
             table(("Version", "Goals", "Progress", "Tasks", "Elapsed", "Remaining"), rows),
             f"Confidence: {cell(release['confidence'])} \u00b7 Basis: {text(release['basis'], 80)} \u00b7 As of {cell(data['observed_at'])}",
             "---", f"### {GOALS_ICON} Goals",
             table(("Goal", "Scope", "Done when", "State"),
                   [[cell(g[k]) for k in ("goal", "scope", "done_when", "state")] for g in data["goals"]]),
             "---", f"### {WAIT_ICON} Decisions waiting"]
    if not data["decisions"]:
        parts.append("No decisions waiting.")
    for decision in data["decisions"]:
        parts.extend(decision_parts(decision, with_detail=True))
    parts.extend(["---", f"### {RUN_ICON} Running"])
    if not data["running"]:
        parts.append("Nothing running.")
    else:
        run_rows = []
        for r in data["running"]:
            rbar, rtasks = progress_parts(*counts(r))
            run_rows.append([running_label(r), rbar, rtasks, cell(r["state"]), cell(r["elapsed"]), cell(r["remaining"])])
        parts.append(table(("Item", "Progress", "Tasks", "State", "Elapsed", "Remaining"), run_rows))
    parts.append(f"*Source: {text(data['source'], 100)}*")
    return "\n\n".join(parts) + "\n"


def decision_parts(decision: dict, with_detail: bool) -> list[str]:
    """One decision as a heading, optional explanation bullet, options table and optional reply line."""
    icon = keycap(decision["id"])
    parts = [f"#### {icon + ' ' if icon else ''}Decision #{text(decision['id'])}: {text(decision['title'])}"]
    if with_detail:
        parts.append(f"- {text(decision['detail'])}")
    options = decision.get("options") or []
    if options:
        parts.append(table(("Option", "What it means", "Effect"),
                           [[cell(o["option"]), text(o.get("meaning") or "-", OPTION_MAX), text(o["effect"], OPTION_MAX)] for o in options]))
    else:
        parts.append("Options not supplied")
    if not with_detail and decision.get("reply") and options:
        parts.append(text(decision["reply"]))
    return parts


def release_table(data: dict, bar: str, tasks: str, released: str) -> str:
    """The four-row release table that opens both the compact and the full report."""
    release = data.get("next_release") or {"version": "unknown", "remaining": "unknown (release estimate not supplied)"}
    left = data.get("versions_left")
    left_label = "versions left unknown" if left is None else f"{left} {'version' if left == 1 else 'versions'} left"
    whole = f"{cell(data['remaining'])}{DOT2}{tasks} tasks {bar}" if tasks != "unknown" else f"{cell(data['remaining'])}{DOT2}tasks unknown"
    rows = [("Last release", "", released), ("Next release", "", cell(release["version"])),
            ("Next release ETA", "", cell(release["remaining"])),
            (f"Full {cell(data['scope'])} implementation", f" ({left_label})", whole)]
    return "\n".join(["| | |", "|---|---|", *(f"| **{bold}**{suffix} | {value} |" for bold, suffix, value in rows)])


def _compact(data: dict, bar: str, tasks: str, released: str) -> str:
    goals = "\n".join(f"- {text(g['goal'])} - {text(g['done_when'])} ({text(g['state'])})" for g in data["goals"]) or "None."
    decisions = "\n\n".join("\n\n".join(decision_parts(d, with_detail=False)) for d in data["decisions"]) or "No decisions waiting."
    running = "\n".join(_running_bullet(r) for r in data["running"]) or "Nothing running."
    parts = ["## Status Update", release_table(data, bar, tasks, released),
             "---", f"### {GOALS_ICON} Goals", goals,
             "---", f"### {WAIT_ICON} Decisions waiting", decisions,
             "---", f"### {RUN_ICON} Running", running,
             '*Full report: /status, or ask for "full status".*']
    return "\n\n".join(parts) + "\n"


def _running_bullet(row: dict) -> str:
    known = counts(row)[0] is not None
    bar = f" {progress_parts(*counts(row))[0]}" if known else ""
    return f"- {running_label(row)}{bar}: {text(row['state'])}"


def fingerprint(data: dict) -> str:
    stable = copy.deepcopy(data)
    for key in ("observed_at", "elapsed", "source"):
        stable.pop(key, None)
    for key in ("rows", "running"):
        for row in stable[key]:
            row.pop("elapsed", None)
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def select_report(data: dict, previous: dict | None, event: str, interval: int = 300) -> dict:
    """A checkpoint is a phase/material transition, not an individual tool call."""
    validate(data)
    if event not in EVENTS or type(interval) is not int or interval <= 0:
        raise ValueError("invalid event or interval")
    now = timestamp(data["observed_at"])
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
    elif data["active"] and event != "progress":
        if event in ("start", "resume") or not same or (
            data["decisions"] != previous.get("decisions") and data["decisions"]
        ):
            mode = "full"
        elif (event == "checkpoint" and current_hash != previous.get("fingerprint")) or (now - timestamp(previous["observed_at"])).total_seconds() >= interval:
            mode = "compact"
    receipt = previous
    if mode != "none":
        receipt = {"contract": CONTRACT, "run_id": data["run_id"], "scope": data["scope"],
                   "observed_at": data["observed_at"], "fingerprint": current_hash, "decisions": data["decisions"]}
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
