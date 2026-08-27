# Session History -- v2.3.0 Phase 8: Code-graph quality & extractor expansion

**Date**: 2026-05-29
**Plan**: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](../../plans/adoption-ecc-cybersec-skills.md)
**Phase**: 8 of 9 -- [known-gaps] Code-graph quality & extractor expansion
**Sub-tasks**: T026 (WN-1), T027 (WN-5), T028 (WN-6), T029 (WN-7), T030 (DF-002), T031 (stabilization)
**Outcome**: All five v2.2.0 carryover items (WN-1, WN-5, WN-6, WN-7, DF-002) closed. Scope was entirely within `extensions/nexus-code-search/` plus the Makefile `eval` target path and docs.

## Goal

Resolve the v2.2.0 `nexus-code-search` code-graph quality and dependency-hygiene gaps and ship the next batch of language extractors, without regressing the existing Python / TypeScript surfaces or the eval recall gate.

## Pre-implementation findings

The Phase 1 review traced each carryover gap to its exact site and confirmed the toolchain on this machine:

- The 52 `GitWildMatchPattern` deprecation warnings originate from a single call: `pathspec.PathSpec.from_lines("gitwildmatch", ...)` in `indexer.py::_load_ignore_spec` (WN-1).
- The `code_search` precision shortfall (63.3%) is a column-matching artifact: the FTS5 virtual table indexes `name`, `qualified_name`, and `docstring`, so a query like `AdminUser` matches the class plus every node whose qualified_name embeds it as an ancestor segment (its method `is_admin`, the parameter `self`) and the duplicate export specifiers in the TS fixture (WN-7).
- `EdgeKind.INSTANTIATES` / `OVERRIDES` already exist in the taxonomy; only extraction logic was missing (WN-6).
- The Go / Rust / Java / C# tree-sitter grammars are installable under the existing `<0.26` ceiling (go 0.25, rust 0.24, java/c-sharp 0.23), and no 0.26-compatible release of the existing pins has shipped (WN-5).

