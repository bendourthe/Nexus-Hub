#!/usr/bin/env python3
"""Apply the v2.0.0 DevAI-Hub -> Nexus-Hub rename across catalog and template trees.

Idempotent: re-running on already-renamed files is a no-op. Variants are applied
in length-descending order so longer strings are replaced before shorter ones
that would over-match (e.g. `DEVAI-HUB` before `DEVAI_HUB`).

Writes a per-file manifest to docs/archive/v2/v2.0/rename-manifest.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

VARIANTS: list[tuple[str, str]] = [
    ("DevAI-Hub", "Nexus-Hub"),
    ("DEVAI-HUB", "NEXUS-HUB"),
    ("DEVAI_HUB", "NEXUS_HUB"),
    ("DevAI Hub", "Nexus Hub"),
    ("devai-hub", "nexus-hub"),
    ("devai_hub", "nexus_hub"),
    ("devai-skill-server", "nexus-skill-server"),
    ("devai-code-search", "nexus-code-search"),
    ("devai-web-fetch", "nexus-web-fetch"),
    ("devai_skill_server", "nexus_skill_server"),
    ("devai_code_search", "nexus_code_search"),
    ("devai_web_fetch", "nexus_web_fetch"),
    ("devai_mcp_benchmark", "nexus_mcp_benchmark"),
    ("devai-backup", "nexus-backup"),
    ("DEVAI_", "NEXUS_"),
    ("DEVAI-", "NEXUS-"),
]

TARGET_ROOTS: list[str] = [
    "catalog",
    "templates",
    ".cursor",
]

SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf"}


def iter_target_files() -> list[Path]:
    files: list[Path] = []
    for root_name in TARGET_ROOTS:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() in SKIP_SUFFIXES:
                continue
            files.append(p)
    return files


def rename_file(path: Path) -> tuple[int, int]:
    """Return (changed_line_count, total_replacements) for the file."""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0, 0

    updated = original
    total_replacements = 0
    for old, new in VARIANTS:
        count = updated.count(old)
        if count:
            updated = updated.replace(old, new)
            total_replacements += count

    if updated == original:
        return 0, 0

    changed_lines = 0
    for o, u in zip(original.splitlines(), updated.splitlines()):
        if o != u:
            changed_lines += 1
    if len(original.splitlines()) != len(updated.splitlines()):
        changed_lines = max(changed_lines, abs(len(updated.splitlines()) - len(original.splitlines())))

    path.write_text(updated, encoding="utf-8", newline="\n" if "\r\n" not in original else None)
    return changed_lines, total_replacements


def main() -> int:
    files = iter_target_files()
    manifest_lines: list[str] = []
    manifest_lines.append("# v2.0.0 Rename Manifest")
    manifest_lines.append("")
    manifest_lines.append("Per-file changed-line / replacement counts from `scripts/apply_rename.py`.")
    manifest_lines.append("")
    manifest_lines.append("| File | Lines changed | Replacements |")
    manifest_lines.append("|------|---------------|--------------|")

    total_files = 0
    total_lines = 0
    total_repl = 0
    for f in sorted(files):
        lines, repl = rename_file(f)
        if repl:
            total_files += 1
            total_lines += lines
            total_repl += repl
            rel = f.relative_to(REPO_ROOT).as_posix()
            manifest_lines.append(f"| `{rel}` | {lines} | {repl} |")

    manifest_lines.append("")
    manifest_lines.append(f"**Totals**: {total_files} files, {total_lines} lines, {total_repl} replacements.")
    manifest_lines.append("")

    manifest = REPO_ROOT / "docs" / "v2.0.0" / "rename-manifest.txt"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8", newline="\n")

    print(f"Rewrote {total_files} files ({total_repl} replacements, {total_lines} lines changed)")
    print(f"Manifest: {manifest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
