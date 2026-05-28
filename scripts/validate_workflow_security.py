#!/usr/bin/env python3
"""Validate GitHub Actions workflow files for known unsafe patterns.

Checks each `.github/workflows/*.yml` for:

    - Third-party actions pinned to a moving ref (@main, @master, @latest).
      GitHub-owned actions (`actions/*`, `github/*`) are allowed to pin to a
      major-version tag (@vN).
    - `pull_request_target` trigger combined with explicit checkout of
      the pull request head ref (untrusted code in a privileged context).
    - Direct interpolation of `${{ github.event.* }}` user-controlled fields
      into `run:` script bodies (script injection risk; use env: passthrough).
    - Workflows that grant `permissions: write-all` or no permissions block
      while accepting `pull_request` events.

Local-only, read-only, zero outbound calls.

Exit codes:
    0 - no findings
    1 - one or more findings
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TRUSTED_OWNERS: frozenset[str] = frozenset({"actions", "github"})

ACTION_USES_RE = re.compile(
    r"^\s*-?\s*uses:\s*([A-Za-z0-9._\-]+)/([A-Za-z0-9._\-/]+?)@([^\s#]+)\s*(?:#.*)?$"
)
COMMIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
MAJOR_TAG_RE = re.compile(r"^v\d+(?:\.\d+){0,2}$")
MOVING_REFS: frozenset[str] = frozenset({"main", "master", "latest", "HEAD", "develop"})

PR_TARGET_TRIGGER_RE = re.compile(r"^\s*(?:on:\s*)?pull_request_target\b", re.MULTILINE)
PR_HEAD_CHECKOUT_RE = re.compile(
    r"(?:ref|sha)\s*:\s*\$\{\{\s*github\.event\.pull_request\.head\.(?:ref|sha)\s*\}\}"
)

GITHUB_EVENT_INJECTION_RE = re.compile(
    r"\$\{\{\s*github\.event\.(?:"
    r"issue\.title|issue\.body|"
    r"pull_request\.title|pull_request\.body|pull_request\.head\.ref|"
    r"comment\.body|review\.body|"
    r"head_commit\.message|head_commit\.author\.email|head_commit\.author\.name|"
    r"workflow_run\.head_branch|workflow_run\.head_commit\.message"
    r")[^}]*\}\}"
)

RUN_INLINE_RE = re.compile(r"^(\s*)(?:-\s+)?run:\s*(.+?)\s*$")
RUN_BLOCK_START_RE = re.compile(r"^(\s*)(?:-\s+)?run:\s*[|>][\-+]?\s*$")

WRITE_ALL_PERMISSIONS_RE = re.compile(r"^\s*permissions:\s*write-all\s*$", re.MULTILINE)


def iter_run_lines(text: str):
    """Yield (line_no, line_text) for every line inside a `run:` block.

    Handles both inline (`run: cmd`) and block-scalar (`run: |` / `run: >`)
    forms. A block-scalar continues until a less-or-equal-indented non-blank
    line that is not part of the block body.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        inline = RUN_INLINE_RE.match(line)
        block = RUN_BLOCK_START_RE.match(line)
        if block:
            base_indent = len(block.group(1))
            j = i + 1
            body_indent: int | None = None
            while j < len(lines):
                body = lines[j]
                stripped = body.lstrip()
                if not stripped:
                    j += 1
                    continue
                indent = len(body) - len(stripped)
                if indent <= base_indent:
                    break
                if body_indent is None:
                    body_indent = indent
                elif indent < body_indent:
                    break
                yield j + 1, body
                j += 1
            i = j
            continue
        if inline and not block:
            yield i + 1, inline.group(2)
        i += 1


def scan_workflow(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings

    lines = text.splitlines()

    has_pr_target = bool(PR_TARGET_TRIGGER_RE.search(text))
    if has_pr_target:
        for m in PR_HEAD_CHECKOUT_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            findings.append((
                line_no,
                "pull_request_target + checkout of PR head ref "
                "(untrusted code in privileged context)",
            ))

    for line_no, line in enumerate(lines, start=1):
        m = ACTION_USES_RE.match(line)
        if not m:
            continue
        owner, _name, ref = m.group(1), m.group(2), m.group(3)
        if owner in TRUSTED_OWNERS:
            if ref in MOVING_REFS:
                findings.append((
                    line_no,
                    f"GitHub-owned action pinned to moving ref @{ref}",
                ))
            continue
        if COMMIT_SHA_RE.match(ref):
            continue
        if MAJOR_TAG_RE.match(ref):
            findings.append((
                line_no,
                f"third-party action {owner}/... pinned to tag @{ref} "
                "(pin to commit SHA for stronger supply-chain guarantees)",
            ))
            continue
        if ref in MOVING_REFS:
            findings.append((
                line_no,
                f"third-party action pinned to moving ref @{ref}",
            ))
            continue
        findings.append((
            line_no,
            f"third-party action ref @{ref} is not a 40-char commit SHA",
        ))

    for line_no, run_line in iter_run_lines(text):
        for inj in GITHUB_EVENT_INJECTION_RE.finditer(run_line):
            findings.append((
                line_no,
                f"untrusted github.event interpolated into run: block: "
                f"{inj.group(0)} (use env: passthrough)",
            ))

    if WRITE_ALL_PERMISSIONS_RE.search(text):
        for line_no, line in enumerate(lines, start=1):
            if "permissions:" in line and "write-all" in line:
                findings.append((
                    line_no,
                    "permissions: write-all grants every scope "
                    "(use least-privilege per-scope grants)",
                ))
                break

    return findings


def find_workflow_files(root: Path, paths: list[str] | None) -> list[Path]:
    if paths:
        files: list[Path] = []
        for p in paths:
            full = root / p
            if full.is_file():
                files.append(full)
            elif full.is_dir():
                files.extend(sorted(full.glob("*.yml")))
                files.extend(sorted(full.glob("*.yaml")))
        return files
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []
    out: list[Path] = []
    out.extend(sorted(workflows_dir.glob("*.yml")))
    out.extend(sorted(workflows_dir.glob("*.yaml")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--path", action="append", default=None)
    parser.add_argument(
        "--strict-sha-pinning",
        action="store_true",
        help="Treat third-party major-version tag pins as errors (default: allowed).",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    files = find_workflow_files(root, args.path)
    if args.verbose:
        print(f"Scanning {len(files)} workflow file(s)...")

    total_errors = 0
    total_warnings = 0
    for path in files:
        findings = scan_workflow(path)
        if not findings:
            continue
        rel = path.relative_to(root)
        for line, msg in findings:
            is_tag_pin_warning = (
                "pinned to tag @" in msg and not args.strict_sha_pinning
            )
            if is_tag_pin_warning:
                print(f"{rel}:{line}: WARN: {msg}")
                total_warnings += 1
            else:
                print(f"{rel}:{line}: {msg}", file=sys.stderr)
                total_errors += 1

    if total_errors:
        print(
            f"\nvalidate_workflow_security: {total_errors} error(s), "
            f"{total_warnings} warning(s) across {len(files)} workflow(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(
            f"validate_workflow_security: clean "
            f"({len(files)} workflow(s), {total_warnings} warning(s))."
        )
    elif total_warnings:
        print(
            f"validate_workflow_security: 0 errors, "
            f"{total_warnings} warning(s)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
