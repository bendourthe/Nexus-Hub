"""Provenance envelope for agent-facing memory records.

The on-disk log stays a dumb append-only byte store. This module is the
write-path contract for `record`: every new lasting entry must name a
`source`. Existing log rows without a header are readable as
`source: legacy-import` so a store from v3.19.1 still loads.

Store writes are a single JSON line so a tiled read still counts one
physical line per record (the read budget is a line budget). File-backed
notes may still use a YAML header plus `---` plus body; the parser accepts
both.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

SEPARATOR = "---"
TIERS = ("session", "working", "durable")
LEGACY_SOURCE = "legacy-import"


class MissingSourceError(ValueError):
    """A write was rejected because it named no origin."""


@dataclass(frozen=True)
class MemoryRecord:
    """One parsed envelope plus its body."""

    source: str
    tier: str
    body: str
    derived_from: tuple[str, ...] = ()
    supersedes: int | None = None
    legacy: bool = False


def format_record(
    body: str,
    *,
    source: str,
    tier: str = "working",
    derived_from: tuple[str, ...] = (),
    supersedes: int | None = None,
) -> str:
    """Serialize *body* as a one-line JSON envelope with a required source."""
    origin = source.strip()
    if not origin:
        raise MissingSourceError(
            "memory record rejected: source is required "
            f"(use source: {LEGACY_SOURCE} when importing a file that has none)"
        )
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}, got {tier!r}")
    if supersedes is not None and supersedes < 0:
        raise ValueError("supersedes must be a non-negative index")
    payload: dict[str, object] = {
        "source": origin,
        "tier": tier,
        "body": body.rstrip("\n"),
    }
    if derived_from:
        payload["derived_from"] = list(derived_from)
    if supersedes is not None:
        payload["supersedes"] = supersedes
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def display_body(text: str) -> str:
    """Return the fact text, stripping a provenance envelope when present."""
    return parse_record(text, strict=False).body


def parse_record(text: str, *, strict: bool = True) -> MemoryRecord:
    """Parse a JSON or YAML envelope. *strict* rejects a missing source."""
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            return _from_fields(
                {str(k): payload[k] for k in payload},
                body=str(payload.get("body", "")),
                strict=strict,
            )

    if f"\n{SEPARATOR}\n" in text:
        header, _, body = text.partition(f"\n{SEPARATOR}\n")
        fields = _header_fields(header)
        return _from_fields(fields, body=body, strict=strict)
    if text.startswith(f"{SEPARATOR}\n"):
        body = text[len(SEPARATOR) + 1 :]
        return _from_fields({}, body=body, strict=strict)

    if strict:
        raise MissingSourceError(
            "memory record rejected: source is required "
            f"(use source: {LEGACY_SOURCE} when importing a file that has none)"
        )
    return MemoryRecord(
        source=LEGACY_SOURCE,
        tier="working",
        body=text,
        legacy=True,
    )


def _header_fields(header: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _from_fields(
    fields: dict[str, object],
    *,
    body: str,
    strict: bool,
) -> MemoryRecord:
    origin = str(fields.get("source", "")).strip()
    legacy = False
    if not origin:
        if strict:
            raise MissingSourceError(
                "memory record rejected: source is required "
                f"(use source: {LEGACY_SOURCE} when importing a file that has none)"
            )
        origin = LEGACY_SOURCE
        legacy = True

    tier = str(fields.get("tier", "working")).strip() or "working"
    if tier not in TIERS:
        if strict:
            raise ValueError(f"tier must be one of {TIERS}, got {tier!r}")
        tier = "working"

    derived_val = fields.get("derived_from", "")
    if isinstance(derived_val, list):
        derived = tuple(str(part).strip() for part in derived_val if str(part).strip())
    else:
        derived = tuple(
            part.strip() for part in str(derived_val).split(",") if part.strip()
        )

    supersedes_val = fields.get("supersedes", "")
    if supersedes_val in ("", None):
        supersedes = None
    else:
        supersedes = int(supersedes_val)

    return MemoryRecord(
        source=origin,
        tier=tier,
        body=body.rstrip("\n"),
        derived_from=derived,
        supersedes=supersedes,
        legacy=legacy,
    )
