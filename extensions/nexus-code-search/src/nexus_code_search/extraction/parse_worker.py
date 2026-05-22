"""Single-file tree-sitter parser dispatch.

Kept separate from `orchestrator.py` so a future revision can run extraction
in a multiprocessing Pool: each worker imports `parse_file` directly and
returns plain (Node, Edge) tuples that pickle cleanly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nexus_code_search.types import Edge, Node

logger = logging.getLogger("nexus-code-search")


def parse_file(file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
    """Parse `source` (bytes) using the extractor registered for its suffix.

    Returns `([], [])` when no extractor is registered, when tree-sitter raises,
    or when the file is empty. Never raises - callers can map over a file list
    and rely on empty results to mean "nothing extracted, move on."
    """
    if not source:
        return [], []

    from nexus_code_search.extraction.languages import LANGUAGE_EXTRACTORS

    ext = file_path.suffix.lower()
    extractor_cls = LANGUAGE_EXTRACTORS.get(ext)
    if extractor_cls is None:
        return [], []

    try:
        extractor = extractor_cls()
        return extractor.extract(file_path, source)
    except Exception:  # noqa: BLE001
        logger.debug("Extractor failed for %s", file_path, exc_info=True)
        return [], []
