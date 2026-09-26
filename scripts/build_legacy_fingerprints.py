#!/usr/bin/env python3
"""Build the fingerprint set of every instruction line Nexus-Hub has ever shipped.

Repo-internal (listed in DEV_ONLY_SCRIPTS; no installer copy step). Walks every
git revision of `templates/ai-instructions/*.md` and `data/SKILL_INDEX.md`, plus
every historical source of default template values (`scripts/installer.sh` sed
rules, `scripts/installer.ps1` `.Replace` calls, and `_DEFAULT_TEMPLATE_VARS` in
`scripts/lib/integrations/base.py`), and writes the sorted SHA-256 set of the
normalized lines to `scripts/lib/installer/legacy_fingerprints.json`.

A template line is recorded literally (placeholders left as `{{KEY}}`, which is how
an unrendered placeholder appears in an installed file) and once per historical
default value of each placeholder it contains. Normalization strips trailing
whitespace; blank lines are dropped. The set lets
`scripts/lib/installer/legacy_instruction_block.py` recognize leftovers of an old
install without git on the user's machine. A match is not proof of authorship.

    python scripts/build_legacy_fingerprints.py            # regenerate the file
    python scripts/build_legacy_fingerprints.py --check    # fail when it has drifted
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "scripts" / "lib" / "installer" / "legacy_fingerprints.json"
SCHEMA = 1
LINE_SOURCES = ("templates/ai-instructions", "data/SKILL_INDEX.md")
DEFAULT_SOURCES = ("scripts/installer.sh", "scripts/installer.ps1", "scripts/lib/integrations/base.py")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
DEFAULT_PATTERNS = (
    re.compile(r"s\|\{\{([A-Z_]+)\}\}\|([^|\n]*)\|g"),
    re.compile(r'\.Replace\("\{\{([A-Z_]+)\}\}",\s*"([^"\n]*)"\)'),
    re.compile(r'^\s*"([A-Z_]+)":\s*"([^"\n]*)",?\s*$', re.MULTILINE),
)
MAX_VARIANTS_PER_LINE = 64


class BuildError(Exception):
    """Generation must fail loudly rather than emit a partial set."""


def _git(*args: str) -> str:
    proc = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise BuildError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def _revisions(paths: tuple[str, ...]) -> list[tuple[str, str]]:
    """Every (commit, path) pair where a matching file existed, oldest first."""
    pairs: list[tuple[str, str]] = []
    log = _git("log", "--reverse", "--format=%H", "--name-only", "--diff-filter=AMR", "--", *paths)
    commit = ""
    for line in log.splitlines():
        if re.fullmatch(r"[0-9a-f]{40}", line):
            commit = line
        elif line.strip() and commit and (line.endswith(".md") or line in DEFAULT_SOURCES):
            pairs.append((commit, line))
    return pairs


def _read_blobs(pairs: list[tuple[str, str]]) -> dict[tuple[str, str], str]:
    """Read many `commit:path` blobs through one `git cat-file --batch`."""
    if not pairs:
        return {}
    request = "".join(f"{c}:{p}\n" for c, p in pairs).encode("utf-8")
    proc = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch"], input=request, capture_output=True,
                          check=False)
    if proc.returncode != 0:
        raise BuildError("git cat-file --batch failed")
    out, blobs, offset = proc.stdout, {}, 0
    for pair in pairs:
        header_end = out.index(b"\n", offset)
        header = out[offset:header_end].decode("utf-8", "replace")
        if header.endswith("missing"):
            offset = header_end + 1
            continue
        size = int(header.split()[2])
        body = out[header_end + 1:header_end + 1 + size]
        offset = header_end + 1 + size + 1
        try:
            blobs[pair] = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BuildError(f"non-UTF-8 revision {pair[0][:10]}:{pair[1]}") from exc
    return blobs


def _defaults(blobs: dict[tuple[str, str], str]) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    for (_, path), text in blobs.items():
        if path not in DEFAULT_SOURCES:
            continue
        for pattern in DEFAULT_PATTERNS:
            for key, value in pattern.findall(text):
                if key != "SKILL_INDEX" and "\\n" not in value:
                    values.setdefault(key, set()).add(value.replace("\\|", "|"))
    return values


def _variants(line: str, defaults: dict[str, set[str]]) -> set[str]:
    keys = sorted(set(PLACEHOLDER.findall(line)))
    found = {line}
    options = [[f"{{{{{k}}}}}", *sorted(defaults.get(k, ()))] for k in keys]
    for combo in itertools.islice(itertools.product(*options), MAX_VARIANTS_PER_LINE):
        rendered = line
        for key, value in zip(keys, combo):
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        found.add(rendered)
    return found


def normalize(line: str) -> str:
    return line.rstrip()


def digest(line: str) -> str:
    return hashlib.sha256(normalize(line).encode("utf-8")).hexdigest()


def build() -> dict:
    line_pairs = _revisions(LINE_SOURCES)
    default_pairs = _revisions(DEFAULT_SOURCES)
    blobs = _read_blobs(line_pairs + default_pairs)
    defaults = _defaults(blobs)
    hashes: set[str] = set()
    for (_, path), text in blobs.items():
        if path in DEFAULT_SOURCES:
            continue
        for raw in text.splitlines():
            if not raw.strip():
                continue
            for variant in _variants(raw, defaults) if "{{" in raw else {raw}:
                if normalize(variant):
                    hashes.add(digest(variant))
    if not hashes:
        raise BuildError("no lines found; refusing to write an empty set")
    # Only the line sources: an installer or base.py edit that changes no default
    # value leaves the hash set identical and must not fail --check.
    newest = _git("log", "-1", "--format=%H", "--", *LINE_SOURCES).strip()
    return {
        "_comment": "Generated by scripts/build_legacy_fingerprints.py; do not edit. SHA-256 of every "
                    "normalized (right-stripped, non-blank) line Nexus-Hub shipped in an instruction "
                    "template or skill index, including rendered default placeholder values. A match is "
                    "not proof of authorship.",
        "schema": SCHEMA,
        "newest_revision": newest,
        "count": len(hashes),
        "hashes": sorted(hashes),
    }


def _serialize(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when the committed file has drifted")
    args = parser.parse_args(argv)
    try:
        doc = build()
    except BuildError as exc:
        print(f"build_legacy_fingerprints: {exc}", file=sys.stderr)
        return 2
    content = _serialize(doc)
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != content:
            print("legacy fingerprints are stale; run: python scripts/build_legacy_fingerprints.py",
                  file=sys.stderr)
            return 1
        print(f"legacy fingerprints current ({doc['count']} lines)")
        return 0
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp, OUTPUT)
    print(f"wrote {OUTPUT.relative_to(REPO)} ({doc['count']} lines, newest {doc['newest_revision'][:10]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
