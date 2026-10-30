"""Shared Windows subprocess policy for Nexus-Hub commands and pytest roots.

Install once before launching children. Pipes capture output; CREATE_NO_WINDOW
prevents console allocation from displaying a window, including from a host
that has no console. Safe process-group flags are preserved.
"""
from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys

NO_WINDOW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def _batch_command(argv: object, env: dict[str, str] | None = None) -> object:
    """Launch a batch shim through a hidden cmd, with literal quoted arguments."""
    if not isinstance(argv, (list, tuple)) or not argv:
        return argv
    program = os.fsdecode(argv[0])
    resolved = shutil.which(program, path=(env or os.environ).get("PATH")) or program
    if not resolved.lower().endswith((".cmd", ".bat")):
        return argv
    # Delayed expansion is disabled below so exclamation marks remain literal.
    values = [resolved, *(os.fsdecode(value) for value in argv[1:])]
    if any(any(char in value for char in '\0\r\n"%') for value in values):
        raise ValueError("Batch shim arguments cannot contain quotes, percent expansion, or control characters")
    # Native programs behind .cmd shims parse a trailing slash before a quote.
    def quote(value: str) -> str:
        trailing = len(value) - len(value.rstrip("\\"))
        return '"' + value + "\\" * trailing + '"'

    command = " ".join(quote(value) for value in values)
    prefix = subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/v:off", "/c"])
    return prefix + ' "' + command + '"'


def install_no_window_default() -> bool:
    """Apply the policy to all subprocess APIs without changing their signatures."""
    if os.name != "nt" or getattr(subprocess.Popen.__init__, "_nexus_console_policy", None) == 2:
        return False
    original = subprocess.Popen.__init__

    @functools.wraps(original)
    def init(self, *args: object, **kwargs: object) -> None:
        # Popen's positional prefix through creationflags is stable on supported
        # Python versions. Bind it explicitly so older generic *args wrappers
        # cannot hide the creationflags parameter from inspect.signature.
        positional = list(args)

        def get(index, name, default=None):
            return positional[index] if len(positional) > index else kwargs.get(name, default)

        def put(index, name, value):
            if len(positional) > index:
                positional[index] = value
            else:
                kwargs[name] = value

        flags = get(13, "creationflags", 0) or 0
        forbidden = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_CONSOLE  # nexus: console-window-ok reject both flags
        if flags & forbidden:
            raise ValueError("Console launches must use CREATE_NO_WINDOW, without detachment or a new console")
        put(13, "creationflags", flags | subprocess.CREATE_NO_WINDOW)
        if not get(8, "shell", False):
            put(0, "args", _batch_command(get(0, "args"), get(10, "env")))
        # CREATE_NO_WINDOW does not allocate console handles. Preserve forwarding
        # through the current streams, including an outer CLI captured by pipes.
        for index, name in ((3, "stdin"), (4, "stdout"), (5, "stderr")):
            if get(index, name) is None:
                stream = getattr(sys, name, None)
                try:
                    stream.fileno()
                except (AttributeError, OSError, ValueError):
                    continue
                put(index, name, stream)
        original(self, *positional, **kwargs)

    init._nexus_no_window = True
    init._nexus_console_policy = 2
    subprocess.Popen.__init__ = init
    return True
