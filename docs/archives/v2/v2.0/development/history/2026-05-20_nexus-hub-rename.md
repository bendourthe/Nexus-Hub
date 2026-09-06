# Session History: v2.0.0 - Nexus-Hub Rename (Cumulative)

**Date**: 2026-05-19 to 2026-05-20
**Scope**: Phases 1 through 8 of `docs/archive/v2/v2.0/plans/nexus-hub-rename.md`
**Outcome**: DevAI-Hub renamed to Nexus-Hub; v2.0.0 release ready to tag.
**Plan reference**: [docs/archives/v2/v2.0/plans/nexus-hub-rename.md](../../plans/nexus-hub-rename.md)

## Goal recap

Rename the repository, distributed artifact, plugin metadata, installer, MCP servers, extensions, scripts, all 203 skills, 33 commands, 14 hooks, 10 agents, rules, templates, and every documentation surface from DevAI-Hub to Nexus-Hub. Modernize the README around the new brand with explicit linkage to the sibling Nexus desktop app. Redesign the installer to print an ASCII-art `NEXUS-HUB` banner and migrate users cleanly from `~/.devai-hub/` to `~/.nexus-hub/`. Close two carry-forward known-gaps from v1.3.0 (WN-001 framework-specialist orphan-bundle warnings, WN-002 Windows `make`/`shellcheck` UTF-8 codec workaround).

## Chronology by phase

### Phase 1 - Foundation, Inventory, Naming Canon (commit `3678338`)

- Captured pre-rename validator baselines at `docs/archive/v2/v2.0/baselines/` (`validate-skills-pre.txt`, `hook-tests-pre.txt`, `extension-tests-pre.txt`). Baseline: 207 skills scanned, 4 WN-001 warnings, 366 hook tests passed + 3 skipped, all three extensions green.
- Wrote `docs/archive/v2/v2.0/rename-inventory.md` (directory renames, file renames, variant table, cross-link targets, asset transfer, reference counts) and `docs/archive/v2/v2.0/rename-decisions.md` (locked canonical name forms; chose in-place installer migration over symlink shim; recorded `v1.4.0 -> v2.0.0` SemVer major bump rationale).

### Phase 2 - Catalog Metadata and `data/` Registries (commit `fb59c96`)

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: name, description, repo, homepage rewritten.
- `data/skills.json`, `data/marketplace.json`, `data/bundles.json`, `data/SKILL_INDEX.md`: variant replacements applied (the `using-devai-hub` skill name updated in advance of its directory rename in Phase 5).
- Root configs: `.pr_agent.toml`, `Makefile`, `.github/copilot-instructions.md`.
- Top-level AI-agent instruction files: `AGENTS.md` (with the rewritten Repository Overview paragraph framing Nexus-Hub as the upstream catalog for Nexus), `CLAUDE.md` (headline + `~/.nexus-hub/style-guides/` reference).

### Phase 3 - Installer Rebrand + ASCII Banner + Migration (commit `82649f7`)

- `print_nexus_banner()` / `Write-NexusBanner` added to both installers with a hand-crafted ASCII NEXUS-HUB wordmark plus tagline and version + URL line.
- `migrate_legacy_install()` / `Invoke-LegacyInstallMigration` added to detect `~/.devai-hub/` and perform a one-shot in-place rename with three handled cases (legacy-only, both-exist, neither-exists).
- 4 new tests in `catalog/hooks/tests/test_installer_smoke.py` assert the banner functions and migration branches in both installers. Total smoke tests: 26.
- `install.sh`, `install.bat`, installer paths, env var prefixes, prose all updated.

### Phase 4 - Extensions, Internal MCPs, scripts/ Rename (commit `765f39f`)

- Three extension directory renames via `git mv` so history is preserved:
    - `extensions/devai-skill-server` -> `extensions/nexus-skill-server`
    - `extensions/devai-code-search` -> `extensions/nexus-code-search`
    - `extensions/devai-web-fetch` -> `extensions/nexus-web-fetch`
