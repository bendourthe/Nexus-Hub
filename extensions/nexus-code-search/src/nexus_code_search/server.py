"""FastMCP server exposing the code-search and graph tools.

v1.0 tools (keyword chunk index):
    index_codebase, search_code, clear_index, get_indexing_status

v2.0 tools (tree-sitter AST graph):
    index_graph              Build / refresh the SQLite AST graph for a repo.
    code_search              FTS5 search over graph node names (name-scoped by
                             default; all_fields=true widens to qualified_name
                             + docstring).
    code_callers             Direct callers of a symbol.
    code_callees             Direct callees of a symbol.
    code_impact              Blast-radius traversal.
    code_node                Resolve a symbol by name / qualified_name.
    code_context             Node + callers + callees + siblings in one call.
    code_explore             Combined search + traversal payload.
    watch_for_changes        Start a debounced file watcher (background thread).

All handlers are synchronous wrappers over the underlying logic; indexing
runs inline (clients can poll get_indexing_status).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nexus_code_search.config import CodeSearchConfig, index_dir_for, resolve_config
from nexus_code_search.contextmap import generate_context_map
from nexus_code_search.contextmap.knowledge import generate_knowledge_map
from nexus_code_search.contextmap.maphealth import lint_context_map
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph import GraphQueryManager, affected_tests
from nexus_code_search.graph.safety import evaluate_safety
from nexus_code_search.indexer import index_codebase
from nexus_code_search.response_codec import (
    DEFAULT_MIN_SAVINGS_PCT,
    RESPONSE_FORMATS,
    encode_response,
)
from nexus_code_search.search_dense import DenseSearchConfig, hybrid_search
from nexus_code_search.search_keyword import KeywordIndex
from nexus_code_search.store import clear_index as store_clear_index
from nexus_code_search.store import index_lock, load_index
from nexus_code_search.tool_profiles import (
    TOOL_MINIMUM_PROFILE,
    definition_token_count,
    tools_for_profile,
)
from nexus_code_search.types import IndexState, IndexStatus

logger = logging.getLogger("nexus-code-search")

__all__ = ["TOOL_MINIMUM_PROFILE"]

SERVER_INSTRUCTIONS = """\
nexus-code-search: AST-aware semantic search over a local codebase.

Tools (what / when):
  index_codebase        Walk a repo, chunk source files, persist a keyword
                        index. Run once per fresh checkout; subsequent calls
                        skip unchanged files. Set force=True to rebuild.
  search_code           Keyword search over the chunk index. Returns ranked
                        chunks with file paths and line ranges.
  clear_index           Remove the keyword + graph indices for a repo root.
  get_indexing_status   Report current state (IDLE / RUNNING) and counts.
  index_graph           v2.0: build the tree-sitter AST graph (nodes / edges
                        / FTS5) for Python + TypeScript source files.
  generate_context_map  Compile a committed .nexus/CONTEXT-MAP.md + a
                        .nexus/context/ article set from the graph. A cheap
                        cold-start map the AI reads once; deterministic,
                        local-only, writes only under .nexus/. Run index_graph
                        first; force=True bypasses the unchanged-graph no-op.
  code_search           v2.0: full-text search over graph node names
                        (name-scoped by default; all_fields=true also matches
                        qualified_name + docstring); returns symbol records.
  code_callers          v2.0: every node that has a `calls` edge into this
                        symbol. Useful for "who calls X" questions.
  code_callees          v2.0: every node this symbol has a `calls` edge to.
  code_impact           v2.0: BFS over calls + references + extends +
                        implements + overrides edges up to `depth` hops.
  code_node             v2.0: resolve a symbol by name or qualified_name.
  code_context          v2.0: one-shot node + callers + callees + siblings.
  code_explore          v2.0: combined search + traversal in a single call.
  code_edit_safety      Read-only mutation preflight: regression risk and the
                        behavior or contract an edit must preserve.
  code_delete_safety    Read-only mutation preflight: indexed dependents that
                        must move before a symbol can be removed.
  code_rename_safety    Read-only mutation preflight: indexed callers,
                        importers, and references that must rename together.
  watch_for_changes     v2.0: start a debounced file watcher in a background
                        thread that re-indexes changed files.
  code_affected_tests   v2.0: given a list of changed files, return every
                        test file in the index whose code transitively
                        imports any of them. CI-friendly impact analysis.

