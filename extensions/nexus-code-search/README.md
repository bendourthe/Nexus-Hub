# nexus-code-search

> Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage.

Nexus-Hub local-only code search MCP server. Walks a repository, chunks source files, builds a content-hash manifest for incremental re-indexing, and serves keyword, AST-graph search, and edit-safety preflights via 20 MCP tools.

**Policy compliance**: zero outbound calls, zero API keys, zero model downloads. Governed by the [MCP Registry Policy](../../AGENTS.md) in the repo root; classified `already-local` in the [Reverse-Engineering Matrix](../../docs/policy/mcp-reverse-engineering-matrix.md).

## Status

- **v1.0 ships keyword-only search** via an inverted index + `rapidfuzz` fuzzy scoring.
- **v2.0 (current) adds a tree-sitter AST graph** for Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP, C, C++, Swift, and Kotlin: SQLite + FTS5 storage, NodeKind / EdgeKind taxonomy, call-graph traversal (callers / callees / impact radius / path finding), a Markdown context provider, optional offline hybrid retrieval, and a debounced filesystem watcher built on watchdog. Both surfaces are available simultaneously; callers pick the right tool for their query.

## Install

From the Nexus-Hub repo root:

```bash
pip install -e "extensions/nexus-code-search[dev]"
```

The installer ships with the repo. Alternatively install via the Nexus-Hub installer script (`scripts/installer.sh` or `scripts/installer.ps1`) which wires up `nexus-code-search` alongside `nexus-skill-server`.

## MCP tools

### Tool profiles

MCP tool definitions are sent to the model and consume context before any tool runs, so exposing only the surface a model needs reduces the cost of every request. Set `NEXUS_CODE_SEARCH_TOOL_PROFILE` to `minimal`, `standard`, or `full`; the default is `full`, preserving the complete pre-profile surface. Invalid values fail open to `full` because profiles control token cost, not authorization.

| Profile | Tools | Offline token estimate | Recommended model tier | Included surface |
|---|---:|---:|---|---|
| `minimal` | 7 | 1,860 | `fast` | Keyword and graph indexing, search, status, cleanup, and direct symbol retrieval |
| `standard` | 16 | 4,480 | `standard` / `strong` | Minimal plus callers, callees, impact, context, exploration, affected tests, and three mutation preflights |
| `full` | 20 | 5,620 | `frontier` or workflows needing every capability | Standard plus context-map generation and health, knowledge-map generation, and file watching |

Counts are generated from the compact JSON serialization of each MCP definition with the extension's deterministic stdlib estimator, so the baseline stays comparable without a tokenizer package or network access. A provider tokenizer may report a different absolute number while preserving the relative savings: `minimal` is about 67% smaller and `standard` about 20% smaller than `full`. These counts include the response-format controls advertised by every tool.

The model-tier names come from [`model-routing`](../../catalog/skills/ai-development/model-routing/SKILL.md); use [`prompt-token-optimization`](../../catalog/skills/orchestration/prompt-token-optimization/SKILL.md) for the broader context-cost workflow.

### Response encoding

Every tool accepts `response_format=json|compact|auto` and `compact_min_savings_pct` from 0 through 100. The default is `json`, which preserves the existing response bytes. `compact` forces the Nexus-Hub-owned, standard-library wire format, while `auto` uses it only when the actual UTF-8 byte reduction meets the threshold, 15% by default. Any producer-side codec error returns valid JSON. Consumers identify compact output by the exact `NEXUS-CW/1` first line and can use the reference decoder in `nexus_code_search.response_codec` or implement the [wire-format specification](docs/wire-format.md).

This codec is producer-side and schema-aware: it removes repeated keys from structured MCP response tables. [`nexus-context-compressor`](../nexus-context-compressor/README.md) is consumer-side and content-routed: it handles arbitrary tool output and uses reversible CCR markers when content is dropped. When producer encoding runs first, the consumer compressor recognizes `NEXUS-CW/1` and returns the payload unchanged, so the two paths compose without double compression.

The following measurements come from the Phase 3 test fixture, which supplies one representative response shape for every live tool and asserts these README rows against `measure_savings()`. Sizes are UTF-8 bytes. A negative percentage means forced compact mode is larger; automatic mode correctly retains JSON.

