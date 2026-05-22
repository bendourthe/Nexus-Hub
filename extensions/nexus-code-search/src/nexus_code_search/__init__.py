"""Nexus-Hub local-only code-search MCP server.

v2.0 layers a tree-sitter AST graph (Python + TypeScript, SQLite + FTS5,
call-graph traversal, native file watcher) on top of the v1.0 keyword
chunk index. Both surfaces remain available - callers pick the right one
for their query.

Policy: zero outbound calls, zero API keys, zero model downloads.
Governed by the MCP Registry Policy in AGENTS.md.
"""

from __future__ import annotations

__version__ = "2.0.0"
