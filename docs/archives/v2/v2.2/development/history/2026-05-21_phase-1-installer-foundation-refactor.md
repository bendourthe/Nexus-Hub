# Session History -- v2.2.0 Phase 1: Installer foundation refactor

**Date**: 2026-05-21
**Plan**: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](../../plans/codegraph-and-antigravity.md)
**Phase**: 1 -- Installer foundation refactor (sub-tasks T001-T006)
**Result**: shipped; all gates green; ready to advance to Phase 2

---

## Goal

Refactor the integration-registry write surface so every disk operation surfaces a typed action vocabulary (`WriteResult` + `FileAction`), shared instruction files merge non-destructively via HTML-comment markers, and the three internal MCP servers return a non-empty `instructions` string on `initialize`. This unblocks Phase 2 (Gemini-to-Antigravity CLI transition, time-critical before 2026-06-18) and Phase 3 (installer rigor + parity migration to close DF-001) by giving them a uniformly-typed foundation.

## Sub-tasks completed (6 of 6)

### T001 -- WriteResult dataclass and action vocabulary

- Created `scripts/lib/integrations/result.py` with `FileAction(path, action)` (frozen dataclass, post-init validation) and `WriteResult(files, notes)` (mutable, with `add` / `extend` / `note` / `actions_by_kind`).
- Re-exported `FileAction`, `WriteResult`, `VALID_ACTIONS` from the package root via `scripts/lib/integrations/__init__.py`.
- Test file: `tests/integrations/test_result.py` (14 assertions, all passing).

### T002 -- IntegrationBase lifecycle methods now return WriteResult

- `install_global`, `install_workspace`, `teardown`, plus a new `uninstall_global` / `uninstall_workspace` dispatch pair all return `WriteResult`.
- Helpers `_copy_file`, `_copy_tree`, `_write_instruction` each return a single `FileAction`; `_copy_tree` adds `_tree_matches` for byte-equality detection across an entire tree.
- Fixed a Windows-newline bug: `Path.write_text(s, encoding="utf-8")` converts `\n` to `\r\n` on Windows, breaking the unchanged-detection byte comparison. Switched all template / TOML / .mdc writes to `Path.write_bytes` to keep newlines deterministic.
- Updated `runner.py` with `_render_write_result` that prints a per-file action line using a prefix table (`[+] created`, `[~] updated`, `[=] unchanged`, `[-] removed`, `[!] not-found`, `[k] kept`).
- Threaded `WriteResult` through every per-platform subclass: `copilot.py`, `cursor.py`, `gemini_cli.py`, `nexus_ai.py` had custom logic that now appends `FileAction`s to a local result and returns it; `claude.py`, `codex.py`, `gemini.py`, `opencode.py`, `antigravity.py` rely on the new mixin chain returning the result.
- Test file: `tests/integrations/test_base_writeresult.py` (30 assertions: 10 platforms x 2 install dispatch methods + 10 platforms x 1 install_workspace + Copilot 3-pass behavior + teardown shape).

### T003 -- Marker-delimited section merge helper

- Created `scripts/lib/installer/` package with `instruction_merge.py`.
- `merge_marker_section(file_path, body, start_marker, end_marker, legacy_header, dry_run) -> FileAction` walks 4 paths: create, replace-between-markers (with `unchanged` short-circuit), migrate-legacy-header, append-after-blank-line.
- `remove_marker_section(file_path, ...) -> FileAction` returns `not-found` / `kept` / `removed` (and unlinks the file when the block was the only content).
- Default markers: `<!-- NEXUS_HUB_START -->` and `<!-- NEXUS_HUB_END -->`.
- Test file: `tests/installer/test_instruction_merge.py` (12 assertions: each creation path, byte-identical unchanged, legacy header migration, user content preservation, remove outcomes, dry-run, custom markers).

### T004 -- MarkdownIntegration routed through merge_marker_section in shared mode

