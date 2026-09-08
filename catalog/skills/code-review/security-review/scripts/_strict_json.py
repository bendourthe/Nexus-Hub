#!/usr/bin/env python3
"""The one strict JSON decoder for every security-review input.

Closure records, routing manifests, inventory receipts, SARIF inputs, and
benchmark scoring inputs all arrive as JSON produced by something this code does
not control. `json.loads` accepts several things that are wrong for that job, and
each one has a concrete failure behind it:

- **Duplicate object members.** `json.loads` keeps the LAST value silently. A
  record carrying `"computed_health": "failed"` followed by
  `"computed_health": "complete"` therefore reads as complete, and the evidence
  that both were claimed is destroyed at parse time. This is the membership
  bypass class that already cost this repository a validator fix.
- **`NaN` / `Infinity`.** Accepted by default as Python floats, then compared and
  aggregated. A non-finite score silently poisons every threshold it touches.
- **Unbounded size, nesting, and collection width.** A decoder with no ceiling
  turns an untrusted file into a memory and CPU budget the caller never agreed
  to.

Every check runs BEFORE any semantic validation, and the decoder either returns a
fully validated value or raises. There is no partial result: a caller can never
act on half-checked input.

Errors carry a stable `code` so callers can record a reason code rather than
matching on prose that may be reworded.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

#: Ceilings. Exposed as module constants so tests can exercise each one at its
#: exact value and one unit beyond it, rather than hardcoding a copy that could
#: drift away from the enforced number.
MAX_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 32
MAX_MEMBERS = 10_000
MAX_STRING_BYTES = 64 * 1024


class StrictJSONError(ValueError):
    """Raised when input is rejected before any semantic validation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _reject(code: str, message: str) -> None:
    raise StrictJSONError(code, message)


def _check_string(value: str, where: str) -> None:
    """Bound one string and prove it is encodable UTF-8.

    A lone surrogate reaches here from an escape such as ``\\ud800``, which the
    stdlib decoder accepts happily but which cannot be encoded, written, or
    hashed later. Catching it at the boundary keeps the failure at the input
    rather than at some downstream write that is much harder to attribute.
    """
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        _reject("invalid_unicode", f"{where} contains unencodable text")
        return
    if len(encoded) > MAX_STRING_BYTES:
        _reject(
            "string_too_large",
            f"{where} is {len(encoded)} bytes, over the {MAX_STRING_BYTES} limit",
        )


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate members and over-wide objects at every nesting level.

    The stdlib calls this for EVERY object it decodes, so duplicate detection is
    recursive by construction rather than by an explicit walk that could miss a
    branch.
    """
    if len(pairs) > MAX_MEMBERS:
        _reject(
            "object_too_large",
            f"object has {len(pairs)} members, over the {MAX_MEMBERS} limit",
        )
    seen: set[str] = set()
    for key, _value in pairs:
        if key in seen:
            _reject(
                "duplicate_object_member",
                "an object member appears more than once",
            )
        seen.add(key)
    return dict(pairs)


def _constant_hook(name: str) -> Any:
    _reject("non_finite_number", f"{name} is not valid JSON for this decoder")


def _enforce_structure(value: Any) -> None:
    """Bound depth, collection width, and string size over the decoded value.

    Iterative on purpose. A recursive walk would itself be a depth-bomb target,
    which is a poor property for the code whose job is rejecting depth bombs.

    Depth counts CONTAINERS, so a bare scalar is 0 and ``{"a": {"b": 1}}`` is 2.
    """
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        if isinstance(node, dict):
            here = depth + 1
            if here > MAX_DEPTH:
                _reject(
                    "depth_exceeded",
                    f"nesting reaches {here} levels, over the {MAX_DEPTH} limit",
                )
            if len(node) > MAX_MEMBERS:
                _reject(
                    "object_too_large",
                    f"object has {len(node)} members, over the {MAX_MEMBERS} limit",
                )
            for key, item in node.items():
                _check_string(key, "object key")
                stack.append((item, here))
        elif isinstance(node, list):
            here = depth + 1
            if here > MAX_DEPTH:
                _reject(
                    "depth_exceeded",
                    f"nesting reaches {here} levels, over the {MAX_DEPTH} limit",
                )
            if len(node) > MAX_MEMBERS:
                _reject(
                    "array_too_large",
                    f"array has {len(node)} members, over the {MAX_MEMBERS} limit",
                )
            for item in node:
                stack.append((item, here))
        elif isinstance(node, str):
            _check_string(node, "string value")
        elif isinstance(node, float):
            # Reached by an overflowing literal such as 1e400, which the parser
            # turns into inf WITHOUT going through the constant hook above. Both
            # guards are needed; neither covers the other's case.
            if not math.isfinite(node):
                _reject("non_finite_number", "number is not finite")


def loads(data: bytes | str) -> Any:
    """Decode one JSON document, or raise `StrictJSONError`."""
    if isinstance(data, str):
        raw = data.encode("utf-8", errors="surrogatepass")
    else:
        raw = data

    if len(raw) > MAX_BYTES:
        _reject(
            "input_too_large",
            f"input is {len(raw)} bytes, over the {MAX_BYTES} limit",
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StrictJSONError(
            "invalid_unicode", f"input is not valid UTF-8: {exc}"
        ) from exc

    decoder = json.JSONDecoder(
        object_pairs_hook=_pairs_hook, parse_constant=_constant_hook
    )
    stripped = text.lstrip()
    if not stripped:
        _reject("empty_input", "input contains no JSON document")
    offset = len(text) - len(stripped)
    try:
        value, end = decoder.raw_decode(text, offset)
    except ValueError as exc:
        if isinstance(exc, StrictJSONError):
            raise
        raise StrictJSONError("malformed_json", "input is not valid bounded JSON") from exc
    except RecursionError as exc:
        # A nesting bomb exhausts the parser before our own depth check can see
        # the decoded value, so the parser's own limit is the fail-closed path.
        raise StrictJSONError(
            "depth_exceeded", "input nesting exhausted the parser"
        ) from exc

    if text[end:].strip():
        _reject("trailing_data", "input contains data after the JSON document")

    _enforce_structure(value)
    return value


def load_path(path: Path) -> Any:
    """Read and strictly decode one file named explicitly by the caller.

    The path always comes from the caller's own arguments, never from inside a
    record. A path appearing in untrusted content is metadata, not a read
    instruction, and this function is not the place that decides otherwise.
    """
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        raise StrictJSONError("unreadable_input", "cannot read the supplied input") from exc
    return loads(raw)
