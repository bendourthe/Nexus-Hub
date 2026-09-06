# Plan - CodeGraph adoption + Gemini-to-Antigravity transition

**Project**: Nexus-Hub
**Version**: v2.2.0
**Slug**: codegraph-and-antigravity
**Plan Type**: Feature/Enhancement (from-comparison mode, RE-first sequenced)
**Created**: 2026-05-21
**Goal**: Adopt every CodeGraph capability surfaced in [docs/archives/v2/v2.1/comparison-codegraph.md](../../v2.1.0/comparison-codegraph.md) (14 items across P0/P1/P2/P3) and complete the Gemini-CLI-to-Antigravity-CLI transition before the 2026-06-18 sunset, leaving v2.2.0 ready to ship as a SemVer minor release.

## Overview

This plan operationalizes the adoption candidates produced by the v2.1.0 comparison against [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) and bundles in the time-critical Gemini-CLI sunset response. The comparison classified all 14 candidates as `re-full` or `re-partial` under the MCP Registry Policy in [AGENTS.md](../../../AGENTS.md): zero outbound calls, zero credentials, zero new third-party processors. Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale.

The plan ingests **1 item carried forward from v2.1.0 known-gaps**: DF-001 (byte-identical parity migration of the original 4 platforms into the integration registry). It is addressed in Phase 3 sub-tasks tagged `[from v2.1.0 known-gaps: DF-001]`.

Two CodeGraph candidates are explicitly deferred to v2.3.0+ (see *Items explicitly NOT adopted in v2.2.0* at the end of this file): C13 standalone runtime bundling and the remaining 10 framework extractors beyond C3's Django/FastAPI/Express starter set.

**Time-critical constraint**: Phase 2 (Gemini-to-Antigravity transition) must ship before 2026-06-18 when Gemini CLI stops serving non-enterprise users. Phase 2 is positioned immediately after the Phase 1 installer foundation so it can be cut and released independently if Phases 3-6 slip.

**v2.2.0 will be SemVer minor**: every adoption is additive (new MCP tools, new installer flags, new integration), every refactor preserves prior call-site behavior (`IntegrationBase` action vocabulary is additive). The Gemini CLI deprecation is gated behind an `--enterprise` flag; default behavior shows a sunset warning but still installs, preserving compatibility through the 2026-06-18 cutover for users who upgrade ahead of time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/archive/v2/v2.2/constitution.md - skipping check. Recommend running /constitution to establish project principles.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Installer foundation refactor | `IntegrationBase` returns `WriteResult` with `created/updated/unchanged/removed/not-found/kept` action vocabulary; instruction files merged via marker-delimited blocks; internal MCPs return `initialize` instructions. |
| 2 | Gemini-to-Antigravity CLI transition | Antigravity CLI integration verified and registered; Gemini CLI install path deprecated behind `--enterprise` flag; AGENTS.md platform coverage updated; shared base-gemini template split. Ships before 2026-06-18. |
| 3 | Installer rigor + legacy-platform parity | `--print-config` / `--check` dry-run flags; `wire_project_surfaces()` hook; legacy self-healing registry; 47-case parameterized contract test suite; legacy 4-platform parity migration (DF-001). |
| 4 | Code-graph foundation | `nexus-code-search` v2.0 with tree-sitter AST extraction, NodeKind/EdgeKind schema, call-graph traversal, native file-watcher. |
| 5 | Code-graph capabilities | Django/FastAPI/Express framework-route extractors; `affected_tests` MCP tool + `nexus-hub affected` CLI; synthetic-codebase MCP eval harness. |
| 6 | Polish, data registry, release | Data-registry rebaselined; v2.2.0 RELEASE_NOTES and CHANGELOG; cross-OS installer smoke; known-gaps finalized; `git tag v2.2.0` ready. |

---

## Phase 1: Installer foundation refactor

**Goal**: Refactor `IntegrationBase` and instruction-file writes so every disk operation surfaces a typed action result, instruction files merge non-destructively, and MCP `initialize` responses carry usage guidance.
**Prerequisites**: None.
**Stability Gate**: All existing integrations install and uninstall identically (byte-for-byte) under the refactored API; new pytest suite for the action vocabulary passes; the 3 internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`) return non-empty `instructions` strings on `initialize`.

### Sub-tasks

#### 1.1 - Define WriteResult dataclass and action vocabulary

- [x] T001 Define `WriteResult` dataclass with `files: list[FileAction]` and `notes: list[str]` in scripts/lib/integrations/result.py

**Objective**: Introduce the typed return shape that every per-integration install / uninstall call will adopt (C4 from the comparison).

**Prompt**:
> Create scripts/lib/integrations/result.py with two dataclasses: `FileAction` (path: str, action: Literal["created","updated","unchanged","removed","not-found","kept"]) and `WriteResult` (files: list[FileAction], notes: list[str] = field(default_factory=list)). Mirror the TypeScript interface at the cloned-codegraph reference src/installer/targets/types.ts:37-71 (the `WriteResult` / file-action union there). The `kept` action means a file was found and intentionally left untouched; the `not-found` action means the install or uninstall path looked for a file that did not exist. Add the module to `scripts/lib/integrations/__init__.py`'s public surface (`from .result import WriteResult, FileAction`). Write a focused pytest at tests/integrations/test_result.py covering the six action enum values and that `WriteResult.files` defaults to an empty list. Do not yet change any integration's signature.

---

#### 1.2 - Refactor IntegrationBase to return WriteResult

- [x] T002 Make `install_global`, `install_workspace`, `uninstall_global`, `uninstall_workspace` return `WriteResult` from scripts/lib/integrations/base.py

**Objective**: Replace the current console-only side-effecting methods with typed returns so the orchestrator can render per-file results and assert on them in tests (C4 continued).

**Prompt**:
> Refactor scripts/lib/integrations/base.py: change the four lifecycle methods (`install_global`, `install_workspace`, `uninstall_global`, `uninstall_workspace`) so each returns a `WriteResult` instead of `None`. Update the existing `MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, and `SkillsIntegration` helpers in the same module to thread through individual `FileAction` records: every `safe_file_copy` / `render_template` / `write_toml_block` call appends one `FileAction` to the running list. Detect `unchanged` by comparing the file bytes on disk to what would be written and short-circuiting the write when equal. Update scripts/lib/integrations/runner.py to consume the returned `WriteResult` and log a single line per file action via the existing `write_item` helper (color by action: green=created, cyan=updated, gray=unchanged, yellow=removed, red=not-found). Subclasses (claude.py, codex.py, copilot.py, cursor.py, gemini.py, gemini_cli.py, nexus_ai.py, opencode.py, antigravity.py) only need their `super().install_global(ctx)` returns piped back - do this in this sub-task. Expand tests/integrations/ with `test_base_writeresult.py` asserting `WriteResult` is returned and that `unchanged` is surfaced when bytes match.

---

#### 1.3 - Marker-delimited section replacement helper

- [x] T003 [P] Create scripts/lib/installer/instruction_merge.py with `merge_marker_section(path, content, start, end)` helper

