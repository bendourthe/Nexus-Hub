#!/usr/bin/env python3
"""Build the fingerprint set of every file Nexus-Hub wrote into its obsolete layouts.

Repo-internal (listed in DEV_ONLY_SCRIPTS; no installer copy step). v4.14.7
Phase 6. Two home-folder layouts are no longer written by any installer:

- ``~/.agent`` (Antigravity 1.0): ``skills/`` as a verbatim copy of
  ``catalog/skills/`` and ``workflows/`` as a verbatim copy of
  ``catalog/commands/``, written by the installers up to ``20a73607d^``.
- ``~/.opencode`` (OpenCode's global folder from ``d721dd173`` to
  ``9b30ad29e^``): a rendered ``AGENTS.md``, verbatim ``commands/`` and
  ``rules/``, ``skills/`` in the category layout and, from ``1e95d4e88``, the
  flattened layout plus one generated command-skill per command.

For every historical blob of those catalog sources in each range, the builder
records the sha256 of the file as installed (LF and CRLF forms) under its
installed relative path. Generated command-skills are reproduced with the
range's own generator, extracted from ``9b30ad29e^``. Rendered instruction
files are listed by name; the legacy classifier recognizes them line by line
against ``legacy_fingerprints.json``. The output is
``scripts/lib/installer/legacy_layout_fingerprints.json``; the spike that
justified it is ``docs/releases/v4/v4.14/development/v4.14.7-legacy-layout-spike.md``.

    python scripts/build_legacy_layout_fingerprints.py            # regenerate
    python scripts/build_legacy_layout_fingerprints.py --check    # fail when stale
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[0] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()

REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "scripts" / "lib" / "installer" / "legacy_layout_fingerprints.json"
SCHEMA = 1
MAX_BYTES = 2 * 1024 * 1024
GENERATOR_REV = "9b30ad29e^"
GENERATOR_FILE = "scripts/lib/integrations/_catalog_adapters.py"
FLATTEN_REV = "1e95d4e88"

# (source prefix, installed prefix, mode). Modes: verbatim, flatten, command-skill.
LAYOUTS = {
    "agent": {
        "root": ".agent",
        "start": None,
        "end": "20a73607d^",
        "maps": (("catalog/skills/", "skills/", "verbatim"), ("catalog/commands/", "workflows/", "verbatim")),
        "rendered": (),
    },
    "opencode": {
        "root": ".opencode",
        "start": "d721dd173",
        "end": "9b30ad29e^",
        "maps": (
            ("catalog/skills/", "skills/", "verbatim"),
            ("catalog/skills/", "skills/", "flatten"),
            ("catalog/commands/", "commands/", "verbatim"),
            ("catalog/rules/", "rules/", "verbatim"),
            ("catalog/commands/", "skills/", "command-skill"),
        ),
        "rendered": ("AGENTS.md",),
    },
}


class BuildError(Exception):
    """Generation must fail loudly rather than emit a partial set."""


def _git(*args: str) -> str:
    proc = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise BuildError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def _pairs(start: str | None, end: str, prefixes: tuple[str, ...]) -> set[tuple[str, str]]:
    """Every (path, blob id) that existed under ``prefixes`` in the range."""
    found: set[tuple[str, str]] = set()
    if start:
        for line in _git("ls-tree", "-r", start, "--", *prefixes).splitlines():
            meta, _, path = line.partition("\t")
            found.add((path, meta.split()[2]))
        span = f"{start}..{end}"
    else:
        span = end
    for line in _git("log", "--raw", "--no-renames", "--format=", span, "--", *prefixes).splitlines():
        meta, _, path = line.partition("\t")
        fields = meta.split()
        if len(fields) >= 5 and fields[4] != "D":
            found.add((path, fields[3]))
    return found


def _blobs(ids: set[str]) -> dict[str, bytes]:
    """Read many blobs through one ``git cat-file --batch``."""
    order = sorted(ids)
    proc = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch"],
                          input="".join(f"{i}\n" for i in order).encode("ascii"),
                          capture_output=True, check=False)
    if proc.returncode != 0:
        raise BuildError("git cat-file --batch failed")
    out, blobs, offset = proc.stdout, {}, 0
    for blob in order:
        header_end = out.index(b"\n", offset)
        header = out[offset:header_end].decode("ascii", "replace").split()
        if len(header) < 3 or header[1] != "blob":
            raise BuildError(f"unreadable blob {blob}")
        size = int(header[2])
        blobs[blob] = out[header_end + 1: header_end + 1 + size]
        offset = header_end + 1 + size + 1
    return blobs


def _generator():
    """The range's own command-skill generator, run in isolation."""
    tree = ast.parse(_git("show", f"{GENERATOR_REV}:{GENERATOR_FILE}"))
    wanted = {"_split_frontmatter", "_yaml_double_quote", "_synthesize_skill"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    if {n.name for n in nodes} != wanted:
        raise BuildError("generator functions not found at " + GENERATOR_REV)
    namespace: dict = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), GENERATOR_FILE, "exec"), namespace)  # noqa: S102
    return namespace["_synthesize_skill"]


