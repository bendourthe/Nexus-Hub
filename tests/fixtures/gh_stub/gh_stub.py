"""A `gh` stand-in for completion-checker and runner tests.

Answers the few `gh` calls those tools make from a JSON state file named by
GH_STUB_STATE. It never touches the network. Every call must carry `--repo`,
mirroring the rule that hosting calls are pinned to the approved repository;
a call without it fails, as does any call when the state sets "fail": true
(standing in for offline or unauthenticated). A missing pull request or release
prints real `gh`'s not-found line, or the state's "not_found_stderr" text when set.
A "releases" map ({tag: isDraft}) answers `release view` per tag instead of the
single "release_draft" value.

For the cleanup executor: `pr list` filters the state's "prs" list (dicts with
headRefName, headRefOid, state, isCrossRepository) by `--state` and `--head=`;
`api repos/<owner>/<repo>` answers "default_branch", `.../branches?protected=true`
answers the "protected" names, and `.../activity` with `-f ref=refs/heads/<b>` answers
{"timestamp": ...} entries from "activity" ({branch: [iso times]}). `gh api` takes
no `--repo`, so an `api` call is accepted when its endpoint names `repos/`. A
"merge_commit" value adds `mergeCommit` to `pr view`. "api_fail" fails every
`api` call; "prs_fail" fails every `pr list` call.

For minor-scope fixtures with several pull requests, "pr_by_branch" ({branch: {"state",
"merge_commit", "checks"}}) answers `pr view` and `pr checks` for a listed branch; an
unlisted branch falls back to the single "pr_state" values above. "sleep" (seconds)
delays every call, standing in for a slow host when a budget is under test.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse


def main(argv: list[str]) -> int:
    with open(os.environ["GH_STUB_STATE"], encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("sleep"):
        time.sleep(float(state["sleep"]))
    log = os.environ.get("GH_STUB_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(argv) + "\n")
    is_api = argv[:1] == ["api"] and any(a.startswith("repos/") for a in argv[1:])
    if state.get("fail") or ("--repo" not in argv and not is_api):
        print("gh stub: unavailable", file=sys.stderr)
        return 1
    if is_api:
        fields = dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv[:-1]) if a == "-f")
        return _api(state, next(a for a in argv[1:] if a.startswith("repos/")), fields)
    head = argv[:2]
    missing_pr = state.get("not_found_stderr", f'no pull requests found for branch "{argv[2]}"')
    branch_pr = (state.get("pr_by_branch") or {}).get(argv[2]) if head[:1] == ["pr"] and len(argv) > 2 else None
    if head == ["pr", "view"] and branch_pr is not None:
        answer = {"state": branch_pr.get("state", "OPEN")}
        if "merge_commit" in branch_pr:
            answer["mergeCommit"] = {"oid": branch_pr["merge_commit"]}
        print(json.dumps(answer))
    elif head == ["pr", "checks"] and branch_pr is not None:
        print(json.dumps(branch_pr.get("checks", [])))
    elif head == ["pr", "view"]:
        if "pr_state" not in state:
            print(missing_pr, file=sys.stderr)
            return 1
        answer = {"state": state["pr_state"]}
        if "merge_commit" in state:
            answer["mergeCommit"] = {"oid": state["merge_commit"]}
        print(json.dumps(answer))
    elif head == ["pr", "list"]:
        if state.get("prs_fail"):
            print("gh stub: unavailable", file=sys.stderr)
            return 1
        print(json.dumps(_pr_list(state, argv)))
    elif head == ["pr", "checks"]:
        if "pr_state" not in state:
            print(missing_pr, file=sys.stderr)
            return 1
        if "no_checks_stderr" in state:
            print(state["no_checks_stderr"], file=sys.stderr)
            return 1
        print(json.dumps(state.get("checks", [])))
    elif head == ["release", "view"] and "releases" in state:
        # Per-tag releases ({tag: isDraft}) for minor-scope fixtures with several plans.
        tag = argv[2]
        if tag not in state["releases"]:
            print(state.get("not_found_stderr", "release not found"), file=sys.stderr)
            return 1
        print(json.dumps({"isDraft": state["releases"][tag]}))
    elif head == ["release", "view"]:
        if "release_draft" not in state:
            print(state.get("not_found_stderr", "release not found"), file=sys.stderr)
            return 1
        print(json.dumps({"isDraft": state["release_draft"]}))
    elif head == ["run", "list"]:
        print(json.dumps(state.get("runs", [])))
    else:
        print(f"gh stub: unsupported {head}", file=sys.stderr)
        return 1
    return 0


def _pr_list(state: dict, argv: list[str]) -> list[dict]:
    wanted = argv[argv.index("--state") + 1].upper() if "--state" in argv else "OPEN"
    head = next((a.split("=", 1)[1] for a in argv if a.startswith("--head=")), None)
    return [
        pr for pr in state.get("prs", [])
        if (wanted == "ALL" or pr.get("state") == wanted) and (head is None or pr.get("headRefName") == head)
    ]


def _api(state: dict, endpoint: str, fields: dict[str, str]) -> int:
    if state.get("api_fail"):
        print("gh stub: unavailable", file=sys.stderr)
        return 1
    path, _, query = endpoint.partition("?")
    parts = path.split("/")
    params = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()} | fields
    if len(parts) == 3:
        print(json.dumps({"default_branch": state.get("default_branch", "main")}))
    elif parts[3:] == ["branches"]:
        print(json.dumps([{"name": n, "protected": True} for n in state.get("protected", [])]))
    elif parts[3:] == ["activity"]:
        branch = params.get("ref", "").removeprefix("refs/heads/")
        print(json.dumps([{"timestamp": t, "ref": "refs/heads/" + branch} for t in state.get("activity", {}).get(branch, [])]))
    else:
        print(f"gh stub: unsupported api {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
