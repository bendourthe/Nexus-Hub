"""Build a real executable stand-in for a Python script, for tests that put a fake tool on PATH.

`repo_host.absolute_tool` never resolves a Windows `.cmd` or `.bat`, because cmd.exe
re-parses arguments (a branch named `feat/x&mkdir,pwned` would run a second
command). So a stand-in must be a real executable:

- Windows: `<name>.exe`, built with the console-script launcher pip vendors
  (distlib). The launcher passes argv through CreateProcess unchanged and runs the
  script with this interpreter via `runpy`, so the script file stays the source.
- POSIX: an executable `#!/bin/sh` script, as before.

An extensionless `#!/bin/sh` copy is also written on Windows, for Git Bash callers.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GH_STUB_SCRIPT = HERE / "gh_stub.py"


def _shell(bin_dir: Path, name: str, script: Path, python: str) -> Path:
    path = bin_dir / name
    path.write_text(
        f'#!/bin/sh\nexec "{Path(python).as_posix()}" "{script.as_posix()}" "$@"\n',
        encoding="utf-8",
        newline="\n",
    )
    path.chmod(0o755)
    return path


def make_stub(bin_dir: Path, name: str, script: Path, python: str = sys.executable) -> Path:
    """Write an executable `name` in `bin_dir` that runs `script` with `python`; returns its path."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    shell = _shell(bin_dir, name, script, python)
    if sys.platform != "win32":
        return shell
    from pip._vendor.distlib.scripts import (
        ScriptMaker,  # vendored by pip on every CPython install
    )

    source = Path(tempfile.mkdtemp(prefix="stub-src-"))
    (source / f"{name}.py").write_text(
        "#!python\nimport runpy, sys\n"
        f"sys.argv[0] = {str(script)!r}\n"
        f"runpy.run_path({str(script)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    maker = ScriptMaker(str(source), str(bin_dir), add_launchers=True)
    maker.executable = python
    maker.variants = {""}
    maker.clobber = True
    maker.make(f"{name}.py")
    exe = bin_dir / f"{name}.exe"
    if not exe.is_file():
        raise RuntimeError(f"could not build the {name}.exe stand-in")
    return exe


FIXED_SSH_DIR = HERE.parent / "fixed_ssh"
SCRIPTS_DIR = HERE.parents[2] / "scripts"


def fixed_ssh_env(ssh: Path, environ: dict[str, str]) -> dict[str, str]:
    """Environment entries that make every Python child resolve `ssh` as git's ssh.

    `tests/fixtures/fixed_ssh/sitecustomize.py` replaces `repo_host.git_ssh` in each
    child process when these are set, so a route test does not depend on which ssh
    the host's git shell prefers (a GitHub Windows runner's prefers Git's bundled
    one, whatever PATH says). Production code reads none of them.
    """
    python_path = [str(FIXED_SSH_DIR), *[p for p in environ.get("PYTHONPATH", "").split(os.pathsep) if p]]
    return {
        "PYTHONPATH": os.pathsep.join(python_path),
        "NEXUS_TEST_FIXED_SSH": str(ssh),
        "NEXUS_TEST_SCRIPTS_DIR": str(SCRIPTS_DIR),
    }


_GH_DIR: Path | None = None


def gh_stub_dir() -> Path:
    """A directory holding the `gh` stand-in for tests/fixtures/gh_stub/gh_stub.py (built once)."""
    global _GH_DIR
    if _GH_DIR is None:
        directory = Path(tempfile.mkdtemp(prefix="gh-stub-bin-"))
        make_stub(directory, "gh", GH_STUB_SCRIPT)
        _GH_DIR = directory
    return _GH_DIR
