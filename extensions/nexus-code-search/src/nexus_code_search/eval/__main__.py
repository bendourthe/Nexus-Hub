"""Allow `python -m nexus_code_search.eval` to invoke the runner."""

from __future__ import annotations

import sys

from nexus_code_search.eval.runner import main

if __name__ == "__main__":
    sys.exit(main())
