# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: The v3.15 minor line carries THREE releases. **v3.15.0 platform-parity-all-gaps** (all 7 phases, RELEASED 2026-07-23): every supported platform receives all the surfaces it can consume, re-verified against current docs. **v3.15.1 adoption-codesight** (all 7 phases built, releasing 2026-07-23): the deterministic compiled context-map inside `nexus-code-search`, both DoD axes holding. **v3.15.2 adoption-awesome-llm-apps** (IN PROGRESS; Phases 1-2 of 6 complete): a deterministic, model-free skill trigger-and-routing quality gate plus an unfilled-placeholder lint. The v3.15.0 version collision (three plans stamped v3.15.0) was reconciled on 2026-07-22 by re-stamping: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight, v3.15.2 = adoption-awesome-llm-apps.
**Last updated**: 2026-07-23 (v3.15.2 Phase 2 - unfilled-placeholder lint)

> **Prior-version ingest (platform-parity)**: v3.14.5's DF-4 (platform additive-surface drift) is the direct input to the v3.15.0 release and was actioned per phase; it does not carry forward as a separate open item. The v3.14.5 Advisory pre-existing failure `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` was re-confirmed and owned by Phase 5.2 (resolved; see the v3.15.0 Advisory below).

> **Prior-version ingest (codesight)**: checked `docs/v3/v3.14/known-gaps.md`. The open v3.14 items (usage-monitor DF/HO series) are unrelated to this feature set and do not carry in. The one relevant caveat is **HO-1** (flat/nested skill-name collision across skill layouts): the codesight plan shipped zero new catalog skills (all work is extension code), so HO-1 does not apply.

> **Scope note (version collision, RESOLVED)**: three plans under `docs/v3/v3.15/plans/` were all stamped `v3.15.0` (`platform-parity-all-gaps`, `adoption-codesight`, and `adoption-awesome-llm-apps`). This was the comparison-versioning artifact (plans stamped with the authoring-cycle version, not the real adoption target). Reconciled on 2026-07-22 by re-stamping: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight, v3.15.2 = adoption-awesome-llm-apps. See the v3.15.1 QG-2 (Resolved) entry.

## v3.15.0 - platform-parity-all-gaps

**Status**: ALL 7 PHASES COMPLETE / RELEASED (2026-07-23). Phase 1 (capability model + read-contract web re-verification), 2 (Cursor parity), 3 (OpenCode parity), 4 (Qwen + Kimi reclassification), 5 (Copilot skill broadening), 6 (installer checklist + runtime verify parity), and 7 (architecture refactor + known-gaps reconciliation + CI/CD) all COMPLETE.

**Phase 1**: `hooks_supported` is now the single load-bearing hook-capability signal - `SkillsIntegration._mirror_catalog` (base) and `Antigravity20Integration._mirror_surface` (bespoke hooks.json writer) both gate hook installation on it; the change is byte-identical for the live registry (every integration declaring `hooks_subdir` also sets `hooks_supported: True`). The dead `permissions_file` config key (declared on 7 subclasses, never read by any code) was removed; the permission JSON files themselves are installed by a separate mechanism and are untouched. The five parity-target platforms (Cursor, OpenCode, Qwen, Kimi, Copilot) were web re-verified against current official docs (2026-07-20); findings + source URLs + MATCH/DRIFT/UNVERIFIED classifications are recorded in `docs/policy/platform-read-contracts.md` (Re-verification log) and the sibling JSON's `parity_verification_v3_15_0` block. Plan: [plans/v3.15.0-platform-parity-all-gaps.md](plans/v3.15.0-platform-parity-all-gaps.md).

**Phase 2 (Cursor parity) COMPLETE.** The Cursor integration surfaces were already implemented in the branch-untangle commit `a56cdffa` (skills flattened to `.cursor/skills`, subagents to `.cursor/agents`, a `version:1` `hooks.json` with `git-guardrails` gated on `hooks_supported`, project `.cursor/commands/`), with a full 8-test `test_cursor.py`. Phase 2 closed the DF-1 verification gate that `a56cdffa` deferred and completed sub-task 2.3: (1) a 2026-07-21 direct re-read of Cursor's official docs RESOLVED DF-1(b) - the `hooks.json` schema is confirmed and the minimal writer is valid as-is (no code change); (2) DF-1(a) global `~/.cursor/commands/` remains UNVERIFIED (no official doc; community feature-request) - the write is retained per plan 2.3 and tracked as the DF-1 residual; (3) `wire_project_surfaces` now also seeds project `.cursor/commands/` so `nexus-hub init` gives a project the slash surface, not just the rules stub. Tests: `test_cursor.py` 9/9.

