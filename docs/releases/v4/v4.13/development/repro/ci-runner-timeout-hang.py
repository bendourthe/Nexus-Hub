"""Repro for QG-3: scripts/ci/run.py cannot bound a step that spawns a process tree.

`run_command` bounds every CI step with
`subprocess.run(capture_output=True, timeout=cmd.timeout)`. That bound does not
hold when the step's own tests spawn surviving descendants, which the installer
tests do. On timeout, `subprocess.run` kills the direct child and then calls
`communicate()` a SECOND time with no timeout to reap it. Killing a child does
not kill its descendants on Windows, so a grandchild holding the inherited
stdout pipe keeps it open, EOF never arrives, and that second call blocks
permanently.

Observed consequence: `python scripts/ci/run.py --profile full --only tests`
reached 340 minutes without printing a single step result, against a combined
cap of 105 minutes (hook-tests 1800s + repo-tests 4500s).

Run it:

    python docs/releases/v4/v4.13/development/repro/ci-runner-timeout-hang.py

Exit 1 and "VERDICT: HUNG" reproduces the defect. Exit 0 means the bound holds
on this host and the diagnosis needs revisiting. The repro hard-caps itself with
a daemon thread, so it never hangs its own caller.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import threading
import time

# The child spawns a grandchild that inherits stdout and outlives it. This is
# the shape of an installer test, reduced to the part that matters.
CHILD = textwrap.dedent(
    """
    import subprocess, sys, time
    subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        stdout=sys.stdout, stderr=sys.stderr,
    )
    print("child spawned grandchild and is exiting", flush=True)
    time.sleep(120)
    """
).strip()

CHILD_TIMEOUT_S = 5
OBSERVE_S = 30

result: dict[str, object] = {}


def run_it() -> None:
    started = time.monotonic()
    try:
        subprocess.run(
            [sys.executable, "-c", CHILD],
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT_S,
        )
        result["outcome"] = "returned normally"
    except subprocess.TimeoutExpired:
        result["outcome"] = "TimeoutExpired raised"
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic, report anything
        result["outcome"] = f"{type(exc).__name__}: {exc}"
    result["elapsed"] = round(time.monotonic() - started, 1)


def main() -> int:
    worker = threading.Thread(target=run_it, daemon=True)
    worker.start()
    worker.join(timeout=OBSERVE_S)

    if worker.is_alive():
        print("VERDICT: HUNG.")
        print(f"  timeout={CHILD_TIMEOUT_S} did not return after {OBSERVE_S}s.")
        print("  The post-kill communicate() is blocked on a pipe still held by")
        print("  the surviving grandchild.")
        print("  => scripts/ci/run.py cannot bound a step that spawns a process tree.")
        return 1

    print(f"VERDICT: bounded. {result['outcome']} after {result['elapsed']}s")
    print("  => the timeout holds even with a surviving grandchild on this host.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
