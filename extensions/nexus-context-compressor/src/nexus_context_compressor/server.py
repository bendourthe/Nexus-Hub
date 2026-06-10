"""Internal MCP server exposing context_compress + context_retrieve.

A local-only, zero-outbound MCP server modeled on ``nexus-web-fetch`` /
``nexus-skill-server``. It exposes two tools over stdio:

* ``context_compress`` -- compress a raw payload (tool output, a JSON dump, a
  code blob) through the deterministic engine, returning the compressed text plus
  token metrics. Any dropped span is persisted to the local CCR store so it can
  be fetched back.
* ``context_retrieve`` -- resolve a ``<<ccr:HASH N_rows>>`` marker (the
  placeholder a drop leaves behind) back to the exact original records.

Reversibility is the point: compression is non-lossy because the originals live
in a local content-hashed SQLite store, and an agent that needs a dropped span
calls ``context_retrieve`` to get it back.

The ``mcp`` dependency is an optional extra: this module imports cleanly without
it (the tool *logic* in :func:`do_compress` / :func:`do_retrieve` is pure and
dependency-light), and ``mcp`` is imported lazily inside :func:`run_server` only
when the server is actually launched. That keeps the engine library and CLI
usable on a machine that never installs the MCP surface.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from . import compress_output
from .ccr import NOT_FOUND, CCRStore, retrieve

logger = logging.getLogger("nexus-context-compressor")

SERVER_INSTRUCTIONS = """\
nexus-context-compressor: local-first, reversible context compression.

Tools (what / when):
  context_compress   Compress a raw payload (tool output, a JSON record dump, a
                     code blob) before it enters context. Returns the compressed
                     text plus token metrics. Structured content (JSON arrays,
                     code) is compressed; logs and prose pass through unchanged.
                     Any dropped span is persisted locally so it stays
                     retrievable -- compression is non-lossy.
  context_retrieve   Resolve a <<ccr:HASH N_rows>> marker (the placeholder a drop
                     leaves behind) back to the exact original records. Use it
                     when you compressed a payload and now need a dropped span
                     back. Returns {found: false} when the span was evicted or
                     the marker is unrecognized.

MCP Registry Policy:
  This server is `re-full` per the MCP Registry Policy
  (catalog/mcp-configs/mcp-servers.json): an owned, audited, local
  reverse-engineered replacement for the external `rtk` context-compression
  binary. It runs as a local Python subprocess, makes zero outbound calls,
  requires no API key, and transmits no source code, prompts, or query text to
  any third party. The CCR store is a local SQLite file under ~/.nexus-hub/cache/.

Related skills:
  - context-compression (orchestration) -- the human-facing methodology this
    engine is the programmatic counterpart to.
  - prompt-token-optimization (orchestration) -- token-budget hygiene guidance.
  - context-optimization (developer-experience) -- applying these optimizations
    to a project.
"""


def do_compress(payload: object, *, persist: bool = True) -> dict[str, Any]:
    """Compress ``payload`` and return a JSON-serializable result dict.

    The pure core of the ``context_compress`` tool, testable without ``mcp``.
    Never raises: an internal error degrades to an identity result with an
    ``error`` note so the caller still gets its payload back.
    """
    try:
        result = compress_output(payload, persist=persist)
        return {
            "compressed": result.text,
            "tokens_before": result.tokens_before,
            "tokens_after": result.tokens_after,
            "ratio": round(result.ratio, 4),
            "segments": len(result.segments),
        }
    except Exception as exc:  # noqa: BLE001 - never lose the caller's payload
        logger.exception("context_compress failed")
        text = payload if isinstance(payload, str) else str(payload)
        return {"compressed": text, "error": f"compression_failed: {exc}"}


def do_retrieve(marker: object) -> dict[str, Any]:
    """Resolve a CCR marker to its originals; the pure core of context_retrieve.

    Returns ``{"found": True, "original": [...]}`` on a hit or
    ``{"found": False, "marker": ...}`` on a miss. Never raises -- a store error
    or a malformed marker is a miss, not a crash.
    """
    marker_str = marker if isinstance(marker, str) else str(marker)
    try:
        with CCRStore() as store:
            original = retrieve(marker_str, store=store)
    except Exception as exc:  # noqa: BLE001 - a store error is a miss
        logger.exception("context_retrieve failed")
        return {"found": False, "marker": marker_str, "error": f"store_error: {exc}"}
    if original is NOT_FOUND:
        return {"found": False, "marker": marker_str}
    return {"found": True, "original": original}


_COMPRESS_SCHEMA = {
    "type": "object",
    "properties": {
        "payload": {
            "type": "string",
            "description": "The raw text to compress (tool output, JSON dump, code).",
        },
        "persist": {
            "type": "boolean",
            "default": True,
            "description": "Persist dropped spans to the local CCR store so they stay retrievable.",
        },
    },
    "required": ["payload"],
}

_RETRIEVE_SCHEMA = {
    "type": "object",
    "properties": {
        "marker": {
            "type": "string",
            "description": "A <<ccr:HASH N_rows>> marker, a marker object's value, or a bare 12-hex hash.",
        },
    },
    "required": ["marker"],
}


async def run_server() -> None:
    """Run the stdio MCP server. Imports ``mcp`` lazily (the optional extra)."""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    server = Server("nexus-context-compressor")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="context_compress",
                description=(
                    "Compress a raw payload before it enters context. Structured "
                    "content (JSON arrays, code) is compressed; logs and prose pass "
                    "through unchanged. Dropped spans are persisted locally and stay "
                    "retrievable via context_retrieve (non-lossy). Zero outbound."
                ),
                inputSchema=_COMPRESS_SCHEMA,
            ),
            Tool(
                name="context_retrieve",
                description=(
                    "Resolve a <<ccr:HASH N_rows>> marker back to the exact original "
                    "dropped records. Returns {found: false} when the span was evicted "
                    "or the marker is unrecognized."
                ),
                inputSchema=_RETRIEVE_SCHEMA,
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "context_compress":
            result = do_compress(
                arguments.get("payload", ""),
                persist=bool(arguments.get("persist", True)),
            )
        elif name == "context_retrieve":
            result = do_retrieve(arguments.get("marker", ""))
        else:
            result = {"error": f"Unknown tool: {name}"}
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    logger.info("Starting nexus-context-compressor MCP server (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options().model_copy(
            update={"instructions": SERVER_INSTRUCTIONS}
        )
        await server.run(read_stream, write_stream, init_options)


def serve_blocking() -> int:
    """Run the server to completion. Returns a process exit code."""
    import asyncio

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        return 0
    return 0