**Phase 3 (OpenCode parity) COMPLETE.** **3.1 (agents surface)**: added `agents_subdir: "agents"` to `OpenCodeIntegration.config` - a config-only change, since the base `_mirror_catalog` copies `catalog/agents/*.md` verbatim to `~/.config/opencode/agents/` (global) and `.opencode/agents/` (project). A 2026-07-21 direct re-read of `opencode.ai/docs/agents/` confirmed OpenCode reads `.md` + YAML frontmatter there with `mode` OPTIONAL (default `all`). **3.2 (plugins/hooks)**: OUT OF SCOPE, confirmed - plugins are JavaScript/TypeScript modules loaded by Bun, so Nexus-Hub's shell/py hooks do not translate without a JS/TS wrapper; `hooks_supported` stays `False` (DF-4 resolved as a documented non-gap). **3.3 (tests)**: `tests/integrations/test_opencode.py` (6 tests).

**Phase 4 (Qwen + Kimi reclassification) COMPLETE.** **4.1 (Qwen)**: reclassified `QwenIntegration` to `MarkdownIntegration + SkillsIntegration`; it now delivers flattened skills + agents + **Markdown** commands at `~/.qwen/{skills,agents,commands}` (global, detection-gated) and `.qwen/{skills,agents,commands}` (project), preserving `QWEN.md`. Commands are Markdown, NOT TOML (deprecated in Qwen). **DF-2 resolved**: skills delivered to both scopes (global is the reliable path). **4.2 (Kimi)**: reclassified and FULLY MIGRATED to the current Kimi Code CLI product (`~/.kimi-code/`), delivering AGENTS.md + flattened skills (command-skills reach Kimi as `/skill:<name>`) at `~/.kimi-code/` (global, detection-gated) and `.kimi-code/` (project). The old `~/.kimi/` writes and the `.kimi/agent.yaml` companion are DROPPED. **DF-3 resolved**. **4.3 (tests)**: 41 passed; `verify_platform_contracts` now covers 10 platforms.

**Phase 5 (Copilot skill broadening) COMPLETE.** Widened Copilot's opt-in `.github/skills` seeding from a bare on/off toggle to a SELECTOR (`scripts/lib/integrations/copilot.py`). `NEXUS_HUB_COPILOT_SKILLS` now accepts a bundle id (any of the 15 in `data/bundles.json`) or `all` (the full catalog), with bare-truthy still meaning the default `core-developer` bundle and an unknown id falling back to the default. Kept OFF by default and never-overwrite (a Nexus-Hub policy choice, not a Copilot requirement). Fixed the pre-existing `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` advisory by adding `copilot` to the test's `overrides` set. DF-5 resolved.

**Phase 6 (installer checklist + runtime verify parity) COMPLETE - confirmation, no production change.** The v3.14.5 summary-driven checklist and the JSON-driven `[verify]` pass are both generic, so the Cursor/OpenCode/Qwen/Kimi surfaces added in Phases 2-4 already flow through both automatically - no installer or runner edit was needed. Locked in with tests: 4 new `_verify_checks` tests in `tests/installer/test_verify_read_paths.py` and a parametrized newly-parity summary test in `tests/integrations/test_install_summary.py`.

**Phase 7 (architecture refactor + known-gaps reconciliation + CI/CD) COMPLETE.** The v3.15.0 cumulative diff introduced no empty dirs, duplicates, or orphans. The substantive work corrected the now-stale AGENTS.md platform-coverage prose (Cursor -> full-surface parity; OpenCode + Qwen Code + Kimi Code CLI moved into a new "Skills-bearing integrations" bullet; guardrails-only is now just Aider / Windsurf / OpenClaw). All deliverable gaps resolved (DF-2/3/4/5); residuals recorded below. CI already covers the release (new integration + verify tests run in the `tests` job; `verify_platform_contracts` + the freshness gate run in `validate`).

### v3.15.0 Release-readiness residuals (open, non-blocking)

