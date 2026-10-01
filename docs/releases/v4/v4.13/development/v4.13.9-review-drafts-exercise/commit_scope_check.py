"""Evidence script for v4.13.9 T421: apply the documented `commit` sub-mode of multi-agent-code-review.

It validates the argument before any git call, resolves it with rev-parse, picks the normal,
root, or merge diff, and logs every git invocation, so a hostile argument can be shown to
reach no git call at all. It never reviews or posts anything.

Usage: python commit_scope_check.py <arg> [<arg> ...]
"""
from __future__ import annotations

import re
import subprocess
import sys

_SHA = re.compile(r"[0-9a-fA-F]{7,40}")
CALLS: list[list[str]] = []


def git(*args: str) -> subprocess.CompletedProcess[str]:
    argv = ["git", *args]
    CALLS.append(argv)
    return subprocess.run(argv, capture_output=True, text=True, check=False)


def resolve(arg: str) -> dict:
    CALLS.clear()
    if not _SHA.fullmatch(arg):
        return {"arg": arg, "result": "rejected before any git call", "git_calls": len(CALLS)}
    rev = git("rev-parse", "--verify", "--end-of-options", f"{arg}^{{commit}}")
    if rev.returncode != 0:
        reason = "ambiguous" if "ambiguous" in rev.stderr else "does not resolve to a commit"
        return {"arg": arg, "result": f"stopped: {reason}", "git_calls": len(CALLS)}
    sha = rev.stdout.strip()
    parents = git("rev-list", "--parents", "-n", "1", "--end-of-options", sha).stdout.split()[1:]
    if not parents:
        plan = ["git", "show", "--end-of-options", sha]
        kind = "root"
    elif len(parents) == 1:
        plan = ["git", "diff", "--end-of-options", f"{sha}^", sha]
        kind = "normal"
    else:
        plan = ["git", "diff", "--end-of-options", f"{sha}^1", sha]
        kind = "merge (ask before reviewing against the first parent)"
    return {"arg": arg, "result": f"resolved {sha[:12]}", "kind": kind, "diff_command": plan, "git_calls": len(CALLS)}


def main() -> int:
    for arg in sys.argv[1:]:
        print(resolve(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
