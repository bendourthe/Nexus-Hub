# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: v3.15.0 platform-parity-all-gaps IN PROGRESS on `feat/platform-parity-all-gaps` (cut off `develop`). Phases 1 (capability model + read-contract web re-verification), 2 (Cursor parity), and 3 (OpenCode parity) COMPLETE; Phases 4-7 pending.
**Last updated**: 2026-07-21 (v3.15.0 Phase 3)

> **Prior-version ingest**: v3.14.5's DF-4 (platform additive-surface drift) is the direct input to this release and is now being actioned per phase; it does not carry forward as a separate open item. The v3.14.5 Advisory pre-existing failure `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` is re-confirmed on this branch (see Advisory below) and is owned by Phase 5.2.

## v3.15.0

**Status**: Phase 1 COMPLETE on `feat/platform-parity-all-gaps`. **1.1**: `hooks_supported` is now the single load-bearing hook-capability signal - `SkillsIntegration._mirror_catalog` (base) and `Antigravity20Integration._mirror_surface` (bespoke hooks.json writer) both gate hook installation on it; the change is byte-identical for the live registry (every integration declaring `hooks_subdir` also sets `hooks_supported: True`). The dead `permissions_file` config key (declared on 7 subclasses, never read by any code) was removed; the permission JSON files themselves are installed by a separate mechanism and are untouched. **1.2/1.3**: the five parity-target platforms (Cursor, OpenCode, Qwen, Kimi, Copilot) were web re-verified against current official docs (2026-07-20); findings + source URLs + MATCH/DRIFT/UNVERIFIED classifications are recorded in `docs/policy/platform-read-contracts.md` (Re-verification log) and the sibling JSON's non-consumed `parity_verification_v3_15_0` block. The Qwen and Kimi Gemini-CLI-class verdicts both came back GO (the Phase 4 reclassification gate). Gates green: hook-gating tests 5/5; full integrations + contract-validator suites 378 passed (1 pre-existing failure, see Advisory); `verify_platform_contracts.py`, `check_platform_contract_freshness.py`, base-parity, no-personal-paths, unicode-safety (0 errors), version-sync all exit 0; `ruff check` clean. Plan: [plans/v3.15.0-platform-parity-all-gaps.md](plans/v3.15.0-platform-parity-all-gaps.md).

**Phase 2 (Cursor parity) COMPLETE.** The Cursor integration surfaces were already implemented in the branch-untangle commit `a56cdffa` (skills flattened to `.cursor/skills`, subagents to `.cursor/agents`, a `version:1` `hooks.json` with `git-guardrails` gated on `hooks_supported`, project `.cursor/commands/`), with a full 8-test `test_cursor.py`. Phase 2 closed the DF-1 verification gate that `a56cdffa` deferred and completed sub-task 2.3: (1) a 2026-07-21 direct re-read of Cursor's official docs RESOLVED DF-1(b) - the `hooks.json` schema is confirmed and the minimal writer is valid as-is (no code change); (2) DF-1(a) global `~/.cursor/commands/` remains UNVERIFIED (no official doc; community feature-request) - the write is retained per plan 2.3 and tracked as the DF-1 residual; (3) `wire_project_surfaces` now also seeds project `.cursor/commands/` so `nexus-hub init` gives a project the slash surface, not just the rules stub (sub-task 2.3 literal acceptance). Tests: `test_cursor.py` 9/9 (added a `wire_project_surfaces` command-seeding test). Contract JSON `parity_verification_v3_15_0.cursor` + the `.md` Re-verification log updated with the 2026-07-21 findings.

