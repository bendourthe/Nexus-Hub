"""A `gh` stand-in for completion-checker and runner tests.

Answers the few `gh` calls those tools make from a JSON state file named by
GH_STUB_STATE. It never touches the network. Every call must carry `--repo`,
mirroring the rule that hosting calls are pinned to the approved repository;
a call without it fails, as does any call when the state sets "fail": true
(standing in for offline or unauthenticated). A missing pull request or release
prints real `gh`'s not-found line, or the state's "not_found_stderr" text when set.
"""

from __future__ import annotations

import json
import os
import sys


def main(argv: list[str]) -> int:
    with open(os.environ["GH_STUB_STATE"], encoding="utf-8") as handle:
        state = json.load(handle)
    log = os.environ.get("GH_STUB_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(argv) + "\n")
    if state.get("fail") or "--repo" not in argv:
        print("gh stub: unavailable", file=sys.stderr)
        return 1
    head = argv[:2]
    missing_pr = state.get("not_found_stderr", f'no pull requests found for branch "{argv[2]}"')
    if head == ["pr", "view"]:
        if "pr_state" not in state:
            print(missing_pr, file=sys.stderr)
            return 1
        print(json.dumps({"state": state["pr_state"]}))
    elif head == ["pr", "checks"]:
        if "pr_state" not in state:
            print(missing_pr, file=sys.stderr)
            return 1
        print(json.dumps(state.get("checks", [])))
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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