- **DF-1(a)** - Cursor global `~/.cursor/commands/` UNVERIFIED (kept, tracked; the confirmed project `.cursor/commands/` is the load-bearing surface).
- **WN-1** - `test_bootstrap.py` fails in the Windows Git-Bash dev env (environmental `tar`); confirmed to be verified green in CI at `/update release`.
- **DF-5 residual** - Copilot's new native custom-agents (`.github/agents/*.agent.md`) + Preview hooks (`.github/hooks/*.json`) surfaces are not yet populated (future release).
- **OpenCode `rules_subdir`** - the contract records "no rules/ folder" yet the integration writes a `rules_subdir`; a pre-existing note flagged in Phase 3 for a future rules-surface review (not a v3.15.0 change).

### v3.15.0 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 4 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 0 |

### v3.15.0 Advisory (pre-existing test failure) - RESOLVED in Phase 5.2

- `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` - the test's `overrides` set omitted `copilot`, which has overridden `wire_project_surfaces` since v3.11.0 (it returns a skip-note `WriteResult`, not `None`). It was confirmed PRE-EXISTING. **RESOLVED (Phase 5.2, 2026-07-21)**: added `copilot` to the test's `overrides` set (and removed a pre-existing unused `import pytest`). The test now passes (6/6).

### v3.15.0 Open Items

#### Deferred

##### DF-1 - Cursor global commands path UNVERIFIED (residual; hooks.json schema RESOLVED in Phase 2)