**Phase 3 (OpenCode parity) COMPLETE.** **3.1 (agents surface)**: added `agents_subdir: "agents"` to `OpenCodeIntegration.config` - a config-only change, since the base `_mirror_catalog` copies `catalog/agents/*.md` verbatim to `~/.config/opencode/agents/` (global) and `.opencode/agents/` (project). A 2026-07-21 direct re-read of `opencode.ai/docs/agents/` confirmed OpenCode reads `.md` + YAML frontmatter there with `mode` OPTIONAL (default `all`), so the catalog personas (`name`/`description`/`tools` frontmatter) load as-is - OpenCode uses `description` + the filename, defaults the mode, and ignores the non-native keys (same way Cursor consumes these files). **3.2 (plugins/hooks)**: OUT OF SCOPE, confirmed - a 2026-07-21 re-read of `opencode.ai/docs/plugins/` verified plugins are JavaScript/TypeScript modules loaded by Bun (exporting functions that subscribe to events like `tool.execute.before`); a `.sh`/`.py` hook cannot be dropped in and run, so Nexus-Hub's shell/py hooks do not translate without a JS/TS wrapper. `hooks_supported` stays `False`; DF-4 resolved as a documented non-gap. **3.3 (tests)**: added `tests/integrations/test_opencode.py` (6 tests: agents written both scopes, verbatim `.md`, skills/commands/rules preserved, no hooks surface, idempotent). Validation: `test_opencode.py` 6/6; ruff clean; workspace + global dry-runs land agents at the verified paths and write no hooks. Contract JSON `parity_verification_v3_15_0.opencode` + `contract_checks`/`install_verify` + the `.md` Re-verification log updated.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 0 |

### Advisory (pre-existing test failure, NOT caused by v3.15.0 Phase 1)

- `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` - the test's `overrides` set omits `copilot`, which has overridden `wire_project_surfaces` since v3.11.0 (it returns a skip-note `WriteResult`, not `None`, when the `.github/skills` opt-in is unset). Confirmed PRE-EXISTING on this branch by stashing all Phase 1 tracked edits and reproducing the identical failure on the bare `develop` baseline; Phase 1 never touched `wire_project_surfaces`. The plan assigns the fix to Phase 5.2 (which broadens Copilot skills and therefore touches copilot). Fix: add `copilot` to the test's `overrides` set (a one-line test update).

### Open Items

#### Deferred

##### DF-1 - Cursor global commands path UNVERIFIED (residual; hooks.json schema RESOLVED in Phase 2)