MCP Registry Policy:
  This server is `already-local` per the MCP Registry Policy
  (catalog/mcp-configs/mcp-servers.json). Zero outbound calls; zero
  credentials; chunks + AST graph live entirely on the local filesystem
  under <repo>/.nexus/code-index/.

Related skill:
  The `code-semantic-search` skill (ai-development category) covers
  retrieval strategy: when to use semantic vs keyword search, how to
  scope queries, and how to consume the ranked results. Load it via
  the nexus-skill-server with search_skills(query="code-semantic-search").
"""


async def run_server() -> None:
    config = resolve_config()
    server = Server("nexus-code-search")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _tools_for_profile(config.tool_profile)

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            result = _dispatch_tool(name, arguments, config)
            return _format_tool_response(result, arguments)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Tool %s failed", name)
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    logger.info("Starting nexus-code-search (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options().model_copy(
            update={"instructions": SERVER_INSTRUCTIONS}
        )
        await server.run(read_stream, write_stream, init_options)


def _dispatch_tool(
    name: str, arguments: dict, config: CodeSearchConfig
) -> list[TextContent]:
    if name == "index_codebase":
        return _handle_index(arguments, config)
    if name == "search_code":
        return _handle_search(arguments, config)
    if name == "clear_index":
        return _handle_clear(arguments, config)
    if name == "get_indexing_status":
        return _handle_status(arguments, config)
    if name == "index_graph":
        return _handle_index_graph(arguments, config)
    if name == "generate_context_map":
        return _handle_generate_context_map(arguments, config)
    if name == "map_health":
        return _handle_map_health(arguments, config)
    if name == "generate_knowledge_map":
        return _handle_generate_knowledge_map(arguments)
    if name in (
        "code_search",
        "code_callers",
        "code_callees",
        "code_impact",
        "code_node",
        "code_context",
        "code_explore",
    ):
        return _handle_graph_query(name, arguments, config)
    if name == "watch_for_changes":
        return _handle_watch(arguments, config)
    if name == "code_affected_tests":
        return _handle_affected_tests(arguments, config)
    if name in ("code_edit_safety", "code_delete_safety", "code_rename_safety"):
        return _handle_safety_check(name, arguments, config)
    return [
        TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))
    ]


def _format_tool_response(
    contents: list[TextContent], arguments: dict
) -> list[TextContent]:
    response_format = arguments.get("response_format", "json")
    if response_format == "json":
        return contents
    threshold = arguments.get(
        "compact_min_savings_pct", DEFAULT_MIN_SAVINGS_PCT
    )
    formatted: list[TextContent] = []
    for content in contents:
        try:
            payload = json.loads(content.text)
            text = encode_response(
                payload,
                response_format=response_format,
                min_savings_pct=threshold,
            )
        except Exception:  # noqa: BLE001 - preserve the valid handler response
            text = content.text
        formatted.append(TextContent(type="text", text=text))
    return formatted


def _response_format_properties() -> dict[str, dict]:
    return {
        "response_format": {
            "type": "string",
            "enum": list(RESPONSE_FORMATS),
            "default": "json",
            "description": (
                "Response encoding: json preserves compatibility, compact forces "
                "Nexus Compact Wire, and auto uses it only when byte savings meet "
                "compact_min_savings_pct."
            ),
        },
        "compact_min_savings_pct": {
            "type": "number",
            "default": DEFAULT_MIN_SAVINGS_PCT,
            "minimum": 0.0,
            "maximum": 100.0,
            "description": "Minimum UTF-8 byte savings required by auto mode.",
        },
    }


def _tool_input_schema(tool: Tool) -> dict:
    """Return the MCP tool schema across SDK 1.x and 2.x field names."""
    schema = getattr(tool, "inputSchema", None)
    if schema is not None:
        return schema
    return tool.input_schema


def _safety_tool_definitions(symbol_arg: dict) -> list[Tool]:
    definitions = (
        (
            "code_edit_safety",
            "Return one read-only verdict for modifying a symbol, the contract to preserve, and concrete local graph evidence.",
        ),
        (
            "code_delete_safety",
            "Return one read-only verdict for deleting a symbol, who would break, and concrete local graph evidence.",
        ),
        (
            "code_rename_safety",
            "Return one read-only verdict for renaming a symbol, what must move together, and concrete local graph evidence.",
        ),
    )
    return [
        Tool(
            name=name,
            description=f"{description} Local-only; never mutates the index or tree.",
            inputSchema={
                "type": "object",
                "properties": dict(symbol_arg),
                "required": ["root", "symbol"],
            },
        )
        for name, description in definitions
    ]


def _all_tools() -> list[Tool]:
    root_arg = {
        "root": {
            "type": "string",
            "description": "Absolute or relative path to the codebase root",
        }
    }
    symbol_arg = {
        "root": root_arg["root"],
        "symbol": {
            "type": "string",
            "description": "Symbol name or qualified_name (e.g. `helper` or `module.Class.method`).",
        },
    }
    tools = [
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
                    **root_arg,
                    "force": {"type": "boolean", "default": False},
                },
                "required": ["root"],
            },
        ),
        Tool(
            name="search_code",
            description=(
                "Keyword search over the indexed chunk corpus, with an optional "
                "offline hybrid mode that loads only pre-placed local weights."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "query": {"type": "string"},
                    "mode": {
                        "type": "string",
                        "enum": ["keyword", "hybrid"],
                        "default": "keyword",
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
            description="Remove the on-disk indices (keyword + graph) for a given codebase root.",
            inputSchema={
                "type": "object",
                "properties": root_arg,
                "required": ["root"],
            },
        ),
        Tool(
            name="get_indexing_status",
            description="Return the current indexing state for a given codebase root.",
            inputSchema={
                "type": "object",
                "properties": root_arg,
                "required": ["root"],
            },
        ),
        Tool(
            name="index_graph",
            description=(
                "Build the tree-sitter AST graph (nodes + edges + FTS) for Python and "
                "TypeScript files under `root`. Idempotent; unchanged files are skipped."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "force": {"type": "boolean", "default": False},
                },
                "required": ["root"],
            },
        ),
        Tool(
            name="generate_context_map",
            description=(
                "Compile a committed .nexus/CONTEXT-MAP.md (plus a .nexus/context/ "
                "article set) from the AST graph so an AI reads the codebase map "
                "once at session start instead of re-exploring files. Deterministic "
                "and local-only; writes only under <root>/.nexus/ (never CLAUDE.md / "
                "AGENTS.md). Unchanged graphs are a no-op unless force=True. Run "
                "index_graph first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "force": {"type": "boolean", "default": False},
                },
                "required": ["root"],
            },
        ),
        Tool(
            name="map_health",
            description=(
                "Lint the compiled context map under <root>/.nexus/: orphan "
                "articles (not linked from the index), missing backlinks, and "
                "staleness (source changed since the map was generated). "
                "Deterministic and local-only; returns a health report."
            ),
            inputSchema={
                "type": "object",
                "properties": root_arg,
                "required": ["root"],
            },
        ),
        Tool(
            name="generate_knowledge_map",
            description=(
                "Compile a committed <root>/.nexus/KNOWLEDGE.md from the Markdown "
                "notes under `notes_path` (default: root): key decisions, open "
                "questions, and a categorized note index (decision / meeting / "
                "retro / spec / research). Deterministic, local-only, graph-"
                "independent; writes only under <root>/.nexus/."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "notes_path": {
                        "type": "string",
                        "description": "Folder of Markdown notes (default: root).",
                    },
                },
                "required": ["root"],
            },
        ),
        Tool(
            name="code_search",
            description=(
                "FTS5 search over graph node names. Scoped to the symbol-name "
                "column by default for precision; set all_fields=true to also "
                "match qualified_names and docstrings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "query": {"type": "string"},
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 200,
                    },
                    "all_fields": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Match name + qualified_name + docstring instead of "
                            "the name column only. Use for docstring or "
                            "path-segment search."
                        ),
                    },
                },
                "required": ["root", "query"],
            },
        ),
        Tool(
            name="code_callers",
            description="Return every node that has a `calls` edge into the named symbol.",
            inputSchema={
                "type": "object",
                "properties": symbol_arg,
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_callees",
            description="Return every node the named symbol has a `calls` edge to.",
            inputSchema={
                "type": "object",
                "properties": symbol_arg,
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_impact",
            description=(
                "BFS over impact-bearing edges (calls + references + extends + implements + "
                "overrides) up to `depth` hops out and in. Use for change blast-radius."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **symbol_arg,
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 6,
                    },
                },
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_node",
            description="Resolve a symbol by name or qualified_name. Returns matching nodes.",
            inputSchema={
                "type": "object",
                "properties": symbol_arg,
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_context",
            description="Return node + callers + callees + siblings (one-shot context window).",
            inputSchema={
                "type": "object",
                "properties": symbol_arg,
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_explore",
            description="Combined search + callers + callees + impact in one payload.",
            inputSchema={
                "type": "object",
                "properties": {
                    **symbol_arg,
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 6,
                    },
                },
                "required": ["root", "symbol"],
            },
        ),
        Tool(
            name="code_affected_tests",
            description=(
                "Given a list of changed files, return every test file in the index whose "
                "code transitively imports any of them. Conservative (false-positives favored "
                "over false-negatives)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths of files that were changed (relative to root or absolute).",
                    },
                    "depth": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "test_glob": {
                        "type": "string",
                        "description": "Optional POSIX glob to filter test files (e.g. 'tests/**/*.py').",
                    },
                },
                "required": ["root", "changed_files"],
            },
        ),
        Tool(
            name="watch_for_changes",
            description=(
                "Start a debounced file watcher in a background thread. Re-indexes changed "
                "source files into the graph. Returns immediately; the watcher runs until "
                "the server stops or `stop_watching` is called."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    **root_arg,
                    "debounce_ms": {
                        "type": "integer",
                        "default": 2000,
                        "minimum": 100,
                        "maximum": 60000,
                    },
                },
                "required": ["root"],
            },
        ),
    ]
    tools.extend(_safety_tool_definitions(symbol_arg))
    for tool in tools:
        _tool_input_schema(tool)["properties"].update(_response_format_properties())
    return tools


def _tools_for_profile(profile: str) -> list[Tool]:
    """Return the tool definitions exposed by ``profile``.

    Unknown profiles fail open to the full surface. Profile selection is a
    token-cost control, not an authorization boundary.
    """
    return tools_for_profile(profile, _all_tools())


def tool_definition_token_count(profile: str) -> int:
    """Estimate tokens for the serialized MCP definitions in ``profile``."""
    return definition_token_count(_tools_for_profile(profile))


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

    if mode not in ("keyword", "hybrid"):
        raise NotImplementedError(
            "search_code supports mode='keyword' or mode='hybrid'. Use code_search "
            "for the AST graph full-text surface."
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
                        "note": f"No keyword index found at {index_dir}. Run index_codebase first.",
                    }
                ),
            )
        ]

    requested_mode = mode
    degraded = False
    hint = None
    if mode == "hybrid":
        outcome = hybrid_search(
            chunks,
            query,
            limit=limit,
            config=DenseSearchConfig(
                enabled=config.dense_enabled,
                model_dir=config.dense_model_dir,
            ),
        )
        results = outcome.results
        mode = outcome.mode
        degraded = outcome.degraded
        hint = outcome.hint
    else:
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
    if requested_mode == "hybrid":
        payload.update(
            {
                "requested_mode": requested_mode,
                "degraded": degraded,
                "hint": hint,
            }
        )
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_clear(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    index_dir = index_dir_for(root, config)
    removed = store_clear_index(index_dir)
    # Also drop the graph database file if present.
    db_path = index_dir / "codegraph.db"
    if db_path.exists():
        try:
            db_path.unlink()
            removed = True
        except OSError:
            pass
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


def _handle_index_graph(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root path does not exist or is not a directory: {root}")
    force = bool(arguments.get("force", False))
    index_dir = index_dir_for(root, config)
    with ExtractionOrchestrator(root, config, index_dir) as orch:
        stats = orch.run(force=force)
    payload = {"root": str(root), **stats.to_dict()}
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_generate_context_map(
    arguments: dict, config: CodeSearchConfig
) -> list[TextContent]:
    root = _resolve_root(arguments)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root path does not exist or is not a directory: {root}")
    force = bool(arguments.get("force", False))
    index_dir = index_dir_for(root, config)
    result = generate_context_map(root, index_dir, force=force)
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


def _handle_generate_knowledge_map(arguments: dict) -> list[TextContent]:
    root = _resolve_root(arguments)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root path does not exist or is not a directory: {root}")
    notes_raw = arguments.get("notes_path")
    notes_path = Path(notes_raw).expanduser().resolve() if notes_raw else None
    result = generate_knowledge_map(root, notes_path)
    return [TextContent(type="text", text=json.dumps(result.to_dict()))]


def _handle_map_health(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    root = _resolve_root(arguments)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root path does not exist or is not a directory: {root}")
    index_dir = index_dir_for(root, config)
    report = lint_context_map(root, index_dir)
    return [TextContent(type="text", text=json.dumps(report.to_dict()))]


def _handle_graph_query(
    name: str, arguments: dict, config: CodeSearchConfig
) -> list[TextContent]:
    root = _resolve_root(arguments)
    index_dir = index_dir_for(root, config)
    conn = open_database(index_dir)
    try:
        qm = GraphQueryManager(conn)
        if name == "code_search":
            query = arguments.get("query", "")
            limit = int(arguments.get("limit", 20))
            all_fields = bool(arguments.get("all_fields", False))
            payload = {
                "root": str(root),
                "query": query,
                "results": qm.search(query, limit=limit, all_columns=all_fields),
            }
        elif name == "code_callers":
            symbol = arguments.get("symbol", "")
            payload = {"root": str(root), **qm.callers_of(symbol)}
        elif name == "code_callees":
            symbol = arguments.get("symbol", "")
            payload = {"root": str(root), **qm.callees_of(symbol)}
        elif name == "code_impact":
            symbol = arguments.get("symbol", "")
            depth = int(arguments.get("depth", 2))
            payload = {"root": str(root), **qm.impact_of(symbol, depth=depth)}
        elif name == "code_node":
            symbol = arguments.get("symbol", "")
            matches = qm._resolve_symbol(symbol, None)
            payload = {
                "root": str(root),
                "symbol": symbol,
                "matches": [_node_to_payload(n) for n in matches],
            }
        elif name == "code_context":
            symbol = arguments.get("symbol", "")
            payload = {"root": str(root), **qm.context_for(symbol)}
        elif name == "code_explore":
            symbol = arguments.get("symbol", "")
            depth = int(arguments.get("depth", 2))
            payload = {"root": str(root), **qm.explore(symbol, depth=depth)}
        else:
            payload = {"error": f"Unknown graph tool: {name}"}
    finally:
        conn.close()
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_watch(arguments: dict, config: CodeSearchConfig) -> list[TextContent]:
    from nexus_code_search.watch import start_watcher_for_graph

    root = _resolve_root(arguments)
    debounce_ms = int(arguments.get("debounce_ms", 2000))
    watcher = start_watcher_for_graph(root, config, debounce_ms=debounce_ms)
    payload = {
        "root": str(root),
        "watcher_id": id(watcher),
        "debounce_ms": debounce_ms,
        "status": "watching",
    }
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_affected_tests(
    arguments: dict, config: CodeSearchConfig
) -> list[TextContent]:
    root = _resolve_root(arguments)
    changed = arguments.get("changed_files", [])
    if not isinstance(changed, list):
        raise ValueError("`changed_files` must be a list of file paths")
    depth = int(arguments.get("depth", 5))
    test_glob = arguments.get("test_glob")
    index_dir = index_dir_for(root, config)
    conn = open_database(index_dir)
    try:
        results = affected_tests(
            conn,
            repo_root=root,
            changed_files=changed,
            depth=depth,
            test_glob=test_glob,
        )
    finally:
        conn.close()
    payload = {
        "root": str(root),
        "changed_files": changed,
        "depth": depth,
        "test_glob": test_glob,
        "affected_tests": results,
    }
    return [TextContent(type="text", text=json.dumps(payload))]


def _handle_safety_check(
    name: str, arguments: dict, config: CodeSearchConfig
) -> list[TextContent]:
    operations = {
        "code_edit_safety": "edit",
        "code_delete_safety": "delete",
        "code_rename_safety": "rename",
    }
    operation = operations.get(name)
    if operation is None:
        raise ValueError(f"unknown safety tool: {name}")
    root = _resolve_root(arguments)
    symbol = arguments.get("symbol", "")
    if not symbol:
        raise ValueError("`symbol` argument is required")
    db_path = index_dir_for(root, config) / "codegraph.db"
    payload = evaluate_safety(db_path, symbol, operation)
    return [TextContent(type="text", text=json.dumps(payload))]


def _node_to_payload(node) -> dict:
    return {
        "id": node.id,
        "name": node.name,
        "kind": node.kind.value,
        "qualified_name": node.qualified_name,
        "file_path": node.file_path,
        "start_line": node.start_line,
        "end_line": node.end_line,
        "signature": node.signature,
        "docstring": node.docstring,
    }
