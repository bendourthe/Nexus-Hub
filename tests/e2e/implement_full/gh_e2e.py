"""Stateful `gh` stand-in for the v4.13.2 end-to-end evaluation.

Unlike tests/fixtures/gh_stub (a fixed-answer stub for unit tests), this one
remembers what an agent did: `pr create` opens a pull request, `pr merge` merges
it, `release create` publishes a release. The completion checker then reads the
same state back, so a fixture run reaches PLAN COMPLETE only if the agent really
performed each hosting step. State lives in the JSON file named by GH_E2E_STATE;
every call is appended to GH_E2E_LOG. No network is used. Calls without --repo
fail, mirroring the rule that hosting calls are pinned to the approved repository.
"""

from __future__ import annotations

import json
import os
import sys


def _flag(argv: list[str], name: str) -> str | None:
    return (
        argv[argv.index(name) + 1]
        if name in argv and argv.index(name) + 1 < len(argv)
        else None
    )


def main(argv: list[str]) -> int:
    path = os.environ["GH_E2E_STATE"]
    state: dict = {"prs": {}, "releases": {}}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
    with open(os.environ.get("GH_E2E_LOG", os.devnull), "a", encoding="utf-8") as log:
        log.write(json.dumps(argv) + "\n")
    if "--repo" not in argv:
        print("gh stand-in: every call must pass --repo", file=sys.stderr)
        return 1
    head = argv[:2]
    out: object = None
    if head == ["pr", "create"]:
        branch = _flag(argv, "--head") or "HEAD"
        state["prs"][branch] = {
            "state": "OPEN",
            "base": _flag(argv, "--base") or "develop",
        }
        out = f"https://github.example/{_flag(argv, '--repo')}/pull/1"
    elif head == ["pr", "merge"]:
        branch = argv[2]
        if branch not in state["prs"]:
            print("no pull request for that branch", file=sys.stderr)
            return 1
        state["prs"][branch]["state"] = "MERGED"
    elif head == ["pr", "view"]:
        pr = state["prs"].get(argv[2])
        if pr is None:
            print(f'no pull requests found for branch "{argv[2]}"', file=sys.stderr)
            return 1
        out = {"state": pr["state"], "headRefOid": pr.get("head", "")}
    elif head == ["pr", "checks"]:
        if argv[2] not in state["prs"]:
            print(f'no pull requests found for branch "{argv[2]}"', file=sys.stderr)
            return 1
        out = [{"name": "ci", "bucket": "pass"}]
    elif head == ["release", "create"]:
        state["releases"][argv[2]] = {"isDraft": "--draft" in argv}
    elif head == ["release", "view"]:
        release = state["releases"].get(argv[2])
        if release is None:
            print("release not found", file=sys.stderr)
            return 1
        out = release
    elif head == ["run", "list"]:
        out = []
    elif head[:1] == ["api"]:
        out = {"default_branch": "main"}
    else:
        print(f"gh stand-in: unsupported {head}", file=sys.stderr)
        return 1
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle)
    if out is not None:
        print(out if isinstance(out, str) else json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
