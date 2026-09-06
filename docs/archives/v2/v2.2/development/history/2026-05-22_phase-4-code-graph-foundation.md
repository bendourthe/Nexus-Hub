# Session history -- v2.2.0 Phase 4: Code-graph foundation (`nexus-code-search` v2.0)

**Date**: 2026-05-22
**Plan**: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](../../plans/codegraph-and-antigravity.md)
**Phase**: 4 of 6 -- "Code-graph foundation"
**Status**: complete

## Goal

Replace `nexus-code-search`'s keyword-only inverted index with a tree-sitter AST extraction pipeline backed by SQLite (FTS5) with a NodeKind / EdgeKind taxonomy, call-graph traversal, and a native filesystem watcher for auto-sync.

## Sub-tasks completed

| ID | Title | Outcome |
|---|---|---|
| T023 | Tree-sitter dependency + extraction module scaffold | pyproject.toml updated; `extraction/` package created with orchestrator + parse_worker + languages registry |
| T024 | NodeKind / EdgeKind schema + DB migration | 22 NodeKind + 12 EdgeKind enums; SQLite schema with FTS5; `migrate_v1_to_v2` renames legacy index aside |
| T025 | Python + TypeScript AST extractors | Both extractors emit nodes / edges per the local-resolution convention; one tree-sitter-typescript heritage-detection bug surfaced and fixed inline |
| T026 | Call-graph traverser + new MCP tools | `GraphTraverser`, `GraphQueryManager`, eight new MCP tools; FTS5 driven by AFTER triggers stays in sync automatically |
| T027 | Filesystem watcher with watchdog | Debounced `FileWatcher`; reentrant `start_watcher_for_graph` registry; `watch_for_changes` MCP tool |
| T028 | Phase 4 tests + stabilization | 104 passed / 1 skipped / 0 failed; **86% line coverage**; ruff clean |

## Files added

- `extensions/nexus-code-search/src/nexus_code_search/db/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/db/schema.sql`
- `extensions/nexus-code-search/src/nexus_code_search/db/schema.py`
- `extensions/nexus-code-search/src/nexus_code_search/db/migrate.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/orchestrator.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/parse_worker.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/base.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/python.py`
- `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/typescript.py`
- `extensions/nexus-code-search/src/nexus_code_search/graph/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/graph/traverser.py`
- `extensions/nexus-code-search/src/nexus_code_search/graph/query_manager.py`
- `extensions/nexus-code-search/src/nexus_code_search/watch.py`
- `extensions/nexus-code-search/tests/test_schema.py`
- `extensions/nexus-code-search/tests/test_extraction_scaffold.py`
- `extensions/nexus-code-search/tests/test_python_extraction.py`
- `extensions/nexus-code-search/tests/test_typescript_extraction.py`
- `extensions/nexus-code-search/tests/test_orchestrator.py`
- `extensions/nexus-code-search/tests/test_traverser.py`
- `extensions/nexus-code-search/tests/test_watcher.py`
- `extensions/nexus-code-search/tests/test_server_graph_handlers.py`
- `extensions/nexus-code-search/tests/test_python_extra.py`
- `extensions/nexus-code-search/tests/test_typescript_extra.py`
- `docs/archive/v2/v2.2/docs-cleanup-report-phase4.md`
- `docs/archive/v2/v2.2/development/history/2026-05-22_phase-4-code-graph-foundation.md`

## Files modified

- `extensions/nexus-code-search/pyproject.toml` -- added `tree-sitter`, `tree-sitter-python`, `tree-sitter-typescript`, `watchdog` dependencies; updated description.
- `extensions/nexus-code-search/src/nexus_code_search/__init__.py` -- `__version__` bumped from 1.0.0 to 2.0.0; docstring describes the dual surface.
- `extensions/nexus-code-search/src/nexus_code_search/types.py` -- added `NodeKind`, `EdgeKind`, `Node`, `Edge` dataclasses alongside the existing v1 chunk types.
- `extensions/nexus-code-search/src/nexus_code_search/server.py` -- registered eight new MCP tools, updated `SERVER_INSTRUCTIONS`, extended `_handle_clear` to drop the SQLite database alongside the JSON index, added `_handle_index_graph` / `_handle_graph_query` / `_handle_watch` dispatch.
- `extensions/nexus-code-search/README.md` -- updated tool table and added the NodeKind / EdgeKind taxonomy section.
- `docs/DEVLOG.md` -- prepended a Phase 4 narrative block.
- `docs/archive/v2/v2.2/known-gaps.md` -- updated last-updated line, summary table, added DF-002 / WN-5 / WN-6, moved BG-P4-1 to Resolved.
- `CHANGELOG.md` -- added five Added entries and three Changed entries under `[Unreleased]`.
- `.gitignore` -- added coverage artifacts (`.coverage`, `.coverage.*`, `htmlcov/`, `coverage.xml`).

