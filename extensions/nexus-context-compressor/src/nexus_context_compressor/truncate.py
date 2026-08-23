"""Non-destructive truncation: tee the full blob, then keep a prefix.

Nothing is silently unrecoverable. If the spool file cannot be written, the
original text is returned unchanged.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Truncation:
    text: str
    full_path: Path | None
    first_dropped_line: int | None

    @property
    def truncated(self) -> bool:
        return self.full_path is not None


def spool_dir() -> Path:
    override = os.environ.get("NEXUS_COMPRESSOR_SPOOL_DIR")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "nexus-compressor-full"


def _pointer(path: Path, first_dropped_line: int) -> str:
    return (
        f"[nexus-context-compressor truncated: full={path} "
        f"recover=tail -n +{first_dropped_line} {path}]\n"
    )


def truncate_text(
    text: str,
    *,
    max_lines: int | None = None,
    max_bytes: int | None = None,
) -> Truncation:
    """Keep a prefix of ``text`` and spool the original when anything is dropped."""
    if not text:
        return Truncation(text=text, full_path=None, first_dropped_line=None)

    lines = text.splitlines(keepends=True)
    drop_from_line: int | None = None
    if max_lines is not None and max_lines >= 0 and len(lines) > max_lines:
        drop_from_line = max_lines + 1
        kept = "".join(lines[:max_lines])
    else:
        kept = text

    if max_bytes is not None and max_bytes >= 0:
        encoded = kept.encode("utf-8")
        if len(encoded) > max_bytes:
            kept = encoded[:max_bytes].decode("utf-8", errors="ignore")
            prefix_lines = kept.splitlines(keepends=True)
            drop_from_line = len(prefix_lines) + 1

    if kept == text:
        return Truncation(text=text, full_path=None, first_dropped_line=None)

    try:
        directory = spool_dir()
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=directory,
            prefix="full-",
            suffix=".txt",
        ) as fh:
            fh.write(text)
            path = Path(fh.name)
    except OSError:
        return Truncation(text=text, full_path=None, first_dropped_line=None)

    first = drop_from_line or (kept.count("\n") + 1)
    return Truncation(
        text=_pointer(path, first) + kept,
        full_path=path,
        first_dropped_line=first,
    )


def recovered_tail(original: str, truncation: Truncation) -> str:
    """Return the dropped suffix of ``original`` (empty when nothing was dropped)."""
    if truncation.first_dropped_line is None:
        return ""
    lines = original.splitlines(keepends=True)
    start = truncation.first_dropped_line - 1
    return "".join(lines[start:])
