# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: v3.15.0 adoption-codesight IN PROGRESS on `feat/adoption-codesight` (cut off `develop`). Phase 1 of 7 COMPLETE (compiled context-map generator + `generate_context_map` MCP tool + `nexus-hub map` CLI). Phases 2-7 (framework extraction, graph enrichment, measurement + health, knowledge layer, terminal refactor + release) pending.
**Last updated**: 2026-07-21 (v3.15.0 adoption-codesight Phase 1)

> **Scope note (version collision)**: three plans under `docs/v3/v3.15/plans/` are all stamped `v3.15.0` - `platform-parity-all-gaps` (appears complete on its own branch), `adoption-codesight` (this file), and `adoption-awesome-llm-apps`. Only one feature set can ship as v3.15.0. This is the comparison-versioning artifact (plans stamped with the authoring-cycle version, not the real adoption target). It is NOT a Phase-1 blocker (Phase 1 is extension-only code with its own package version and touches no catalog version surface), but it MUST be reconciled before this plan's release phase (Phase 7 / `/update release`). See QG-2.

> **Prior-version ingest**: checked `docs/v3/v3.14/known-gaps.md`. The open v3.14 items (usage-monitor DF/HO series) are unrelated to this feature set and do not carry in. The one relevant caveat is **HO-1** (flat/nested skill-name collision across skill layouts): this plan may ship at most one or two new catalog skills in later phases (map-health lint E, knowledge extractor F); Phase 7's dry-run install must verify no flat/nested same-`name` collision is introduced. Phase 1 shipped zero new catalog skills (all work is extension code), so HO-1 does not apply this phase.

## v3.15.0

**Status**: Phase 1 of 7 COMPLETE on `feat/adoption-codesight`. Extension-only: a deterministic `.nexus/CONTEXT-MAP.md` + `.nexus/context/` article set compiled from the existing tree-sitter graph, exposed as the `generate_context_map` MCP tool and a `nexus-hub map` one-shot CLI. Emits only under `<root>/.nexus/` (never CLAUDE.md / AGENTS.md); deterministic (no wall-clock timestamp, so the tool and CLI are byte-identical); content-hash-incremental (unchanged graph is a no-op). New-code coverage 97%; full extension suite green (222 passed, 1 pre-existing skip). No catalog registry files, installers, or `base-*.md` templates touched.

### Open Items

#### Deferred

##### DF-1 - Overview "frameworks" line and "Most-Imported Files" section are Phase 1 placeholders

- **Source phase**: v3.15.0 adoption-codesight Phase 1 (1.1)
- **Plan reference**: Phase 1.1 ("frameworks best-effort"; "most-imported files (placeholder in this phase, filled in Phase 4)")
- **Reason**: the compiled map renders a "Most-Imported Files" section as an explicit placeholder, and the Overview omits a frameworks line entirely, to respect phase boundaries. Framework detection is Phase 2 (route/framework extraction) and file-level import ranking is Phase 4 (graph enrichment). Doing either now would pull later-phase work forward.
- **Suggested next step**: Phase 2 populates frameworks in the Overview from the framework extractors; Phase 4 fills the Most-Imported Files section from the import edges the graph already stores (a file-level view labeled distinct from symbol-level `code_impact`).

##### DF-2 - nexus-code-search extension package version not bumped

- **Source phase**: v3.15.0 adoption-codesight Phase 1
- **Plan reference**: Constitution Check ("The extension carries its own package version, independent of the catalog version"; version bumps happen at release)
- **Reason**: Phase 1 added a feature (the context-map surface) but left `extensions/nexus-code-search/pyproject.toml` at `2.0.0`. Per the plan, version bumps are a release-phase action, and the full context-map feature set spans Phases 1-6; bumping mid-feature would be premature.
- **Suggested next step**: bump the extension package version (e.g. `2.0.0 -> 2.1.0`) in Phase 7 once all context-map phases have landed, alongside the README surface documentation.

#### Warnings

##### WN-1 - Pre-existing unused `json` import in scripts/nexus_hub_cli.py

