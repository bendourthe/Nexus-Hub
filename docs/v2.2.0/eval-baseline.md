# nexus-code-search eval baseline (v2.2.0)

This is the baseline scoring report produced by the synthetic-codebase eval harness in `extensions/nexus-code-search/src/nexus_code_search/eval/`. Regenerate with `make eval` (or `python -m nexus_code_search.eval` from the extension directory).

The harness runs four fixture codebases (`minimal`, `python_app`, `fastapi_app`, `ts_express`) under `eval/fixtures/`, indexes each with the v2.0 AST graph, then runs the questions in each fixture's `fixtures.yaml` against the relevant MCP tools (`code_search`, `code_callers`, `code_callees`, `code_impact`, `code_context`). Each question is scored as recall (fraction of expected names found) and precision (fraction of found names that were expected).

The v2.2.0 exit gate is **>= 80% aggregate recall**, which the current baseline clears comfortably. Cross-file call edges are deferred to v2.3.0+; the python_app fixture deliberately exercises FTS-based search rather than cross-file traversal so the baseline reflects what Phase 4 / Phase 5 actually ship.

## nexus-code-search eval report

Aggregate recall: **100.0%** Aggregate precision: **63.3%**

## Per-fixture

| Fixture | Questions | Recall | Precision |
|---------|-----------|--------|-----------|
| fastapi_app | 4 | 100.0% | 75.0% |
| minimal | 5 | 100.0% | 90.0% |
| python_app | 5 | 100.0% | 38.3% |
| ts_express | 4 | 100.0% | 50.0% |

## fastapi_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `create_item` | create_item | create_item, name | 100.0% | 50.0% |
| code_search | `delete_item` | delete_item | delete_item, item_id | 100.0% | 50.0% |
| code_callees | `root` | (none) | (none) | 100.0% | 100.0% |
| code_context | `create_item` | (none) | (none) | 100.0% | 100.0% |

## minimal

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `helper` | helper | helper, x | 100.0% | 50.0% |
| code_callers | `helper` | main | main | 100.0% | 100.0% |
| code_callees | `main` | helper | helper | 100.0% | 100.0% |
| code_impact | `helper` | main | main | 100.0% | 100.0% |
| code_context | `helper` | main | main | 100.0% | 100.0% |

## python_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `AdminUser` | AdminUser | AdminUser, models.AdminUser, is_admin, self | 100.0% | 25.0% |
| code_search | `make_admin` | make_admin | make_admin, name | 100.0% | 50.0% |
| code_search | `is_admin` | is_admin | is_admin, self | 100.0% | 50.0% |
| code_search | `make_user` | make_user | make_user, service.make_user, name | 100.0% | 33.3% |
| code_search | `greet_user` | greet_user | greet_user, service.greet_user, user | 100.0% | 33.3% |

## ts_express

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `listUsers` | listUsers | listUsers, listUsers, req, res | 100.0% | 33.3% |
| code_search | `getUser` | getUser | getUser, getUser, req, res | 100.0% | 33.3% |
| code_search | `createUser` | createUser | createUser, createUser, req, res | 100.0% | 33.3% |
| code_context | `listUsers` | (none) | (none) | 100.0% | 100.0% |
