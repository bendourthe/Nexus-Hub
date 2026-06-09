"""Deterministic compression strategies.

Each transform takes content and returns a smaller, semantically-faithful
version, recording any reversible drops in the CCR store. Phase 1 ships the
empty subpackage; ``smart_crusher`` (JSON-array dedup) lands in Phase 1 T003,
and ``cache_aligner`` / ``content_router`` / ``code_compressor`` in Phase 3.
"""

from __future__ import annotations

__all__: list[str] = []