- New `instruction_mode: Literal["shared", "dedicated"]` class attribute on `MarkdownIntegration` (default `"shared"`).
- `_write_instruction` branches: `shared` -> `merge_marker_section` + `manifest.track_shared`; `dedicated` -> existing full-rewrite + `manifest.track`.
- `InstallManifest` extended with `track_shared` / `untrack_shared` / `shared_for` and a serialized `shared` dict; `to_dict` / `from_dict` propagate.
- `MarkdownIntegration.teardown` overridden to first call `remove_marker_section` on every `shared_for(self.key)` path, then delegate to `super().teardown` for tracked tree paths.
- Subclass declarations: `claude`, `codex`, `gemini`, `gemini-cli`, `opencode`, `cursor`, `copilot`, `antigravity`, `antigravity2` -> shared; `nexus-ai` -> dedicated.
- `Cursor.install_workspace` AGENTS.md write routed through `merge_marker_section`; the `.mdc` rules pipeline still does raw writes (Nexus-Hub-owned generated artifacts).
- `Copilot.install_workspace` retains its legacy `## Nexus-Hub Harness` append-after-heading pattern unchanged (logged as MT-1 in known-gaps for a follow-up refactor in Phase 3).
- Test file: `tests/integrations/test_markdown_integration.py` (17 assertions: user-content-around-marker survives, unchanged on reinstall, dedicated mode produces no markers, teardown removes only block, legacy header migration, each of 7 shared subclasses writes with markers).

### T005 -- MCP initialize server-instructions

- Added a non-empty `SERVER_INSTRUCTIONS` string to each of the three internal MCP servers.
- Wired via `server.create_initialization_options().model_copy(update={"instructions": SERVER_INSTRUCTIONS})` before `await server.run(...)`.
- Each instructions string lists the server's tools, cites the MCP Registry Policy (`already-local`), and points at related catalog skills.
- Test files: `extensions/{nexus-skill-server,nexus-code-search,nexus-web-fetch}/tests/test_initialize.py` (6 assertions each = 18 total).

### T006 -- Phase 1 verification + smoke install

- `python -m pytest tests/integrations tests/installer -q` -> 105 passed.
- `PYTHONPATH=extensions/nexus-skill-server/src python -m pytest extensions/nexus-skill-server/tests -q` -> 43 passed.
- `PYTHONPATH=extensions/nexus-code-search/src python -m pytest extensions/nexus-code-search/tests -q` -> 42 passed + 1 pre-existing skip.
- `PYTHONPATH=extensions/nexus-web-fetch/src python -m pytest extensions/nexus-web-fetch/tests -q` -> 29 passed.
- `python scripts/validate_skills.py --bundles-only` -> 0 errors, 0 warnings (210 skill bundles).
- Smoke install: `python scripts/lib/integrations/runner.py install --scope workspace --target /tmp/smoke-phase1 --integrations opencode,claude` produced `[+] created` per file on first run, `[=] unchanged` per file on reinstall, and a synthetic edit to `CLAUDE.md` (added `# user prelude` above and `## My TODOs` below the marker block) was preserved verbatim through a third reinstall.

## Test results (Phase 8.2 post-phase pass)

| Suite | Passed | Failed | Skipped | Notes |
|---|---|---|---|---|
| `tests/integrations` + `tests/installer` | 105 | 0 | 0 | 32 pre-existing + 73 new |
| `extensions/nexus-skill-server/tests` | 43 | 0 | 0 | +6 initialize |
| `extensions/nexus-code-search/tests` | 42 | 0 | 1 | +6 initialize; pre-existing pathspec skip |
| `extensions/nexus-web-fetch/tests` | 29 | 0 | 0 | +6 initialize |
| **Total** | **219** | **0** | **1** | |

Coverage: every new module has at least one dedicated test file; no new files lack test coverage.

## CI/CD edits (sub-step 8.3)

- `.github/workflows/ci.yml`: added one step `pytest tests/integrations tests/installer -v` to the `tests` job, placed after the `catalog/hooks/tests/` step and before the extension editable-install steps. This is a strictly-additive change; no existing step was modified or removed. The pre-existing CI gap (the `tests/integrations/` and `tests/installer/` dirs were never wired into CI even though they existed in v2.1.0) was applied alongside Phase 1's new tests because Phase 1 enlarges the affected surface materially (+71 assertions).

