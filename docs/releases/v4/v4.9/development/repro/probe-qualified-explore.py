"""Reproduce the Phase 3 public qualified-symbol contract gap without target writes.

Run from the repository root with the existing development Python environment.
Exit 1 means the advertised explore contract is still broken; 0 means repaired.
Only metadata and digests reach stdout; server diagnostics are discarded.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from builtins import ExceptionGroup
from pathlib import Path
from typing import TextIO

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[6]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "catalog/skills/code-review/security-review/scripts"))
import _graph_receipt as graph
import _safe_artifact as safe
from _target_manifest import build_target_manifest, manifest_digest


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


async def probe(errors: TextIO) -> dict:
    source = REPO / "extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/minimal/code"
    before = manifest_digest(build_target_manifest(source))
    report: dict = {"schema": "nexus.qualified-explore-probe/v1", "profile": "standard", "calls": [], "graph_receipts": []}
    with safe.owned_temp_root("nexus-appsec-probe-") as root:
        try:
            for path in sorted(source.iterdir()):
                if path.is_file():
                    safe.safe_copy_file(source, path, root / path.name)
            identity = {"run_fingerprint": digest({"source_manifest": before, "copy_manifest": manifest_digest(build_target_manifest(root))}), "target_root_fingerprint": digest(str(root)), "scope_fingerprint": digest([]), "routing_manifest_digest": digest("probe-only-no-routing"), "target_revision": "0" * 40}
            observed_index = None

            def index_digest() -> str:
                return digest([(p.relative_to(root).as_posix(), hashlib.sha256(safe.open_contained_bytes(root, p)).hexdigest()) for p in sorted((root / ".nexus/code-index").rglob("*")) if p.is_file()])
            env = {k: v for k, v in os.environ.items() if k in ("SystemRoot", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC")}
            env.update(PYTHONPATH=str(REPO / "extensions/nexus-code-search/src"), NEXUS_CODE_SEARCH_TOOL_PROFILE="standard", NEXUS_CODE_SEARCH_DENSE="0", PYTHONDONTWRITEBYTECODE="1")
            params = StdioServerParameters(command=sys.executable, args=["-m", "nexus_code_search"], env=env)
            async with stdio_client(params, errlog=errors) as (reader, writer), ClientSession(reader, writer) as session:
                await session.initialize()
                listing = await session.list_tools()
                names = {"code_callers", "code_callees", "code_impact", "code_node", "code_context", "code_explore", "index_graph", "get_indexing_status"}
                report["capabilities"] = [{"name": t.name, "schema_sha256": digest(t.inputSchema), "parameters": sorted(t.inputSchema["properties"]), "required": t.inputSchema.get("required", [])} for t in listing.tools if t.name in names]
                async def call(name: str, arguments: dict, case: str) -> dict:
                    started = time.monotonic_ns()
                    result = await asyncio.wait_for(session.call_tool(name, {"root": str(root), **arguments}), timeout=60)
                    assert not result.isError
                    duration_ms = (time.monotonic_ns() - started) // 1000000
                    payload = json.loads(result.content[0].text)
                    matches = payload.get("matches", 0)
                    report["calls"].append({"operation": name, "case": case, "input_sha256": digest({"root_fingerprint": digest(str(root)), **arguments}), "output_sha256": digest(payload), "fields": sorted(payload), "failed": bool(result.isError or payload.get("error")), "matches": matches if type(matches) is int else len(matches)})
                    if name in graph.OPERATIONS and case in {"qualified", "qualified-hop", "truncation-control", "missing-control"}:
                        receipt = graph.project(payload, operation=name, qualified_symbol=arguments["symbol"], parameters=arguments, identity=identity, receipt_id=f"G-{len(report['calls'])}", duration_ms=duration_ms, index_digest=observed_index, limit=1 if case == "truncation-control" else 100)
                        report["graph_receipts"].append(receipt)
                    return payload
                await call("index_graph", {}, "disposable-copy")
                observed_index = index_digest()
                node = await call("code_node", {"symbol": "helper"}, "plain")
                assert len(node["matches"]) == 1
                qualified = node["matches"][0]["qualified_name"]
                report["qualified_symbol_sha256"] = digest(qualified)
                for name in ("code_node", "code_callers", "code_callees", "code_impact", "code_context", "code_explore"):
                    args = {"symbol": qualified}
                    if name in ("code_impact", "code_explore"):
                        args["depth"] = 2
                    payload = await call(name, args, "qualified")
                    assert not payload.get("error")
                    count = len(payload["matches"]) if isinstance(payload["matches"], list) else payload["matches"]
                    assert count == 1
                    assert any(loc["symbol"] == graph.symbol_id(qualified) for loc in report["graph_receipts"][-1]["locations"]) or name == "code_callees"
                    if name == "code_callers":
                        caller = payload["results"][0]["caller"]["qualified_name"]
                    if name == "code_explore":
                        report["qualified_explore_failed"] = bool(payload.get("error")) or payload.get("matches") != 1
                hop = await call("code_callees", {"symbol": caller}, "qualified-hop")
                assert any(n["callee"]["qualified_name"] == qualified for n in hop["results"])
                await call("code_explore", {"symbol": "helper", "depth": 2}, "plain-control")
                absent = await call("code_explore", {"symbol": "missing.py::helper", "depth": 2}, "missing-control")
                assert absent.get("matches") == 0 and not absent.get("error")
                await call("code_context", {"symbol": qualified}, "truncation-control")
                report["index_unchanged_by_queries"] = index_digest() == observed_index
                assert report["index_unchanged_by_queries"]
                safe.safe_copy_file(source, source / "app.py", root / "duplicate.py")
                identity["run_fingerprint"] = digest({"source_manifest": before, "copy_manifest": manifest_digest(build_target_manifest(root))})
                await call("index_graph", {}, "ambiguity-copy")
                observed_index = index_digest()
                ambiguous = await call("code_explore", {"symbol": "helper", "depth": 2}, "ambiguity-control")
                assert ambiguous.get("matches") == 2
                report["ambiguous_index_unchanged_by_query"] = index_digest() == observed_index
                assert report["ambiguous_index_unchanged_by_query"]
                status = await call("get_indexing_status", {}, "chunk-status-only")
                report["chunk_status"] = {"state": status.get("state") if status.get("state") in ("idle", "indexing", "error") else "unknown", "last_updated_present": status.get("last_updated") is not None}
                report["graph_quality"] = "unknown"
            report["copy_index_exists"] = (root / ".nexus/code-index").is_dir()
        finally:
            after = manifest_digest(build_target_manifest(source))
            report.update(original_before_sha256=before, original_after_sha256=after, original_unchanged=before == after)
    report["owned_copy_cleaned"] = not root.exists()
    assert report["owned_copy_cleaned"]
    return report


if __name__ == "__main__":
    try:
        with open(os.devnull, "w") as errors:
            observed = asyncio.run(asyncio.wait_for(probe(errors), timeout=90))
    except AssertionError:
        print(json.dumps({"schema": "nexus.qualified-explore-probe/v1", "reason": "PROBE_CONTRACT_FAILED"}))
        raise SystemExit(1) from None
    except (ExceptionGroup, OSError, ValueError, TimeoutError) as exc:
        print(json.dumps({"schema": "nexus.qualified-explore-probe/v1", "reason": "PROBE_UNAVAILABLE", "exception_type_sha256": digest(type(exc).__name__)}))
        raise SystemExit(2) from None
    print(json.dumps(observed, indent=2, sort_keys=True))
    raise SystemExit(1 if observed["qualified_explore_failed"] or not observed["original_unchanged"] else 0)
