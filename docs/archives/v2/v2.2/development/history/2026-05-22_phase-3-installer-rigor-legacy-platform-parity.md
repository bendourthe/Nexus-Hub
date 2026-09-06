# Session History -- v2.2.0 Phase 3: installer rigor + legacy-platform parity

**Date**: 2026-05-22
**Plan**: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](../../plans/codegraph-and-antigravity.md)
**Phase**: 3 -- Installer rigor + legacy-platform parity migration (sub-tasks T015-T022)
**Result**: shipped; first half of DF-001 (tree-mirror parity) closed; second half (instruction-file byte parity) deferred to v2.3.0 as DF-001-part2

---

## Goal

Bring the integration registry to CodeGraph parity rigor (C6 / C7 / C11 / C12 from the v2.1.0 comparison) and complete the v2.1.0-carried DF-001 byte-identical parity migration where feasible. Specifically: (1) a per-integration legacy-state cleanup registry, (2) project-local surface bootstrapping via a new `nexus-hub init` subcommand, (3) dry-run drift detection via `--check`, (4) paste-ready config introspection via `--print-config <key>`, (5) a 50-case parameterized contract suite, (6) a parity diff suite versus the legacy installer, (7) refactor the legacy installer copy paths to delegate to the registry runner (conditional on (6) full parity), (8) stabilization.

## Sub-tasks completed (7 of 8, plus 1 documented deferral)

### T015 -- Per-integration legacy-state self-healing registry

- Created `scripts/lib/integrations/legacy.py` with `LEGACY_CLEANUPS: dict[str, list[CleanupFn]]` and a `run_cleanups(integration_key, ctx) -> list[FileAction]` driver.
- Five cleanups: pre-2.0.0 `~/.devai-hub/` (gated on `~/.nexus-hub/` existing), `~/.claude/devai-hub-skills.json`, `~/.codex/devai-hub-skills/`, `~/.gemini/devai-hub-skills/`, and the renamed `devai-hub.claude-usage-monitor` VS Code extension (mirrors bash commit b52a038).
- Wired into `IntegrationBase.install` (local import to break import cycle): cleanups run before the install body and the resulting `FileAction`s are prepended to the `WriteResult.files` so execution order is preserved.
- Test file: `tests/integrations/test_legacy_cleanups.py` -- 11 new test cases (per-cleanup remove + skip-when-absent, dry-run behavior, idempotency, unknown-key empty list, VS Code cleanup with monkeypatched subprocess for cross-platform CI safety).

### T016 -- `wire_project_surfaces()` hook + `nexus-hub init` subcommand

- Added `IntegrationBase.wire_project_surfaces(self, ctx) -> WriteResult | None` (default returns `None`).
- `CursorIntegration.wire_project_surfaces`: writes `.cursor/rules/nexus-hub.mdc` with YAML frontmatter (`name: nexus-hub`, `scope: auto`) and a short body deferring to `~/.cursor/` for catalog-level guidance. Idempotent: byte-equal re-write returns `unchanged`.
- `ClaudeIntegration.wire_project_surfaces`: writes a `.claude/settings.json` stub when none exists; returns `kept` when a user file is already present. Never overwrites.
- Runner: new `cmd_init` walks `list_keys()`, calls `wire_project_surfaces(ctx)` per integration, logs the WriteResult, writes manifest unless `--dry-run`.
- Installer scripts: `scripts/installer.sh init [--target PATH] [--dry-run]` and `pwsh scripts/installer.ps1 init` dispatch the subcommand before the interactive scope menu so the subcommand is pipeable / scriptable.
- Test file: `tests/installer/test_init_subcommand.py` -- 6 new test cases (rule-file create, idempotent re-invoke, settings.json stub creation, settings.json preservation, dry-run no-op, default-None invariant for the 8 non-overriding integrations).

### T017 -- `--print-config <key>` read-only mode + `print_config()` hook