- **Source phase**: v3.15.0 Phase 1.2; actioned in Phase 2 (2026-07-21)
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Status**: PARTIALLY RESOLVED. **DF-1(b) hooks.json schema - RESOLVED**: [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms `{version:1, hooks:{<event>:[{...}]}}` with the optional fields defaulted, so the integration's minimal `beforeShellExecution -> {command}` writer is schema-valid as-is (no code change). **DF-1(a) global `~/.cursor/commands/` - RESIDUAL (still UNVERIFIED)**: project `.cursor/commands/<name>.md` is officially documented (Cursor 1.6+) and confirmed, but the user-global `~/.cursor/commands/` dir has no reachable official doc and [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request.
- **Decision**: the global write is RETAINED per plan sub-task 2.3 and the contract's negative-only-evidence caution; it is harmless if unread.
- **Suggested next step**: a future cycle with a reachable Cursor commands doc (or an empirical test) should confirm or drop the global `~/.cursor/commands/` write. Not blocking - the confirmed project `.cursor/commands/` surface is the load-bearing path.

##### DF-2 - Qwen skills auto-load reliability (open issue #2343) - RESOLVED (mitigated in Phase 4)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 4 (2026-07-21)
- **Status**: RESOLVED (mitigated). A live smoke test on a current Qwen build was not possible, so the mitigation the gap suggested was taken: skills are delivered to BOTH the global `~/.qwen/skills/` (the reliable path) and the project `.qwen/skills/`. The #2343 project-auto-load issue is an open upstream GitHub issue, not documented behavior; the global path covers it.
- **Residual**: none blocking.

##### DF-3 - Kimi current product is `~/.kimi-code/`, not the baseline's deprecated `~/.kimi/` - RESOLVED (Phase 4)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 4 (2026-07-21)
- **Status**: RESOLVED. A 2026-07-21 re-read of kimi.com/code/docs confirmed the current product is Kimi Code CLI (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`), separate from the older "Kimi CLI" (`~/.kimi/`).
- **Decision (maintainer)**: FULL migration to `~/.kimi-code/`. The integration writes AGENTS.md + native `~/.kimi-code/skills` at both scopes (global detection-gated on `~/.kimi-code`); the old `~/.kimi/` writes and the `.kimi/agent.yaml` companion are DROPPED.
- **Residual**: a user still on the OLD "Kimi CLI" (`~/.kimi/`) no longer receives a surface (accepted trade-off); pre-existing `~/.kimi/` files are left in place. Not blocking.

##### DF-4 - OpenCode plugins/hooks out of scope (RESOLVED as a documented non-gap in Phase 3.2)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 3.2 (2026-07-21)
- **Status**: RESOLVED (decision: out of scope). A 2026-07-21 re-read of [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins) confirmed plugins are JavaScript/TypeScript modules loaded by Bun; a `.sh`/`.py` script cannot be dropped into `plugins/` and run, so Nexus-Hub's shell/py hooks cannot be delivered without a JS/TS wrapper per hook.
- **Decision**: OpenCode hooks are OUT OF SCOPE. `hooks_supported` stays `False`.
- **Suggested next step**: none required. Revisit only if a maintainer wants OpenCode hook parity badly enough to own a JS/TS plugin wrapper.

##### DF-5 - Copilot skill broadening + stale opt-in framing - RESOLVED (Phase 5)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 5 (2026-07-21)
- **Status**: RESOLVED. Phase 5 widened `.github/skills` seeding from a bare toggle to a SELECTOR (bundle id or `all`; bare-truthy = default `core-developer`), keeping OFF-by-default + never-overwrite as the commit-visibility policy, and corrected the framing in `copilot.py`'s docstring to state the opt-in is a Nexus-Hub policy, not a Copilot requirement.
- **Residual (out of scope, not blocking)**: Copilot's custom agents (`.github/agents/*.agent.md`) and Preview hooks (`.github/hooks/*.json`) are new native surfaces Nexus-Hub does not yet populate. A candidate for a future release.

#### Warnings

##### WN-1 - `test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails in the Windows Git-Bash dev env (pre-existing, environmental)

- **Source phase**: surfaced during v3.15.0 Phase 6's `tests/installer` run (pre-existing, NOT caused by any v3.15.0 phase)
- **Reason**: the standalone-bootstrap test drives `install.ps1`, which shells out to extract the downloaded `main` tarball; on this Windows Git-Bash host `/usr/bin/tar` fails with `unexpected end of file` (a local `tar`-binary quirk, not a code defect). `tests/installer` is otherwise 120 passed / 15 skipped.
- **Suggested next step**: confirm the bootstrap test passes in CI (Linux/macOS `tar`), where this environmental quirk does not apply. Not a release blocker on its own (the core installers `scripts/installer.{sh,ps1}` are unaffected).

#### Quality-gate gaps

##### QG-1 - `make validate` compression-accuracy eval not run in Phase 1 (unrelated to Phase 1 scope)

- **Source phase**: v3.15.0 Phase 1.4
- **Reason**: `make` is unavailable in the dev environment, so the `make validate` steps were run individually. The context-compressor accuracy-regression eval was not run in Phase 1 because Phase 1 does not touch `extensions/nexus-context-compressor`. Every other `make validate` step passed.
- **Suggested next step**: the eval runs in CI and at `/update release`; no action needed unless a later phase touches the compressor.

## v3.15.1 - adoption-codesight

**Status**: ALL 7 PHASES BUILT on `feat/adoption-codesight`. Extension-only, no catalog registry / installer / `base-*.md` changes. Phase 1: a deterministic `.nexus/CONTEXT-MAP.md` + `.nexus/context/` article set compiled from the existing tree-sitter graph, exposed as the `generate_context_map` MCP tool and a `nexus-hub map` one-shot CLI (neutral-path, byte-identical tool/CLI, content-hash no-op). Phase 2: framework-aware route extraction, an env-var audit, and middleware detection/categorization. Phase 3: ORM schema extraction (SQLAlchemy / Django / Prisma), React component extraction, and background-event detection, feeding Data Models / Components / Events sections. Phases 4-6 added hot-file ranking + a git-scoped change map, the token-savings benchmark + map-health lint, and the knowledge-map extractor. Phase 7 completed the terminal refactor, known-gaps reconciliation, reverse-engineering-matrix update, and CI/CD (context-map Action recipe). **Both DoD axes hold** (measured token-reduction + verified extractor accuracy). `GENERATOR_VERSION` reached 4. Full extension suite green (294 passed, 1 pre-existing skip).

### v3.15.1 Open Items

#### Deferred

##### DF-3 - Additional frameworks / ORMs / component libs / event patterns deferred (explicit coverage, not silent)

- **Source phase**: v3.15.1 adoption-codesight Phase 2 (2.1) + Phase 3 (3.1, 3.2)
- **Plan reference**: Phase 2.1 / Phase 3.1 / Phase 3.2 ("verifying each with a fixture before adding the next ... Do NOT attempt every framework at once")
- **Reason**: per the plan's incremental posture, each detector lands with its own fixture rather than all at once. Currently covered:
    - **Routes**: FastAPI, Flask, Django, Express (via the existing resolvers). Deferred: Hono / Fastify / Next / NestJS (TS), Gin (Go), Rails (Ruby), Spring Boot (Java), Laravel (PHP) - each needs a new extraction-time resolver + fixture.
    - **ORM schema**: SQLAlchemy, Django ORM, Prisma. Deferred: TypeORM, Drizzle (TS), ActiveRecord (Ruby), GORM (Go) - decorator/call-based, each needs its own detector + fixture.
    - **Components**: React (props via destructuring or the resolved prop type). Deferred: Vue, Svelte. Design-system-primitive auto-filtering is also deferred.
    - **Events**: declaration-strong signals (Celery task decorators, BullMQ `new Queue/Worker`, Kafka, `new EventEmitter`). Deferred: invocation-only patterns (`.delay(`, `.emit(`, Redis `.publish(`/`.subscribe(`) - too common to detect without false positives.
- **Suggested next step**: add a detector + fixture per additional target in a follow-on pass. The map's section renderers and the accuracy harness already handle any new detector's output generically.

#### Warnings

##### WN-1 - Pre-existing unused `json` import in scripts/nexus_hub_cli.py

- **Source phase**: v3.15.1 adoption-codesight Phase 1 (1.2)
- **Reason**: ruff flags `F401 json imported but unused` in `scripts/nexus_hub_cli.py`. The import is PRE-EXISTING (present on `develop`), not introduced by this phase, and `scripts/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove the unused import as part of a dedicated `scripts/` lint pass.

##### WN-2 - Pre-existing ruff findings in graph/affected.py

- **Source phase**: v3.15.1 adoption-codesight Phase 4 (4.1)
- **Reason**: ruff flags an unused `EdgeKind` import (F401) and an unused `frontier` local (F841) in `graph/affected.py`. Both are PRE-EXISTING; Phase 4 only ADDED `most_imported_files` (ruff-clean). The extension `src/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove both in a dedicated extension lint pass.

#### Missing tests / coverage gaps

##### MT-2 - Benchmark `--update-baseline` write path not automated-tested

- **Source phase**: v3.15.1 adoption-codesight Phase 5 (5.1)
- **Reason**: `measured_baseline()` is unit-tested, but the `benchmark --update-baseline` CLI branch that OVERWRITES the committed `benchmark_baseline.json` is deliberately not exercised (a test that ran it would clobber the committed baseline). The gate path (`--check`), JSON/report output, and `--repo` mode are all tested.
- **Suggested next step**: if desired, test `--update-baseline` against a monkeypatched `BASELINE_PATH` pointing at a temp file. Low value.

##### MT-1 - Repo-level `nexus-hub map` dispatch has no automated test

- **Source phase**: v3.15.1 adoption-codesight Phase 1 (1.2)
- **Reason**: the extension test suite fully covers the map surface (generator, model, tokens, the `generate_context_map` MCP handler, and `nexus_code_search.contextmap.cli`; tool-vs-CLI byte-identity is asserted). The thin dispatch in `scripts/nexus_hub_cli.py` (a 3-line verbatim forward) is verified only by a manual smoke run, not an automated repo-level test.
- **Suggested next step**: add a small repo-level dispatch test asserting `nexus_hub_cli.main(["map", ...])` forwards and returns the extension CLI's exit code.

### v3.15.1 Resolved

##### DF-1 - Overview frameworks line + Most-Imported Files section (RESOLVED)

- Originally Phase 1's placeholder for the Overview `Frameworks:` line and the "Most-Imported Files" section. The frameworks half was resolved in Phase 2; the Most-Imported Files half was resolved in Phase 4 (`most_imported_files` fills the section from inbound import edges, labeled distinct from symbol-level `code_impact`). Both halves shipped and are fixture-tested.

##### DF-2 - nexus-code-search extension package version bump (RESOLVED, Phase 7)

- The extension carries its own package version, independent of the catalog release version. Phase 7 bumped `extensions/nexus-code-search/pyproject.toml` `2.0.0 -> 2.1.0` and refreshed the description to cover the context-map surface. This is NOT a `check_version_sync.py` surface (that guard covers the catalog release version, which `/update release` owns; the QG-2 release hold has since been reconciled by the v3.15.0/v3.15.1/v3.15.2 re-stamp).

##### QG-1 - Duplicate extension-test run across ci.yml and code-search.yml (RESOLVED by decision, Phase 7)

- Decision: RETAIN both. `code-search.yml` (path-filtered, cached, concurrency) is the fast scoped signal on extension changes; the always-on `tests` job in `ci.yml` is the cross-cutting safety gate. The small duplicate on extension-only changes is an intentional coverage-over-minutes trade-off. The benchmark + lint + knowledge tests run in that suite on every extension change; the context-map GitHub Action recipe is documented in the extension README.

##### QG-2 - Three plans stamped v3.15.0 (release-time version reconciliation) (RESOLVED, 2026-07-22)

- Three plans under `docs/v3/v3.15/plans/` were all stamped `v3.15.0` (`platform-parity-all-gaps`, `adoption-codesight`, `adoption-awesome-llm-apps`): the comparison-versioning artifact where plans carry the authoring-cycle version, not the real adoption target. Reconciled by re-stamping the deferred plans: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight (this plan), v3.15.2 = adoption-awesome-llm-apps (and in the v3.16 line, v3.16.0 = model-prompting-research, v3.16.1 = rtk-and-meterless).

### v3.15.1 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 2 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 0 | 2 |
| Hand-offs (HO) | 0 | 0 |

RESOLVED: DF-1 (frameworks line P2 + Most-Imported Files P4), DF-2 (extension version bump P7), QG-1 (CI duplicate-run decision P7), QG-2 (v3.15.0 version collision reconciled by re-stamping, 2026-07-22). OPEN and carried as documented, non-blocking deferrals: DF-3 (deferred detectors - explicit future coverage), WN-1 / WN-2 (pre-existing ruff findings in `scripts/nexus_hub_cli.py` and `graph/affected.py`, in files this plan edited but not introduced by it; a future dedicated lint pass), MT-1 (repo-level `nexus-hub map` dispatch not auto-tested), MT-2 (benchmark `--update-baseline` write path untested).

### v3.15.1 Advisory

- **Definition-of-done measured half VALIDATED (Phase 5)**: the token-savings benchmark measures the compiled map vs a simulated manual-exploration cost. On the committed sample corpus (3 realistic repos) the map saves ~44-55% of exploration tokens (regression-guarded by `benchmark_baseline.json`); on Nexus-Hub itself a ~22k-token map replaces ~1.9M tokens (~99% reduction, 443 files). Combined with the Phase 2-3 zero-FP + recall accuracy harness, both DoD axes hold. The tiny per-framework `contextmap` fixtures are NOT a benchmark corpus - a map is not worth its fixed overhead on a 2-file repo; savings scale with codebase size.
- **Map-health lint ships as extension code, not a new catalog skill (Phase 5.2 decision)**: the deterministic checks (orphan articles, missing backlinks, staleness) live in `contextmap/maphealth.py` (exposed as the `map_health` MCP tool + `nexus-hub map --lint`); the richer semantic checks stay in the LLM-native `documentation-consistency` skill. No `data/` registry files were touched.
- **Knowledge-map extractor ships as extension code, not a new catalog skill (Phase 6.1 decision)**: the mechanical classification + decision / open-question extraction lives in `contextmap/knowledge.py` (exposed as the `generate_knowledge_map` MCP tool + `nexus-hub map --knowledge`); narrative synthesis stays with the LLM-native `solution-knowledge-base` skill. Phases 1-6 remained entirely extension-only.
- **tiktoken is optional, not a dependency**: the token-count header prefers `tiktoken` (cl100k_base) when it is importable and loads without a network fetch, and otherwise falls back to a deterministic stdlib heuristic. The extension adds no dependency on tiktoken, preserving its zero-outbound posture. Token counts differ between an environment with tiktoken cached and one without; within any single environment they are deterministic, so the tool-vs-CLI byte-identity and the token-header self-consistency both hold.
- **`.nexus/` layout for consumers**: the generator writes `<root>/.nexus/CONTEXT-MAP.md` and `<root>/.nexus/context/*.md` (intended to be committed) alongside the pre-existing `<root>/.nexus/code-index/` graph database (gitignored). Consumer-repo `.gitignore` guidance (commit the map, ignore the index) is documented in the extension README.

## v3.15.2 - adoption-awesome-llm-apps

**Status**: IN PROGRESS. Phases 1-2 COMPLETE; Phases 3-6 pending. This section is appended per-phase and finalized at the v3.15.2 release (Phase 6). Plan: [plans/v3.15.2-adoption-awesome-llm-apps.md](plans/v3.15.2-adoption-awesome-llm-apps.md).

**Phase 1 (catalog-wide trigger-and-routing eval, A1) COMPLETE.** Shipped `scripts/run_trigger_evals.py` (Python stdlib only, model-free): it tokenizes every skill `description`, stems light inflections (ing/es/ed/s), and flags any pair whose trigger vocabulary overlaps at or above a configurable threshold (default 0.5, containment metric `|A n B| / min(|A|, |B|)`). First-run triage over all 267 skills surfaced 39 near-collisions. 38 are by-design category siblings (parallel `<lang>-cleanup` / `<lang>-expert` / `init-<lang>-project` / framework-expert / `*-generation` / mobile-platform / compliance-regulation pairs, plus two matched pairs that already carry mutual SKIP clauses) recorded in `scripts/run_trigger_evals.allowlist.json`; the one genuine collision (the broad `technical-documentation` skill lacked a SKIP clause carving out the single-artifact `architecture-decision-record` and `project-constitution` skills) was FIXED by sharpening `technical-documentation`'s description (and its `data/skills.json` mirror). Registered warning-first in `installer.sh`, `installer.ps1`, the `Makefile` (`make trigger-evals` plus a `make validate` step), and `.github/workflows/ci.yml`. Tests: `tests/validators/test_run_trigger_evals.py` (25 tests, 96% line coverage). Promotion from warning-only to a hard `--gate` is deferred to Phase 6 per the plan.

**Phase 2 (unfilled-placeholder lint, A3) COMPLETE.** Extended `scripts/validate_skills.py` with `validate_placeholders`: it flags unfilled multi-word angle-bracket template placeholders (two or more single-space-separated lowercase words, e.g. `<what this skill does>`) as a HARD ERROR in both the `description` frontmatter field and the SKILL.md body prose. Single-word CLI notation (`<path>`), uppercase template tokens (`<MAJOR>`), and HTML tags are excluded by the tight regex shape, and fenced code blocks + inline-code spans are skipped (CommonMark-aware fence tracking mirrored from the secret scanner). The check runs inside the `--bundles-only` mode that `make validate` and CI already invoke, so NO new CI job was added. First run over all 267 skills produced ZERO findings (no genuine scaffolds, no false positives), so no SKILL.md fix was needed. Tests: 14 cases added to `tests/validators/test_validate_skills.py` (description hit, body hit, CLI-notation / HTML / uppercase-token / comparison-operator negatives, fenced + inline-code + backticked-description exemptions, nested-fence guard, `_body_after_frontmatter`, and two `--bundles-only` CLI tests) - new-code line coverage 100% in-process. AGENTS.md documents the new lint alongside the orphan-bundle detection block.

### v3.15.2 Open Items

#### Deferred

##### DF-1 - CI per-path-filter granularity for the trigger-eval step not implemented

- **Source phase**: v3.15.2 Phase 1.5.
- **Plan reference**: Phase 1.5 ("path filters so it only runs on `catalog/skills/**` and `scripts/run_trigger_evals*` changes").
- **Reason**: the repo runs all validators in a single `validate` job triggered by the workflow-level `paths-ignore: docs/**`. The eval is a sub-second stdlib step; splitting it into a separately-path-filtered job would ADD checkout + setup minutes, defeating the stated optimization goal. It was kept as a step in the existing optimized job (which already has `concurrency` cancel-in-progress, pip caching, and cost-gated macOS/Windows matrix legs).
- **Suggested next step**: revisit only if the `validate` job's runtime grows materially; otherwise close as a non-gap in the Phase 6 CI review.

#### Warnings

##### WN-1 - Windows-local dry-run install of the new copy block not executed

- **Source phase**: v3.15.2 Phase 1.4.
- **Plan reference**: Phase 1.4 ("do a dry-run install into a throwaway directory and confirm the script lands at `~/.nexus-hub/scripts/`").
- **Reason**: the bash installer cannot fully run on the Windows dev host (WN-v36-1). The new copy block mirrors the `generate_report.py` pattern exactly, is shellcheck-clean, and targets `$scripts_dest` (which resolves to `~/.nexus-hub/scripts`).
- **Suggested next step**: none required - CI's `bootstrap` and `install-smoke` jobs exercise the installer end-to-end on ubuntu / macOS / Windows.

### v3.15.2 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

> **Forward pointer (Phase 3 coverage gap)**: the per-skill `trigger-cases.json` routing-assertion coverage gap (skills left on the WARN path) is a Phase 3 deliverable and will be tracked here when Phase 3 lands, per the plan's Phase 6.2 instruction.
