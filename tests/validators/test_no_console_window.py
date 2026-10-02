"""No console windows flash on Windows while Nexus-Hub scripts or tests run.

On Windows a console program started by a process with no visible console opens
a window that takes keyboard focus. A suite that starts thousands of children, or
a detached checker that runs `git` and `gh` many times per call, then flashes
windows for minutes and keeps taking the keyboard from the person at the machine.

These tests start real processes and ask Windows, from inside the child, whether
it has a console window (`GetConsoleWindow`) or any console at all
(`GetConsoleProcessList`). The static test keeps every captured subprocess call
in the checker family on the no-window flag, so a new call cannot bring the
windows back unnoticed.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"
WINDOWS = os.name == "nt"
on_windows = pytest.mark.skipif(not WINDOWS, reason="console windows exist only on Windows")

# Prints the child's console window handle (0 = no window) and how many processes
# share its console (0 = no console at all).
PROBE = (
    "import ctypes; k = ctypes.windll.kernel32; ids = (ctypes.c_uint * 4)(); "
    "print(int(k.GetConsoleWindow() or 0), k.GetConsoleProcessList(ids, 4))"
)


def _probe(**kwargs: object) -> tuple[int, int]:
    out = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True,
                         check=True, timeout=60, **kwargs).stdout.split()
    return int(out[0]), int(out[1])


@on_windows
def test_a_test_child_gets_a_console_without_a_window() -> None:
    window, attached = _probe()
    assert window == 0, "a child started by the suite has a visible console window"
    assert attached >= 1, "the child should still have a (hidden) console"


@on_windows
def test_a_child_that_asks_to_detach_stays_detached() -> None:
    window, attached = _probe(creationflags=subprocess.DETACHED_PROCESS)
    assert (window, attached) == (0, 0)


@on_windows
def test_the_checker_run_from_a_detached_process_opens_no_window() -> None:
    """The real flood: tests detach the checker, and every git or gh it ran got a window."""
    script = (
        "import sys; sys.path.insert(0, sys.argv[1]); import check_plan_completion as ck; "
        f"rc, out, _ = ck._run_with_stderr([sys.executable, '-c', {PROBE!r}], ck.Budget(60)); "
        "print(out.strip())"
    )
    out = subprocess.run([sys.executable, "-c", script, str(SCRIPTS)], capture_output=True, text=True,
                         check=True, timeout=120, stdin=subprocess.DEVNULL,
                         creationflags=subprocess.DETACHED_PROCESS).stdout.split()
    assert int(out[0]) == 0, "a child of the detached checker opened a console window"


CAPTURED = {
    "check_plan_completion.py": 1,
    "minor_close.py": 1,
    "cleanup_merged.py": 1,
    "completion_gate.py": 1,
    "check_release_preconditions.py": 3,
}


@pytest.mark.parametrize(("name", "calls"), sorted(CAPTURED.items()))
def test_every_captured_child_in_the_checker_family_hides_its_window(name: str, calls: int) -> None:
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    bodies = []  # each call's text, from `subprocess.run(` to its matching parenthesis
    for m in re.finditer(r"subprocess\.run\(", text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            if depth == 0:
                break
            i += 1
        bodies.append(text[m.start():i])
    assert len(bodies) == calls, f"{name}: expected {calls} subprocess.run calls, found {len(bodies)}"
    for body in bodies:
        assert "NO_WINDOW" in body, f"{name}: a subprocess.run call does not pass NO_WINDOW:\n{body}"