- Nested Python packages renamed (`src/devai_*` -> `src/nexus_*`), all `import` statements and `pyproject.toml` package configs updated.
- `catalog/mcp-configs/mcp-servers.json` registry keys and spawn commands rewritten.
- `scripts/devai_mcp_benchmark.py` -> `scripts/nexus_mcp_benchmark.py`; `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1`. Both installers' explicit-name script copy steps updated.
- Extension test sweep at phase close: 37 + 36(s) + 23 passed, unchanged from pre-rename baseline.

### Phase 5 - Hooks, Commands, Skills, Rules, Templates Sweep (commit `9b87c56` + fixup `7ab2707`)

- Bulk textual rename via `scripts/apply_rename.py` across 203 skills, 33 commands, 14 hooks, 10 agents, all 4 rule families, every style-guide and checklist, both context and memory template files. Manifest at `docs/archive/v2/v2.0/rename-manifest.txt`.
- All 5 `templates/ai-instructions/base-*.md` updated in lockstep per the platform-agnostic rule.
- `catalog/skills/workflow/using-devai-hub/` -> `using-nexus-hub/` (directory + SKILL.md frontmatter + body content).
- `.cursor/rules/devai-hub.mdc` -> `nexus-hub.mdc`.
- **Troubleshooting**: a follow-up commit (`7ab2707`) was needed to catch residual `DEVAI_` env-var references and `DEVAI-` ASCII-banner artifacts that the bulk-rename script's variant ordering had missed.

### Phase 6 - README Modernization + Nexus Brand Linkage (commit `b85425c`)

- `README.md` rewritten from scratch around the 11-section spec: centered title hero, one-paragraph pitch, "Renamed from DevAI-Hub at v2.0.0" callout, dedicated "How Nexus-Hub fits with Nexus" block, "What's New in v2.0.0" subsections, platform compatibility matrix, Quick Start updated to `~/.nexus-hub/`, retained New/Inherited workflows, v2.0.0+ roadmap, collaboration footer.
- `README_zh.md` Chinese-language equivalent: H1 + live prose renamed inline; v1.0.0 historical block preserved per `rename-decisions.md` historical-snapshot policy. DF-005 logged.
- Six nested extension/script READMEs synced.
- **Troubleshooting (DF-004)**: the plan instructed copying `nexus_primary.png` / `nexus_monochrome.png` from the sibling `Nexus-AI` repo's `assets/` directory, but the sibling repo path (`C:\Users\bdour\...`) lives on a different Windows account and is not reachable from this `BEDOURTHE` session. The hero block ships as text-only; a follow-up asset transfer is tracked as DF-004 in `docs/archive/v2/v2.0/known-gaps.md`.

### Phase 7 - Docs / Config / DevLog / Gitignore Sync + CHANGELOG (commit `e5bd094`)