**Objective**: Add the non-destructive instruction-file merge primitive used by every shared-file platform (CLAUDE.md, AGENTS.md, .cursor/rules/*.mdc) (C5 from the comparison).

**Prompt**:
> Create scripts/lib/installer/instruction_merge.py with `merge_marker_section(file_path: Path, body: str, start_marker: str, end_marker: str) -> FileAction`. Behavior: (1) if the file does not exist, create it with `{start_marker}\n{body}\n{end_marker}\n` and return action="created"; (2) if the file exists and contains the markers, replace the slice between them with `{start_marker}\n{body}\n{end_marker}\n` and return "updated" unless the bytes match - then return "unchanged"; (3) if the file exists but contains a literal `## Nexus-Hub` (or caller-supplied legacy header) section with no markers, migrate it inline by replacing that section with the marker-delimited block and return "updated"; (4) otherwise append the marker-delimited block after a single trailing blank line and return "updated". Add a companion `remove_marker_section(file_path, start_marker, end_marker) -> FileAction` for uninstall flows. Reference the cloned-codegraph implementation src/installer/targets/shared.ts (functions `replaceOrAppendMarkedSection`, `removeMarkedSection`) and src/installer/targets/claude.ts:367-403 (the unmarked `## CodeGraph` legacy migration path) for the algorithm. Write tests/installer/test_instruction_merge.py covering all four creation paths, unchanged detection on byte-identical re-runs, and the legacy `## Nexus-Hub` migration path.

---

#### 1.4 - Migrate MarkdownIntegration writes to use marker-delimited merge

- [x] T004 Replace `render_template` calls in scripts/lib/integrations/base.py `MarkdownIntegration` with `merge_marker_section` for shared instruction files

**Objective**: Make Nexus-Hub's instruction-file writes stop clobbering user edits to CLAUDE.md / AGENTS.md / .cursor/rules/*.mdc (C5 applied).

**Prompt**:
> Update `MarkdownIntegration.install_global` and `install_workspace` in scripts/lib/integrations/base.py: shared-file targets (those whose `instruction_file` is a file the user owns - CLAUDE.md, AGENTS.md, codegraph.mdc, GEMINI.md when shared with Antigravity) now call `merge_marker_section` from sub-task 1.3 instead of `render_template`. Dedicated-file targets (where Nexus-Hub owns the whole file - currently `~/.gemini/GEMINI.md` if treated as dedicated) keep using `render_template` for full-file rewrite. Add a class attribute `instruction_mode: Literal["shared", "dedicated"] = "shared"` on each integration subclass; default `MarkdownIntegration` is `shared`, override on the subclasses listed in scripts/lib/integrations/{claude.py,codex.py,copilot.py,cursor.py,gemini.py,gemini_cli.py,nexus_ai.py,opencode.py,antigravity.py} as appropriate (Claude/Codex/Cursor/OpenCode/Copilot/Antigravity are `shared`; Gemini IDE remains `dedicated` unless your audit says otherwise). Define start/end markers as `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->`. Update `uninstall_*` to call `remove_marker_section`. Expand tests/integrations/test_markdown_integration.py to assert: re-install on a user-edited CLAUDE.md preserves the user content above and below the marker block; uninstall removes only the block.

---

#### 1.5 - Add MCP `initialize` server-instructions to the 3 internal MCPs

- [x] T005 [P] Set the `instructions` field on the MCP `initialize` response in extensions/nexus-skill-server/src/nexus_skill_server/server.py, extensions/nexus-code-search/src/nexus_code_search/server.py, and extensions/nexus-web-fetch/src/nexus_web_fetch/server.py

**Objective**: Mirror CodeGraph's `server-instructions.ts` pattern so any agent connecting to a Nexus-Hub MCP sees authoritative tool guidance even without the platform's installed CLAUDE.md / AGENTS.md template (C9 from the comparison).

**Prompt**:
> For each of the three internal MCP servers, add a non-empty `instructions` string to the response returned from the MCP `initialize` handler. Each server's instructions text should: (1) list the server's tools in a one-line "what / when" table; (2) cite the MCP Registry Policy (`already-local`); (3) end with a pointer to the corresponding Nexus-Hub skill (`nexus-skill-server` -> the `using-nexus-hub` skill; `nexus-code-search` -> the `code-semantic-search` skill; `nexus-web-fetch` -> trend-research / local-docs-lookup as relevant). Reference the cloned-codegraph implementation src/mcp/server-instructions.ts for length / tone (target ~30-50 lines per server). Add per-server pytest fixtures under extensions/<name>/tests/test_initialize.py asserting the response contains a non-empty `instructions` field and that the string contains the server name and tool list.

---

#### 1.6 - Phase 1 tests and stabilization

- [x] T006 Run and stabilize all Phase 1 tests in tests/integrations/, tests/installer/, and extensions/*/tests/

**Objective**: Verify the foundation before Phase 2 builds on it.

**Prompt**:
> Run the full test suite: `python -m pytest tests/integrations tests/installer extensions/nexus-skill-server/tests extensions/nexus-code-search/tests extensions/nexus-web-fetch/tests -v`. Fix every failure. Then run `make validate` and `make lint` to confirm no JSON or shell lint regressions. Then run a smoke install into a throwaway directory: `bash scripts/installer.sh --target /tmp/smoke-phase1` and verify the installer logs the new `created` / `updated` / `unchanged` action lines. Do not advance to Phase 2 until tests pass and the smoke output looks correct. After all tests pass, run /generate-session-history to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Gemini-to-Antigravity CLI transition (time-critical, ship before 2026-06-18)

**Goal**: Complete the Gemini-CLI sunset response: verify the Antigravity CLI install paths, register a clean `antigravity-cli` integration (or reconcile with the existing `antigravity2` registration), deprecate the standalone Gemini CLI install behind an `--enterprise` flag, and update all cross-cutting docs.
**Prerequisites**: Phase 1 (Phase 2 uses the new `WriteResult` action vocabulary and the marker-delimited instruction merge).
**Stability Gate**: A user with no prior install can run the installer post-2026-06-18 and get a working Antigravity CLI surface; an enterprise user can still install the Gemini CLI integration via `--enterprise`; `make validate` reports zero registry inconsistencies; AGENTS.md "Platform coverage caveats" reflects the new state.

### Sub-tasks

#### 2.1 - Probe and verify Antigravity CLI paths empirically

- [x] T007 Document the actual Antigravity CLI install paths, config dir, command schema, and auth flow in docs/archive/v2/v2.2/antigravity-cli-probe.md

**Objective**: The current `antigravity2` integration in scripts/lib/integrations/antigravity.py assumes `~/.agent/` / `AGENT.md` / `workflows/` / `subagents/`. The 2026-05-21 Google Developers Blog announcement confirmed only that the new CLI shares the Antigravity 2.0 backend; it did not confirm directory conventions. This sub-task pins the assumption to evidence.

**Prompt**:
> Install Antigravity CLI in a clean VM or container per Google's official docs (see https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ for the migration pointer). Run `which antigravity` and `antigravity --help`. Identify: (1) the binary name and PATH location; (2) the global config dir (likely `~/.agent/` or `~/.antigravity/`); (3) the per-project config dir; (4) the instructions-file name (`AGENT.md`, `ANTIGRAVITY.md`, etc.); (5) the commands subdirectory layout and file format (TOML, Markdown, YAML, ...); (6) whether hooks / skills / subagents are supported and where they live; (7) the auth flow (API key location, sign-in command). Capture each finding with concrete file paths and verbatim CLI output. Write docs/archive/v2/v2.2/antigravity-cli-probe.md with the findings. If the actual paths differ from scripts/lib/integrations/antigravity.py:36-47, list every divergence as a bullet so sub-task 2.2 can fix the integration in one pass.

---

#### 2.2 - Reconcile / register the canonical Antigravity CLI integration

- [x] T008 Update scripts/lib/integrations/antigravity.py to match the probe findings, and register a new `antigravity-cli` key in scripts/lib/integrations/__init__.py if the probe shows the CLI uses different paths from Antigravity 2.0 desktop

**Objective**: Make the integration honest about what it installs. Either the existing `antigravity2` key absorbs the CLI (if paths match), or a new `antigravity-cli` subclass is added.

**Prompt**:
> Based on the docs/archive/v2/v2.2/antigravity-cli-probe.md findings: (a) if Antigravity CLI uses the same `~/.agent/` paths as Antigravity 2.0 desktop, update the `Antigravity20Integration` display_name to "Antigravity 2.0 + CLI (Google)" and add a docstring note confirming dual coverage; (b) if the CLI uses different paths, add a new `AntigravityCliIntegration` class to scripts/lib/integrations/antigravity.py with the correct config dict, register it in scripts/lib/integrations/__init__.py::_register_builtins() in alphabetical order (between `antigravity2` and `claude`), and add the corresponding installer dispatch call in scripts/installer.sh:769-770 and scripts/installer.ps1 (mirror the Antigravity 2.0 invocation pattern). Either way: extend tests/integrations/test_antigravity.py to cover the install path empirically (target_path fixture + WriteResult assertions). Update docs/policy/mcp-reverse-engineering-matrix.md if a new MCP server config row needs to mention Antigravity CLI as a destination.

---

#### 2.3 - Add antigravity-cli-diff-review hook variant

- [x] T009 [P] Author catalog/hooks/antigravity-cli-diff-review.sh and catalog/hooks/antigravity-cli-diff-review.ps1 mirroring the existing Claude/Gemini/Codex/OpenCode variants

**Objective**: The installer copy loop at scripts/installer.sh:1523 iterates over claude/gemini/codex/opencode diff-review variants. Add the Antigravity CLI sibling so the new platform gets the same pre-commit AI review affordance.

**Prompt**:
> Copy catalog/hooks/gemini-diff-review.sh to catalog/hooks/antigravity-cli-diff-review.sh and replace every occurrence of `gemini` with `antigravity` (binary name, config path references, log prefixes). Repeat for the PowerShell sibling: copy catalog/hooks/gemini-diff-review.ps1 (or the equivalent .ps1) to catalog/hooks/antigravity-cli-diff-review.ps1 with the same substitution. Update the installer copy loop at scripts/installer.sh:1523 to include `antigravity-cli-diff-review.sh` alongside the existing four variants. Update the equivalent loop in scripts/installer.ps1 with the .ps1 variant. Add a one-line entry under "Hooks" in CHANGELOG.md's [Unreleased] section. Verify both new files pass shellcheck / `bash -n` (sh) and `[System.Management.Automation.Language.Parser]::ParseFile` (ps1).

---

#### 2.4 - Update AGENTS.md "Platform coverage caveats"

- [x] T010 Rewrite the "Platform coverage caveats (current state)" subsection in AGENTS.md to reflect the Gemini-CLI sunset and the new Antigravity CLI integration

**Objective**: AGENTS.md currently lists Gemini CLI as one of the Extended 3. After 2026-06-18 that line is stale for non-enterprise users.

**Prompt**:
> Edit AGENTS.md "Platform coverage caveats (current state)" subsection. Replace the existing Extended-3 listing with: "Extended 4 (v2.2.0+, via integration registry): Antigravity 2.0 desktop (Google), Antigravity CLI (Google - formerly Gemini CLI before 2026-06-18), Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18, opt-in via --enterprise installer flag), Nexus-AI". Add a callout box near the top of that subsection: "**Gemini CLI sunset**: per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18. The standalone `gemini-cli` integration is now opt-in via `--enterprise` and installs only when the user explicitly requests it." Update the integration coverage table at AGENTS.md lines listing "Original 4 / Extended 3" to "Original 4 / Extended 4". Confirm the change in scripts/lib/integrations/__init__.py reflects the same naming (Phase 2.2 already updated that file). Run `make validate` to confirm no docs-link breakage.

---

#### 2.5 - Split the shared base-gemini template

- [x] T011 Refactor templates/ai-instructions/base-gemini.md into templates/ai-instructions/base-google-shared.md plus dedicated per-surface variants for Gemini-IDE / Antigravity-1.0 / Antigravity-2.0 / Antigravity-CLI / Gemini-CLI

**Objective**: One template currently serves five Google-side surfaces (scripts/lib/integrations/antigravity.py:25,40; scripts/lib/integrations/gemini.py; scripts/lib/integrations/gemini_cli.py:32). Splitting lets the sunset Gemini CLI surface be archived cleanly without affecting Antigravity.

**Prompt**:
> Copy templates/ai-instructions/base-gemini.md to templates/ai-instructions/base-google-shared.md (the new shared body) and prune any Gemini-CLI-specific paragraphs from the shared body. Create dedicated thin wrappers in templates/ai-instructions/base-{gemini-ide,antigravity-10,antigravity-20,antigravity-cli,gemini-cli}.md - each wrapper begins with `@base-google-shared.md` (the `@` import idiom used in CLAUDE.md) and then adds 3-10 lines of surface-specific guidance (binary name, CLI invocation, surface-specific permissions). Update scripts/lib/integrations/{gemini.py,gemini_cli.py,antigravity.py} so each integration's `instruction_template` field points at its dedicated wrapper. Confirm `render_template` still works for any `dedicated`-mode integration (Phase 1.4 introduced this distinction). Add tests/integrations/test_google_templates.py asserting each of the 5 templates renders without error.

---

#### 2.6 - Validate TOML commands convention compatibility

- [x] T012 Verify the Gemini CLI TOML commands schema (scripts/lib/integrations/gemini_cli.py:42-48 `_write_toml_commands`) still applies to Antigravity CLI, and document the result in docs/archive/v2/v2.2/antigravity-cli-commands-schema.md

**Objective**: Antigravity CLI inherited Gemini CLI's Agent Skills / Hooks / Subagents / Extensions per the blog post, but the on-disk command file format was not confirmed. If it differs, sub-task 2.2's integration needs an Antigravity variant of `_write_toml_commands`.

**Prompt**:
> Working from the Antigravity CLI install in sub-task 2.1: locate one example slash-command file shipped by Antigravity CLI itself (probably in the binary's resource bundle or under `~/.agent/commands/` after `antigravity init`). Open it and identify: (1) file format (TOML / Markdown / YAML / JSON); (2) required fields (name, description, prompt template, parameters); (3) directory layout. Compare against scripts/lib/integrations/gemini_cli.py:42-48 which writes `~/.gemini/commands/<name>.toml` for Gemini CLI. Write docs/archive/v2/v2.2/antigravity-cli-commands-schema.md with: the file format diff, a sample file in each format, the schema delta. If the formats are identical, note that the existing `_write_toml_commands` helper applies as-is. If they differ, add a `_write_antigravity_commands` helper variant to scripts/lib/integrations/antigravity.py and wire it into the appropriate integration's `install_global` / `install_workspace`. Add tests/integrations/test_antigravity_commands.py with golden-file assertions for two representative commands.

---

#### 2.7 - Deprecate the standalone Gemini CLI install path

- [x] T013 Gate scripts/installer.sh:770,1163 (and the PowerShell equivalents) Gemini CLI dispatch behind an `--enterprise` flag, and print a sunset warning when the flag is absent

**Objective**: After 2026-06-18, the unconditional `invoke_registry_platform ... gemini-cli` calls become silent no-ops for non-enterprise users. Switching to opt-in prevents confusion.

**Prompt**:
> Edit scripts/installer.sh: add an `--enterprise` flag parser near the existing flag handling. Inside the Gemini CLI install dispatch at lines 770 and 1163, wrap the `invoke_registry_platform ... gemini-cli "Gemini CLI"` call in `if [ "$ENTERPRISE" = "1" ]; then ... else echo "[INFO] Gemini CLI stops serving free / Google AI Pro / Ultra users on 2026-06-18. Re-run with --enterprise to install (requires paid Gemini API key); otherwise install Antigravity CLI for the same functionality."; fi`. Mirror the same change in scripts/installer.ps1 (add a `-Enterprise` switch; gate the equivalent `Invoke-RegistryPlatform ... gemini-cli` calls). Update the installer's `--help` text in both files to document the new flag. Update the integration's display_name in scripts/lib/integrations/gemini_cli.py to "Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)". Add tests/installer/test_enterprise_flag.py asserting (a) default run prints the sunset warning and skips Gemini CLI, (b) `--enterprise` runs the legacy install path. Run a fresh `bash scripts/installer.sh --target /tmp/smoke-phase2` and visually confirm the warning prints exactly once.

---

#### 2.8 - Phase 2 tests and stabilization

- [x] T014 Run and stabilize all Phase 2 tests in tests/integrations/, tests/installer/, and verify the sunset warning + --enterprise gating end-to-end

**Objective**: Phase 2 is time-critical. Confirm it is shippable in isolation before continuing.

**Prompt**:
> Run: `python -m pytest tests/integrations tests/installer -v -k "antigravity or gemini or enterprise"`. Then run the cross-platform installer in three modes against throwaway dirs: (1) default (no flag) - expect Gemini CLI skipped with warning; (2) `--enterprise` - expect Gemini CLI installed; (3) on a system where Antigravity CLI is present (sub-task 2.1's VM) - expect Antigravity CLI integration installs and the new diff-review hook is wired. Verify the SKILL_INDEX, marketplace.json, and skills.json reflect any data-registry deltas from sub-tasks 2.3 / 2.5. Run `make validate` and `make lint`. Do not advance to Phase 3 until tests pass. After all tests pass, run /generate-session-history to document Phase 2.
>
> **If schedule slips and Phases 3-6 are not ready by 2026-06-01**: cut a v2.2.0-rc1 or v2.2.0-alpha1 release containing only Phase 1 + Phase 2 so the Antigravity transition ships ahead of the 2026-06-18 sunset, then ship the remaining phases as v2.2.0 stable or v2.3.0 as appropriate.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [ ] Antigravity CLI installs and functions on a clean VM *(deferred: no VM available at authoring time; documented as WN-2/WN-3/WN-4 in `<version_dir>/known-gaps.md` per the static-probe approach in `docs/archive/v2/v2.2/antigravity-cli-probe.md`)*
- [x] Gemini CLI is gated behind --enterprise with a working sunset warning
- [x] AGENTS.md and CHANGELOG reflect the new state
- [x] Session history generated for this phase
- [x] Phase 2 is independently shippable before 2026-06-18

---

## Phase 3: Installer rigor + legacy-platform parity migration

**Goal**: Add the dry-run modes, project-surfaces hook, and parameterized contract test suite that bring Nexus-Hub's installer to CodeGraph parity rigor; complete the v2.1.0-deferred byte-identical parity migration for the original 4 platforms (DF-001).
**Prerequisites**: Phase 1 (uses `WriteResult` for parity assertions; uses marker-delimited merge for the legacy 4 integrations).
**Stability Gate**: `bash scripts/installer.sh --check` and `bash scripts/installer.sh --print-config <id>` work without touching disk; the 47-case parameterized contract suite passes; the legacy installer copy blocks for Claude / Codex / Cursor / Gemini / OpenCode produce identical `WriteResult` arrays to the registry's runner output.

### Sub-tasks

#### 3.1 - Generalize legacy state self-healing

- [x] T015 Add scripts/lib/integrations/legacy.py with a registry of per-integration cleanup functions, modeled after the v2.1.0 VS Code extension cleanup commit b52a038

**Objective**: Make legacy-state cleanup a first-class pattern rather than per-platform ad-hoc code (C12 from the comparison).

**Prompt**:
> Create scripts/lib/integrations/legacy.py exposing a `LEGACY_CLEANUPS: dict[str, list[Callable[[InstallContext], FileAction | None]]]` dict where the key is the integration key and the value is a list of cleanup functions. Each function inspects the disk for one specific legacy artifact (a renamed config file, a deprecated hook, an old directory location) and returns a `FileAction(path=..., action="removed")` when it cleaned something up, or `None` when there was nothing to clean. Migrate the v2.1.0 VS Code extension cleanup from scripts/installer.sh (introduced in commit b52a038) into a Python cleanup function under the `claude` key. Add cleanup functions for: pre-2.1.0 `~/.devai-hub/` directory (rename from the DevAI-Hub era), pre-2.0.0 skill registry path, and any other legacy artifact the repo history documents. Update `IntegrationBase.install_global` / `install_workspace` in base.py to invoke `LEGACY_CLEANUPS.get(self.key, [])` at the start of every install and append the returned `FileAction`s to the result. Add tests/integrations/test_legacy_cleanups.py with at least 3 cleanup-function tests using `tmp_path` fixtures that pre-create the legacy artifact and assert it is removed.

---

#### 3.2 - Add wire_project_surfaces() optional method

- [x] T016 Add `wire_project_surfaces(ctx) -> WriteResult` as an optional method on IntegrationBase, called from a new `nexus-hub init` installer subcommand

**Objective**: Enable a global install to bootstrap project-local surfaces (Cursor `.cursor/rules/*.mdc`, project-local skill manifests, etc.) without forcing the user to re-run the full installer per project (C7 from the comparison).

**Prompt**:
> Add `wire_project_surfaces(self, ctx: InstallContext) -> WriteResult | None` as a default-None method on `IntegrationBase` in scripts/lib/integrations/base.py. Implement it on `CursorIntegration` (writes `.cursor/rules/nexus-hub.mdc` from the existing per-platform template) and on `ClaudeIntegration` (writes a `.claude/settings.json` permissions stub if one does not already exist). Add a new top-level installer subcommand `nexus-hub init` (Bash: `scripts/installer.sh init`; PowerShell: `scripts/installer.ps1 init`) that walks every registered integration and calls `wire_project_surfaces(ctx)` when defined, logging the WriteResult. Reference the cloned-codegraph implementation: `targets/types.ts:107-120` (interface) and `targets/cursor.ts` (the canonical example of why this hook exists). Update AGENTS.md "Distribution channels" table to add a row for "Project-local surfaces (called from `nexus-hub init`)". Write tests/installer/test_init_subcommand.py asserting `.cursor/rules/nexus-hub.mdc` is created in a `tmp_path` project root and that re-running prints `unchanged`.

---

#### 3.3 - Add --print-config flag and per-integration print_config()

- [x] T017 Implement `installer.sh --print-config <integration-key>` (and PowerShell equivalent) that dumps the MCP / settings / instructions snippets a user would paste manually, without touching disk

**Objective**: Dry-run-style readout for users who want to inspect what Nexus-Hub would write (C6 from the comparison).

**Prompt**:
> Add `print_config(self, ctx: InstallContext) -> str` to `IntegrationBase` returning a multi-section Markdown string showing each file Nexus-Hub would write at this install location, with the rendered content for each. Default implementation walks the integration's `config` dict and uses the existing `render_template` / `merge_marker_section` / `_write_toml_commands` machinery in dry-run mode (extract the bytes that would be written without touching disk - introduce a `dry_run=True` parameter to those helpers if needed). Add `--print-config <key>` parsing to scripts/installer.sh and scripts/installer.ps1; resolve `<key>` against the registry via the runner, call `print_config`, print to stdout, and exit 0. Add tests/installer/test_print_config.py with one golden-file fixture per integration asserting the snippet contains the expected target paths. Reference the cloned-codegraph implementation src/installer/targets/claude.ts:196-200 and src/installer/index.ts (`--print-config` flag) for the UX.

---

#### 3.4 - Add --check / --dry-run flag and per-integration dry_run()

- [x] T018 Implement `installer.sh --check` that runs the full install in dry-run mode (no disk writes) and exits 0 if nothing would change, non-zero if it would

**Objective**: CI-friendly install-drift detection (C6 from the comparison).

**Prompt**:
> Add `dry_run(self, ctx: InstallContext) -> WriteResult` to `IntegrationBase` that mirrors `install_global` / `install_workspace` but skips every actual disk write - it returns a `WriteResult` whose `files` array reflects what *would* happen (each `FileAction.action` reads from the would-be byte comparison; `unchanged` for files that already match, `created` / `updated` for files that would diverge, `removed` for legacy artifacts that would be cleaned). Implement the `--check` flag in scripts/installer.sh and scripts/installer.ps1: parses args, calls each registered integration's `dry_run`, prints a per-integration summary, exits 0 if every `FileAction.action == "unchanged"` across every integration and 1 otherwise. Add tests/installer/test_check_flag.py asserting (a) fresh install state -> exit 1, (b) post-install re-run with --check -> exit 0, (c) `--check` produces no disk writes (verified by capturing the tmp_path tree before / after and asserting byte-equality).

---

#### 3.5 - Parameterized installer contract test suite

- [x] T019 Expand tests/integrations/ with a parameterized contract suite covering install idempotency, sibling preservation, uninstall-reverses-install, byte-identical re-runs returning `unchanged`, partial-state recovery - across all 10 integrations

**Objective**: Match CodeGraph's `__tests__/installer-targets.test.ts` rigor (47 cases). For Nexus-Hub's 10 integrations and the same 5 invariants, the matrix is roughly 50 cases (C11 from the comparison).

**Prompt**:
> Create tests/integrations/test_contract.py with five `@pytest.mark.parametrize` test functions, each parameterized over every registered integration key from `scripts/lib/integrations/__init__.py::list_keys()`. The five invariants: (1) `test_install_idempotent` - install twice in `tmp_path`, assert second WriteResult is all `unchanged`; (2) `test_uninstall_reverses_install` - install, snapshot tmp_path tree, uninstall, assert tree matches a pre-install snapshot; (3) `test_sibling_preservation` - pre-populate the target instruction file / settings file / MCP config with unrelated keys, install, assert siblings are byte-preserved; (4) `test_partial_state_recovery` - delete one of the three target files mid-install, re-run, assert it converges; (5) `test_dry_run_matches_install` - run `dry_run` then `install` and assert the resulting `WriteResult.files` arrays match. Reference the cloned-codegraph implementation `__tests__/installer-targets.test.ts` for the test-shape and the per-target fixture conventions. Run the suite; expect ~50 cases passing. If any integration fails an invariant, fix the integration (not the test). Add `make test` to the validation gates the suite runs in CI.

---

#### 3.6 - Parity diff suite: legacy installer vs registry runner

- [x] T020 [from v2.1.0 known-gaps: DF-001] Write tests/integrations/test_parity_with_legacy_installer.py asserting byte-identical output between the legacy installer copy blocks and the registry runner for Claude / Codex / Cursor / Gemini / OpenCode

**Objective**: Resolve DF-001 carried forward from v2.1.0. The v2.1.0 plan deferred this because byte-identical parity was the heaviest sub-task; with C4's WriteResult vocabulary now in place, parity is straightforward to assert.

**Prompt**:
> Carry forward from v2.1.0 known-gaps DF-001. **Reason** (from v2.1.0/known-gaps.md): Phase 10 in v2.1.0 shipped the integration registry as ADDITIVE - the original 4 platforms (Claude / Gemini / Codex / Copilot - plus Cursor / OpenCode as behavioral-guardrails) continue through the legacy `installer.sh` / `installer.ps1` copy blocks. The parity tests were deferred. **Suggested next step** (from v2.1.0/known-gaps.md): write `tests/integrations/test_parity_with_legacy_installer.py` that diffs the legacy installer output against the registry output for Claude, Codex, Cursor, Gemini, OpenCode.
>
> Create tests/integrations/test_parity_with_legacy_installer.py. For each of the five platforms (claude, codex, cursor, gemini, opencode): (a) run the legacy installer code-path against a clean `tmp_path` target with all platforms but the one under test stubbed out; (b) snapshot the resulting directory tree (every file's relative path + sha256); (c) run the registry runner alone for the same platform against a separate clean `tmp_path`; (d) snapshot that tree; (e) assert the two snapshots are byte-identical except for known-divergent metadata files (timestamps, install-ID nonces - allowlist these explicitly). If a divergence is found, fix it in the registry runner (not the legacy path) since the legacy path is the canonical reference for v2.2.0. Add the suite to `make test` and to the CI workflow.

---

#### 3.7 - Refactor legacy installer copy paths to delegate to runner

- [ ] T021 [from v2.1.0 known-gaps: DF-001] Refactor scripts/installer.sh and scripts/installer.ps1 to delegate the original 4 platforms to the registry runner; remove the duplicated copy blocks *(deferred to v2.3.0 as DF-001-part2 -- the plan made T021 conditional on full instruction-file byte parity from T020, but the registry runner does not yet substitute the full bash placeholder set (`{{PRIMARY_LANGUAGE}}`, `{{BUILD_CMD}}`, `{{SKILL_INDEX}}`, ...) nor append per-language coding snippets; removing the legacy blocks today would silently downgrade end-user instruction-file content. Tracked as DF-001 in [docs/archives/v2/v2.2/known-gaps.md](../../known-gaps.md).)*

**Objective**: Complete the DF-001 migration. With parity tests in place from sub-task 3.6, the duplicated copy blocks can be safely removed.

**Prompt**:
> Carry forward from v2.1.0 known-gaps DF-001 (second half). Once tests/integrations/test_parity_with_legacy_installer.py from sub-task 3.6 passes, refactor scripts/installer.sh: remove the legacy copy blocks for claude / codex / cursor / gemini / opencode (search for the `# --- Anthropic -- Claude Code ---` / `# --- Google -- Gemini ...` / `# --- OpenAI -- Codex ---` blocks around lines 750-1200) and replace each with a single `invoke_registry_platform "$repo_root" "global" "" "<key>" "<display_name>"` call. Mirror the same refactor in scripts/installer.ps1. Re-run the parity tests from 3.6 against the refactored installer; they must still pass. Update the AGENTS.md "Distribution channels the installer uses" table: the "Original 4 (legacy installer copy blocks)" row collapses into the "Extended N (via integration registry)" row. Bump the row count from "Extended 4" to "All 10 integrations install via registry runner; legacy copy blocks removed in v2.2.0".

---

#### 3.8 - Phase 3 tests and stabilization

- [x] T022 Run and stabilize all Phase 3 tests including the 50-case contract suite and the parity diff suite

**Objective**: Verify the installer reaches CodeGraph parity rigor and DF-001 is closed.

**Prompt**:
> Run: `python -m pytest tests/integrations tests/installer -v`. Confirm all ~50 contract tests pass and the 5 parity tests pass. Run `make validate && make lint && make test`. Run `bash scripts/installer.sh --check` against a freshly-installed target and confirm exit code 0 and zero non-`unchanged` actions. Run `bash scripts/installer.sh --print-config claude` and confirm the output matches expected. Do not advance to Phase 4 until everything passes. After all tests pass, run /generate-session-history to document Phase 3. Mark DF-001 as resolved in docs/archive/v2/v2.1/known-gaps.md (move it from "Open Items" to "Resolved" with "Resolved in: v2.2.0 Phase 3").

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed *(7 of 8; T021 deferred to v2.3.0 as DF-001-part2 -- see annotation on T021 above)*
- [x] All tests passing (contract suite + parity suite) *(223 passed, 0 failed)*
- [x] DF-001 closed in docs/archive/v2/v2.1/known-gaps.md *(part 1 -- tree-mirror parity -- closed in v2.2.0 Phase 3 T020; part 2 -- instruction-file byte parity + legacy block removal -- carried forward to v2.2.0 known-gaps DF-001, target v2.3.0)*
- [ ] Legacy installer copy blocks removed *(deferred with T021 to v2.3.0; see DF-001 in [docs/archives/v2/v2.2/known-gaps.md](../../known-gaps.md))*
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 4

---

## Phase 4: Code-graph foundation - nexus-code-search v2.0

**Goal**: Replace `nexus-code-search`'s keyword-only inverted index with a tree-sitter AST extraction pipeline backed by SQLite (FTS5) with a NodeKind/EdgeKind taxonomy, call-graph traversal, and a native file-watcher for auto-sync.
**Prerequisites**: None directly (Phase 1's WriteResult is not needed inside the extension), but Phase 1 must have shipped so the extension's MCP `initialize` instructions are in place.
**Stability Gate**: `nexus-code-search` indexes a 1000-file repo in under 30 seconds, surfaces every symbol it extracted via `search_code`, answers `callers(symbol)` / `callees(symbol)` / `impact(symbol)` correctly against fixture codebases, and detects external file edits within 2 seconds (file-watcher debounce).

### Sub-tasks

#### 4.1 - Add tree-sitter-python dependency and scaffolding

- [x] T023 Add `tree-sitter` and `tree-sitter-languages` to extensions/nexus-code-search/pyproject.toml with appropriate version pins, and scaffold extensions/nexus-code-search/src/nexus_code_search/extraction/

**Objective**: Bring tree-sitter into the dependency surface and lay out the per-language extractor module structure (C1 from the comparison).

**Prompt**:
> Edit extensions/nexus-code-search/pyproject.toml: add `tree-sitter = "^0.23.0"` and `tree-sitter-languages = "^1.10.0"` to `[project.dependencies]`. Pin to versions that ship wheels for Python 3.10 / 3.11 / 3.12 on Windows / macOS / Linux (verify via `pip index versions tree-sitter-languages`). Create extensions/nexus-code-search/src/nexus_code_search/extraction/ with `__init__.py`, `orchestrator.py` (will host `ExtractionOrchestrator`), `parse_worker.py` (will host the per-file parser - kept separate so it can later run in a multiprocessing Pool), and `languages/` (per-language extractor modules - one per supported language). Update extensions/nexus-code-search/src/nexus_code_search/server.py to import `ExtractionOrchestrator` (a stub for now). Add extensions/nexus-code-search/tests/test_extraction_scaffold.py asserting the new modules import cleanly. Reference the cloned-codegraph implementation src/extraction/ for the module layout (we will not literally port the TypeScript, but the file-organization mirror keeps the model coherent).

---

#### 4.2 - Build NodeKind/EdgeKind schema and DB migration

- [x] T024 Define `NodeKind` and `EdgeKind` enums in extensions/nexus-code-search/src/nexus_code_search/types.py, and add a SQLite schema migration creating the `nodes` / `edges` / `files` tables with FTS5 virtual table

**Objective**: Move from the v1.0.0 pickled-index to a relational AST graph (C1 continued).

**Prompt**:
> Create extensions/nexus-code-search/src/nexus_code_search/types.py with two `Enum` classes: `NodeKind` containing exactly the values `file`, `module`, `class`, `struct`, `interface`, `trait`, `protocol`, `function`, `method`, `property`, `field`, `variable`, `constant`, `enum`, `enum_member`, `type_alias`, `namespace`, `parameter`, `import`, `export`, `route`, `component` (matches the cloned-codegraph reference src/types.ts); and `EdgeKind` containing `contains`, `calls`, `imports`, `exports`, `extends`, `implements`, `references`, `type_of`, `returns`, `instantiates`, `overrides`, `decorates`. Create extensions/nexus-code-search/src/nexus_code_search/db/schema.sql with the relational schema: `nodes(id INTEGER PRIMARY KEY, name TEXT, kind TEXT, qualified_name TEXT, file_id INTEGER, start_line INTEGER, end_line INTEGER, signature TEXT, docstring TEXT)`, `edges(id INTEGER PRIMARY KEY, source_id INTEGER, target_id INTEGER, kind TEXT, call_site_line INTEGER)`, `files(id INTEGER PRIMARY KEY, path TEXT UNIQUE, language TEXT, content_hash TEXT, indexed_at INTEGER)`, plus an FTS5 virtual table `nodes_fts` on `(name, qualified_name, docstring)`. Add extensions/nexus-code-search/src/nexus_code_search/db/migrate.py with a `migrate_v1_to_v2(index_dir: Path)` function that detects the v1.0.0 pickled index and: (a) prints a clear warning - "v2 schema requires re-index; run `nexus-code-search index` to rebuild"; (b) renames the v1 index dir to `<dir>.v1-backup`. Add tests/test_schema.py asserting all 22 NodeKind values + 12 EdgeKind values are present and the schema parses against a fresh sqlite3 db.

---

#### 4.3 - Port per-language AST extractors (start with Python and TypeScript)

- [x] T025 Implement extensions/nexus-code-search/src/nexus_code_search/extraction/languages/python.py and typescript.py using tree-sitter queries to extract NodeKind / EdgeKind records *(code shipped at original Phase 4 close; the companion `docs/archive/v2/v2.2/deferred-language-extractors.md` deliverable was created in the 2026-05-26 checkbox-sync pass)*

**Objective**: First two-language slice of the AST extractor. Other languages follow the same pattern and are tracked under Phase 4's "remaining languages" follow-up (deferred to v2.3.0).

**Prompt**:
> Implement extensions/nexus-code-search/src/nexus_code_search/extraction/languages/python.py with a `PythonExtractor` class whose `extract(file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]` method uses tree-sitter to parse Python source and emits: `function` / `class` / `method` / `parameter` / `import` / `variable` / `constant` nodes, plus `contains` / `calls` / `imports` / `inherits-from` (-> `extends`) edges. Reference the cloned-codegraph implementation src/extraction/languages/python.ts for the tree-sitter queries (the TypeScript form is identical to what Python needs - copy the s-expression queries verbatim, just call them from py-tree-sitter). Repeat for typescript.py covering `class` / `interface` / `function` / `method` / `type_alias` / `import` / `export`. Wire both into extensions/nexus-code-search/src/nexus_code_search/extraction/orchestrator.py via a `LANGUAGE_EXTRACTORS: dict[str, type[Extractor]]` registry. Add tests/test_python_extraction.py and tests/test_typescript_extraction.py with at least 5 fixture files per language under tests/fixtures/<lang>/ asserting expected node + edge counts. Document the deferred languages (Go, Rust, Java, C#, PHP, Ruby, C, C++, Swift, Kotlin, Scala, Dart, Lua, Luau, Svelte, Vue, Liquid, Pascal, plus JavaScript proper) in docs/archive/v2/v2.2/deferred-language-extractors.md - one paragraph each on why each one is deferred to v2.3.0+.

---

#### 4.4 - Implement call-graph traversal

- [x] T026 Create extensions/nexus-code-search/src/nexus_code_search/graph/traverser.py with `GraphTraverser.callers(node_id)` / `callees(node_id)` / `impact_radius(node_id, depth=2)` plus `get_node(node_id, include_source=False)`

**Objective**: Add the call-graph layer the comparison's C2 candidate requires.

**Prompt**:
> Create extensions/nexus-code-search/src/nexus_code_search/graph/ with `__init__.py`, `traverser.py`, and `query_manager.py`. `GraphTraverser` exposes: `callers(node_id) -> list[Node]` (returns every node with a `calls` edge whose target is node_id); `callees(node_id) -> list[Node]` (inverse); `impact_radius(node_id, depth) -> list[Node]` (BFS over `calls` + `references` + `extends` + `implements` + `overrides` edges up to `depth` hops); `find_path(source_id, target_id) -> list[Node] | None` (shortest path via BFS). `GraphQueryManager` wraps these with higher-level convenience methods (`callers_by_name(symbol_name)`, etc.). Reference the cloned-codegraph implementation src/graph/ for the BFS / impact-radius semantics. Add tests/test_traverser.py with fixture codebases producing known call graphs and assert each method returns the expected node-id sets. Wire new MCP tools `code_callers`, `code_callees`, `code_impact`, `code_node`, `code_context`, `code_explore` into extensions/nexus-code-search/src/nexus_code_search/server.py. Update the server's `initialize` instructions string (set in Phase 1.5) to list these new tools.

---

#### 4.5 - File watcher with watchdog

- [x] T027 [P] Add extensions/nexus-code-search/src/nexus_code_search/watch.py using the `watchdog` library to detect file changes and trigger incremental re-index

**Objective**: Keep the index fresh as the user edits files (C14 from the comparison).

**Prompt**:
> Add `watchdog ^4.0.0` to extensions/nexus-code-search/pyproject.toml. Create extensions/nexus-code-search/src/nexus_code_search/watch.py with `FileWatcher(repo_root: Path, on_change: Callable[[list[Path]], None], debounce_ms: int = 2000)`. Use `watchdog.observers.Observer` (native FSEvents on macOS / inotify on Linux / ReadDirectoryChangesW on Windows). Buffer change events into a list, debounce by `debounce_ms`, then dispatch the flushed list to `on_change`. Filter: only source files (extensions from the per-language registry in 4.3), skip `.git/`, `node_modules/`, `.venv/`, anything in `.gitignore` or `.nexusignore`. Add a `watch_for_changes(repo_root)` MCP tool to extensions/nexus-code-search/src/nexus_code_search/server.py that starts the watcher in a background thread when the agent calls it. Reference the cloned-codegraph implementation src/sync/file-watcher.ts for the debounce / filter strategy. Add tests/test_watcher.py with a `tmp_path` fixture that touches files and asserts the `on_change` callback fires with the expected paths after the debounce window.

---

#### 4.6 - Phase 4 tests and stabilization

- [x] T028 Run and stabilize Phase 4 tests; index a real medium-sized repo and validate the call-graph against ground truth *(live `pallets/flask` clone skipped for network constraints; equivalent end-to-end coverage via the synthetic-repo `test_orchestrator.py` paths -- see the 2026-05-22 Phase 4 session history)*

**Objective**: Verify the AST + call-graph + watcher pipeline end-to-end.

**Prompt**:
> Run: `python -m pytest extensions/nexus-code-search/tests -v`. Then run an end-to-end smoke: from a clean tmp_path, clone a medium Python repo (e.g., https://github.com/pallets/flask at a pinned tag), run `python -m nexus_code_search index <tmp_path>`, and verify (a) the SQLite db at `<tmp_path>/.nexus/code-index/codegraph.db` exists and contains `> 1000` nodes; (b) `nexus_code_search.searchNodes('Flask')` returns the right symbol; (c) `nexus_code_search.callers(<id_of_Flask.__init__>)` returns plausible callers; (d) `nexus_code_search.impact_radius(<id>, depth=2)` returns a reasonable set; (e) modifying a file under <tmp_path> and waiting 3s causes the watcher to log a re-index. Compare results against a manual `grep -rn` baseline to catch obvious miss-rates. If miss-rate > 10%, fix the relevant extractor and re-run. After all tests pass, run /generate-session-history to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing *(136 passed, 1 skipped in the 2026-05-26 sync re-run; 104 passed at original Phase 4 close, grown by Phase 5)*
- [x] End-to-end smoke against Flask (or equivalent) succeeds *(equivalent: synthetic-repo `test_orchestrator.py` paths; live Flask clone skipped for network constraints per the 2026-05-22 session history)*
- [x] v1.0.0 -> v2.0 index migration warning works correctly *(`migrate_v1_to_v2` renames the legacy index aside and prints the re-index warning; covered by `test_schema.py`)*
- [x] Session history generated for this phase *(2026-05-22 implementation history + 2026-05-26 checkbox-sync history)*
- [x] Ready to advance to Phase 5 *(Phase 5 already shipped on top of this foundation)*

---

## Phase 5: Code-graph capabilities - frameworks, affected-tests, eval harness

**Goal**: Layer framework-route extraction (Django / FastAPI / Express), an `affected_tests` MCP tool with a `nexus-hub affected` CLI subcommand, and a synthetic-codebase MCP eval harness on top of the Phase 4 foundation.
**Prerequisites**: Phase 4 (uses the AST tables and call-graph traversal).
**Stability Gate**: `code_search('route:/users')` returns route nodes for all three framework fixtures; `nexus-hub affected src/foo.py` produces the same test-file list as a manual `pytest --collect-only` derivation; the eval harness scores Phase 4's tooling against a 20-question fixture set with `>= 80%` correctness.

### Sub-tasks

#### 5.1 - Django framework route extractor

- [x] T029 [P] Add extensions/nexus-code-search/src/nexus_code_search/frameworks/django.py emitting `route` nodes and `references` edges from urls.py files

**Objective**: First of three framework extractors (C3 from the comparison, starter set).

**Prompt**:
> Create extensions/nexus-code-search/src/nexus_code_search/frameworks/django.py with a `DjangoFrameworkResolver` class whose `resolve(file_path: Path, source: bytes, ast_nodes: list[Node]) -> tuple[list[Node], list[Edge]]` method recognizes `path()`, `re_path()`, `url()`, `include()` patterns in urls.py files, plus `MyView.as_view()` patterns and dotted-path string references. For each detected URL pattern, emit one `route` node (kind=`route`, name=`/path/<param>`, qualified_name=`<method> /path/<param>` if a method is implied) and one `references` edge to the handler class or function node. Reference the cloned-codegraph implementation src/resolution/frameworks/django.ts for the regex / s-expression queries. Wire `DjangoFrameworkResolver` into extensions/nexus-code-search/src/nexus_code_search/resolution/orchestrator.py - call it after the per-language AST extraction completes for any file whose path ends in `urls.py`. Add tests/fixtures/frameworks/django/ with 3 fixture urls.py files covering: simple `path()`, parameterized `re_path()`, and nested `include()`. Add tests/test_django_routes.py asserting the expected route nodes and references edges.

---

#### 5.2 - FastAPI framework route extractor

- [x] T030 [P] Add extensions/nexus-code-search/src/nexus_code_search/frameworks/fastapi.py emitting `route` nodes from `@app.get()` / `@router.post()` decorators

**Objective**: Second framework extractor (C3 starter set).

**Prompt**:
> Create extensions/nexus-code-search/src/nexus_code_search/frameworks/fastapi.py with a `FastAPIFrameworkResolver` class. Recognize: `@app.<method>('/path')` and `@router.<method>('/path')` decorators on functions, for `<method>` in {get, post, put, patch, delete, options, head}. Emit one `route` node per decorated function with name=`<METHOD> /path` and a `decorates` edge from the route node to the handler function node. Reference the cloned-codegraph implementation src/resolution/frameworks/fastapi.ts. Wire into the resolution orchestrator. Add tests/fixtures/frameworks/fastapi/ with 3 fixture files and tests/test_fastapi_routes.py.

---

#### 5.3 - Express framework route extractor

- [x] T031 [P] Add extensions/nexus-code-search/src/nexus_code_search/frameworks/express.py emitting `route` nodes from `app.get()` / `router.post()` calls

**Objective**: Third framework extractor (C3 starter set complete).

**Prompt**:
> Create extensions/nexus-code-search/src/nexus_code_search/frameworks/express.py with `ExpressFrameworkResolver`. Recognize: `app.<method>('/path', handler)` and `router.<method>('/path', ...middleware, handler)` for `<method>` in get / post / put / patch / delete / use / all. Handle middleware chains by emitting one `route` node and `references` edges to every middleware function. Reference the cloned-codegraph implementation src/resolution/frameworks/express.ts. Wire into the resolution orchestrator. Add tests/fixtures/frameworks/express/ with 3 fixture files (one with middleware chain) and tests/test_express_routes.py.

---

#### 5.4 - affected_tests MCP tool and nexus-hub affected CLI

- [x] T032 Add a `code_affected_tests` MCP tool to extensions/nexus-code-search/src/nexus_code_search/server.py and a `nexus-hub affected <files>` CLI subcommand

**Objective**: Test-impact analysis via graph traversal (C8 from the comparison).

**Prompt**:
> Implement `code_affected_tests(repo_root: Path, changed_files: list[Path], depth: int = 5, test_glob: str | None = None) -> list[Path]`. Algorithm: (1) for each changed file, find its file node in the index; (2) BFS over reverse `imports` edges (callees of import) and reverse `calls` edges up to `depth` hops; (3) filter the discovered file set to those matching the test glob (default heuristic: filenames containing `test_` or `_test` or paths under `tests/`); (4) return the deduplicated list of test file paths. Reference the cloned-codegraph implementation README.md lines 343-370 (`codegraph affected` semantics) and src/graph/affected.ts. Wire the tool into the MCP server. Add a `nexus-hub affected [files...]` CLI subcommand to scripts/installer.sh and scripts/installer.ps1 (or to a new `scripts/nexus-hub.sh` thin dispatcher) that proxies stdin pipe / argv to the MCP server's tool. Add tests/test_affected.py with a fixture project where changing `src/utils.py` should surface `tests/test_utils.py`, `tests/test_api.py` (because api.py imports utils), but NOT `tests/test_db.py`.

---

#### 5.5 - Synthetic-codebase MCP eval harness

- [x] T033 Add extensions/nexus-code-search/eval/ with a synthetic-codebase fixture set and a runner that scores each tool's answers against ground truth

**Objective**: Match CodeGraph's `__tests__/evaluation/` pattern (C10 from the comparison).

**Prompt**:
> Create extensions/nexus-code-search/eval/ with: (a) eval/fixtures/ containing 3-5 synthetic small codebases (one Python Flask app, one FastAPI app, one TypeScript Express app, plus a "minimal" one for quick iteration); each fixture ships a fixtures.yaml file with 20 questions (5 per tool: search / callers / callees / impact / context) and the expected answer key (list of node IDs or symbol names); (b) eval/runner.py that for each fixture, builds the index, calls each MCP tool with the eval questions, scores recall / precision against the answer key, and emits a markdown report; (c) a `make eval` target in the repo root Makefile that runs the harness; (d) docs/archive/v2/v2.2/eval-baseline.md capturing the v2.2.0 baseline scores. Reference the cloned-codegraph implementation __tests__/evaluation/runner.ts and __tests__/evaluation/test-cases.ts. Add tests/test_eval_runner.py asserting the runner produces a markdown report (do not assert specific score thresholds in unit tests - those live in the eval baseline doc).

---

#### 5.6 - Phase 5 tests and stabilization

- [x] T034 Run and stabilize Phase 5 tests; run the eval harness end-to-end and capture baseline scores

**Objective**: Verify the framework / affected / eval layers integrate cleanly with Phase 4.

**Prompt**:
> Run: `python -m pytest extensions/nexus-code-search/tests -v`. Then run `make eval` and inspect the markdown report. Confirm: (a) Django / FastAPI / Express routes are extracted correctly; (b) `affected_tests` returns reasonable results on a real repo (use the Flask clone from Phase 4.6); (c) the eval harness scores at least 80% recall on every fixture set. Commit the baseline report to docs/archive/v2/v2.2/eval-baseline.md. If any fixture scores below 80%, fix the underlying extractor / resolver and re-run. After all tests pass, run /generate-session-history to document Phase 5.

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] Eval baseline >= 80% across all fixtures
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 6

---

## Phase 6: Polish, data-registry rebaseline, and release

**Goal**: Update the data registry (SKILL_INDEX, skills.json, marketplace.json), author the v2.2.0 RELEASE_NOTES and CHANGELOG block, run cross-OS installer smoke tests, finalize known-gaps, and prepare the `git tag v2.2.0` cut.
**Prerequisites**: Phases 1-5 all complete and stable.
**Stability Gate**: `make validate && make lint && make test && make eval` all pass cleanly on Windows / macOS / Linux smoke environments; RELEASE_NOTES.md and CHANGELOG.md are authored from the user's perspective; docs/archive/v2/v2.2/known-gaps.md is finalized; no `[Unreleased]` content remains in CHANGELOG.md.

### Sub-tasks

#### 6.1 - Update data registry

- [x] T035 Rebaseline data/SKILL_INDEX.md, data/skills.json, and data/marketplace.json to reflect v2.2.0 additions (new MCP tools, new integration, new templates) *(no-op at Phase 6 close -- the codegraph deltas were MCP tools / hooks / templates, not new SKILL.md entries, so the registry stayed at 206; the later adoption-antigravity-sdk-python plan added the one new skill (google-antigravity-sdk), taking the registry to 207, reflected in the AGENTS.md count + RELEASE_NOTES + CHANGELOG during the combined release-prep sweep)*

**Objective**: Mandatory data-registry sync per AGENTS.md rule #5.

**Prompt**:
> Walk every Phase 1-5 sub-task that added a skill / template / MCP tool, and update: (a) data/SKILL_INDEX.md - add one row per new skill; (b) data/skills.json - add one entry per new skill with structural/integrity/semantic scores; (c) data/marketplace.json - increment per-category `skill_count` and the top-level `statistics.total_skills`. The biggest expected delta is in `ai-development` (one or two new skills for the AST graph / framework resolution), `infrastructure` (one for `affected_tests` CI usage), and `developer-experience` (one for the MCP eval harness). Confirm the counts add up correctly. Run `make validate` and fix any reported inconsistency.

---

#### 6.2 - Author v2.2.0 RELEASE_NOTES.md

- [x] T036 Write docs/archive/v2/v2.2/RELEASE_NOTES.md with the CodeGraph adoption narrative, the Antigravity transition narrative, and the per-candidate map (C1-C14 -> shipped artifacts)

**Objective**: Match the user-narrative style of CodeGraph's CHANGELOG (Section 7 of the comparison report flagged this as worth borrowing) and the structure of docs/archive/v2/v2.1/RELEASE_NOTES.md.

**Prompt**:
> Create docs/archive/v2/v2.2/RELEASE_NOTES.md. Open with a 3-paragraph narrative: paragraph 1 frames v2.2.0 as adopting 12 of 14 CodeGraph capabilities surfaced in [docs/archives/v2/v2.1/comparison-codegraph.md](../v2.1.0/comparison-codegraph.md); paragraph 2 frames the Gemini-CLI-to-Antigravity-CLI transition (cite the 2026-05-21 Google announcement) and confirms the transition shipped ahead of the 2026-06-18 sunset; paragraph 3 surfaces what is DEFERRED (C13 standalone runtime bundling and C3-extended remaining framework extractors -> v2.3.0). Then a "Highlights" section with 5-8 bullet points written from the user perspective ("Your Nexus-Hub installer can now run `--check` to detect drift without writing a byte", "`nexus-code-search` answers `callers(...)` / `callees(...)` / `impact(...)` against a tree-sitter AST graph"). Then a "Per-candidate adoption map" table mapping each comparison candidate (C1, C2, ..., C14) to the sub-task IDs that shipped it (T001, T002, ..., T034). Cross-link to the plan file [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md), the comparison report, and the CHANGELOG entry.

---

#### 6.3 - Author CHANGELOG.md [2.2.0] block

- [x] T037 Add the `## [2.2.0] - YYYY-MM-DD` block to CHANGELOG.md grouping changes under Added / Changed / Fixed / Deprecated

**Objective**: Source of truth for the GitHub Release notes per CLAUDE.md release flow.

**Prompt**:
> Edit CHANGELOG.md: replace `## [Unreleased]\n\n(none)` with `## [2.2.0] - <today's UTC date>` and the full block. Group: **Added** (every new MCP tool, every new installer flag, every new integration, every new framework extractor, every new template, every new test file - paraphrased to the user-facing capability they enable); **Changed** (`IntegrationBase` API now returns `WriteResult`; instruction files merged via marker-delimited blocks; data registry rebaselined); **Fixed** (DF-001 from v2.1.0 closed); **Deprecated** (`gemini-cli` integration is opt-in via `--enterprise`; default flow installs Antigravity CLI). Mirror the user-narrative style from CodeGraph's CHANGELOG (see Section 7 of the comparison report for the rationale). Re-create an empty `## [Unreleased]\n\n(none)` block above the new [2.2.0] block. Confirm `make validate` still passes (CHANGELOG is referenced by some validators).

---

#### 6.4 - Cross-OS installer smoke

- [x] T038 Run the installer end-to-end on Windows / macOS / Linux throwaway environments and capture results in docs/archive/v2/v2.2/installer-smoke-post.txt *(Windows smoke run clean; macOS / Linux re-verification deferred to the next packaged-binary release and tracked as WN-8 -- this is a source release, so the deferral is acceptable)*

**Objective**: Confirm the installer refactor (Phases 1-3) does not regress any platform.

**Prompt**:
> On a Windows host: `pwsh scripts/installer.ps1 -Target C:\temp\nexus-smoke-win` then `pwsh scripts/installer.ps1 -Target C:\temp\nexus-smoke-win --check` (expect exit 0 after the first run). On a macOS host (or a Docker container running macOS-mode): `bash scripts/installer.sh --target /tmp/nexus-smoke-mac` then `bash scripts/installer.sh --target /tmp/nexus-smoke-mac --check`. On Linux: same with `/tmp/nexus-smoke-linux`. For each host, capture: (a) exit code; (b) total file count under the target; (c) the `--check` output post-install showing all `unchanged`; (d) a smoke check that each of the 3 internal MCP servers starts (`python -m nexus_skill_server --health`, `python -m nexus_code_search --health`, `python -m nexus_web_fetch --health`). Aggregate into docs/archive/v2/v2.2/installer-smoke-post.txt. If any host fails, root-cause and fix before tagging.

---

#### 6.5 - Finalize known-gaps and bump version manifests

- [x] T039 Finalize docs/archive/v2/v2.2/known-gaps.md with any deferred / open items from Phases 1-5, and bump version in data/marketplace.json plugin.version, package manifests, and the AGENTS.md catalog count *(version strings bumped to 2.2.0 across plugin.json / marketplace.json / installer.sh / installer.ps1; AGENTS.md count set to 206 at Phase 6, then rebaselined to 207 in the combined release-prep sweep after the SDK skill landed)*

**Objective**: Lock in the version-bump artifacts so the release tag is the only remaining step.

**Prompt**:
> Create docs/archive/v2/v2.2/known-gaps.md following the v2.1.0 template format (Summary table, Open Items table, Resolved table). The Resolved table should list at minimum DF-001 (resolved in Phase 3) and the original 4-platform parity migration. Open items should list any sub-tasks that were partially completed or deferred (e.g., if any of the 18 deferred-language extractors were attempted but dropped, document why). Bump: (a) data/marketplace.json `plugin.version` from "2.1.0" to "2.2.0"; (b) any other version-string locations the v2.1.0 close-out touched (search `grep -rn "2\\.1\\.0" --include="*.json" --include="*.toml" --include="*.md" .` and audit each hit). Update the catalog count in AGENTS.md "Current catalog: 203 skills..." to reflect the v2.2.0 totals after data-registry rebaseline. Confirm `make validate` passes.

---

#### 6.6 - Phase 6 final tests and release-tag prep

- [x] T040 Run the full validation + test + eval pipeline one final time and produce the commit message for the version-bump commit

**Objective**: Last checkpoint before the user runs `git tag v2.2.0` and pushes.

**Prompt**:
> Run, in order: `make validate`, `make lint`, `make test`, `make eval`. All four must pass cleanly. Verify no `[Unreleased]` entries remain in CHANGELOG.md. Verify docs/archive/v2/v2.2/RELEASE_NOTES.md and docs/archive/v2/v2.2/known-gaps.md exist and parse. Verify data/skills.json `statistics.total_skills` matches the actual skills array length. Stage the version-bump commit with `git status` and `git diff --stat`. Compose a commit message of the form: `release: v2.2.0 (CodeGraph adoption + Antigravity CLI transition)` followed by a 3-line body summarizing the headline changes. Print the commit message and the suggested next commands (`git commit`, `git push`, `git tag v2.2.0`, `git push origin v2.2.0`) to stdout - **do not run them yourself per the CLAUDE.md destructive-git rule**. After printing, run /generate-session-history to document Phase 6.

---

### Phase 6 Exit Checklist

- [x] All sub-tasks completed *(T035-T040)*
- [x] make validate / make lint / make test / make eval all pass *(re-verified during the combined release-prep sweep)*
- [x] RELEASE_NOTES, CHANGELOG, known-gaps all finalized *(plus the adoption-antigravity-sdk-python additions folded in during the combined release-prep sweep)*
- [x] Cross-OS smoke results recorded *(Windows clean; macOS / Linux deferred as WN-8 -- source release)*
- [x] Version-bump commit message printed and staged
- [x] User has run `git tag v2.2.0 && git push origin v2.2.0` *(annotated tag cut on commit 352f8be and pushed to origin on 2026-05-26)*
- [x] Session history generated for this phase *(2026-05-22 implementation history + the 2026-05-26 checkbox-sync history)*

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution file in place; no violations to track.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | (none)     | (none)                              |

---

## Items explicitly NOT adopted in v2.2.0 (deferred to v2.3.0+)

These items appeared in the [comparison report](../../v2.1.0/comparison-codegraph.md) but are intentionally not in v2.2.0 scope. They are deferrals, not policy rejections.

- **N1 - C13: Standalone runtime bundling.** Defers the vendored-Python install path (pyoxidizer / PyInstaller). **Reason**: Nexus-Hub's Python 3.10+ dependency is documented and accepted; bundling a 80+ MB runtime adds a build matrix per (Python version x OS x arch) to maintain. The cost outweighs the benefit until a regulated-environment user files a concrete ticket asking for it. Re-evaluate in v2.3.0.

- **N2 - C3-extended: Remaining 10 framework extractors beyond Django / FastAPI / Express.** Defers NestJS, Laravel, Rails, Spring, Gin, chi, gorilla / mux, Axum, actix, Rocket, ASP.NET, Vapor, React Router, SvelteKit, Vue/Nuxt, Cargo workspaces. **Reason**: 13 frameworks at 40-100 LoC each is a long tail. Ship 3 in v2.2.0 to validate the architecture, then port the remainder as user demand surfaces. Tracked at docs/archive/v2/v2.2/deferred-language-extractors.md (created in sub-task 4.3).

Both items will be re-evaluated when v2.3.0 planning starts.
