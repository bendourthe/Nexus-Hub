# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: The v3.15 minor line carries THREE releases. **v3.15.0 platform-parity-all-gaps** (all 7 phases, RELEASED 2026-07-23): every supported platform receives all the surfaces it can consume, re-verified against current docs. **v3.15.1 adoption-codesight** (all 7 phases built, releasing 2026-07-23): the deterministic compiled context-map inside `nexus-code-search`, both DoD axes holding. **v3.15.2 adoption-awesome-llm-apps** (ALL 6 PHASES COMPLETE; RELEASE HELD): a deterministic, model-free skill trigger-and-routing quality gate (now a hard `--gate`), an unfilled-placeholder lint, per-skill routing assertions, behavioral-eval schema interop, and a Hermes platform-roster integration. Implementation is done and verified on `feat/adoption-awesome-llm-apps`; the `/update release` hand-off is HELD (see the v3.15.2 Release hold section). The v3.15.0 version collision (three plans stamped v3.15.0) was reconciled on 2026-07-22 by re-stamping: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight, v3.15.2 = adoption-awesome-llm-apps. A fourth release, **v3.15.3 adoption-no-ai-slop** (ALL 3 PHASES COMPLETE / RELEASED 2026-07-24), adds a dedicated prose `anti-slop-editing` skill. A fifth cycle, **v3.15.4 presentify-visual-fidelity** (IN PROGRESS; Phases 1-6 of 7 COMPLETE), makes presentify's output visually faithful and self-correcting: a full-width canvas contract, image-sizing discipline, annotated-figure overlay recreation, reliable stock/mix imagery integration, an iterative multi-agent visual-QA self-critique loop, and command/skill polish (the `--qa-depth` knob).
**Last updated**: 2026-07-24 (v3.15.4 Phase 6 COMPLETE - command, skill, and registry polish)

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

**Status**: IN PROGRESS. Phases 1-5 COMPLETE; Phase 6 pending. This section is appended per-phase and finalized at the v3.15.2 release (Phase 6). Plan: [plans/v3.15.2-adoption-awesome-llm-apps.md](plans/v3.15.2-adoption-awesome-llm-apps.md).

**Phase 1 (catalog-wide trigger-and-routing eval, A1) COMPLETE.** Shipped `scripts/run_trigger_evals.py` (Python stdlib only, model-free): it tokenizes every skill `description`, stems light inflections (ing/es/ed/s), and flags any pair whose trigger vocabulary overlaps at or above a configurable threshold (default 0.5, containment metric `|A n B| / min(|A|, |B|)`). First-run triage over all 267 skills surfaced 39 near-collisions. 38 are by-design category siblings (parallel `<lang>-cleanup` / `<lang>-expert` / `init-<lang>-project` / framework-expert / `*-generation` / mobile-platform / compliance-regulation pairs, plus two matched pairs that already carry mutual SKIP clauses) recorded in `scripts/run_trigger_evals.allowlist.json`; the one genuine collision (the broad `technical-documentation` skill lacked a SKIP clause carving out the single-artifact `architecture-decision-record` and `project-constitution` skills) was FIXED by sharpening `technical-documentation`'s description (and its `data/skills.json` mirror). Registered warning-first in `installer.sh`, `installer.ps1`, the `Makefile` (`make trigger-evals` plus a `make validate` step), and `.github/workflows/ci.yml`. Tests: `tests/validators/test_run_trigger_evals.py` (25 tests, 96% line coverage). Promotion from warning-only to a hard `--gate` is deferred to Phase 6 per the plan.

**Phase 2 (unfilled-placeholder lint, A3) COMPLETE.** Extended `scripts/validate_skills.py` with `validate_placeholders`: it flags unfilled multi-word angle-bracket template placeholders (two or more single-space-separated lowercase words, e.g. `<what this skill does>`) as a HARD ERROR in both the `description` frontmatter field and the SKILL.md body prose. Single-word CLI notation (`<path>`), uppercase template tokens (`<MAJOR>`), and HTML tags are excluded by the tight regex shape, and fenced code blocks + inline-code spans are skipped (CommonMark-aware fence tracking mirrored from the secret scanner). The check runs inside the `--bundles-only` mode that `make validate` and CI already invoke, so NO new CI job was added. First run over all 267 skills produced ZERO findings (no genuine scaffolds, no false positives), so no SKILL.md fix was needed. Tests: 14 cases added to `tests/validators/test_validate_skills.py` (description hit, body hit, CLI-notation / HTML / uppercase-token / comparison-operator negatives, fenced + inline-code + backticked-description exemptions, nested-fence guard, `_body_after_frontmatter`, and two `--bundles-only` CLI tests) - new-code line coverage 100% in-process. AGENTS.md documents the new lint alongside the orphan-bundle detection block.

**Phase 3 (per-skill trigger-cases + routing assertions, A2) COMPLETE.** Extended `scripts/run_trigger_evals.py` to consume optional `catalog/skills/<cat>/<name>/evals/trigger-cases.json` files and assert lexical routing: (a) each `should_trigger: true` prompt must rank its own skill first among all skills (else it names the mis-routed-to skill), and (b) within a skill's cases the weakest positive must clear the strongest near-miss negative by a configurable `--margin` (default 1.15x). `lexical: false` cases are skipped (left for behavioral evals); skills without a file emit a WARN (never a FAIL), so the catalog never blocks on incomplete coverage. The schema and `evals/` convention are documented in AGENTS.md; the orphan-bundle audit is reconciled (a code comment on `BUNDLED_SUBDIRS` records that `evals/` is intentionally excluded because it is runner-consumed, not SKILL.md-referenced). First tranche authored for 6 distinctive-noun skills (react-expert, vue-expert, gdpr-compliance, ccpa-compliance, kubernetes-expert, docx-generation), chosen from the Phase 1 near-collision pairs plus a high-value standalone; all 36 lexical cases pass (0 routing failures). One vue near-miss was retuned to lean on react-distinctive vocabulary after the margin check correctly flagged that generic component/state words did not separate vue from react - the eval working as intended. Tests: routing cases added to `tests/validators/test_run_trigger_evals.py` (rank-first pass, misroute, margin-fail, lexical-false skip, malformed file, no-cases WARN, JSON routing block, real-catalog tranche) - runner line coverage 95%. No CI edit needed (the extended eval is the same warning-only step; new tests run via the existing `pytest tests/validators` step).

