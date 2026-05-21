# nexus-code-search

> Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage.

Nexus-Hub local-only code search MCP server. Walks a repository, chunks source files, builds a content-hash manifest for incremental re-indexing, and serves keyword search over the chunks via four MCP tools.

**Policy compliance**: zero outbound calls, zero API keys, zero model downloads. Governed by the [MCP Registry Policy](../../AGENTS.md) in the repo root; classified `already-local` in the [Reverse-Engineering Matrix](../../docs/policy/mcp-reverse-engineering-matrix.md).

## Status

- **v1.0.0 ships keyword-only search** via an inverted index + `rapidfuzz` fuzzy scoring.
- **v1.1.0 will add dense + hybrid retrieval** with local ONNX embeddings (`fastembed`) and a `sqlite-vec` vector store. The `search_code(mode="hybrid")` path is reserved and currently raises `NotImplementedError` with a pointer note.

## Install

From the Nexus-Hub repo root:

```bash
pip install -e "extensions/nexus-code-search[dev]"
```

The installer ships with the repo. Alternatively install via the Nexus-Hub installer script (`scripts/installer.sh` or `scripts/installer.ps1`) which wires up `nexus-code-search` alongside `nexus-skill-server`.

## MCP tools

| Tool | Purpose |
|---|---|
| `index_codebase(root, force=False)` | Walk `root`, chunk files, persist an index under `<root>/.nexus/code-index/`. Respects `.gitignore` and an optional `.nexusignore`. Content-hash incremental: unchanged files are skipped. |
| `search_code(query, mode="keyword", limit=10)` | Return up to `limit` matching chunks. `mode` must be `"keyword"` in v1.0.0. |
| `clear_index(root)` | Remove `<root>/.nexus/code-index/`. |
| `get_indexing_status(root)` | Return index state (`idle` / `running` / `error`) plus counts and timestamps. |

## Data flow

- **Local filesystem only**. Index data is stored under `<root>/.nexus/code-index/` as a pickled index file plus a JSON manifest. Nothing leaves the machine.
- **No network sockets** are opened during indexing or search.

## Default exclusions

The walker skips:

- Anything matched by `.gitignore` or `.nexusignore` (at repo root).
- Directory names: `node_modules`, `.venv`, `venv`, `dist`, `build`, `__pycache__`, `.git`, `.nexus`.
- File patterns: `*.lock`, `*.min.js`, `*.min.css`.
- Files larger than 1 MB.
- Files that fail UTF-8 decode (binary).

Add project-specific exclusions to `.nexusignore` at the repo root. Syntax matches `.gitignore`.

## Chunking

Recursive character splitter with language-aware separator preference (function / class / brace / blank-line / newline / space boundaries). 600-char target window, 80-char overlap. No tree-sitter dependency in v1.0.0 to keep the Windows install path wheels-only.

## 5-question audit

Per the MCP Registry Policy:

1. **Who runs the process?** Python subprocess on the user's machine; spawned by the user's agent.
2. **Outbound calls?** None.
3. **API keys?** None.
4. **Data transmitted to third parties?** None. Chunk contents live on disk and are returned to the agent via stdio.
5. **Vendor relationship required?** None.

## License

MIT. Copyright (c) Benjamin Dourthe / Nexus-Hub.
