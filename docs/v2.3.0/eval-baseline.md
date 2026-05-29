# nexus-code-search eval baseline (v2.3.0)

This is the baseline scoring report produced by the synthetic-codebase eval harness in `extensions/nexus-code-search/src/nexus_code_search/eval/`. Regenerate with `make eval` (or `python -m nexus_code_search.eval` from the extension directory).

The harness runs eight fixture codebases under `eval/fixtures/`, indexes each with the v2.0 AST graph, then runs the questions in each fixture's `fixtures.yaml` against the relevant MCP tools (`code_search`, `code_callers`, `code_callees`, `code_impact`, `code_context`). Each question is scored as recall (fraction of expected names found) and precision (fraction of found names that were expected).

## What changed at v2.3.0 (Phase 8)

- **Precision: 63.3% -> 96.2%** (recall held at 100%). T029 (WN-7) scoped the default `code_search` FTS match to the `name` column. Previously the match also covered `qualified_name`, so a query like `AdminUser` surfaced the class plus every node whose qualified_name embedded it as an ancestor segment (its method `is_admin`, the parameter `self`) and the duplicate export specifiers in the TS fixture. Name-scoping removes that false-positive class; `all_fields=true` restores the wider match for docstring / path-segment search.
- **Four new language fixtures** (T030 / DF-002): `go_app`, `rust_app`, `java_app`, `csharp_app`, exercising the new Go / Rust / Java / C# extractors (struct/trait/class/interface extraction, `extends` / `implements` / `instantiates` / `overrides` edges, and in-file calls). Every fixture clears the >= 80% per-fixture recall gate (all at 100%).
- **`instantiates` edges** (T028 / WN-6) now participate in `code_impact`: the Java / C# `code_impact Lion` questions reach `create` / `Create` through the constructor relationship.

The v2.3.0 exit gate remains **>= 80% aggregate recall**, which the current baseline clears at 100%. The only sub-100% precision fixture is `python_app` (70%): a `code_search` for a class or function legitimately also surfaces the import-statement node that re-exports it under a dotted name (e.g. `service.make_user`), which the FTS `name` column tokenizes to include the queried symbol. This is honest import-site noise, not a false positive in the extractor; widening the answer keys or excluding import nodes from default search is tracked as a future refinement.

## nexus-code-search eval report

Aggregate recall: **100.0%** Aggregate precision: **96.2%**

## Per-fixture

| Fixture | Questions | Recall | Precision |
|---------|-----------|--------|-----------|
| csharp_app | 5 | 100.0% | 100.0% |
| fastapi_app | 4 | 100.0% | 100.0% |
| go_app | 5 | 100.0% | 100.0% |
| java_app | 5 | 100.0% | 100.0% |
| minimal | 5 | 100.0% | 100.0% |
| python_app | 5 | 100.0% | 70.0% |
| rust_app | 5 | 100.0% | 100.0% |
| ts_express | 4 | 100.0% | 100.0% |

## csharp_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Lion` | Lion | Lion | 100.0% | 100.0% |
| code_search | `Animal` | Animal | Animal | 100.0% | 100.0% |
| code_search | `Create` | Create | Create | 100.0% | 100.0% |
| code_impact | `Lion` | Create, Animal | Animal, Create | 100.0% | 100.0% |
| code_callers | `Animal` | (none) | (none) | 100.0% | 100.0% |

## fastapi_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `create_item` | create_item | create_item | 100.0% | 100.0% |
| code_search | `delete_item` | delete_item | delete_item | 100.0% | 100.0% |
| code_callees | `root` | (none) | (none) | 100.0% | 100.0% |
| code_context | `create_item` | (none) | (none) | 100.0% | 100.0% |

## go_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Greeter` | Greeter | Greeter | 100.0% | 100.0% |
| code_search | `NewGreeter` | NewGreeter | NewGreeter | 100.0% | 100.0% |
| code_search | `Speaker` | Speaker | Speaker | 100.0% | 100.0% |
| code_callees | `main` | NewGreeter, Speak | NewGreeter, Speak | 100.0% | 100.0% |
| code_callers | `NewGreeter` | main | main | 100.0% | 100.0% |

## java_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Lion` | Lion | Lion | 100.0% | 100.0% |
| code_search | `Animal` | Animal | Animal | 100.0% | 100.0% |
| code_search | `create` | create | create | 100.0% | 100.0% |
| code_impact | `Lion` | create, Animal | Animal, create | 100.0% | 100.0% |
| code_callers | `Animal` | (none) | (none) | 100.0% | 100.0% |

## minimal

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `helper` | helper | helper | 100.0% | 100.0% |
| code_callers | `helper` | main | main | 100.0% | 100.0% |
| code_callees | `main` | helper | helper | 100.0% | 100.0% |
| code_impact | `helper` | main | main | 100.0% | 100.0% |
| code_context | `helper` | main | main | 100.0% | 100.0% |

## python_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `AdminUser` | AdminUser | AdminUser, models.AdminUser | 100.0% | 50.0% |
| code_search | `make_admin` | make_admin | make_admin | 100.0% | 100.0% |
| code_search | `is_admin` | is_admin | is_admin | 100.0% | 100.0% |
| code_search | `make_user` | make_user | make_user, service.make_user | 100.0% | 50.0% |
| code_search | `greet_user` | greet_user | greet_user, service.greet_user | 100.0% | 50.0% |

## rust_app

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `Circle` | Circle | Circle | 100.0% | 100.0% |
| code_search | `Shape` | Shape | Shape | 100.0% | 100.0% |
| code_search | `make` | make | make | 100.0% | 100.0% |
| code_callees | `run` | make, area | make, area | 100.0% | 100.0% |
| code_callers | `make` | run | run | 100.0% | 100.0% |

## ts_express

| Tool | Query | Expected | Found | Recall | Precision |
|------|-------|----------|-------|--------|-----------|
| code_search | `listUsers` | listUsers | listUsers, listUsers | 100.0% | 100.0% |
| code_search | `getUser` | getUser | getUser, getUser | 100.0% | 100.0% |
| code_search | `createUser` | createUser | createUser, createUser | 100.0% | 100.0% |
| code_context | `listUsers` | (none) | (none) | 100.0% | 100.0% |
