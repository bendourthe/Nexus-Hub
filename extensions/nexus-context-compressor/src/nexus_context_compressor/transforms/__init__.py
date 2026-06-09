"""Deterministic compression strategies.

Each transform takes content and returns a smaller (or cache-friendlier),
semantically-faithful version, recording any reversible drops in the CCR store.

* ``smart_crusher`` (Phase 1) -- JSON-array dedup with reversible CCR markers.
* ``cache_aligner`` (Phase 3) -- KV-cache prefix stabilization (reorder volatile
  lines to the tail; no drop).
* ``code_compressor`` (Phase 3) -- AST-aware function-body elision, reusing the
  ``nexus-code-search`` tree-sitter extractors, with reversible CCR markers.
* ``content_router`` (Phase 3) -- detect content type and dispatch each segment
  to the strategy that fits.
"""

from __future__ import annotations

from .cache_aligner import AlignResult, CacheAlignerConfig, align
from .code_compressor import (
    CodeCompressorConfig,
    CodeCompressResult,
    ElidedBody,
    compress_code,
)
from .content_router import (
    ContentType,
    RouteResult,
    RouterConfig,
    Segment,
    classify,
    route,
)
from .smart_crusher import (
    CCRSpan,
    CrushResult,
    SmartCrusherConfig,
    smart_crush,
)

__all__ = [
    # smart_crusher
    "smart_crush",
    "SmartCrusherConfig",
    "CrushResult",
    "CCRSpan",
    # cache_aligner
    "align",
    "CacheAlignerConfig",
    "AlignResult",
    # code_compressor
    "compress_code",
    "CodeCompressorConfig",
    "CodeCompressResult",
    "ElidedBody",
    # content_router
    "route",
    "classify",
    "RouterConfig",
    "RouteResult",
    "Segment",
    "ContentType",
]