**Phase 4 (behavioral-eval schema interop, A4) COMPLETE.** Decision: ship an ADAPTER, not a native re-alignment. The eval-loop's internal `evals.json` is a strict superset of the interoperable behavioral-eval schema `{skill_name, evals:[{id, prompt, expected_output, expectations[]}]}` - it carries `should_trigger` (trigger-rate metric), `turns`/`trigger_turn` (multi-turn), `model` (cheap-model fragility), and `tags`, none of which the interoperable schema can express - so adopting it natively would drop capabilities and force a rewrite of the grader/aggregator/optimizer/viewer. Instead shipped `scripts/skill_eval_convert.py`, a stdlib-only bidirectional converter (`--to-interop` / `--to-internal`) that maps `query`<->`prompt` and `assertions[].text`<->`expectations[]`, preserving `expected_output` verbatim and stashing every internal-only field under an `x_nexus` extension key so BOTH round-trips are lossless (`internal->interop->internal == internal`, `interop->internal->interop == interop`). Behavior preserved by construction: the grading path (internal format + grader/aggregator/optimizer/viewer) is unchanged; there was no committed sample `evals.json` to migrate. Registered in both installers (sibling of the other eval-loop scripts); documented in `references/schemas.md` (interop section + decision rationale) and referenced from the skill's SKILL.md. Tests: `tests/validators/test_skill_eval_convert.py` (18 cases: field mapping, both lossless round-trips, extension-namespace behavior, error handling, and CLI + in-process main surfaces) - converter line coverage 96%.

**Phase 5 (Hermes roster + shared `.agents/skills/`, A5) COMPLETE.** Added `scripts/lib/integrations/hermes.py` as a `SkillsIntegration` (skills-native: reads folder-per-skill `SKILL.md` directly, so NO instruction file and NO `base-hermes.md` - a `SkillsIntegration`, not a `MarkdownIntegration`), registered in `_register_builtins()`. It writes flattened skills to `~/.hermes/skills/` (global, detection-gated on `~/.hermes`) and `.hermes/skills/` (project), each catalog command also surfacing as a skill. Per the shared-path ownership rule Kimi follows, Hermes READS but does not WRITE the shared `~/.agents/skills/` (owned by `codex`) or the project `.agents/skills/` (seeded by `antigravity2`'s `wire_project_surfaces` on `nexus-hub init`), avoiding a teardown conflict. The shared-project `.agents/skills/` path is therefore CONFIRMED present (`cmd_init` walks every integration's `wire_project_surfaces`, and `antigravity2` seeds `.agents/skills/`), not newly added. Documented in `docs/policy/platform-read-contracts.md` (surface-table rows + a Hermes section) and the AGENTS.md platform-coverage section. Tests: `tests/integrations/test_hermes.py` (6 cases) + the parameterized `test_contract.py` (hermes: 4 passed, 1 skipped) + a runner dry-run confirming `.hermes/skills/` and zero disk writes. No `base-*.md`, catalog-registry, or hook change; `verify_platform_contracts` stays green (Hermes intentionally not in `contract_checks`, see DF-2).

**Phase 6 (architecture refactor + known-gaps reconciliation + CI/CD) COMPLETE (release HELD).** **6.1 refactor**: audited this plan's cumulative diff (2584 insertions across 33 files) - all additions are cohesive and correctly placed (repo scripts under `scripts/` referenced in both installers + Makefile + CI; the `hermes` integration under `scripts/lib/integrations/` registered in `_register_builtins()`; per-skill `evals/trigger-cases.json` consumed by the runner; tests under `tests/validators` + `tests/integrations`). No empty dirs, duplicates, orphans, or overcomplicated structure - a no-op cleanup. Docs-tree refactoring (`docs-layout-refactor`) was DEFERRED because a parallel task is actively re-stamping `docs/v3/v3.16` -> `docs/v3/v3.15` plans/comparisons; running it now would collide (see the release hold below). **6.2 known-gaps**: this reconciliation (DF-1 resolved by the CI-review decision; DF-2 / WN-1 / MT-1 carried as documented non-blocking deferrals; MT-1 - the trigger-cases WARN-path coverage - is the explicit item the next release picks up). **6.3 CI/CD**: promoted the trigger-and-routing eval from warning-only to a HARD `--gate` in both `.github/workflows/ci.yml` and the Makefile `validate` step (catalog is clean: 0 un-allowlisted collisions, 0 routing failures); confirmed CI covers every plan change (A1/A2 via the `--gate` step, A3 inside `validate_skills.py --bundles-only`, A4 via `pytest tests/validators`, A5 via `pytest tests/integrations`) with no new/redundant job and the existing concurrency + caching + gated-matrix optimizations intact. **6.4 verification**: validators + `tests/validators` (302) + `tests/integrations` (398) green; `--gate` passes; dry-run install lands `.hermes/skills/`. RELEASE HELD - the release-readiness sub-phases (9A/9B) ran, but 9C-9E (`/update release`: version bump / changelog / develop->main merge / tag / GitHub Release) is NOT run pending the active-parallel-re-stamp reconciliation, the unpushed branch, and the in-flux v3.15.x version numbering (see the release-hold note below).

### v3.15.2 Open Items

#### Deferred

##### DF-2 - Hermes not yet first-class installer-wired (registry-only)

- **Source phase**: v3.15.2 Phase 5.1 / 5.2.
- **Plan reference**: Phase 5.1 ("no installer copy-step edit is needed because the runner is invoked automatically").
- **Reason**: `hermes` is registered in `_register_builtins()` and installable on demand via `runner.py install --integrations hermes` (detection-gated), but the installers drive extended platforms through explicit `should_install <key>` / `invoke_registry_platform` blocks + a `known_platform_keys` list, and Hermes is intentionally NOT added to those yet (nor to the JSON `contract_checks`, which would then REQUIRE the installer reference and fail `verify_platform_contracts`). Editing the installers is an AGENTS.md "ask first" action and outside this phase's stated scope. Hermes therefore sits in the same tier as aider/windsurf/openclaw: registered + documented + runner-installable.
- **Suggested next step**: if Hermes adoption warrants it, promote it to a default-installed platform in a follow-on - add `should_install hermes` / `invoke_registry_platform` blocks to both installers, add `hermes` to `known_platform_keys`, and add a `contract_checks` entry (with the required installer reference).

#### Warnings

##### WN-1 - Windows-local dry-run install of the new copy block not executed

- **Source phase**: v3.15.2 Phase 1.4.
- **Plan reference**: Phase 1.4 ("do a dry-run install into a throwaway directory and confirm the script lands at `~/.nexus-hub/scripts/`").
- **Reason**: the bash installer cannot fully run on the Windows dev host (WN-v36-1). The new copy block mirrors the `generate_report.py` pattern exactly, is shellcheck-clean, and targets `$scripts_dest` (which resolves to `~/.nexus-hub/scripts`).
- **Suggested next step**: none required - CI's `bootstrap` and `install-smoke` jobs exercise the installer end-to-end on ubuntu / macOS / Windows.

#### Missing tests / coverage gaps

##### MT-1 - trigger-cases.json routing coverage is a first tranche (6/267 skills)

