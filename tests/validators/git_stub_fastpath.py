"""Skip the Python git stand-in for commands it forwards unchanged (test-only).

The bridge operations tests put a `git` stand-in on PATH that only intercepts `push`
and `ls-remote` and forwards every other command to the real git. A forwarded call
still costs a launcher, an interpreter start and a second git start, about three
times a plain git start on Windows, and one checker run makes dozens of them.

When BRIDGE_TEST_GIT_STUB (the stand-in) and BRIDGE_TEST_REAL_GIT are set, `Popen`
runs the real git directly for a call that the stand-in would forward as is. The
predicate is the stand-in's own (`push` or `ls-remote` anywhere in the arguments),
so intercepted calls, and every other tool, still reach the stand-in unchanged.
Nothing here is reachable from production code.
"""

from __future__ import annotations

import os
import shutil
import subprocess

INTERCEPTED = frozenset({"push", "ls-remote"})


def _same(path: str, stub: str, cache: dict[str, bool]) -> bool:
    if path not in cache:
        found = path if os.path.dirname(path) else shutil.which(path)
        cache[path] = bool(found) and os.path.normcase(os.path.abspath(found)) == stub
    return cache[path]


def install(setattr_=None) -> bool:
    """Patch `subprocess.Popen.__init__`; `setattr_(obj, name, value)` lets a test undo it."""
    stub, real = os.environ.get("BRIDGE_TEST_GIT_STUB"), os.environ.get(
        "BRIDGE_TEST_REAL_GIT"
    )
    if not stub or not real:
        return False
    stub = os.path.normcase(os.path.abspath(stub))
    original, cache = subprocess.Popen.__init__, {}

    def init(self, args, *rest, **options):
        if (
            isinstance(args, (list, tuple))
            and args
            and isinstance(args[0], (str, os.PathLike))
        ):
            first = os.fspath(args[0])
            if _same(first, stub, cache) and not INTERCEPTED & set(map(str, args[1:])):
                args = [real, *args[1:]]
        original(self, args, *rest, **options)

    (setattr_ or setattr)(subprocess.Popen, "__init__", init)
    return True
