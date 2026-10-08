#!/usr/bin/env python3
"""Report font sizes in a .pptx or .docx that break the standard-size rule.

Slides (.pptx) must use PowerPoint's standard list with a 12 pt minimum;
documents (.docx) must use Word's standard list without half sizes, with a
10 pt minimum. The lists are owned by the pptx-generation and docx-generation
SKILL.md files; this script only measures them.

Scope: explicit sizes in the package XML. For .pptx that is every run,
paragraph default and end-of-paragraph size on slides and charts. For .docx it
is every run size in the body, headers, footers, footnotes and endnotes, plus
the effective size of each style those parts reference (following basedOn).
Sizes inherited silently from a slide layout or master are not resolved.

Exit codes: 0 clean, 1 at least one violation, 2 usage or file error.
Standard library only (zipfile + ElementTree), so no extra install is needed.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SLIDE_SIZES = (12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 44, 48, 54, 60, 66, 72, 80, 88, 96)
DOCUMENT_SIZES = (10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{" + W_NS + "}"
PPTX_PARTS = re.compile(r"^ppt/(slides/slide|charts/chart)\d+\.xml$")
DOCX_PARTS = re.compile(r"^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
PPTX_TAGS = {"rPr", "defRPr", "endParaRPr"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _pptx_sizes(archive: zipfile.ZipFile) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    for name in sorted(n for n in archive.namelist() if PPTX_PARTS.match(n)):
        for element in ET.fromstring(archive.read(name)).iter():
            size = element.get("sz")
            if size is not None and _local(element.tag) in PPTX_TAGS:
                found.append((f"{name} <{_local(element.tag)}>", int(size) / 100))
    return found


def _style_sizes(archive: zipfile.ZipFile) -> dict[str, float]:
    """Map each style id to its effective size in points, following basedOn."""
    if "word/styles.xml" not in archive.namelist():
        return {}
    root = ET.fromstring(archive.read("word/styles.xml"))
    own: dict[str, float] = {}
    parent: dict[str, str] = {}
    for style in root.iter(W + "style"):
        style_id = style.get(W + "styleId", "")
        size = style.find(f"{W}rPr/{W}sz")
        if size is not None:
            own[style_id] = int(size.get(W + "val", "0")) / 2
        based = style.find(W + "basedOn")
        if based is not None:
            parent[style_id] = based.get(W + "val", "")
    resolved: dict[str, float] = {}
    for style_id in set(own) | set(parent):
        current, seen = style_id, set()
        while current and current not in own and current not in seen:
            seen.add(current)
            current = parent.get(current, "")
        if current in own:
            resolved[style_id] = own[current]
    return resolved


def _docx_sizes(archive: zipfile.ZipFile) -> list[tuple[str, float]]:
    styles = _style_sizes(archive)
    found: list[tuple[str, float]] = []
    used: set[str] = set()
    for name in sorted(n for n in archive.namelist() if DOCX_PARTS.match(n)):
        for element in ET.fromstring(archive.read(name)).iter():
            tag = _local(element.tag)
            if tag == "sz" and element.get(W + "val") is not None:
                found.append((f"{name} <w:sz>", int(element.get(W + "val")) / 2))
            elif tag in {"pStyle", "rStyle"} and element.get(W + "val"):
                used.add(element.get(W + "val"))
    found.extend((f"word/styles.xml style '{s}'", styles[s]) for s in sorted(used) if s in styles)
    return found


def check(path: Path, extra: tuple[float, ...] = ()) -> list[str]:
    """Return one message per violating size; an empty list means clean."""
    suffix = path.suffix.lower()
    if suffix not in {".pptx", ".docx"}:
        raise ValueError(f"unsupported file type {suffix!r}: expected .pptx or .docx")
    allowed = (SLIDE_SIZES if suffix == ".pptx" else DOCUMENT_SIZES) + tuple(extra)
    minimum = SLIDE_SIZES[0] if suffix == ".pptx" else DOCUMENT_SIZES[0]
    with zipfile.ZipFile(path) as archive:
        sizes = _pptx_sizes(archive) if suffix == ".pptx" else _docx_sizes(archive)
    problems = []
    for where, points in sizes:
        if points in allowed:
            continue
        reason = f"below the {minimum} pt minimum" if points < minimum else "not a standard size"
        problems.append(f"{where}: {points:g} pt is {reason}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path, help="generated .pptx or .docx to check")
    parser.add_argument(
        "--allow", type=float, action="append", default=[],
        help="extra size in points the user explicitly asked for (repeatable)",
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        problems = check(args.file, tuple(args.allow))
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} font size violation(s) in {args.file}", file=sys.stderr)
        return 1
    print(f"OK: every font size in {args.file} is standard and at or above the minimum")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