- **Source phase**: v3.15.2 Phase 3.3.
- **Plan reference**: Phase 3.3 ("leave the rest of the catalog on the WARN path for incremental authoring in later releases") and Phase 6.2 ("Explicitly record the deferred incremental work ... skills still on the WARN path").
- **Reason**: routing cases were authored for 6 distinctive-noun skills; the remaining 261 skills have no `evals/trigger-cases.json` and are on the WARN path (never fails the gate). This is by design - lexical routing cases are only meaningful for skills with distinctive description vocabulary, and command-dispatcher skills (`/plan`, `/implement`, `/review`, `/compare`, `/update`) lexically overlap their sub-skills, so they need `lexical: false` reasoning-routed cases (deferred).
- **Suggested next step**: author further tranches incrementally in later releases; for the command dispatchers, add `lexical: false` cases covered by behavioral evals (ties into Phase 4 schema interop).

### v3.15.2 Resolved

##### DF-1 - CI per-path-filter granularity for the trigger-eval step - RESOLVED (Phase 6.3 CI review, by decision)

- **Source phase**: v3.15.2 Phase 1.5; closed in Phase 6.3.
- **Resolution**: the Phase 6.3 CI review confirmed the design decision - the eval is a sub-second stdlib step that rides the existing single `validate` job (which already has `concurrency` cancel-in-progress, pip caching, and cost-gated macOS/Windows matrix legs). Splitting it into a separately-path-filtered job would ADD checkout + setup minutes, defeating the stated optimization goal, so no per-path-filter granularity is added. Closed as a non-gap by decision (mirrors the v3.15.1 QG-1 CI-dedup resolution pattern).

### v3.15.2 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

RESOLVED: DF-1 (CI per-path-filter granularity, closed by the Phase 6.3 CI-review decision). OPEN and carried as documented, non-blocking deferrals: DF-2 (Hermes registry-only, not yet default-installer-wired), WN-1 (Windows-local dry-run not run; CI is authoritative), MT-1 (trigger-cases WARN-path coverage - the explicit item the next release picks up).

### v3.15.2 Release hold (Phase 6, release-readiness 9C-9E)

The final phase's `/update release` hand-off (version bump / changelog / develop->main merge / tag / push / GitHub Release) is HELD. Active hold conditions at Phase 6 completion:

1. **Active parallel re-stamp in the working tree** - a concurrent task is renumbering `docs/v3/v3.16/{plans,comparisons}/*` into the `docs/v3/v3.15/` line (v3.15.3 / v3.15.4 / v3.15.5 / v3.15.6 plans + comparisons appearing, v3.16.x files deleted/renamed). These are uncommitted and NOT part of this plan; the Phase 1-6 commits deliberately excluded them via surgical staging. A release must not run over a half-reorganized docs tree.
2. **In-flux version numbering** - with v3.15.3-.6 being created from former v3.16.x plans, whether v3.15.2 is still the correct release stamp for this plan needs user confirmation (the comparison-versioning-flaw pattern).
3. **Unpushed branch** - `feat/adoption-awesome-llm-apps` (Phases 1-6) is local-only; nothing is pushed.

Resolution path (user-owned): reconcile the parallel re-stamp, confirm the version stamp, push the branch, then run `/update release` for whichever version this plan ships as (it re-verifies the platform contract, bumps every version surface via `check_version_sync`, finalizes the changelog, merges develop->main, tags, and publishes the GitHub Release under its own gates).

## v3.15.3 - adoption-no-ai-slop

**Status**: ALL 3 PHASES COMPLETE / RELEASED (2026-07-24). This section is finalized. Plan: [plans/v3.15.3-adoption-no-ai-slop.md](plans/v3.15.3-adoption-no-ai-slop.md).

**Phase 1 (author the anti-slop-editing skill and bundle) COMPLETE.** Authored a new `catalog/skills/developer-experience/anti-slop-editing/` bundle: `SKILL.md` (dual Edit/Detect mode, a 17-entry named-slop-pattern catalog each with a quoted smell + a concrete before/after fix, voice-preservation discipline, a wired self-check loop, Common Rationalizations, and a binary Verification section), `references/slop-wordlist.md` (banned words + often-empty adverbs + empty phrases, framed as judgment guidance not a hard lint), `references/self-check.md` (a pass/fail content-quality rubric the skill grades its own output against before returning), and `evals/trigger-cases.json` (4 positives + 4 near-miss negatives drawn from the SKIP clause). The single-line `description` was lexically co-engineered with the eval prompts so the routing gate ranks `anti-slop-editing` first on every positive and clears the 1.15x near-miss margin, and so it collides with no sibling description. Per the reverse-engineering attribution rule, no external repository, product, author, or course is named anywhere in the shipped bundle. Gates green: full `validate_skills.py` on the skill PASS (0 errors, 0 warnings); whole-tree `--bundles-only` PASS (this skill clean; see the Advisory below for the one pre-existing warning); `run_trigger_evals.py --gate` PASS (0 un-allowlisted collisions, 0 routing failures across 7 skills with cases). CI already covers the skill's validation with no edit (the new bundle flows through the existing `--bundles-only` + `--gate` + skill-security steps under the optimized `validate` job). Registration in the three `data/` files, the reverse-engineering-matrix row, and the CHANGELOG entry are Phase 2 work.

**Phase 2 (register and record provenance) COMPLETE.** Registered `anti-slop-editing` by hand in the three registry files (no full catalog rebuild): a row in `data/SKILL_INDEX.md`, a full entry in `data/skills.json` (matching the sibling schema, `summary_l0`/`overview_l1` wrapped in the literal-quote convention, `description` unwrapped), and the developer-experience `skill_count` bumped 31 -> 32 in `data/marketplace.json`. Catalog now consistently reports **268 skills** across `skills.json` (268 entries), the marketplace category-sum (268), and `SKILL_INDEX.md`. Added a `skill-native` row to `docs/policy/mcp-reverse-engineering-matrix.md` recording the MIT external source (named ONLY in the matrix, never in the shipped skill body, per the Reverse-Engineering Attribution Rule) and confirming zero outbound call / API key / dependency / data processor / new commercial relationship. Added a `## [Unreleased]` section to `CHANGELOG.md` (Added: the skill; note the 268-skill count; no version-surface bump). Gates green: JSON integrity (all 5 catalog files parse), `check_version_sync` still matches 3.15.2 (no version numbers touched; the `[Unreleased]` heading is correctly ignored by the extractor), `run_trigger_evals.py --gate` still PASS (the routing gate reads SKILL.md, not skills.json, so the mirror add is inert to it), and the skill validator still PASS. The README / AGENTS.md prose skill-count ("267 skills") is intentionally NOT bumped here; `/update release` owns the count-surface reconciliation at release time (Phase 3 hands off to it).

