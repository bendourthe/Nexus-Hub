# Nexus-Hub v2.2.0 -- CodeGraph adoption + Antigravity CLI transition

**Release date**: 2026-05-26
**Type**: SemVer **minor** (additive; no breaking changes)
**Plans**: [`plans/codegraph-and-antigravity.md`](plans/codegraph-and-antigravity.md), [`plans/adoption-antigravity-sdk-python.md`](plans/adoption-antigravity-sdk-python.md)
**CHANGELOG block**: [`CHANGELOG.md` -> `## [2.2.0]`](../../CHANGELOG.md)

## Highlights

v2.2.0 adopts **12 of 14** CodeGraph capabilities surfaced by the v2.1.0 cross-project comparison (see [`docs/archives/v2/v2.1/comparison-codegraph.md`](../v2.1.0/comparison-codegraph.md)) and ships the Gemini-CLI-to-Antigravity-CLI transition ahead of Google's 2026-06-18 sunset. The release operationalizes a reverse-engineering-first adoption strategy: every adopted capability is classified `re-full` or `re-partial` under the MCP Registry Policy (zero outbound calls, zero credentials, zero new third-party processors).

The Gemini CLI sunset is the time-critical anchor. Per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on **2026-06-18**. v2.2.0 deprecates the standalone Gemini CLI install behind an opt-in `--enterprise` flag, prints a sunset warning on every install, and verifies Antigravity CLI as the transition target via a documented install-path probe and dedicated integration tests. Phase 2 was positioned immediately after the Phase 1 installer foundation so the Antigravity transition could be cut and shipped independently if Phases 3-6 slipped; in practice all six phases shipped on schedule and v2.2.0 is the single combined release.

Two CodeGraph candidates are explicitly deferred to v2.3.0+: **C13** (standalone runtime bundling) and the remaining **10 framework extractors beyond C3's Django / FastAPI / Express starter set**. Both deferrals are documented at the end of [`plans/codegraph-and-antigravity.md`](plans/codegraph-and-antigravity.md) and at [`docs/archives/v2/v2.2/deferred-language-extractors.md`](deferred-language-extractors.md). The architectural surface is ready for them; only the long-tail extractor implementations are deferred.

The release ships:

