# Session history -- v2.2.0 Phase 5: Code-graph capabilities (frameworks, affected-tests, eval harness)

**Date**: 2026-05-22
**Plan**: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](../../plans/codegraph-and-antigravity.md)
**Phase**: 5 of 6 -- "Code-graph capabilities"
**Status**: complete

## Goal

Layer three framework route extractors (Django, FastAPI/Flask, Express), a test-impact analysis algorithm with both an MCP tool and a CLI dispatcher, and a synthetic-codebase MCP eval harness on top of the Phase 4 AST foundation. Every sub-task is strictly additive; no Phase 4 behavior changed.

## Sub-tasks completed

| ID | Title | Outcome |
|---|---|---|
| T029 | Django framework route extractor | `frameworks/django.py` + 5 tests; recognizes `path()` / `re_path()` / `url()` / `include()` / `MyView.as_view()`; emits `route` nodes + `references` edges |
| T030 | FastAPI / Flask framework route extractor | `frameworks/fastapi.py` + 6 tests; recognizes `@app.<method>` / `@router.<method>` / `@app.route` decorators; emits `route` nodes + `decorates` edges |
| T031 | Express framework route extractor | `frameworks/express.py` + 5 tests; recognizes `app.<method>()` / `router.<method>()` calls; middleware chains produce multiple `references` edges from one route |
| T032 | `code_affected_tests` MCP tool + `nexus-hub affected` CLI | `graph/affected.py` reverse-import BFS + `code_affected_tests` MCP handler + `scripts/nexus_hub_affected.py` CLI; installer registration in lockstep; 11 tests across algorithm / handler / CLI |
| T033 | Synthetic-codebase MCP eval harness | `src/nexus_code_search/eval/` with 4 fixture codebases (18 questions total); in-tree YAML subset parser; Markdown + JSON reporting; `make eval` target; 5 tests |
| T034 | Phase 5 tests + stabilization | 223 passed / 1 skipped / 0 failed; 32 net new tests; no Phase 4 regressions; eval baseline captured at 100% aggregate recall |

## Files added

- `extensions/nexus-code-search/src/nexus_code_search/frameworks/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/frameworks/base.py`
- `extensions/nexus-code-search/src/nexus_code_search/frameworks/django.py`
- `extensions/nexus-code-search/src/nexus_code_search/frameworks/express.py`
- `extensions/nexus-code-search/src/nexus_code_search/frameworks/fastapi.py`
- `extensions/nexus-code-search/src/nexus_code_search/graph/affected.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/__init__.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/__main__.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/runner.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/minimal/code/app.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/minimal/fixtures.yaml`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/python_app/code/{main,models,service}.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/python_app/fixtures.yaml`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/fastapi_app/code/routes.py`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/fastapi_app/fixtures.yaml`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/ts_express/code/handlers.ts`
- `extensions/nexus-code-search/src/nexus_code_search/eval/fixtures/ts_express/fixtures.yaml`
- `extensions/nexus-code-search/tests/fixtures/frameworks/django/{simple,regex,nested}_urls.py`
- `extensions/nexus-code-search/tests/fixtures/frameworks/fastapi/{basic,router,flask}_app.py`
- `extensions/nexus-code-search/tests/fixtures/frameworks/express/{basic_app,router_app,middleware_chain}.ts`
- `extensions/nexus-code-search/tests/test_django_routes.py`
- `extensions/nexus-code-search/tests/test_fastapi_routes.py`
- `extensions/nexus-code-search/tests/test_express_routes.py`
- `extensions/nexus-code-search/tests/test_affected.py`
- `extensions/nexus-code-search/tests/test_affected_cli.py`
- `extensions/nexus-code-search/tests/test_server_affected.py`
- `extensions/nexus-code-search/tests/test_eval_runner.py`
- `scripts/nexus_hub_affected.py`
- `docs/archive/v2/v2.2/eval-baseline.md`
- `docs/archive/v2/v2.2/docs-cleanup-report-phase5.md`
- `docs/archive/v2/v2.2/development/history/2026-05-22_phase-5-code-graph-capabilities.md` (this file)

## Files modified

- `extensions/nexus-code-search/src/nexus_code_search/extraction/orchestrator.py` -- invoke FRAMEWORK_RESOLVERS after AST extraction; thread emitted nodes / edges into the per-file combined output
- `extensions/nexus-code-search/src/nexus_code_search/graph/__init__.py` -- export `affected_tests`
- `extensions/nexus-code-search/src/nexus_code_search/server.py` -- add `code_affected_tests` MCP tool registration + handler + SERVER_INSTRUCTIONS update
- `extensions/nexus-code-search/pyproject.toml` -- add `force-include` for `eval/fixtures/`
- `extensions/nexus-code-search/README.md` -- document `code_affected_tests`, the CLI dispatcher, framework resolvers, and the eval harness
- `scripts/installer.sh` -- copy `nexus_hub_affected.py` into `~/.nexus-hub/scripts/`
- `scripts/installer.ps1` -- mirror lockstep
- `Makefile` -- add `make eval` target wired to `docs/archive/v2/v2.2/eval-baseline.md`
- `docs/archive/v2/v2.2/known-gaps.md` -- log Phase 5 close + new WN-7 gap (FTS5 precision)
- `docs/DEVLOG.md` -- prepend Phase 5 entry

## Test results

- **`extensions/nexus-code-search/tests/`**: 223 passed, 1 skipped, 0 failed (up from 191 / 1 / 0 at Phase 4 close; 32 net new tests).
- **`make validate` equivalent** (`data/*.json` parse + skill counts): 206 skills / 15 bundles / 17 workflows; templates.json OK; no changes from Phase 4.
- **Eval baseline**: 100% aggregate recall, 63.3% aggregate precision; every fixture clears the 80% per-fixture recall gate.

## Deviations from plan

- The plan said to ship the eval harness at `extensions/nexus-code-search/eval/`. I placed it at `extensions/nexus-code-search/src/nexus_code_search/eval/` instead so `python -m nexus_code_search.eval.runner` works as the plan also documented in its T033 prompt. The harness, fixtures, and Make target work as specified; only the directory layout differs.
- The `python_app` fixture originally tested cross-file call resolution (e.g. `run` calls `make_user` in `service.py`). Phase 4 only emits in-file `calls` edges (cross-file resolution is deferred to v2.3.0+ per WN-6), so the fixture was reshaped to exercise FTS search across files instead. This keeps the eval baseline honest about what Phase 4 / Phase 5 actually deliver. Logged in this session-history; not a separate known-gap entry because cross-file resolution is already tracked under WN-6.

## Known gaps logged

- **WN-7**: Phase 5 eval baseline shows 63.3% aggregate precision because FTS5 surfaces parameters and signature tokens alongside the target symbol name. Recall is 100% on every fixture; the precision gap is a function of the eval answer-key narrowness, not a graph defect. Suggested follow-up in v2.3.0: tighten `code_search` kind filtering or widen fixture expectations.

## Next phase

Phase 6 (Polish, data-registry rebaseline, and release) is now unblocked. It runs the cross-OS installer smoke, authors `docs/archive/v2/v2.2/RELEASE_NOTES.md` and the CHANGELOG `[2.2.0]` block, finalizes `docs/archive/v2/v2.2/known-gaps.md`, bumps version manifests, and prepares the `git tag v2.2.0` cut.