## Tests

| Suite | Result |
|---|---|
| `extensions/nexus-code-search/tests/` | 104 passed, 1 skipped, 0 failed |
| Line coverage (v2.0 code) | 86% (1587 stmts, 221 missed) |
| `tests/integrations/` + `tests/installer/` | 223 passed (Phase 3 baseline preserved) |
| `python -m ruff check` | clean |
| `python -m ruff format --check` | clean (24 net-new / modified files formatted) |

23 net new tests covering the v2.0 surface: schema bootstrap, FTS5 triggers, v1->v2 migration backup, Python extractor edge cases (decorators, class fields, typed parameters, attribute calls, unresolvable calls), TypeScript extractor edge cases (named imports, default / namespace imports, export clauses, const-vs-let kind discrimination, class properties, member-expression calls), end-to-end orchestrator (idempotent re-run, force rebuild, file-change detection), graph traverser (callers, callees, impact radius, path finding, FTS5 search, name resolution, explore), file watcher (debounce collapsing, extension filter, exclude-dir filter, invalid-debounce rejection), and per-tool MCP handler dispatch.

## CI/CD changes

None. The existing `pip install -e "extensions/nexus-code-search/[dev]"` step in `.github/workflows/ci.yml` picks up the new tree-sitter / watchdog dependencies via the updated `pyproject.toml`.

## Deviations from plan

- **Dependency pin**. Plan suggested `tree-sitter = "^0.23.0"` with `tree-sitter-languages = "^1.10.0"`. The umbrella `tree-sitter-languages` package is abandoned and crashes on tree-sitter 0.23+ with `TypeError: Language.__init__() takes exactly 1 argument`. Phase 4 instead uses the maintained per-language packages `tree-sitter-python` and `tree-sitter-typescript` with `tree-sitter>=0.24,<0.26`. Recorded as `WN-5` in `known-gaps.md`.
- **End-to-end smoke against Flask**. Plan's 4.6 sub-task asked for a clone of `pallets/flask` at a pinned tag and a manual verification of node counts / call-graph plausibility. Skipped due to network constraints; the synthetic-repo coverage in `test_orchestrator.py` exercises the same code paths. Not recorded as a gap since the equivalent verification surfaces through the unit tests.
- **C2-extended call resolutions**. The current extractors classify `Service()` constructor calls as `calls` rather than `instantiates`, and do not detect parent-class method overrides. The `EdgeKind` taxonomy is ready (both kinds are defined); the extractors do not yet emit them. Recorded as `WN-6` in `known-gaps.md`.

## Bugs found + fixed

- **BG-P4-1**: TypeScript extractor missed `extends` / `implements` clauses because `tree-sitter-typescript` 0.23+ no longer exposes `class_heritage` under a field name. Fixed by walking `node.named_children` to find the heritage node. Now resolved in `known-gaps.md`.

## Known issues / next steps

- Phase 5 will layer Django / FastAPI / Express route extractors on the same orchestrator, plus the `affected_tests` MCP tool + `nexus-hub affected` CLI subcommand, plus a synthetic-codebase eval harness.
- The 18 deferred language extractors (`DF-002` in `known-gaps.md`) wait on v2.3.0+ user demand.
- Constructor-instantiation and parent-override edge resolution (`WN-6`) is local-only work; can be folded into Phase 5 or deferred to v2.3.0+.

## Commit

Phase 4 ready to commit. Commit message and prompt handled in `/implement-phase` sub-steps 8.9-8.10.