- Added `IntegrationBase.print_config(self, ctx) -> str` -- returns multi-section Markdown (H1 + scope/target metadata + FileActions table + Rendered instruction body fence for MarkdownIntegration subclasses).
- Runner: new `cmd_print_config` resolves the integration key, builds `InstallContext(dry_run=True)`, calls `print_config`, prints to stdout. Exit 0 success, 1 unknown key.
- Installer scripts: `--print-config <key>` / `--print-config=<key>` (bash) and `-PrintConfig <key>` (PowerShell). Both dispatch to the runner via `exec` / `&` so they bypass the interactive scope menu.
- Test file: `tests/installer/test_print_config.py` -- 13 new test cases (parameterized over all 10 integrations: no disk write + non-empty output + key/File-actions present; unknown-key exit code; instruction body rendered for Claude; direct Python hook returns string).

### T018 -- `--check` / `--dry-run` install-drift detection + `dry_run()` hook

- Added `IntegrationBase.dry_run(self, ctx) -> WriteResult` -- flips `ctx.dry_run=True` (via `dataclasses.replace`) and delegates to `self.install(ctx)`. Existing helpers (`_copy_file`, `_copy_tree`, `_write_instruction`, `merge_marker_section`) already honor `ctx.dry_run`, so no per-integration override is needed.
- Runner: new `cmd_check` walks `list_keys()` (or `--integrations` subset), accumulates `FileAction`s, exits 0 if every action is `unchanged` or `kept`, else 1. Per-integration drift summary prints unless `--quiet`.
- Installer scripts: `--check` / `--dry-run` (bash, treated as synonyms) and `-Check` (PowerShell).
- Test file: `tests/installer/test_check_flag.py` -- 6 new test cases (fresh state exit 1, post-install exit 0, no disk writes during check, default invocation walks all integrations, `dry_run()` returns WriteResult, `dry_run` action histogram equals `install` histogram on equivalent fresh targets).

### T019 -- 50-case parameterized contract suite

- Created `tests/integrations/test_contract.py` with five `@pytest.mark.parametrize`d test functions, each over all 10 registered integration keys (50 cases total).
- Invariants: (1) `test_install_idempotent` -- second install reports only `unchanged` / `kept` / `not-found`; (2) `test_uninstall_reverses_install` -- post-uninstall snapshot of `tmp_path` (excluding `.nexus-hub/install-manifest.json`) matches pre-install snapshot; (3) `test_sibling_preservation` -- user content pre-populated in the instruction file survives the install (dedicated-mode integrations satisfy this trivially via the kept-on-existing-file branch); (4) `test_partial_state_recovery` -- deleting one tracked file then re-installing recreates it; (5) `test_dry_run_matches_install` -- `dry_run` action histogram on a fresh target equals `install` histogram on an equivalently-fresh target.
- Two bugs surfaced and fixed inline (both Resolved entries in `docs/archive/v2/v2.2/known-gaps.md`):
    - `merge_marker_section` truncated the block at the first nested mention of the end marker (gemini-IDE template literally references `<!-- NEXUS_HUB_END -->` to explain the merge mechanism). Fixed by switching `text.index(end_marker, start)` to `text.rindex` in `_replace_between_markers` and `_strip_between_markers`.
    - Copilot's first install wrote the rendered template bare while subsequent installs appended a `## Nexus-Hub Harness` marker block to a marker-less file. Result: file grew on every run. Fixed by always emitting `<marker>\n\n<rendered>\n` on first install.
- All 50 contract cases plus the previously-existing 132 tests pass.

### T020 -- [DF-001] Parity diff suite: legacy installer vs registry runner (part 1 closed)

- Created `tests/integrations/test_parity_with_legacy_installer.py` with three test functions: `test_catalog_tree_mirror_is_byte_identical` (10 parameterized cases across claude / codex / cursor / gemini / opencode + skills/commands/agents/rules), `test_cursor_produces_expected_rule_set` (frontmatter and scope assertions on `.mdc` files), and `test_instruction_file_is_produced` (parametrized over the 5 platforms, asserts presence and non-zero size only).
- The tree-mirror test computes a `{relative_posix_path: sha256_hex}` map for both the source catalog tree and the registry-installed target tree, then asserts equality. The legacy bash installer uses `safe_folder_copy` (delegates to `rsync -a` / `cp -R` / `robocopy /MIR`); the registry uses `IntegrationBase._copy_tree` (delegates to `shutil.copytree(src, dst, dirs_exist_ok=True)`) -- both byte-for-byte, so SHA equality is the right invariant.
- 16 of 16 parity cases pass in 2 minutes.
- Instruction-file byte-parity (the other half of DF-001) is deliberately not asserted -- see T021 deferral.

