"""Compiled context-map generator for nexus-code-search.

Turns the already-built tree-sitter AST graph into a committed, deterministic
`.nexus/CONTEXT-MAP.md` plus a `.nexus/context/` article set: an AI reads the
map once at session start instead of re-exploring files every session. The
generator is zero-LLM, local-only, and writes only under `<root>/.nexus/`.

Public surface:
    generate_context_map    Compile the map + articles from the graph.
    ContextMapResult        Structured outcome (paths + token summary).
    ContextMapModel         The rendered-independent content model.
"""

from __future__ import annotations

from nexus_code_search.contextmap.generator import (
    ContextMapResult,
    generate_context_map,
)
from nexus_code_search.contextmap.model import ContextMapModel

__all__ = [
    "ContextMapModel",
    "ContextMapResult",
    "generate_context_map",
]
