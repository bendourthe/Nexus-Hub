"""`ssh` stand-in for the minor scenario: `ssh -G [-p port] [user@]host` answers like OpenSSH.

SSH_E2E_HOSTS maps an alias to its hostname (the fixture's `github-work` alias to
`github.com`), so the checker resolves the SSH-alias remote to its repository the
way it does with a real `~/.ssh/config` Host block. Any other use exits 255: the
fixture's transport never reaches ssh, because git_e2e.py routes it to the mirror.
"""

from __future__ import annotations

import json
import os
import sys


def main(argv: list[str]) -> int:
    if "-G" not in argv or not argv:
        print("ssh stand-in: only -G is supported", file=sys.stderr)
        return 255
    hosts = json.loads(os.environ.get("SSH_E2E_HOSTS", "{}"))
    host = argv[-1].rsplit("@", 1)[-1]
    print("user git")
    print("hostname " + hosts.get(host, host))
    print("port " + (argv[argv.index("-p") + 1] if "-p" in argv else "22"))
    print("proxycommand none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
