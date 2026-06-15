#!/usr/bin/env python3
"""
extract-session.py - Local session-log digest extractor for the session-query skill.

This script ships as a Tier-3 bundled resource: the agent invokes it via the
shell and consumes its JSON output without reading the source into context. It
is single-file, stdlib-only, and works on Python 3.8+ across macOS, Linux, and
Windows.

It reads LOCAL prior-context sources and emits a topic / branch / time-windowed
digest of prior investigation context. Supported sources, selected per file by
a source tag (the "tool" column from discover-sessions, or --tool):

    - AI session-log JSONL (Claude Code / Codex / Cursor, or any NDJSON) - default
    - Obsidian vault notes (.md with frontmatter, headings, and [[backlinks]])
    - Exported ChatGPT history (conversations.json)
    - Exported Gemini history (Google Takeout "My Activity" JSON)

All sources are parsed into one normalized digest structure. It is strictly
read-only and makes ZERO network calls: it imports no socket / urllib / http /
requests module and opens no connection. Every source reads files on disk only.

Inputs (any combination):
    - one or more file paths as positional arguments, or
    - --root <dir> to recursively discover source files under a directory, or
    - file paths on stdin (one per line, optionally "tool<TAB>path" from
      discover-sessions), used when no positional paths and no --root are given.
      The "tool" tag from each stdin line selects that file's parser.

Filters:
    --topic   substring(s), comma-separated, case-insensitive (match in text)
    --branch  branch name; matches records whose text mentions it or whose
              record carries a git-branch field
    --since   ISO-8601 lower bound (inclusive) on record timestamps
    --until   ISO-8601 upper bound (inclusive) on record timestamps
    --tool    source label/parser for passed/discovered files (claude | codex |
              cursor | custom for JSONL; obsidian | chatgpt | gemini for the
              non-JSONL sources). Untagged inputs auto-detect by file extension.
    --max-snippets  cap on matched snippets per session (default 20)
    --out     write the JSON digest to this path instead of stdout

Usage:
    python extract-session.py session.jsonl --topic "auth,token" --since 2026-05-01
    python extract-session.py --root ~/.claude/projects --branch feature/login
    python extract-session.py note.md --tool obsidian --topic "auth"
    python extract-session.py --root ~/Downloads/chatgpt --tool chatgpt --topic deploy
    discover-sessions.sh --tool obsidian | python extract-session.py --topic deploy
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple

# Candidate JSON keys for each normalized field, in priority order.
TS_KEYS = ("ts", "timestamp", "time", "created_at", "createdAt", "date")
ROLE_KEYS = ("role", "event", "type", "speaker", "author")
TEXT_KEYS = ("prompt_sample", "prompt", "text", "content", "message", "summary")
BRANCH_KEYS = ("branch", "git_branch", "gitBranch", "ref")

# Source tags that select a non-JSONL parser (the discriminator that keeps the
# default JSONL behavior unchanged for every other tag).
OBSIDIAN_TOOL = "obsidian"
CHATGPT_TOOL = "chatgpt"
GEMINI_TOOL = "gemini"
NON_JSONL_TOOLS = (OBSIDIAN_TOOL, CHATGPT_TOOL, GEMINI_TOOL)
UNTYPED_TOOLS = ("", "unknown", "custom")

# Per-source glob patterns used when --root is scanned with a source --tool.
ROOT_PATTERNS = {
    OBSIDIAN_TOOL: ("*.md",),
    CHATGPT_TOOL: ("*.json", "*.md"),
    GEMINI_TOOL: ("*.json", "*.md"),
}

# Obsidian frontmatter keys that may carry a note timestamp, in priority order.
OBSIDIAN_TS_KEYS = ("updated", "modified", "date", "created", "ctime", "mtime")

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


def epoch_to_iso(value: object) -> Optional[str]:
    """Convert a Unix epoch-seconds number (ChatGPT create_time) to an ISO string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    return None


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


