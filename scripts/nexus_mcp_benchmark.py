"""Benchmark Nexus-Hub's internal MCP servers.

Measures round-trip latency for the handler functions of the three
internal MCPs (nexus-skill-server, nexus-code-search, nexus-web-fetch).
Pure-internal; policy-compliant; the harness itself refuses to open
outbound sockets during the skill-server and code-search phases.

Usage:
    python scripts/nexus_mcp_benchmark.py
    python scripts/nexus_mcp_benchmark.py --append --quiet --iterations 3
    python scripts/nexus_mcp_benchmark.py --server code-search
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import json
import logging
import os
import platform
import socket
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable

logger = logging.getLogger("nexus-mcp-benchmark")


DEFAULT_ITERATIONS = 5
DEFAULT_OUTPUT_PATH = "data/benchmarks/mcp.json"
RETAIN_LAST_N = 10

VALID_SERVERS = ("skill-server", "code-search", "web-fetch", "all")


# --- No-network guard ---------------------------------------------------

class NetworkCalledDuringLocalBenchmarkError(RuntimeError):
    """Raised when a local-only MCP benchmark attempts an outbound connection."""


_original_connect = socket.socket.connect


def _forbid_connect(self, address) -> None:
    """Replacement for socket.socket.connect that refuses any outbound attempt."""
    raise NetworkCalledDuringLocalBenchmarkError(
        f"Local-only MCP benchmark attempted an outbound connection to {address!r}. "
        "This is a policy violation: nexus-skill-server and nexus-code-search must "
        "make zero outbound calls."
    )


@contextlib.contextmanager
def no_network_guard():
    """Patch socket.socket.connect so outbound calls raise. Restore on exit."""
    socket.socket.connect = _forbid_connect  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = _original_connect  # type: ignore[assignment]


# --- Timing primitives --------------------------------------------------

def _time_ms(fn: Callable[[], Any]) -> float:
    start = time.perf_counter()
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        logger.debug("call raised during benchmark: %s", exc)
    return (time.perf_counter() - start) * 1000.0


def _summarize(timings_ms: Iterable[float]) -> dict:
    values = sorted(timings_ms)
    if not values:
        return {"min_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "count": 0}
    p95 = values[max(0, int(len(values) * 0.95) - 1)]
    return {
        "min_ms": round(values[0], 3),
        "median_ms": round(median(values), 3),
        "p95_ms": round(p95, 3),
        "max_ms": round(values[-1], 3),
        "count": len(values),
    }


# --- Per-server benchmark drivers --------------------------------------

def _benchmark_skill_server(repo_root: Path, iterations: int) -> dict:
    """Benchmark nexus-skill-server handlers. Zero outbound calls expected."""
    from nexus_skill_server.catalog import SkillCatalog
    from nexus_skill_server.config import ServerConfig
    from nexus_skill_server.search import SearchEngine
    from nexus_skill_server.types import DetailLevel

    config = ServerConfig(
        hub_root=repo_root,
        skills_json_path=repo_root / "data" / "skills.json",
        bundles_json_path=repo_root / "data" / "bundles.json"
        if (repo_root / "data" / "bundles.json").exists()
        else None,
        catalog_skills_dir=repo_root / "catalog" / "skills"
        if (repo_root / "catalog" / "skills").exists()
        else None,
    )
    catalog = SkillCatalog(config)
    catalog.load()
    engine = SearchEngine(config)
    if catalog.is_loaded:
        engine.build_index(catalog.get_all_skills_metadata(), catalog.version)

    queries = [
        ("search_skills:code semantic search", lambda: engine.search("code semantic search", 5)),
        ("search_skills:security audit", lambda: engine.search("security audit", 5)),
        ("search_skills:test generation", lambda: engine.search("test generation", 5)),
        ("get_skill:code-semantic-search", lambda: catalog.get_skill("code-semantic-search", DetailLevel.L0)),
        ("get_skill:rag-implementation", lambda: catalog.get_skill("rag-implementation", DetailLevel.L0)),
        ("list_categories", lambda: catalog.get_all_skills_metadata()),
    ]

    results: dict[str, dict] = {}
    with no_network_guard():
        for name, fn in queries:
            timings = [_time_ms(fn) for _ in range(iterations)]
            results[name] = _summarize(timings)

    return {
        "server": "nexus-skill-server",
        "skill_count": len(catalog.get_all_skills_metadata()) if catalog.is_loaded else 0,
        "results": results,
    }


def _benchmark_code_search(repo_root: Path, iterations: int) -> dict:
    """Benchmark nexus-code-search handlers against a tmp fixture tree."""
    from nexus_code_search.config import resolve_config, index_dir_for
    from nexus_code_search.server import (
        _handle_clear,
        _handle_index,
        _handle_search,
        _handle_status,
    )

    # Use a small fixture root to keep the benchmark fast and deterministic.
    fixture_root = Path(tempfile.mkdtemp(prefix="nexus-mcp-bench-"))
    (fixture_root / "src").mkdir()
    for i in range(10):
        (fixture_root / "src" / f"mod_{i}.py").write_text(
            f"def func_{i}():\n    return {i}\n\n\nclass Class{i}:\n    def method(self):\n        return {i}\n",
            encoding="utf-8",
        )

    config = resolve_config()
    args = {"root": str(fixture_root)}

    queries = [
        ("index_codebase:cold", lambda: _handle_index(args, config)),
        ("index_codebase:warm", lambda: _handle_index(args, config)),
        ("search_code:func_5", lambda: _handle_search({**args, "query": "func_5"}, config)),
        ("search_code:Class3", lambda: _handle_search({**args, "query": "Class3"}, config)),
        ("search_code:return", lambda: _handle_search({**args, "query": "return"}, config)),
        ("get_indexing_status", lambda: _handle_status(args, config)),
    ]

    try:
        results: dict[str, dict] = {}
        with no_network_guard():
            for name, fn in queries:
                timings = [_time_ms(fn) for _ in range(iterations)]
                results[name] = _summarize(timings)
            # Clear after benchmarking so the fixture does not linger beyond the fn call.
            _handle_clear(args, config)

        # Extract file count from the current manifest (if any).
        idx_dir = index_dir_for(fixture_root, config)
        file_count = 0
        if idx_dir.exists():
            manifest_path = idx_dir / "manifest.json"
            if manifest_path.exists():
                file_count = len(json.loads(manifest_path.read_text(encoding="utf-8")).get("file_hashes", {}))
    finally:
        import shutil

        shutil.rmtree(fixture_root, ignore_errors=True)

    return {
        "server": "nexus-code-search",
        "fixture_files": 10,
        "indexed_files_at_last_run": file_count,
        "results": results,
    }


def _benchmark_web_fetch(iterations: int) -> dict:
    """Benchmark nexus-web-fetch against a local HTTP fixture server.

    The no-network-guard is NOT applied here because web-fetch legitimately
    opens a socket to the fixture server on 127.0.0.1.
    """
    import asyncio

    from nexus_web_fetch.fetcher import fetch_url
    from nexus_web_fetch.ssrf_guard import GuardConfig

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = b"<html><head><title>Benchmark</title></head><body><main><p>Sample content for benchmark.</p></main></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:  # silence
            return

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://{host}:{port}/"
        cfg = GuardConfig(allow_private_networks=True)

        def _call() -> None:
            asyncio.run(fetch_url(url, config=cfg))

        results = {"fetch_url:readability": _summarize([_time_ms(_call) for _ in range(iterations)])}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    return {
        "server": "nexus-web-fetch",
        "results": results,
    }


# --- Orchestration ------------------------------------------------------

def _detect_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` (or the script's directory) to find the repo root."""
    current = (start or Path(__file__).resolve().parent).resolve()
    for _ in range(6):
        if (current / "AGENTS.md").exists() and (current / "data").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not detect Nexus-Hub repo root")


