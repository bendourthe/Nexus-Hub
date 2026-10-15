#!/usr/bin/env python3
"""Flatten a yt-dlp json3 caption file into clean raw text.

Find the first ``*.json3`` in the given directory (default: cwd), join every
caption ``utf8`` fragment, unescape HTML entities, collapse whitespace, and
write a sibling ``.txt``. Standard library only; no network call, no secrets.
"""

from __future__ import annotations

import glob
import html
import json
import re
import sys
from pathlib import Path


def flatten(out_dir: Path) -> Path:
    """Flatten the first json3 caption file in ``out_dir`` to a sibling .txt."""
    matches = sorted(glob.glob(str(out_dir / "*.json3")))
    if not matches:
        raise SystemExit(f"no json3 caption file found in {out_dir}")
    src = Path(matches[0])
    data = json.loads(src.read_text(encoding="utf-8"))
    parts: list[str] = [
        seg.get("utf8", "")
        for event in data.get("events", [])
        for seg in (event.get("segs") or [])
    ]
    flat = re.sub(r"\s+", " ", html.unescape("".join(parts))).strip()
    dest = src.with_suffix(".txt")
    dest.write_text(flat, encoding="utf-8")
    print(dest)
    return dest


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    flatten(target)