def _forms(content: bytes) -> set[str]:
    """sha256 of the content as committed and with CRLF line endings."""
    forms = {content}
    if b"\0" not in content:
        lf = content.replace(b"\r\n", b"\n")
        forms |= {lf, lf.replace(b"\n", b"\r\n")}
    return {hashlib.sha256(f).hexdigest() for f in forms}


def _installed(path: str, src: str, dst: str, mode: str) -> str | None:
    rest = path[len(src):]
    if mode == "verbatim":
        return dst + rest
    if mode == "flatten":
        parts = rest.split("/")
        return dst + "/".join(parts[1:]) if len(parts) >= 3 else None
    if mode == "command-skill":
        return f"{dst}{rest[:-3]}/SKILL.md" if rest.endswith(".md") and "/" not in rest else None
    raise BuildError(f"unknown mode {mode}")


def build() -> dict:
    synthesize = _generator()
    layouts: dict = {}
    for name, spec in LAYOUTS.items():
        prefixes = tuple(sorted({src for src, _, _ in spec["maps"]}))
        pairs = _pairs(spec["start"], spec["end"], prefixes)
        if not pairs:
            raise BuildError(f"no history found for layout {name}")
        blobs = _blobs({blob for _, blob in pairs})
        files: dict[str, set[str]] = {}
        for path, blob in pairs:
            content = blobs[blob]
            for src, dst, mode in spec["maps"]:
                if not path.startswith(src):
                    continue
                target = _installed(path, src, dst, mode)
                if target is None:
                    continue
                if mode == "command-skill":
                    text = content.decode("utf-8", "replace")
                    for variant in {text.replace("\r\n", "\n"), text.replace("\r\n", "\n").replace("\n", "\r\n")}:
                        files.setdefault(target, set()).update(_forms(synthesize(Path(target).parent.name, variant)))
                else:
                    files.setdefault(target, set()).update(_forms(content))
        layouts[name] = {
            "root": spec["root"],
            "rendered": list(spec["rendered"]),
            "files": {path: sorted(hashes) for path, hashes in sorted(files.items())},
        }
    return {
        "schema": SCHEMA,
        "_comment": "Generated by scripts/build_legacy_layout_fingerprints.py; do not edit.",
        "layouts": layouts,
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
        print(f"build_legacy_layout_fingerprints: {exc}", file=sys.stderr)
        return 2
    content = _serialize(doc)
    size = len(content.encode("utf-8"))
    counts = ", ".join(f"{k}: {len(v['files'])} paths" for k, v in doc["layouts"].items())
    if size > MAX_BYTES:
        print(f"build_legacy_layout_fingerprints: {size} bytes exceeds the {MAX_BYTES}-byte bound", file=sys.stderr)
        return 2
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != content:
            print("legacy layout fingerprints are stale; run: python scripts/build_legacy_layout_fingerprints.py",
                  file=sys.stderr)
            return 1
        print(f"legacy layout fingerprints current ({counts}; {size} bytes)")
        return 0
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp, OUTPUT)
    print(f"wrote {OUTPUT.relative_to(REPO)} ({counts}; {size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
