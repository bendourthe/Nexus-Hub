#!/usr/bin/env python3
"""Measure what a model actually receives from an installed instruction file.

Repo-internal (listed in DEV_ONLY_SCRIPTS; no installer copy step). For each
`--path` it reports estimated tokens and words, per H1/H2 section sizes,
duplicate headings, the skill-index row and `**Total:` line counts, and the
candidate Legacy Instruction Blocks found by
`scripts/lib/installer/legacy_instruction_block.detect`.

Token counts are ESTIMATED with the stdlib regex estimator imported from
`scripts/check_memory_integration_budget.py`, so the repository keeps one
definition of an estimated token; no tokenizer is imported and nothing is
downloaded. Read-only.

    python scripts/measure_rendered_context.py --path ~/.claude/CLAUDE.md
    python scripts/measure_rendered_context.py --path A --path B --json --redact
    python scripts/measure_rendered_context.py --path A --check

`--redact` replaces the home directory with `~` and every heading that is not a
line some Nexus-Hub template shipped with `user section #n`, so output is safe
to commit. Exit codes: 0 ok; 1 `--check` found a candidate legacy span or more
than one skill-index `**Total:` line; 2 no target was readable or bad arguments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.check_memory_integration_budget import estimate_tokens
from scripts.lib.installer.legacy_instruction_block import (
    detect,
    line_hash,
    load_fingerprints,
)

ESTIMATOR = "estimated (stdlib regex, scripts/check_memory_integration_budget.py)"
_HEADING = re.compile(r"^(#{1,2})\s+(.*\S)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_INDEX_ROW = re.compile(r"^\|.*\|\s*catalog/skills/[^|]+/SKILL\.md\s*\|\s*$")
_TOTAL = re.compile(r"^\*\*Total:\s*\d+\s+skills across\s+\d+\s+categories\*\*\s*$")


def _words(text: str) -> int:
    return len(text.split())


def _sections(lines: list[str]) -> list[dict]:
    """H1/H2 sections outside code fences; text before the first heading is the preamble."""
    sections: list[dict] = [{"heading": "(preamble)", "level": 0, "line": 1, "body": []}]
    fenced = False
    for number, line in enumerate(lines, start=1):
        if _FENCE.match(line):
            fenced = not fenced
        match = None if fenced else _HEADING.match(line)
        if match:
            sections.append({"heading": match.group(2), "level": len(match.group(1)), "line": number,
                             "raw": line, "body": [line]})
        else:
            sections[-1]["body"].append(line)
    if not "".join(sections[0]["body"]).strip():
        sections.pop(0)
    out = []
    for section in sections:
        text = "\n".join(section.pop("body"))
        out.append({**section, "tokens": estimate_tokens(text), "words": _words(text)})
    return out


def _redact_path(path: str) -> str:
    home = Path.home()
    for form in (str(home), home.as_posix()):
        if form and path.startswith(form):
            return "~" + path[len(form):].replace("\\", "/")
    return path


def _redact_headings(sections: list[dict], known: set[str] | None) -> None:
    counter = 0
    for section in sections:
        raw = section.pop("raw", None)
        if raw is None:
            continue
        if known is None or line_hash(raw) not in known:
            counter += 1
            section["heading"] = f"user section #{counter}"


def measure(path: Path, redact: bool, known: set[str] | None) -> dict:
    shown = _redact_path(str(path)) if redact else str(path)
    if not path.is_file():
        return {"path": shown, "status": "missing", "reason": "no such file"}
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except OSError as exc:
        return {"path": shown, "status": "unreadable", "reason": exc.strerror or type(exc).__name__}
    except UnicodeDecodeError:
        return {"path": shown, "status": "unreadable", "reason": "not UTF-8"}
    lines = text.splitlines()
    sections = _sections(lines)
    if redact:
        _redact_headings(sections, known)
    else:
        for section in sections:
            section.pop("raw", None)
    seen: dict[str, int] = {}
    for section in sections:
        if section["level"]:
            seen[section["heading"]] = seen.get(section["heading"], 0) + 1
    legacy = detect(path, known)
    spans = [{"start_line": s.start_line, "end_line": s.end_line, "line_count": s.line_count,
              "tokens": estimate_tokens("\n".join(lines[s.start_line - 1:s.end_line])),
              "consent_sha256": s.consent_sha256} for s in legacy.spans]
    return {
        "path": shown,
        "status": "ok",
        "tokens": estimate_tokens(text),
        "words": _words(text),
        "sections": sections,
        "duplicate_headings": sorted(h for h, n in seen.items() if n > 1 and not h.startswith("user section #")),
        "skill_index_rows": sum(1 for line in lines if _INDEX_ROW.match(line)),
        "skill_index_totals": sum(1 for line in lines if _TOTAL.match(line)),
        "legacy": {"status": legacy.status, "spans": spans, "kept_lines": len(legacy.kept_lines)},
    }


def _render_text(report: dict) -> str:
    out = [f"Token counts: {report['estimator']}"]
    for target in report["targets"]:
        out.append("")
        if target["status"] != "ok":
            out.append(f"{target['path']}: {target['status']} ({target['reason']})")
            continue
        out.append(f"{target['path']}: {target['tokens']} tokens, {target['words']} words")
        for section in target["sections"]:
            indent = "  " * max(section["level"], 1)
            out.append(f"{indent}{section['heading']}: {section['tokens']} tokens")
        out.append(f"  skill index: {target['skill_index_rows']} rows, {target['skill_index_totals']} Total line(s)")
        if target["duplicate_headings"]:
            out.append(f"  duplicate headings: {', '.join(target['duplicate_headings'])}")
        legacy = target["legacy"]
        out.append(f"  legacy spans: {len(legacy['spans'])} ({legacy['status']}), kept lines: {legacy['kept_lines']}")
        for span in legacy["spans"]:
            out.append(f"    lines {span['start_line']}-{span['end_line']}: {span['tokens']} tokens")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--path", action="append", required=True, help="instruction file to measure (repeatable)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 when a target has a legacy span or more than one **Total: line")
    parser.add_argument("--redact", action="store_true", help="hide the home directory and user headings")
    args = parser.parse_args(argv)
    known = load_fingerprints()
    targets = [measure(Path(p).expanduser(), args.redact, known) for p in args.path]
    report = {"estimator": ESTIMATOR, "targets": targets}
    print(json.dumps(report, indent=2) if args.json else _render_text(report))
    readable = [t for t in targets if t["status"] == "ok"]
    for target in targets:
        if target["status"] != "ok":
            print(f"measure_rendered_context: {target['path']}: {target['reason']}", file=sys.stderr)
    if not readable:
        return 2
    if args.check and any(t["legacy"]["spans"] or t["skill_index_totals"] > 1 for t in readable):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
