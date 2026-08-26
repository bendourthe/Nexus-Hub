#!/usr/bin/env python3
"""Capture and compare unresolved relative Markdown links in tracked files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Iterator, List, Optional
from urllib.parse import unquote, urlsplit


MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<destination>[^)]+)\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _tracked_markdown(root: Path) -> Iterator[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or f"git ls-files failed with exit {result.returncode}")
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        if relative.suffix.lower() in MARKDOWN_SUFFIXES:
            yield root / relative


def _destination(raw: str) -> Optional[str]:
    value = raw.strip()
    if value.startswith("<"):
        close = value.find(">")
        if close == -1:
            return None
        value = value[1:close]
    else:
        value = value.split(maxsplit=1)[0]
    value = value.strip()
    if not value or value.startswith("#") or value.startswith("//") or value.startswith("\\\\"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or not parsed.path:
        return None
    return unquote(parsed.path)


def _links(text: str) -> Iterable[tuple[str, str]]:
    fence: Optional[str] = None
    for line in text.splitlines():
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            fence = None if fence == marker else marker
            continue
        if fence is not None:
            continue
        for match in MARKDOWN_LINK_RE.finditer(INLINE_CODE_RE.sub("", line)):
            raw = match.group("destination").strip()
            destination = _destination(raw)
            if destination is not None:
                yield raw, destination


def _resolved_target(root: Path, source: Path, destination: str) -> Path:
    if destination.startswith("/"):
        candidate = root / destination.lstrip("/")
    else:
        candidate = source.parent / destination
    return Path(os.path.abspath(os.path.normpath(candidate)))


def _display_target(root: Path, target: Path) -> str:
    try:
        return _to_posix(target.relative_to(root))
    except ValueError:
        try:
            return _to_posix(Path(os.path.relpath(target, root)))
        except ValueError:
            return _to_posix(target)


def collect_unresolved(root: Path) -> List[dict[str, str]]:
    records: set[tuple[str, str, str]] = set()
    for source in _tracked_markdown(root):
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise RuntimeError(f"cannot read tracked Markdown file {source}: {exc}") from exc
        source_display = _to_posix(source.relative_to(root))
        for raw_link, destination in _links(text):
            target = _resolved_target(root, source, destination)
            if target.exists():
                continue
            records.add((source_display, raw_link, _display_target(root, target)))
    return [
        {"source": source, "link": link, "resolved_target": target}
        for source, link, target in sorted(records)
    ]


def _write_ndjson(path: Path, records: Iterable[dict[str, str]]) -> None:
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _read_ndjson(path: Path) -> set[tuple[str, str, str]]:
    records: set[tuple[str, str, str]] = set()
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise RuntimeError(f"cannot read baseline {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            records.add((record["source"], record["link"], record["resolved_target"]))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError(f"invalid NDJSON at {path}:{line_number}: {exc}") from exc
    return records


def _render(records: set[tuple[str, str, str]]) -> List[dict[str, str]]:
    return [
        {"source": source, "link": link, "resolved_target": target}
        for source, link, target in sorted(records)
    ]


def cmd_baseline(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: repository root not found at {root}", file=sys.stderr)
        return 2
    try:
        records = collect_unresolved(root)
        _write_ndjson(Path(args.out).resolve(), records)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"unresolved": len(records), "output": str(Path(args.out).resolve())}))
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    try:
        before = _read_ndjson(Path(args.before).resolve())
        after = _read_ndjson(Path(args.after).resolve())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    newly_broken = after - before
    fixed = before - after
    unchanged = before & after
    report = {
        "newly_broken": _render(newly_broken),
        "fixed": _render(fixed),
        "unchanged": _render(unchanged),
        "totals": {
            "before": len(before),
            "after": len(after),
            "newly_broken": len(newly_broken),
            "fixed": len(fixed),
            "unchanged": len(unchanged),
        },
    }
    json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if newly_broken else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="link-baseline",
        description="Capture and compare unresolved links in tracked Markdown files.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    baseline = subcommands.add_parser("baseline", help="Write unresolved links as sorted NDJSON.")
    baseline.add_argument("--root", default=".", help="Repository root.")
    baseline.add_argument("--out", required=True, help="Output NDJSON path.")
    baseline.set_defaults(func=cmd_baseline)

    diff = subcommands.add_parser("diff", help="Compare two unresolved-link baselines.")
    diff.add_argument("--before", required=True, help="Baseline before the change.")
    diff.add_argument("--after", required=True, help="Baseline after the change.")
    diff.set_defaults(func=cmd_diff)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
