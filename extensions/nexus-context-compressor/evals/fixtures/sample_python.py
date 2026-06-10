"""Sample Python module fixture for the compression accuracy harness.

Side-effect-free on import: this file contains only definitions, so collecting
or importing it is harmless. The harness reads it as *text* and runs the
CodeCompressor over it -- it is never executed. Each function/method body is
deliberately at least ``ccr_min_lines`` non-blank lines long so the compressor
elides it behind a reversible ``<<ccr:HASH N_rows>>`` marker, which exercises
the code-body CCR round-trip in the eval.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Runtime configuration carried between the loader and the service."""

    name: str
    retries: int
    verbose: bool


def load_config(path: str) -> Config:
    """Read a JSON config file from disk and build a Config.

    The body is several lines long on purpose so CodeCompressor elides it
    behind a CCR marker rather than leaving it inline.
    """
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    name = raw.get("name", "default")
    retries = int(raw.get("retries", 3))
    verbose = bool(raw.get("verbose", False))
    return Config(name=name, retries=retries, verbose=verbose)


class Service:
    """A small service with a couple of multi-line methods."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.calls = 0
        self.errors = 0
        self.last_path = None

    def process(self, payload: dict) -> dict:
        """Normalize one payload and return the enriched result."""
        self.calls += 1
        result = dict(payload)
        result["service"] = self.config.name
        result["ok"] = True
        return result

    def shutdown(self) -> None:
        """Reset counters and clear the active-service marker."""
        self.calls = 0
        self.errors = 0
        self.last_path = None
        os.environ.pop("SERVICE_ACTIVE", None)
