"""Local passthrough log: commands whose output entered the compressor unchanged.

Fail-soft. Opt-in path via ``NEXUS_COMPRESSOR_PASSTHROUGH_LOG``, else a sibling
of the CCR store, else ``~/.nexus-hub/compressor-passthrough.jsonl``. This is the
read-only data source session-query and continuous-learning mine for unrealized
compression savings. No outbound I/O.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def log_path() -> Path:
    override = os.environ.get("NEXUS_COMPRESSOR_PASSTHROUGH_LOG")
    if override:
        return Path(override)
    ccr = os.environ.get("NEXUS_CCR_STORE_PATH")
    if ccr:
        return Path(ccr).with_name("passthrough.jsonl")
    return Path.home() / ".nexus-hub" / "compressor-passthrough.jsonl"


def record_passthrough(*, tokens: int, bytes_in: int) -> None:
    if tokens <= 0:
        return
    path = log_path()
    line = json.dumps(
        {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kind": "passthrough",
            "tokens": tokens,
            "bytes": bytes_in,
        },
        separators=(",", ":"),
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        return