| Tool | JSON bytes | Compact bytes | Savings | Auto at 15% |
|---|---:|---:|---:|---|
| `index_codebase` | 156 | 156 | 0.0% | `json` |
| `search_code` | 1,848 | 1,195 | 35.3% | `compact` |
| `clear_index` | 34 | 44 | -29.4% | `json` |
| `get_indexing_status` | 136 | 138 | -1.5% | `json` |
| `index_graph` | 116 | 118 | -1.7% | `json` |
| `generate_context_map` | 797 | 576 | 27.7% | `compact` |
| `map_health` | 990 | 840 | 15.2% | `compact` |
| `generate_knowledge_map` | 752 | 585 | 22.2% | `compact` |
| `code_search` | 3,582 | 2,506 | 30.0% | `compact` |
| `code_callers` | 6,761 | 6,210 | 8.1% | `json` |
| `code_callees` | 6,761 | 6,210 | 8.1% | `json` |
| `code_impact` | 9,009 | 8,421 | 6.5% | `json` |
| `code_node` | 3,583 | 2,507 | 30.0% | `compact` |
| `code_context` | 17,985 | 16,767 | 6.8% | `json` |
| `code_explore` | 19,749 | 18,431 | 6.7% | `json` |
| `code_affected_tests` | 428 | 421 | 1.6% | `json` |
| `code_edit_safety` | 16,627 | 15,044 | 9.5% | `json` |
| `code_delete_safety` | 16,629 | 15,046 | 9.5% | `json` |
| `code_rename_safety` | 16,629 | 15,046 | 9.5% | `json` |
| `watch_for_changes` | 81 | 87 | -7.4% | `json` |

### v1 keyword surface

| Tool | Purpose |
|---|---|
| `index_codebase(root, force=False)` | Walk `root`, chunk files, persist a content-hash JSON index under `<root>/.nexus/code-index/`. Respects `.gitignore` and an optional `.nexusignore`. Content-hash incremental: unchanged files are skipped. |
| `search_code(query, mode="keyword", limit=10)` | Return up to `limit` matching chunks. Keyword mode uses token overlap + `rapidfuzz`; opt-in hybrid mode combines that rank with a pre-placed local encoder and fails soft to keyword. |
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
| `code_edit_safety(symbol)` | Return one ranked, read-only verdict for modifying a symbol, what behavior or contract must be preserved, and the concrete indexed callers/importers/references behind it. |
| `code_delete_safety(symbol)` | Return one ranked, read-only verdict for removing a symbol, who would break, and the concrete indexed evidence that must be migrated first. |
| `code_rename_safety(symbol)` | Return one ranked, read-only verdict for renaming a symbol and the indexed callers/importers/references that must move atomically. |
| `generate_context_map(root, force=False)` | Compile a committed `<root>/.nexus/CONTEXT-MAP.md` (plus a `<root>/.nexus/context/` article set) from the graph, so an AI reads the codebase map once at session start instead of re-exploring files. Includes framework-aware Routes (method / path / params / behavior tags), an Environment audit (required vs default), Middleware, ORM Data Models (fields / keys / relations), UI Components (props), background Events, and a Most-Imported Files ranking. Deterministic and local-only; writes only under `<root>/.nexus/`. Unchanged graph is a no-op unless `force=True`. Run `index_graph` first. Companion CLI: `nexus-hub map` (see "Context map" below). |
| `map_health(root)` | Lint the compiled map: orphan articles, missing backlinks, and staleness (source changed since the map was generated). Deterministic and local-only; returns a health report. Companion CLI: `nexus-hub map --lint`. |
| `generate_knowledge_map(root, notes_path=None)` | Compile a committed `<root>/.nexus/KNOWLEDGE.md` from the Markdown notes under `notes_path` (default: root): key decisions, open questions, and a categorized note index (decision / meeting / retro / spec / research). Deterministic, local-only, graph-independent. Companion CLI: `nexus-hub map --knowledge`. |

The three safety tools share the ordered verdict and evidence contract in [Edit-Safety Verdict Contract](docs/edit-safety-verdicts.md). `insufficient_data` is never collapsed into a safe result, `no_known_callers` is only a possible dead-code signal, and cross-repository visibility is explicitly reported as unavailable because one local graph cannot prove it.

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

The local [context-provider contract](docs/context-providers.md) extends that resolver seam to non-code files. The intentionally small shipped set contains one Markdown provider, which adds heading nodes and hierarchy edges without parsing links or opening connections.

