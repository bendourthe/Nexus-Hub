"""The Nexus-Hub managed-block markers, shared by the merge owner and the detector.

A separate leaf module so `instruction_merge` (which uses the detector) and
`legacy_instruction_block` (which needs the markers) never import each other.
"""

from __future__ import annotations

DEFAULT_START_MARKER = "<!-- NEXUS_HUB_START -->"
DEFAULT_END_MARKER = "<!-- NEXUS_HUB_END -->"

__all__ = ["DEFAULT_END_MARKER", "DEFAULT_START_MARKER"]
