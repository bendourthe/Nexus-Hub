#!/usr/bin/env python3
"""Inline the guide's shared fragments into every guide page, from one source.

Repo-internal maintainer tool (v4.13.10). It is listed in ``DEV_ONLY_SCRIPTS`` in
``catalog/hooks/tests/test_installer_smoke.py`` and is deliberately NOT copied by
either installer: it edits files in this repository's ``guides/website/`` tree.

The guide ships as two self-contained offline pages, ``nexus-hub-guide.html`` and
``training.html`` (decision 2026-10-04, guide Training as a second offline page).
Pieces both pages carry live once in ``guides/website/shared/``, described by
``guides/website/shared/fragments.json``. Each page holds every fragment between
a pair of markers whose comment syntax matches where it sits::

    <!-- shared:footer -->            (HTML)
    ...fragment...
    <!-- /shared:footer -->

    /* shared:theme-js */             (CSS and JavaScript)
    ...fragment...
    /* /shared:theme-js */

A page carries every fragment unless its manifest entry lists the ones it holds in
``fragments``. A fragment may hold ``{{name}}`` placeholders, filled from the page's ``vars`` in
the manifest, so one header source can link in-page in one file and across pages
in the other. A fragment with ``wrap`` (two strings) is data, such as a JSON file: it is
placed between the two strings unchanged, without placeholder filling, and may not
contain ``</script``. Markers sit at the start of their line; the fragment text sits
between them unchanged.

Usage::

    python scripts/stamp_guide_shared.py            # rewrite every page from the sources
    python scripts/stamp_guide_shared.py --check    # exit 1 when a page differs from its source
    python scripts/stamp_guide_shared.py --root PATH

Exit codes: 0 clean (or written), 1 drift under ``--check``, 2 the manifest, a
fragment, a placeholder, or a marker is missing, duplicated, or malformed. On exit
2 nothing is written.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

WEB = Path("guides") / "website"
MANIFEST = WEB / "shared" / "fragments.json"
SYNTAX = {"html": ("<!-- ", " -->"), "css": ("/* ", " */"), "js": ("/* ", " */")}
PLACEHOLDER = re.compile(r"\{\{([a-z0-9_.-]+)\}\}")


class StampError(RuntimeError):
    """The manifest, a fragment, a placeholder, or a page marker is unusable."""


@dataclass(frozen=True)
class Fragment:
    name: str
    syntax: str
    text: str
    wrap: tuple[str, str] | None = None

    def markers(self) -> tuple[str, str]:
        left, right = SYNTAX[self.syntax]
        return f"{left}shared:{self.name}{right}", f"{left}/shared:{self.name}{right}"


def _read_lf(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), "\r\n" in raw


def load(root: Path) -> tuple[list[Fragment], dict[str, tuple[dict[str, str], list[Fragment]]]]:
    path = root / MANIFEST
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StampError(f"{MANIFEST.as_posix()}: unreadable manifest ({exc})") from exc
    fragments: list[Fragment] = []
    for name, spec in manifest.get("fragments", {}).items():
        syntax = spec.get("syntax")
        if syntax not in SYNTAX:
            raise StampError(f"fragment {name}: syntax must be one of {sorted(SYNTAX)}")
        src = root / WEB / "shared" / spec.get("file", "")
        if not src.is_file():
            raise StampError(f"fragment {name}: source file {src.relative_to(root).as_posix()} is missing")
        text, _ = _read_lf(src)
        if not text.endswith("\n"):
            text += "\n"
        wrap = spec.get("wrap")
        if wrap is not None:
            if not (isinstance(wrap, list) and len(wrap) == 2 and all(isinstance(w, str) for w in wrap)):
                raise StampError(f"fragment {name}: wrap must be a list of two strings")
            # Either sequence ends a script block early: '</script' directly, and '<!--' by
            # putting the parser in a state where the block's own closing tag is skipped.
            for marker in ("</script", "<!--"):
                if marker in text.lower():
                    raise StampError(f"fragment {name}: wrapped data may not contain '{marker}'")
            wrap = (wrap[0], wrap[1])
        fragments.append(Fragment(name, syntax, text, wrap))
    by_name = {fragment.name: fragment for fragment in fragments}
    pages: dict[str, tuple[dict[str, str], list[Fragment]]] = {}
    for page, spec in manifest.get("pages", {}).items():
        names = spec.get("fragments", list(by_name))
        unknown = [name for name in names if name not in by_name]
        if unknown:
            raise StampError(f"page {page}: unknown fragment(s) {', '.join(unknown)}")
        pages[page] = (dict(spec.get("vars", {})), [by_name[name] for name in names])
    if not fragments or not pages:
        raise StampError(f"{MANIFEST.as_posix()}: needs at least one fragment and one page")
    return fragments, pages


def render(fragment: Fragment, page: str, values: dict[str, str]) -> str:
    if fragment.wrap is not None:
        # Wrapped fragments carry data (for example JSON): no placeholder filling.
        return fragment.wrap[0] + fragment.text + fragment.wrap[1]

    def fill(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise StampError(f"{page}: fragment {fragment.name} needs a value for {{{{{key}}}}}")
        return values[key]

    return PLACEHOLDER.sub(fill, fragment.text)


def _region(text: str, page: str, fragment: Fragment) -> tuple[int, int]:
    """Return the span of the fragment body (between the two marker lines)."""
    open_m, close_m = fragment.markers()
    opens = [m.start() for m in re.finditer(r"(?m)^" + re.escape(open_m) + r"\n", text)]
    closes = [m.start() for m in re.finditer(r"(?m)^" + re.escape(close_m) + r"$", text)]
    if not opens or not closes:
        raise StampError(f"{page}: marker pair for {fragment.name} is missing ({open_m} ... {close_m})")
    if len(opens) > 1 or len(closes) > 1:
        raise StampError(f"{page}: marker pair for {fragment.name} appears more than once")
    start, end = opens[0] + len(open_m) + 1, closes[0]
    if end < start:
        raise StampError(f"{page}: closing marker for {fragment.name} comes before its opening marker")
    return start, end


def stamp(root: Path, check: bool) -> int:
    fragments, pages = load(root)
    outputs: dict[Path, tuple[str, bool]] = {}
    drift: list[str] = []
    for page, (values, page_fragments) in pages.items():
        path = root / WEB / page
        if not path.is_file():
            raise StampError(f"page {page} is missing from {WEB.as_posix()}")
        text, crlf = _read_lf(path)
        # Validate every marker before changing anything, so a bad page writes nothing.
        spans = sorted(((_region(text, page, f), f) for f in page_fragments), key=lambda item: item[0][0])
        for (prev, _), (nxt, _) in pairwise(spans):
            if nxt[0] < prev[1]:
                raise StampError(f"{page}: two shared regions overlap")
        out, cursor = [], 0
        for (start, end), fragment in spans:
            body = render(fragment, page, values)
            if text[start:end] != body:
                drift.append(f"{page}: {fragment.name}")
            out.append(text[cursor:start])
            out.append(body)
            cursor = end
        out.append(text[cursor:])
        outputs[path] = ("".join(out), crlf)
    if check:
        for line in drift:
            print(f"stamp_guide_shared: drift -- {line} differs from guides/website/shared", file=sys.stderr)
        if drift:
            return 1
        print(f"stamp_guide_shared: OK -- {len(fragments)} fragment(s) match in {len(pages)} page(s)")
        return 0
    for path, (text, crlf) in outputs.items():
        path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    print(f"stamp_guide_shared: stamped {len(fragments)} fragment(s) into {len(pages)} page(s); {len(drift)} region(s) changed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when a page differs from its source")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    try:
        return stamp(args.root.resolve(), args.check)
    except StampError as exc:
        print(f"stamp_guide_shared: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
