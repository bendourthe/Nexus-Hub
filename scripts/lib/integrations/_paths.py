"""Path helpers shared by the integration modules, importing nothing from them.

``long_path`` lived in ``base.py``. ``base`` imports ``manifest``, and
``manifest`` and ``legacy`` need ``long_path``, so they imported ``base`` from
inside functions to avoid a cycle, which static analysis still reports. Here it
depends on the standard library only; ``base`` re-exports it, so
``from .base import long_path`` keeps working.
"""

from __future__ import annotations

import os
from pathlib import Path

_EXTENDED_PREFIX = "\\\\?\\"


def long_path(path: Path) -> Path:
    """Return ``path`` in Windows extended-length form; unchanged elsewhere.

    Windows rejects a path over 260 characters (MAX_PATH) unless the host enabled
    the LongPathsEnabled policy, so a flattened skill's nested bundled files can
    fail to copy into a deep repository with WinError 3 (AR-11). The ``\\\\?\\``
    prefix lifts the limit per call. It also disables Win32 normalization, which
    is why the path is made absolute and backslash-separated first. Only the file
    operations use this form; manifests and reports keep the plain path.
    """
    if os.name != "nt":
        return path
    text = str(path)
    if text.startswith(_EXTENDED_PREFIX):
        return path
    absolute = os.path.abspath(text)
    if absolute.startswith("\\\\"):
        return Path(_EXTENDED_PREFIX + "UNC\\" + absolute[2:])
    return Path(_EXTENDED_PREFIX + absolute)


__all__ = ["long_path"]