## Optional offline dense retrieval

Dense retrieval is an opt-in extra and is off by default. Keyword search remains the fallback on every missing or failing component.

```bash
cd extensions/nexus-code-search
pip install -e '.[dense]'
```

Place `model.onnx` and `tokenizer.json` in `~/.nexus-hub/cache/models/code-search-encoder/`, or set `NEXUS_CODE_SEARCH_MODEL_DIR` to another local directory. Obtain and place those weights yourself, then set `NEXUS_CODE_SEARCH_DENSE=1` and call `search_code` with `mode="hybrid"`.

The extension only reads those exact pre-placed files. It has no download command, no implicit first-use fetch, and no URL-backed fallback; it never downloads weights. If the extra, files, or encoder are unavailable, the response uses keyword ranking and returns a precise local installation hint instead of failing.

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

# Compile a knowledge primer from a folder of Markdown notes (decisions, open questions).
nexus-hub map --knowledge docs/notes
```

The lint is also the `map_health` MCP tool. The knowledge extractor (also the `generate_knowledge_map` MCP tool) is graph-independent - it classifies `.md` notes (decision / meeting / retro / spec / research) by filename and heading heuristics and emits `.nexus/KNOWLEDGE.md` with key decisions, open questions, and a categorized index; narrative synthesis stays in the `solution-knowledge-base` skill. Its richer, semantic companion (prose quality, cross-doc consistency) stays in the LLM-native `documentation-consistency` skill; the lint is the mechanical, CI-runnable half only, and ships no new skill.

## Token-savings benchmark

`python -m nexus_code_search.contextmap.benchmark` measures how many tokens the compiled map saves versus reading the codebase manually. The manual-exploration cost is modeled as the sum of per-file tokens times a revisit multiplier (an AI re-reads files while exploring) plus a per-entity discovery overhead for each route / model / component / env var; the map cost is the map + article tokens. The reduction ratio is `1 - map_cost / manual_cost`. The estimation constants (`REVISIT_MULTIPLIER`, `TOKENS_PER_ROUTE`, ...) are the tool's own heuristic, documented in `benchmark.py`.

```bash
# Benchmark the committed sample corpus and gate against the baseline.
python -m nexus_code_search.contextmap.benchmark --check

# Benchmark any real repository (prints the ratio; no gate).
python -m nexus_code_search.contextmap.benchmark --repo /path/to/repo --json
```

A committed `benchmark_baseline.json` records a per-repo floor (a margin below the measured ratio) so a regression - the map silently losing its savings - fails the gate; re-baseline intentionally with `--update-baseline`. On the sample corpus the map saves ~44-55% of exploration tokens; on Nexus-Hub itself a ~22k-token map replaces ~1.9M tokens of manual exploration (~99% reduction, 443 files). A map is not worth its fixed overhead on a trivially small repo - the savings scale with codebase size.

## Keeping the map fresh (CI recipe)

Regenerate and commit `.nexus/CONTEXT-MAP.md` on every push so the map never drifts from the code. The recipe is platform-agnostic; GitHub Actions is shown. Pin the action refs to commit SHAs in production.

```yaml
name: context-map
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  context-map:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install nexus-code-search
      - name: Build the graph and regenerate the context map
        run: |
          python - <<'PY'
          from pathlib import Path
          from nexus_code_search.config import CodeSearchConfig, index_dir_for
          from nexus_code_search.contextmap import generate_context_map
          from nexus_code_search.extraction import ExtractionOrchestrator
          root = Path(".").resolve()
          cfg = CodeSearchConfig(hub_root=None)
          index_dir = index_dir_for(root, cfg)
          with ExtractionOrchestrator(root, cfg, index_dir) as orch:
              orch.run()
          generate_context_map(root, index_dir, force=True)
          PY
      - name: Commit the map if it changed
        run: |
          git add .nexus/CONTEXT-MAP.md .nexus/context
          git diff --cached --quiet || {
            git config user.name "github-actions"
            git config user.email "github-actions@users.noreply.github.com"
            git commit -m "chore: refresh context map"
            git push
          }
```

Because the map is deterministic and content-hash incremental, an unchanged graph produces an identical map, so the commit step is a no-op on pushes that do not affect the graph. Add a `map --lint` step (exit 1 on orphan / backlink / staleness issues) to fail CI when a committed map goes stale.

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
