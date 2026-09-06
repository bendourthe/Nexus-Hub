"""Page agent-consumed script output so it survives CLI truncation.

These are TRANSPORT limits, not content limits. They exist so a single
tool-call payload is not silently truncated by a target CLI. They are not
a statement about how large a domain object (a report, a memory store, a
catalog) may be. Per-surface evidence and the MATCH / DRIFT / UNVERIFIED
classifications live in ``docs/policy/output-truncation-limits.md``.

The defaults below are the minimum across every MATCH row in that file
as of 2026-08-23 (second pass): 16,000 bytes (OpenClaw's live tool-result
default for models below a 100K-token window, applied as UTF-8 bytes)
and 256 lines (the tightest historical line fuse). Callers may override
either value.

A payload that fits in one part is returned unchanged: no framing, no
trailer. When more parts remain, exactly one trailing line names the
resolved command that fetches the next part. Lines are never split. A
single line longer than the byte cap is reported rather than silently
truncated.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

try:
    from self_naming import runnable_self_command
except ImportError:  # imported as scripts.lib.output_paging
    from .self_naming import runnable_self_command

# Transport defaults. Keep in lockstep with the "Safe default" paragraph
# of docs/policy/output-truncation-limits.md; a test asserts the pair.
DEFAULT_MAX_BYTES = 16_000
DEFAULT_MAX_LINES = 256

NEXT_PREFIX = "# next: "


class OversizedLineError(ValueError):
    """A single line exceeds the byte cap and cannot be paged intact.

    Splitting it would violate the never-split-mid-line rule. Silently
    truncating it would corrupt the payload. The caller must report this
    rather than emit a partial line.
    """

    def __init__(self, line_number: int, byte_length: int, max_bytes: int) -> None:
        self.line_number = line_number
        self.byte_length = byte_length
        self.max_bytes = max_bytes
        super().__init__(
            f"line {line_number} is {byte_length} bytes, which exceeds the "
            f"{max_bytes}-byte transport cap and cannot be paged without "
            f"splitting the line"
        )


@dataclass(frozen=True)
class Page:
    """One transport-sized part of a larger payload."""

    text: str
    part: int
    total_parts: int
    next_command: str | None

    @property
    def has_more(self) -> bool:
        return self.next_command is not None


def utf8_size(text: str) -> int:
    """Return the UTF-8 byte length of *text*."""
    return len(text.encode("utf-8"))


def page_text(
    text: str,
    *,
    part: int = 1,
    max_bytes: int | None = None,
    max_lines: int | None = None,
    next_command_prefix: str | None = None,
    extra_args: Sequence[str] | None = None,
    script_path: Path | None = None,
    interpreter: Path | None = None,
) -> Page:
    """Return one part of *text* bounded by both a byte cap and a line cap.

    *part* is 1-based. *next_command_prefix*, when supplied, is the exact
    command printed in the trailer (with ``--part N`` appended). When it
    is omitted, the trailer is built from *script_path* / *extra_args*
    via :func:`self_naming.runnable_self_command` so the printed command
    is PATH-independent.

    When the whole payload fits in one part the returned ``text`` is the
    original string with no framing.
    """
    if part < 1:
        raise ValueError(f"part must be >= 1, got {part}")

    byte_cap = DEFAULT_MAX_BYTES if max_bytes is None else int(max_bytes)
    line_cap = DEFAULT_MAX_LINES if max_lines is None else int(max_lines)
    if byte_cap < 1:
        raise ValueError(f"max_bytes must be >= 1, got {byte_cap}")
    if line_cap < 1:
        raise ValueError(f"max_lines must be >= 1, got {line_cap}")

    lines = text.split("\n")
    _reject_oversized_lines(lines, byte_cap)

    prefix = next_command_prefix
    if prefix is None:
        prefix = runnable_self_command(
            extra_args,
            script_path=script_path,
            interpreter=interpreter,
        )

    chunks = _pack_parts(lines, byte_cap, line_cap, prefix)
    total = len(chunks)
    if part > total:
        raise ValueError(f"part {part} of {total} does not exist")

    body = chunks[part - 1]
    if total == 1:
        return Page(text=text, part=1, total_parts=1, next_command=None)

    if part == total:
        return Page(text=body, part=part, total_parts=total, next_command=None)

    next_cmd = f"{prefix} --part {part + 1}"
    trailer = NEXT_PREFIX + next_cmd
    rendered = body + ("\n" if body and not body.endswith("\n") else "") + trailer
    return Page(text=rendered, part=part, total_parts=total, next_command=next_cmd)


def emit_paged(
    text: str,
    *,
    part: int = 1,
    max_bytes: int | None = None,
    max_lines: int | None = None,
    extra_args: Sequence[str] | None = None,
    script_path: Path | None = None,
    interpreter: Path | None = None,
    next_command_prefix: str | None = None,
) -> str:
    """Return the printable form of one part (convenience around :func:`page_text`)."""
    return page_text(
        text,
        part=part,
        max_bytes=max_bytes,
        max_lines=max_lines,
        extra_args=extra_args,
        script_path=script_path,
        interpreter=interpreter,
        next_command_prefix=next_command_prefix,
    ).text


def _reject_oversized_lines(lines: list[str], byte_cap: int) -> None:
    for index, line in enumerate(lines, start=1):
        size = utf8_size(line)
        if size > byte_cap:
            raise OversizedLineError(index, size, byte_cap)


def _trailer_for(prefix: str, next_part: int) -> str:
    return NEXT_PREFIX + f"{prefix} --part {next_part}"


def _pack_parts(
    lines: list[str],
    byte_cap: int,
    line_cap: int,
    prefix: str,
) -> list[str]:
    """Greedy-pack *lines* into parts that leave room for a next-part trailer.

    Trailer reservation is applied to every part during packing so a
    non-final part plus its trailer stays under both caps. After packing,
    a one-part result is returned without a trailer (the caller emits the
    original text). A line that cannot share a part with a trailer, and
    is not the last line of the payload, is reported as oversized: paging
    it would either split the line or emit a part over the cap.
    """
    # Representative trailer: part numbers stay in a narrow width, so a
    # prefix-based trailer is a stable reservation.
    trailer = _trailer_for(prefix, 2)
    trailer_bytes = utf8_size(trailer) + 1  # the joining newline
    trailer_lines = 1

    if trailer_bytes >= byte_cap or trailer_lines >= line_cap:
        raise OversizedLineError(0, trailer_bytes, byte_cap)

    content_byte_cap = byte_cap - trailer_bytes
    content_line_cap = line_cap - trailer_lines

    parts: list[list[str]] = []
    current: list[str] = []
    current_bytes = 0

    def flush() -> None:
        nonlocal current, current_bytes
        if not current:
            return
        parts.append(current)
        current = []
        current_bytes = 0

    for index, line in enumerate(lines):
        line_bytes = utf8_size(line)
        is_last_line = index == len(lines) - 1
        # A newline joins this line to the previous one in the same part.
        join = 1 if current else 0
        projected_bytes = current_bytes + join + line_bytes
        projected_lines = len(current) + 1

        fits_reserved = (
            projected_bytes <= content_byte_cap and projected_lines <= content_line_cap
        )
        if current and not fits_reserved:
            flush()
            join = 0
            projected_bytes = line_bytes
            projected_lines = 1
            fits_reserved = (
                projected_bytes <= content_byte_cap and projected_lines <= content_line_cap
            )

        if not fits_reserved:
            # Last line of the payload needs no trailer, so it may use
            # the full caps. Any earlier line that cannot sit with a
            # trailer cannot be paged legally.
            if is_last_line and not current:
                if line_bytes <= byte_cap and 1 <= line_cap:
                    current = [line]
                    current_bytes = line_bytes
                    flush()
                    continue
            raise OversizedLineError(index + 1, line_bytes + trailer_bytes, byte_cap)

        current.append(line)
        current_bytes = projected_bytes

    flush()
    if not parts:
        return [""]
    return ["\n".join(chunk) for chunk in parts]
