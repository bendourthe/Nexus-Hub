# nexus-code-search

> Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage.

Nexus-Hub local-only code search MCP server. Walks a repository, chunks source files, builds a content-hash manifest for incremental re-indexing, and serves keyword + AST-graph search via twelve MCP tools.

**Policy compliance**: zero outbound calls, zero API keys, zero model downloads. Governed by the [MCP Registry Policy](../../AGENTS.md) in the repo root; classified `already-local` in the [Reverse-Engineering Matrix](../../docs/policy/mcp-reverse-engineering-matrix.md).

## Status

- **v1.0 ships keyword-only search** via an inverted index + `rapidfuzz` fuzzy scoring.
- **v2.0 (current) adds a tree-sitter AST graph** for Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP, C, C++, Swift, and Kotlin: SQLite + FTS5 storage, NodeKind / EdgeKind taxonomy, call-graph traversal (callers / callees / impact radius / path finding), and a debounced filesystem watcher built on watchdog. Both surfaces are available simultaneously; callers pick the right tool for their query. Future versions may add dense / hybrid retrieval with local ONNX embeddings; nothing is reserved today.

## Install

From the Nexus-Hub repo root:

```bash
pip install -e "extensions/nexus-code-search[dev]"
```

The installer ships with the repo. Alternatively install via the Nexus-Hub installer script (`scripts/installer.sh` or `scripts/installer.ps1`) which wires up `nexus-code-search` alongside `nexus-skill-server`.

## MCP tools

### v1 keyword surface

| Tool | Purpose |
|---|---|
| `index_codebase(root, force=False)` | Walk `root`, chunk files, persist a content-hash JSON index under `<root>/.nexus/code-index/`. Respects `.gitignore` and an optional `.nexusignore`. Content-hash incremental: unchanged files are skipped. |
| `search_code(query, mode="keyword", limit=10)` | Return up to `limit` matching chunks ranked by token overlap + `rapidfuzz` fuzzy ratio. |
| `clear_index(root)` | Remove both the JSON index and the SQLite graph database for `<root>`. |
| `get_indexing_status(root)` | Return index state (`idle` / `running` / `error`) plus counts and timestamps. |

### v2 AST graph surface (Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP, C, C++, Swift, Kotlin)

| Tool | Purpose |
|---|---|
| `index_graph(root, force=False)` | Build / refresh the tree-sitter AST graph at `<root>/.nexus/code-index/codegraph.db` (nodes / edges / files / FTS5 over names + docstrings). Content-hash incremental. |
| `code_search(query, limit=20, all_fields=False)` | FTS5 full-text search over node names. Scoped to the symbol-name column by default for precision; pass `all_fields=true` to also match qualified_names and docstrings (e.g. for path-segment or docstring search). Returns ranked node records. |
| `code_callers(symbol)` | Every node with a `calls` edge into `symbol` (qualified_name or plain name). |
| `code_callees(symbol)` | Every node `symbol` has a `calls` edge to. |
| `code_impact(symbol, depth=2)` | BFS over impact-bearing edges (`calls` + `references` + `extends` + `implements` + `overrides`) up to `depth` hops in both directions. |
| `code_node(symbol)` | Resolve a symbol by qualified_name first, then by plain name. Returns matching node records. |
| `code_context(symbol)` | One-shot context window: node + callers + callees + module-siblings. |
| `code_explore(symbol, depth=2)` | Combined search + traversal payload (matches + callers + callees + impact). |
| `watch_for_changes(root, debounce_ms=2000)` | Start a debounced filesystem watcher that re-indexes the graph as files change. Returns immediately; the watcher runs in a background thread. |
| `code_affected_tests(changed_files, depth=5, test_glob=None)` | Reverse-import BFS: given a list of changed files, return every test file in the index whose code transitively imports any of them. Conservative -- false positives favored over false negatives. Companion CLI: `nexus-hub affected` (see "CLI dispatcher" below). |

## NodeKind / EdgeKind taxonomy