**Phase 3 (terminal refactor + known-gaps reconciliation + CI/CD) COMPLETE.** **3.1 refactor** ([[project-refactor]] + [[docs-layout-refactor]]): a verification pass, near-no-op as expected for a skill-only plan. The cumulative plan diff (`develop..HEAD`) is exactly 13 cohesive files - the 4-file skill bundle (standard `SKILL.md` + `references/` + `evals/` layout, no empty dirs, no orphans, no stray files), the 3 `data/` registry files, and the docs (CHANGELOG, matrix row, DEVLOG, known-gaps, 2 session-history files, all correctly placed under `docs/v3/v3.15/`). Nothing to move or delete. **3.2 known-gaps**: this reconciliation - NI-1 kept as a documented non-blocking deferral; DF-1 (below) records the one deferred follow-up; the three advisories carried for `/update release`. **3.3 CI/CD**: confirmed the existing `.github/workflows/ci.yml` already covers every change with no edit - skill validation (`validate_skills.py --bundles-only`), trigger + routing (`run_trigger_evals.py --gate`), and registry integrity (the `skills.json` / `bundles.json` / `workflows.json` JSON-parse steps) all run under the single `validate` job, which is already optimized (workflow-level `paths-ignore: docs/**` so `catalog/**` + `data/**` + `scripts/**` changes trigger it, `concurrency` cancel-in-progress, pip caching, and cost-gated macOS/Windows matrix legs on the bootstrap / install-smoke jobs). A separately-path-filtered job for this sub-second work would only add checkout + setup minutes (the same decision recorded at v3.15.1 QG-1 and v3.15.2 DF-1). **3.4 validation**: `validate_skills.py` (skill + whole-tree `--bundles-only`), `run_trigger_evals.py --gate`, `check_version_sync`, and the catalog JSON-integrity checks all green; no behavior changed (verification-only refactor). `make` is unavailable on this Windows host, so the steps ran individually; CI is the authoritative full-suite gate. **Release hand-off**: the version bump, changelog finalization, and the count-surface reconciliation (README / AGENTS.md / `plugin.description` to 268) are handed to `/update release`; no tag / merge / push performed by this phase.

### v3.15.3 Open Items

#### Deferred

##### DF-1 - promote the self-check eval-loop pattern into a reusable authoring convention

- **Source phase**: v3.15.3 Phase 3.2 (deferred follow-up).
- **Plan reference**: Phase 3.2 ("Record any deferred anti-slop follow-ups, for example promoting the self-check eval pattern into a reusable authoring convention").
- **Reason**: `anti-slop-editing` ships a runtime self-check loop (the skill grades its own output against `references/self-check.md`, fixes, and re-checks before returning). This is a genuinely reusable authoring pattern - a skill that produces content could ship a rubric and self-grade against it - but generalizing it (a shared convention documented in AGENTS.md, or a `references/self-check.md` template other skills adopt) is out of scope for this single-skill plan.
- **Suggested next step**: in a future cycle, evaluate promoting the self-check-loop pattern into an authoring convention (AGENTS.md guidance + an optional shared rubric template), so other content-producing skills can adopt it. Non-blocking; the pattern works today inside `anti-slop-editing`.

#### Not implemented

##### NI-1 - description carries 3 of the 5 plan-listed trigger phrases verbatim (250-char ceiling; mitigated)

- **Source phase**: v3.15.3 Phase 1.1.
- **Plan reference**: Phase 1.1 (description trigger phrases: "make this less AI-sounding", "does this read as AI", "de-slop this", "remove AI patterns", "audit this draft for slop").
- **Reason**: the single-line `description` is capped at 250 chars (the `validate_skills.py` I-03 rule). The three phrases that also carry the strongest lexical routing signal ("de-slop this", "make it less AI-sounding", "does this read as AI") are in the description verbatim; the other two ("remove AI patterns", "audit this draft for slop") are covered by `overview_l1` and the "When to Use This Skill" section, which the agent reads at trigger time. Routing is proven by the passing trigger-eval `--gate`, so discoverability is not degraded.
- **Suggested next step**: none required. If the 250-char budget frees up (for example via a shorter SKIP phrasing), fold one more phrase into the description. Non-blocking.

### v3.15.3 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 1 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

OPEN and carried as documented, non-blocking deferrals: NI-1 (description carries 3 of 5 plan-listed trigger phrases verbatim under the 250-char cap; routing proven by the `--gate`), DF-1 (promote the self-check eval-loop pattern into a reusable authoring convention in a future cycle). No release blocker.

### v3.15.3 Release readiness (Phase 3, release-readiness 9A/9B)

- **9A resolve known gaps**: re-read the Open Items above; grepped the plan's added files for `TODO`/`FIXME`/`XXX`/`HACK`/`# DEVIATION:` - none (the bundle is prose; the only "TODO"-like strings are absent). NI-1 and DF-1 are out-of-scope-to-fix-now, documented deferrals. No release blocker remains.
- **9B verify tests + CI**: no new code module ships (prose skill), so no unit test is owed; the validation surface (`evals/trigger-cases.json` + the validators) is green, and CI covers `catalog/skills/**` + `data/**` through the `validate` job. No missing tests.
- **9C-9E hand-off**: handed to `/update release` (version bump 3.15.2 -> 3.15.3 across every `check_version_sync` surface, changelog finalization, the 268-skill count reconciliation in README / AGENTS.md / `plugin.description`, then commit / merge develop -> main / tag / GitHub Release under its own gates). This phase performed no tag, merge, or push.

### v3.15.3 Advisory (pre-existing, not introduced by this plan)

- The whole-tree bundle audit reports one orphan: `catalog/skills/workflow/demo-capture/scripts/__pycache__/capture-demo.cpython-312.pyc` (a compiled-bytecode artifact). It is PRE-EXISTING (not created by this plan), lives in a different skill, and is a warning, never an error. Left untouched per the no-out-of-scope-cleanup rule; a future `demo-capture` touch or a `.gitignore` / clean pass should remove the stray `.pyc`.
- **`marketplace.json` `statistics.total_skills` does not exist** (Phase 2 reconciliation): the plan's sub-task 2.1 said to "increment ... `statistics.total_skills`", but the current `marketplace.json` schema has an empty `statistics: {}` block and derives the catalog total from the sum of `categories[].skill_count`. Registration therefore only bumped the developer-experience `skill_count` (31 -> 32), which keeps the derived total (268) consistent with `skills.json`. No `statistics.total_skills` field was invented (that would risk breaking schema consumers). Non-blocking; the derived total is correct.
- **`marketplace.json` `plugin.description` skill count is stale** ("265 curated skills"): PRE-EXISTING drift (it already read 265 while the catalog held 267), not introduced by this plan and not made worse by it. It is a marketing-prose count, not a `check_version_sync` surface. Left untouched per the no-out-of-scope-cleanup rule; `/update release` should reconcile it (along with the README / AGENTS.md "267 skills" prose) to 268 at release time.

## v3.15.4 - presentify-visual-fidelity

**Status**: IN PROGRESS. Phases 1-6 COMPLETE; Phase 7 (terminal refactor + known-gaps + CI/CD) pending. This section is appended per-phase and finalized at the v3.15.4 release (Phase 7). Plan: [plans/v3.15.4-presentify-visual-fidelity.md](plans/v3.15.4-presentify-visual-fidelity.md).

