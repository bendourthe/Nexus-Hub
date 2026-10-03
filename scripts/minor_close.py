#!/usr/bin/env python3
"""Migrate an approved unfixable gap to the next minor, and archive a closed minor.

Installed at ~/.nexus-hub/scripts/minor_close.py beside check_plan_completion.py
and completion_minor.py, which hold the read-only rules; this module performs the
two writes a minor close makes:

    minor_close.py migrate --minor vX.Y --id vA.B#WN-3 --reason R --evidence TEXT
                           [--date YYYY-MM-DD] [--session ID] [--dry-run] [--repo PATH]
    minor_close.py archive --minor vX.Y [--dry-run | --apply] [--confirmed]
                           [--closing-branch chore/close-vX.Y] [--integration-branch develop]
                           [--session ID] [--link-checker PATH] [--repo PATH]
    minor_close.py status --minor vX.Y [--repo PATH]   the gaps.minor and archive.minor lines
    minor_close.py carry --plan PLAN [--id ID]... [--date YYYY-MM-DD] [--session ID] [--dry-run]
    minor_close.py archive --minor vX.Y --plan PLAN --apply [...]   archive on a one-plan run's approval

`migrate` copies one open item whose id is in the minor record's frozen
`gap-migration` list into the next minor's known-gaps.md with a
`**Migrated from**: <minor>#<id> on <date> (reason: <reason>)` line, and suffixes the
source heading with ` - MIGRATED to vX.Y.0`. `archive` verifies the closure
conditions, moves the minor's active tree to docs/archives/vM/vM.m/, repairs every
reference to it, proves zero newly broken links with the docs-layout-refactor link
checker, and commits once; any failure restores the tree unmoved. The rules are
owned by the completion contract ("Minor gaps and archive") and the procedures by
the known-gaps-tracker (Migrate mode) and docs-layout-refactor ("Archive a closed
minor") skills; read those before changing this file.

Exit codes: 0 done, 2 usage, 3 refused (the first line is `REFUSED: <reason> (<detail>)`
or the record's forced verdict). Output carries only fixed reason ids, gap ids,
version tokens, and repository-relative paths, never text read from a ledger.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import check_plan_completion as ck
import completion_minor as cm

EXIT_OK, EXIT_USAGE, EXIT_REFUSED = 0, 2, 3
BUDGET_SECONDS = 180.0
LINK_CHECK_TIMEOUT = 600.0
MAX_TEXT_BYTES = 5_000_000

CATEGORY_NAMES = {
    "NI": "Not Implemented",
    "DF": "Deferred",
    "BG": "Bugs / Regressions",
    "WN": "Warnings",
    "MT": "Missing Tests / Coverage Gaps",
    "QG": "Quality-Gate Gaps",
}
SUMMARY_ROWS = (
    ("Not implemented", "NI"),
    ("Deferred", "DF"),
    ("Bugs / regressions", "BG"),
    ("Warnings", "WN"),
    ("Missing tests / coverage gaps", "MT"),
    ("Quality-gate gaps", "QG"),
)
MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdc"}
# Scripts and tests whose path strings are data the move must follow (see mention_eligible).
CODE_SUFFIXES = {".py", ".sh", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".ts", ".json", ".yml", ".yaml",
                 ".toml", ".csv", ".txt"}
INDEX_NAMES = {"README.md", "INDEX.md", "index.md"}


class Refused(Exception):
    """A refusal the caller reports as `REFUSED: <reason> (<detail>)` with exit 3."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail

    def line(self) -> str:
        return f"REFUSED: {self.reason}" + (f" ({self.detail})" if self.detail else "")


class Forced(Exception):
    """The minor record forces a verdict (tampered, paused, blocked)."""


# --------------------------------------------------------------------------- shared


def _context(args: argparse.Namespace) -> ck.RepoContext:
    return ck.RepoContext(Path(args.repo).resolve(), ck.Budget(BUDGET_SECONDS))


def _git(rctx: ck.RepoContext, *args: str) -> tuple[int, str]:
    return rctx.run([rctx.git, "-C", str(rctx.root), *args])


def _record(rctx: ck.RepoContext, token: str, session: str | None) -> tuple[dict | None, Path]:
    """The verified minor record (or None) and its path; a forced verdict raises Forced."""
    state = cm.load_minor(ck, rctx, token, session)
    if state.forced is not None:
        raise Forced(state.forced[0])
    return state.record, cm.record_file(ck, rctx, token)


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".minor-close.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(tmp, path)


def _newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


# --------------------------------------------------------------------------- link repair


_INLINE_LINK_RE = re.compile(
    r"(?P<pre>!?\[[^\]\n]*\]\()(?P<dest><[^>\n]*>|[^)\s]+)(?P<post>(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\))"
)
_REF_DEF_RE = re.compile(r"^(?P<pre>[ ]{0,3}\[[^\]\n]+\]:[ \t]*)(?P<dest><[^>\n]*>|\S+)")
_CODE_SPAN_RE = re.compile(r"(`+).*?\1")


def repoint(dest: str, old_dir: str, new_dir: str, mapper: Callable[[str], str]) -> str | None:
    """The destination re-expressed from `new_dir` after `mapper`, or None when unchanged.

    Resolves against the referring file's OLD directory (never by counting `../`),
    maps the target through the move, and re-expresses it from the NEW directory.
    External, anchor-only, and out-of-repository destinations are left alone.
    """
    angle = dest.startswith("<") and dest.endswith(">")
    value = dest[1:-1] if angle else dest
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path or value.startswith(("#", "//", "\\\\")):
        return None
    path = unquote(parsed.path)
    suffix = value[len(parsed.path):]
    rooted = path.startswith("/")
    resolved = posixpath.normpath(posixpath.join("" if rooted else old_dir, path.lstrip("/")))
    if resolved == ".." or resolved.startswith("../"):
        return None
    mapped = mapper(resolved)
    if mapped == resolved and old_dir == new_dir:
        return None
    if rooted:
        new_path = "/" + mapped
    else:
        new_path = posixpath.relpath(mapped, new_dir or ".")
    if path.endswith("/") and not new_path.endswith("/"):
        new_path += "/"
    if new_path == path:
        return None
    if "%" in parsed.path or (" " in new_path and not angle):
        new_path = quote(new_path, safe="/-._~")
    rebuilt = new_path + suffix
    return f"<{rebuilt}>" if angle else rebuilt


def _outside_code(text: str, fix: Callable[[str], str], markdown: bool) -> str:
    """Apply `fix` to every stretch of `text` outside fenced code and inline code spans.

    Fences follow the one CommonMark implementation in `completion_minor.fence_mask`;
    a fence left open at the end keeps the rest of the file as code, so nothing past
    it is rewritten. Non-Markdown text has no code syntax and is fixed whole.
    """
    if not markdown:
        return fix(text)
    lines = text.splitlines(keepends=True)
    mask, _unclosed = cm.fence_mask(lines)
    out: list[str] = []
    for index, line in enumerate(lines):
        if mask[index]:
            out.append(line)
            continue
        pieces, last = [], 0
        for code in _CODE_SPAN_RE.finditer(line):
            pieces.append(fix(line[last:code.start()]))
            pieces.append(code.group(0))
            last = code.end()
        pieces.append(fix(line[last:]))
        out.append("".join(pieces))
    return "".join(out)