def run_benchmarks(servers: list[str], iterations: int, repo_root: Path) -> dict:
    """Run the selected server benchmarks and return a full result payload."""
    payload: dict[str, Any] = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "iterations": iterations,
        "results": {},
    }

    if "skill-server" in servers:
        payload["results"]["nexus-skill-server"] = _benchmark_skill_server(repo_root, iterations)
    if "code-search" in servers:
        payload["results"]["nexus-code-search"] = _benchmark_code_search(repo_root, iterations)
    if "web-fetch" in servers:
        payload["results"]["nexus-web-fetch"] = _benchmark_web_fetch(iterations)

    return payload


def resolve_servers(arg: str | None) -> list[str]:
    """Resolve the --server argument into a concrete server list."""
    if arg in (None, "all"):
        return ["skill-server", "code-search", "web-fetch"]
    if arg not in VALID_SERVERS:
        raise ValueError(f"Invalid --server={arg!r}. Expected one of: {VALID_SERVERS}")
    return [arg]


def append_run(output_path: Path, payload: dict, retain: int = RETAIN_LAST_N) -> None:
    """Append the run to the output JSON file, retaining only the last `retain` runs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except (json.JSONDecodeError, OSError):
            history = []
    history.append(payload)
    history = history[-retain:]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Nexus-Hub's internal MCPs")
    parser.add_argument(
        "--server",
        choices=VALID_SERVERS,
        default="all",
        help="Which server to benchmark (default: all)",
    )
    parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations per query (default: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=f"Append results to {DEFAULT_OUTPUT_PATH} (retains last {RETAIN_LAST_N} runs)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override output path (implies --append behavior)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable output; emit JSON only",
    )
    args = parser.parse_args(argv)

    if args.iterations <= 0:
        parser.error("--iterations must be a positive integer")

    try:
        repo_root = _detect_repo_root()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    servers = resolve_servers(args.server)

    if not args.quiet:
        print(f"nexus-mcp-benchmark: root={repo_root}, servers={servers}, iterations={args.iterations}")

    payload = run_benchmarks(servers, args.iterations, repo_root)

    if args.append or args.output:
        output_path = args.output or (repo_root / DEFAULT_OUTPUT_PATH)
        append_run(output_path, payload)
        if not args.quiet:
            print(f"appended to {output_path}")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
