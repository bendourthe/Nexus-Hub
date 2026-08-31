"""Host interpreter resolution checks for the interpreters hooks are launched with.

Nexus-Hub registers its hooks as `bash <script>` (and PowerShell siblings). The
assistant host, not Nexus-Hub, performs that launch, so if the host's `bash`
cannot execute a script every hook is silently inert.

The defect this module exists for (v4.3.0 Phase 5): on Windows, `bash` on PATH is
commonly the WSL launcher stub in System32. With no distribution installed it
prints its notice to STDOUT and exits non-zero WITHOUT writing to stderr. A caller
that only inspects stderr sees a silent non-zero child. In the Copilot permission
bridge that meant every guarded tool call was denied with no actionable
diagnostic, which reads as a broken agent rather than a missing interpreter.

`tests/conftest.py` already handled this for the test suite by prepending Git Bash.
Nothing checked it for a real install, and no local gate could observe it, because
the failure depends on how the HOST resolves an interpreter name.

Two consumers share this probe so the rule is stated once:

- `runner.py verify` reports it as a NEEDS-ACTION line, so `nexus-hub doctor`
  turns a silent breakage into an instruction the user can act on.
- `scripts/check_interpreter_resolution.py` runs it as a repository gate.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Probe text chosen so a stub that merely prints a banner cannot pass by accident:
# the probe must reproduce this exact marker on stdout AND exit 0.
_PROBE_MARKER = "nexus-hub-interpreter-ok"
_PROBE_SCRIPT = "printf '%s' '{marker}'\n".format(marker=_PROBE_MARKER)

_WINDOWS_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


@dataclass(frozen=True)
class InterpreterStatus:
    """One interpreter's ability to actually execute a script on this host."""

    name: str
    resolved: str | None
    usable: bool
    detail: str

    @property
    def needs_action(self) -> bool:
        return not self.usable


def _run_probe(interpreter: str, script: Path) -> tuple[bool, str]:
    """Whether `interpreter script` executes and reproduces the probe marker."""
    try:
        completed = subprocess.run(
            [interpreter, str(script)],
            input="",
            text=True,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"could not execute: {exc}"
    if completed.returncode != 0:
        # The WSL stub lands here. Its notice goes to stdout, so a stderr-only
        # report would say nothing at all; include both, trimmed.
        noise = (completed.stderr or completed.stdout or "").strip().splitlines()
        first = noise[0][:160] if noise else "no output"
        return False, f"exited {completed.returncode}: {first}"
    if _PROBE_MARKER not in completed.stdout:
        return False, "ran but did not reproduce the probe output"
    return True, "ok"


def check_bash(*, prefer_git_bash: bool = True) -> InterpreterStatus:
    """Report whether a `bash` that can run a script is reachable on this host."""
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "nexus-probe.sh"
        script.write_text(_PROBE_SCRIPT, encoding="utf-8", newline="\n")

        path_bash = shutil.which("bash")
        if path_bash is not None:
            usable, detail = _run_probe(path_bash, script)
            if usable:
                return InterpreterStatus("bash", path_bash, True, detail)
            path_detail = detail
        else:
            path_detail = "not found on PATH"

        if prefer_git_bash and os.name == "nt":
            for candidate in _WINDOWS_BASH_CANDIDATES:
                if not Path(candidate).is_file():
                    continue
                usable, _ = _run_probe(candidate, script)
                if usable:
                    return InterpreterStatus(
                        "bash",
                        candidate,
                        False,
                        (
                            f"PATH bash is unusable ({path_detail}); a working Git Bash "
                            f"exists at {candidate}. Put its directory ahead of "
                            "System32 on PATH so hooks the host launches as "
                            "`bash <script>` can run."
                        ),
                    )
        return InterpreterStatus("bash", path_bash, False, path_detail)


def check_all() -> list[InterpreterStatus]:
    """Every interpreter Nexus-Hub hook registrations depend on."""
    return [check_bash()]
