#!/usr/bin/env python3
"""Emit a small, synthetic, metadata-only agent trace for local inspection.

Standard library only. No network, no environment capture, no real tool
execution, no loader for caller-supplied data. Every record is fabricated here.

The point is what it does NOT write: the generator holds a sentinel payload and
a sentinel exception string, and neither reaches the output. A redaction demo
whose input contains no secret demonstrates nothing.

Field names follow `references/agent-span-contract.md`, pinned to an upstream
convention at Development status. Output is plain JSONL, not OTLP, and claims
no OpenTelemetry conformance.

Usage:  python trace-example.py --output /path/to/new/trace.jsonl
Exit:   0 records written; 2 unsafe or refused output path
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Bounded allowlist. Anything unrecognized becomes `internal_error` rather than
# carrying an uncontrolled exception string into the record.
ERROR_CATEGORIES = (
    "timeout",
    "rate_limited",
    "invalid_input",
    "permission_denied",
    "unavailable",
    "internal_error",
)

# Attributes the span contract classifies Opt-In. They are payload-bearing and
# must never appear in default output.
FORBIDDEN_KEYS = (
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "gen_ai.system_instructions",
    "gen_ai.tool.definitions",
)

# Sentinels. Present in the generator, absent from every emitted record.
_SENTINEL_PAYLOAD = "sk-live-SENTINEL-must-not-appear"
_SENTINEL_EXCEPTION = "PermissionError: /srv/secrets/SENTINEL-private-key.pem denied"

_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _trace_id() -> str:
    """32 hex characters."""
    return secrets.token_hex(16)


def _span_id() -> str:
    """16 hex characters."""
    return secrets.token_hex(8)


def _at(offset_ms: int) -> str:
    return (_BASE + timedelta(milliseconds=offset_ms)).isoformat().replace("+00:00", "Z")


def _record(
    trace_id: str,
    span_id: str,
    parent_span_id: str | None,
    operation: str,
    kind: str,
    start_ms: int,
    end_ms: int,
    status: str,
    attributes: dict[str, object],
) -> dict[str, object]:
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "name": operation,
        "gen_ai.operation.name": operation,
        "span_kind": kind,
        "start_time": _at(start_ms),
        "end_time": _at(end_ms),
        "status": status,
        "nexus.synthetic": True,
        **attributes,
    }


def build_records() -> list[dict[str, object]]:
    """One workflow containing a local agent, a successful tool call, a failed
    tool call, and a remote call whose internals were not observable.

    No `plan` span is emitted: this integration cannot observe planning
    boundaries, and inventing one would describe an architecture nobody built.
    _SENTINEL_PAYLOAD would belong to `gen_ai.input.messages` on the agent
    span; being Opt-In, it is omitted entirely rather than truncated.
    """
    trace, wf, agent = _trace_id(), _span_id(), _span_id()
    specs = [
        (wf, None, "invoke_workflow", "INTERNAL", 0, 900, "OK",
         {"gen_ai.workflow.name": "example-workflow", "nexus.iteration": 1}),
        (agent, wf, "invoke_agent", "INTERNAL", 10, 880, "OK",
         {"gen_ai.agent.name": "example-agent", "gen_ai.agent.id": _span_id(),
          "gen_ai.request.model": "example-model",
          "gen_ai.usage.input_tokens": 412, "gen_ai.usage.output_tokens": 98}),
        (_span_id(), agent, "execute_tool", "INTERNAL", 120, 300, "OK",
         {"gen_ai.tool.name": "example_reader",
          "nexus.coverage.arguments": "omitted_by_policy",
          "nexus.coverage.result": "omitted_by_policy"}),
        # Only the allowlisted category survives the sentinel exception.
        (_span_id(), agent, "execute_tool", "INTERNAL", 320, 410, "ERROR",
         {"gen_ai.tool.name": "example_writer",
          "error.type": _categorize(_SENTINEL_EXCEPTION),
          "nexus.coverage.exception_detail": "omitted_by_policy"}),
        (_span_id(), agent, "invoke_agent", "CLIENT", 430, 870, "OK",
         {"gen_ai.agent.name": "remote-example-agent",
          "gen_ai.provider.name": "example-provider",
          "server.address": "example.invalid",
          "nexus.coverage.planning": "not_observable",
          "nexus.coverage.internal_reasoning": "unavailable"}),
    ]
    return [_record(trace, *spec) for spec in specs]


def _categorize(raw: str) -> str:
    """Map an arbitrary failure to an allowlisted category.

    The raw text is read but never returned, which is the point.
    """
    lowered = raw.lower()
    if "permission" in lowered:
        return "permission_denied"
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    return "internal_error"


def assert_no_payload(records: list[dict[str, object]]) -> None:
    """Fail loudly rather than write a record carrying payload or a sentinel."""
    blob = json.dumps(records)
    for key in FORBIDDEN_KEYS:
        if key in blob:
            raise AssertionError(f"payload attribute present in output: {key}")
    for sentinel in (_SENTINEL_PAYLOAD, _SENTINEL_EXCEPTION):
        if sentinel in blob:
            raise AssertionError("sentinel value reached the output")


def resolve_output(raw: str) -> Path:
    """Accept only a new, regular file inside an existing directory, and say where it lands.

    An adversarial pass showed the previous `parent.is_symlink()` check was
    incomplete in two ways: `Path.is_symlink()` is False for a Windows junction
    (IO_REPARSE_TAG_MOUNT_POINT), which any user can create without privilege,
    and only the IMMEDIATE parent was ever inspected, so a redirected
    grandparent went unexamined.

    Refusing every redirected ancestor was tried and rejected as the fix. It
    breaks the script's own documented use: on macOS `/tmp` is a symlink to
    `/private/tmp` and `$TMPDIR` sits under `/var`, itself a symlink to
    `/private/var`, so "a caller-owned temporary directory" would be refused on
    the most ordinary platform. Comparing resolved against unresolved paths is
    worse still, because `resolve()` also expands Windows 8.3 short names, so
    a perfectly normal `C:\\Users\\RUNNER~1\\...` path would be rejected as
    redirected.

    The guard that actually protects the caller is the O_EXCL write in `main`,
    which cannot clobber an existing file and will not follow a symlink at the
    final component. Redirection of an ancestor is therefore DISCLOSED rather
    than refused: the caller chose the path, and is told where the bytes really
    went.
    """
    if "\x00" in raw:
        raise ValueError("refusing a path containing a NUL byte")
    path = Path(raw)
    if path.is_symlink() or path.exists():
        raise ValueError(f"refusing to write an existing path: {path}")
    parent = path.parent
    if not parent.is_dir():
        raise ValueError(f"output directory does not exist: {parent}")
    return path


def _is_reparse_point(path: Path) -> bool:
    """True for a POSIX symlink or a Windows symlink/junction.

    `os.path.islink` is False for a Windows junction, so the reparse-point
    attribute is checked directly. Comparing resolved against unresolved paths
    would be simpler and wrong: `resolve()` also expands 8.3 short names, so
    an ordinary `C:\\Users\\RUNNER~1\\...` path would look redirected.
    """
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def describe_destination(destination: Path) -> str:
    """Name the real location only when an ancestor genuinely redirects the write."""
    absolute = Path(os.path.abspath(destination))
    redirected = any(_is_reparse_point(ancestor) for ancestor in absolute.parents)
    if not redirected:
        return str(destination)
    try:
        real = absolute.parent.resolve(strict=True) / absolute.name
    except OSError:
        return str(destination)
    return f"{destination} (an ancestor redirects; the bytes land at {real})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        required=True,
        help="path to a NEW .jsonl file in a caller-owned temporary directory",
    )
    args = parser.parse_args(argv)

    try:
        destination = resolve_output(args.output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    records = build_records()
    assert_no_payload(records)
    # "x" is O_EXCL: it refuses an existing path and will not follow a symlink
    # at the final component, closing the window between the check above and
    # this write in which the path could be swapped.
    #
    # It is strict in one surprising way, measured on Windows rather than
    # assumed: an exclusive create through a directory junction fails with
    # FileExistsError even when nothing is there. That is reported as a refusal,
    # never as a traceback, and never by falling back to a truncating open,
    # which would hand back the race this mode exists to close.
    try:
        handle = destination.open("x", encoding="utf-8", newline="\n")
    except OSError as exc:
        print(
            f"error: cannot create {destination}: {exc.strerror or exc}. "
            "A junctioned or otherwise redirected output directory can cause this "
            "even when the file does not exist; use a plain directory.",
            file=sys.stderr,
        )
        return 2
    with handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    print(f"wrote {len(records)} synthetic records to {describe_destination(destination)}")
    print("payloads, tool arguments, results, instructions and raw exceptions omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