def load_json(path: Path) -> object:
    """Load a whole JSON file, returning None on read or parse failure."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


# --- Obsidian vault notes ----------------------------------------------------


def split_frontmatter(raw: str) -> Tuple[dict, str]:
    """Split a leading YAML-ish frontmatter block from a Markdown note body.

    Only the few scalar keys this extractor cares about are parsed (timestamp
    keys, title, tags) using a minimal key: value line scan - no YAML library
    is imported. Returns (frontmatter_dict, body)."""
    if not raw.startswith("---"):
        return {}, raw
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw
    fm: dict = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        line = lines[i]
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip().strip('"').strip("'")
            if key and value:
                fm[key] = value
    if end is None:
        return {}, raw
    body = "\n".join(lines[end + 1:])
    return fm, body


def split_md_sections(body: str) -> Iterator[Tuple[str, str]]:
    """Split a Markdown body into (heading, section_body) pairs at ATX headings.

    Content before the first heading is yielded with an empty heading."""
    heading = ""
    buf: List[str] = []
    for line in body.splitlines():
        stripped = line.lstrip()
        is_heading = False
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= hashes <= 6 and stripped[hashes:hashes + 1] in (" ", "\t"):
                is_heading = True
        if is_heading:
            if heading or "".join(buf).strip():
                yield heading, "\n".join(buf)
            heading = stripped.strip()
            buf = []
        else:
            buf.append(line)
    if heading or "".join(buf).strip():
        yield heading, "\n".join(buf)


def iter_obsidian_records(path: Path) -> Iterator[dict]:
    """Yield normalized records from an Obsidian Markdown note."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    fm, body = split_frontmatter(raw)
    ts: Optional[datetime] = None
    for key in OBSIDIAN_TS_KEYS:
        if key in fm:
            ts = parse_ts(fm[key])
            if ts is not None:
                break
    if ts is None:
        try:
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            ts = None
    ts_iso = ts.isoformat() if ts else None

    title = fm.get("title") or path.stem
    tags = fm.get("tags")
    title_text = f"{title} tags: {tags}" if tags else str(title)
    yield {"ts": ts_iso, "role": "note", "text": title_text}

    for heading, section in split_md_sections(body):
        text = (heading + "\n" + section).strip() if heading else section.strip()
        if text:
            yield {"ts": ts_iso, "role": "note", "text": text}


# --- Exported ChatGPT history ------------------------------------------------


def iter_chatgpt_records(path: Path) -> Iterator[dict]:
    """Yield normalized records from an exported ChatGPT conversations file."""
    data = load_json(path)
    if data is None:
        return
    conversations = data if isinstance(data, list) else [data]
    for conv in conversations:
        if not isinstance(conv, dict):
            continue
        title = conv.get("title")
        conv_ct = conv.get("create_time")
        mapping = conv.get("mapping")
        messages: List[dict] = []
        if isinstance(mapping, dict):
            for node in mapping.values():
                if isinstance(node, dict) and isinstance(node.get("message"), dict):
                    messages.append(node["message"])
            messages.sort(key=lambda m: m.get("create_time") or 0)
        elif isinstance(conv.get("messages"), list):
            messages = [m for m in conv["messages"] if isinstance(m, dict)]

        first = True
        for msg in messages:
            author = msg.get("author")
            role = author.get("role") if isinstance(author, dict) else msg.get("role")
            content = msg.get("content")
            text = ""
            if isinstance(content, dict):
                parts = content.get("parts")
                if isinstance(parts, str):
                    text = parts.strip()
                elif isinstance(parts, list):
                    text = " ".join(p for p in parts if isinstance(p, str)).strip()
            elif isinstance(content, str):
                text = content.strip()
            if not text:
                text = extract_text(first_key(msg, TEXT_KEYS)).strip()
            if not text:
                continue
            ts_iso = epoch_to_iso(msg.get("create_time")) or epoch_to_iso(conv_ct)
            if ts_iso is None:
                ts_iso = parse_ts(first_key(msg, TS_KEYS))
                ts_iso = ts_iso.isoformat() if isinstance(ts_iso, datetime) else None
            if first and isinstance(title, str) and title:
                text = f"[{title}] {text}"
                first = False
            yield {"ts": ts_iso, "role": role if isinstance(role, str) else None, "text": text}


# --- Exported Gemini history (Google Takeout "My Activity") ------------------


def iter_gemini_records(path: Path) -> Iterator[dict]:
    """Yield normalized records from an exported Gemini "My Activity" file."""
    data = load_json(path)
    if data is None:
        return
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and isinstance(data.get("activity"), list):
        entries = data["activity"]
    else:
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ts_iso = None
        raw_ts = entry.get("time")
        if isinstance(raw_ts, str):
            parsed = parse_ts(raw_ts)
            ts_iso = parsed.isoformat() if parsed else raw_ts
        title = entry.get("title")
        text = title if isinstance(title, str) else ""
        extra: List[str] = []
        for key in ("subtitles", "details"):
            value = entry.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and isinstance(item.get("name"), str):
                        extra.append(item["name"])
                    elif isinstance(item, str):
                        extra.append(item)
        if extra:
            text = (text + " " + " ".join(extra)).strip()
        text = text.strip()
        if not text:
            continue
        yield {"ts": ts_iso, "role": "user", "text": text}


