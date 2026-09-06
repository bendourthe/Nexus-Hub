"""Local context-provider extension-point contracts."""

from __future__ import annotations

import json
import socket
from pathlib import Path

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.frameworks import CONTEXT_PROVIDERS
from nexus_code_search.frameworks.markdown import MarkdownContextProvider
from nexus_code_search.server import _handle_graph_query
from nexus_code_search.types import EdgeKind, NodeKind


def test_provider_registry_is_intentionally_small() -> None:
    assert [provider.name for provider in CONTEXT_PROVIDERS] == ["markdown"]


def test_markdown_provider_declares_patterns_and_emits_heading_graph() -> None:
    provider = MarkdownContextProvider()
    path = Path("docs/architecture.md")
    source = b"# Architecture\n\n## Local search\n\n### Failure modes\n"

    assert provider.file_patterns == ("*.md",)
    assert provider.applies_to(path)
    assert not provider.applies_to(Path("service.py"))

    nodes, edges = provider.resolve(path, source, [])
    assert [node.name for node in nodes] == [
        "Architecture",
        "Local search",
        "Failure modes",
    ]
    assert all(node.kind is NodeKind.MODULE for node in nodes)
    assert [edge.kind for edge in edges] == [
        EdgeKind.CONTAINS,
        EdgeKind.CONTAINS,
    ]


def test_orchestrator_indexes_provider_files_and_graph_is_searchable(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "OPERATIONS.md").write_text(
        "# Operations\n\n## Offline Recovery Contract\n",
        encoding="utf-8",
    )

    def reject_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("context provider attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    config = CodeSearchConfig(hub_root=None)
    with ExtractionOrchestrator(
        tmp_path, config, tmp_path / ".nexus" / "code-index"
    ) as orchestrator:
        stats = orchestrator.run(force=True)

    assert stats.files_indexed == 2
    contents = _handle_graph_query(
        "code_search",
        {"root": str(tmp_path), "query": "Offline Recovery Contract"},
        config,
    )
    payload = json.loads(contents[0].text)
    assert payload["results"][0]["name"] == "Offline Recovery Contract"
    assert payload["results"][0]["file_path"] == "OPERATIONS.md"


def test_provider_modules_have_no_egress_surface() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "nexus_code_search" / "frameworks"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root / "base.py", root / "markdown.py")
    ).lower()
    forbidden = ("requests", "httpx", "urllib", "socket", "api_key", "credential")
    assert not any(token in sources for token in forbidden)
