"""Module entry point: ``python -m nexus_skill_scanner <target> ...``."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
