"""Test configuration for nexus-context-compressor.

Adds the ``src/`` layout to ``sys.path`` so the suite runs whether or not the
package has been ``pip install -e``'d (mirrors nexus-skill-scanner's conftest,
keeping a bare ``cd extensions/nexus-context-compressor && pytest`` working).
"""

from __future__ import annotations

import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[3] / "scripts" / "nexus_process.py"))
CHILD_CONSOLES_HIDDEN = _PROCESS_POLICY["install_no_window_default"]()

import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
SRC = PKG_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Also expose the package root so the top-level ``evals/`` harness package
# (sibling of src/ and tests/, added in Phase 5) imports cleanly in the eval
# tests without an install: ``from evals.runner import ...``.
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

# Repo root is three levels up: extensions/nexus-context-compressor/tests -> repo.
REPO_ROOT = PKG_ROOT.parents[1]
