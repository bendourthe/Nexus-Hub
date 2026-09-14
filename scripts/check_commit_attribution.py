#!/usr/bin/env python3
"""Check maintainer Git attribution; never distributed by Nexus-Hub installers.

Scan history, pending commit identities and/or one commit-message file.
Exit 0: clean; 1: attribution findings; 2: usage or incomplete-scan error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET = ("Ben Dourthe", "50595044+bendourthe@users.noreply.github.com")
GITHUB = ("GitHub", "noreply@github.com")
TRAILER = re.compile(r"^[ \t]*(Co-authored-by|Made-with)[ \t]*:", re.IGNORECASE)
IDENTITY = re.compile(r"([^<>\r\n]+?)\s*<([^<>\s]+)>")


def allowed(name: str, email: str, *, committer: bool = False) -> bool:
    """Use a closed allowlist, so unknown future identities cannot pass."""
    identity = (name, email.lower())
    return identity == TARGET or (committer and identity == GITHUB)


def attribution_fields(message: str) -> list[tuple[str, str]]:
    """Read attribution lines, including their folded continuation lines."""
    fields: list[tuple[str, str]] = []
    for line in message.splitlines():
        match = TRAILER.match(line)
        if match:
            fields.append((match.group(1), line[match.end() :].strip()))
        elif line.startswith((" ", "\t")) and fields:
            key, value = fields[-1]
            fields[-1] = (key, value + " " + line.strip())
        else:
            # A later indented paragraph must not continue an earlier field.
            fields.append(("", ""))
    return [(key, value) for key, value in fields if key]


def message_findings(message: str, source: str) -> list[str]:
    """Reject malformed or non-allowlisted attribution without editing prose."""
    findings = []
    for key, value in attribution_fields(message):
        identity = IDENTITY.fullmatch(value)
        if not identity or not allowed(*identity.groups()):
            findings.append(f"{source}: {key}: {json.dumps(value, ensure_ascii=True)}")
    return findings


def git(root: Path, *args: str) -> bytes:
    """Read actual objects, bypassing replacement refs and display configuration."""
    result = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "-C",
            str(root),
            "-c",
            "log.showSignature=false",
            "-c",
            "i18n.logOutputEncoding=UTF-8",
            *args,
        ],
        capture_output=True,
        timeout=60,
        check=True,
    )
    return result.stdout


def history_findings(root: Path) -> tuple[int, list[str]]:
    """Scan every commit reachable from refs; reject incomplete histories."""
    shallow = git(root, "rev-parse", "--is-shallow-repository").strip()
    if shallow != b"false":
        raise ValueError(
            "a shallow or unrecognized repository cannot prove all-ref history; fetch full history"
        )
    grafts = git(root, "rev-parse", "--git-path", "info/grafts").decode().strip()
    if (root / grafts).exists():
        raise ValueError(
            "legacy grafts can hide history; remove them in an isolated full-history clone"
        )
    raw = git(
        root,
        "log",
        "--all",
        "--no-use-mailmap",
        "--no-notes",
        "-z",
        "--format=%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B",
    )
    if not raw or not raw.endswith(b"\0"):
        raise ValueError("no complete commit records were returned")
    fields = raw[:-1].decode("utf-8", errors="replace").split("\0")
    if len(fields) % 6:
        raise ValueError("malformed Git commit records")
    findings = []
    for offset in range(0, len(fields), 6):
        sha, author, email, committer, committer_email, message = fields[
            offset : offset + 6
        ]
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            raise ValueError("malformed Git object identity")
        for role, name, address in [
            ("author", author, email),
            ("committer", committer, committer_email),
        ]:
            if not allowed(name, address, committer=role == "committer"):
                findings.append(
                    f"{sha[:12]}: {role}: {json.dumps(f'{name} <{address}>')}"
                )
        findings.extend(message_findings(message, sha[:12]))
    return len(fields) // 6, findings


def pending_findings(root: Path) -> list[str]:
    """Check identities Git exposes to commit hooks, including amended authors."""
    if git(root, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        raise ValueError("pending commit checks require a Git working tree")
    findings = []
    for role in ("author", "committer"):
        value = git(root, "var", f"GIT_{role.upper()}_IDENT").decode("utf-8").strip()
        identity = re.fullmatch(r"(.+) <([^<>]+)> -?\d+ [+-]\d{4}", value)
        if not identity:
            raise ValueError(f"malformed pending {role} identity")
        name, email = identity.groups()
        if not allowed(name, email, committer=role == "committer"):
            findings.append(f"pending {role}: {json.dumps(f'{name} <{email}>')}")
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run every requested operation; errors dominate findings in the exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root for history and pending-commit checks",
    )
    parser.add_argument(
        "--all-refs", action="store_true", help="scan full history on every ref"
    )
    parser.add_argument(
        "--message-file", type=Path, help="check one UTF-8 commit-message file"
    )
    parser.add_argument(
        "--pending-commit",
        action="store_true",
        help="check Git's pending author and committer in a commit hook",
    )
    args = parser.parse_args(argv)
    if not args.all_refs and args.message_file is None and not args.pending_commit:
        parser.error("specify --all-refs, --message-file and/or --pending-commit")
    findings: list[str] = []
    errors: list[str] = []
    commits = 0
    if args.all_refs:
        try:
            commits, found = history_findings(args.root.resolve())
            findings.extend(found)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            errors.append(f"history scan incomplete: {type(exc).__name__}: {exc}")
    if args.pending_commit:
        try:
            findings.extend(pending_findings(args.root.resolve()))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            errors.append(
                f"pending commit scan incomplete: {type(exc).__name__}: {exc}"
            )
    if args.message_file is not None:
        try:
            findings.extend(
                message_findings(
                    args.message_file.read_text(encoding="utf-8"), "message-file"
                )
            )
        except (OSError, ValueError) as exc:
            errors.append(f"message scan incomplete: {type(exc).__name__}: {exc}")
    for finding in findings[:20]:
        print(finding)
    if len(findings) > 20:
        print(f"... {len(findings) - 20} additional findings")
    print(
        f"Attribution: {commits} commits scanned; {len(findings)} findings; {len(errors)} errors"
    )
    for error in errors:
        print(json.dumps(error, ensure_ascii=True), file=sys.stderr)
    return 2 if errors else int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
