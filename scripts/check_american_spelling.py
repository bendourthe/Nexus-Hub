#!/usr/bin/env python3
"""Fail when a living tracked file uses British instead of American spelling.

Nexus-Hub writes American English everywhere it is still edited: the catalog,
the instruction templates every platform installs, guides, living docs, code
comments, and tests. Frozen records are left as they were written, because they
are history rather than product text and some of them are hash-pinned evidence:
`docs/archives/`, CI receipts, patch files, and every released CHANGELOG entry
(only the `## [Unreleased]` section is checked).

A word is checked only outside literals. Backtick code spans, URLs, and the HTML
`aria-labelledby` attribute keep their published spelling, and so do words
joined by a hyphen or underscore (kebab-case and snake_case identifiers). A line
carrying the marker `spelling: allow` is skipped for any other literal that must
stay as is.

    python scripts/check_american_spelling.py          # report, exit 1 on findings
    python scripts/check_american_spelling.py --fix    # rewrite living files in place
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Whole words that differ by more than a suffix. Keys are lowercase British forms.
WORDS = {
    "artefact": "artifact", "artefacts": "artifacts",
    "judgement": "judgment", "judgements": "judgments",
    "acknowledgement": "acknowledgment", "acknowledgements": "acknowledgments",
    "licence": "license", "licences": "licenses",
    "defence": "defense", "defences": "defenses",
    "offence": "offense", "offences": "offenses",
    "catalogue": "catalog", "catalogues": "catalogs", "catalogued": "cataloged",
    "cataloguing": "cataloging",
    "analogue": "analog", "analogues": "analogs",
    "programme": "program", "programmes": "programs",
    "centre": "center", "centres": "centers", "centred": "centered",
    "centring": "centering",
    "theatre": "theater", "theatres": "theaters",
    "fibre": "fiber", "fibres": "fibers",
    "metre": "meter", "metres": "meters", "litre": "liter", "litres": "liters",
    "grey": "gray", "greys": "grays", "greyed": "grayed", "greyish": "grayish",
    "fulfil": "fulfill", "fulfils": "fulfills", "fulfilment": "fulfillment",
    "enrol": "enroll", "enrols": "enrolls", "enrolment": "enrollment",
    "practise": "practice", "practised": "practiced", "practises": "practices",
    "practising": "practicing",
    "towards": "toward", "whilst": "while", "amongst": "among",
    "learnt": "learned", "spelt": "spelled",
    "sceptical": "skeptical", "manoeuvre": "maneuver",
    "ageing": "aging", "focussed": "focused", "focussing": "focusing",
}

# -our words: colour -> color, keeping whatever suffix follows.
OUR_STEMS = (
    "colo", "behavio", "favo", "hono", "labo", "neighbo", "flavo", "humo",
    "rumo", "harbo", "armo", "vapo", "endeavo", "savo",
)
OUR_SUFFIXES = (
    "", "s", "ed", "ing", "ful", "less", "al", "ally", "ite", "ites", "able",
    "hood", "hoods", "ings",
)

# Doubled-L inflections: labelled -> labeled. "cancelled" is deliberately absent:
# American dictionaries accept it, and GitHub Actions, VS Code, and this repo's
# extensions publish it as an API value, so rewriting it splits one identifier.
DOUBLE_L = (
    "label", "model", "travel", "signal", "level", "total", "counsel",
    "fuel", "channel", "tunnel", "marshal", "dial", "marvel", "equal", "jewel",
    "trowel", "shovel", "rival", "duel", "pencil", "panel", "funnel",
)
DOUBLE_L_SUFFIXES = ("ed", "ing", "er", "ers", "or", "ors")

# -ise / -yse verbs and their -isation nouns: organise -> organize.
ISE_STEMS = (
    "anonym", "apolog", "author", "capital", "categor", "central", "character",
    "critic", "custom", "digit", "emphas", "external", "final", "general",
    "global", "harmon", "initial", "internal", "item", "legitim", "local",
    "material", "maxim", "memor", "minim", "mobil", "modern", "monet",
    "neutral", "normal", "operational", "optim", "organ", "parallel",
    "parameter", "parenthes", "penal", "personal", "priorit", "random",
    "raster", "rational", "real", "recogn", "serial", "special", "stabil",
    "standard", "summar", "symbol", "synchron", "synthes", "templat", "theor",
    "token", "util", "vapor", "virtual", "visual", "container", "sanit",
    "fertil", "industrial", "commercial", "contextual", "conceptual",
    "familiar", "jeopard", "econom", "scrutin", "sympath", "trivial",
    "vector", "production", "hospital",
)
ISE_SUFFIXES = {
    "ise": "ize", "ised": "ized", "ises": "izes", "ising": "izing",
    "isation": "ization", "isations": "izations", "iser": "izer",
    "isers": "izers", "isable": "izable",
}
ISE_PREFIXES = ("", "re", "de", "un", "non", "pre", "over", "under", "de-", "re-")
YSE_STEMS = ("anal", "paral", "catal", "hydrol", "electrol", "dial")
# "analyses" is also the American plural of "analysis", so it is never flagged.
YSE_SUFFIXES = {"yse": "yze", "ysed": "yzed", "ysing": "yzing", "yser": "yzer", "ysers": "yzers"}


def _build_map() -> dict[str, str]:
    mapping = dict(WORDS)
    for stem in OUR_STEMS:
        for suffix in OUR_SUFFIXES:
            mapping[f"{stem}ur{suffix}"] = f"{stem}r{suffix}"
    for stem in DOUBLE_L:
        for suffix in DOUBLE_L_SUFFIXES:
            mapping[f"{stem}l{suffix}"] = f"{stem}{suffix}"
    for prefix in ISE_PREFIXES:
        for stem in ISE_STEMS:
            for british, american in ISE_SUFFIXES.items():
                mapping[f"{prefix}{stem}{british}"] = f"{prefix}{stem}{american}"
        for stem in YSE_STEMS:
            for british, american in YSE_SUFFIXES.items():
                mapping[f"{prefix}{stem}{british}"] = f"{prefix}{stem}{american}"
    return {k: v for k, v in mapping.items() if k != v}


SPELLINGS = _build_map()

# A coarse superset of every key, built from the word families, used as the
# git grep prefilter. A list of every word form is exact but made git grep take
# minutes; a handful of rare family stems runs in seconds. Plain groups only,
# so the text is valid POSIX ERE.
PREFILTER_PATTERN = "|".join(
    [
        "(" + "|".join(OUR_STEMS) + ")ur",
        "(" + "|".join(DOUBLE_L) + ")l(ed|ing|er|or)",
        "(" + "|".join(ISE_STEMS) + ")is(e|ing|ation|able)",
        "(" + "|".join(YSE_STEMS) + ")ys(e|ing)",
        *sorted(WORDS),
    ]
)
LETTERS = re.compile(r"[a-z]+")
# Every standalone word token; a dict lookup decides. Hyphen and underscore
# neighbors exclude kebab-case and snake_case identifiers, which are literals.
WORD = re.compile(r"(?<![\w-])([A-Za-z]+)(?![\w-])")

# Spans whose spelling is published elsewhere and must not change.
LITERAL = re.compile(
    r"`[^`\n]*`"                       # inline code span
    r"|https?://\S+"                   # URL
    r"|aria-labelledby",               # HTML attribute
    re.IGNORECASE,
)
ALLOW_MARKER = "spelling: allow"

FROZEN_PREFIXES = ("docs/archives/",)
FROZEN_SUFFIXES = (".patch", ".diff", ".lock", ".svg", ".min.js", ".min.css")
# Files whose subject is British spelling: the word list and its test inputs.
SELF = {
    "scripts/check_american_spelling.py",
    "tests/validators/test_check_american_spelling.py",
}
TEXT_SUFFIXES = {
    ".md", ".py", ".js", ".mjs", ".ts", ".json", ".yml", ".yaml", ".toml",
    ".sh", ".ps1", ".css", ".html", ".txt", ".cfg", ".ini", ".mdc",
}


def is_frozen(path: str) -> bool:
    """History and verbatim evidence keep the spelling they were recorded with."""
    if path in SELF or path.startswith(FROZEN_PREFIXES) or path.endswith(FROZEN_SUFFIXES):
        return True
    # CI receipts and their captured "before/after" snapshots are evidence.
    return any("receipts" in part for part in path.split("/"))


def candidates(root: Path) -> list[str]:
    """Tracked text files that might contain a British form (git grep prefilter).

    `fix_line` makes the exact, literal-aware decision on each candidate.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "grep", "-l", "-z", "-I", "-i", "-E", PREFILTER_PATTERN],
        capture_output=True,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    names = result.stdout.decode("utf-8", "replace").split("\0")
    return [n for n in names if n and Path(n).suffix.lower() in TEXT_SUFFIXES and not is_frozen(n)]


