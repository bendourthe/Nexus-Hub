#!/usr/bin/env python3
"""Fail the build if the context compressor grows a network call.

Nexus-Hub's compressor is a local, zero-outbound engine. This guard scans
``extensions/nexus-context-compressor/`` (production sources, not tests) for
network primitives and exits non-zero when any appear outside an explicit
allowlist. It is repo-internal maintainer tooling: no ``.ps1`` sibling, no
installer copy step. Listed in ``DEV_ONLY_SCRIPTS``.

Detected primitives (the set the plan named, plus close cousins):

- imports of ``requests``, ``httpx``, ``aiohttp``, ``socket``, ``http.client``,
  ``urllib.request``
- ``subprocess`` invocations of ``curl`` / ``wget``
- ``os.system`` / ``os.popen`` strings that launch ``curl`` / ``wget``

Usage:

    python scripts/check_no_outbound.py
    python scripts/check_no_outbound.py --root DIR

Exit codes:
    0 - the scanned tree is clean
    1 - one or more network primitives were found
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

DEFAULT_REL = "extensions/nexus-context-compressor"
SKIP_DIR_NAMES = frozenset({"tests", "__pycache__", ".venv", "node_modules"})
NETWORK_MODULES = frozenset(
    {
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "http.client",
        "urllib.request",
    }
)
SUBPROCESS_NAMES = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
CURL_WGET = frozenset({"curl", "wget"})

# Opt-in modules that may talk to the network. Empty today: the compressor
# must stay local. A future opt-in module is added here by path relative to
# the compressor root, never by commenting out a finding.
ALLOWLIST: frozenset[str] = frozenset()


def _is_network_module(name: str) -> bool:
    if name in NETWORK_MODULES:
        return True
    return any(name.startswith(mod + ".") for mod in NETWORK_MODULES)


def _string_tokens(node: ast.AST) -> list[str]:
    found: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            found.append(child.value)
    return found


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def scan_source(path: Path, source: str) -> list[str]:
    """Return finding strings for one file. Empty means clean."""
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{path.as_posix()}: syntax error: {exc}"]

    findings: list[str] = []

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)
        loc = f"{path.as_posix()}:{lineno}"
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_network_module(alias.name):
                    findings.append(f"{loc}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_network_module(module):
                findings.append(f"{loc}: from {module} import ...")
            for alias in node.names:
                combined = f"{module}.{alias.name}" if module else alias.name
                if _is_network_module(combined):
                    findings.append(f"{loc}: from {module} import {alias.name}")
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            tokens = _string_tokens(node)
            first = tokens[0].split()[0] if tokens and tokens[0].split() else ""
            is_subproc = name.startswith("subprocess.") or name.split(".")[-1] in SUBPROCESS_NAMES
            uses_curl = first in CURL_WGET or any(
                tok.split()[0] in CURL_WGET for tok in tokens if tok.split()
            )
            if is_subproc and uses_curl:
                findings.append(f"{loc}: subprocess invocation of curl/wget")
            if name in {"os.system", "os.popen"} and first in CURL_WGET:
                findings.append(f"{loc}: {name}({first})")

    return findings


def iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def scan_tree(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"MISS {root.as_posix()}: compressor root is not a directory"]
    files = iter_python_files(root)
    if not files:
        return [f"MISS {root.as_posix()}: no Python files to scan"]
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8")
        findings.extend(scan_source(path, text))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Compressor tree to scan (default: <repo>/extensions/nexus-context-compressor).",
    )
    args = parser.parse_args(argv)

    if args.root is None:
        repo = Path(__file__).resolve().parent.parent
        root = repo / DEFAULT_REL
    else:
        root = args.root.resolve()

    try:
        findings = scan_tree(root)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if findings:
        print(
            f"check_no_outbound: {len(findings)} network primitive(s) in {root.as_posix()}:",
            file=sys.stderr,
        )
        for item in findings:
            print(f"  {item}", file=sys.stderr)
        return 1

    print(f"check_no_outbound: OK ({root.as_posix()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