def rewrite_links(text: str, old_dir: str, new_dir: str, mapper: Callable[[str], str]) -> tuple[str, int]:
    """Repair inline links and link-reference definitions outside code; (text, count)."""
    count = 0

    def fix(segment: str) -> str:
        nonlocal count

        def inline(match: re.Match[str]) -> str:
            nonlocal count
            new = repoint(match.group("dest"), old_dir, new_dir, mapper)
            if new is None:
                return match.group(0)
            count += 1
            return match.group("pre") + new + match.group("post")

        out: list[str] = []
        for line in segment.splitlines(keepends=True):
            line = _INLINE_LINK_RE.sub(inline, line)
            ref = _REF_DEF_RE.match(line)
            if ref:
                new = repoint(ref.group("dest"), old_dir, new_dir, mapper)
                if new is not None:
                    count += 1
                    line = ref.group("pre") + new + line[ref.end():]
            out.append(line)
        return "".join(out)

    return _outside_code(text, fix, markdown=True), count


def _mention_patterns(old: str) -> list[re.Pattern[str]]:
    """`old` as a whole path segment run, in forward- and backslash form."""
    tail = r"(?![A-Za-z0-9_-]|\.\d)"
    return [
        re.compile(r"(?<![A-Za-z0-9_.-])" + re.escape(form) + tail)
        for form in (old, old.replace("/", "\\"))
    ]


def _in_url(text: str, start: int) -> bool:
    """True when the match at `start` sits inside a URL token (a scheme or `//` before it)."""
    token_start = max(text.rfind(c, 0, start) for c in " \t\r\n(<[\"'`") + 1
    token = text[token_start:start]
    return "://" in token or token.startswith("//") or "www." in token


def rewrite_mentions(text: str, old: str, new: str, markdown: bool = False) -> tuple[str, int]:
    """Replace plain mentions of the old tree outside URLs and, in Markdown, outside code."""
    count = 0

    def fix(segment: str) -> str:
        nonlocal count
        for pattern, replacement in zip(_mention_patterns(old), (new, new.replace("/", "\\"))):
            source = segment

            def swap(match: re.Match[str], r: str = replacement, within: str = source) -> str:
                nonlocal count
                if _in_url(within, match.start()):
                    return match.group(0)
                count += 1
                return r
            segment = pattern.sub(swap, source)
        return segment

    return _outside_code(text, fix, markdown), count


@dataclass
class Repair:
    new_rel: str
    old_rel: str
    original: str
    repaired: str
    links: int
    mentions: int


def link_eligible(old_rel: str) -> bool:
    """Markdown anywhere gets its links repaired; a link is navigation, not evidence."""
    return posixpath.splitext(old_rel)[1].lower() in MARKDOWN_SUFFIXES


def mention_eligible(old_rel: str) -> bool:
    """Plain path mentions are rewritten only where a path is live data, never in evidence.

    The allowlist: known-gaps trackers, plans, `docs/todos.md`, README-style indexes
    under `docs/`, and scripts and tests that read a path. Nothing under
    `docs/archives/` (another archive's evidence records the tree as it was), and no
    HTML, JSON, CSV, or other captured output elsewhere.
    """
    name = posixpath.basename(old_rel)
    suffix = posixpath.splitext(name)[1].lower()
    if old_rel.startswith(("docs/archives/", "docs/archive/")):
        return False
    if name == "known-gaps.md" or old_rel == "docs/todos.md":
        return True
    if suffix == ".md" and "/plans/" in f"/{old_rel}":
        return True
    if old_rel.startswith("docs/") and name in INDEX_NAMES:
        return True
    return old_rel.startswith(("scripts/", "tests/")) and suffix in CODE_SUFFIXES


def plan_repairs(
    root: Path, files: list[tuple[str, str, str]], src: str, dst: str,
) -> list[Repair]:
    """Every tracked file whose references to the moved tree change.

    `files` is (path to read, pre-move path, post-move path). Markdown gets the link
    pass (classes 2, 3, 5, and 7 of the renumber procedure's reference list: links
    from sibling trees, link-reference definitions, tracker rows, and evidence under
    the moved tree), then files on the mention allowlist get the plain-mention pass
    (classes 1, 4, and 6: plan and tracker prose, self-referential task-line paths,
    and tracker headings). Links inside URLs and code are never touched.
    """

    def mapper(path: str) -> str:
        if path == src or path.startswith(src + "/"):
            return dst + path[len(src):]
        return path

    repairs: list[Repair] = []
    for read_rel, old_rel, new_rel in files:
        links_ok, mentions_ok = link_eligible(old_rel), mention_eligible(old_rel)
        if not links_ok and not mentions_ok:
            continue
        path = root / read_rel
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                continue
            with path.open("r", encoding="utf-8", newline="") as handle:
                original = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        text, links, mentions = original, 0, 0
        if links_ok:
            text, links = rewrite_links(text, posixpath.dirname(old_rel), posixpath.dirname(new_rel), mapper)
        if mentions_ok:
            text, mentions = rewrite_mentions(text, src, dst, markdown=links_ok)
        if text != original:
            repairs.append(Repair(new_rel, old_rel, original, text, links, mentions))
    return repairs


# --------------------------------------------------------------------------- migrate


def _block_end(text: str, start: int, level: int) -> int:
    """Offset of the first heading at `level` or above after `start`, else len(text)."""
    lines = text[start:].splitlines(keepends=True)
    pos = start
    for index, line in enumerate(lines):
        if index > 0:
            match = re.match(r"^(#{1,6})[ \t]", line)
            if match and len(match.group(1)) <= level:
                return pos
        pos += len(line)
    return len(text)


def _find_heading(text: str, level: int, predicate: Callable[[str], bool], start: int = 0, end: int | None = None) -> int | None:
    end = len(text) if end is None else end
    # `\r` too: a ledger checked out with CRLF endings must still match its headings,
    # or the summary-count check and update would silently be skipped.
    for match in re.finditer(r"^(#{1,6})[ \t]+(.*?)[ \t\r]*$", text[start:end], re.MULTILINE):
        if len(match.group(1)) == level and predicate(match.group(2)):
            return start + match.start()
    return None


def _template(token: str, version: str, project: str, date: str, nl: str) -> str:
    rows = [f"| {label} ({kind}) | 0 | 0 |" for label, kind in SUMMARY_ROWS]
    return nl.join([
        f"# Known Gaps - {token}", "",
        f"**Project**: {project}",
        "**Status**: in-progress",
        f"**Last updated**: {date}",
        "**Open items**: 0", "",
        _section_body(version, rows).replace(chr(10), nl), "",
    ])


def _section_body(version: str, rows: list[str]) -> str:
    return "\n".join([
        f"## {version}", "", "### Summary", "",
        "| Category | Open | Resolved |", "|---|---|---|", *rows, "",
        "### Open Items", "",
        "### Resolved", "",
        "| ID | Title | Resolved in | Notes |", "|---|---|---|---|",
    ])


def _derived_open(text: str, section: str, kind: str) -> int:
    return sum(
        1 for i in cm.parse_ledger(text) if i.section == section and i.kind == kind and i.state == "open"
    )