- **`nexus-code-search` v2.0** -- a tree-sitter AST graph with 22 NodeKind values, 12 EdgeKind values, FTS5 full-text search, BFS call-graph traversal, debounced filesystem watcher, three framework route extractors (Django / FastAPI / Express), and an `affected_tests` test-impact analyzer. The v1 keyword-chunk index is preserved unchanged; v1 tools (`index_codebase`, `search_code`, `clear_index`, `get_indexing_status`) keep their original signatures.
- **Eight new code-graph MCP tools** on the `nexus-code-search` server: `index_graph`, `code_search`, `code_callers`, `code_callees`, `code_impact`, `code_node`, `code_context`, `code_explore`, plus `code_affected_tests` and `watch_for_changes`.
- **`IntegrationBase` returns `WriteResult`** -- every installer lifecycle method (`install_global`, `install_workspace`, `uninstall_global`, `uninstall_workspace`) returns a typed `WriteResult` with a `files: list[FileAction]` array whose actions are drawn from the canonical six-value vocabulary (`created` / `updated` / `unchanged` / `removed` / `not-found` / `kept`). The console output is rendered from the structured result; tests assert against the structure directly.
- **Marker-delimited instruction-file merge** -- every shared instruction file (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, the Google-family `GEMINI.md` / `AGENT.md` variants) is now updated via `merge_marker_section` with `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->` boundaries. User edits outside the marker block are preserved verbatim across reinstalls; legacy `## Nexus-Hub` unmarked sections are migrated inline.
- **Three new installer modes** -- `--check` exits 0 when the install is at parity with the registry and 1 when drift is detected (CI-friendly); `--print-config <integration-key>` dumps the multi-section Markdown readout of what the integration would install without touching disk; `nexus-hub init` walks every registered integration and invokes its `wire_project_surfaces` hook to bootstrap project-local surfaces (e.g., `.cursor/rules/nexus-hub.mdc`, `.claude/settings.json` permissions stub).
- **50-case parameterized contract suite** covering five invariants (install idempotency, uninstall reverses install, sibling preservation, partial state recovery, dry-run matches install) across all 10 registered integrations.
- **Tree-mirror parity tests** (10 cases) asserting SHA-256-identical output between the legacy bash `safe_folder_copy` blocks and the registry runner's `_copy_tree` for `catalog/skills`, `catalog/commands`, `catalog/agents`, `catalog/rules` across Claude / Codex / Cursor / Gemini / OpenCode. This closes **part 1** of DF-001 (carried forward from v2.1.0); the instruction-file byte-parity assertion (part 2) remains deferred to v2.3.0 as documented in [`docs/archives/v2/v2.2/known-gaps.md`](known-gaps.md).
- **Antigravity CLI as transition target** -- the existing `Antigravity20Integration` now covers both the desktop IDE and the CLI (renamed display_name "Antigravity 2.0 + CLI (Google)"). Probe results live at [`docs/archives/v2/v2.2/antigravity-cli-probe.md`](antigravity-cli-probe.md). A new `antigravity-cli-diff-review.sh/.ps1` hook joins the four existing Claude / Gemini / Codex / OpenCode pre-commit diff-review variants.
- **Gemini CLI gated behind `--enterprise`** -- default installer runs print a sunset warning and skip Gemini CLI; `--enterprise` (Bash) or `-Enterprise` (PowerShell) preserves the legacy install path for paying users.
- **Per-surface Google instruction templates** -- the shared body lives in `templates/ai-instructions/base-google-shared.md`; six thin wrappers (`base-gemini-ide.md`, `base-gemini-cli.md`, `base-antigravity-10.md`, `base-antigravity-20.md`, `base-antigravity-cli.md`, plus the legacy `base-gemini.md`) import the shared body via `@base-google-shared.md` and add 3-10 lines of surface-specific guidance.
- **MCP `initialize` server-instructions** on all three internal MCPs (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`). The instructions string lists the server's tools, cites the MCP Registry Policy (`already-local`), and points at the corresponding Nexus-Hub skill so agents connecting cold see authoritative tool guidance.
- **`affected_tests` MCP tool + `nexus-hub affected` CLI** -- reverse-import + reverse-call BFS over the AST graph identifies the test files transitively touched by a source change. Surfaces at the MCP layer (`code_affected_tests`) and via a thin CLI dispatcher (`scripts/nexus_hub_affected.py`) registered in both `installer.sh` and `installer.ps1`.
- **Synthetic-codebase MCP eval harness** -- `extensions/nexus-code-search/eval/` with four fixture codebases (minimal / python_app / fastapi_app / ts_express), 18 questions total, and a `make eval` target. v2.2.0 baseline: **100% aggregate recall**, **63.3% aggregate precision** -- all four fixtures clear the 80% per-fixture recall gate. Baseline preserved at [`docs/archives/v2/v2.2/eval-baseline.md`](eval-baseline.md). The 63.3% precision figure is documented in known-gaps WN-7 and tracked for v2.3.0.
- **`google-antigravity-sdk` skill** -- a new `ai-development` catalog skill for building autonomous agents on the Google Antigravity backend (async agent loop, declarative tool-call policies, lifecycle hooks, MCP integration, multimodal ingestion, triggers, subagents, structured output), with 7 reference docs and 12 example walkthroughs. Adopted from the `adoption-antigravity-sdk-python` plan alongside three pattern references and three cross-links woven into existing skills. See the dedicated section below.

Every change is additive. Users upgrading from v2.1.1 rerun the installer to pick up the new artifacts; pre-existing behavior is preserved for every integration. The Gemini CLI deprecation is gated behind `--enterprise` so users who upgrade ahead of 2026-06-18 keep working until the cutover.

## CodeGraph adoption -- the narrative

CodeGraph (https://github.com/colbymchenry/codegraph) is a TypeScript MCP server that wraps a SQLite-backed tree-sitter AST graph with call-graph traversal, framework-route extraction, an installer that supports 10 platforms with action-vocabulary output and `--check` / `--print-config` dry-run modes, and a 47-case parameterized contract test suite. The v2.1.0 comparison surfaced 14 candidates spanning four buckets:

- **Code intelligence** (C1, C2, C3, C8, C14): AST extraction, call-graph traversal, framework routes, test-impact analysis, file watching. These were entirely missing from `nexus-code-search` v1.0.0 (keyword-only inverted index).
- **Installer rigor** (C4, C5, C6, C7, C11, C12): action vocabulary, marker-delimited merges, dry-run modes, project-surfaces hook, parameterized contract tests, legacy self-healing. Nexus-Hub had the integration registry foundation (introduced in v2.1.0 Phase 10) but lacked the rigor.
- **MCP discoverability** (C9, C10): `initialize` server-instructions, MCP-tool eval harness. Nexus-Hub had `skill-eval-loop` for skills but no equivalent for MCP tools.
- **Distribution** (C13): standalone runtime bundling. Deferred to v2.3.0+.

Nexus-Hub already had the right architectural primitives (the integration registry from v2.1.0, the per-skill bundled-resources convention from v1.1.5, the cross-platform installer pair). What it lacked was the **typed surface** that turns those primitives into something a test suite can assert against. The bulk of v2.2.0 is that surface: `WriteResult`, `FileAction`, `NodeKind`, `EdgeKind`, `GraphTraverser`, `GraphQueryManager`, `ExtractionOrchestrator`, `FrameworkResolver`, the marker-merge primitive, the dry-run / print-config / init affordances, and the contract / parity / eval test suites that make the surface inspectable.

The Gemini CLI sunset is orthogonal to CodeGraph adoption but ran on the same v2.2.0 cycle. Phase 2 was sequenced immediately after Phase 1's installer foundation so the Antigravity transition could ship on its own if Phases 3-6 slipped. In practice the full plan landed on schedule, but the phase structure deliberately preserves the option to cut a `v2.2.0-rc1` or `-alpha1` containing only Phases 1+2 if a future release needs to ship under similar time pressure.

## What's new

### New MCP tools (on `nexus-code-search`)

| Tool | What it does | Phase |
|---|---|---|
| `index_graph` | Build / refresh the v2 SQLite + FTS5 AST graph at `<root>/.nexus/code-index/codegraph.db`. | Phase 4 |
| `code_search` | FTS5 full-text search over `(name, qualified_name, docstring)` with optional `kind` filter. | Phase 4 |
| `code_callers` | Direct callers of a symbol (`calls` edges where the target is the node). | Phase 4 |
| `code_callees` | Direct callees of a symbol (`calls` edges where the source is the node). | Phase 4 |
| `code_impact` | BFS over impact-bearing edges (`calls`, `references`, `extends`, `implements`, `overrides`) up to N hops. | Phase 4 |
| `code_node` | Resolve a node by ID or qualified name; optional source snippet. | Phase 4 |
| `code_context` | One-shot node + neighbors (callers, callees, contains). | Phase 4 |
| `code_explore` | Combined search + traversal: name -> node -> callers / callees / context. | Phase 4 |
| `watch_for_changes` | Start a debounced background filesystem watcher for the indexed repo. | Phase 4 |
| `code_affected_tests` | Reverse-import + reverse-call BFS to identify test files transitively touched by changed source files. | Phase 5 |

### New installer modes

| Mode | What it does | Phase |
|---|---|---|
| `installer.sh --check` / `installer.ps1 -Check` | Run every registered integration's `dry_run()`; exit 0 if every file action is `unchanged` / `kept`, else 1. Zero disk writes. | Phase 3 |
| `installer.sh --print-config <key>` / `installer.ps1 -PrintConfig <key>` | Dump a multi-section Markdown readout of what the integration would install at the current target. Zero disk writes. | Phase 3 |
| `installer.sh init` / `installer.ps1 init` | Walk every registered integration and invoke `wire_project_surfaces(ctx)`. Bootstraps `.cursor/rules/nexus-hub.mdc`, `.claude/settings.json` permissions stub, etc., per integration. | Phase 3 |
| `installer.sh --enterprise` / `installer.ps1 -Enterprise` | Opt-in Gemini CLI install; default flow skips Gemini CLI with a sunset warning. | Phase 2 |

### New integration coverage

| Integration | What changed | Phase |
|---|---|---|
| `Antigravity20Integration` | Display name renamed to "Antigravity 2.0 + CLI (Google)" reflecting dual desktop + CLI coverage; docstring states the CLI inheritance explicitly. | Phase 2 |
| `GeminiCliIntegration` | Display name renamed to "Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)"; default installer path skips with sunset warning. | Phase 2 |
| Google-family `instruction_template` fields | Each Google-side integration now points at its dedicated thin wrapper (`base-gemini-ide.md`, `base-gemini-cli.md`, `base-antigravity-10.md`, `base-antigravity-20.md`, `base-antigravity-cli.md`) instead of the shared `base-gemini.md`. | Phase 2 |

### New code-graph subsystem

| Module | What it does | Phase |
|---|---|---|
| `extensions/nexus-code-search/src/nexus_code_search/extraction/` | Tree-sitter parse worker, extraction orchestrator, per-language extractors. | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/python.py` | Python AST -> `function` / `class` / `method` / `parameter` / `import` / `variable` nodes + `contains` / `calls` / `imports` / `extends` edges. | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/extraction/languages/typescript.py` | TypeScript AST -> `class` / `interface` / `function` / `method` / `type_alias` / `import` / `export` nodes + heritage edges. | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/graph/` | `GraphTraverser` (BFS traversal) + `GraphQueryManager` (name-keyed convenience methods). | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/db/` | SQLite + FTS5 schema, v1 -> v2 migration with `.v1-backup` rename. | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/watch.py` | `watchdog`-backed debounced file watcher. | Phase 4 |
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/django.py` | `path()` / `re_path()` / `url()` / `include()` / `MyView.as_view()` -> `route` nodes + `references` edges. | Phase 5 |
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/fastapi.py` | `@app.<method>` / `@router.<method>` decorators (also matches Flask) -> `route` nodes + `decorates` edges. | Phase 5 |
| `extensions/nexus-code-search/src/nexus_code_search/frameworks/express.py` | `app.<method>` / `router.<method>` calls with middleware chains -> `route` nodes + `references` edges per middleware. | Phase 5 |
| `extensions/nexus-code-search/src/nexus_code_search/graph/affected.py` | Reverse-import + reverse-call BFS for test-impact analysis. | Phase 5 |
| `extensions/nexus-code-search/eval/` | Synthetic-codebase MCP eval harness with 4 fixtures + 18 questions. | Phase 5 |

### New installer infrastructure

| Module | What it does | Phase |
|---|---|---|
| `scripts/lib/integrations/result.py` | `FileAction` + `WriteResult` dataclasses; six-value action enum. | Phase 1 |
| `scripts/lib/installer/instruction_merge.py` | `merge_marker_section` + `remove_marker_section` non-destructive primitives. | Phase 1 |
| `scripts/lib/integrations/legacy.py` | `LEGACY_CLEANUPS` registry; per-integration cleanup functions called at install time. | Phase 3 |
| `scripts/nexus_hub_affected.py` | CLI dispatcher for `code_affected_tests`. Registered in both installers. | Phase 5 |

### New hooks

| Hook | What it does | Phase |
|---|---|---|
| `catalog/hooks/antigravity-cli-diff-review.sh` + `.ps1` | Pre-commit diff review via `antigravity -p`. Joins the Claude / Gemini / Codex / OpenCode siblings. | Phase 2 |

### New templates

| Template | What it does | Phase |
|---|---|---|
| `templates/ai-instructions/base-google-shared.md` | Shared body for every Google-family surface. | Phase 2 |
| `templates/ai-instructions/base-gemini-ide.md` | Gemini IDE wrapper; imports shared body. | Phase 2 |
| `templates/ai-instructions/base-gemini-cli.md` | Gemini CLI wrapper; imports shared body; surface-specific deprecation note. | Phase 2 |
| `templates/ai-instructions/base-antigravity-10.md` | Antigravity 1.0 wrapper. | Phase 2 |
| `templates/ai-instructions/base-antigravity-20.md` | Antigravity 2.0 + CLI wrapper. | Phase 2 |
| `templates/ai-instructions/base-antigravity-cli.md` | Antigravity CLI alias wrapper. | Phase 2 |

### New test suites

| Suite | What it asserts | Phase |
|---|---|---|
| `tests/integrations/test_contract.py` | 50 cases: install idempotency, uninstall reverses install, sibling preservation, partial state recovery, dry-run matches install -- across all 10 integrations. | Phase 3 |
| `tests/integrations/test_parity_with_legacy_installer.py` | 10 cases: SHA-256-identical tree-mirror output between legacy bash and registry runner for claude / codex / cursor / gemini / opencode across `catalog/skills`, `catalog/commands`, `catalog/agents`, `catalog/rules`. | Phase 3 |
| `tests/installer/test_check_flag.py` | `--check` exits 0 on no-drift, 1 on drift; zero disk writes verified by tree byte-equality before/after. | Phase 3 |
| `tests/installer/test_print_config.py` | `--print-config` golden-file fixtures per integration. | Phase 3 |
| `tests/installer/test_init_subcommand.py` | `nexus-hub init` creates project-local surfaces; idempotency verified by `unchanged` on re-run. | Phase 3 |
| `tests/installer/test_enterprise_flag.py` | Default run prints sunset warning + skips Gemini CLI; `--enterprise` runs the legacy path. | Phase 2 |
| `tests/integrations/test_antigravity.py` | 6 cases: Antigravity 1.0 and 2.0 + CLI install correctly; display_name surfaces dual coverage; templates point at dedicated wrappers; idempotency. | Phase 2 |
| `tests/integrations/test_google_templates.py` | All 5 Google-family templates render without error. | Phase 2 |
| `tests/integrations/test_legacy_cleanups.py` | 5 cleanups: pre-2.0.0 `~/.devai-hub/`, `~/.claude/devai-hub-skills.json`, `~/.codex/devai-hub-skills/`, `~/.gemini/devai-hub-skills/`, VS Code extension rename. | Phase 3 |
| `extensions/nexus-code-search/tests/test_python_extraction.py` + `test_typescript_extraction.py` | Per-language AST extractors emit expected NodeKind / EdgeKind counts on 5 fixture files each. | Phase 4 |
| `extensions/nexus-code-search/tests/test_traverser.py` | `GraphTraverser.callers` / `callees` / `impact_radius` / `find_path` against known fixture graphs. | Phase 4 |
| `extensions/nexus-code-search/tests/test_watcher.py` | Debounced filesystem watcher fires `on_change` after the debounce window. | Phase 4 |
| `extensions/nexus-code-search/tests/test_django_routes.py` + `test_fastapi_routes.py` + `test_express_routes.py` | Framework resolvers emit expected route nodes + references / decorates edges. | Phase 5 |
| `extensions/nexus-code-search/tests/test_affected.py` | `code_affected_tests` returns the right test files for changed source files in a fixture project. | Phase 5 |
| `extensions/nexus-code-search/tests/test_eval_runner.py` | Eval harness produces a Markdown report against fixture answer keys. | Phase 5 |

## Per-candidate adoption map (C1 -- C14)

| ID | Title | Shipped artifact(s) | Phase / sub-tasks |
|---|---|---|---|
| **C1** | Tree-sitter AST extraction with `NodeKind` / `EdgeKind` taxonomy | `extensions/nexus-code-search/src/nexus_code_search/extraction/` + `types.py` (22 NodeKind / 12 EdgeKind values) + `db/schema.sql` (SQLite + FTS5) | Phase 4 -- T023, T024, T025 |
| **C2** | Call-graph traversal (`callers`, `callees`, `impact`) | `extensions/nexus-code-search/src/nexus_code_search/graph/` (`GraphTraverser` + `GraphQueryManager`) + 6 new MCP tools | Phase 4 -- T026 |
| **C3** | Framework-route extraction (starter set: Django / FastAPI / Express) | `extensions/nexus-code-search/src/nexus_code_search/frameworks/{django,fastapi,express}.py` + `FrameworkResolver` base class | Phase 5 -- T029, T030, T031 |
| **C4** | Action vocabulary on every installer write | `scripts/lib/integrations/result.py` (`FileAction` + `WriteResult`); `IntegrationBase` lifecycle returns `WriteResult` | Phase 1 -- T001, T002 |
| **C5** | Marker-delimited section replacement in instruction files | `scripts/lib/installer/instruction_merge.py` (`merge_marker_section` + `remove_marker_section`); `MarkdownIntegration` routes shared-mode files through it | Phase 1 -- T003, T004 |
| **C6** | `--print-config <target>` / `--check` dry-run modes | `IntegrationBase.print_config()` + `IntegrationBase.dry_run()`; CLI flags in both installers | Phase 3 -- T017, T018 |
| **C7** | `wireProjectSurfaces()` hook called from project init | `IntegrationBase.wire_project_surfaces()` + `nexus-hub init` subcommand | Phase 3 -- T016 |
| **C8** | `codegraph affected <files>` for test-impact analysis | `graph/affected.py` + `code_affected_tests` MCP tool + `nexus_hub_affected.py` CLI | Phase 5 -- T032 |
| **C9** | MCP `initialize`-response server-instructions | `SERVER_INSTRUCTIONS` strings on all 3 internal MCPs; `initialize` returns the string per server | Phase 1 -- T005 |
| **C10** | Synthetic-codebase eval harness for the MCP server | `extensions/nexus-code-search/eval/` (4 fixtures, 18 questions, Markdown + JSON reports) + `make eval` target + `docs/archive/v2/v2.2/eval-baseline.md` | Phase 5 -- T033, T034 |
| **C11** | Parameterized installer-target contract tests (~50 cases) | `tests/integrations/test_contract.py` (5 invariants x 10 integrations) | Phase 3 -- T019 |
| **C12** | Legacy-state self-healing on re-install | `scripts/lib/integrations/legacy.py` + `LEGACY_CLEANUPS` registry + 5 cleanup functions | Phase 3 -- T015 |
| **C13** | Standalone installer bundling its own Node runtime | **DEFERRED to v2.3.0+** (item N1 in plan; Python 3.10+ dependency is accepted) | n/a |
| **C14** | File watcher with native OS events + debounce for index freshness | `extensions/nexus-code-search/src/nexus_code_search/watch.py` + `watch_for_changes` MCP tool | Phase 4 -- T027 |

**Adoption coverage**: 12 of 14 candidates shipped (C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C14). C13 deferred. C3's framework set is starter-only (3 of 13 frameworks); the remaining 10 are tracked under DF-002 in [`docs/archives/v2/v2.2/known-gaps.md`](known-gaps.md).

## antigravity-sdk-python adoption (A1-A8)

A second v2.2.0 plan, [`plans/adoption-antigravity-sdk-python.md`](plans/adoption-antigravity-sdk-python.md), adopts 8 skill-native candidates (A1-A8) from a cross-project comparison against an external Google Antigravity SDK skill. Every candidate is pure catalog content under the MCP Registry Policy `skill-native` classification: zero code, zero runtime dependencies added to Nexus-Hub, zero outbound calls. The skill teaches users to `pip install google-antigravity` in their own project; Nexus-Hub never executes the SDK. Per the Reverse-Engineering Attribution Rule, no user-facing line names the upstream repo -- attribution lives only in [`docs/policy/mcp-reverse-engineering-matrix.md`](../policy/mcp-reverse-engineering-matrix.md).

### What ships

- **New skill `ai-development/google-antigravity-sdk/`** (A1) -- `SKILL.md` plus 7 reference docs (`architecture`, `agent_configuration`, `mcp_integration`, `safety_policies`, `error_handling`, `observability`, `built_in_tools`) and 12 example walkthroughs under `references/examples/`. Covers the SDK's three-layer Agent / Conversation / Connection architecture, the async-first API, the declarative tool-call policy with its six-tier resolution order and fail-closed predicates, lifecycle hooks, MCP stdio + SSE integration, multimodal ingestion, triggers, subagents, and Pydantic structured output.
- **Antigravity CLI probe pinned** (A2) -- four backend-runtime fields (default model `gemini-3.5-flash`, app data dir `~/.gemini/antigravity/brain/`, MCP transport stdio + SSE, default policy `confirm_run_command()`) pinned to `(documented, SDK v0.1.1)` in a new Section 7 of [`docs/archives/v2/v2.2/antigravity-cli-probe.md`](antigravity-cli-probe.md), de-risking the Phase 2 probe assumptions.
- **Three pattern references** (A3, A4, A5) -- `agent-policy-resolution.md` under `security/authentication-patterns`, `lifecycle-hooks.md` and `multimodal-ingestion.md` under `ai-development/ai-agent-development`, each cross-linked bidirectionally with the new skill.
- **Three cross-link references** (A6, A7, A8) -- `sdk-triggers.md` under `workflow/dev-progress-tracker` (prior art for `/loop` + `/schedule`), `sdk-subagents.md` under `orchestration/multi-agent-coordinator`, `sdk-structured-output.md` under `ai-development/ai-agent-development`.

### Per-candidate adoption map (A1 -- A8)

| Candidate | What | Shipped as |
|---|---|---|
| A1 | google-antigravity-sdk skill | `catalog/skills/ai-development/google-antigravity-sdk/` (SKILL.md + 7 references + 12 examples) -- SDK plan T001-T003 |
| A2 | Antigravity runtime details pinned | `docs/archive/v2/v2.2/antigravity-cli-probe.md` Section 7 -- SDK plan T004 |
| A3 | Declarative policy resolution order | `security/authentication-patterns/references/agent-policy-resolution.md` -- SDK plan T008 |
| A4 | Agent lifecycle hooks | `ai-development/ai-agent-development/references/lifecycle-hooks.md` -- SDK plan T009 |
| A5 | Multimodal ingestion | `ai-development/ai-agent-development/references/multimodal-ingestion.md` -- SDK plan T010 |
| A6 | Triggers prior art | `workflow/dev-progress-tracker/references/sdk-triggers.md` -- SDK plan T013 |
| A7 | Subagents prior art | `orchestration/multi-agent-coordinator/references/sdk-subagents.md` -- SDK plan T014 |
| A8 | Structured output via Pydantic | `ai-development/ai-agent-development/references/sdk-structured-output.md` -- SDK plan T015 |

Four items were explicitly rejected per the MCP Registry Policy (N1 `google-genai` runtime dep, N2 bundled Go local-harness binary, N3 Vercel/Context7 skills-CLI distribution, N4 CONTRIBUTING/SECURITY stubs); these are policy rejections, not deferrals.

## Gemini-to-Antigravity CLI transition (Phase 2)

### Timeline

- **2026-05-21**: Google Developers Blog announces Gemini CLI transitions to Antigravity CLI; standalone Gemini CLI stops serving free / Pro / Ultra / GitHub-installed users on 2026-06-18.
- **2026-05-21**: v2.2.0 Phase 2 ships. Antigravity CLI verified as transition target; Gemini CLI gated behind `--enterprise`.
- **2026-06-18**: Google's sunset date. By this point, `--enterprise`-less installs already skip Gemini CLI with a sunset warning.

### What ships in Phase 2

1. **Antigravity CLI install-path probe** ([`docs/archives/v2/v2.2/antigravity-cli-probe.md`](antigravity-cli-probe.md)) confirming the existing `Antigravity20Integration` covers both the desktop IDE and the CLI without a separate class. The desktop and CLI share the `~/.agent/` config convention per the 2026-05-21 announcement.
2. **`Antigravity20Integration` display_name renamed** to "Antigravity 2.0 + CLI (Google)"; class docstring confirms dual coverage.
3. **6 new integration tests** covering Antigravity 1.0 and Antigravity 2.0 + CLI install paths, idempotency, and template wiring.
4. **`antigravity-cli-diff-review` hook** (`.sh` + `.ps1`) joining the Claude / Gemini / Codex / OpenCode siblings; installer copy loop updated in both `installer.sh` and `installer.ps1`.
5. **AGENTS.md "Platform coverage caveats"** rewritten to reflect the Extended-4 lineup (Antigravity 2.0 + CLI, Gemini CLI enterprise-only, Antigravity CLI alias, Nexus-AI) and the 2026-06-18 sunset.
6. **Per-surface Google instruction templates** -- shared body in `base-google-shared.md`, six dedicated wrappers. Lets the Gemini CLI surface be archived cleanly in a future release without affecting Antigravity.
7. **Antigravity CLI workflow file format schema** documented at [`docs/archives/v2/v2.2/antigravity-cli-commands-schema.md`](antigravity-cli-commands-schema.md). The CLI inherits Antigravity 2.0 desktop's Markdown workflow format (verbatim `.md` under `~/.agent/workflows/`), not Gemini CLI's TOML schema.
8. **`--enterprise` / `-Enterprise` flag** in both installers. Default flow prints `[INFO] Gemini CLI stops serving free / Google AI Pro / Ultra users on 2026-06-18. Re-run with --enterprise to install (requires paid Gemini API key); otherwise install Antigravity CLI for the same functionality.` and skips Gemini CLI.

### Open verification items

Three Antigravity-CLI items are tracked as WN-2 / WN-3 / WN-4 in [`docs/archives/v2/v2.2/known-gaps.md`](known-gaps.md): the binary name, the workflow file format, and the front-matter / name-derivation schema were all inferred from the public 2026-05-21 announcement and confirmed against Antigravity 2.0 desktop behavior, but not yet verified empirically on a live VM (Google had not shipped Antigravity CLI to a verifiable user channel as of v2.2.0 release). Re-verification is scheduled for the 2026-06-18 cutover.

## Known gaps carried forward to v2.3.0

The full list of open items is in [`docs/archives/v2/v2.2/known-gaps.md`](known-gaps.md). The headlines:

- **DF-001 part 2 (instruction-file byte parity)** -- the legacy bash `render_template` substitutes 13+ placeholders (`{{PRIMARY_LANGUAGE}}`, `{{BUILD_CMD}}`, `{{OS_CONTEXT}}`, `{{SKILL_INDEX}}`, ...) plus appends language-specific coding snippets; the Python `MarkdownIntegration._render` currently substitutes only `{{PROJECT_NAME}}`. Removing the legacy bash blocks without bringing the registry runner to feature parity would silently downgrade end-user instruction file content. Closes alongside MT-2 in v2.3.0.
- **DF-002 (18 deferred language extractors + 10 deferred framework extractors)** -- Go / Rust / Java / C# / PHP / Ruby / C / C++ / Swift / Kotlin / Scala / Dart / Lua / Luau / Svelte / Vue / Liquid / Pascal / JavaScript on the language side; NestJS / Laravel / Rails / Spring / Gin / chi / gorilla-mux / Axum / actix / Rocket / ASP.NET / Vapor / React Router / SvelteKit / Vue-Nuxt / Cargo on the framework side. Architecture ready; only the implementations are deferred.
- **WN-1 through WN-7** -- low-severity warnings: `pathspec` deprecation in nexus-code-search tests; Antigravity CLI binary / workflow / front-matter empirical verification (3 items); tree-sitter pin tightening rationale; Phase 4 in-file call resolution does not yet emit `instantiates` / `overrides`; Phase 5 eval precision at 63.3% (recall 100%) due to FTS5 matching parameter / signature tokens.

## Resolved this version

- **BG-P3-1** -- `merge_marker_section` truncated blocks at nested mentions of the end marker. Fixed by switching to `rindex`.
- **BG-P3-2** -- Copilot first-install wrote without a marker; subsequent installs appended marker + body to themselves. Fixed by always emitting the marker on first install.
- **BG-P4-1** -- TypeScript extractor missed `extends` / `implements` clauses under tree-sitter-typescript 0.23+. Fixed by walking `node.named_children` for `class_heritage`.
- **DF-001 part 1 (tree-mirror parity)** -- closed in Phase 3 by 10 SHA-256-identical parity tests. Part 2 (instruction-file byte parity) deferred to v2.3.0.

## Upgrade path

Users upgrading from v2.1.1:

1. Pull the latest commit and re-run `bash scripts/installer.sh` (macOS / Linux) or `pwsh scripts/installer.ps1` (Windows). Default behavior is preserved for every integration except Gemini CLI (now opt-in via `--enterprise`).
2. After install, run `bash scripts/installer.sh --check` (or `-Check` on PowerShell) to confirm zero drift.
3. To bootstrap project-local surfaces in a project root, run `bash scripts/installer.sh init` (or `pwsh scripts/installer.ps1 init`). Creates `.cursor/rules/nexus-hub.mdc` and the Claude permissions stub if absent.
4. To use the v2 code-graph, re-index any repo `nexus-code-search` was tracking: the v1 JSON index is auto-renamed to `<dir>.v1-backup` and a warning is printed; run `python -m nexus_code_search index <repo>` to rebuild against the v2 SQLite + FTS5 schema.
5. Gemini CLI users on the free / Pro / Ultra / GitHub-installed tier should plan their 2026-06-18 transition to Antigravity CLI. v2.2.0 prepares the Antigravity install path; the cutover itself is a Google-side event.

## See also

- [Plan -- `docs/archive/v2/v2.2/plans/codegraph-and-antigravity.md`](plans/codegraph-and-antigravity.md)
- [Source comparison -- `docs/archive/v2/v2.1/comparison-codegraph.md`](../v2.1.0/comparison-codegraph.md)
- [Antigravity CLI probe -- `docs/archive/v2/v2.2/antigravity-cli-probe.md`](antigravity-cli-probe.md)
- [Antigravity CLI commands schema -- `docs/archive/v2/v2.2/antigravity-cli-commands-schema.md`](antigravity-cli-commands-schema.md)
- [Eval baseline -- `docs/archive/v2/v2.2/eval-baseline.md`](eval-baseline.md)
- [Known gaps -- `docs/archive/v2/v2.2/known-gaps.md`](known-gaps.md)
- [Deferred language extractors -- `docs/archive/v2/v2.2/deferred-language-extractors.md`](deferred-language-extractors.md)
- [CHANGELOG `## [2.2.0]`](../../CHANGELOG.md)