- `/update-documentation`: 8 guides + `docs/CATALOG-COVERAGE.md` + `docs/permissions-setup.md` rebranded. Manifest at `docs/archive/v2/v2.0/documentation-sync-manifest.md`.
- `/update-config`: catalog/hooks/settings.json, configs/permissions, mcp-servers, all 5 base templates verified clean; per-user surfaces flagged for installer-driven update. Manifest at `docs/archive/v2/v2.0/config-sync-manifest.md`.
- `/update-devlog`: new Phase 7 entry + backfilled Phase 6 entry in `docs/DEVLOG.md`.
- `/update-gitignore`: `.gitignore` audited clean. Audit document at `docs/archive/v2/v2.0/gitignore-audit.md`.
- `CHANGELOG.md` `## [2.0.0]` block written with six subsections (Renamed / Breaking changes / Added / Changed / Tests / Migration / Carry-overs).
- `docs/archive/v2/v2.0/RELEASE_NOTES.md` expanded from stub to full release notes: summary, How Nexus-Hub fits with Nexus block, migration story, complete 22-row old-path / new-path reference table.
- **Troubleshooting (BG-001)**: the 7.6 stability gate residual-rename grep surfaced 5 active surfaces that Phase 5.1 had missed (`CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `GEMINI.md`, `SECURITY.md`, `data/report_data.json`); all rebranded in the same Phase 7 commit. Separately, `infrastructure/tools/build_skills_catalog.py` was found to carry 4 hardcoded DevAI literals that would have regressed `data/` on next `make build-catalog`. BG-001 was logged and closed in the same commit.

### Phase 8 - Validation, Carry-Forward Known-Gaps, Version Bump (this commit)

- **8.1**: Post-rename baselines captured at `docs/archive/v2/v2.0/baselines/{validate-skills,hook-tests,extension-tests}-post.txt`. Validator green, 0 errors / 0 warnings after 8.3 fix (was 0 errors / 4 warnings at run start). Hook tests: 370 passed + 3 skipped (366 baseline + 4 new installer-migration smoke tests added in Phase 3.3). Extensions: 37 + 36(s) + 23 unchanged. Validation diff document at `docs/archive/v2/v2.0/baselines/validation-diff.md`.
- **8.2**: Cross-platform installer smoke captured at `docs/archive/v2/v2.0/installer-smoke-post.txt`. All 26 assertions in `test_installer_smoke.py` PASS (banner, version constant, migration branches, syntax cleanliness, AST parse). macOS smoke deferred per WN-002 limitation.
- **8.3**: **WN-001 closed** by adding a `## References` section to `fastapi-expert/SKILL.md`, `nextjs-expert/SKILL.md`, and `react-expert/SKILL.md`, linking the 4 orphan reference files with one-line topic summaries. **WN-002 closed** by patching the four inline `python -c "json.load(open(...))"` calls in the Makefile `validate` target to pass `encoding='utf-8'`, plus writing `docs/dev-environment-windows.md` to document `scoop install make`, `scoop install shellcheck`, and `PYTHONUTF8=1` user env var setup.
- **8.4**: Version literal bumped from `1.4.0` to `2.0.0` in 8 source-of-truth files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `data/marketplace.json`, `scripts/installer.sh` (`NEXUS_HUB_VERSION`), `scripts/installer.ps1` (`$script:NexusHubVersion`), `extensions/nexus-skill-server/pyproject.toml`, `extensions/nexus-code-search/pyproject.toml`, `extensions/nexus-web-fetch/pyproject.toml`. Extension versions aligned to 2.0.0 to clearly signal the rebrand-major-bump; prior internal release histories (0.1.0 / 1.0.0 / 1.0.0) preserved in git.
- **8.5**: This session-history document authored; `docs/archive/v2/v2.0/known-gaps.md` finalized (status `finalized`, WN-001 and WN-002 in the Resolved table, 2 open items remaining = DF-004 and DF-005 both intentional deferrals from Phase 6).

## Commit timeline

| Phase | Commit | Title |
|---|---|---|
| 1 | `3678338` | v2.0.0: phase 1 foundation, inventory, and rename decisions |
| 2 | `fb59c96` | feat(v2.0.0): phase 2 catalog metadata rename to nexus-hub |
| 3 | `82649f7` | feat(v2.0.0): phase 3 installer rebrand and migration |
| 4 | `765f39f` | feat(v2.0.0): phase 4 extensions, MCPs, and brand-bearing scripts renamed |
| 5 | `9b87c56` + `7ab2707` | feat(v2.0.0): phase 5 catalog bulk rename + fix(v2.0.0) residual DEVAI_ misses |
| 6 | `b85425c` | feat(v2.0.0): phase 6 README modernization and Nexus brand linkage |
| 7 | `e5bd094` | feat(v2.0.0): phase 7 docs / config / devlog / gitignore sync and CHANGELOG / RELEASE_NOTES |
| 8 | (this commit) | feat(v2.0.0): phase 8 validation, carry-forward known-gaps close, version bump |

## Validation results (final)

| Check | Result |
|---|---|
| `python scripts/validate_skills.py --bundles-only` | PASS, 0 errors, 0 warnings (was 0 errors, 4 warnings pre-8.3) |
| `pytest catalog/hooks/tests` | 370 passed, 3 skipped |
| `extensions/nexus-skill-server` pytest | 37 passed |
| `extensions/nexus-code-search` pytest | 36 passed, 1 skipped |
| `extensions/nexus-web-fetch` pytest | 23 passed |
| 6-file JSON parse-check | All clean |
| `bash -n` over installer.sh + hooks + install.sh | Clean |
| PowerShell AST parse of installer.ps1 | Clean |
| Final residual-rename grep (excluding documented surfaces) | 0 unintended matches |

## Troubleshooting summary

- **Phase 5 -> 5 fixup (`7ab2707`)**: bulk-rename variant ordering missed `DEVAI_` env-var prefixes that did not have a kebab-case sibling. Fix: a follow-up commit ran the same script with the explicit `DEVAI_` -> `NEXUS_` variant first.
- **Phase 6 DF-004 (open)**: sibling Nexus repo not reachable from this dev machine; PNG hero assets deferred. README ships text-only hero.
- **Phase 6 DF-005 (open)**: `README_zh.md` v1.0.0 historical block left as-is per the historical-snapshot policy; explicit rename notice prepended.
- **Phase 7 BG-001 (closed)**: `infrastructure/tools/build_skills_catalog.py` carried 4 hardcoded DevAI literals; closed in the Phase 7 commit before BG-001 could regress `data/`.
- **Phase 8 8.3 WN-001 (closed)**: 4 orphan-bundle references linked from parent SKILL.md.
- **Phase 8 8.3 WN-002 (closed)**: Makefile patched for UTF-8; Windows dev-environment guide written.

## Next steps (pending user action)

1. **Push the v2.0.0 tag**: `git tag` is cut as part of Phase 8.5; the push is deferred per the global rule on destructive / remote-mutating git operations. User must explicitly run `git push origin v2.0.0` after final review.
2. **Rename the GitHub repo**: from `bendourthe/DevAI-Hub` to `bendourthe/Nexus-Hub` via GitHub.com settings UI. GitHub's automatic redirect handles the transition window for any external links that still point at the old URL.
3. **Update the sibling Nexus repo's README**: the `Nexus-AI` repo's README references `bendourthe/DevAI-Hub`; update the link to `bendourthe/Nexus-Hub` in a follow-up commit on that repo (out of scope for this plan).
4. **DF-004 follow-up**: when the sibling Nexus repo is accessible on a machine, copy `nexus_primary.png` and `nexus_monochrome.png` into `assets/` and patch the README hero to use `<img src="assets/nexus_primary.png">`. Write `LICENSE-ASSETS.md` per Phase 6.1.
5. **Future hygiene**: cross-OS CI smoke matrix (Windows + macOS + Linux installer dry-runs in CI) tracked as v2.0.x or v2.1.0 hygiene item.

## Files produced during Phase 8

- `docs/archive/v2/v2.0/baselines/validate-skills-post.txt`
- `docs/archive/v2/v2.0/baselines/hook-tests-post.txt`
- `docs/archive/v2/v2.0/baselines/extension-tests-post.txt`
- `docs/archive/v2/v2.0/baselines/validation-diff.md`
- `docs/archive/v2/v2.0/installer-smoke-post.txt`
- `docs/dev-environment-windows.md`
- `docs/archive/v2/v2.0/development/history/2026-05-20_nexus-hub-rename.md` (this file)
- Updates to `Makefile`, `docs/archive/v2/v2.0/known-gaps.md`, three framework-specialist `SKILL.md` files, 8 version-literal files.
