"""Markdown fenced-code awareness.

A producer catalog like Nexus-Hub legitimately contains dangerous-looking
constructs (``eval(``, "ignore previous instructions", ``password = "..."``)
inside fenced code blocks that *teach* security rather than execute it. The
text analyzers must know whether a given line sits inside a fenced block so
low-confidence patterns can be suppressed there.

The fence tracker follows the same CommonMark rule used by
``scripts/validate_skills.py`` (the v2.4.0 secret-scanner nuance, BG-v23-1):
an opening fence may carry an info string, but a CLOSING fence must use the
same fence character, be at least as long, and carry NO info string. A
fence-looking line that is not a valid closer while already inside a fence is
treated as block content. Reusing the exact rule keeps the two surfaces
consistent.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

# A fenced-code delimiter: 3+ backticks or 3+ tildes, optionally indented,
# optionally followed by an info string (only on the OPENING fence).
_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def iter_lines_with_fence(text: str) -> Iterator[tuple[int, str, bool]]:
    """Yield ``(line_no, line, in_fence)`` for every line of ``text``.

    ``in_fence`` is True for lines that are inside a fenced code block. The
    fence-delimiter lines themselves are reported with the state they
    transition *into* an irrelevant detail for callers, which only use the
    flag to decide whether to suppress a low-confidence pattern.
    """
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        m = _FENCE_RE.match(line)
        if m:
            fence = m.group("fence")
            info = m.group("info").strip()
            char = fence[0]
            if not in_fence:
                in_fence, fence_char, fence_len = True, char, len(fence)
                yield line_no, line, True
                continue
            if char == fence_char and len(fence) >= fence_len and not info:
                in_fence, fence_char, fence_len = False, "", 0
                yield line_no, line, False
                continue
            # fence-looking content inside an open fence: still inside.
            yield line_no, line, True
            continue
        yield line_no, line, in_fence
