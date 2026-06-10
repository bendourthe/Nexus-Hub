"""Allow ``python -m evals`` (from the package root) to run the harness/gate."""

from __future__ import annotations

import sys

from evals.runner import main

if __name__ == "__main__":
    sys.exit(main())
