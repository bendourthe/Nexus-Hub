"""Route only the stub fixture's Git transport to its disposable bare mirror."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    command = [os.environ["E2E_REAL_GIT"]]
    if "push" in args or "ls-remote" in args:
        mirror = Path(os.environ["E2E_STUB_REMOTE_MIRROR"]).resolve().as_uri()
        command += ["-c", f"url.{mirror}.insteadOf=https://github.com/acme/demo.git"]
    return subprocess.run([*command, *args], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