def iter_json_export_records(path: Path) -> Iterator[dict]:
    """Auto-detect an untyped .json export (ChatGPT vs Gemini) and parse it."""
    data = load_json(path)
    if data is None:
        return
    sample = data[0] if isinstance(data, list) and data else data
    if isinstance(sample, dict):
        if "mapping" in sample or "messages" in sample:
            yield from iter_chatgpt_records(path)
            return
        if "time" in sample and "title" in sample:
            yield from iter_gemini_records(path)
            return
    # Unknown JSON shape: skip rather than fabricate context.
    return


def iter_normalized_records(path: Path, tool: str) -> Iterator[dict]:
    """Dispatch to the right parser by source tag, then file extension."""
    tag = (tool or "").strip().lower()
    suffix = path.suffix.lower()
    if tag == OBSIDIAN_TOOL:
        yield from iter_obsidian_records(path)
        return
    if tag == CHATGPT_TOOL:
        yield from iter_chatgpt_records(path)
        return
    if tag == GEMINI_TOOL:
        yield from iter_gemini_records(path)
        return
    if tag in UNTYPED_TOOLS:
        if suffix == ".md":
            yield from iter_obsidian_records(path)
            return
        if suffix == ".json":
            yield from iter_json_export_records(path)
            return
    # Default: NDJSON / JSONL session logs (unchanged behavior).
    yield from iter_records(path)


def discover(root: Path, tool: str = "unknown") -> List[Path]:
    """Recursively find source files under root, by the tool's glob patterns."""
    if not root.exists():
        return []
    patterns = ROOT_PATTERNS.get((tool or "").strip().lower(), ("*.jsonl",))
    found: List[Path] = []
    for pattern in patterns:
        found.extend(p for p in root.rglob(pattern) if p.is_file())
    return sorted(set(found))


def read_stdin_pairs(default_tool: str) -> List[Tuple[str, Path]]:
    """Read (tool, path) pairs from stdin: bare paths or 'tool<TAB>path' lines."""
    pairs: List[Tuple[str, Path]] = []
    if sys.stdin is None or sys.stdin.isatty():
        return pairs
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        tool = default_tool
        if "\t" in line:
            tool, line = line.split("\t", 1)
        pairs.append((tool, Path(line)))
    return pairs


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

    for record in iter_normalized_records(path, tool):
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
        description="Extract a topic/branch/time-windowed digest from local prior-context sources (zero-outbound).",
    )
    parser.add_argument("paths", nargs="*", help="Source file path(s).")
    parser.add_argument("--root", help="Recursively discover source files under this directory.")
    parser.add_argument("--topic", default="", help="Comma-separated, case-insensitive substrings.")
    parser.add_argument("--branch", default=None, help="Branch name to filter on.")
    parser.add_argument("--since", default=None, help="ISO-8601 lower bound (inclusive).")
    parser.add_argument("--until", default=None, help="ISO-8601 upper bound (inclusive).")
    parser.add_argument(
        "--tool",
        default="unknown",
        help="Source label/parser: claude|codex|cursor|custom (JSONL) or obsidian|chatgpt|gemini.",
    )
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

    default_tool = args.tool
    pairs: List[Tuple[str, Path]] = [(default_tool, Path(p)) for p in args.paths]
    if args.root:
        for p in discover(Path(args.root).expanduser(), default_tool):
            pairs.append((default_tool, p))
    if not pairs:
        pairs.extend(read_stdin_pairs(default_tool))

    # De-duplicate by path while preserving order (keep the first tool seen).
    seen: set = set()
    ordered: List[Tuple[str, Path]] = []
    for tool, p in pairs:
        key = str(p)
        if key not in seen:
            seen.add(key)
            ordered.append((tool, p))

    sessions: List[dict] = []
    for tool, path in ordered:
        if not path.is_file():
            continue
        result = digest_file(path, tool, topics, args.branch, since, until, args.max_snippets)
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
