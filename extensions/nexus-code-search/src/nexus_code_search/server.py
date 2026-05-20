"""FastMCP server exposing the four code-search tools.

Tools: index_codebase, search_code, clear_index, get_indexing_status.
All tool handlers are synchronous wrappers over the underlying logic;
indexing large trees runs inline (the MCP client can poll
get_indexing_status; background-thread indexing is reserved for v1.1.0
when the dense-embedding path makes inline indexing expensive).
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nexus_code_search.config import CodeSearchConfig, index_dir_for, resolve_config
from nexus_code_search.indexer import index_codebase
from nexus_code_search.search_keyword import KeywordIndex
from nexus_code_search.store import clear_index as store_clear_index
from nexus_code_search.store import index_lock, load_index
from nexus_code_search.types import IndexState, IndexStatus

logger = logging.getLogger("nexus-code-search")


def _dataclass_to_dict(obj) -> dict:
    """Serialize dataclass + enum to a JSON-safe dict."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    raise TypeError(f"Not serializable: {type(obj)!r}")


async def run_server() -> None:
    config = resolve_config()
    server = Server("nexus-code-search")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="index_codebase",
                description=(
                    "Walk a codebase, chunk source files, and persist a content-hash index. "
                    "Skips unchanged files on re-index (set force=True to rebuild from scratch). "
                    "Local-only; no network calls."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root": {
                            "type": "string",
                            "description": "Absolute or relative path to the codebase root",
                        },
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": "If True, re-chunk every file regardless of prior hashes",
                        },
                    },
                    "required": ["root"],
                },
            ),
            Tool(
                name="search_code",
                description=(
                    "Search the indexed codebase for a query. v1.0.0 accepts mode='keyword' "
                    "only; mode='hybrid' is reserved for v1.1.0 when dense retrieval lands."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root": {
                            "type": "string",
                            "description": "Codebase root that was previously indexed",
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query (natural language or keywords)",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["keyword"],
                            "default": "keyword",
                            "description": "Retrieval mode. Only 'keyword' in v1.0.0.",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["root", "query"],
                },
            ),
            Tool(
                name="clear_index",
                description="Remove the on-disk index for a given codebase root.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                    },
                    "required": ["root"],
                },
            ),
            Tool(
                name="get_indexing_status",
                description="Return the current indexing state for a given codebase root.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                    },
                    "required": ["root"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "index_codebase":
                return _handle_index(arguments, config)
            if name == "search_code":
                return _handle_search(arguments, config)
            if name == "clear_index":
                return _handle_clear(arguments, config)
            if name == "get_indexing_status":
                return _handle_status(arguments, config)
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Tool %s failed", name)
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    logger.info("Starting nexus-code-search (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def _resolve_root(arguments: dict) -> Path:
    raw = arguments.get("root")
    if not raw:
        raise ValueError("`root` argument is required")
    return Path(raw).expanduser().resolve()


def _handle_index(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root path does not exist or is not a directory: {root}")
    force = bool(arguments.get("force", False))

    index_dir = index_dir_for(root, config)

    try:
        with index_lock(index_dir):
            chunks, manifest = index_codebase(root, config, index_dir, force=force)
    except BlockingIOError:
        status = IndexStatus(
            root=str(root),
            state=IndexState.RUNNING,
            error="Another index operation is in progress for this root",
        )
        return [TextContent(type="text", text=json.dumps(status.to_dict()))]

    status = IndexStatus(
        root=str(root),
        state=IndexState.IDLE,
        files_processed=len(manifest.file_hashes),
        total_files=len(manifest.file_hashes),
        last_updated=manifest.indexed_at,
    )
    payload = {
        **status.to_dict(),
        "total_chunks": manifest.total_chunks,
    }
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_search(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    query = arguments.get("query", "")
    mode = arguments.get("mode", "keyword")
    limit = int(arguments.get("limit", 10))

    if mode != "keyword":
        raise NotImplementedError(
            "nexus-code-search v1.0.0 supports mode='keyword' only. "
            "Hybrid retrieval (mode='hybrid') is planned for v1.1.0 with a local ONNX "
            "embedding backend and a sqlite-vec vector store."
        )

    index_dir = index_dir_for(root, config)
    chunks, manifest = load_index(index_dir)
    if not chunks:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "results": [],
                        "note": f"No index found at {index_dir}. Run index_codebase first.",
                    }
                ),
            )
        ]

    idx = KeywordIndex.build(chunks)
    results = idx.search(query, limit=limit)
    payload = {
        "root": str(root),
        "query": query,
        "mode": mode,
        "total_chunks": len(chunks),
        "results": [
            {
                "rank": r.rank,
                "score": r.score,
                "file_path": r.chunk.file_path,
                "start_line": r.chunk.start_line,
                "end_line": r.chunk.end_line,
                "text": r.chunk.text,
            }
            for r in results
        ],
    }
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_clear(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    index_dir = index_dir_for(root, config)
    removed = store_clear_index(index_dir)
    payload = {"root": str(root), "cleared": removed}
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_status(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    index_dir = index_dir_for(root, config)
    chunks, manifest = load_index(index_dir)

    if manifest is None:
        status = IndexStatus(root=str(root), state=IndexState.IDLE)
    else:
        status = IndexStatus(
            root=str(root),
            state=IndexState.IDLE,
            files_processed=len(manifest.file_hashes),
            total_files=len(manifest.file_hashes),
            last_updated=manifest.indexed_at,
        )
    return [TextContent(type="text", text=json.dumps(status.to_dict()))]
