"""Tests for scripts/nexus_mcp_benchmark.py.

The benchmark script is a standalone file under scripts/ that exercises
the three internal MCPs. These tests validate the CLI surface, the
output shape, the --append behavior, and the no-network guard.

The script is imported via importlib.util because scripts/ is not a
package. All tests run offline.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

# Locate the repo root from the test file's known location.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BENCHMARK_PATH = _REPO_ROOT / "scripts" / "nexus_mcp_benchmark.py"


def _load_benchmark_module():
    """Import the benchmark script as a module for direct testing."""
    if not _BENCHMARK_PATH.exists():
        pytest.skip(f"benchmark script not found at {_BENCHMARK_PATH}")
    spec = importlib.util.spec_from_file_location("nexus_mcp_benchmark", _BENCHMARK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["nexus_mcp_benchmark"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bench():
    return _load_benchmark_module()


def test_resolve_servers_all(bench) -> None:
    assert bench.resolve_servers(None) == ["skill-server", "code-search", "web-fetch"]
    assert bench.resolve_servers("all") == ["skill-server", "code-search", "web-fetch"]


def test_resolve_servers_single(bench) -> None:
    assert bench.resolve_servers("skill-server") == ["skill-server"]
    assert bench.resolve_servers("code-search") == ["code-search"]
    assert bench.resolve_servers("web-fetch") == ["web-fetch"]


def test_resolve_servers_rejects_unknown(bench) -> None:
    with pytest.raises(ValueError):
        bench.resolve_servers("unknown-server")


def test_summarize_empty(bench) -> None:
    summary = bench._summarize([])
    assert summary["count"] == 0
    assert summary["min_ms"] == 0.0


def test_summarize_single_value(bench) -> None:
    summary = bench._summarize([12.5])
    assert summary["count"] == 1
    assert summary["min_ms"] == 12.5
    assert summary["max_ms"] == 12.5
    assert summary["median_ms"] == 12.5


def test_summarize_multiple_values(bench) -> None:
    summary = bench._summarize([1.0, 2.0, 3.0, 4.0, 5.0])
    assert summary["count"] == 5
    assert summary["min_ms"] == 1.0
    assert summary["max_ms"] == 5.0
    assert summary["median_ms"] == 3.0


def test_detect_repo_root(bench) -> None:
    root = bench._detect_repo_root()
    assert (root / "AGENTS.md").exists()
    assert (root / "data").exists()


def test_no_network_guard_blocks_outbound(bench) -> None:
    """Verify the no-network-guard raises on a real outbound connect attempt."""
    with pytest.raises(bench.NetworkCalledDuringLocalBenchmarkError):
        with bench.no_network_guard():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # 8.8.8.8:53 is Google DNS - the attempt should be intercepted BEFORE
                # any actual network activity, because the guard raises synchronously.
                s.connect(("8.8.8.8", 53))
            finally:
                s.close()


def test_no_network_guard_restores_on_exit(bench) -> None:
    """Outside the context manager, socket.connect must work normally."""
    # Take a snapshot of the connect function; after the guard exits, it must
    # be the original again (testing the restoration behavior).
    before = socket.socket.connect
    with bench.no_network_guard():
        during = socket.socket.connect
        assert during is not before  # guard is patched in
    after = socket.socket.connect
    assert after is before  # original restored


def test_append_run_creates_file(bench, tmp_path: Path) -> None:
    output = tmp_path / "mcp-bench.json"
    payload = {"timestamp": "2026-04-24T00:00:00Z", "results": {}}
    bench.append_run(output, payload)
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["timestamp"] == "2026-04-24T00:00:00Z"


def test_append_run_retains_last_n(bench, tmp_path: Path) -> None:
    output = tmp_path / "mcp-bench.json"
    for i in range(bench.RETAIN_LAST_N + 3):
        payload = {"timestamp": f"run-{i}", "results": {}}
        bench.append_run(output, payload)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == bench.RETAIN_LAST_N
    # Last entry should be the most recent run.
    assert data[-1]["timestamp"] == f"run-{bench.RETAIN_LAST_N + 2}"


def test_append_run_handles_corrupt_history(bench, tmp_path: Path) -> None:
    output = tmp_path / "mcp-bench.json"
    output.write_text("not valid json", encoding="utf-8")
    bench.append_run(output, {"timestamp": "fresh", "results": {}})
    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["timestamp"] == "fresh"


def test_main_single_server_iterations_one(bench, tmp_path: Path, monkeypatch) -> None:
    """Smoke-run main() against the skill-server only with --iterations=1."""
    output = tmp_path / "mcp-bench.json"
    captured: dict[str, Any] = {}

    def fake_print(*args, **kwargs) -> None:
        # Capture the JSON payload printed at the end.
        if args and isinstance(args[0], str) and args[0].startswith("{"):
            captured["payload"] = args[0]

    monkeypatch.setattr("builtins.print", fake_print)

    rc = bench.main(["--server", "skill-server", "--iterations", "1", "--output", str(output), "--quiet"])
    assert rc == 0
    assert output.exists()
    history = json.loads(output.read_text(encoding="utf-8"))
    assert history
    latest = history[-1]
    assert "timestamp" in latest
    assert "python_version" in latest
    assert "results" in latest
    assert "nexus-skill-server" in latest["results"]
    # With --server=skill-server, other servers should NOT be benchmarked.
    assert "nexus-code-search" not in latest["results"]
    assert "nexus-web-fetch" not in latest["results"]
