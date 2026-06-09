"""Test configuration for nexus-context-compressor.

Adds the ``src/`` layout to ``sys.path`` so the suite runs whether or not the
package has been ``pip install -e``'d (mirrors nexus-skill-scanner's conftest,
keeping a bare ``cd extensions/nexus-context-compressor && pytest`` working).
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
SRC = PKG_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Repo root is three levels up: extensions/nexus-context-compressor/tests -> repo.
REPO_ROOT = PKG_ROOT.parents[1]