> **Prior-version ingest**: checked this file (docs/v3/v3.15/known-gaps.md). The open v3.15.0-.3 items are unrelated to presentify visual fidelity and do not carry in. The v3.15.2/.3 `__pycache__` `.pyc` advisory recurs (a transient, gitignored bytecode artifact); see the v3.15.4 Advisory.

**Phase 1 (full-width canvas contract) COMPLETE.** Made "full-width" a concrete, measurable edge-to-edge canvas across both the LLM-native authoring path and the deterministic baseline builder. **1.1**: replaced the prose "Full-width" bullet in `references/interactive-features.md` ("Output aspect (the canvas)") with an enforceable contract (page shell spans the viewport via named `--gutter` tokens not a centered `max-width` column; full-bleed top-level bands; the 45-85ch `--measure` scoped per prose element only; and a success metric - the widest top-level content band reaches at least ~95% of a 1920px viewport with no global zoom) plus a "failure to avoid" note. **1.2**: tightened SKILL.md Step 6 (the "Use the viewport width on purpose" and "Spacing, density, and aspect" bullets) to cite the contract by name and state the binary full-width rule, and added a distinct Common Rationalizations row rebutting the full-width centered-column retreat. **1.3**: added `--layout {full|standard|portrait}` (default standard) to `build_presentation.py`, which injects a `--page-max`/`--gutter` pair into a new `NEXUS_ASPECT` marker block and stamps `data-aspect` on the root `<html>`; the template (`assets/presentation-template.html`) now drives the canvas from those vars (`--slide-max` -> `--page-max`, `.slide` padding -> `--gutter`), keeps `--measure` scoped to prose only, widens a full-width chart to its band, and gates the projector-padding widening to non-full aspects. `standard` reproduces the historical centered column; `full` is edge-to-edge (page-max 100%, small gutters, ~96.7% band at 1920px); `portrait` is a 46rem reading column. **1.4**: `tests/skills/test_presentify_layout.py` (11 pass / 1 skip) asserts the injected vars + `data-aspect` per layout, offline-cleanliness, head integrity, and a browser-free CSS heuristic proving the >=95% full-width / <95% standard metric; it also ships a headless-optional `measure_widest_band` helper (the Phase 5 gate seed) whose true-render check skips-with-note without a browser. CI: `presentify-extractor.yml` path filter broadened to the whole bundle + the new test, `pytest` added, and the layout suite wired in (concurrency-cancel + pip cache already present). Gates green: ruff clean, `validate_skills.py --bundles-only` (0 errors), `validate_unicode_safety.py` (0 errors), `validate_workflow_security.py`, and the full `tests/skills` suite (33 pass / 1 skip).

**Phase 2 (image sizing and placement discipline) COMPLETE.** Gave every image a prominence-appropriate, bounded box with no meaningful-content crop and no dead space at 100% zoom. **2.1**: extended `references/interactive-features.md` "Prominence preservation" with four measurable image-box rules (a hero height cap of ~80vh; a secondary cap that forbids a low-`page_fraction` image from ballooning past a hero, the inverse of the contact-sheet defect; an object-fit / crop policy where `contain` plus a matched background serves meaningful content and `cover` is reserved for decorative backdrops; and a no-oversized-tile rule) plus a dead-space ceiling (~30%) in "Spacing and density", each with an observable metric the Phase 5 QA gate grades (rendered box vs viewport, aspect-distortion ratio, whitespace fraction). **2.2**: CONFIRMED (no extractor code change) that `scripts/extract_content.py` already emits `page_fraction` and native `width`/`height` for BOTH PPTX picture shapes (`shape-picture`, fraction from shape-vs-slide area) and PDF embedded rasters (`embedded-raster`, fraction from bbox-vs-page area), and that `references/content-model.md` already documents these v3 fields; the confirmation artifact is the new prominence test. **2.3**: applied the caps to `assets/presentation-template.html`: `figure img` now carries `max-height: 80vh` + `object-fit: contain` + a matched `background` (aspect preserved via `height: auto` + `max-width`), and a new token-driven `.gallery` grid caps each tile (a minimum width plus `max-height: 40vh` + `object-fit: contain`) so no secondary balloons. **2.4**: `tests/skills/test_presentify_extractor_prominence.py` (PPTX + PDF fixtures via python-pptx / reportlab, `importorskip`-guarded) asserts populated `page_fraction` + native dimensions; `tests/skills/test_presentify_layout.py` gained a browser-free image-cap assertion (max-height, object-fit, gallery) and a headless-optional rendered image-box check (skips without a browser). CI: `presentify-extractor.yml` path filter broadened to `tests/skills/**` and the step now runs the whole `tests/skills/` dir (that runner installs the heavy extractor libs, so the prominence tests execute there). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, workflow-security pass, full `tests/skills` suite 36 pass / 2 skip.

**Phase 3 (annotated-figure overlay recreation) COMPLETE.** When a source figure is a base image carrying author-added annotations (map regions, colored zones, callout labels), those annotations are now recreated as a registered interactive overlay on the extracted base image instead of being dropped to a textual list beside a flat map. **3.1**: `references/figure-reconstruction.md` part 1 records an `annotated: true` signal alongside the base classification, and part 5 is rewritten from a binary (full SVG rebuild OR flat enhanced-original) into a THREE-way decision that adds the OVERLAY-RECREATION path (keep the base image; recreate each annotation in a registered overlay layer normalized to the base image with percentage coords; make it interactive with hover/focus highlight, a click-toggle legend, keyboard focus, and a lightbox that moves base + overlay together; carry the provenance badge + view-original toggle), with the side-text kept as an ACCESSIBLE COMPLEMENT, never the replacement. **3.2**: part 4 gates overlays on confidence (high/medium recreate; low degrades to enhanced-original + textual complement with no fabricated regions), part 6 adds the overlay round-trip, and the coverage-reconciliation format adds an `[overlay-reconstructed]` accounting line. **3.3**: `scripts/extract_content.py` now captures PPTX overlay shapes drawn over a picture as an `annotations` array on the image block (a non-picture shape whose center lies inside a picture and is smaller than it, with an image-relative bbox, text, solid fill/line colors, and the enclosing group name); `_iter_pptx_shapes` was extended to carry the group name, and a two-pass shape walk assigns overlays without emitting them as stray text. `content-model.md` and `extraction-runbook.md` document the new field and the flattened-PDF agent-vision path. The extractor change is regression-free (the committed and the new extractor both score 41 PASS / 4 environmental-OCR FAIL on `verify_phase1.py`, and all 8 PPTX checks pass). **3.4**: the baseline builder (`build_presentation.py` + `assets/presentation-template.html`) recreates the overlay from the `annotations` metadata as the deterministic realization of the pattern (a `.fig-annotated` figure: base image, a `.fig-overlay` layer of percentage-positioned `.fig-region` elements with labels, a `.fig-legend`, a provenance badge, and a CSS-only view-original toggle - a checkbox + label, no JS), so the end-to-end path (annotated PPTX -> extractor -> builder -> HTML) is testable. Tests in `tests/skills/test_presentify_annotations.py` (5 cases, 4 run locally + 1 headless-optional skip) cover the extractor annotations, the end-to-end overlay, the dependency-free builder overlay, and the no-annotations degrade. CI needs no edit: `presentify-extractor.yml` already runs the whole `tests/skills/` dir under a `tests/skills/**` path filter (Phase 2). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, full `tests/skills` suite 40 pass / 3 skip. **Post-commit security hardening**: a background commit-review flagged that `annotations[].fill` (and the legend color) was interpolated RAW into an inline `style="..."` attribute (attribute-context injection). Fixed by adding `_safe_color` (strict `#hex` validation, drop otherwise) at the fill's point of use, so the content-model JSON (a general input contract, not only the trusted extractor output) cannot inject via a color; legitimate hex is unaffected, and `test_builder_rejects_malicious_fill_color` regression-guards it (suite now 41 pass / 3 skip).

