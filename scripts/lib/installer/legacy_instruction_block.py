"""Report candidate Legacy Instruction Blocks left in an instruction file by an old install.

A candidate is a run of lines OUTSIDE the managed `<!-- NEXUS_HUB_START -->` /
`<!-- NEXUS_HUB_END -->` markers made only of blank lines and exact matches
against `legacy_fingerprints.json` (every line Nexus-Hub ever shipped in an
instruction template or skill index), inside an out-of-marker region that holds
both the historical `# Nexus-Hub Skill Index` heading and a
`**Total: N skills across M categories**` line. A match is NOT proof of
authorship: a user may have typed identical text. This module only reports;
removal belongs to the instruction writer and requires a per-span consent token.

Every non-matching, non-blank line is kept and ends a run, so a user edit
interleaved with legacy text splits it into separate candidates around the kept
line. Results carry the SHA-256 of the bytes read and, per span, a content hash
and a consent hash bound to the resolved target path, the full-file hash, and the
span's byte offsets, so identical text in a second file cannot share consent.
Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .instruction_merge import DEFAULT_END_MARKER, DEFAULT_START_MARKER

FINGERPRINTS = Path(__file__).resolve().parent / "legacy_fingerprints.json"
SCHEMA = 1
MIN_NONBLANK = 3
BOM = b"\xef\xbb\xbf"
_HEADING = re.compile(r"^#\s+Nexus-Hub Skill Index\s*$")
_TOTAL = re.compile(r"^\*\*Total:\s*\d+\s+skills across\s+\d+\s+categories\*\*\s*$")


@dataclass(frozen=True)
class LegacySpan:
    start_line: int  # 1-based, inclusive
    end_line: int  # 1-based, inclusive
    start_byte: int
    end_byte: int  # exclusive
    sha256: str  # hash of the span's bytes (evidence)
    consent_sha256: str  # hash binding path, file state, offsets, and span content
    line_count: int


@dataclass
class LegacyBlockResult:
    status: str  # ok | absent | unreadable | markers-malformed | no-fingerprints
    sha256: str = ""
    managed_span: tuple[int, int] | None = None
    spans: list[LegacySpan] = field(default_factory=list)
    kept_lines: list[int] = field(default_factory=list)


def load_fingerprints(path: Path | None = None) -> set[str] | None:
    """The shipped line-hash set, or None when the file is missing, unreadable, or of an unknown schema."""
    try:
        doc = json.loads((path or FINGERPRINTS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(doc.get("hashes"), list):
        return None
    return set(doc["hashes"])


def line_hash(text: str) -> str:
    return hashlib.sha256(text.rstrip().encode("utf-8")).hexdigest()


def consent_hash(path: Path, file_sha: str, start_byte: int, end_byte: int, span_sha: str) -> str:
    """Unambiguous encoding of target, file state, offsets, and span content."""
    resolved = str(Path(path).resolve())
    payload = json.dumps([resolved, file_sha, start_byte, end_byte, span_sha], separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _split(content: bytes) -> list[tuple[int, int, str]]:
    """(start byte, end byte incl. newline, text without line ending) for every line."""
    lines: list[tuple[int, int, str]] = []
    offset = len(BOM) if content.startswith(BOM) else 0
    while offset < len(content):
        newline = content.find(b"\n", offset)
        end = len(content) if newline == -1 else newline + 1
        raw = content[offset:end].rstrip(b"\n").rstrip(b"\r")
        lines.append((offset, end, raw.decode("utf-8")))
        offset = end
    return lines


def _managed(lines: list[tuple[int, int, str]]) -> tuple[int, int] | None | str:
    """Line indices of the first start and last end marker, None, or 'malformed'."""
    starts = [i for i, (_, _, t) in enumerate(lines) if DEFAULT_START_MARKER in t]
    ends = [i for i, (_, _, t) in enumerate(lines) if DEFAULT_END_MARKER in t]
    if not starts and not ends:
        return None
    if not starts or not ends or ends[-1] < starts[0]:
        return "malformed"
    return starts[0], ends[-1]


def detect_bytes(path: Path, content: bytes, fingerprints: set[str] | None = None) -> LegacyBlockResult:
    file_sha = hashlib.sha256(content).hexdigest()
    try:
        lines = _split(content)
    except UnicodeDecodeError:
        return LegacyBlockResult(status="unreadable", sha256=file_sha)
    managed = _managed(lines)
    if managed == "malformed":
        return LegacyBlockResult(status="markers-malformed", sha256=file_sha)
    known = fingerprints if fingerprints is not None else load_fingerprints()
    if known is None:
        return LegacyBlockResult(status="no-fingerprints", sha256=file_sha)
    result = LegacyBlockResult(status="ok", sha256=file_sha)
    if managed is not None:
        result.managed_span = (managed[0] + 1, managed[1] + 1)
        regions = [range(managed[0]), range(managed[1] + 1, len(lines))]
    else:
        regions = [range(len(lines))]
    for region in regions:
        texts = [lines[i][2] for i in region]
        eligible = any(_HEADING.match(t) for t in texts) and any(_TOTAL.match(t) for t in texts)
        run: list[int] = []
        for i in [*region, None]:
            if i is not None:
                text = lines[i][2]
                if not text.strip() or line_hash(text) in known:
                    run.append(i)
                    continue
                result.kept_lines.append(i + 1)
            if eligible:
                _close_run(path, lines, run, file_sha, result)
            run = []
    return result


def _close_run(path: Path, lines: list[tuple[int, int, str]], run: list[int], file_sha: str,
               result: LegacyBlockResult) -> None:
    while run and not lines[run[0]][2].strip():
        run.pop(0)
    while run and not lines[run[-1]][2].strip():
        run.pop()
    if sum(1 for i in run if lines[i][2].strip()) < MIN_NONBLANK:
        return
    start_byte, end_byte = lines[run[0]][0], lines[run[-1]][1]
    content = b"".join(lines[i][2].encode("utf-8") + b"\n" for i in run)
    span_sha = hashlib.sha256(content).hexdigest()
    result.spans.append(LegacySpan(
        start_line=run[0] + 1, end_line=run[-1] + 1, start_byte=start_byte, end_byte=end_byte,
        sha256=span_sha, consent_sha256=consent_hash(path, file_sha, start_byte, end_byte, span_sha),
        line_count=len(run),
    ))


def detect(path: Path, fingerprints: set[str] | None = None) -> LegacyBlockResult:
    path = Path(path)
    if not path.exists():
        return LegacyBlockResult(status="absent")
    try:
        content = path.read_bytes()
    except OSError:
        return LegacyBlockResult(status="unreadable")
    return detect_bytes(path, content, fingerprints)


__all__ = ["LegacyBlockResult", "LegacySpan", "consent_hash", "detect", "detect_bytes", "line_hash", "load_fingerprints"]
