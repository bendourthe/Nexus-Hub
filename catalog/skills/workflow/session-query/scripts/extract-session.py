#!/usr/bin/env python3
"""
extract-session.py - Local session-log digest extractor for the session-query skill.

This script ships as a Tier-3 bundled resource: the agent invokes it via the
shell and consumes its JSON output without reading the source into context. It
is single-file, stdlib-only, and works on Python 3.8+ across macOS, Linux, and
Windows.

It reads LOCAL AI session-log JSONL files (Claude Code / Codex / Cursor, or any
NDJSON transcript) and emits a topic / branch / time-windowed digest of prior
investigation context. It is strictly read-only and makes ZERO network calls:
it imports no socket / urllib / http / requests module and opens no connection.

Inputs (any combination):
    - one or more JSONL file paths as positional arguments, or
    - --root <dir> to recursively discover *.jsonl under a directory, or
    - file paths on stdin (one per line, optionally "tool<TAB>path" from
      discover-sessions), used when no positional paths and no --root are given.

Filters:
    --topic   substring(s), comma-separated, case-insensitive (match in text)
    --branch  branch name; matches records whose text mentions it or whose
              record carries a git-branch field
    --since   ISO-8601 lower bound (inclusive) on record timestamps
    --until   ISO-8601 upper bound (inclusive) on record timestamps
    --tool    label applied to discovered/passed files when not inferable
    --max-snippets  cap on matched snippets per session (default 20)
    --out     write the JSON digest to this path instead of stdout

Usage:
    python extract-session.py session.jsonl --topic "auth,token" --since 2026-05-01
    python extract-session.py --root ~/.claude/projects --branch feature/login
    discover-sessions.sh | python extract-session.py --topic deploy
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

# Candidate JSON keys for each normalized field, in priority order.
TS_KEYS = ("ts", "timestamp", "time", "created_at", "createdAt", "date")
ROLE_KEYS = ("role", "event", "type", "speaker", "author")
TEXT_KEYS = ("prompt_sample", "prompt", "text", "content", "message", "summary")
BRANCH_KEYS = ("branch", "git_branch", "gitBranch", "ref")

SNIPPET_MAX_CHARS = 240


def parse_ts(value: object) -> Optional[datetime]:
    """Parse an ISO-8601-ish timestamp into an aware UTC datetime, or None."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Fall back to a date-only or space-separated form.
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(value.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def first_key(record: dict, keys: Iterable[str]) -> object:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def extract_text(value: object) -> str:
    """Flatten a text/content value (string or block list) into one string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: List[str] = []
        for block in value:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                inner = first_key(block, ("text", "content", "value"))
                if isinstance(inner, str):
                    parts.append(inner)
        return " ".join(parts)
    if isinstance(value, dict):
        inner = first_key(value, ("text", "content", "value"))
        return inner if isinstance(inner, str) else ""
    return ""


def iter_records(path: Path) -> Iterator[dict]:
    """Yield parsed JSON objects from a JSONL file, skipping malformed lines."""
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(obj, dict):
                yield obj


def discover(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.jsonl") if p.is_file())


def read_stdin_paths() -> List[Path]:
    paths: List[Path] = []
    if sys.stdin is None or sys.stdin.isatty():
        return paths
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        # Accept either a bare path or "tool<TAB>path" from discover-sessions.
        if "\t" in line:
            line = line.split("\t", 1)[1]
        paths.append(Path(line))
    return paths


def digest_file(
    path: Path,
    tool: str,
    topics: List[str],
    branch: Optional[str],
    since: Optional[datetime],
    until: Optional[datetime],
    max_snippets: int,
) -> Optional[dict]:
    topics_lc = [t.lower() for t in topics if t]
    branch_lc = branch.lower() if branch else None
    has_window = since is not None or until is not None

    records_total = 0
    records_matched = 0
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    branches: set = set()
    snippets: List[dict] = []

    for record in iter_records(path):
        records_total += 1
        ts = parse_ts(first_key(record, TS_KEYS))
        if ts is not None:
            first_ts = ts if first_ts is None or ts < first_ts else first_ts
            last_ts = ts if last_ts is None or ts > last_ts else last_ts

        # Time-window filter: when a window is set, drop records that fall
        # outside it and records with no parseable timestamp.
        if has_window:
            if ts is None:
                continue
            if since is not None and ts < since:
                continue
            if until is not None and ts > until:
                continue

        text = extract_text(first_key(record, TEXT_KEYS))
        text_lc = text.lower()

        rec_branch = first_key(record, BRANCH_KEYS)
        if isinstance(rec_branch, str) and rec_branch:
            branches.add(rec_branch)

        # Topic filter (any substring matches).
        if topics_lc and not any(t in text_lc for t in topics_lc):
            continue
        # Branch filter (record field or text mention).
        if branch_lc is not None:
            field_hit = isinstance(rec_branch, str) and branch_lc in rec_branch.lower()
            if not field_hit and branch_lc not in text_lc:
                continue

        records_matched += 1
        if len(snippets) < max_snippets and text.strip():
            role = first_key(record, ROLE_KEYS)
            snippets.append(
                {
                    "ts": ts.isoformat() if ts else None,
                    "role": role if isinstance(role, str) else None,
                    "text": text.strip()[:SNIPPET_MAX_CHARS],
                }
            )

    # A session with no filter is always reported; with a filter it is
    # reported only when at least one record matched.
    any_filter = bool(topics_lc) or branch_lc is not None or has_window
    if any_filter and records_matched == 0:
        return None

    return {
        "tool": tool,
        "path": str(path),
        "first_ts": first_ts.isoformat() if first_ts else None,
        "last_ts": last_ts.isoformat() if last_ts else None,
        "records_total": records_total,
        "records_matched": records_matched,
        "branches": sorted(branches),
        "snippets": snippets,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract a topic/branch/time-windowed digest from local session JSONL logs (zero-outbound).",
    )
    parser.add_argument("paths", nargs="*", help="JSONL file path(s).")
    parser.add_argument("--root", help="Recursively discover *.jsonl under this directory.")
    parser.add_argument("--topic", default="", help="Comma-separated, case-insensitive substrings.")
    parser.add_argument("--branch", default=None, help="Branch name to filter on.")
    parser.add_argument("--since", default=None, help="ISO-8601 lower bound (inclusive).")
    parser.add_argument("--until", default=None, help="ISO-8601 upper bound (inclusive).")
    parser.add_argument("--tool", default="unknown", help="Tool label for passed/discovered files.")
    parser.add_argument("--max-snippets", type=int, default=20, help="Max matched snippets per session.")
    parser.add_argument("--out", default=None, help="Write JSON digest here instead of stdout.")
    args = parser.parse_args(argv)

    topics = [t.strip() for t in args.topic.split(",") if t.strip()]
    since = parse_ts(args.since) if args.since else None
    until = parse_ts(args.until) if args.until else None
    if args.since and since is None:
        parser.error(f"--since is not a valid ISO-8601 timestamp: {args.since!r}")
    if args.until and until is None:
        parser.error(f"--until is not a valid ISO-8601 timestamp: {args.until!r}")

    paths: List[Path] = [Path(p) for p in args.paths]
    if args.root:
        paths.extend(discover(Path(args.root).expanduser()))
    if not paths:
        paths.extend(read_stdin_paths())

    # De-duplicate while preserving order.
    seen: set = set()
    ordered: List[Path] = []
    for p in paths:
        key = str(p)
        if key not in seen:
            seen.add(key)
            ordered.append(p)

    sessions: List[dict] = []
    for path in ordered:
        if not path.is_file():
            continue
        result = digest_file(path, args.tool, topics, args.branch, since, until, args.max_snippets)
        if result is not None:
            sessions.append(result)

    digest = {
        "query": {
            "topics": topics,
            "branch": args.branch,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
        },
        "sessions": sessions,
        "summary": {
            "files_scanned": len(ordered),
            "files_matched": len(sessions),
            "snippets_total": sum(len(s["snippets"]) for s in sessions),
        },
    }

    payload = json.dumps(digest, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).expanduser().write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
