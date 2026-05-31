#!/usr/bin/env python3
"""generate_release_changelog.py - local conventional-commit release helper.

Parses conventional-commit messages since the last tag, computes the next
semantic-version bump (major / minor / patch), and renders a Keep-a-Changelog
section. Prints the section to stdout (or to a ``--out`` file) and reports the
proposed bump on stderr.

This is a LOCAL alternative to a third-party release automation Action: it
shells out only to the local ``git`` binary, makes no network call, and
requires no credentials. It does not replace the manual changelog flow in the
``update-version`` / ``generate-changelog`` skills - it is an optional helper
those flows can reference.

Python 3 stdlib only.

Usage:
    # Read commits from local git history (last tag -> HEAD):
    python scripts/generate_release_changelog.py

    # Override the current version and write the section to a file:
    python scripts/generate_release_changelog.py --current-version 2.4.0 --out section.md

    # Test / fixture mode: read NUL-separated commit messages from a file:
    python scripts/generate_release_changelog.py --commits-from fixture.txt --current-version 1.2.3
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date as date_cls
from pathlib import Path

# Conventional-commit subject: type(scope)!: description
_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:\s*(?P<desc>.+?)\s*$"
)
_SEMVER_RE = re.compile(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")

# Commit type -> (bump level, Keep-a-Changelog section). Levels: 2=minor, 1=patch.
# Types absent here are non-release (docs/chore/etc.) and categorize to Changed.
_RELEASE_TYPES = {
    "feat": (2, "Added"),
    "feature": (2, "Added"),
    "fix": (1, "Fixed"),
    "bugfix": (1, "Fixed"),
    "perf": (1, "Changed"),
}
_SECTION_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "revert": "Removed",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
}
_SECTION_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def parse_commit(message: str) -> dict:
    """Parse a single commit message into its conventional-commit parts."""
    lines = message.strip().splitlines()
    subject = lines[0].strip() if lines else ""
    breaking = "BREAKING CHANGE" in message or "BREAKING-CHANGE" in message
    match = _SUBJECT_RE.match(subject)
    if not match:
        return {
            "type": None,
            "scope": None,
            "breaking": breaking,
            "description": subject,
            "raw": subject,
        }
    if match.group("breaking"):
        breaking = True
    return {
        "type": match.group("type").lower(),
        "scope": (match.group("scope") or "").strip() or None,
        "breaking": breaking,
        "description": match.group("desc").strip(),
        "raw": subject,
    }


def determine_bump(commits: list[dict]) -> str | None:
    """Return 'major' | 'minor' | 'patch' | None for a list of parsed commits."""
    level = 0  # 0=none, 1=patch, 2=minor, 3=major
    for commit in commits:
        if commit.get("breaking"):
            return "major"
        ctype = commit.get("type")
        if ctype in _RELEASE_TYPES:
            level = max(level, _RELEASE_TYPES[ctype][0])
    return {0: None, 1: "patch", 2: "minor"}[level]


def bump_version(current: str, bump: str) -> str:
    """Apply a semver bump to a current version string (leading 'v' tolerated)."""
    match = _SEMVER_RE.match(current.strip())
    if not match:
        raise ValueError(f"not a semantic version: {current!r}")
    major, minor, patch = (int(match.group(k)) for k in ("major", "minor", "patch"))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump: {bump!r}")


def _entry(commit: dict) -> str:
    """Render one changelog bullet, bolding the scope and flagging breaking changes."""
    desc = commit["description"] or commit["raw"]
    prefix = "**BREAKING**: " if commit.get("breaking") else ""
    if commit.get("scope"):
        return f"- {prefix}**{commit['scope']}**: {desc}"
    return f"- {prefix}{desc}"


def categorize(commits: list[dict]) -> dict[str, list[str]]:
    """Group parsed commits into Keep-a-Changelog sections (order-preserving)."""
    sections: dict[str, list[str]] = {}
    for commit in commits:
        ctype = commit.get("type")
        if ctype is None:
            continue  # non-conventional; skip from the categorized changelog
        text = (commit.get("description") or "") + " " + commit.get("raw", "")
        if re.search(r"\b(security|vulnerability|cve)\b", text, re.IGNORECASE):
            section = "Security"
        elif commit.get("breaking"):
            section = "Changed"
        else:
            section = _SECTION_MAP.get(ctype, "Changed")
        sections.setdefault(section, []).append(_entry(commit))
    return sections


def render_changelog_section(version: str, when: str, commits: list[dict]) -> str:
    """Render the full ``## [version] - date`` block with non-empty sections only."""
    sections = categorize(commits)
    out = [f"## [{version}] - {when}", ""]
    any_section = False
    for name in _SECTION_ORDER:
        entries = sections.get(name)
        if not entries:
            continue
        any_section = True
        out.append(f"### {name}")
        out.extend(entries)
        out.append("")
    if not any_section:
        out.append("_No conventional-commit changes since the last tag._")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --- git readers (the only impure part) --------------------------------------


