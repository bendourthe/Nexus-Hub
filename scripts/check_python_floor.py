"""Check tracked Python source against the repository's Python 3.11 CI floor."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOOR = (3, 11)


def _check_paths_on_floor(paths: list[Path]) -> list[str]:
    """Parse source in a Python 3.11 process, never an emulated grammar mode."""
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            failures.append(f"{path}: {exc}")
    return failures


def _floor_interpreter() -> str:
    for candidate in (sys.executable, shutil.which("python3.11")):
        if candidate is None:
            continue
        result = subprocess.run(
            [candidate, "-c", "import sys; print(sys.version_info[:2] == (3, 11))"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip() == "True":
            return candidate
    raise RuntimeError("Python 3.11 is required; install it and expose python3.11 on PATH")


def check_paths(paths: list[Path]) -> list[str]:
    """Return failures from an actual Python 3.11 interpreter."""
    result = subprocess.run(
        [_floor_interpreter(), __file__, "--worker"],
        input="\0".join(str(path) for path in paths).encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return [entry for entry in result.stdout.decode("utf-8").split("\0") if entry]


def main() -> int:
    if sys.argv[1:] == ["--worker"]:
        if sys.version_info[:2] != FLOOR:
            print("Python 3.11 worker required", file=sys.stderr)
            return 2
        paths = [Path(name) for name in sys.stdin.buffer.read().decode("utf-8").split("\0") if name]
        sys.stdout.buffer.write("\0".join(_check_paths_on_floor(paths)).encode("utf-8"))
        return 0
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    )
    paths = [ROOT / name for name in result.stdout.decode("utf-8").split("\0") if name]
    try:
        failures = check_paths(paths)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        print(f"Python 3.11 grammar: {len(failures)} of {len(paths)} tracked files failed", file=sys.stderr)
        return 1
    print(f"Python 3.11 grammar: {len(paths)} tracked files passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