**Phase 4 (reliable stock/mix imagery integration) COMPLETE.** Made a stock/mix imagery choice reliably put relevant, license-verified images into image-starved sections, so "mix" never silently produces zero images. **4.1**: folded the build-time-network / generation CONSENT into the up-front batched design round (`catalog/commands/presentify.md` + SKILL.md Step 2): when the resolved imagery tier is `stock`, `mix` / `auto`, or `ai`, consent is captured with the four design choices, not as a separate mid-run prompt, and a consented run is EXPECTED to attempt integration (silence is a bug). The load-bearing invariants are preserved: the default `procedural` tier and every non-interactive run stay offline; `fetch_stock_media.py` performs NO network without `--consent`; a recalled preference never pre-answers consent. **4.2**: defined an image-starved-section detection pass (SKILL.md Step 6 + `references/interactive-features.md` Tier 2): after the structure is drafted, identify each section that carries no source visual AND would be materially clearer with one, derive SHORT content-relevant keywords from the section topic (never the source document text, keeping the compiling-content trap closed), and fetch/license-verify/base64-embed ONE relevant asset per starved section (Openverse-first, then Wikimedia, Pexels when configured), placed per the Phase 2 sizing rules, with relevance-and-restraint (a loosely-related photo is worse than none). **4.3**: added the integration gate (SKILL.md Verification item + a Tier 2 rubric criterion feeding Phase 5): a consented `stock` / `mix` / `ai` run MUST integrate at least one relevant asset into each starved section OR record a per-section reason; a consented run that integrated ZERO assets with no reason FAILS. **4.4**: VERIFIED (no change) that `nexus-hub setup-media` already exists and stores the Pexels key at `~/.nexus-hub/config/media.env` at mode 0600 - it is wired in `scripts/nexus_hub_cli.py` (`cmd_setup_media` dispatches to `scripts/setup_media_keys.py`), listed in `--help`, present in both installers, and tested by `tests/skills/test_media_key_setup.py`; the first-time-video note in the command/skill already points at it. No installer edit and no "Ask first" trigger. **4.5**: `tests/skills/test_presentify_stock_fetch.py` (14 cases, network monkeypatched so no real request and no `requests` dependency) covers the consent gate (no `--consent` = no network + degrade code 3), a consented Openverse run integrating + crediting a base64 asset (offline), the free-for-commercial-use allow-list rejecting NC/ND (parametrized `is_commercial_cc` + `accept_candidate`), and degrade-always-carries-a-reason (so the integration gate never sees silent zero-integration). CI needs no edit: the fetcher is under the bundle path filter and the new test under `tests/skills/**` (Phase 2). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, full `tests/skills` suite 55 pass / 3 skip. Extractor (`fetch_stock_media.py`) UNCHANGED (complete since v3.13/v3.14); this phase is pipeline wiring (command + skill + reference prose) plus tests.

**Phase 5 (iterative multi-agent visual-QA self-critique loop) COMPLETE.** Replaced the single-pass Step 9 with a genuine iterative loop that renders the output, grades each segment against its source and the measurable Phase 1-4 rubric, adversarially verifies, synthesizes fixes, and re-renders until the page-level bar passes or a cap is hit. **5.1**: authored `references/visual-qa-rubric.md` - the per-segment grading rubric assembling metrics from Phases 1-4 (full-width band, image sizing / crop / dead-space, annotation-overlay fidelity vs source, imagery integration into starved sections, readability / layout integrity), split into STRUCTURAL (deterministic, scorer-checkable) and AGENT-VISION (screenshot judgment) kinds, with a per-segment score schema and a binary page-level pass bar (no open high-severity finding). **5.2**: added the Dynamic-Workflow TEMPLATE `assets/visual-qa-workflow.js` (adapt, not run verbatim) that fans the per-segment grading out (pipeline: grade -> adversarially verify high-severity findings with an independent skeptic -> synthesize fixes -> rebuild -> re-grade), carrying the THREE mandatory workflow rules inline: graceful degradation (Dynamic Workflows -> isolated subagents -> single sequential agent, and headless render -> the structural scorer), scope-first token caution (5-15x multiplier, calibrate on one segment, confirm before scale), and skill-native (no outbound call / dependency / credential, LOCAL render); cross-links `[[agent-orchestration-primitives]]` + `[[ai-billing-safeguards]]`. **5.5a**: shipped `scripts/visual_qa_score.py` - the deterministic STRUCTURAL scorer (stdlib-only, no network, headless-optional) that scores a generated `.html` against the structural rubric subset (full-width band via the canvas vars, image caps, overlay well-formedness, imagery-integration count, offline / layout integrity) and returns per-criterion findings + the binary pass bar; it is the structural-review degradation path AND the reused Phase-1 `measure_widest_band` "gate seed" made concrete. **5.3**: rewrote SKILL.md Step 9 from a single render-and-look into the iterative render -> per-segment grade -> adversarially-verify -> synthesize -> re-render loop with the full degradation ladder and the scope-first / budget caution, and updated the Bundled Resources list with the rubric, the scorer, and the workflow template. **5.4**: refreshed the SKILL.md Verification checklist (binary items for the full-width band metric, image sizing, annotation-overlay fidelity, the imagery-integration gate, and the loop-ran-and-converged-or-degraded check) and added four Common Rationalizations rows (one-render-pass, whole-page-not-per-segment, skip-verification-because-expensive, skip-QA-without-a-browser), each tied to one of the four observed defects. **5.5b**: `tests/skills/test_presentify_visual_qa.py` (10 cases, dependency-free) asserts the scorer flags each seeded structural defect (narrow full-width, missing image caps, dropped overlay, zero imagery on a consented expectation, a non-offline page) and passes a clean fixture and n/a cases, drives the CLI exit codes, and asserts the workflow template carries the three mandatory rules + cross-links and the rubric lists all five criteria + the pass bar. CI needs no edit: the scorer is under the bundle path filter (and ruff-linted by the presentify-extractor "Lint the bundled scripts" step), and the new test under `tests/skills/**` (Phase 2). Gates green: ruff clean, orphan-bundle audit 0 errors (rubric + scorer + workflow template all referenced from SKILL.md), unicode 0 errors, SKILL.md 229 lines (within the 800 cap), full `tests/skills` suite 65 pass / 3 skip.