def _adjust_summary(text: str, section: str, kind: str, before: str) -> str:
    """Set the section's Summary Open cell for `kind` to the derived count.

    The row must equal the count derived from the file before the change (the
    tracker's hard-stop rule); a section without a Summary row is left as it is.
    """
    head = _find_heading(text, 2, lambda h: h == section)
    if head is None:
        return text
    end = _block_end(text, head, 2)
    summary = _find_heading(text, 3, lambda h: h.lower().startswith("summary"), head, end)
    if summary is None:
        return text
    summary_end = _block_end(text, summary, 3)
    row_re = re.compile(r"^(\|[^|\n]*\(" + kind + r"\)[^|\n]*\|\s*)(\d+)(\s*\|)", re.MULTILINE)
    row = row_re.search(text, summary, summary_end)
    if row is None:
        return text
    if int(row.group(2)) != _derived_open(before, section, kind):
        raise Refused("summary-mismatch", f"{section.split()[0]} {kind}")
    new = _derived_open(text, section, kind)
    return text[: row.start(2)] + str(new) + text[row.end(2):]


def _set_header(text: str, date: str) -> str:
    """Set `**Last updated**` and the derived `**Open items**` total in the file header."""
    nl = _newline(text)
    first = re.search(r"^## ", text, re.MULTILINE)
    header_end = first.start() if first else len(text)
    header, rest = text[:header_end], text[header_end:]
    total = sum(1 for i in cm.parse_ledger(text) if i.state == "open")
    header = re.sub(r"^\*\*Last updated\*\*:[^\r\n]*", f"**Last updated**: {date}", header, count=1, flags=re.MULTILINE)
    line = f"**Open items**: {total}"
    if re.search(r"^\*\*Open items\*\*:", header, re.MULTILINE):
        header = re.sub(r"^\*\*Open items\*\*:[^\r\n]*", line, header, count=1, flags=re.MULTILINE)
    else:
        anchor = None
        for key in ("Last updated", "Status", "Project"):
            anchor = re.search(r"^\*\*" + key + r"\*\*:[^\r\n]*", header, re.MULTILINE)
            if anchor:
                break
        if anchor:
            header = header[: anchor.end()] + nl + line + header[anchor.end():]
        else:
            header = header.rstrip() + nl + nl + line + nl + nl
    return header + rest


def _entry(item: cm.GapItem, gid: str, level: int, body: str, lines: list[str], nl: str) -> str:
    title = item.title
    kept = body.strip("\r\n").rstrip()  # one blank line after the heading, never two
    parts = [f"{'#' * level} {gid}{title}", ""]
    if kept:
        parts += [kept, ""]
    parts += lines
    return nl.join(parts) + nl + nl


def _insert_entry(text: str, version: str, item: cm.GapItem, gid: str, body: str, lines: list[str]) -> str:
    """Append the migrated entry under the target's `## <version>` Open Items."""
    nl = _newline(text)
    head = _find_heading(text, 2, lambda h: h.split()[0] == version if h.split() else False)
    if head is None:
        rows = [f"| {label} ({kind}) | 0 | 0 |" for label, kind in SUMMARY_ROWS]
        text = text.rstrip() + nl + nl + _section_body(version, rows).replace("\n", nl) + nl
        head = _find_heading(text, 2, lambda h: h.split()[0] == version if h.split() else False)
        assert head is not None
    section_end = _block_end(text, head, 2)
    open_at = _find_heading(text, 3, lambda h: h.lower().startswith("open items"), head, section_end)
    if open_at is None:
        resolved = _find_heading(text, 3, lambda h: h.lower().startswith("resolved"), head, section_end)
        insert_at = resolved if resolved is not None else section_end
        text = text[:insert_at] + "### Open Items" + nl + nl + text[insert_at:]
        section_end = _block_end(text, head, 2)
        open_at = _find_heading(text, 3, lambda h: h.lower().startswith("open items"), head, section_end)
        assert open_at is not None
    open_end = _block_end(text, open_at, 3)
    level, insert_at = 4, open_end
    category = CATEGORY_NAMES.get(item.kind)
    has_categories = any(
        not cm.LEDGER_ITEM_RE.match(m.group(1))
        for m in re.finditer(r"^#### (.+?)\s*$", text[open_at:open_end], re.MULTILINE)
    )
    if has_categories:
        level = 5
        cat_at = None if category is None else _find_heading(
            text, 4, lambda h: h.strip().lower() == category.lower(), open_at, open_end
        )
        if cat_at is None:
            text = text[:open_end] + f"#### {category or item.kind}" + nl + nl + text[open_end:]
            cat_at = open_end  # the new category ends where Open Items did: at the next `###`
        insert_at = _block_end(text, cat_at, 4)
    before = text[:insert_at]
    if before and not before.endswith(nl + nl):
        before = before.rstrip("\r\n") + nl + nl
    return before + _entry(item, gid, level, body, lines, nl) + text[insert_at:].lstrip("\r\n")


def _next_gid(text: str, kind: str) -> str:
    numbers = [int(i.gid.split("-")[1]) for i in cm.parse_ledger(text) if i.kind == kind]
    return f"{kind}-{max(numbers, default=0) + 1}"


@dataclass
class MigrationPlan:
    pid: str
    source: cm.Ledger
    item: cm.GapItem
    target_path: Path
    target_rel: str
    target_before: str | None
    target_after: str
    source_after: str
    new_gid: str
    reused: bool


def _project_name(root: Path, text: str) -> str:
    found = re.search(r"^\*\*Project\*\*:\s*([^\r\n]+)", text, re.MULTILINE)
    return found.group(1).strip() if found else root.name


def plan_migration(
    rctx: ck.RepoContext, token: str, record: dict, pid: str, reason: str, evidence: str, date: str,
) -> MigrationPlan:
    """Every check the Migrate mode requires, then the two files' new text, unwritten."""
    bound, _named = cm.migration_class(record)
    if pid not in bound:
        raise Refused("migration-not-approved", pid)
    source_token, gid = pid.split("#")
    source_minor = cm.minor_of(source_token)
    if source_minor > cm.minor_of(token):
        raise Refused("out-of-scope", pid)
    ledgers, unreadable = cm.load_ledgers(rctx.root)
    if unreadable:
        raise Refused("ledger-unreadable", unreadable[0])
    sources = [l for l in ledgers if l.minor == source_minor]
    if len(sources) != 1:
        raise Refused("source-ledger-missing" if not sources else "source-ledger-ambiguous", source_token)
    source = sources[0]
    if source.problems:
        raise Refused("ledger-unparsed", f"{source.rel} {source.problems[0]}")
    matches = [i for i in source.items if i.gid == gid]
    open_items = [i for i in matches if i.state == "open"]
    if len(open_items) > 1:
        raise Refused("gap-ambiguous", pid)
    if not open_items:
        raise Refused("already-migrated" if any(i.state == "migrated" for i in matches) else "gap-not-open", pid)
    item = open_items[0]
    # The shared gate: frozen id, open at the record's start, and named when the item
    # is security or high-severity now OR at the start (an edited Severity line counts).
    gate, why = cm.migration_gate(rctx, record, source_minor, gid, item)
    if gate == "cannot-verify":
        raise Refused("cannot-verify", "ledger history at the record start")
    if gate != "met":
        raise Refused(why, pid)
    target_token = cm.next_minor(token)
    tmin = cm.minor_of(target_token)
    target_path, target_rel, target_before = _target_ledger(rctx, ledgers, target_token)
    scoped = [source, cm.Ledger(target_path, target_rel, tmin, "active", target_before or "", [])]
    excluded = cm.excluded_ledgers(ck, rctx, token, record, scoped)
    if excluded is None:
        raise Refused("cannot-verify", "which branches touch the ledgers")
    if source.rel in excluded:
        raise Refused("source-" + excluded[source.rel], source.rel)
    if target_rel in excluded:
        raise Refused("target-" + excluded[target_rel], target_rel)
    return _migration_texts(rctx, pid, source, item, target_token, (target_path, target_rel, target_before),
                            reason, evidence, date)


