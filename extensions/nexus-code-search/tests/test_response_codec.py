"""Round-trip, fail-open, and composition tests for response encoding."""

from __future__ import annotations

import importlib
import json
import random
import sys
from pathlib import Path

import pytest
from mcp.types import TextContent

from nexus_code_search import response_codec as codec
from nexus_code_search import server

_COMPRESSOR_SRC = Path(__file__).parents[2] / "nexus-context-compressor" / "src"
sys.path.insert(0, str(_COMPRESSOR_SRC))
compress_output = importlib.import_module("nexus_context_compressor").compress_output


ROUND_TRIP_PAYLOADS = [
    {},
    {"results": []},
    {"results": [{"rank": 1, "score": 0.5, "text": "single"}]},
    {
        "query": "tabs\tand\nlines",
        "results": [
            {"path": "a\tb.py", "text": "NEXUS-CW/1\nE\t{}", "note": None},
            {"path": "c.py", "text": "snowman \u2603", "missing_only_before": True},
        ],
    },
    {
        "root": "/repo",
        "results": [
            {
                "node": {"name": "render", "line": 4},
                "callers": [{"name": "main", "line": 10}],
                "flags": [True, False, None],
            },
            {
                "node": {"name": "save", "line": 8},
                "callers": [],
                "flags": [],
            },
        ],
        "metadata": {"complete": True, "count": 2},
    },
]


def _sample_node(index: int) -> dict[str, object]:
    return {
        "id": index,
        "name": f"symbol_{index}",
        "kind": "function",
        "qualified_name": f"package.module.symbol_{index}",
        "file_path": f"src/package/module_{index % 4}.py",
        "start_line": index * 7 + 1,
        "end_line": index * 7 + 5,
        "signature": f"def symbol_{index}(value: int) -> str",
        "docstring": "Return a stable representative value for codec measurement.",
    }


_NODES = [_sample_node(index) for index in range(12)]


def _sample_safety_response(operation: str) -> dict[str, object]:
    dependencies = [
        {
            "edge_kind": "calls",
            "call_site_line": 20 + index,
            "target": _NODES[0],
            "source": node,
        }
        for index, node in enumerate(_NODES[1:9])
    ]
    return {
        "operation": operation,
        "symbol": "package.module.symbol_0",
        "verdict": {
            "tier": "runtime_dependency",
            "rank": 0,
            "meaning": "A cross-file, non-test production path depends on this symbol.",
        },
        "recommended_action": "Preserve the indexed contract and migrate all dependents atomically.",
        "evidence": {
            "matches": [_NODES[0]],
            "callers": dependencies,
            "importers": [],
            "references": [],
            "production_dependents": dependencies,
            "external_dependents": dependencies,
            "internal_dependents": [],
            "test_coverage": {"present": False, "files": []},
            "complexity": [
                {
                    "qualified_name": "package.module.symbol_0",
                    "span_lines": 5,
                    "incoming_dependencies": len(dependencies),
                }
            ],
            "cross_repo_visibility": "unavailable",
            "index": {"present": True, "files": 24, "nodes": 144},
        },
    }


