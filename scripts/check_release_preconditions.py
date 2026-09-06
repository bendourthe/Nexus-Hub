#!/usr/bin/env python3
"""Release-flow preconditions: refuse to tag the wrong commit, and report branch drift.

Three independent checks, each answering a failure this repository actually hit.

`--pre-tag` is the one that matters. In the v3.17.5 release a `git checkout main`
failed on a OneDrive-locked directory, left HEAD on an unrelated branch, and the
tag was created there and published -- shipping an unreleased plan file in the
release tarball. The remedy is not "check the branch earlier in the script": it is
to read HEAD at the last possible moment, immediately before `git tag`, because a
checkout that failed is exactly the state being guarded against. So this check
reads live git state on every invocation and caches nothing.

`--branches` reports two distinct categories: remote branches already merged
into the integration branch, and branches that survive a CLOSED, unmerged PR.
The second matters because `delete_branch_on_merge` only fires on a MERGE, so
with that setting enabled the first list is usually empty while stale refs still
accumulate -- which is exactly what Nexus-Hub found on itself.
It NEVER deletes anything and never proposes deleting a protected branch or one
with an open pull request. Reporting-only is deliberate: a merged branch is
sometimes still wanted, and this runs inside a release flow where a surprise
deletion would be the worst possible time.

`--repo-settings` reports whether `delete_branch_on_merge` is enabled, and (when a
catalog is present) whether the repository DESCRIPTION still agrees with the counts
README.md declares. Nexus-Hub's own description read "256 curated skills, 15 commands, 22
hooks" against an actual 273/18/31, drifted for many releases because no
version-carrying surface covers a GitHub setting.

Local-first. `--pre-tag` and `--branches` use local `git` only, with no network
and no credential. `--repo-settings` shells out to the user's own authenticated
`gh` and degrades to a skip when `gh` is absent, unauthenticated, or the
repository is not on GitHub; it only ever READS, and enabling
`delete_branch_on_merge` is left to the human, since Nexus-Hub has no credentials
and acquiring any would breach the zero-outbound policy.

Usage:
    python scripts/check_release_preconditions.py --pre-tag [--release-branch main]
    python scripts/check_release_preconditions.py --branches [--integration-branch develop]
    python scripts/check_release_preconditions.py --repo-settings
    python scripts/check_release_preconditions.py --all

Exit codes:
    0  every requested check passed (an advisory check with nothing to report
       also exits 0)
    1  a BLOCKING precondition failed -- currently only --pre-tag can do this
    2  a check could not run (not a git repository, git unavailable)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_RELEASE_BRANCH = "main"
DEFAULT_INTEGRATION_BRANCH = "develop"

# Branches never proposed for deletion, whatever git reports about them.
ALWAYS_PROTECTED = ("main", "master", "develop", "HEAD")


class GitUnavailable(RuntimeError):
    """git is missing, or the working directory is not a repository."""


def git(*args: str, cwd: Path | None = None) -> str:
    """Run git and return stripped stdout, raising GitUnavailable on failure."""
    if shutil.which("git") is None:
        raise GitUnavailable("git is not installed or not on PATH")
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise GitUnavailable(
            f"`git {' '.join(args)}` failed: {(exc.stderr or '').strip()}"
        ) from exc
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# --pre-tag
# ---------------------------------------------------------------------------


def check_pre_tag(release_branch: str, cwd: Path | None = None) -> list[str]:
    """Return a list of blocking problems; empty means safe to tag.

    Two conditions, both required:
      1. HEAD is on `release_branch`. A detached HEAD or any other branch fails.
      2. HEAD equals `origin/<release_branch>`. Tagging a commit the remote does
         not have publishes a tag nobody can reproduce.

    The remote-tracking ref is compared as-is rather than fetched: a release flow
    has already pushed, and fetching here would mask a stale local ref behind a
    network call this script deliberately does not make.
    """
    problems: list[str] = []

    head_branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    if head_branch != release_branch:
        detail = (
            "HEAD is detached"
            if head_branch == "HEAD"
            else f"HEAD is on '{head_branch}'"
        )
        problems.append(
            f"{detail}, not the expected release branch '{release_branch}'. "
            "Do NOT tag. A checkout that failed silently leaves exactly this "
            "state, which is how the v3.17.5 tag was created on the wrong commit."
        )
        # Without the right branch checked out there is nothing meaningful to
        # compare against the remote, so stop here rather than emit a confusing
        # second failure about a ref the caller never intended to tag.
        return problems

    local_sha = git("rev-parse", "HEAD", cwd=cwd)
    remote_ref = f"origin/{release_branch}"
    try:
        remote_sha = git("rev-parse", "--verify", remote_ref, cwd=cwd)
    except GitUnavailable:
        problems.append(
            f"'{remote_ref}' does not exist locally, so HEAD cannot be confirmed "
            "to match the remote. Fetch, or pass the correct --release-branch."
        )
        return problems

    if local_sha != remote_sha:
        problems.append(
            f"HEAD ({local_sha[:8]}) does not match {remote_ref} "
            f"({remote_sha[:8]}). Tagging now would publish a tag for a commit "
            "the remote does not have. Push or pull first."
        )

    return problems


# ---------------------------------------------------------------------------
# --branches
# ---------------------------------------------------------------------------


def open_pr_branches() -> set[str]:
    """Branch names with an open PR, via the user's own gh. Empty when absent.

    Failing to an EMPTY set is deliberate and is the conservative direction here:
    this function only ever removes branches from a deletion-candidate list, so an
    empty answer can only make the report more cautious, never less.
    """
    if shutil.which("gh") is None:
        return set()
    try:
        out = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "headRefName",
                "--limit",
                "200",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return {entry["headRefName"] for entry in json.loads(out)}
    except (
        OSError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ):
        return set()


def closed_unmerged_pr_branches(cwd: Path | None = None) -> list[str]:
    """Remote branches whose PR was CLOSED without merging, and which still exist.

    This category exists because the merged-branch report structurally cannot see
    it, and on a repository with `delete_branch_on_merge` enabled it is the only
    accumulation left. GitHub auto-deletes a branch when its PR MERGES; it does
    nothing when a PR is closed unmerged, so throwaway and abandoned branches
    survive indefinitely while `git branch -r --merged` reports a clean tree.

    Nexus-Hub found this on itself: the merged report returned nothing while ten
    stale refs sat on the remote.

    Requires `gh`; returns an empty list without it, which keeps the report quiet
    rather than wrong.
    """
    if shutil.which("gh") is None:
        return []
    try:
        out = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "closed",
                "--limit",
                "200",
                "--json",
                "headRefName,mergedAt",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        closed = {
            entry["headRefName"]
            for entry in json.loads(out)
            if not entry.get("mergedAt")
        }
    except (
        OSError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ):
        return []
    if not closed:
        return []

    # Only report refs that actually still exist on the remote.
    try:
        existing = {
            line.strip()[len("origin/") :]
            for line in git("branch", "-r", cwd=cwd).splitlines()
            if line.strip().startswith("origin/") and "->" not in line
        }
    except GitUnavailable:
        return []

    return sorted(name for name in closed & existing if name not in ALWAYS_PROTECTED)


def merged_branch_candidates(
    integration_branch: str, cwd: Path | None = None
) -> tuple[list[str], set[str]]:
    """Remote branches merged into the integration branch and safe to propose."""
    raw = git("branch", "-r", "--merged", f"origin/{integration_branch}", cwd=cwd)
    with_open_pr = open_pr_branches()

    candidates: list[str] = []
    for line in raw.splitlines():
        ref = line.strip()
        if not ref or "->" in ref:  # skip the origin/HEAD -> origin/main pointer
            continue
        if not ref.startswith("origin/"):
            continue
        name = ref[len("origin/") :]
        if name in ALWAYS_PROTECTED:
            continue
        if name == integration_branch:
            continue
        if name in with_open_pr:
            continue
        candidates.append(name)

    return sorted(candidates), with_open_pr


# ---------------------------------------------------------------------------
# --repo-settings
# ---------------------------------------------------------------------------


def gh_json(*args: str) -> dict | None:
    """Read-only gh call returning parsed JSON, or None when unavailable."""
    if shutil.which("gh") is None:
        return None
    try:
        out = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=True
        ).stdout
        return json.loads(out)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def authoritative_skill_count(root: Path) -> int | None:
    """The one count with a machine-readable source: one entry per skill."""
    skills = root / "data" / "skills.json"
    if not skills.is_file():
        return None
    try:
        return len(json.loads(skills.read_text(encoding="utf-8"))["skills"])
    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        return None


def declared_counts(root: Path) -> dict[str, int]:
    """Counts the project DECLARES about itself, parsed from README.md.

    A file glob was the obvious source and the wrong one: `catalog/commands/*.md`
    includes permanent aliases and `catalog/hooks/` mixes hook scripts with
    helpers, so globbing yields 21 and 34 where the project states 18 and 31.
    Emitting a derived number would have been worse than emitting none, because
    it is the number someone copies into the description.

    README.md is the declaration the description is supposed to agree with, so
    the comparison is between two hand-maintained surfaces -- which is exactly
    the drift class this check exists for. `declared_vs_actual` below covers the
    case where the declaration itself has gone stale.

    Empty dict when there is no README to read, so this self-gates on a
    repository that declares nothing.
    """
    readme = root / "README.md"
    if not readme.is_file():
        return {}
    text = readme.read_text(encoding="utf-8", errors="replace")
    counts: dict[str, int] = {}
    for noun in ("skills", "commands", "hooks", "agents"):
        match = re.search(
            rf"\*?\*?(\d+)\*?\*?\s+(?:[a-z-]+\s+)?{noun}\b", text, re.IGNORECASE
        )
        if match:
            counts[noun] = int(match.group(1))
    return counts


def declared_vs_actual(root: Path) -> list[str]:
    """Catch the declaration itself drifting from the catalog it describes."""
    actual = authoritative_skill_count(root)
    declared = declared_counts(root).get("skills")
    if actual is None or declared is None or actual == declared:
        return []
    return [
        (
            f"README.md declares {declared} skills but data/skills.json has "
            f"{actual}; fix the declaration before using it to judge the "
            "repository description"
        )
    ]


def description_drift(description: str, declared: dict[str, int]) -> list[str]:
    """Report each 'N <noun>' in the description that disagrees with the declaration.

    Only nouns the description actually mentions are checked, so a description
    making no numeric claim reports nothing rather than being nagged into one.
    """
    findings: list[str] = []
    for noun, expected in sorted(declared.items()):
        match = re.search(
            rf"(\d+)\s+(?:[a-z-]+\s+)?{noun}\b", description, re.IGNORECASE
        )
        if match and int(match.group(1)) != expected:
            findings.append(
                f"{noun}: description says {match.group(1)}, README.md declares {expected}"
            )
    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def report_pre_tag(release_branch: str, root: Path) -> int:
    print(f"Pre-tag assertion (expected release branch: {release_branch})")
    sys.stdout.flush()
    problems = check_pre_tag(release_branch, cwd=root)
    if problems:
        print("  BLOCKED -- do not create the tag:", file=sys.stderr)
        for problem in problems:
            print(f"    - {problem}", file=sys.stderr)
        return 1
    print(f"  OK: HEAD is on {release_branch} and matches origin/{release_branch}")
    return 0


def report_branches(integration_branch: str, root: Path) -> int:
    print(f"Branch hygiene (merged into origin/{integration_branch})")
    candidates, with_open_pr = merged_branch_candidates(integration_branch, cwd=root)
    if candidates:
        print(f"  {len(candidates)} merged branch(es) are cleanup candidates:")
        for name in candidates:
            print(f"    - origin/{name}")
        if with_open_pr:
            print(f"  ({len(with_open_pr)} branch(es) with an open PR were excluded)")
    else:
        print("  OK: no merged remote branches to clean up")

    # Second, distinct category. `delete_branch_on_merge` removes a branch when
    # its PR MERGES and does nothing when a PR is closed unmerged, so on a repo
    # with that setting on, this is the only accumulation left -- and the merged
    # report above structurally cannot see it.
    abandoned = closed_unmerged_pr_branches(cwd=root)
    if abandoned:
        print(f"  {len(abandoned)} branch(es) survive a CLOSED, unmerged PR:")
        for name in abandoned:
            print(f"    - origin/{name}")
        print(
            "  delete_branch_on_merge does NOT cover these. Review and delete by hand."
        )

    print("  Reporting only -- nothing was deleted.")
    return 0


def report_repo_settings(root: Path) -> int:
    print("Repository settings")
    info = gh_json(
        "repo", "view", "--json", "deleteBranchOnMerge,description,nameWithOwner"
    )
    if info is None:
        print("  SKIPPED: gh unavailable, unauthenticated, or not a GitHub repo")
        return 0

    if info.get("deleteBranchOnMerge"):
        print("  OK: delete_branch_on_merge is enabled")
    else:
        print(
            "  NOTE: delete_branch_on_merge is DISABLED, so merged branches accumulate."
        )
        print(
            "        Enable it with your own gh, which this script deliberately does not do:"
        )
        print(
            f"          gh repo edit {info.get('nameWithOwner', '<owner/repo>')}"
            " --delete-branch-on-merge"
        )
        print(
            "        Nexus-Hub cannot set this at install time: the installer holds no"
        )
        print(
            "        credentials, and acquiring any would breach the zero-outbound policy."
        )
        print("        It also does NOT remove a branch whose PR was closed unmerged.")

    stale_declaration = declared_vs_actual(root)
    if stale_declaration:
        print("  NOTE: the project's own declaration is stale:")
        for finding in stale_declaration:
            print(f"    - {finding}")

    declared = declared_counts(root)
    description = info.get("description") or ""
    if not declared:
        print("  Description drift: SKIPPED (no README declaration to compare against)")
        return 0
    drift = description_drift(description, declared)
    if drift:
        print("  NOTE: the repository description disagrees with README.md:")
        for finding in drift:
            print(f"    - {finding}")
        print("        The description is not a version-carrying surface, so")
        print("        check_version_sync.py cannot see it and it drifts silently")
        print("        across releases. Update it by hand.")
    else:
        print("  OK: repository description agrees with README.md")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument(
        "--pre-tag",
        action="store_true",
        help="BLOCKING: assert HEAD is the release branch and matches its remote",
    )
    parser.add_argument(
        "--branches", action="store_true", help="report merged remote branches"
    )
    parser.add_argument(
        "--repo-settings",
        action="store_true",
        help="report delete_branch_on_merge and description drift (needs gh)",
    )
    parser.add_argument("--all", action="store_true", help="run every check")
    parser.add_argument("--release-branch", default=DEFAULT_RELEASE_BRANCH)
    parser.add_argument("--integration-branch", default=DEFAULT_INTEGRATION_BRANCH)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    run_pre_tag = args.pre_tag or args.all
    run_branches = args.branches or args.all
    run_settings = args.repo_settings or args.all

    if not (run_pre_tag or run_branches or run_settings):
        parser.error(
            "choose at least one of --pre-tag, --branches, --repo-settings, --all"
        )

    exit_code = 0
    try:
        if run_pre_tag:
            exit_code = max(exit_code, report_pre_tag(args.release_branch, root))
        if run_branches:
            exit_code = max(exit_code, report_branches(args.integration_branch, root))
    except GitUnavailable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if run_settings:
        exit_code = max(exit_code, report_repo_settings(root))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
