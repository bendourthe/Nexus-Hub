"""Stateful `gh` stand-in for the v4.13.2 end-to-end evaluation.

Unlike tests/fixtures/gh_stub (a fixed-answer stub for unit tests), this one
remembers what an agent did: `pr create` opens a pull request, `pr merge` merges
it, `release create` publishes a release. The completion checker then reads the
same state back, so a fixture run reaches PLAN COMPLETE only if the agent really
performed each hosting step. State lives in the JSON file named by GH_E2E_STATE;
every call is appended to GH_E2E_LOG. No network is used. Calls without --repo
fail, mirroring the rule that hosting calls are pinned to the approved repository;
`gh api` takes no --repo, so an `api` call is accepted when its endpoint names `repos/`.

When E2E_STUB_REMOTE_MIRROR names the fixture's bare mirror, the stand-in reads it
the way the host would: `pr create` records the pushed head's SHA, and `pr merge`
records the base branch's tip as the merge commit once that tip contains the head
(the agent pushes the merge first, which is where the host's own merge leaves it).

For the minor scenario (v4.13.6) it also answers `pr list` (filtered by `--state`
and `--head=`), `api repos/<r>` (the default branch), `.../branches` (none
protected), and `.../activity` (from the state's "activity" map, {branch: [iso
times]}), so the cleanup executor's hosting checks read the same state. A fixture
seeds its pre-existing pull requests and activity in the state file before the run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _flag(argv: list[str], name: str) -> str | None:
    return (
        argv[argv.index(name) + 1]
        if name in argv and argv.index(name) + 1 < len(argv)
        else None
    )


def _mirror_git(*args: str) -> subprocess.CompletedProcess | None:
    mirror = os.environ.get("E2E_STUB_REMOTE_MIRROR")
    if not mirror:
        return None
    return subprocess.run(
        [os.environ.get("E2E_REAL_GIT") or "git", "--git-dir", mirror, *args],
        capture_output=True, text=True, check=False,
    )


def _mirror_rev(ref: str) -> str:
    """The SHA `ref` names in the bare mirror, or "" when there is no mirror or no such ref."""
    proc = _mirror_git("rev-parse", "--verify", "-q", ref)
    return proc.stdout.strip() if proc is not None and proc.returncode == 0 else ""


def _contains(older: str, newer: str) -> bool:
    proc = _mirror_git("merge-base", "--is-ancestor", older, newer) if older and newer else None
    return proc is not None and proc.returncode == 0


def _pr_list(state: dict, argv: list[str]) -> list[dict]:
    wanted = (_flag(argv, "--state") or "open").upper()
    head = next((a.split("=", 1)[1] for a in argv if a.startswith("--head=")), None)
    return [
        {"number": pr.get("number", i + 1), "headRefName": branch, "headRefOid": pr.get("head", ""),
         "baseRefName": pr.get("base", "develop"), "isCrossRepository": False, "state": pr["state"]}
        for i, (branch, pr) in enumerate(state["prs"].items())
        if (wanted == "ALL" or pr["state"] == wanted) and (head is None or branch == head)
    ]


def _api(state: dict, argv: list[str]) -> object | None:
    endpoint = next(a for a in argv[1:] if a.startswith("repos/"))
    parts = endpoint.split("?", 1)[0].split("/")
    fields = dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv[:-1]) if a == "-f")
    if len(parts) == 3:
        return {"default_branch": "main"}
    if parts[3:] == ["branches"]:
        return []
    if parts[3:] == ["activity"]:
        branch = fields.get("ref", "").removeprefix("refs/heads/")
        return [{"timestamp": t, "ref": "refs/heads/" + branch} for t in state.get("activity", {}).get(branch, [])]
    return None


def main(argv: list[str]) -> int:
    path = os.environ["GH_E2E_STATE"]
    state: dict = {"prs": {}, "releases": {}}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
    state.setdefault("prs", {})
    state.setdefault("releases", {})
    with open(os.environ.get("GH_E2E_LOG", os.devnull), "a", encoding="utf-8") as log:
        log.write(json.dumps(argv) + "\n")
    is_api = argv[:1] == ["api"] and any(a.startswith("repos/") for a in argv[1:])
    if "--repo" not in argv and not is_api:
        print("gh stand-in: every call must pass --repo", file=sys.stderr)
        return 1
    head = argv[:2]
    out: object = None
    if is_api:
        out = _api(state, argv)
        if out is None:
            print("gh stand-in: unsupported api endpoint", file=sys.stderr)
            return 1
    elif head == ["pr", "create"]:
        branch = _flag(argv, "--head") or "HEAD"
        number = len(state["prs"]) + 1
        state["prs"][branch] = {
            "number": number,
            "state": "OPEN",
            "base": _flag(argv, "--base") or "develop",
            "head": _mirror_rev(f"refs/heads/{branch}"),
        }
        out = f"https://github.example/{_flag(argv, '--repo')}/pull/{number}"
    elif head == ["pr", "merge"]:
        branch = argv[2]
        if branch not in state["prs"]:
            print("no pull request for that branch", file=sys.stderr)
            return 1
        pr = state["prs"][branch]
        pr["state"] = "MERGED"
        tip = _mirror_rev(f"refs/heads/{pr['base']}")
        if tip and _contains(pr.get("head", ""), tip):
            pr["merge_commit"] = tip
    elif head == ["pr", "view"]:
        pr = state["prs"].get(argv[2])
        if pr is None:
            print(f'no pull requests found for branch "{argv[2]}"', file=sys.stderr)
            return 1
        out = {"state": pr["state"], "headRefOid": pr.get("head", "")}
        if pr.get("merge_commit"):
            out["mergeCommit"] = {"oid": pr["merge_commit"]}
    elif head == ["pr", "checks"]:
        if argv[2] not in state["prs"]:
            print(f'no pull requests found for branch "{argv[2]}"', file=sys.stderr)
            return 1
        out = [{"name": "ci", "bucket": "pass"}]
    elif head == ["pr", "list"]:
        out = _pr_list(state, argv)
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
