"""Test configuration for nexus-skill-scanner.

Adds the ``src/`` layout to ``sys.path`` so the suite runs whether or not the
package has been ``pip install -e``'d (the other internal MCP packages are
installed in CI; this keeps a bare ``cd extensions/nexus-skill-scanner &&
pytest`` working locally too).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
SRC = PKG_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Repo root is four levels up: extensions/nexus-skill-scanner/tests -> repo.
REPO_ROOT = PKG_ROOT.parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def malicious_skill() -> Path:
    return FIXTURES / "malicious-skill"


@pytest.fixture
def clean_skill() -> Path:
    return FIXTURES / "clean-skill"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
