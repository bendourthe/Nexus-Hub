"""Deterministic producer-side encoding for structured MCP responses."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

WIRE_MARKER = "NEXUS-CW/1"
DEFAULT_MIN_SAVINGS_PCT = 15.0
RESPONSE_FORMATS = ("json", "compact", "auto")


@dataclass(frozen=True)
class SavingsMeasurement:
    """Actual UTF-8 byte sizes for JSON and compact representations."""

    json_bytes: int
    compact_bytes: int
    savings_pct: float


@dataclass(frozen=True)
class _Table:
    table_id: int
    path: list[str | int]
    row_count: int
    columns: list[str]
    presence: list[str]
    values: list[list[Any]]


def _fragment(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _is_table(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(
            isinstance(row, dict)
            and all(isinstance(key, str) for key in row)
            for row in value
        )
    )


def _table_from_rows(
    rows: list[dict[str, Any]], path: list[str | int], table_id: int
) -> _Table:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)

    presence: list[str] = []
    values: list[list[Any]] = []
    for column in columns:
        bits: list[str] = []
        column_values: list[Any] = []
        for row in rows:
            if column in row:
                bits.append("1")
                column_values.append(row[column])
            else:
                bits.append("0")
        presence.append("".join(bits))
        values.append(column_values)

    return _Table(
        table_id=table_id,
        path=list(path),
        row_count=len(rows),
        columns=columns,
        presence=presence,
        values=values,
    )


def _extract_tables(
    value: Any, path: list[str | int], tables: list[_Table]
) -> Any:
    if _is_table(value):
        table = _table_from_rows(value, path, len(tables))
        tables.append(table)
        return []
    if isinstance(value, dict):
        return {
            key: _extract_tables(item, [*path, key], tables)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _extract_tables(item, [*path, index], tables)
            for index, item in enumerate(value)
        ]
    return value


def _encode_compact(payload: object) -> str:
    tables: list[_Table] = []
    envelope = _extract_tables(payload, [], tables)
    lines = [WIRE_MARKER, f"E\t{_fragment(envelope)}"]
    for table in tables:
        lines.append(
            "\t".join(
                (
                    "T",
                    str(table.table_id),
                    _fragment(table.path),
                    str(table.row_count),
                    _fragment(table.columns),
                )
            )
        )
        for column_index, (presence, values) in enumerate(
            zip(table.presence, table.values, strict=True)
        ):
            lines.append(
                "\t".join(
                    (
                        "C",
                        str(table.table_id),
                        str(column_index),
                        presence,
                        _fragment(values),
                    )
                )
            )
    return "\n".join(lines)


def measure_savings(payload: object) -> SavingsMeasurement:
    """Measure compact output against the existing JSON representation."""

    json_output = json.dumps(payload)
    compact_output = _encode_compact(payload)
    json_bytes = len(json_output.encode("utf-8"))
    compact_bytes = len(compact_output.encode("utf-8"))
    savings_pct = (
        0.0
        if json_bytes == 0
        else ((json_bytes - compact_bytes) / json_bytes) * 100.0
    )
    return SavingsMeasurement(json_bytes, compact_bytes, savings_pct)


def encode_response(
    payload: object,
    *,
    response_format: str = "json",
    min_savings_pct: float = DEFAULT_MIN_SAVINGS_PCT,
) -> str:
    """Encode one JSON-compatible response, falling back to JSON on any error."""

    json_output = json.dumps(payload)
    if response_format == "json":
        return json_output
    if response_format not in RESPONSE_FORMATS:
        return json_output

    try:
        threshold = float(min_savings_pct)
        if not 0.0 <= threshold <= 100.0:
            return json_output
        compact_output = _encode_compact(payload)
        if response_format == "compact":
            return compact_output
        json_bytes = len(json_output.encode("utf-8"))
        compact_bytes = len(compact_output.encode("utf-8"))
        savings_pct = (
            0.0
            if json_bytes == 0
            else ((json_bytes - compact_bytes) / json_bytes) * 100.0
        )
        return compact_output if savings_pct >= threshold else json_output
    except Exception:  # noqa: BLE001 - this hot path must always fail open
        return json_output


@dataclass
class _DecodedTable:
    path: list[str | int]
    row_count: int
    columns: list[str]
    encoded_columns: dict[int, tuple[str, list[Any]]]


def _set_path(root: Any, path: list[str | int], value: object) -> Any:
    if not path:
        return value
    target = root
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = value
    return root


def _decode_compact(text: str) -> object:
    lines = text.splitlines()
    if not lines or lines[0] != WIRE_MARKER:
        raise ValueError("unsupported compact response marker")
    if len(lines) < 2 or not lines[1].startswith("E\t"):
        raise ValueError("compact response is missing its envelope")
    envelope = json.loads(lines[1][2:])
    tables: dict[int, _DecodedTable] = {}

    for line in lines[2:]:
        if line.startswith("T\t"):
            parts = line.split("\t", 4)
            if len(parts) != 5:
                raise ValueError("invalid table declaration")
            table_id = int(parts[1])
            path = json.loads(parts[2])
            row_count = int(parts[3])
            columns = json.loads(parts[4])
            if (
                table_id in tables
                or not isinstance(path, list)
                or row_count < 0
                or not isinstance(columns, list)
                or not all(isinstance(column, str) for column in columns)
            ):
                raise ValueError("invalid table metadata")
            tables[table_id] = _DecodedTable(path, row_count, columns, {})
        elif line.startswith("C\t"):
            parts = line.split("\t", 4)
            if len(parts) != 5:
                raise ValueError("invalid column declaration")
            table_id = int(parts[1])
            column_index = int(parts[2])
            presence = parts[3]
            values = json.loads(parts[4])
            table = tables.get(table_id)
            if (
                table is None
                or column_index in table.encoded_columns
                or not 0 <= column_index < len(table.columns)
                or len(presence) != table.row_count
                or any(bit not in "01" for bit in presence)
                or not isinstance(values, list)
                or presence.count("1") != len(values)
            ):
                raise ValueError("invalid column metadata")
            table.encoded_columns[column_index] = (presence, values)
        else:
            raise ValueError("unknown compact response record")

    root = envelope
    for table_id in sorted(tables):
        table = tables[table_id]
        if len(table.encoded_columns) != len(table.columns):
            raise ValueError("compact response is missing a column")
        rows: list[dict[str, Any]] = [{} for _ in range(table.row_count)]
        for column_index, column in enumerate(table.columns):
            presence, values = table.encoded_columns[column_index]
            value_index = 0
            for row_index, bit in enumerate(presence):
                if bit == "1":
                    rows[row_index][column] = values[value_index]
                    value_index += 1
        root = _set_path(root, table.path, rows)
    return root


def decode_response(
    text: str, *, json_retry: Callable[[], str] | None = None
) -> object:
    """Decode JSON or compact output, retrying as JSON after compact failure."""

    if not text.startswith(f"{WIRE_MARKER}\n"):
        return json.loads(text)
    try:
        return _decode_compact(text)
    except Exception:
        if json_retry is None:
            raise
        return json.loads(json_retry())