def _target_ledger(rctx: ck.RepoContext, ledgers: list[cm.Ledger], target_token: str) -> tuple[Path, str, str | None]:
    """(path, repository-relative path, current text or None) of the next minor's active ledger."""
    tmin = cm.minor_of(target_token)
    targets = [l for l in ledgers if l.minor == tmin]
    active = [l for l in targets if l.layout == "active"]
    if targets and not active:
        raise Refused("target-archived", target_token)
    if len(active) > 1:
        raise Refused("target-ledger-ambiguous", target_token)
    if active:
        if active[0].problems:
            raise Refused("ledger-unparsed", f"{active[0].rel} {active[0].problems[0]}")
        return active[0].path, active[0].rel, active[0].text
    target_rel = cm.ledger_rels(*tmin)[0]
    return rctx.root / target_rel, target_rel, None


def _migration_texts(
    rctx: ck.RepoContext, pid: str, source: cm.Ledger, item: cm.GapItem, target_token: str,
    target: tuple[Path, str, str | None], reason: str, evidence: str, date: str,
    label: str | None = None,
) -> MigrationPlan:
    """Both files' new text for moving one open item to the next minor's `.0` section.

    `label` names the source as `vX.Y.Z#ID` for a one-plan run, whose ledger repeats
    ids across version sections; a minor close names it `vX.Y#ID`.
    """
    gid = item.gid
    source_label = label or f"{source.token()}#{gid}"
    target_path, target_rel, target_before = target
    target_version = target_token + ".0"
    tmin = cm.minor_of(target_token)
    nl = _newline(source.text)
    target_text = target_before if target_before is not None else _template(
        target_token, target_version, _project_name(rctx.root, source.text), date, nl
    )
    target_items = cm.parse_ledger(target_text)
    if label is None:
        existing = cm.find_migrated_copy(
            [cm.Ledger(target_path, target_rel, tmin, "active", target_text, target_items)],
            target_version, source.token(), gid,
        )
    else:
        existing = next(
            ((None, copy) for copy in target_items
             if any(f"{m.group('version')}#{m.group('id')}" == label for m in cm.PLAN_MIGRATED_FROM_RE.finditer(copy.body))),
            None,
        )
    if existing is not None:
        # A re-run after a partial write: the copy exists, so never write a duplicate entry.
        target_after, new_gid, reused = target_text, existing[1].gid, True
    else:
        new_gid = _next_gid(target_text, item.kind)
        body, _ = rewrite_links(
            item.body, posixpath.dirname(source.rel), posixpath.dirname(target_rel), lambda p: p
        )
        # A second migration keeps the earlier `**Migrated from**` line in the body
        # and adds this one, so the chain back to the first minor stays readable.
        lines = [
            f"- **Migrated from**: {source_label} on {date} (reason: {reason})",
            f"- **Migration evidence**: {evidence}",
        ]
        target_after = _insert_entry(target_text, target_version, item, new_gid, body, lines)
        target_after = _adjust_summary(target_after, _section_heading(target_after, target_version), item.kind, target_text)
        target_after = _set_header(target_after, date)
        reused = False
    source_after = source.text[: item.heading_end] + f" - MIGRATED to {target_version}" + source.text[item.heading_end:]
    source_after = _adjust_summary(source_after, item.section, item.kind, source.text)
    source_after = _set_header(source_after, date)
    return MigrationPlan(pid, source, item, target_path, target_rel, target_before, target_after,
                         source_after, new_gid, reused)


def _section_heading(text: str, version: str) -> str:
    for match in re.finditer(r"^## (.*?)[ \t\r]*$", text, re.MULTILINE):
        if match.group(1).split() and match.group(1).split()[0] == version:
            return match.group(1)
    return version


