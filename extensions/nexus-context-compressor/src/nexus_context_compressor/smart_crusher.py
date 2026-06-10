"""Top-level entry point for the SmartCrusher strategy.

The implementation lives in :mod:`nexus_context_compressor.transforms.smart_crusher`
(strategies live under the ``transforms`` subpackage). This thin module re-exports
the public surface and provides the
``python -m nexus_context_compressor.smart_crusher`` entry named in the
adoption-headroom Phase 1 stability gate, so the documented command works
verbatim.
"""

from __future__ import annotations

import sys

from .transforms.smart_crusher import (
    CCRSpan,
    CrushResult,
    SmartCrusherConfig,
    main,
    smart_crush,
)

__all__ = ["smart_crush", "SmartCrusherConfig", "CrushResult", "CCRSpan", "main"]

if __name__ == "__main__":
    sys.exit(main())
