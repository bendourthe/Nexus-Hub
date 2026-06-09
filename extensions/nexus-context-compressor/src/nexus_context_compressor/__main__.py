"""Module entry point: ``python -m nexus_context_compressor``.

Prints package identity and the active token-counting mode (accurate tiktoken
vs. stdlib fallback). Per-strategy entry points (e.g.
``python -m nexus_context_compressor.smart_crusher``) ship with their phases.
"""

from __future__ import annotations

import sys

from . import __version__
from .tokens import using_accurate_counter


def main() -> int:
    mode = "tiktoken" if using_accurate_counter() else "stdlib-fallback"
    print(f"nexus-context-compressor {__version__} (token counter: {mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