def _read_exact(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return handle.read()
    except FileNotFoundError:
        return None


def apply_migration(plan: MigrationPlan) -> None:
    """Write the target, then the source; a concurrent edit or a failure writes neither."""
    if _read_exact(plan.source.path) != plan.source.text:
        raise Refused("source-changed", plan.source.rel)
    if _read_exact(plan.target_path) != plan.target_before:
        raise Refused("target-changed", plan.target_rel)
    if not plan.reused:
        _write_atomic(plan.target_path, plan.target_after)
    try:
        if _read_exact(plan.source.path) != plan.source.text:
            raise Refused("source-changed", plan.source.rel)
        _write_atomic(plan.source.path, plan.source_after)
    except (OSError, Refused):
        if not plan.reused:
            if plan.target_before is None:
                plan.target_path.unlink(missing_ok=True)
            else:
                _write_atomic(plan.target_path, plan.target_before)
        raise


def cmd_migrate(args: argparse.Namespace) -> int:
    rctx = _context(args)
    token = args.minor
    cm.parse_minor(ck, token)
    pid = cm.normalize_gap_id(args.id)
    if pid is None:
        raise ck.Malformed("--id must name a gap such as v0.5#WN-3")
    if args.reason not in cm.MIGRATION_REASONS:
        raise ck.Malformed("--reason must be one of " + ", ".join(cm.MIGRATION_REASONS))
    evidence = " ".join(str(args.evidence or "").split())
    if not evidence:
        raise ck.Malformed("--evidence must say why the gap cannot be fixed in this minor")
    date = args.date or _today()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ck.Malformed("--date must be YYYY-MM-DD")
    record, _path = _record(rctx, token, args.session)
    if record is None:
        raise Refused("approval-not-covered", f"no minor record for {token}")
    plan = plan_migration(rctx, token, record, pid, args.reason, evidence, date)
    target_token = cm.next_minor(token)
    verb = "WOULD MIGRATE" if args.dry_run else "MIGRATED"
    if not args.dry_run:
        apply_migration(plan)
    print(f"{verb} {pid} -> {target_token}#{plan.new_gid} ({target_token}.0) {plan.target_rel}")
    return EXIT_OK


# --------------------------------------------------------------------------- one-plan carry


def _plan_record(plan: str, session: str | None) -> tuple[ck.Context, dict]:
    """The plan's context and its verified schema-1 run record, or a refusal."""
    ctx = ck.Context(plan, ck.Budget(BUDGET_SECONDS))
    state = ck.load_record(ctx, session)
    if state.forced is not None:
        raise Forced(state.forced[0])
    if state.record is None or state.record.get("schema") != ck.SCHEMA:
        raise Refused("approval-not-covered", "no verified run record for this plan")
    return ctx, state.record


def _named(record: dict, name: str) -> set[str]:
    entry = next((c for c in (record.get("approvals") or {}).get("classes") or []
                  if isinstance(c, dict) and c.get("class") == name), {})
    return {pid for pid in (cm.normalize_gap_id(str(i)) for i in entry.get("named") or []) if pid}


def _last_plan(ctx: ck.Context, record: dict) -> bool:
    repo = (record.get("approvals") or {}).get("repo") or ctx.default_repo
    state = cm.last_plan_status(ck, ctx, ctx.version, repo)
    if state == "cannot-verify":
        raise Refused("cannot-verify", "whether this is the last plan of its minor")
    return state == "met"


def _source_ledger(ctx: ck.Context) -> tuple[list[cm.Ledger], cm.Ledger]:
    minor = cm.minor_of(ctx.version)
    ledgers, unreadable = cm.load_ledgers(ctx.root)
    if unreadable:
        raise Refused("ledger-unreadable", unreadable[0])
    own = [l for l in ledgers if l.minor == minor and l.layout == "active"]
    if len(own) != 1:
        raise Refused("source-ledger-missing" if not own else "source-ledger-ambiguous", ctx.version)
    if own[0].problems:
        raise Refused("ledger-unparsed", f"{own[0].rel} {own[0].problems[0]}")
    return ledgers, own[0]


_TITLE_VERSION_RE = re.compile(r"^(\s*)\(v\d+\.\d+\.\d+\)")


def carry_within(text: str, item: cm.GapItem, target: str, version: str, date: str) -> tuple[str, str]:
    """Move one open item into the next patch's section under the next free id.

    Ids repeat across a ledger's version sections, so the item takes the next free id
    of its kind, its title's `(vX.Y.Z)` tag becomes the target's, and a
    `**Carried from**: <version>#<old id>` line keeps its origin exact.
    Returns (new text, new id).
    """
    removed = text[: item.start] + text[item.end:]
    new_gid = _next_gid(text, item.kind)
    title = _TITLE_VERSION_RE.sub(lambda m: f"{m.group(1)}({target})", item.title, count=1)
    lines = [f"- **Carried from**: {version}#{item.gid} on {date}"]
    moved = _insert_entry(removed, target, replace(item, title=title), new_gid, item.body, lines)
    moved = _adjust_summary(moved, item.section, item.kind, text)
    moved = _adjust_summary(moved, _section_heading(moved, target), item.kind, text)
    return _set_header(moved, date), new_gid


def cmd_carry(args: argparse.Namespace) -> int:
    ctx, record = _plan_record(args.plan, args.session)
    if not ck._has_class(record, "carry-gaps"):
        raise Refused("approval-not-covered", "the run record does not carry carry-gaps")
    date = args.date or _today()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ck.Malformed("--date must be YYYY-MM-DD")
    last = _last_plan(ctx, record)
    token = "v{}.{}".format(*cm.minor_of(ctx.version))
    ledgers, source = _source_ledger(ctx)
    chosen = [i for i in source.items if i.state == "open"
              and (last or cm.section_version(i.section) == ctx.version)]
    if args.id:
        # `WN-3`, or `v4.13.7#WN-3` when the same id is open in more than one section.
        wanted = {(raw.split("#", 1)[0] if "#" in raw else None, raw.split("#")[-1]) for raw in args.id}

        def hit(item: cm.GapItem, want: tuple[str | None, str]) -> bool:
            return want[1] == item.gid and want[0] in (None, cm.section_version(item.section))

        missing = sorted(f"{v}#{g}" if v else g for v, g in wanted if not any(hit(i, (v, g)) for i in chosen))
        if missing:
            raise Refused("gap-not-open", ", ".join(missing))
        chosen = [i for i in chosen if any(hit(i, w) for w in wanted)]
    named = _named(record, "carry-gaps")
    unnamed = [f"{token}#{i.gid}" for i in chosen if i.sensitive() and f"{token}#{i.gid}" not in named]
    if unnamed:
        raise Refused("security-not-named", ", ".join(unnamed))
    target = cm.carry_target(ctx.version, last)
    verb = "WOULD " if args.dry_run else ""
    for key in [(cm.section_version(i.section), i.gid) for i in chosen]:
        ledgers, source = _source_ledger(ctx)
        item = next(i for i in source.items if (cm.section_version(i.section), i.gid) == key and i.state == "open")
        label = f"{key[0]}#{key[1]}"
        if last:
            target_token = cm.next_minor(token)
            plan = _migration_texts(
                ctx, f"{token}#{key[1]}", source, item, target_token,
                _target_ledger(ctx, ledgers, target_token), cm.PLAN_CARRY_REASON,
                f"left open by {ctx.version}, the last plan of {token}", date, label=label,
            )
            if not args.dry_run:
                apply_migration(plan)
            print(f"{verb}MIGRATED {label} -> {target_token}#{plan.new_gid} ({target}) {plan.target_rel}")
            continue
        after, new_gid = carry_within(source.text, item, target, ctx.version, date)
        if not args.dry_run:
            if _read_exact(source.path) != source.text:
                raise Refused("source-changed", source.rel)
            _write_atomic(source.path, after)
        print(f"{verb}CARRIED {label} -> {target}#{new_gid} {source.rel}")
    if not chosen:
        print(f"NOTHING TO CARRY {ctx.version}")
    return EXIT_OK


# --------------------------------------------------------------------------- archive


_UNCHECKED_TASK_RE = re.compile(r"^- \[ \] T\d+\b", re.MULTILINE)
_STATUS_RE = re.compile(r"^\*\*Status\*\*\s*:(.*)$", re.MULTILINE | re.IGNORECASE)
_ZERO_OPEN_RE = re.compile(r"^\*\*Open items\*\*\s*:\s*0\s*$", re.MULTILINE | re.IGNORECASE)
_PLAN_REL_RE = re.compile(r"^docs/(?:[^/]+/)*plans/[^/]+\.md\Z", re.ASCII)


def source_tree(rctx: ck.RepoContext, major: int, minor: int) -> str | None:
    """The one active tree of the minor, None when there is none; two is a refusal."""
    found = [t.format(M=major, m=minor) for t in cm.ACTIVE_TREES if (rctx.root / t.format(M=major, m=minor)).is_dir()]
    if len(found) > 1:
        raise Refused("multiple-active-trees", ", ".join(found))
    return found[0] if found else None


def register_refusals(
    rctx: ck.RepoContext, token: str, record: dict | None, tree: str,
) -> list[Refused]:
    """The known-gaps closure test of `/update release` step 2a2, with verified
    migrations counted as closed. Status and `**Open items**` are read from the file
    header only (before the first `## ` heading), so a line quoted further down never
    closes the register."""
    ledgers, unreadable = cm.load_ledgers(rctx.root)
    rel = f"{tree}/known-gaps.md"
    ledger = next((l for l in ledgers if l.rel == rel), None)
    if rel in unreadable:
        return [Refused("register-unreadable", rel)]
    if ledger is None:
        return [Refused("no-register", rel)]
    out = [Refused("register-unparsed", f"{rel} {problem}") for problem in ledger.problems]
    plan_run = (record or {}).get("schema") == ck.SCHEMA
    for item in ledger.items:
        if item.state == "open":
            out.append(Refused("open-gap", f"{token}#{item.gid}"))
        elif item.state == "migrated" and plan_run:
            # A one-plan run's migration (completion contract, "Single-plan carry and archive").
            if not cm.plan_migration_met(ledgers, ledger, item):
                out.append(Refused("unverified-migration", f"{token}#{item.gid} migration-target-missing"))
        elif item.state == "migrated":
            status, reason = cm.verify_migration(rctx, record, token, ledgers, ledger, item)
            if status != "met":
                out.append(Refused("unverified-migration", f"{token}#{item.gid} {reason}"))
    header = cm.ledger_header(ledger.text)
    if not _ZERO_OPEN_RE.search(header):
        out.append(Refused("open-items-not-zero", rel))
    statuses = [m.group(1).lower() for m in _STATUS_RE.finditer(header)]
    if not any(re.search(r"\b(?:finalized|closed)\b", s) for s in statuses):
        out.append(Refused("register-not-finalized", rel))
    if any("in-progress" in s or "in progress" in s or (re.search(r"\bopen\b", s) and "no open" not in s) for s in statuses):
        out.append(Refused("register-status-open", rel))
    if "- [ ]" in ledger.text:
        out.append(Refused("register-unchecked-box", rel))
    return out


def plan_refusals(rctx: ck.RepoContext, token: str, record: dict | None) -> list[Refused]:
    """Every plan of the minor is released (or superseded), has no unchecked task, and
    no queued plan sits outside the frozen members."""
    major, minor = cm.parse_minor(ck, token)
    try:
        plans = cm.scan_plans(rctx.root, major, minor)
    except cm.MinorMalformed as exc:
        return [Refused("plans-malformed", str(exc))]
    members = {str(m.get("version")) for m in (record or {}).get("members") or [] if isinstance(m, dict)}
    repo = cm.hosting_repo(ck, rctx, (record or {}).get("repo"))
    out: list[Refused] = []
    for plan in plans:
        if _UNCHECKED_TASK_RE.search(plan.text):
            out.append(Refused("unchecked-task", plan.version))
        if plan.status == "superseded":
            continue
        if plan.status not in cm.DONE_STATUSES and plan.version not in members:
            out.append(Refused("queued-plan-outside-members", plan.version))
        state = cm.shipped(ck, rctx, repo, plan.version)
        if state == "unmet":
            out.append(Refused("unreleased-member", plan.version))
        elif state != "met":
            out.append(Refused("cannot-verify-shipped", plan.version))
    return out


def branch_refusals(
    rctx: ck.RepoContext, token: str, record: dict | None, tree: str, closing: str, integration_branch: str,
) -> list[Refused]:
    """No live worktree on the minor's branches, and no unmerged remote branch touching its tree."""
    major, minor = cm.parse_minor(ck, token)
    out: list[Refused] = []
    member_branches = cm.record_branches(record)
    prefix = f"feat/v{major}.{minor}."
    rc, listing = _git(rctx, "worktree", "list", "--porcelain")
    if rc != 0:
        return [Refused("cannot-verify", "worktree list")]
    for block in listing.split("\n\n"):
        path = next((l[len("worktree "):] for l in block.splitlines() if l.startswith("worktree ")), None)
        branch = next((l[len("branch refs/heads/"):] for l in block.splitlines() if l.startswith("branch refs/heads/")), None)
        if path is None or branch is None or Path(path).resolve() == rctx.root:
            continue
        if branch.startswith(prefix) or branch in member_branches:
            out.append(Refused("live-worktree", branch))
    integration = cm._integration_ref(rctx, integration_branch)
    if integration is None:
        return out + [Refused("cannot-verify", f"integration branch {integration_branch}")]
    rc, heads = _git(rctx, "ls-remote", "--heads", "origin")
    if rc != 0:
        return out + [Refused("cannot-verify", "origin heads")]
    skip = {integration_branch, "main", "master", closing}
    for line in heads.splitlines():
        sha, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/heads/")
        if not ref.startswith("refs/heads/") or name in skip:
            continue
        if _git(rctx, "cat-file", "-e", sha)[0] != 0:
            out.append(Refused("cannot-verify", f"branch {name} is not fetched"))
            continue
        if cm._merged(rctx, sha, integration):
            continue
        rc, changed = _git(rctx, "diff", "--name-only", f"{integration}...{sha}", "--", tree)
        if rc != 0:
            out.append(Refused("cannot-verify", f"branch {name}"))
        elif changed.strip():
            out.append(Refused("unmerged-branch-touches-tree", name))
    return out


def tracked_under(rctx: ck.RepoContext, tree: str) -> list[str]:
    rc, out = _git(rctx, "ls-files", "-z", "--", tree)
    if rc != 0:
        raise Refused("cannot-verify", "tracked files")
    return [p for p in out.split("\0") if p]


def tree_refusals(rctx: ck.RepoContext, tree: str, dest: str, closing: str) -> list[Refused]:
    out: list[Refused] = []
    rc, status = _git(rctx, "status", "--porcelain")
    if rc != 0 or status.strip():
        out.append(Refused("dirty-worktree", "commit or stash first; rollback needs a clean tree"))
    branch = cm.current_branch(rctx)
    if branch != closing:
        out.append(Refused("not-on-closing-branch", branch or "detached"))
    for rel in tracked_under(rctx, tree):
        moved = dest + rel[len(tree):]
        if (rctx.root / moved).exists():
            out.append(Refused("archive-collision", moved))
            break
    return out


def bound_plan_refusals(rctx: ck.RepoContext, repairs: list[Repair], record: dict | None) -> list[Refused]:
    """A repair that rewrites a plan another live run froze by hash would make that run
    `record-tampered`; name those plans and refuse instead."""
    plans = {r.old_rel for r in repairs if _PLAN_REL_RE.match(r.old_rel)}
    if not plans:
        return []
    own_nonce = (record or {}).get("nonce")
    bound: set[str] = set()
    for path in ck.find_records_by_content(rctx.root, lambda r: True):
        other = ck.read_record(rctx, path)
        if other is None:
            bound.update(plans)  # an unreadable record could bind any of them
            continue
        if own_nonce and other.get("nonce") == own_nonce:
            continue
        if other.get("schema") == ck.SCHEMA:
            if other.get("plan") in plans and ck.record_live(rctx, path)[0]:
                bound.add(str(other.get("plan")))
        elif cm._minor_record_live(ck, other):
            for member in other.get("members") or []:
                if isinstance(member, dict) and member.get("plan_path") in plans:
                    bound.add(str(member.get("plan_path")))
    return [Refused("plan-bound-by-another-run", rel) for rel in sorted(bound)]


def link_checker(root: Path, override: str | None) -> Path | None:
    """The docs-layout-refactor link checker: an installed copy first, then this repository's."""
    home = Path.home()
    candidates = [Path(override)] if override else []
    candidates += [
        home / ".claude" / "skills" / "docs-layout-refactor" / "scripts" / "link-baseline.py",
        home / ".agents" / "skills" / "docs-layout-refactor" / "scripts" / "link-baseline.py",
        home / ".codex" / "skills" / "docs-layout-refactor" / "scripts" / "link-baseline.py",
        Path(_SCRIPT_DIR) / "link-baseline.py",
        root / "catalog" / "skills" / "code-cleanup" / "docs-layout-refactor" / "scripts" / "link-baseline.py",
    ]
    return next((c for c in candidates if c.is_file()), None)


def _link_run(checker: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            [sys.executable, str(checker), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=LINK_CHECK_TIMEOUT, env=ck._env(), check=False,
            **ck.NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return -1, ""
    return proc.returncode, proc.stdout


@dataclass
class Moves:
    pairs: list[tuple[str, str]] = field(default_factory=list)  # (from, to) in order


def _git_mv(rctx: ck.RepoContext, src: str, dst: str) -> bool:
    (rctx.root / dst).parent.mkdir(parents=True, exist_ok=True)
    return _git(rctx, "mv", "--", src, dst)[0] == 0


def move_tree(rctx: ck.RepoContext, tree: str, dest: str, moves: Moves) -> None:
    """`git mv` the tree whole, or file by file into an existing archive directory.

    Every completed move is appended to `moves` as it happens, so a caller's rollback
    sees a partial move too. A failed `git mv` (a locked directory, antivirus,
    OneDrive) refuses with `locked-directory`.
    """
    if not (rctx.root / dest).exists():
        pairs = [(tree, dest)]
    else:
        pairs = [(rel, dest + rel[len(tree):]) for rel in tracked_under(rctx, tree)]
    for src, dst in pairs:
        if not _git_mv(rctx, src, dst):
            raise Refused("locked-directory", src)
        moves.pairs.append((src, dst))
    # A file-by-file move leaves the emptied directories behind; drop only empty ones.
    for dirpath, _dirs, _files in sorted(os.walk(rctx.root / tree), key=lambda w: -len(w[0])):
        try:
            Path(dirpath).rmdir()
        except OSError:
            pass  # not empty (an ignored file stays where it was)


def undo_moves(rctx: ck.RepoContext, moves: Moves) -> bool:
    ok = True
    for src, dst in reversed(moves.pairs):
        ok = _git_mv(rctx, dst, src) and ok
    return ok


def _rename_rows(rctx: ck.RepoContext) -> str:
    rc, out = _git(rctx, "diff", "--cached", "--name-status", "-M", "HEAD")
    if rc != 0:
        raise Refused("cannot-verify", "rename map")
    return "\n".join(l for l in out.splitlines() if l.startswith("R")) + "\n"


def _restore(rctx: ck.RepoContext, written: list[Repair], moves: Moves, staged: bool) -> bool:
    """Put every written file back and undo the moves; False when anything failed.

    Only files actually written are restored (a repair never written needs nothing),
    each attempt is independent, and the moves are undone even when a restore fails.
    """
    ok = True
    for repair in reversed(written):
        try:
            _write_atomic(rctx.root / repair.new_rel, repair.original)
        except OSError:
            ok = False
    if staged and written:
        ok = _git(rctx, "add", "--", *[r.new_rel for r in written])[0] == 0 and ok
    return undo_moves(rctx, moves) and ok


def refreeze(rctx: ck.RepoContext, record: dict, record_path: Path, token: str) -> None:
    """Re-freeze each member's `plan_path` and `plan_sha256` at its archived path and re-sign.

    The record was verified before the move, so every member hashed to its frozen
    value then; the new values bind only the link and path repairs of this commit.
    """
    major, minor = cm.parse_minor(ck, token)
    by_version = {p.version: p for p in cm.scan_plans(rctx.root, major, minor)}
    for member in record.get("members") or []:
        plan = by_version.get(str(member.get("version")))
        if plan is not None:
            member["plan_path"] = plan.rel
            member["plan_sha256"] = ck.plan_hash_text(plan.text)
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(record_path, record)


def refreeze_plan(ctx: ck.Context, record: dict, record_path: Path, tree: str, dest: str) -> str:
    """Re-point a one-plan run record at its archived plan: new path, hash, signature, and key."""
    new_rel = dest + ctx.rel[len(tree):] if ctx.rel.startswith(tree + "/") else ctx.rel
    text = (ctx.root / new_rel).read_text(encoding="utf-8")
    record["plan"] = new_rel
    record["plan_sha256"] = ck.plan_hash_text(text)
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    new_path = ck.plan_record_paths(ctx.root, ctx.key_repo, ctx.remote_url, new_rel)[0]
    ck._write_record(new_path, record)
    if record_path.resolve() != new_path.resolve():
        record_path.unlink(missing_ok=True)
    return new_rel


def remove_empty_dirs(root: Path) -> list[str]:
    """Remove every empty directory under docs/releases/, deepest first; return them."""
    base = root / "docs" / "releases"
    removed: list[str] = []
    if not base.is_dir():
        return removed
    for path in sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            removed.append(path.relative_to(root).as_posix())
    return removed


def _authority(record: dict | None, confirmed: bool) -> str:
    """`record` under the record's `archive-minor`; `confirmed` only when there is no record.

    A verified record that lacks `archive-minor` is the user's answer for this minor,
    so `--confirmed` cannot override it (and the re-freeze a record needs would
    otherwise be skipped, leaving it tampered).
    """
    classes = ((record or {}).get("approvals") or {}).get("classes") or []
    if any(isinstance(c, dict) and c.get("class") == "archive-minor" for c in classes):
        return "record"
    if record is not None:
        raise Refused("approval-not-covered", "the minor record does not carry archive-minor")
    if confirmed:
        return "confirmed"
    raise Refused("approval-not-covered", "no archive-minor approval; confirm through docs-layout-refactor")


def _apply_archive(
    rctx: ck.RepoContext, token: str, tree: str, dest: str, files: list[str], checker: Path,
) -> list[Repair]:
    """Move, repair, prove, and commit; on any failure restore the tree and refuse."""

    def moved(rel: str) -> str:
        return dest + rel[len(tree):] if rel == tree or rel.startswith(tree + "/") else rel

    moves = Moves()
    written: list[Repair] = []
    staged = False
    with tempfile.TemporaryDirectory(prefix="minor-close-") as scratch:
        before = Path(scratch) / "before.ndjson"
        after = Path(scratch) / "after.ndjson"
        rename_map = Path(scratch) / "rename-map.tsv"
        if _link_run(checker, "baseline", "--root", str(rctx.root), "--out", str(before))[0] != 0:
            raise Refused("link-check-failed", "baseline before the move")
        try:
            move_tree(rctx, tree, dest, moves)
            rc, listing = _git(rctx, "ls-files", "-z")
            if rc != 0:
                raise Refused("cannot-verify", "tracked files after the move")
            inverse = {moved(rel): rel for rel in files}
            now = [p for p in listing.split("\0") if p]
            repairs = plan_repairs(rctx.root, [(rel, inverse.get(rel, rel), rel) for rel in now], tree, dest)
            for repair in repairs:
                _write_atomic(rctx.root / repair.new_rel, repair.repaired)
                written.append(repair)
            rename_map.write_text(_rename_rows(rctx), encoding="utf-8")
            if _link_run(checker, "baseline", "--root", str(rctx.root), "--out", str(after))[0] != 0:
                raise Refused("link-check-failed", "baseline after the move")
            rc, report = _link_run(checker, "diff", "--before", str(before), "--after", str(after),
                                   "--rename-map", str(rename_map))
            try:
                broken = int(json.loads(report)["totals"]["newly_broken"])
            except (ValueError, KeyError, TypeError):
                raise Refused("link-check-failed", "unreadable report") from None
            if rc != 0 or broken:
                raise Refused("link-check-failed", f"{broken} newly broken")
            if written:
                staged = True
                if _git(rctx, "add", "--", *[r.new_rel for r in written])[0] != 0:
                    raise Refused("commit-failed", "stage repairs")
            if _git(rctx, "commit", "-q", "-m", f"docs(archives): archive closed minor {token}")[0] != 0:
                raise Refused("commit-failed", "git commit")
        except Refused:
            if not _restore(rctx, written, moves, staged):
                raise Refused("rollback-failed", "restore the tree with git mv before anything else") from None
            raise
        except BaseException as exc:
            # Anything else (a PermissionError mid-write, an interrupt) must not leave the
            # tree half moved: restore, then report it as a refusal the caller can act on.
            if not _restore(rctx, written, moves, staged):
                raise Refused("rollback-failed", "restore the tree with git mv before anything else") from exc
            raise Refused("rolled-back", type(exc).__name__) from exc
    return written


def cmd_archive(args: argparse.Namespace) -> int:
    rctx = _context(args)
    token = args.minor
    major, minor = cm.parse_minor(ck, token)
    dest = cm.ARCHIVE_TREE.format(M=major, m=minor)
    closing = args.closing_branch or f"chore/close-{token}"
    plan_ctx: ck.Context | None = None
    if args.plan:
        # A one-plan run archives its minor only as its last plan, on its own record.
        plan_ctx, record = _plan_record(args.plan, args.session)
        record_path = plan_ctx.record_path()
        if "v{}.{}".format(*cm.minor_of(plan_ctx.version)) != token:
            raise Refused("out-of-scope", f"{plan_ctx.version} is not in {token}")
        if not _last_plan(plan_ctx, record):
            raise Refused("not-last-plan", plan_ctx.version)
    else:
        record, record_path = _record(rctx, token, args.session)
    tree = source_tree(rctx, major, minor)
    if tree is None:
        if (rctx.root / dest).is_dir():
            print(f"ALREADY ARCHIVED {token} {dest}")
            return EXIT_OK
        raise Refused("no-tree", token)
    authority = _authority(record, args.confirmed) if args.apply else "dry-run"
    rc, listing = _git(rctx, "ls-files", "-z")
    if rc != 0:
        raise Refused("cannot-verify", "tracked files")
    files = [p for p in listing.split("\0") if p]

    def moved(rel: str) -> str:
        return dest + rel[len(tree):] if rel == tree or rel.startswith(tree + "/") else rel

    preview = plan_repairs(rctx.root, [(rel, rel, moved(rel)) for rel in files], tree, dest)
    refusals = [
        *register_refusals(rctx, token, record, tree),
        *plan_refusals(rctx, token, record),
        *branch_refusals(rctx, token, record, tree, closing, args.integration_branch),
        *tree_refusals(rctx, tree, dest, closing),
        *bound_plan_refusals(rctx, preview, record),
    ]
    checker = link_checker(rctx.root, args.link_checker)
    if checker is None:
        refusals.append(Refused("link-checker-unavailable", "docs-layout-refactor scripts/link-baseline.py"))
    summary = (f"links={sum(r.links for r in preview)} mentions={sum(r.mentions for r in preview)} "
               f"files={len(preview)}")
    if refusals:
        for refusal in refusals:
            print(refusal.line())
        return EXIT_REFUSED
    if not args.apply:
        print(f"WOULD ARCHIVE {token} {tree} -> {dest} {summary}")
        return EXIT_OK
    assert checker is not None
    _apply_archive(rctx, token, tree, dest, files, checker)
    head = rctx._git_out("rev-parse", "--short", "HEAD")
    emptied = remove_empty_dirs(rctx.root)
    if authority == "record" and record is not None and plan_ctx is not None:
        new_rel = refreeze_plan(plan_ctx, record, record_path, tree, dest)
        print(f"RE-POINTED run record -> {new_rel}")
    elif authority == "record" and record is not None:
        refreeze(rctx, record, record_path, token)
    for rel in emptied:
        print(f"REMOVED empty {rel}")
    print(f"ARCHIVED {token} {tree} -> {dest} commit={head} {summary} newly_broken=0")
    return EXIT_OK


# --------------------------------------------------------------------------- status


def cmd_status(args: argparse.Namespace) -> int:
    rctx = _context(args)
    token = args.minor
    cm.parse_minor(ck, token)
    record, _path = _record(rctx, token, None)
    gaps, notices = cm.gaps_minor_status(ck, rctx, token, record)
    print(f"gaps.minor {gaps}")
    print(f"archive.minor {cm.archive_minor_status(ck, rctx, token, record)}")
    for notice in notices:
        print(notice, file=sys.stderr)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    migrate = sub.add_parser("migrate", help="migrate one approved gap to the next minor")
    migrate.add_argument("--minor", required=True)
    migrate.add_argument("--id", required=True, help="the gap, such as v0.5#WN-3")
    migrate.add_argument("--reason", required=True, choices=cm.MIGRATION_REASONS)
    migrate.add_argument("--evidence", required=True)
    migrate.add_argument("--date")
    migrate.add_argument("--session")
    migrate.add_argument("--dry-run", action="store_true")
    migrate.add_argument("--repo", default=".")
    migrate.set_defaults(func=cmd_migrate)
    archive = sub.add_parser("archive", help="archive a closed minor (dry run by default)")
    archive.add_argument("--minor", required=True)
    mode = archive.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    archive.add_argument("--confirmed", action="store_true",
                         help="the user confirmed this archive in the docs-layout-refactor gate (no record)")
    archive.add_argument("--closing-branch")
    archive.add_argument("--integration-branch", default="develop")
    archive.add_argument("--session")
    archive.add_argument("--link-checker")
    archive.add_argument("--plan", help="archive on this one-plan run's record (its last plan only)")
    archive.add_argument("--repo", default=".")
    archive.set_defaults(func=cmd_archive)
    carry = sub.add_parser("carry", help="record a one-plan run's open gaps in the next version")
    carry.add_argument("--plan", required=True)
    carry.add_argument("--id", action="append", help="carry only this gap (repeatable), such as WN-3")
    carry.add_argument("--date")
    carry.add_argument("--session")
    carry.add_argument("--dry-run", action="store_true")
    carry.set_defaults(func=cmd_carry)
    status = sub.add_parser("status", help="print the gaps.minor and archive.minor lines")
    status.add_argument("--minor", required=True)
    status.add_argument("--repo", default=".")
    status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ck.Malformed as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Forced as exc:
        print(str(exc))
        return EXIT_REFUSED
    except Refused as exc:
        print(exc.line())
        return EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