- **Source phase**: v3.15.0 Phase 1.2; actioned in Phase 2 (2026-07-21)
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Status**: PARTIALLY RESOLVED. Phase 2 did the direct doc re-read the original gap asked for. **DF-1(b) hooks.json schema - RESOLVED**: [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms `{version:1, hooks:{<event>:[{...}]}}` with `type`/`timeout`/`loop_limit`/`failClosed`/`matcher` all OPTIONAL (defaults `type=command`, `failClosed=false`), so the integration's minimal `beforeShellExecution -> {command}` writer is schema-valid as-is (no code change). **DF-1(a) global `~/.cursor/commands/` - RESIDUAL (still UNVERIFIED)**: project `.cursor/commands/<name>.md` is officially documented (Cursor 1.6+) and confirmed, but the user-global `~/.cursor/commands/` dir has no reachable official doc (the commands page 404s / redirects to Skills) and [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request, not a built-in.
- **Decision**: the global write is RETAINED per plan sub-task 2.3 ("keep the global mirror unchanged") and the contract's negative-only-evidence caution (removing a possibly-live path could break delivery); it is harmless if unread. Recorded in `cursor.py`'s docstring, the contract JSON `parity_verification_v3_15_0.cursor.commands.phase2_note`, and the contract `.md` Re-verification log (2026-07-21).
- **Suggested next step**: a future cycle with a reachable Cursor commands doc (or an empirical test on a live Cursor install) should confirm or drop the global `~/.cursor/commands/` write. Not blocking - the confirmed project `.cursor/commands/` surface (seeded by both the workspace install and `nexus-hub init`) is the load-bearing path.

##### DF-2 - Qwen skills auto-load reliability (open issue #2343) needs a live smoke test before Phase 4 ships the reclassification

- **Source phase**: v3.15.0 Phase 1.2
- **Plan reference**: Phase 4 (Qwen reclassification, gated GO)
- **Reason**: Qwen Code's official docs unambiguously document a skills folder (`~/.qwen/skills/<name>/SKILL.md`, project `.qwen/skills/`) and TOML/Markdown commands (`~/.qwen/commands/`), so the Gemini-CLI-class verdict is GO. But open issue QwenLM/qwen-code#2343 reports that project-scoped skills may not auto-load on some builds after a terminal restart, a docs-vs-behavior gap.
- **Suggested next step**: Phase 4 should live-smoke-test actual skill discovery on a current Qwen Code build before shipping the reclassification; if auto-load is unreliable, prefer the global `~/.qwen/skills/` path and/or document the caveat.

##### DF-3 - Kimi current product is `~/.kimi-code/`, not the baseline's deprecated `~/.kimi/`

- **Source phase**: v3.15.0 Phase 1.2
- **Plan reference**: Phase 4 (Kimi reclassification, gated GO)
- **Reason**: the current product is Kimi Code CLI (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`), the Node.js successor to the deprecated Python Kimi CLI (`~/.kimi/`) that the current integration baseline targets. Kimi Code CLI reads a folder-per-skill `SKILL.md` tree (`~/.kimi-code/skills/`, `~/.agents/skills/`, project `.kimi-code/skills/`, `.agents/skills/`) and exposes each skill as `/skill:<name>` (there is no separate command file format; `commands.html` 404s). It has no user-definable agents surface (three fixed built-ins) and its hooks are a `[[hooks]]` TOML array in `~/.kimi-code/config.toml` (config-merge, not a folder copy). The baseline `.kimi/agent.yaml` is unsupported in the new product.
- **Suggested next step**: Phase 4 must resolve the write target - new `~/.kimi-code/skills/` vs the cross-tool `.agents/skills/` (which both variants honor) - drop the unsupported `.kimi/agent.yaml`, and preserve the `.kimi/AGENTS.md` instruction write for back-compat while adding the `~/.kimi-code/` surfaces.

##### DF-4 - OpenCode plugins/hooks out of scope (RESOLVED as a documented non-gap in Phase 3.2)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 3.2 (2026-07-21)
- **Plan reference**: Phase 3.2 (OpenCode plugins/hooks surface, ask-first)
- **Status**: RESOLVED (decision: out of scope). Phase 3 delivered OpenCode's agents surface (3.1) and made the plugins/hooks call (3.2). A 2026-07-21 re-read of [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins) confirmed plugins are JavaScript/TypeScript modules loaded by Bun (each exporting plugin functions that subscribe to events like `tool.execute.before` / `file.edited`); the docs state plainly that plugins must be JS/TS modules and that a `.sh` / `.py` script cannot be dropped into `plugins/` and run. Nexus-Hub's `catalog/hooks/*.{sh,py}` therefore cannot be delivered here without authoring a JS/TS wrapper per hook that shells out.
- **Decision**: OpenCode hooks are OUT OF SCOPE. `hooks_supported` stays `False` (the base `_mirror_catalog` gates the hook copy on it, so no hook surface is written); recorded in `opencode.py`'s docstring + config comment and the contract. A thin JS/TS wrapper that invokes the shell hooks is a possible future item but is not judged worth the per-hook authoring + Bun-runtime maintenance for this release.
- **Suggested next step**: none required. Revisit only if a maintainer wants OpenCode hook parity badly enough to own a JS/TS plugin wrapper.

##### DF-5 - Copilot skills are now native default-on; the `.github/skills` commit-visibility policy remains a Nexus-Hub concern

- **Source phase**: v3.15.0 Phase 1.2
- **Plan reference**: Phase 5 (Copilot skill broadening)
- **Reason**: the re-verification found Copilot now reads Agent Skills natively and default-on (`.github/skills/` canonical, also `.claude/skills/`, `.agents/skills/`, and user paths `~/.copilot/skills/`, `~/.agents/skills/`, VS Code `~/.claude/skills/`); the `.github/skills` PATH matches the current opt-in path, but the baseline's "opt-in / env-gated / off-by-default" FRAMING is stale. Copilot also gained custom agents (`.github/agents/*.agent.md`) and hooks (`.github/hooks/*.json`, Preview).
- **Suggested next step**: Phase 5 broadens the delivered skill set while keeping the never-overwrite-existing-file guarantee, because `.github/skills/` is commit-visible (a Nexus-Hub policy consideration independent of Copilot no longer technically requiring opt-in).

#### Quality-gate gaps

##### QG-1 - `make validate` compression-accuracy eval not run this phase (unrelated to Phase 1 scope)

- **Source phase**: v3.15.0 Phase 1.4
- **Plan reference**: Phase 1.4 (run `make validate`)
- **Reason**: `make` is unavailable in the dev environment, so the `make validate` steps were run individually. The context-compressor accuracy-regression eval (`extensions/nexus-context-compressor python -m evals --check`) was not run because Phase 1 does not touch `extensions/nexus-context-compressor` and the eval carries no signal about these changes. Every other `make validate` step passed (all validators exit 0).
- **Suggested next step**: the eval runs in CI and at `/update release` (Phase 7); no action needed unless a later phase touches the compressor.