- **Source phase**: v3.15.0 adoption-codesight Phase 1 (1.2)
- **Plan reference**: Phase 1.2 (wiring `nexus-hub map` into the existing CLI dispatcher)
- **Reason**: ruff flags `F401 json imported but unused` in `scripts/nexus_hub_cli.py`. The import is PRE-EXISTING (present on `develop`; only referenced in a docstring string "plugin.json"), not introduced by this phase, and `scripts/` is not ruff-gated in this repo's CI. Per the no-out-of-scope-cleanup rule it was left untouched. All Phase 1 new/modified extension code is ruff-clean.
- **Suggested next step**: remove the unused import as part of a dedicated `scripts/` lint pass, or in Phase 7's terminal refactor if it touches this file.

#### Missing tests / coverage gaps

##### MT-1 - Repo-level `nexus-hub map` dispatch has no automated test

- **Source phase**: v3.15.0 adoption-codesight Phase 1 (1.2)
- **Plan reference**: Phase 1.3 ("Assert the MCP tool and `nexus-hub map` produce identical output")
- **Reason**: the extension test suite fully covers the map surface (generator, model, tokens, the `generate_context_map` MCP handler, and `nexus_code_search.contextmap.cli` - which is exactly what `nexus-hub map` forwards to; tool-vs-CLI byte-identity is asserted). The thin dispatch in `scripts/nexus_hub_cli.py` (a 3-line verbatim forward, mirroring the un-tested `nexus_hub_affected.py` precedent) is verified only by a manual smoke run this phase, not an automated repo-level test. The extension suite lives in isolation and should not import a repo-level `scripts/` module.
- **Suggested next step**: add a small repo-level dispatch test (e.g. under `tests/`) asserting `nexus_hub_cli.main(["map", ...])` forwards and returns the extension CLI's exit code, or fold it into Phase 7's CI/test-coverage pass.

#### Quality-gate gaps

##### QG-1 - code-search extension tests run in both ci.yml and code-search.yml on extension changes

- **Source phase**: v3.15.0 adoption-codesight Phase 1 (1.3)
- **Plan reference**: Phase 1.3 ("path-filtered ... while minimizing action minutes")
- **Reason**: Phase 1 added `.github/workflows/code-search.yml` (path-filtered to `extensions/nexus-code-search/**`, pip-cached, concurrency cancel-in-progress) for fast scoped feedback, but the always-on `tests` job in `ci.yml` still installs and runs the extension suite too. On an extension-touching change both run, a small duplicate cost. Removing the extension step from the monolithic `tests` job was NOT done in Phase 1 because it is an invasive edit to a shared CI file that also weakens cross-cutting coverage (a non-extension change that breaks the extension's imports would no longer be caught by an always-on job), and CI optimization is explicitly Phase 7's charter.
- **Suggested next step**: in Phase 7's CI/CD optimization pass, decide whether the path-filtered `code-search.yml` becomes the sole runner for the extension suite (dropping the `ci.yml` step) or whether the always-on gate is retained for cross-cutting safety.

##### QG-2 - Three plans stamped v3.15.0 (release-time version reconciliation)

- **Source phase**: v3.15.0 adoption-codesight Phase 1 (Phase 0 resolution)
- **Plan reference**: n/a (surfaced during plan/phase resolution)
- **Reason**: `platform-parity-all-gaps`, `adoption-codesight`, and `adoption-awesome-llm-apps` are all stamped `v3.15.0`. Only one can ship under that version. Not a Phase-1 blocker (extension-only code, no catalog version surface touched), but a release blocker for this plan until reconciled.
- **Suggested next step**: before Phase 7 / `/update release`, decide which plan is the real v3.15.0 and re-stamp the others to their true adoption targets (this is the comparison-versioning-flaw pattern the v3.14.2 fix addressed for future comparisons).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |
| Hand-offs (HO) | 0 | 0 |

### Advisory

- **tiktoken is optional, not a dependency**: the token-count header prefers `tiktoken` (cl100k_base) when it is importable and loads without a network fetch, and otherwise falls back to a deterministic stdlib heuristic (word + punctuation runs). The extension adds no dependency on tiktoken, preserving its zero-outbound posture. Token counts therefore differ between an environment with tiktoken cached and one without; within any single environment they are deterministic, so the tool-vs-CLI byte-identity and the token-header self-consistency both hold.
- **`.nexus/` layout for consumers**: the generator writes `<root>/.nexus/CONTEXT-MAP.md` and `<root>/.nexus/context/*.md` (intended to be committed) alongside the pre-existing `<root>/.nexus/code-index/` graph database (gitignored). Consumer-repo `.gitignore` guidance (commit the map, ignore the index) is documented in the extension README and will be expanded in Phase 5/7.