Two decisions were taken to the user up front (both shape the implementation): the T030 language batch (chosen: **Go + Rust + Java + C#**) and the T029 precision approach (chosen: **scope the default search to the name column**, rather than the plan's kind-inference heuristic or answer-key widening).

## What was implemented

### T026 (WN-1) -- pathspec deprecation

`indexer.py::_load_ignore_spec` switched the pattern factory from the deprecated `gitwildmatch` to `gitignore`, verified to match identically on the indexer fixtures. The full suite now passes under `pytest -W error::DeprecationWarning`.

### T027 (WN-5) -- tree-sitter pin re-verification

Re-verified the latest published versions: `tree-sitter` 0.25.2, `tree-sitter-python` 0.25.0, `tree-sitter-typescript` 0.23.2 -- all still `<0.26`, so the ceiling stays. A dated comment in `pyproject.toml` records the 2026-05-29 check; the four new grammar deps were added under the same shared `<0.26` ceiling.

### T028 (WN-6) -- instantiates / overrides edges

`python.py` and `typescript.py` now emit:

- `instantiates`: a call (`Foo()` in Python, `new Foo()` or a call resolving to a class in TS) whose resolved target is a `class` becomes `INSTANTIATES` instead of `CALLS`.
- `overrides`: a new `_resolve_overrides` pass walks the in-file `extends` chain (transitively, with a cycle guard) and emits `OVERRIDES` from a method to a same-named parent method.

`INSTANTIATES` was added to `traverser._IMPACT_KINDS` so re-typing a constructor call from `calls` does not silently drop it from `code_impact`.

### T029 (WN-7) -- name-scoped search

`traverser.search_fts` now wraps the default FTS query as `name : (<query>)` via a new `_scope_to_name` helper (left unchanged when the query is empty or already uses column syntax). An `all_columns` opt-out is threaded through `GraphQueryManager.search` and surfaced on the `code_search` MCP tool as `all_fields`. Aggregate eval precision rose **63.3% -> 96.2%** with recall held at 100%.

### T030 (DF-002) -- Go / Rust / Java / C# extractors

Four new extractor modules under `extraction/languages/`, registered in `LANGUAGE_EXTRACTORS` for `.go` / `.rs` / `.java` / `.cs` / `.csx`, each following the `python.py` pattern (parser -> top-level walk -> `_collect_calls`):

- **go.py**: package / struct / interface / receiver-keyed method / field / import / const / var; `instantiates` from composite literals; calls via identifier + selector.
- **rust.py**: mod / struct / enum / trait / impl-block method / use-import; `implements` from `impl Trait for Type`; `instantiates` from struct literals; calls via identifier / scoped_identifier / field_expression.
- **java.py**: package / class / interface / method / constructor / field / import; full `extends` / `implements` / `overrides`; `instantiates` from `new`.
- **csharp.py**: namespace (block + file-scoped, recursive) / class / interface / struct / method / property / field / using; `base_list` resolved to `extends` vs `implements` by the target's kind; `overrides`; `instantiates` from `new`.

The new extractors deliberately omit `parameter` nodes (to avoid re-introducing the FTS noise T029 just removed). Four matching tree-sitter deps were added to `pyproject.toml`. Four eval fixtures (`go_app` / `rust_app` / `java_app` / `csharp_app`) were added, each clearing the 80% per-fixture recall gate (all at 100%).

`_language_for` in `orchestrator.py` gained proper labels (`go` / `rust` / `java` / `csharp`).

### T031 -- stabilization + eval baseline

Created `docs/archive/v2/v2.3/eval-baseline.md` (eight fixtures, 100% recall, 96.2% precision) and repointed the Makefile `eval` target to it. Added 24 extractor unit tests, 3 Python-edge + 2 TS-edge tests (T028), 2 name-scope tests (T029), and a recall-gate assertion that fails if any fixture drops below 80%.

## Deviations from a naive plan reading (all intended)

- **T029 approach**: the plan offered (a) kind-inference or (b) answer-key widening; the user chose a third, more principled lever -- name-column scoping -- which is squarely within "improve precision without dropping recall" and yields a real-world gain, not just a higher eval number.
- **`INSTANTIATES` added to impact kinds**: not literally in the T028 prompt, but required to avoid silently shrinking `code_impact` when constructor calls are re-typed away from `calls`.
- **No installer edit for T030**: the new tree-sitter deps live in `pyproject.toml`, which both installers resolve via `pip install -e` of the copied package; T030 added no standalone `scripts/*.py`, so the explicit-name copy step does not apply.
- **python_app eval at 70%**: name-scoping still surfaces import-statement nodes whose `name` is the dotted import path (`service.make_user`). This is honest import-site noise, recorded as DF-v23-5 rather than masked.

## Testing results

- `extensions/nexus-code-search`: **168 passed, 1 skipped** (+32 new tests), zero `DeprecationWarning`s under `pytest -W error::DeprecationWarning`.
- Eval: 8/8 fixtures at 100% recall; aggregate precision 63.3% -> 96.2%; every fixture clears the >=80% recall gate.
- `make validate` equivalent: skills.json 227 OK, bundle audit 0 orphans / 0 errors, four CI validators (no-personal-paths, unicode-safety, supply-chain, workflow-security) all rc=0.
- Git status: only intended source / doc changes; no stray build artifacts (8.1 -> 0 new `.gitignore` patterns).
- CI readiness (8.3): GitHub Actions `pip install -e "extensions/nexus-code-search/[dev]"` resolves the new deps and auto-discovers the new test files; 0 workflow edits.

## Known gaps recorded

- **DF-v23-4**: extractor coverage is partial -- 4 of ~18 languages shipped, no new framework extractors, parameter nodes omitted for the new languages.
- **DF-v23-5**: `code_search` precision residual on import-statement nodes (python_app 70%).

Five carryover items (WN-1, WN-5, WN-6, WN-7, DF-002) were moved to the Resolved table in `docs/archive/v2/v2.3/known-gaps.md`.

## Next steps

Phase 9 (the final phase) -- live-environment verification of the Antigravity CLI assumptions (WN-2 / WN-3 / WN-4) on a live VM and the cross-OS installer smoke on macOS / Linux (WN-8) -- then the v2.3.0 release-readiness workflow.

## Dependency / network note

Four new runtime dependencies (`tree-sitter-go`, `tree-sitter-rust`, `tree-sitter-java`, `tree-sitter-c-sharp`), all pinned under the existing `<0.26` ceiling and resolved automatically by both installers' editable install. Zero outbound network calls anywhere in the new extractors -- all parsing is local tree-sitter, consistent with the MCP Registry Policy.
