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
| `generate_context_map(root, force=False)` | Compile a committed `<root>/.nexus/CONTEXT-MAP.md` (plus a `<root>/.nexus/context/` article set) from the graph, so an AI reads the codebase map once at session start instead of re-exploring files. Includes framework-aware Routes (method / path / params / behavior tags), an Environment audit (required vs default), Middleware, ORM Data Models (fields / keys / relations), UI Components (props), background Events, and a Most-Imported Files ranking. Deterministic and local-only; writes only under `<root>/.nexus/`. Unchanged graph is a no-op unless `force=True`. Run `index_graph` first. Companion CLI: `nexus-hub map` (see "Context map" below). |
| `map_health(root)` | Lint the compiled map: orphan articles, missing backlinks, and staleness (source changed since the map was generated). Deterministic and local-only; returns a health report. Companion CLI: `nexus-hub map --lint`. |

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

## Context map

`generate_context_map` (MCP tool) and `nexus-hub map` (CLI) compile the AST graph into a committed, deterministic context map an AI can read once at session start, instead of paying the file-exploration cost every session. Build the graph first (`index_graph`), then:

```bash
# Compile <root>/.nexus/CONTEXT-MAP.md + <root>/.nexus/context/ from the graph.
nexus-hub map

# Target another repo, force a rebuild, or emit JSON for tooling.
nexus-hub map /repo --force --json

# Print a change-scoped view (affected routes / models / symbols / tests) for
# what changed since a git ref, instead of the full map (writes nothing).
nexus-hub map --since HEAD~1 --json
```

Outputs, written ONLY under `<root>/.nexus/`:

- `CONTEXT-MAP.md` - overview (languages, detected frameworks, file / symbol / module counts), a module-structure table, framework-aware Routes / Environment / Middleware / Data Models / Components / Events sections, a Most-Imported Files ranking (file-level inbound import count, distinct from symbol-level `code_impact`), and an index of the per-module articles.
- `context/index.md` plus `context/<module>.md` - one article per top-level module (files, symbol counts, and key symbols).
- `context/routes.md` - the full route list (method, path, params, behavior tags, handler) when any routes are detected.
- `context/database.md` - per-model field / key / relation detail when any ORM models are detected.

Framework extraction reads the graph the resolvers already build (routes cover FastAPI, Flask, Django, Express); schema covers SQLAlchemy, Django ORM, and Prisma (with relation resolution); components cover React; events cover Celery, BullMQ, Kafka, and EventEmitter. The env audit reads `.env.example`-style files by NAME only (never the real `.env`, never a value). Detection is gated by an extraction-accuracy harness (per-section recall + a hard zero-false-positive check, plus a relation-resolution assertion) - see the accuracy fixtures under `tests/fixtures/contextmap/`.

Every file carries a metadata header with an accurate token count and a source fingerprint. Properties, all locked by the test suite:

- **Neutral path**: writes are confined to `<root>/.nexus/`; the map never touches `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or any other AI-config file (those are owned by the Nexus-Hub installer).
- **Deterministic**: output is a pure function of the graph (no wall-clock timestamp), so the MCP tool and the CLI produce byte-identical output for the same input.
- **Content-hash incremental**: the source fingerprint is embedded in the map, so regenerating on an unchanged graph is a no-op unless `--force` / `force=True`.

The token-count header prefers `tiktoken` (cl100k_base) when it is importable and loads offline, and otherwise falls back to a stdlib heuristic - the extension adds no dependency on tiktoken.

`.gitignore` guidance for consumer repos: commit `.nexus/CONTEXT-MAP.md` and `.nexus/context/`, but ignore the `.nexus/code-index/` graph database.

The CLI exits with code 2 if no graph index is found at `<root>/.nexus/code-index/codegraph.db` (run `index_graph` first), and code 1 for a missing root.

Two more `nexus-hub map` modes:

```bash
# Change-scoped view since a git ref (affected routes / models / symbols / tests).
nexus-hub map --since HEAD~1 --json

# Lint the compiled map: orphan articles, missing backlinks, staleness (exit 1 if unhealthy).
nexus-hub map --lint
```

The lint is also the `map_health` MCP tool. Its richer, semantic companion (prose quality, cross-doc consistency) stays in the LLM-native `documentation-consistency` skill; the lint is the mechanical, CI-runnable half only, and ships no new skill.

## Token-savings benchmark

`python -m nexus_code_search.contextmap.benchmark` measures how many tokens the compiled map saves versus reading the codebase manually. The manual-exploration cost is modeled as the sum of per-file tokens times a revisit multiplier (an AI re-reads files while exploring) plus a per-entity discovery overhead for each route / model / component / env var; the map cost is the map + article tokens. The reduction ratio is `1 - map_cost / manual_cost`. The estimation constants (`REVISIT_MULTIPLIER`, `TOKENS_PER_ROUTE`, ...) are the tool's own heuristic, documented in `benchmark.py`.

```bash
# Benchmark the committed sample corpus and gate against the baseline.
python -m nexus_code_search.contextmap.benchmark --check

# Benchmark any real repository (prints the ratio; no gate).
python -m nexus_code_search.contextmap.benchmark --repo /path/to/repo --json
```

A committed `benchmark_baseline.json` records a per-repo floor (a margin below the measured ratio) so a regression - the map silently losing its savings - fails the gate; re-baseline intentionally with `--update-baseline`. On the sample corpus the map saves ~44-55% of exploration tokens; on Nexus-Hub itself a ~22k-token map replaces ~1.9M tokens of manual exploration (~99% reduction, 443 files). A map is not worth its fixed overhead on a trivially small repo - the savings scale with codebase size.

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