The v2 graph stores 22 node kinds (`file`, `module`, `class`, `struct`, `interface`, `trait`, `protocol`, `function`, `method`, `property`, `field`, `variable`, `constant`, `enum`, `enum_member`, `type_alias`, `namespace`, `parameter`, `import`, `export`, `route`, `component`) and 12 edge kinds (`contains`, `calls`, `imports`, `exports`, `extends`, `implements`, `references`, `type_of`, `returns`, `instantiates`, `overrides`, `decorates`). Each language extractor emits a subset suited to its grammar:

- **Python / TypeScript** emit `contains` / `calls` / `imports` / `extends` (+ TS `implements` / `exports`) plus `instantiates` (constructor / `new` calls) and `overrides` (a method shadowing an in-file parent's method).
- **Go** emits structs, interfaces, receiver-keyed methods, fields, and `instantiates` from composite literals (no inheritance edges -- Go interface satisfaction is structural).
- **Rust** emits structs, enums, traits, impl-block methods, `implements` from `impl Trait for Type`, and `instantiates` from struct literals.
- **Java / C#** emit the full OOP edge set: `extends`, `implements`, `overrides`, and `instantiates` from `new` expressions. C# resolves its single syntactic `base_list` into `extends` vs `implements` by the resolved target's kind.
- **Ruby** emits modules (as namespaces), classes, methods vs top-level functions, top-level constants, `require` imports, `extends` from `class C < Base`, and in-file `calls`.
- **PHP** emits namespaces, classes, interfaces, methods, functions, class constants, properties, `use` imports, `extends` / `implements`, and in-file `calls`.
- **C** emits functions, structs + fields, enums + members, typedefs, `#include` imports, and in-file `calls` (no inheritance -- C has no classes).
- **C++** emits namespaces, classes / structs, methods vs free functions, fields, enums, `#include` imports, `extends` from base-class clauses, and in-file `calls`.
- **Swift** emits protocols, classes / structs / enums (the grammar's single `class_declaration` discriminated by keyword), methods vs top-level functions, initializers, properties, enum cases, `import` declarations, `extends` (class) / `implements` (protocol conformance) from inheritance clauses, and in-file `calls`.
- **Kotlin** emits interfaces, classes (and `object` singletons), enum classes + entries, methods vs top-level functions, properties vs top-level constants, package namespaces, `import` declarations, `extends` / `implements` from delegation specifiers, and in-file `calls`.

Three framework resolvers (Django for `urls.py` files, FastAPI / Flask for decorator-driven handlers, Express for `app.<method>` / `router.<method>` calls) run after AST extraction and emit `route` nodes plus `decorates` / `references` edges so URL handlers and middleware chains are searchable through the same `code_search` / `code_context` tools.

## CLI dispatcher

The `nexus-hub affected` CLI dispatcher (installed at `~/.nexus-hub/scripts/nexus_hub_affected.py` by the Nexus-Hub installer) wraps `code_affected_tests` for shell use:

```bash
# Pipe `git diff` into the test-impact query.
git diff --name-only HEAD~1 | nexus-hub affected --root . -

# Or pass files as positional args; emit JSON for downstream tooling.
nexus-hub affected --root /repo --depth 3 --json src/foo.py src/bar.py
```

The dispatcher exits with code 2 if no graph index is found at `<root>/.nexus/code-index/codegraph.db` (run `index_graph` via the MCP server first).

## Eval harness

`make eval` (or `python -m nexus_code_search.eval` from this directory) runs the synthetic-codebase harness under `src/nexus_code_search/eval/`. The harness ships eight fixture codebases (minimal / python_app / fastapi_app / ts_express / go_app / rust_app / java_app / csharp_app), scores recall + precision against the answer keys, and writes a Markdown report. The current baseline is captured at `docs/archive/v2/v2.3/eval-baseline.md` (100% aggregate recall, 96.2% aggregate precision; every fixture clears the >=80% per-fixture recall gate).

## Data flow

- **Local filesystem only**. v1 index data lives at `<root>/.nexus/code-index/{chunks.json, manifest.json}`. v2 graph data lives at `<root>/.nexus/code-index/codegraph.db` (SQLite with FTS5). Both indices coexist independently; running `clear_index` removes both.
- **v1 -> v2 migration**: detecting a v1 index renames it aside to `<dir>.v1-backup` and surfaces a clear "please re-index" message. No data is destroyed.
- **No network sockets** are opened during indexing, searching, or watching.

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
