"""Put src/ on sys.path so tests run without an editable install."""

from __future__ import annotations

import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[3] / "scripts" / "nexus_process.py"))
CHILD_CONSOLES_HIDDEN = _PROCESS_POLICY["install_no_window_default"]()

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
