# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: v3.15.0 adoption-codesight IN PROGRESS on `feat/adoption-codesight` (cut off `develop`). Phases 1-6 of 7 COMPLETE (Phase 1: generator + tool + CLI; Phase 2: routes + env + middleware; Phase 3: ORM schema + components + events; Phase 4: hot files + `--since` change map; Phase 5: token-savings benchmark + map-health lint; Phase 6: knowledge-map extractor). **Both DoD axes hold** (measured token-reduction + verified extractor accuracy). Phase 7 (terminal refactor + known-gaps reconciliation + matrix + CI/CD + release) pending.
**Last updated**: 2026-07-21 (v3.15.0 adoption-codesight Phase 6)

> **Scope note (version collision)**: three plans under `docs/v3/v3.15/plans/` are all stamped `v3.15.0` - `platform-parity-all-gaps` (appears complete on its own branch), `adoption-codesight` (this file), and `adoption-awesome-llm-apps`. Only one feature set can ship as v3.15.0. This is the comparison-versioning artifact (plans stamped with the authoring-cycle version, not the real adoption target). It is NOT a Phase-1 blocker (Phase 1 is extension-only code with its own package version and touches no catalog version surface), but it MUST be reconciled before this plan's release phase (Phase 7 / `/update release`). See QG-2.

> **Prior-version ingest**: checked `docs/v3/v3.14/known-gaps.md`. The open v3.14 items (usage-monitor DF/HO series) are unrelated to this feature set and do not carry in. The one relevant caveat is **HO-1** (flat/nested skill-name collision across skill layouts): this plan may ship at most one or two new catalog skills in later phases (map-health lint E, knowledge extractor F); Phase 7's dry-run install must verify no flat/nested same-`name` collision is introduced. Phase 1 shipped zero new catalog skills (all work is extension code), so HO-1 does not apply this phase.

## v3.15.0

**Status**: Phases 1-3 of 7 COMPLETE on `feat/adoption-codesight`. Extension-only, no catalog registry / installer / `base-*.md` changes. Phase 1: a deterministic `.nexus/CONTEXT-MAP.md` + `.nexus/context/` article set compiled from the existing tree-sitter graph, exposed as the `generate_context_map` MCP tool and a `nexus-hub map` one-shot CLI (neutral-path, byte-identical tool/CLI, content-hash no-op). Phase 2: framework-aware route extraction (method / path / params / behavior tags), an env-var audit (required vs has-default, `.env.example` names only), and middleware detection/categorization, feeding Routes / Environment / Middleware sections. Phase 3: ORM schema extraction (SQLAlchemy / Django / Prisma - fields, PK/FK/unique, and relation resolution), React component extraction (props), and background-event detection (Celery / BullMQ / Kafka / EventEmitter), feeding Data Models / Components / Events sections + a `database` article. All gated by an extraction-accuracy harness (per-section recall + a hard zero-false-positive gate, plus an explicit relation-resolution assertion) over per-framework fixtures. `GENERATOR_VERSION` 1 -> 3. New-code coverage 95%; full extension suite green (257 passed, 1 pre-existing skip).

### Open Items

#### Deferred

##### DF-3 - Additional frameworks / ORMs / component libs / event patterns deferred (explicit coverage, not silent)

- **Source phase**: v3.15.0 adoption-codesight Phase 2 (2.1) + Phase 3 (3.1, 3.2)
- **Plan reference**: Phase 2.1 / Phase 3.1 / Phase 3.2 ("verifying each with a fixture before adding the next ... Do NOT attempt every framework at once")
- **Reason**: per the plan's incremental posture, each detector lands with its own fixture rather than all at once. Currently covered:
    - **Routes**: FastAPI, Flask, Django, Express (via the existing resolvers). Deferred: Hono / Fastify / Next / NestJS (TS), Gin (Go), Rails (Ruby), Spring Boot (Java), Laravel (PHP) - each needs a new extraction-time resolver + fixture.
    - **ORM schema**: SQLAlchemy, Django ORM, Prisma. Deferred: TypeORM, Drizzle (TS), ActiveRecord (Ruby), GORM (Go) - decorator/call-based, each needs its own detector + fixture.
    - **Components**: React (props via destructuring or the resolved prop type). Deferred: Vue, Svelte. Design-system-primitive auto-filtering is also deferred (JSX-file scoping + node_modules exclusion already filter library primitives).
    - **Events**: declaration-strong signals (Celery task decorators, BullMQ `new Queue/Worker`, Kafka, `new EventEmitter`). Deferred: invocation-only patterns (`.delay(`, `.emit(`, Redis `.publish(`/`.subscribe(`) - too common to detect without false positives.
- **Suggested next step**: add a detector + fixture per additional target in a follow-on pass; Phase 7 records the final deferred-coverage list. The map's section renderers and the accuracy harness already handle any new detector's output generically.

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