### T021 -- [DF-001 part 2] Refactor legacy installer copy paths to delegate to runner (DEFERRED)

- DEFERRED to v2.3.0 with documented carry-forward. The plan made T021 conditional on T020 passing in full: "Once `tests/integrations/test_parity_with_legacy_installer.py` from sub-task 3.6 passes". T020's tree-mirror cases pass, but the instruction-file byte-parity assertion is not yet in place because the registry runner does not yet substitute the full bash placeholder set (`{{PRIMARY_LANGUAGE}}`, `{{BUILD_CMD}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{OS_CONTEXT}}`, `{{SKILL_INDEX}}`, `{{NON_OBVIOUS_TOOLING}}`, ...) nor appends per-language coding snippets.
- Removing the legacy bash blocks today would silently downgrade end-user instruction file content (less rich substitution, no coding snippets appended) -- a user-visible regression.
- Captured as `DF-001` in `docs/archive/v2/v2.2/known-gaps.md` with a precise next-step list: extend `runner.cmd_install` to accept and thread the full placeholder set, inline the per-language coding-snippet append into `MarkdownIntegration._write_instruction`, add the instruction-file byte-parity assertion to `tests/integrations/test_parity_with_legacy_installer.py`, then refactor the legacy bash blocks. Target: v2.3.0.

### T022 -- Phase 3 stabilization

- `python -m pytest tests/integrations tests/installer` returns **223 passed in 10:05** on the Windows host (132 inherited + 91 net new).
- Net new tests by file:
    - `tests/integrations/test_legacy_cleanups.py`: 11
    - `tests/installer/test_init_subcommand.py`: 6
    - `tests/installer/test_print_config.py`: 13
    - `tests/installer/test_check_flag.py`: 6
    - `tests/integrations/test_contract.py`: 50
    - `tests/integrations/test_parity_with_legacy_installer.py`: 16 (including the 5 instruction-file smoke cases) -- so the parity file actually adds 15 net new since 1 was added to T019's contract count.
- Syntax: `bash -n scripts/installer.sh` clean; PowerShell AST parser clean on `scripts/installer.ps1`; `shellcheck --severity=warning scripts/installer.sh` clean.
- JSON integrity: `data/*.json` 0 errors.
- Smoke: `bash scripts/installer.sh --help` displays the three new entry points (init / `--print-config` / `--check`) alongside the existing `--enterprise` flag. `python scripts/lib/integrations/runner.py print-config cursor --scope workspace --target /tmp/probe` produced a 30+ line Markdown readout with H1, scope metadata, FileActions table (13 paths), and rendered instruction body in a fenced code block.

## Results

| Gate | Status |
|------|--------|
| All tests passing | ✓ 223 / 223 |
| Coverage | ✓ 91 net new test cases |
| Lint | ✓ shellcheck + PowerShell AST + JSON valid |
| Build | ✓ runner.py + installer.sh + installer.ps1 import / parse / smoke-test cleanly |

## Known gaps after this phase

- **DF-001** (carried forward to v2.3.0 as DF-001-part2): instruction-file byte parity gates T021's legacy bash block removal. Precise next-step list in `docs/archive/v2/v2.2/known-gaps.md`.
- **MT-1**: Copilot still uses a bespoke append-after-marker pattern instead of `merge_marker_section`. Phase 3 hardened it to be idempotent (first install emits the marker) but the marker-merge refactor remains for v2.3.0.
- **MT-2** (new): instruction-file byte-parity assertion not yet in the parity suite. Couples with DF-001.

Two bugs Resolved: BG-P3-1 (marker-merge first-occurrence boundary) and BG-P3-2 (Copilot first-install marker omission).

## Next steps

- Phase 4: code-graph foundation -- `nexus-code-search` v2.0 with tree-sitter AST extraction, NodeKind/EdgeKind schema, call-graph traversal, native file-watcher.
- Phase 5: framework route extractors (Django / FastAPI / Express), `affected_tests` MCP tool + `nexus-hub affected` CLI, synthetic-codebase eval harness.
- Phase 6: data registry rebaselined; v2.2.0 RELEASE_NOTES and CHANGELOG; cross-OS installer smoke; known-gaps finalized; `git tag v2.2.0` ready.