**Phase 6 (command, skill, and registry polish) COMPLETE.** Finalized the user-facing command and skill text and added the loop-depth knob; no new open items (a polish phase). **6.1**: added an optional `--qa-depth {light|standard|deep}` flag to `catalog/commands/presentify.md` (Usage + a flag bullet) that bounds the Step 9 iterative visual-QA loop (`light` = a single grading pass, `standard` = the capped loop, `deep` = the full per-segment fan-out, the default per the chosen ambition), with the scope-first / 5-15x-multiplier caution and the `[[ai-billing-safeguards]]` cross-link; updated the command's visual-QA delegation sentence from the old single-pass description to the iterative per-segment render -> grade vs source -> adversarially-verify -> synthesize -> re-render loop with the degradation ladder; and added a matching `--qa-depth` note to SKILL.md Step 9 (the command already referenced the knob in its Common Rationalizations since Phase 5, so this closed that coherence gap). The four up-front design choices and the no-memory-pre-answer rule are intact. **6.2**: coherence pass over SKILL.md - added the iterative visual-QA loop as a node in the pipeline diagram (it previously stopped at the authored `.html`), and confirmed the Instructions, Common Rationalizations, Verification, and Bundled Resources all reflect Phases 1-5 (they do, from the per-phase edits). SKILL.md is 236 lines, within the 800 soft cap. **Frontmatter / registry decision (deliberate NO-CHANGE)**: reviewed `description` / `summary_l0` / `overview_l1` and left them UNCHANGED, so the three `data/` registry files are untouched. The description's trigger surface already covers the creation intent comprehensively (it already names the output aspect full-width / standard / portrait and "dominant source visuals kept prominent (not flattened into thumbnails)"); the Phase 1-5 work refines that intent rather than adding a new entry intent, and the plan's suggested refine / defect trigger phrases ("fix the layout", "the images are too big / cropped") would risk over-triggering the creation skill on requests that are not "build a presentify site from these documents". `summary_l0` is at its ~15-word budget and still accurate; `overview_l1` remains accurate (the visual-QA loop is an internal quality mechanism, not a new user-facing output type). Per the plan's "ONLY IF changed", no registry sync was performed. **6.3**: `validate_skills.py --bundles-only` (0 errors), `run_trigger_evals.py --gate` (0 collisions, 0 routing failures; descriptions unchanged), and `validate_unicode_safety.py` (0 errors) all green; confirmed CI needs no edit - `ci.yml`'s `validate` job already runs catalog validation and triggers on `catalog/**` + `data/**` (via `paths-ignore: docs/**`) with concurrency + caching, so a separately-path-filtered job would only add minutes (the same decision recorded at v3.15.1 QG-1 / v3.15.2 DF-1). No code changed (Markdown-only), so ruff is not applicable; full `tests/skills` suite still 65 pass / 3 skip.

### v3.15.4 Open Items

#### Deferred

##### DF-3 - overlay-annotation detection is a geometric heuristic (full-slide-background text is captured)

- **Source phase**: v3.15.4 Phase 3.3.
- **Plan reference**: Phase 3.3 (capture author-added overlay shapes over a picture).
- **Reason**: the extractor assigns a non-picture shape as an annotation when its CENTER lies inside a picture AND its area is smaller than the picture. This correctly captures region rectangles and callout labels over a figure, but a full-slide BACKGROUND picture with body text on top would capture that body text as annotations (the text is, arguably, overlaid on the image). The LLM-native path re-reads under the confidence gate and applies judgment; the deterministic builder renders whatever `annotations` carries. Documented in the `extraction-runbook.md` PPTX gotchas.
- **Suggested next step**: if this over-capture is observed in practice, tighten the heuristic (for example, skip pictures whose `page_fraction` is ~1.0 unless they are classified `map`/`diagram`/annotated, or require the annotation shape to carry a fill or a short label). Non-blocking; the primary consumer applies judgment.

##### DF-1 - baseline builder does not group images into a `.gallery` (styles are latent)

- **Source phase**: v3.15.4 Phase 2.3.
- **Plan reference**: Phase 2.3 (template image / gallery styles) and 2.1 (prominence rules; the primary target is the LLM-native authoring path).
- **Reason**: the Phase 2.3 template now carries a token-driven `.gallery` grid with a bounded per-tile cap, but the deterministic baseline builder (`build_presentation.py`) renders each image as its own stacked `<figure>` and does not emit a `.gallery` wrapper or classify hero-vs-secondary from `page_fraction`. So on the baseline path several small images stack (each bounded by `max-height: 80vh` + `max-width`, so none crops or distorts) rather than forming a grid. The prominence-aware hero/secondary sizing and the gallery grid are the LLM-native path's job per the reference; the baseline is the "plain draft to elevate".
- **Suggested next step**: if the baseline should render a true gallery, teach the builder to group a run of comparable-`page_fraction` images into a `.gallery` wrapper (and size a high-`page_fraction` image as a hero) in a later phase. Non-blocking.

##### DF-2 - PDF embedded-raster `page_fraction` is null when the pdfplumber image-bbox count does not match the extracted raster count

- **Source phase**: v3.15.4 Phase 2.2 (discovered while confirming the signals).
- **Plan reference**: Phase 2.2 ("If any is missing or frequently null, add it").
- **Reason**: the PDF path computes `page_fraction` for an embedded raster only when pdfplumber's per-page `images` bbox list length equals the extracted raster count (the extractor's intentional geometry-alignment guard, so a bbox is never mis-assigned to the wrong raster). When the counts differ the block still carries native `width`/`height` but `page_fraction` is absent. This is NOT "frequently null" for well-formed report PDFs (the confirmed embedded-raster test yields a populated fraction), so it is documented rather than fixed; PPTX pictures and PDF rasterized-regions always carry the fraction.
- **Suggested next step**: a later phase could add per-raster bbox matching (by size / order heuristics) to populate `page_fraction` even when the counts differ. Non-blocking; the native dimensions still provide a fallback ranking signal.

#### Bugs / regressions

##### BG-1 - baseline builder loses theme background/foreground colors in built output (PRE-EXISTING, discovered in Phase 1.3)

