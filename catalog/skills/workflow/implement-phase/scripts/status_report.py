#!/usr/bin/env python3
"""Render portable status and select cadence from evidence; never write run state."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
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


def text(value: object) -> str:
    """Keep evidence on one line and escape Markdown/HTML, including table pipes."""
    value = " ".join(str(value).split())
    value = "".join(c for c in value if ord(c) >= 32 and ord(c) != 127)
    return re.sub(r"([\\`*_{}\[\]()#+|>])", r"\\\1", html.escape(value, quote=False))


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
                options = item.get("options")
                if not isinstance(options, list) or not options or any(
                    not isinstance(o, dict) or not all(isinstance(o.get(k), str) and o[k].strip() for k in ("option", "effect"))
                    for o in options
                ):
                    raise ValueError("each decision requires option/effect entries")
    ids = [d["id"] for d in data["decisions"]]
    if len(set(ids)) != len(ids):
        raise ValueError("decision ids must be unique")


def progress(done: int | None, total: int | None) -> str:
    if done is None:
        return "unknown"
    if total == 0:
        return "N/A (0/0 tasks)"
    percent = (100 * done + total // 2) // total
    filled = min(10, (10 * done) // total)
    return f"`{'#' * filled}{'-' * (10 - filled)}` {percent}% | {done}/{total} tasks"


def aggregate(data: dict) -> tuple[int | None, int | None]:
    values = [counts(row) for row in data["rows"]]
    if any(done is None for done, _ in values):
        return None, None
    return sum(d for d, _ in values), sum(t for _, t in values)


def table(headers: tuple[str, ...], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def running_label(row: dict) -> str:
    label = text(row["name"])
    if row.get("url"):
        return f"[{label}]({quote(row['url'], safe=':/?=&%#@')})"
    return label


def render(data: dict, mode: str) -> str:
    validate(data)
    if mode not in ("compact", "full"):
        raise ValueError("mode must be compact or full")
    done, total = aggregate(data)
    released = text(data.get("last_released") or "unknown")
    left = data.get("versions_left")
    parts = [f"## Status: {text(data['scope'])}",
             f"{progress(done, total)} | last released {released} | {left if left is not None else 'unknown'} versions left | time left: {text(data['remaining'])}",
             f"As of {text(data['observed_at'])} | Elapsed: {text(data['elapsed'])}"]
    if mode == "full":
        rows = [[text(r["name"]), text(r["goals"]), progress(*counts(r)).replace(" | ", " / "),
                 text(r["state"]), text(r["elapsed"]), text(r["remaining"]), text(r["dependency"])] for r in data["rows"]]
        rows.append(["Total", "", progress(done, total).replace(" | ", " / "), "", text(data["elapsed"]), text(data["remaining"]), ""])
        parts.extend([table(("Plan / phase", "Goals", "Progress / tasks", "State", "Elapsed", "Remaining", "Dependency"), rows),
                      f"Estimate basis: {text(data['estimate_basis'])}"])
    parts.append("### Goals")
    if mode == "compact":
        parts.append("\n".join(f"- {text(g['goal'])} - {text(g['done_when'])} ({text(g['state'])})" for g in data["goals"]))
    else:
        parts.append(table(("Goal", "Scope", "Done when", "State"),
                           [[text(g[k]) for k in ("goal", "scope", "done_when", "state")] for g in data["goals"]]))
    parts.append("### Decisions")
    if not data["decisions"]:
        parts.append("No decisions waiting.")
    elif mode == "compact":
        parts.append("\n".join(f"- #{text(d['id'])}: {text(d['title'])}" for d in data["decisions"]))
    else:
        for decision in data["decisions"]:
            parts.extend([f"#### Decision {text(decision['id'])}: {text(decision['title'])}", text(decision["detail"]),
                          table(("Option", "Effect"), [[text(o["option"]), text(o["effect"])] for o in decision["options"]])])
    parts.append("### Running")
    if not data["running"]:
        parts.append("Nothing running.")
    elif mode == "compact":
        parts.append("\n".join(f"- {running_label(r)}: {progress(*counts(r))} ({text(r['state'])})" for r in data["running"]))
    else:
        parts.append(table(("Item", "Progress / tasks", "State", "Elapsed", "Remaining"),
                           [[running_label(r), progress(*counts(r)).replace(" | ", " / "), text(r["state"]), text(r["elapsed"]), text(r["remaining"])] for r in data["running"]]))
    parts.append(f"Source: {text(data['source'])}")
    if mode == "compact":
        parts.append('*Full report: /status, or ask for "full status".*')
    return "\n\n".join(parts) + "\n"


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
