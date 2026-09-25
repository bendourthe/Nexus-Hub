#!/usr/bin/env python3
"""Fail when the host's registered hook interpreter cannot run a script.

Repo-internal gate (v4.3.0 Phase 5). POSIX registrations launch Bash scripts;
current Windows registrations launch PowerShell siblings. The assistant HOST
performs that launch, so this gate probes the selected interpreter directly.

That blind spot is not hypothetical. The v4.3.0 integration run was red twice on a
Windows runner for exactly this reason while the full local suite was green, and
the underlying condition (the WSL launcher stub answering to `bash`, printing to
stdout, exiting non-zero with an empty stderr) would have denied every guarded
tool call for a real user with no actionable message.

Advisory by default so a missing selected shell is reported rather than blocked;
`--gate` makes it fail, which is how the repository profiles run it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations._interpreters import check_all  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        action="store_true",
        help="exit non-zero when an interpreter cannot run a script",
    )
    args = parser.parse_args(argv)

    findings = check_all()
    unusable = [status for status in findings if status.needs_action]

    for status in findings:
        if status.usable:
            print(f"[interpreters] OK   {status.name} -> {status.resolved}")
        else:
            print(f"[interpreters] FAIL {status.name}: {status.detail}")

    if not unusable:
        print("[interpreters] every hook interpreter can execute a script.")
        return 0

    print(
        "[interpreters] Hooks using an unusable interpreter would be silently "
        "inert on this host."
    )
    return 1 if args.gate else 0


if __name__ == "__main__":
    raise SystemExit(main())