- **Source phase**: discovered during v3.15.4 Phase 1.3 (out of scope to fix here).
- **Plan reference**: Phase 1.3 (builder + template aspect support; colors are orthogonal to the full-width canvas contract).
- **Reason**: `theme_to_css()` in `build_presentation.py` emits `--color-background` / `--color-foreground`, but the template CSS references `var(--color-bg)` / `var(--color-fg)` (and the template's own `:root` defaults define `--color-bg` / `--color-fg`). The raw template renders correctly standalone; the BUILT output leaves `--color-bg` / `--color-fg` undefined, so `body` background / foreground fall back to initial values. This is PRE-EXISTING (both `theme_to_css` and the template default names are unchanged by this phase) and unrelated to the full-width canvas contract; fixing it would change "today's look" for `--layout standard`, which Phase 1 must reproduce. Not fixed here per the no-out-of-scope-cleanup rule.
- **Suggested next step**: align the two names (either `theme_to_css` emits `--color-bg`/`--color-fg`, or the template consumes `--color-background`/`--color-foreground`) in a later presentify phase (Phase 2 image/color work or Phase 7 refactor) or a dedicated fix; add a builder-output color-var assertion to the layout suite when fixed.

#### Missing tests / coverage gaps

##### MT-1 - rendered-width full-width check skips without a headless browser (browser-free heuristic covers the metric)

- **Source phase**: v3.15.4 Phase 1.4.
- **Plan reference**: Phase 1.4 ("when no headless browser is present, the helper falls back to a computed-CSS/markup heuristic and the test skips-with-note rather than failing") and the plan's Phase 7 deferral ("the headless-browser-optional degradation - structural review is weaker than a real render").
- **Reason**: `measure_widest_band` renders and measures the widest `.slide__body` when a headless browser (Playwright) is present, but no browser is installed on the dev host or in the `presentify-extractor` CI runner, so `test_rendered_band_width` SKIPS. The >=95% full-width / <95% standard metric IS asserted browser-free by `test_heuristic_band_fraction_meets_contract` (deterministic CSS/markup math), and the injected-var / offline / head-integrity assertions all run without a browser.
- **Suggested next step**: Phase 5 builds the iterative visual-QA loop and its gate; gate a headless-render job to merges/schedule there (per the plan) so the true rendered-width check runs in CI, and reuse `measure_widest_band` as its seed.

##### MT-2 - consented stock/mix per-section integration is agent behavior (fetcher enforcement is unit-tested; end-to-end graded by Phase 5)

- **Source phase**: v3.15.4 Phase 4.5.
- **Plan reference**: Phase 4.2 / 4.3 (image-starved-section detection + integration gate).
- **Reason**: the deterministic enforcement layer (`fetch_stock_media.py`'s consent gate, free-for-commercial-use allow-list, and degrade-with-a-reason) is unit-tested in `tests/skills/test_presentify_stock_fetch.py`. The agent-side behavior (detecting which sections are image-starved, deriving per-section keywords, and placing a fetched asset into each starved section) is LLM-native authoring, not deterministically unit-testable; it is graded by the Phase 5 visual-QA loop (imagery-integration criterion). This mirrors the prior phases' pattern (agent behavior graded by Phase 5).
- **Suggested next step**: Phase 5 adds the imagery-integration rubric criterion and gate; no additional unit test is owed for the agent-side placement. Non-blocking.

##### MT-3 - the visual-QA loop's agent-vision grading, fan-out, and end-to-end sample-deck smoke are behavioral (the structural scorer is the unit-tested backbone)

- **Source phase**: v3.15.4 Phase 5.5.
- **Plan reference**: Phase 5.5 ("a test that the workflow template degrades ... an end-to-end smoke test on the sample board deck fixture asserting the loop reaches the pass bar").
- **Reason**: the deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) is fully unit-tested (per-criterion defect flagging, clean pass, CLI exit codes). The AGENT-VISION grading (crop, dead space, annotation placement vs source, imagery relevance, contrast), the Dynamic-Workflow fan-out, and the full render -> grade -> fix -> re-render loop are LLM-native + runtime + browser behavior, not deterministically unit-testable; the workflow template is an adapt-me artifact asserted structurally (it carries the three mandatory rules), not executed. There is no committed "sample board deck" fixture, and the loop is agent-driven, so the e2e smoke is a browser-gated / release-time verification (the Phase 7 exit checklist verifies the four observed defects on the sample deck), not a CI unit test.
- **Suggested next step**: when a headless-browser CI job is added (gated to merges/schedule, per the plan), wire an e2e smoke that runs the scorer against a built sample-deck fixture; the agent-vision grading stays a behavioral (non-unit) check. Non-blocking.

### v3.15.4 Resolved

##### BG (deviation) - TITLE_RE swallowed the document head (PRE-EXISTING, root-cause fixed in Phase 1.3)

- **Source phase**: discovered and fixed in v3.15.4 Phase 1.3 (logged as a `# DEVIATION:` in `build_presentation.py`).
- **Status**: RESOLVED. `TITLE_RE = <title>.*?</title>` (DOTALL) matched the template header comment's literal "<title>" mention and spanned to the real `</title>`, deleting the comment close (`-->`), the `<html>` tag, `<head>`, and the `<meta>` tags on every build - so the baseline builder had been emitting malformed HTML with no document head (unnoticed because no test checked builder output structure and `assert_no_external` strips comments before scanning). Constraining the pattern to `<title>[^<]*</title>` keeps the match to a single well-formed title element. Fixed here because Phase 1.3 requires the builder to emit a valid `<html data-aspect="...">` (the head must survive); guarded by `test_head_survives_title_substitution`.

### v3.15.4 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 1 | 1 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 3 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

OPEN and carried as documented, non-blocking items: DF-1 (baseline builder does not group images into a `.gallery`; the gallery styles are latent for the LLM-native path), DF-2 (PDF embedded-raster `page_fraction` is null on a pdfplumber bbox-count mismatch; native dimensions still rank), DF-3 (overlay-annotation detection is a geometric heuristic that would capture full-slide-background body text; the primary consumer applies judgment), BG-1 (pre-existing builder color-var mismatch, out of scope for the canvas / sizing / overlay phases), MT-1 (rendered-width, rendered image-box, and rendered overlay-toggle checks skip without a headless browser; the metrics are covered browser-free by the CSS heuristic + markup assertions), MT-2 (consented stock/mix per-section integration is agent behavior; the fetcher enforcement is unit-tested and the end-to-end placement is graded by the Phase 5 loop), MT-3 (the visual-QA loop's agent-vision grading, fan-out, and e2e sample-deck smoke are behavioral; the structural scorer is the unit-tested backbone, and the e2e is a browser-gated / release-time check). RESOLVED: the pre-existing TITLE_RE head-corruption bug (root-cause fixed because Phase 1.3 depends on a valid document head).

### v3.15.4 Advisory (pre-existing, not introduced by this phase)

- The whole-tree bundle audit reports transient `__pycache__/*.pyc` orphan warnings (e.g. `catalog/skills/specialized-domains/document-to-interactive-html/scripts/__pycache__/build_presentation.cpython-312.pyc`) whenever the bundle's Python is executed locally. These are gitignored (`.gitignore` line 60, `__pycache__/`), never staged, and were cleaned after the Phase 1 test runs. Warning, never error; no action needed.