##### WN-2 - Pre-existing ruff findings in graph/affected.py

- **Source phase**: v3.15.0 adoption-codesight Phase 4 (4.1)
- **Plan reference**: Phase 4.1 (adding `most_imported_files` to `graph/affected.py`)
- **Reason**: ruff flags an unused `EdgeKind` import (F401) and an unused `frontier` local (F841) in `graph/affected.py`. Both are PRE-EXISTING (confirmed present on committed HEAD; Phase 4 only ADDED `most_imported_files`, which is ruff-clean), and the extension `src/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove both in Phase 7's terminal refactor (or a dedicated extension lint pass).

#### Missing tests / coverage gaps

##### MT-2 - Benchmark `--update-baseline` write path not automated-tested

- **Source phase**: v3.15.0 adoption-codesight Phase 5 (5.1)
- **Plan reference**: Phase 5.1 / 5.3
- **Reason**: `measured_baseline()` (the value builder) is unit-tested, but the `benchmark --update-baseline` CLI branch that OVERWRITES the committed `benchmark_baseline.json` is deliberately not exercised in the suite - a test that ran it would clobber the committed baseline. The gate path (`--check`), JSON/report output, and `--repo` mode are all tested.
- **Suggested next step**: if desired, test `--update-baseline` against a monkeypatched `BASELINE_PATH` pointing at a temp file. Low value (the write is a two-line `Path.write_text`).

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

#### Resolved

##### DF-1 - Overview frameworks line + Most-Imported Files section (RESOLVED)

- Originally Phase 1's placeholder for the Overview `Frameworks:` line and the "Most-Imported Files" section. The frameworks half was resolved in Phase 2 (the Overview now carries a `Frameworks:` line inferred from detected routes + middleware); the Most-Imported Files half was resolved in Phase 4 (`most_imported_files` fills the section from inbound import edges, labeled distinct from symbol-level `code_impact`). Both halves shipped and are fixture-tested.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |
| Hand-offs (HO) | 0 | 0 |

DF-1 is fully RESOLVED (frameworks line in Phase 2, Most-Imported Files in Phase 4). DF-2 (extension version bump) and DF-3 (deferred detectors) remain open. MT-2 added in Phase 5 (benchmark `--update-baseline` write path untested). WN-1, WN-2, MT-1, QG-1, QG-2 carry unchanged.

### Advisory

- **Definition-of-done measured half VALIDATED (Phase 5)**: the token-savings benchmark measures the compiled map vs a simulated manual-exploration cost. On the committed sample corpus (3 realistic repos) the map saves ~44-55% of exploration tokens (regression-guarded by `benchmark_baseline.json`); on Nexus-Hub itself a ~22k-token map replaces ~1.9M tokens (~99% reduction, 443 files, 67 routes / 13 models / 5 components / 42 env vars detected). Combined with the Phase 2-3 zero-FP + recall accuracy harness, both DoD axes hold. The tiny per-framework `contextmap` fixtures are NOT a benchmark corpus - a map is not worth its fixed overhead on a 2-file repo; savings scale with codebase size, which is why the plan specifies real repos.
- **Map-health lint ships as extension code, not a new catalog skill (Phase 5.2 decision)**: the deterministic checks (orphan articles, missing backlinks, staleness) live in `contextmap/maphealth.py` (exposed as the `map_health` MCP tool + `nexus-hub map --lint`); the richer semantic checks stay in the LLM-native `documentation-consistency` skill. No `data/` registry files were touched.
- **Knowledge-map extractor ships as extension code, not a new catalog skill (Phase 6.1 decision, re-confirmed at implementation)**: the mechanical classification + decision / open-question extraction lives in `contextmap/knowledge.py` (exposed as the `generate_knowledge_map` MCP tool + `nexus-hub map --knowledge`); narrative synthesis stays with the LLM-native `solution-knowledge-base` skill. **Phases 1-6 remain entirely extension-only - no `data/` registry, installer, or `base-*.md` change.**
- **tiktoken is optional, not a dependency**: the token-count header prefers `tiktoken` (cl100k_base) when it is importable and loads without a network fetch, and otherwise falls back to a deterministic stdlib heuristic (word + punctuation runs). The extension adds no dependency on tiktoken, preserving its zero-outbound posture. Token counts therefore differ between an environment with tiktoken cached and one without; within any single environment they are deterministic, so the tool-vs-CLI byte-identity and the token-header self-consistency both hold.
- **`.nexus/` layout for consumers**: the generator writes `<root>/.nexus/CONTEXT-MAP.md` and `<root>/.nexus/context/*.md` (intended to be committed) alongside the pre-existing `<root>/.nexus/code-index/` graph database (gitignored). Consumer-repo `.gitignore` guidance (commit the map, ignore the index) is documented in the extension README and will be expanded in Phase 5/7.