def _git(args: list[str], repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(repo_root),
    )
    return proc.stdout if proc.returncode == 0 else ""


def last_tag(repo_root: Path) -> str | None:
    out = _git(["describe", "--tags", "--abbrev=0"], repo_root).strip()
    return out or None


def commits_since(tag: str | None, repo_root: Path) -> list[str]:
    """Return NUL-split commit messages from ``tag..HEAD`` (or all history)."""
    rng = f"{tag}..HEAD" if tag else "HEAD"
    # %B = raw body (subject + body); %x00 = NUL record separator.
    out = _git(["log", rng, "--no-merges", "--format=%B%x00"], repo_root)
    return [c.strip() for c in out.split("\0") if c.strip()]


def _version_from_tag(tag: str | None) -> str | None:
    if not tag:
        return None
    match = _SEMVER_RE.match(tag)
    if not match:
        return None
    return f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute the next semver bump and render a Keep-a-Changelog section from conventional commits."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root (defaults to CWD).")
    parser.add_argument("--from-tag", default=None, help="Base tag (default: latest git tag).")
    parser.add_argument(
        "--current-version",
        default=None,
        help="Current version (default: derived from the base tag).",
    )
    parser.add_argument(
        "--commits-from",
        default=None,
        help="Read NUL-separated commit messages from this file instead of git (testing/fixtures).",
    )
    parser.add_argument("--date", default=None, help="Release date YYYY-MM-DD (default: today).")
    parser.add_argument("--out", default=None, help="Write the section to this file instead of stdout.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()

    if args.commits_from:
        raw = Path(args.commits_from).read_text(encoding="utf-8")
        messages = [c.strip() for c in raw.split("\0") if c.strip()]
        if len(messages) <= 1:
            # No NUL separators: fall back to blank-line-separated records.
            messages = [c.strip() for c in re.split(r"\n[ \t]*\n", raw) if c.strip()]
        tag = args.from_tag
    else:
        tag = args.from_tag or last_tag(repo_root)
        messages = commits_since(tag, repo_root)

    commits = [parse_commit(m) for m in messages]
    bump = determine_bump(commits)

    current = args.current_version or _version_from_tag(tag)
    if not current:
        print(
            "error: could not determine the current version; pass --current-version",
            file=sys.stderr,
        )
        return 2

    if bump is None:
        print(
            f"No release-triggering conventional commits since {tag or 'the start of history'}; "
            f"current version {current} stands.",
            file=sys.stderr,
        )
        next_version = current
    else:
        next_version = bump_version(current, bump)
        print(f"Proposed bump: {bump} -> {next_version} (from {current})", file=sys.stderr)

    when = args.date or date_cls.today().isoformat()
    section = render_changelog_section(next_version, when, commits)

    if args.out:
        Path(args.out).write_text(section, encoding="utf-8")
        print(f"Wrote changelog section to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
