"""Whole-tree contracts for the code-search offline guarantee."""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "nexus-code-search"


def _runtime_sources() -> list[Path]:
    sources = list((EXTENSION_ROOT / "src").rglob("*.py"))
    sources.extend((EXTENSION_ROOT / "benchmarks").glob("*.py"))
    sources.extend(
        REPO_ROOT / "catalog" / "hooks" / name
        for name in ("code-search-routing.sh", "code-search-routing.ps1")
    )
    return sources


def test_runtime_tree_has_no_outbound_or_model_acquisition_surface() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in _runtime_sources())
    forbidden = (
        r"(?m)^\s*(?:from|import)\s+(?:aiohttp|httpx|requests|urllib)\b",
        r"https?://",
        r"\b(?:snapshot_download|from_pretrained|hf_hub_download|download_model)\b",
    )
    assert not any(re.search(pattern, source, re.IGNORECASE) for pattern in forbidden)


def test_runtime_tree_has_no_secret_shaped_environment_read() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in _runtime_sources())
    secret = r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|credential)"
    environment = r"(?:getenv|environ|get_environment_variable|\$env:)"
    assert (
        re.search(
            fr"{environment}.*?{secret}|{secret}.*?{environment}",
            source,
            re.IGNORECASE,
        )
        is None
    )


def test_documented_policy_and_registry_classification_remain_exact() -> None:
    readme = (EXTENSION_ROOT / "README.md").read_text(encoding="utf-8")
    assert "zero outbound calls, zero API keys, zero model downloads" in readme

    matrix_path = REPO_ROOT / "docs" / "policy" / "mcp-reverse-engineering-matrix.md"
    matrix = matrix_path.read_text(encoding="utf-8")
    row = next(
        line
        for line in matrix.splitlines()
        if line.startswith("| `nexus-code-search` |")
    )
    assert "| `already-local` |" in row


def test_ci_runs_full_suite_and_benchmark_without_container_network(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "code-search.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    assert "test-network-blocked:" in workflow
    assert (
        "python scripts/ci/run.py --profile full --only code-search-offline "
        "--reports-dir reports" in workflow
    )

    monkeypatch.syspath_prepend(str(REPO_ROOT))

    from scripts.ci.profiles import groups_for

    group = next(group for group in groups_for("full") if group.name == "code-search-offline")
    assert len(group.commands) == 2
    build, run = group.commands
    assert build.platforms == run.platforms == ("linux",)
    assert list(build.argv[:3]) == ["docker", "build", "--tag"]
    assert "scripts/ci/code-search-offline.Dockerfile" in build.argv
    assert list(run.argv[:-1]) == [
        "docker", "run", "--rm", "--network", "none",
        "--env", "NEXUS_CODE_SEARCH_BLOCK_NETWORK=1",
        "--volume", f"{REPO_ROOT}:/workspace:ro",
        "nexus-code-search-offline", "bash", "-c",
    ]
    check = run.argv[-1]
    assert check.startswith("set -euo pipefail; ")
    assert "test -d /sys/class/net/lo" in check
    assert (
        "if find /sys/class/net -mindepth 1 -maxdepth 1 ! -name lo "
        "-print -quit | grep -q .; then exit 1; fi" in check
    )
    assert "python -m pytest extensions/nexus-code-search/tests/ -q -p no:cacheprovider;" in check
    assert (
        "cd extensions/nexus-code-search; python benchmarks/harness.py --check "
        "--work /tmp/nexus-code-search-benchmark "
        "--json-out /tmp/nexus-code-search-benchmark.json "
        "--markdown-out /tmp/nexus-code-search-benchmark.md" in check
    )


def test_process_guard_rejects_non_loopback_destination() -> None:
    if os.environ.get("NEXUS_CODE_SEARCH_BLOCK_NETWORK") != "1":
        return
    with pytest.raises(RuntimeError, match="network egress blocked"):
        socket.create_connection(("192.0.2.1", 443), timeout=0.01)
