#!/usr/bin/env python3
"""Scan dependency manifests and installer scripts for supply-chain IOCs.

Heuristics:
    - curl/wget piped into a shell interpreter ("curl ... | bash").
    - npm / pip postinstall or preinstall lifecycle scripts that shell out.
    - Direct git+https / git+ssh dependency URLs in package manifests.
    - Known typosquat candidates against a small high-value allowlist.
    - GitHub Action references pinned to a moving ref (@main, @master, @latest).

Local-only, read-only, zero outbound calls.

Exit codes:
    0 - no findings
    1 - one or more IOC findings
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_TARGETS: tuple[str, ...] = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "scripts",
    "extensions",
    ".github/workflows",
    "infrastructure",
)

EXEMPT_DIR_PARTS: frozenset[str] = frozenset({
    "archive",
    # v4.0.0 renamed the frozen container to the plural form; both spellings
    # are listed so the exemption survives the rename and still applies to a
    # consuming repo on the legacy singular tree.
    "archives",
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "site-packages",
    "dist",
    "build",
})

LEGIT_PACKAGES: frozenset[str] = frozenset({
    # python
    "requests", "urllib3", "pydantic", "pytest", "ruff", "mypy",
    "fastapi", "starlette", "uvicorn", "httpx", "aiohttp",
    "pyyaml", "tomli", "tomllib", "pathspec", "watchdog",
    "tree-sitter", "tree-sitter-python", "tree-sitter-typescript",
    "python-docx", "python-pptx", "openpyxl", "matplotlib",
    "numpy", "pandas", "scipy", "scikit-learn",
    "anthropic", "openai", "mcp", "claude-agent-sdk",
    # node / web
    "react", "react-dom", "next", "express", "vite",
    "typescript", "eslint", "prettier", "vitest", "jest",
    "playwright", "cypress", "tailwindcss", "lodash",
    "@anthropic-ai/sdk", "@types/node", "@types/react",
})

TYPOSQUAT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^requestz$"), "typosquat of 'requests'"),
    (re.compile(r"^urlib3$"), "typosquat of 'urllib3'"),
    (re.compile(r"^pyjson$"), "typosquat of stdlib 'json'"),
    (re.compile(r"^python-sqlite$"), "typosquat (sqlite3 is stdlib)"),
    (re.compile(r"^crossenv$"), "known malicious typosquat of 'cross-env'"),
    (re.compile(r"^node-fabric$"), "known malicious typosquat"),
    (re.compile(r"^colorss$"), "typosquat of 'colors'"),
    (re.compile(r"^ua-parser-js-?\d"), "potential typosquat of 'ua-parser-js'"),
    (re.compile(r"^lodahs$"), "typosquat of 'lodash'"),
    (re.compile(r"^expresss$"), "typosquat of 'express'"),
]

CURL_PIPE_SHELL_RE = re.compile(
    r"(?:^|[;&|`$(\s])(?:curl|wget)\s+[A-Za-z0-9_./?:&=%@\-\s]+?"
    r"\|\s*(?:bash|sh|zsh|ksh|python)(?:\s|$)",
    re.IGNORECASE | re.MULTILINE,
)

GIT_DEP_RE = re.compile(r"(git\+https?://|git\+ssh://)[^\s'\"\)\]]+")

GH_ACTION_FLOATING_RE = re.compile(
    r"uses:\s*([A-Za-z0-9._\-]+/[A-Za-z0-9._\-/]+)@(main|master|latest|HEAD)\b"
)

NPM_LIFECYCLE_KEYS = ("preinstall", "postinstall", "install")
NPM_LIFECYCLE_SHELL_RE = re.compile(
    r"(curl|wget|powershell|cmd\s*/c|bash\s+-c|sh\s+-c|eval\s+|node\s+-e)",
    re.IGNORECASE,
)

TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh",
    ".ps1", ".js", ".ts", ".cfg", ".ini",
})


def in_exempt_dir(path: Path) -> bool:
    return any(part in EXEMPT_DIR_PARTS for part in path.parts)


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name == "Pipfile"


def iter_target_files(root: Path, targets: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        full = root / target
        if not full.exists():
            continue
        if full.is_file():
            if is_text_file(full) and not in_exempt_dir(full):
                files.append(full)
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIR_PARTS]
            for name in filenames:
                candidate = Path(dirpath) / name
                if not is_text_file(candidate):
                    continue
                if in_exempt_dir(candidate):
                    continue
                files.append(candidate)
    return files


def scan_curl_pipe(text: str) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in CURL_PIPE_SHELL_RE.finditer(line):
            findings.append(
                (line_no, m.start() + 1, f"curl/wget piped to shell: {m.group(0)!r}")
            )
    return findings


def scan_git_deps(text: str) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in GIT_DEP_RE.finditer(line):
            findings.append(
                (line_no, m.start() + 1, f"direct git dependency: {m.group(0)!r}")
            )
    return findings


def scan_typosquats(text: str) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    candidate_re = re.compile(
        r"['\"]?([A-Za-z][A-Za-z0-9._\-]{1,40})['\"]?\s*(?:[:=>~^=]|==)\s*"
    )
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in candidate_re.finditer(line):
            name = m.group(1).lower()
            if name in LEGIT_PACKAGES:
                continue
            for pat, reason in TYPOSQUAT_PATTERNS:
                if pat.match(name):
                    findings.append((line_no, m.start() + 1, f"{name}: {reason}"))
                    break
    return findings


def scan_npm_lifecycle(path: Path) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    if path.name != "package.json":
        return findings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return findings
    scripts = data.get("scripts") or {}
    if not isinstance(scripts, dict):
        return findings
    for key in NPM_LIFECYCLE_KEYS:
        value = scripts.get(key)
        if not isinstance(value, str):
            continue
        if NPM_LIFECYCLE_SHELL_RE.search(value):
            findings.append(
                (0, 0, f"npm '{key}' lifecycle shells out: {value!r}")
            )
    return findings


def scan_floating_actions(text: str) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in GH_ACTION_FLOATING_RE.finditer(line):
            findings.append(
                (line_no, m.start() + 1,
                 f"GitHub Action pinned to moving ref: {m.group(1)}@{m.group(2)}")
            )
    return findings


def scan_file(path: Path) -> list[tuple[int, int, str]]:
    findings: list[tuple[int, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    findings.extend(scan_curl_pipe(text))
    findings.extend(scan_git_deps(text))
    if path.name in {"package.json", "pyproject.toml", "requirements.txt",
                     "requirements-dev.txt", "Pipfile"}:
        findings.extend(scan_typosquats(text))
    findings.extend(scan_npm_lifecycle(path))
    if path.suffix.lower() in {".yml", ".yaml"} and ".github" in path.parts:
        findings.extend(scan_floating_actions(text))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--path", action="append", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    targets = tuple(args.path) if args.path else DEFAULT_TARGETS
    files = iter_target_files(root, targets)

    if args.verbose:
        print(f"Scanning {len(files)} candidate file(s)...")

    total = 0
    for path in files:
        findings = scan_file(path)
        if not findings:
            continue
        rel = path.relative_to(root)
        for line, col, msg in findings:
            loc = f"{rel}:{line}:{col}" if line else str(rel)
            print(f"{loc}: supply-chain IOC: {msg}", file=sys.stderr)
            total += 1

    if total:
        print(
            f"\nscan_supply_chain_iocs: {total} finding(s) across "
            f"{len(files)} file(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(f"scan_supply_chain_iocs: clean ({len(files)} file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
