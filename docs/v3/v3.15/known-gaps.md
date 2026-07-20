# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: v3.15.0 platform-parity-all-gaps IN PROGRESS on `feat/platform-parity-all-gaps` (cut off `develop`). Phase 1 (capability model + read-contract web re-verification) COMPLETE; Phases 2-7 pending.
**Last updated**: 2026-07-20 (v3.15.0 Phase 1)

> **Prior-version ingest**: v3.14.5's DF-4 (platform additive-surface drift) is the direct input to this release and is now being actioned per phase; it does not carry forward as a separate open item. The v3.14.5 Advisory pre-existing failure `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` is re-confirmed on this branch (see Advisory below) and is owned by Phase 5.2.

## v3.15.0

**Status**: Phase 1 COMPLETE on `feat/platform-parity-all-gaps`. **1.1**: `hooks_supported` is now the single load-bearing hook-capability signal - `SkillsIntegration._mirror_catalog` (base) and `Antigravity20Integration._mirror_surface` (bespoke hooks.json writer) both gate hook installation on it; the change is byte-identical for the live registry (every integration declaring `hooks_subdir` also sets `hooks_supported: True`). The dead `permissions_file` config key (declared on 7 subclasses, never read by any code) was removed; the permission JSON files themselves are installed by a separate mechanism and are untouched. **1.2/1.3**: the five parity-target platforms (Cursor, OpenCode, Qwen, Kimi, Copilot) were web re-verified against current official docs (2026-07-20); findings + source URLs + MATCH/DRIFT/UNVERIFIED classifications are recorded in `docs/policy/platform-read-contracts.md` (Re-verification log) and the sibling JSON's non-consumed `parity_verification_v3_15_0` block. The Qwen and Kimi Gemini-CLI-class verdicts both came back GO (the Phase 4 reclassification gate). Gates green: hook-gating tests 5/5; full integrations + contract-validator suites 378 passed (1 pre-existing failure, see Advisory); `verify_platform_contracts.py`, `check_platform_contract_freshness.py`, base-parity, no-personal-paths, unicode-safety (0 errors), version-sync all exit 0; `ruff check` clean. Plan: [plans/v3.15.0-platform-parity-all-gaps.md](plans/v3.15.0-platform-parity-all-gaps.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 5 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 0 |

### Advisory (pre-existing test failure, NOT caused by v3.15.0 Phase 1)

- `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` - the test's `overrides` set omits `copilot`, which has overridden `wire_project_surfaces` since v3.11.0 (it returns a skip-note `WriteResult`, not `None`, when the `.github/skills` opt-in is unset). Confirmed PRE-EXISTING on this branch by stashing all Phase 1 tracked edits and reproducing the identical failure on the bare `develop` baseline; Phase 1 never touched `wire_project_surfaces`. The plan assigns the fix to Phase 5.2 (which broadens Copilot skills and therefore touches copilot). Fix: add `copilot` to the test's `overrides` set (a one-line test update).

### Open Items

#### Deferred

##### DF-1 - Cursor global commands path and hooks.json field spelling need a direct confirmation before Phase 2

- **Source phase**: v3.15.0 Phase 1.2
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Reason**: the 2026-07-20 web re-verification confirmed Cursor 2.4 reads skills (`~/.cursor/skills`, `.cursor/skills`, `.agents/skills`, `.claude/skills`), subagents (`.cursor/agents/*.md`, NOT `.agent.md`), and hooks (`~/.cursor/hooks.json`, `.cursor/hooks.json`), and project commands at `.cursor/commands/<name>.md`. Two items are not fully pinned: (a) the baseline global `~/.cursor/commands/` path could not be confirmed against reachable official docs (the commands doc redirected to the skills page); (b) the exact optional-field spelling of the `hooks.json` schema (`type`/`timeout`/`loop_limit`/`failClosed`) was enumerated in a single fetch, while `version:1`, `command`, `matcher`, the event names, and the exit-code semantics were double-confirmed.
- **Suggested next step**: Phase 2 should do one direct human read of `cursor.com/docs/hooks` and the commands doc to lock the optional-field spelling and confirm the global commands path before emitting the `hooks.json` writer and project-command mirror.

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

##### DF-4 - OpenCode plugins/hooks are a different (JS/TS Bun) runtime; hook parity is out of scope unless a wrapper is warranted

- **Source phase**: v3.15.0 Phase 1.2
- **Plan reference**: Phase 3.2 (OpenCode plugins/hooks surface, ask-first)
- **Reason**: OpenCode's agents folder (`~/.config/opencode/agents/`, `.opencode/agents/`) is a clean additive surface Phase 3 can deliver, but its hook mechanism is a `plugins/` directory of JS/TS modules on a Bun runtime with an event-subscription API, not a Claude-style shell/python hook model. Nexus-Hub's `catalog/hooks/*.sh` / `*.py` cannot be dropped into `plugins/` and run; delivering hooks here would require authoring a JS/TS plugin wrapper that shells out.
- **Suggested next step**: Phase 3.2 should record OpenCode's plugin model as a documented non-gap (out of scope: different runtime) unless a thin JS/TS wrapper that invokes the shell hooks is judged worth it.

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
