"""Route only the stub fixture's Git transport to its disposable bare mirror.

Every URL the fixture advertises for origin (E2E_STUB_REMOTE_URLS, space-separated;
the per-plan scenario's https URL by default, the minor scenario's SSH alias) is
rewritten to the mirror for transport commands only, so a config read still reports
the advertised remote and the checker verifies that route, not the mirror.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

TRANSPORT = ("push", "fetch", "ls-remote")


def main() -> int:
    args = sys.argv[1:]
    log = os.environ.get("E2E_GIT_LOG")
    if log:
        # Every git call any process makes during the run, so a test can assert no forcing flag.
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(args) + "\n")
    command = [os.environ["E2E_REAL_GIT"]]
    if any(a in TRANSPORT for a in args):
        mirror = Path(os.environ["E2E_STUB_REMOTE_MIRROR"]).resolve().as_uri()
        for url in os.environ.get("E2E_STUB_REMOTE_URLS", "https://github.com/acme/demo.git").split():
            command += ["-c", f"url.{mirror}.insteadOf={url}"]
    return subprocess.run([*command, *args], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
