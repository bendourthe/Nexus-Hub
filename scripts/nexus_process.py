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


def _is_tty(stream: object) -> bool:
    try:
        return bool(stream.isatty())  # type: ignore[attr-defined]
    except (AttributeError, OSError, ValueError):
        return False


def has_shareable_console() -> bool:
    """True only when this process owns a visible, interactive console (Windows).

    Both halves are required. ``GetConsoleWindow`` is non-zero only when a console
    window exists (a host launched with CREATE_NO_WINDOW, or detached, reports
    zero), and a TTY stdin and stdout prove a person is on the other end rather
    than a pipe an agent or IDE reads. Anywhere else the answer is False and the
    caller keeps the windowless default.
    """
    if os.name != "nt":
        return False
    try:
        import ctypes

        window = ctypes.windll.kernel32.GetConsoleWindow()  # type: ignore[attr-defined]
    except (AttributeError, ImportError, OSError):
        return False
    return bool(window) and _is_tty(sys.stdin) and _is_tty(sys.stdout)


def _original_popen_init() -> object:
    """The Popen initializer beneath every layer of the Nexus no-window default."""
    init = subprocess.Popen.__init__
    while getattr(init, "_nexus_no_window", False) and hasattr(init, "__wrapped__"):
        init = init.__wrapped__
    return init


def _launch_in_current_console(args: object, env: dict[str, str] | None, cwd: object) -> int:
    class SharedConsolePopen(subprocess.Popen):
        def __init__(self, *a: object, **k: object) -> None:
            _original_popen_init()(self, *a, **k)

    # No creationflags: the child attaches to this process's console, so its
    # host output, progress bars and prompts appear where the person is looking.
    with SharedConsolePopen(args, env=env, cwd=cwd) as process:  # nexus: console-window-ok child shares the visible console this process already owns
        return process.wait()


def run_in_current_console(
    args: object, *, env: dict[str, str] | None = None, cwd: object = None
) -> subprocess.CompletedProcess:
    """Run a child attached to this process's console, when one is visible.

    This is the one sanctioned exception to the no-window default, for a long
    interactive child whose own output must reach the person (the upgrade
    bootstrap). A child started with CREATE_NO_WINDOW gets a private hidden
    console, so its host output and progress bar are invisible and any prompt
    waits unseen. The exception applies only when ``has_shareable_console`` is
    true. In every other case, including every non-Windows host, this is a plain
    ``subprocess.run`` under the normal default, which forwards output through
    the current streams. It never detaches or opens a new console, and it accepts
    no stream, flag or capture options, so it cannot be used to relax the policy
    for any other kind of launch.
    """
    if not has_shareable_console():
        return subprocess.run(args, env=env, cwd=cwd, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if not isinstance(args, (list, tuple)) or not args:
        raise ValueError("run_in_current_console needs a non-empty argument list")
    returncode = _launch_in_current_console(_batch_command(args, env), env, cwd)
    return subprocess.CompletedProcess(args, returncode)