REPRESENTATIVE_TOOL_PAYLOADS: dict[str, object] = {
    "index_codebase": {
        "root": "/repo",
        "state": "idle",
        "files_processed": 24,
        "total_files": 24,
        "last_updated": "2026-08-22T12:00:00+00:00",
        "error": None,
        "total_chunks": 96,
    },
    "search_code": {
        "root": "/repo",
        "query": "symbol",
        "mode": "keyword",
        "total_chunks": 96,
        "results": [
            {
                "rank": index + 1,
                "score": round(1.0 - index / 20, 3),
                "file_path": f"src/package/module_{index % 4}.py",
                "start_line": index * 7 + 1,
                "end_line": index * 7 + 5,
                "text": f"def symbol_{index}(value): return value",
            }
            for index in range(12)
        ],
    },
    "clear_index": {"root": "/repo", "cleared": True},
    "get_indexing_status": {
        "root": "/repo",
        "state": "idle",
        "files_processed": 24,
        "total_files": 24,
        "last_updated": "2026-08-22T12:00:00+00:00",
        "error": None,
    },
    "index_graph": {
        "root": "/repo",
        "files_indexed": 24,
        "files_skipped": 0,
        "nodes_created": 144,
        "edges_created": 288,
        "errors": [],
    },
    "generate_context_map": {
        "root": "/repo",
        "changed": True,
        "token_count": 4200,
        "articles": [
            {
                "path": f".nexus/context/module-{index}.md",
                "title": f"Module {index}",
                "symbols": 18 + index,
                "tokens": 320 + index * 10,
            }
            for index in range(8)
        ],
    },
    "map_health": {
        "healthy": False,
        "issues": [
            {
                "kind": "stale",
                "path": f".nexus/context/module-{index}.md",
                "message": "Source fingerprint changed after map generation.",
            }
            for index in range(8)
        ],
    },
    "generate_knowledge_map": {
        "root": "/repo",
        "output_path": "/repo/.nexus/KNOWLEDGE.md",
        "notes": [
            {
                "path": f"docs/notes/decision-{index}.md",
                "category": "decision",
                "title": f"Decision {index}",
            }
            for index in range(8)
        ],
    },
    "code_search": {"root": "/repo", "query": "symbol", "results": _NODES},
    "code_callers": {
        "root": "/repo",
        "symbol": "symbol_0",
        "matches": 1,
        "results": [
            {"target": _NODES[0], "caller": node} for node in _NODES[1:]
        ],
    },
    "code_callees": {
        "root": "/repo",
        "symbol": "symbol_0",
        "matches": 1,
        "results": [
            {"caller": _NODES[0], "callee": node} for node in _NODES[1:]
        ],
    },
    "code_impact": {
        "root": "/repo",
        "symbol": "symbol_0",
        "matches": 1,
        "depth": 2,
        "results": [
            {"node": node, "impact": _NODES[:4]} for node in _NODES[:6]
        ],
    },
    "code_node": {"root": "/repo", "symbol": "symbol", "matches": _NODES},
    "code_context": {
        "root": "/repo",
        "symbol": "symbol_0",
        "matches": 1,
        "results": [
            {
                "node": node,
                "callers": _NODES[:3],
                "callees": _NODES[3:6],
                "siblings": _NODES[6:9],
            }
            for node in _NODES[:6]
        ],
    },
    "code_explore": {
        "root": "/repo",
        "symbol": "symbol_0",
        "matches": 1,
        "depth": 2,
        "results": [
            {
                "node": node,
                "callers": _NODES[:3],
                "callees": _NODES[3:6],
                "impact": _NODES[6:10],
            }
            for node in _NODES[:6]
        ],
    },
    "code_affected_tests": {
        "root": "/repo",
        "changed_files": ["src/package/module_0.py"],
        "depth": 5,
        "test_glob": None,
        "affected_tests": [f"tests/test_module_{index}.py" for index in range(12)],
    },
    "code_edit_safety": _sample_safety_response("edit"),
    "code_delete_safety": _sample_safety_response("delete"),
    "code_rename_safety": _sample_safety_response("rename"),
    "watch_for_changes": {
        "root": "/repo",
        "watcher_id": 12345,
        "debounce_ms": 2000,
        "status": "watching",
    },
}


@pytest.mark.parametrize("payload", ROUND_TRIP_PAYLOADS)
def test_compact_round_trip_preserves_json_structure(payload: object) -> None:
    encoded = codec.encode_response(payload, response_format="compact")
    assert encoded.startswith(f"{codec.WIRE_MARKER}\n")
    decoded = codec.decode_response(encoded)
    assert decoded == payload
    if isinstance(payload, dict):
        assert list(decoded) == list(payload)
    if isinstance(payload, dict) and payload.get("results"):
        assert [list(row) for row in decoded["results"]] == [
            list(row) for row in payload["results"]
        ]


