#!/usr/bin/env python3
"""Fail when an interpreter Nexus-Hub hooks are launched with cannot run a script.

Repo-internal gate (v4.3.0 Phase 5). Nexus-Hub registers its hooks as
`bash <script>`; the assistant HOST performs that launch. If the host's `bash`
cannot execute a script, every hook is silently inert and no other check notices,
because every existing gate runs Python directly rather than through the
interpreter the hooks actually use.

That blind spot is not hypothetical. The v4.3.0 integration run was red twice on a
Windows runner for exactly this reason while the full local suite was green, and
the underlying condition (the WSL launcher stub answering to `bash`, printing to
stdout, exiting non-zero with an empty stderr) would have denied every guarded
tool call for a real user with no actionable message.

Advisory by default so a contributor without Git Bash is told rather than blocked;
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
        "[interpreters] A hook registered as `bash <script>` would not run on this "
        "host. Hooks would be silently inert rather than reporting an error."
    )
    return 1 if args.gate else 0


if __name__ == "__main__":
    raise SystemExit(main())
