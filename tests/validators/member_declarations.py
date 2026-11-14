"""Test-only declared member rules, so tests never read the live v4.15 plan files.

Production keeps every per-member fact in `completion_minor.MEMBER_DECLARATIONS`, keyed by a
member's original plan path and frozen hash. A test that fabricates a plan has a different
path and hash, so it declares its own rows here instead of editing the production table:

    fixture_rules(version, ...)     one row, shaped like a production row, for a fixture plan
    VersionDeclarations             a table that answers by the version prefix of a plan file
                                    name; used when a fixture plan's hash is not known up front
    install(monkeypatch)            patch the in-process table
    apply_to(module)                the same patch for a module a subprocess imported
    write_wrapper(dir)              a wrapper beside a private copy of the scripts
    DECLARED_CHECKER                a wrapper script that applies it in a subprocess, because a
                                    subprocess never sees a monkeypatch
    DECLARED_SCRIPT                 the same wrapper for any other script under scripts/

This module imports no checker code at import time, so a test can load it beside a private
copy of the scripts without pulling in the repository copy. Nothing here is reachable from
production code: the wrapper is a file under `tests/`.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
DECLARED_CHECKER = Path(__file__).with_name("declared_checker.py")
DECLARED_SCRIPT = Path(__file__).with_name("declared_script.py")


def _completion_minor():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import completion_minor

    return completion_minor


def _by_version(rows) -> dict[str, dict]:
    """Production rows by the version prefix of their plan file name."""
    return {Path(row["plan_path"]).name.split("-")[0]: row for row in rows}


def fixture_rules(version: str, *, plan_path: str | None = None, plan_sha256: str | None = None,
                  **overrides: object) -> dict:
    """A declaration row for a fixture plan, copied from the production row of `version`."""
    row = dict(_by_version(_completion_minor()._DECLARED_MEMBER_ROWS)[version])
    row.update(overrides)
    if plan_path is not None:
        row["plan_path"] = plan_path
    if plan_sha256 is not None:
        row["plan_sha256"] = plan_sha256
    return row


class VersionDeclarations(dict):
    """Answers `get((path, sha))` for any fixture plan whose file name starts with a declared version."""

    def __init__(self, rows) -> None:
        super().__init__()
        self._templates = _by_version(rows)
        self._served: dict[tuple[str, str], dict] = {}

    def get(self, key, default=None):  # type: ignore[override]
        path, sha = key
        row = self._templates.get(Path(str(path)).name.split("-")[0])
        if row is None:
            return default
        served = {**row, "plan_path": path, "plan_sha256": sha}
        self._served[(path, sha)] = served
        return served

    def values(self):  # type: ignore[override]
        return [*self._served.values()]


def apply_to(module) -> VersionDeclarations:
    """Point a `completion_minor` module at the version-prefix table of its own production rows."""
    table = VersionDeclarations(module._DECLARED_MEMBER_ROWS)
    module.MEMBER_DECLARATIONS = table
    return table


def write_wrapper(installed: Path) -> Path:
    """Write a checker wrapper next to a private copy of the scripts and return its path."""
    checker = installed / "check_plan_completion.py"
    wrapper = installed / "declared_checker.py"
    wrapper.write_text(
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
        f"sys.path.insert(0, {str(installed)!r})\n"
        "import completion_minor, member_declarations\n"
        "member_declarations.apply_to(completion_minor)\n"
        f"sys.argv[0] = {str(checker)!r}\n"
        f"runpy.run_path({str(checker)!r}, run_name='__main__')\n",
        encoding="utf-8")
    return wrapper


def install(monkeypatch) -> VersionDeclarations:
    module = _completion_minor()
    table = VersionDeclarations(module._DECLARED_MEMBER_ROWS)
    monkeypatch.setattr(module, "MEMBER_DECLARATIONS", table)
    return table