## Deviations from the plan

- T002: the plan referenced separate `uninstall_global` / `uninstall_workspace` methods matching the CodeGraph TypeScript interface. Nexus-Hub's manifest is scope-agnostic, so the existing single `teardown(ctx)` method was retained as the implementation; `uninstall_global` / `uninstall_workspace` were added as thin dispatchers that delegate to `teardown` (preserving the CodeGraph naming for future scope-specific cleanup needs).
- T004: the plan listed Copilot among the integrations to migrate to `merge_marker_section`. Copilot's bespoke `## Nexus-Hub Harness` append-after-heading pattern was retained unchanged to minimize surface change; the `instruction_mode = "shared"` attribute was set for documentation but is informational on that subclass. Logged as MT-1 in `docs/archive/v2/v2.2/known-gaps.md` so Phase 3's parameterized contract suite can drive the refactor.

## Known gaps surfaced

See `docs/archive/v2/v2.2/known-gaps.md`:
- **DF-001** -- carried forward from v2.1.0; byte-identical parity migration for the original 4 platforms. Phase 3 sub-tasks T020 / T021 discharge it.
- **MT-1** -- Copilot retains bespoke install path; Cursor `.mdc` rules pipeline still does raw writes. Phase 3's contract suite will surface drift.
- **WN-1** -- `pathspec` `GitWildMatchPattern` deprecation warning in nexus-code-search tests (pre-existing, third-party library). Pin to `gitignore` mode in v2.3.0.

## Files touched

**New files (10)**:
- `scripts/lib/integrations/result.py`
- `scripts/lib/installer/__init__.py`
- `scripts/lib/installer/instruction_merge.py`
- `tests/integrations/test_result.py`
- `tests/integrations/test_base_writeresult.py`
- `tests/integrations/test_markdown_integration.py`
- `tests/installer/test_instruction_merge.py`
- `extensions/nexus-skill-server/tests/test_initialize.py`
- `extensions/nexus-code-search/tests/test_initialize.py`
- `extensions/nexus-web-fetch/tests/test_initialize.py`

**Modified files (16)**:
- `scripts/lib/integrations/__init__.py` (re-export new types)
- `scripts/lib/integrations/base.py` (lifecycle methods return `WriteResult`; shared/dedicated `_write_instruction`; teardown overridden)
- `scripts/lib/integrations/manifest.py` (`track_shared` / `untrack_shared` / `shared_for`)
- `scripts/lib/integrations/runner.py` (`_render_write_result` printer)
- `scripts/lib/integrations/{antigravity,claude,codex,copilot,cursor,gemini,gemini_cli,nexus_ai,opencode}.py` (declare `instruction_mode`; thread `WriteResult` through overrides)
- `extensions/nexus-skill-server/src/nexus_skill_server/server.py` (SERVER_INSTRUCTIONS + initialize wire-up)
- `extensions/nexus-code-search/src/nexus_code_search/server.py` (SERVER_INSTRUCTIONS + initialize wire-up)
- `extensions/nexus-web-fetch/src/nexus_web_fetch/server.py` (SERVER_INSTRUCTIONS + initialize wire-up)
- `.github/workflows/ci.yml` (added `tests/integrations tests/installer` step)

**Generated docs**:
- `docs/archive/v2/v2.2/known-gaps.md`
- `docs/archive/v2/v2.3/docs-cleanup-report.md`
- `docs/DEVLOG.md` (entry appended at top)

## Next steps

Advance to Phase 2 (Gemini-to-Antigravity CLI transition). Phase 2 is time-critical (ship before 2026-06-18) and is positioned in the plan immediately after Phase 1 so it can be cut and released independently if Phases 3-6 slip. The new `WriteResult` vocabulary + marker-delimited merge primitive are direct prerequisites for Phase 2.7's `--enterprise` flag flow and Phase 2.5's split base-google-shared template.
