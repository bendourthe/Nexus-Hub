# DevAI-Hub v1.3.0 - Release Notes

**Release date**: 2026-05-12
**Type**: MINOR (additive; no breaking changes)
**Previous version**: v1.2.1

## Headline

A structured way to clean up cluttered `docs/` folders. Every file gets a category, the agent proposes a version-first reorganization with a dedicated archive subtree, and changes only apply after explicit user confirmation.

## What ships

### New skill: `docs-layout-refactor`

Audit-then-confirm-then-apply workflow for the `docs/` directory. Eight weighted heuristics classify every file into one of four categories:

| Cat | Disposition |
|---|---|
| **Cat 1** | Safe to delete outright |
| **Cat 2** | Archive under `docs/archive/<source-version>/<topic>/` |
| **Cat 3** | Stale but load-bearing - flag for refresh, no file action |
| **Cat 4** | Transient or currently active - revisit later |

Heuristics include version-vs-active, external reference count (hard floor at Cat 3), filename pattern, age, sha256 duplication, CHANGELOG citation (hard floor at Cat 2), body keywords, and inbound-link count. The skill bundle ships a stdlib-only Python helper (`audit-docs.py`) plus a PowerShell wrapper for Windows users.

### New command: `/refactor-docs`

Wraps the skill in a 10-phase orchestration: resolve scope and mode -> inventory -> reference graph -> categorize -> propose target layout -> generate report -> confirmation gate -> execute -> repair references -> verify. Propose-only is the default; `--apply` turns on the gate. The `--mode audit` flag (used when chained from other commands) skips the gate entirely and writes only the report.

Flags: `--apply`, `--mode audit|full`, `--scope <subpath>`, `--output <path>`, `--keep-current-version` (default ON), `--migrate-known-gaps`.

### New hook: `old-version-docs-guard`

PreToolUse hook that warns when Write or Edit targets a historical `docs/v<old-version>/` path. Non-blocking by default; the `DEVAI_OLD_DOCS_GUARD=block` env var upgrades to a hard block. Ships with a PowerShell sibling for Windows parity.

### New bundle: `release-prep`

Groups seven skills for one-click release-prep installation:

1. `docs-layout-refactor` (new)
2. `project-layout-refactor`
3. `documentation-consistency`
4. `version-upgrade`
5. `release-notes-writer`
6. `known-gaps-tracker`
7. `code-commit-workflow`

### Integrations

The new command slots into the existing release chain at safe defaults:

| Command | Integration | Mode |
|---|---|---|
| `/wrap-up-session` | New Step 2c after `refactor-project-layout` | audit-only |
| `/update-version` | New Step B4 after `update-gitignore` | propose-then-apply with gate |
| `/run-deep-review` | New subsection 4.11 in Phase 4 | audit-only |
| `/review-codebase` | Advisory bullet in Phase 6f | audit-only |

The `--migrate-known-gaps` flag bridges to the `known-gaps-tracker` skill: Cat 3 (stale but load-bearing) findings auto-promote into `docs/<next-version>/known-gaps.md` under a `## Stale documentation flagged by /refactor-docs` section, deduplicating by file path.

## Migration

Re-run the installer. Everything lands at its target path automatically:

- The skill bundle at `~/.claude/skills/docs-layout-refactor/` (and the equivalent paths for Codex, Gemini).
- The command at `~/.claude/commands/refactor-docs.md`.
- The hook scripts at `~/.claude/hooks/old-version-docs-guard.{sh,ps1}` (registered in `~/.claude/settings.json` under `PreToolUse` for Write and Edit).
- The bundle in `data/bundles.json` (downloadable via the marketplace).

**No breaking changes.** Existing user customizations are preserved. The four chained commands default to safe modes (audit-only or with a confirmation gate). Pre-existing workflows that did not use the new skill are unaffected.

## What this skill replaces

Nothing. It complements three existing skills without overlapping:

- `update-documentation` checks **content accuracy** of docs (factually correct against the code). `docs-layout-refactor` checks **folder structure**.
- `project-layout-refactor` reorganizes **repo-root** files. `docs-layout-refactor` operates strictly under `docs/`.
- `known-gaps-tracker` tracks **per-version unfinished work**. `docs-layout-refactor` flags **stale documentation** as Cat 3 (refresh queue) but does not migrate findings unless `--migrate-known-gaps` is set.

## Verification

- `python scripts/validate_skills.py --bundles-only` passes (0 errors, 4 pre-existing warnings carried from WN-001).
- 364 pytest tests pass; 3 skip without `jq` installed (the warning-path tests for the new hook; consistent with `large-file-guard.sh` and `secret-scan.sh`).
- `audit-docs.py inventory --root ./docs` emits valid NDJSON for every file in the repo's own `docs/`.
- `audit-docs.py refgraph --root ./docs --repo-root .` correctly identifies inbound references to `docs/DEVLOG.md` from `README.md`, `AGENTS.md`, and workflow skills.

## Files added

- `catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md`
- `catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py`
- `catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.ps1`
- `catalog/skills/code-cleanup/docs-layout-refactor/references/archive-layout.md`
- `catalog/commands/refactor-docs.md`
- `catalog/hooks/old-version-docs-guard.sh`
- `catalog/hooks/old-version-docs-guard.ps1`
- `catalog/hooks/tests/test_old_version_docs_guard.py`
- `docs/archive/v1/v1.3/RELEASE_NOTES.md` (this file)

## Files changed

- `catalog/commands/wrap-up-session.md` (Step 2c)
- `catalog/commands/update-version.md` (Step B4)
- `catalog/commands/run-deep-review.md` (subsection 4.11)
- `catalog/commands/review-codebase.md` (Phase 6f advisory)
- `catalog/hooks/settings.json` (register old-version-docs-guard for Write and Edit)
- `data/SKILL_INDEX.md`
- `data/skills.json`
- `data/marketplace.json`
- `data/bundles.json` (new release-prep bundle, version bump)
- `data/workflows.json`, `data/templates.json` (version bump)
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (counts + version)
- `AGENTS.md`, `README.md` (counts + What's New)
- `scripts/installer.sh`, `scripts/installer.ps1` (version banner)
- `CHANGELOG.md`

## Self-classification

This release notes file classifies itself as Cat 4 (transient/active) for the duration of the v1.3.0 release cycle. After v1.4.0 ships, a follow-up `/refactor-docs` run will promote it to Cat 2 and archive it under `docs/archive/v1.3.0/RELEASE_NOTES.md`.
