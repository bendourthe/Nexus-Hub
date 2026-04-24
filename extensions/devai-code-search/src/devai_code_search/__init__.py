"""DevAI-Hub local-only code-search MCP server.

v1.0.0 ships keyword-only search. Dense / hybrid retrieval (local ONNX
embeddings + sqlite-vec) is planned for v1.1.0.

Policy: zero outbound calls, zero API keys, zero model downloads.
Governed by the MCP Registry Policy in AGENTS.md.
"""
from __future__ import annotations

__version__ = "1.0.0"
