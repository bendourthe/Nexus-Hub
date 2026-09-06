# Nexus Compact Wire Format

## Purpose

The Nexus Compact Wire Format is a Nexus-Hub-owned, producer-side encoding for structured `nexus-code-search` MCP responses. It removes repeated object keys from tabular arrays while preserving the complete JSON value model. It is not a general compressor and does not replace `nexus-context-compressor`.

The reference implementation lives in `nexus_code_search.response_codec` and uses only the Python standard library. Consumers may use that decoder or implement this specification independently.

## Testable Requirements

- **Deterministic**: encoding the same JSON-compatible response structure, including its object insertion order, produces identical UTF-8 bytes every time.

- **Round-trippable**: decoding reconstructs the original top-level key order, table column order, JSON value types, nested values, null values, and missing fields.

- **Fail-open**: `response_format=json` always returns the existing JSON representation. Any producer-side codec exception returns that JSON representation instead of failing the tool call. A consumer that cannot decode a compact response retries the same call with `response_format=json`; the reference decoder accepts a JSON retry callback and never propagates a compact-decoding error when that callback is supplied.

- **Size-justified**: `response_format=auto` selects compact output only when its UTF-8 byte count is at least `compact_min_savings_pct` smaller than JSON. The default threshold is 15%. `response_format=compact` always selects the compact representation, including for small responses where it may be larger.

## Request Controls

Every `nexus-code-search` tool accepts these optional arguments:

| Argument | Values | Default | Meaning |
|---|---|---|---|
| `response_format` | `json`, `compact`, `auto` | `json` | Preserve JSON, force compact, or choose by measured byte savings |
| `compact_min_savings_pct` | Number from 0 through 100 | `15` | Minimum UTF-8 byte reduction required by automatic mode |

The JSON default is the compatibility boundary for existing consumers.

## Media Detection and Version

A compact payload starts with this exact first line:

```text
NEXUS-CW/1
```

JSON never starts with this marker. A consumer distinguishes formats by checking the complete first line, not by searching the payload. The integer after the slash is the format version; an unsupported version must trigger a retry with `response_format=json`.

## Line Grammar

Every physical line is UTF-8. Fields are separated by one tab character. JSON fragments use compact JSON encoding, so tabs, newlines, and other delimiter characters inside values are escaped and never create physical fields or lines.

```text
NEXUS-CW/1
E<TAB><envelope-json>
T<TAB><table-id><TAB><path-json><TAB><row-count><TAB><columns-json>
C<TAB><table-id><TAB><column-index><TAB><presence-bitmap><TAB><values-json>
```

The records mean:

- `E` is the JSON envelope. Each extracted table position contains an empty array until decoding restores it. Non-tabular content remains in the envelope unchanged.

- `T` declares one table. `table-id` is a zero-based decimal integer assigned in deterministic preorder. `path-json` is a JSON array of object keys and array indices locating the empty-array slot in the envelope. `row-count` is a non-negative decimal integer. `columns-json` is the ordered JSON array of column names.

- `C` carries one column. `column-index` addresses `columns-json`. `presence-bitmap` has exactly one `0` or `1` per row. `values-json` contains one typed JSON value for every `1`, in row order. A `0` means the field was missing; a `1` with a JSON `null` value means the field existed and was null.

An eligible table is a non-empty JSON array whose elements are all JSON objects with string keys. Column order is first appearance across rows: keys from row zero in their original order, followed by previously unseen keys from later rows. Nested objects and arrays inside a cell remain typed JSON values; the codec does not flatten them.

## Example

Input JSON:

```json
{
  "query": "render",
  "results": [
    {"file": "a.py", "line": 3, "note": null},
    {"file": "b.py", "line": 8, "score": 0.9}
  ]
}
```

Compact representation, with `<TAB>` shown visibly:

```text
NEXUS-CW/1
E<TAB>{"query":"render","results":[]}
T<TAB>0<TAB>["results"]<TAB>2<TAB>["file","line","note","score"]
C<TAB>0<TAB>0<TAB>11<TAB>["a.py","b.py"]
C<TAB>0<TAB>1<TAB>11<TAB>[3,8]
C<TAB>0<TAB>2<TAB>10<TAB>[null]
C<TAB>0<TAB>3<TAB>01<TAB>[0.9]
```

## Encoding Algorithm

1. Serialize the original response with the existing JSON path. Keep this byte string as the fail-open result and automatic-mode baseline.

2. Walk the response in deterministic preorder. Replace each eligible table with an empty array in the envelope and record its path, ordered columns, presence bitmaps, and values.

3. Emit the marker, envelope, table declarations, and columns in ascending table and column order.

4. In `compact` mode, return the compact candidate. In `auto` mode, compare the actual UTF-8 byte lengths and return compact only when the configured threshold is met. In `json` mode, return the original JSON without invoking the compact encoder.

5. Catch every compact-encoding exception at the public response boundary and return the original valid JSON.

## Decoding and Retry

1. If the marker is absent, parse the payload as JSON.

2. If the marker is present, validate the version and record grammar, parse the envelope, reconstruct every table from its presence bitmaps and typed values, then write each table back to its declared path.

3. If compact decoding fails, the bytes cannot safely reconstruct missing information. Retry the same tool call with `response_format=json`. The reference decoder's `json_retry` callback performs this protocol step and parses the returned JSON without exposing the compact error.

## Relationship to Consumer-Side Compression

This format runs at the producer and knows the response schema. `nexus-context-compressor` runs later at the consumer boundary and routes arbitrary tool output by content type, using reversible CCR markers when it drops content. The compressor recognizes the exact `NEXUS-CW/1` marker and passes the payload through unchanged, so producer encoding happens first and is never double-compressed. A CCR marker stored as a response value remains ordinary typed string data and round-trips without alteration.
