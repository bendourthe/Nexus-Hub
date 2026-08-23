"""Relocatable store root and per-store tunables.

The default root is a local, user-scoped path. ``NEXUS_MEMORY_ROOT``
overrides it so the store can sit in a synced folder or a git repository.
The read budget is a reading budget: changing it never recomputes stored
data.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

ENV_ROOT = "NEXUS_MEMORY_ROOT"
CONFIG_NAME = "config.json"

# Transport paging defaults match docs/policy/output-truncation-limits.md
# (Phase 1 safe default). Duplicated here so the extension does not import
# repo-level scripts at runtime.
DEFAULT_PAGE_MAX_BYTES = 20_000
DEFAULT_PAGE_MAX_LINES = 256

DEFAULT_RECORD_WIDTH = 1024
DEFAULT_MAX_ENTRY_LENGTH = 512
DEFAULT_READ_BUDGET = 200


@dataclass(frozen=True)
class StoreConfig:
    """Per-store tunables. ``record_width`` is sticky once a log exists."""

    record_width: int = DEFAULT_RECORD_WIDTH
    max_entry_length: int = DEFAULT_MAX_ENTRY_LENGTH
    read_budget: int = DEFAULT_READ_BUDGET
    page_max_bytes: int = DEFAULT_PAGE_MAX_BYTES
    page_max_lines: int = DEFAULT_PAGE_MAX_LINES

    def validate(self) -> None:
        if self.record_width < 32:
            raise ValueError(f"record_width must be >= 32, got {self.record_width}")
        if self.max_entry_length < 1:
            raise ValueError("max_entry_length must be >= 1")
        if self.max_entry_length + 4 > self.record_width:
            raise ValueError(
                "max_entry_length plus the 4-byte length prefix must fit "
                f"in record_width ({self.record_width})"
            )
        if self.read_budget < 1:
            raise ValueError("read_budget must be >= 1")
        if self.page_max_bytes < 1 or self.page_max_lines < 1:
            raise ValueError("paging limits must be >= 1")


def default_store_root() -> Path:
    """Return the user-scoped default, or ``NEXUS_MEMORY_ROOT`` when set.

    The default is never a project directory.
    """
    override = os.environ.get(ENV_ROOT, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".nexus-hub" / "memory"


def load_config(root: Path) -> StoreConfig:
    """Load ``config.json`` from *root*, or return defaults if it is absent."""
    path = Path(root) / CONFIG_NAME
    if not path.is_file():
        cfg = StoreConfig()
        cfg.validate()
        return cfg
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    cfg = StoreConfig(
        record_width=int(raw.get("record_width", DEFAULT_RECORD_WIDTH)),
        max_entry_length=int(raw.get("max_entry_length", DEFAULT_MAX_ENTRY_LENGTH)),
        read_budget=int(raw.get("read_budget", DEFAULT_READ_BUDGET)),
        page_max_bytes=int(raw.get("page_max_bytes", DEFAULT_PAGE_MAX_BYTES)),
        page_max_lines=int(raw.get("page_max_lines", DEFAULT_PAGE_MAX_LINES)),
    )
    cfg.validate()
    return cfg


def save_config(root: Path, config: StoreConfig) -> None:
    """Write *config* to ``<root>/config.json`` as UTF-8 JSON."""
    config.validate()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CONFIG_NAME
    payload = json.dumps(asdict(config), indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