def _random_json_payload(seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []
    for index in range(rng.randint(0, 20)):
        row: dict[str, object] = {"index": index, "active": bool(index % 2)}
        if rng.random() > 0.2:
            row["score"] = round(rng.random(), 6)
        if rng.random() > 0.35:
            row["note"] = None if rng.random() < 0.3 else f"note\t{index}\n\u2603"
        if rng.random() > 0.5:
            row["nested"] = {
                "tags": [f"t{index}", "NEXUS-CW/1"],
                "enabled": rng.choice([True, False]),
            }
        rows.append(row)
    return {
        "seed": seed,
        "label": f"payload-{seed}",
        "results": rows,
        "footer": {"count": len(rows), "nullable": None},
    }


def test_property_style_round_trip_for_deterministic_random_payloads() -> None:
    for seed in range(100):
        payload = _random_json_payload(seed)
        encoded = codec.encode_response(payload, response_format="compact")
        assert codec.decode_response(encoded) == payload


def test_encoding_is_byte_deterministic() -> None:
    payload = _random_json_payload(42)
    candidates = {
        codec.encode_response(payload, response_format="compact") for _ in range(20)
    }
    assert len(candidates) == 1


def test_json_default_preserves_existing_serialization() -> None:
    payload = {"snowman": "\u2603", "results": [{"rank": 1, "ok": True}]}
    assert codec.encode_response(payload) == json.dumps(payload)


def test_auto_mode_uses_measured_savings_threshold() -> None:
    small = {"ok": True}
    large = {
        "results": [
            {
                "rank": index,
                "file_path": f"src/module_{index}.py",
                "start_line": index * 10,
                "end_line": index * 10 + 8,
                "text": "def repeated_shape(): return 'value'",
            }
            for index in range(50)
        ]
    }

    assert not codec.encode_response(
        small, response_format="auto"
    ).startswith(codec.WIRE_MARKER)
    encoded = codec.encode_response(large, response_format="auto")
    assert encoded.startswith(codec.WIRE_MARKER)
    assert codec.measure_savings(large).savings_pct >= 15.0
    assert codec.decode_response(encoded) == large


def test_custom_threshold_controls_auto_mode() -> None:
    payload = {"results": [{"a": i, "b": i * 2} for i in range(20)]}
    savings = codec.measure_savings(payload).savings_pct
    compact = codec.encode_response(
        payload,
        response_format="auto",
        min_savings_pct=max(0.0, savings - 0.1),
    )
    json_output = codec.encode_response(
        payload,
        response_format="auto",
        min_savings_pct=min(100.0, savings + 0.1),
    )
    assert compact.startswith(codec.WIRE_MARKER)
    assert json.loads(json_output) == payload


def test_encoder_exception_falls_back_to_valid_json(monkeypatch) -> None:
    payload = {"results": [{"value": 1}]}

    def fail(_payload: object) -> str:
        raise RuntimeError("injected encoder failure")

    monkeypatch.setattr(codec, "_encode_compact", fail)
    result = codec.encode_response(payload, response_format="compact")
    assert json.loads(result) == payload


def test_compact_decode_failure_retries_json_without_propagating() -> None:
    payload = {"results": [{"value": 1}]}
    calls: list[str] = []

    def retry_json() -> str:
        calls.append("json")
        return json.dumps(payload)

    decoded = codec.decode_response(
        f"{codec.WIRE_MARKER}\nE\t{{broken", json_retry=retry_json
    )
    assert decoded == payload
    assert calls == ["json"]


@pytest.mark.parametrize(
    ("response_format", "threshold"),
    [("unknown", 15.0), ("auto", -1.0), ("auto", 101.0)],
)
def test_invalid_controls_fail_open_to_json(
    response_format: str, threshold: float
) -> None:
    payload = {"results": [{"value": 1}]}
    result = codec.encode_response(
        payload,
        response_format=response_format,
        min_savings_pct=threshold,
    )
    assert json.loads(result) == payload


def test_every_tool_exposes_response_format_controls() -> None:
    for tool in server._all_tools():
        properties = tool.model_dump(mode="json", by_alias=True)["inputSchema"][
            "properties"
        ]
        assert properties["response_format"]["enum"] == ["json", "compact", "auto"]
        assert properties["response_format"]["default"] == "json"
        assert properties["compact_min_savings_pct"]["default"] == 15.0


def test_response_boundary_preserves_json_default_and_formats_once() -> None:
    payload = {"results": [{"rank": index, "path": f"src/{index}.py"} for index in range(20)]}
    original = [TextContent(type="text", text=json.dumps(payload))]

    assert server._format_tool_response(original, {}) is original
    compact = server._format_tool_response(
        original,
        {"response_format": "compact", "compact_min_savings_pct": 15.0},
    )
    assert len(compact) == 1
    assert compact[0].text.startswith(codec.WIRE_MARKER)
    assert codec.decode_response(compact[0].text) == payload


def test_compact_payload_composes_with_consumer_compressor() -> None:
    marker = "<<ccr:0123456789ab 3_rows>>"
    payload = {
        "results": [
            {"rank": index, "path": f"src/{index}.py", "marker": marker}
            for index in range(30)
        ]
    }
    compact = codec.encode_response(payload, response_format="compact")
    compressed = compress_output(compact, persist=False)
    assert compressed.text == compact
    assert compressed.segments == []
    assert compressed.tokens_after == compressed.tokens_before
    assert codec.decode_response(compressed.text) == payload
    assert codec.decode_response(compact)["results"][0]["marker"] == marker


def test_readme_records_live_per_tool_measurements() -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    assert set(REPRESENTATIVE_TOOL_PAYLOADS) == {
        tool.name for tool in server._all_tools()
    }
    for tool_name, payload in REPRESENTATIVE_TOOL_PAYLOADS.items():
        measurement = codec.measure_savings(payload)
        selected = "compact" if measurement.savings_pct >= 15.0 else "json"
        expected_row = (
            f"| `{tool_name}` | {measurement.json_bytes:,} | "
            f"{measurement.compact_bytes:,} | {measurement.savings_pct:.1f}% | "
            f"`{selected}` |"
        )
        assert expected_row in readme


def test_codec_is_offline_and_credential_free(monkeypatch) -> None:
    for key, value in {
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "socks5://127.0.0.1:9",
        "API_KEY": "must-not-be-read",
    }.items():
        monkeypatch.setenv(key, value)

    payload = {"results": [{"rank": index, "path": f"src/{index}.py"} for index in range(20)]}
    encoded = codec.encode_response(payload, response_format="compact")
    assert codec.decode_response(encoded) == payload

    source = (Path(__file__).parents[1] / "src/nexus_code_search/response_codec.py").read_text(
        encoding="utf-8"
    ).lower()
    forbidden = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "api_key",
        "credential",
        "getenv",
        "environ",
    )
    assert not any(token in source for token in forbidden)