def _match_case(british: str, american: str) -> str:
    if british.isupper() and len(british) > 1:
        return american.upper()
    if british[0].isupper():
        return american[0].upper() + american[1:]
    return american


def fix_line(line: str, present: frozenset[str] | None = None) -> tuple[str, list[str]]:
    """Return the line with British forms replaced outside literals, and the forms found.

    `present` is the set of British forms known to occur in the file; a line
    containing none of them is returned untouched without tokenizing it.
    """
    if ALLOW_MARKER in line:
        return line, []
    if present is not None:
        lowered = line.lower()
        if not any(word in lowered for word in present):
            return line, []
    found: list[str] = []
    pieces: list[str] = []
    cursor = 0

    def convert(segment: str) -> str:
        def swap(match: re.Match[str]) -> str:
            word = match.group(1)
            if word.lower() not in SPELLINGS:
                return word
            found.append(word)
            return _match_case(word, SPELLINGS[word.lower()])
        return WORD.sub(swap, segment)

    for literal in LITERAL.finditer(line):
        pieces.append(convert(line[cursor:literal.start()]))
        pieces.append(literal.group(0))
        cursor = literal.end()
    pieces.append(convert(line[cursor:]))
    return "".join(pieces), found


def checked_range(path: str, lines: list[str]) -> range:
    """Only the Unreleased section of the changelog is living text."""
    if path != "CHANGELOG.md":
        return range(len(lines))
    headings = [i for i, line in enumerate(lines) if line.startswith("## [")]
    end = headings[1] if len(headings) > 1 else len(lines)
    return range(end)


def process(root: Path, path: str, fix: bool) -> list[str]:
    file = root / path
    try:
        text = file.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return []  # not UTF-8 text; rewriting it could corrupt it
    present = frozenset(LETTERS.findall(text.lower())) & SPELLINGS.keys()
    if not present:
        return []
    lines = text.splitlines(keepends=True)
    findings: list[str] = []
    for index in checked_range(path, lines):
        new, found = fix_line(lines[index], present)
        for word in found:
            findings.append(f"{path}:{index + 1}: {word} -> {_match_case(word, SPELLINGS[word.lower()])}")
        lines[index] = new
    if fix and findings:
        file.write_bytes("".join(lines).encode("utf-8"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--fix", action="store_true", help="rewrite living files in place")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    findings: list[str] = []
    for path in candidates(root):
        findings.extend(process(root, path, args.fix))

    files = len({f.split(":")[0] for f in findings})
    if args.fix:
        print(f"check_american_spelling: fixed {len(findings)} spelling(s) in {files} file(s).")
        return 0
    for finding in findings:
        print(f"british spelling: {finding}")
    print(f"check_american_spelling: {len(findings)} British spelling(s) in {files} file(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
