"""Path-safety helper codifying the invariant the installer scripts assume.

The bash installer relies on `realpath` and the PowerShell installer relies on
`Resolve-Path` to collapse `..` segments before any write. Both behaviors are
equivalent to `pathlib.Path.resolve()` in Python. This helper makes the
invariant explicit and testable so that the security contract can be exercised
in CI without spinning up a full installer run.

Use `resolve_under(target_root, candidate)` to obtain a resolved absolute path
that is guaranteed to live under `target_root`. Any candidate that escapes the
root (via `..`, an absolute path, a null byte, or a UNC prefix on Windows)
raises `PathTraversalError`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath


class PathTraversalError(ValueError):
    """Raised when a candidate path resolves outside the target root."""


def _has_null_byte(name: str) -> bool:
    return "\x00" in name


def _looks_absolute(name: str) -> bool:
    if not name:
        return False
    if name.startswith(("/", "\\")):
        return True
    if len(name) >= 2 and name[1] == ":" and name[0].isalpha():
        return True
    if name.startswith("\\\\"):
        return True
    return False


def _is_unc(name: str) -> bool:
    return name.startswith("\\\\") or name.startswith("//")


def resolve_under(target_root: Path | str, candidate: str) -> Path:
    """Return the absolute resolved path for `candidate` joined under `target_root`.

    Rejects:
      - empty or whitespace-only candidate
      - candidate containing a null byte
      - candidate that is absolute (POSIX `/`, Windows `C:\\`, UNC `\\\\server\\share`)
      - candidate that, once joined and resolved, would escape `target_root`

    The function does not create or touch the filesystem; it operates purely on
    path math. This makes it safe to call from unit tests.
    """
    if candidate is None:
        raise PathTraversalError("candidate is None")
    if not isinstance(candidate, str):
        raise PathTraversalError(f"candidate is not a string: {type(candidate)!r}")
    if not candidate.strip():
        raise PathTraversalError("candidate is empty or whitespace")
    if _has_null_byte(candidate):
        raise PathTraversalError("candidate contains null byte")
    if _is_unc(candidate):
        raise PathTraversalError(f"candidate is a UNC path: {candidate!r}")
    if _looks_absolute(candidate):
        raise PathTraversalError(f"candidate is an absolute path: {candidate!r}")

    root = Path(target_root).resolve()

    # Reject candidates that contain path separators that would resolve outside
    # the root. We let pathlib do the join+resolve, then check containment.
    joined = (root / candidate).resolve()

    try:
        joined.relative_to(root)
    except ValueError as exc:
        raise PathTraversalError(
            f"resolved path {joined!r} escapes target root {root!r}"
        ) from exc

    return joined


def is_safe_candidate(target_root: Path | str, candidate: str) -> bool:
    """Boolean form of resolve_under -- True iff the candidate would be accepted."""
    try:
        resolve_under(target_root, candidate)
    except PathTraversalError:
        return False
    return True


__all__ = ["PathTraversalError", "resolve_under", "is_safe_candidate"]
