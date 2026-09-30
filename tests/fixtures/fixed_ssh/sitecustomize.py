"""Test-only: pin the ssh `repo_host.git_ssh` reports to a fixture's stand-in.

Never shipped: the installers copy nothing from `tests/`. Python imports this module
at startup only when a test puts this directory on PYTHONPATH (see
`launcher.fixed_ssh_env`), so every subprocess the test launches (the checker, the
completion gate, the runner, the cleanup executor) shares one resolver answer.

Why: `repo_host.git_ssh` asks git's own shell which ssh a push runs, and on a
GitHub-hosted Windows runner that shell resolves Git's bundled
`usr/bin/ssh.exe` whatever PATH says. Tests of the ROUTE logic (aliases, Match
blocks, ports, overrides) need a known ssh; they are about what the checker does
with a resolved ssh, not about how the host resolves it. The resolution itself is
proven separately against git's own answer
(`test_git_ssh_matches_what_git_itself_reports`).
"""

from __future__ import annotations

import os
import sys

_SSH = os.environ.get("NEXUS_TEST_FIXED_SSH")
_SCRIPTS = os.environ.get("NEXUS_TEST_SCRIPTS_DIR")

if _SSH and _SCRIPTS:
    if _SCRIPTS not in sys.path:
        sys.path.insert(0, _SCRIPTS)
    import repo_host

    def _fixed_git_ssh(root: object, *, git: str, run: object) -> str:
        return _SSH

    repo_host.git_ssh = _fixed_git_ssh
