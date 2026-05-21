"""Installer-internal helpers shared across the registry and the bash / pwsh
installers. Contains primitives that are too cross-cutting to live under any
single integration subclass (e.g., marker-delimited file merges).
"""

from __future__ import annotations

from .instruction_merge import (
    DEFAULT_END_MARKER,
    DEFAULT_START_MARKER,
    merge_marker_section,
    remove_marker_section,
)

__all__ = [
    "DEFAULT_END_MARKER",
    "DEFAULT_START_MARKER",
    "merge_marker_section",
    "remove_marker_section",
]
