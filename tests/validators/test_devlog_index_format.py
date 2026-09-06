"""Conformance gate for the docs/DEVLOG.md per-release index (v3.18.0).

Phase 1 converted DEVLOG from a 5,615-line narrative log into a 99-line index.
Phase 2 rewrote every writer to produce the index format. Neither of those stops a
future agent from writing a paragraph into a table cell, because the format is
carried by prose instructions and prose instructions are advisory.

This is the mechanical half. It asserts the properties that make the index useful
and bounded: one line per release, no narrative, every link resolving, and no
release silently missing its line.

The line ceiling is deliberately a HARD assertion rather than a warning. A soft
ceiling on an append-only file is how the previous 5,615 lines happened.

Run from the repo root:
    python -m pytest tests/validators/test_devlog_index_format.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_DEVLOG = _REPO / "docs" / "DEVLOG.md"
_CHANGELOG = _REPO / "CHANGELOG.md"

# The gate from the v3.18.0 plan's Phase 1 stability criterion. Raising this needs
# the same justification a doc-budget ratchet needs: the index grows one line per
# release, so a breach means a cell grew, not that the project shipped too much.
_MAX_LINES = 150

# A summary is one sentence. This bounds it without trying to parse English; the
# longest legitimate summary in the converted index is well under this.
_MAX_SUMMARY_CHARS = 200

_ROW = re.compile(r"^\|\s*(?P<date>[^|]+?)\s*\|\s*(?P<version>v[^|]+?)\s*\|(?P<rest>.*)\|\s*$")


@pytest.fixture(scope="module")
def devlog_text() -> str:
    assert _DEVLOG.is_file(), f"{_DEVLOG} is missing"
    return _DEVLOG.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rows(devlog_text: str) -> list[re.Match]:
    matches = []
    for line in devlog_text.splitlines():
        if not line.startswith("|") or set(line) <= set("|- "):
            continue  # separator row
        m = _ROW.match(line)
        if m and m.group("version").lower().startswith("v"):
            matches.append(m)
    assert matches, "the index has no release rows"
    return matches


def test_index_stays_under_the_line_ceiling(devlog_text: str) -> None:
    count = len(devlog_text.splitlines())
    assert count <= _MAX_LINES, (
        f"docs/DEVLOG.md is {count} lines, over the {_MAX_LINES}-line ceiling. "
        "The index grows one line per release, so this is a cell that grew into "
        "prose, not a project that shipped too much."
    )


def test_no_narrative_headings_remain(devlog_text: str) -> None:
    """`## [date] - title` is the narrative-log shape the conversion removed."""
    offenders = [
        line for line in devlog_text.splitlines() if line.startswith("## [")
    ]
    assert not offenders, (
        "docs/DEVLOG.md has regrown narrative entry headings: "
        f"{offenders[:3]}. Narrative belongs in docs/v*/*/development/history/."
    )


def test_exactly_one_h1(devlog_text: str) -> None:
    h1s = [line for line in devlog_text.splitlines() if line.startswith("# ")]
    assert len(h1s) == 1, f"expected one H1, found {h1s}"


def test_no_details_blocks(devlog_text: str) -> None:
    """Collapsible blocks were a narrative-entry feature; an index has no use for one."""
    assert "<details" not in devlog_text, "an index row cannot contain a details block"


def test_each_version_appears_at_most_once(rows: list[re.Match]) -> None:
    """A duplicate line means a reader cannot tell which one is current."""
    seen: dict[str, int] = {}
    for m in rows:
        version = m.group("version").strip()
        seen[version] = seen.get(version, 0) + 1
    duplicates = {v: n for v, n in seen.items() if n > 1}
    assert not duplicates, f"duplicate index lines: {duplicates}"


def test_dates_are_iso(rows: list[re.Match]) -> None:
    """A time component or a locale format breaks sorting and diffing."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}( to \d{4}-\d{2}-\d{2})?$")
    bad = [m.group("date").strip() for m in rows if not pattern.match(m.group("date").strip())]
    assert not bad, f"non-ISO dates in the index: {bad}"


def test_summaries_stay_one_sentence_long(rows: list[re.Match]) -> None:
    over = []
    for m in rows:
        cells = [c.strip() for c in m.group("rest").split("|")]
        if not cells:
            continue
        summary = cells[0]
        if len(summary) > _MAX_SUMMARY_CHARS:
            over.append((m.group("version").strip(), len(summary)))
    assert not over, (
        f"summary cells over {_MAX_SUMMARY_CHARS} chars: {over}. "
        "The summary is a pointer, not a restatement of the changelog."
    )


def test_every_link_resolves(devlog_text: str) -> None:
    """Links are relative to docs/DEVLOG.md, so resolve them against docs/."""
    broken = []
    for target in set(re.findall(r"\]\(([^)]+)\)", devlog_text)):
        if target.startswith(("http://", "https://", "#")):
            continue
        path = (_REPO / "docs" / target.split("#", 1)[0]).resolve()
        if not path.exists():
            broken.append(target)
    assert not broken, f"broken links in the index: {sorted(broken)}"


def test_no_root_relative_links(devlog_text: str) -> None:
    """A leading slash does not resolve to the repo root on GitHub."""
    bad = [t for t in re.findall(r"\]\(([^)]+)\)", devlog_text) if t.startswith("/")]
    assert not bad, f"root-relative links do not resolve on the forge: {bad}"


def test_every_released_version_is_indexed(rows: list[re.Match]) -> None:
    """Catches a release that shipped without gaining its index line.

    Scoped to the current major, because earlier majors predate the per-version
    docs layout and are deliberately collapsed into one row per minor.
    """
    changelog = _CHANGELOG.read_text(encoding="utf-8")
    released = set(re.findall(r"^## \[(3\.\d+\.\d+)\]", changelog, re.M))
    indexed = {m.group("version").strip().lstrip("v") for m in rows}
    missing = sorted(released - indexed)
    assert not missing, (
        f"released but not in the DEVLOG index: {missing}. "
        "/update release adds the line at devlog scope."
    )
