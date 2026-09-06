# Session History -- 2026-05-20 -- v2.0.0 Phase 5 (catalog bulk rename, lockstep templates, disk renames)

**Plan**: [docs/archives/v2/v2.0/plans/nexus-hub-rename.md](../../plans/nexus-hub-rename.md)
**Phase**: 5 -- Hooks, Commands, Skills, Rules, Templates Sweep
**Status**: complete
**Date**: 2026-05-20

## Goal

Bulk-rename every brand variant out of `catalog/`, `templates/`, and `.cursor/`. Update all five `templates/ai-instructions/base-*.md` AI-instruction templates in lockstep so the rename is platform-agnostic (claude / codex / cursor / gemini / opencode all see the same change). Rename the two on-disk artifacts whose names still carry the old brand: the `using-devai-hub` skill directory and the `.cursor/rules/devai-hub.mdc` rule file. Confirm all four stability gates remain green and the post-rename grep returns NOTHING.

## Sub-tasks Completed

### 5.1 Catalog bulk textual rename

Wrote `scripts/apply_rename.py`, an idempotent Python helper that walks `catalog/`, `templates/`, and `.cursor/` applying variants in length-descending order and writes a per-file manifest to `docs/archive/v2/v2.0/rename-manifest.txt`.

The script was run twice during this phase:

- **Pass 1** applied variants 1-6 from `docs/archive/v2/v2.0/rename-inventory.md` (`DevAI-Hub`, `DEVAI-HUB`, `DEVAI_HUB`, `DevAI Hub`, `devai-hub`, `devai_hub`). Result: 66 files rewritten, 177 replacements, 170 changed lines.
- **Pass 2** added variants 7-14 (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`, the snake-case Python package ids `devai_skill_server` / `devai_code_search` / `devai_web_fetch`, `devai_mcp_benchmark`, and `devai-backup`). Pass 2 caught 7 files that pass 1 had left untouched: 4 SKILL.md bodies referencing the internal MCP server keys, 2 command Markdown files (`install-pre-commit-review-hook.md` for the pre-commit-backup pattern; `run-deep-review.md` for an example path), and `catalog/skills/orchestration/context-manager/SKILL.md`. Pass 2 result: 32 replacements across 25 lines.

The script was added to `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` so the `test_installers_copy_every_scripts_dir_py_file` contract (every `scripts/*.py` must appear in both installers) does not flag the maintainer-only utility.

### 5.2 All five AI-instruction templates updated in lockstep

The five `templates/ai-instructions/base-*.md` files (claude, codex, cursor, gemini, opencode) plus `templates/ai-instructions/generic-instructions.md` and the `coding-instructions/` and `coding-snippets/` subdirectories were rewritten by pass 1 of the same script. Confirmed clean via `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB\|devai" templates/`. The five base templates received the same line-level replacements, so no lockstep divergence was introduced by the rename itself.

### 5.3 `using-devai-hub` skill directory renamed to `using-nexus-hub`

`git mv catalog/skills/workflow/using-devai-hub catalog/skills/workflow/using-nexus-hub`. The frontmatter `name`, `summary_l0`, and `overview_l1` fields were already updated by the Phase 5.1 textual sweep. The `description` field was rewritten to follow the AGENTS.md trigger-phrase guidance: it now lists concrete invocation phrases ("how do I find a skill?", "what can you do here?", "onboarding a new agent platform") and ends with an explicit `SKIP:` clause. The `data/SKILL_INDEX.md` and `data/skills.json` entries already point at the new path (those edits landed in Phase 2 sub-task 2.2 ahead of the on-disk move), so the cross-file registry stayed consistent throughout.

### 5.4 `.cursor/rules/devai-hub.mdc` renamed to `nexus-hub.mdc`

`git mv .cursor/rules/devai-hub.mdc .cursor/rules/nexus-hub.mdc`. The file's body was already rewritten by pass 1; no inline `name`-of-self references remained that needed manual edits.

### 5.5 Stability gate -- all four checks green

| Gate | Command | Result |
|---|---|---|
| Brand variant grep | `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" catalog/ templates/ .cursor/` | Empty |
| Skill validator | `python scripts/validate_skills.py --bundles-only` | PASS, 0 errors, 4 WN-001 carry-over warnings |
| Hook tests | `python -m pytest catalog/hooks/tests -q` | 370 passed, 3 skipped |
| Bash syntax | `for f in catalog/hooks/*.sh; do bash -n "$f"; done` | No errors |

The single hit in `catalog/hooks/tests/test_installer_smoke.py` (a `DEV_ONLY_SCRIPTS` comment describing the `apply_rename.py` purpose) was rephrased from a literal "DevAI-Hub -> Nexus-Hub" string to the generic "legacy-name to Nexus-Hub variant table" wording so the grep gate stays strictly green.

## Deviations

1. **Two-pass rename helper instead of one.** The inventory's variants 7-14 (MCP server keys, snake-case package ids, `devai_mcp_benchmark`, `devai-backup`) were not in the initial variant list because the plan prose describes them as Phase 4 surface, but they survived in catalog SKILL.md prose (architecture cross-references and pre-commit backup-pattern examples). Resolved by extending `VARIANTS` and re-running the script. The script is idempotent so the second pass only touched files that still held an unrenamed token.
2. **Catalog builder reverted.** The plan's DF-001 follow-up step prescribes running `python infrastructure/tools/build_skills_catalog.py` after the Phase 5.1 sweep and diffing the output against the manually-edited `data/` files. Running the builder produced a 1149-insertion / 1156-deletion regression that reverted `# Nexus-Hub Skill Index` back to `# DevAI-Hub Skill Index`. Root cause: the builder source carries four hardcoded DevAI literals (lines 292, 300, 339, 340: two GitHub URLs, the H1 title, and the catalog `description` field). The regeneration was reverted with `git checkout -- data/SKILL_INDEX.md data/skills.json`. The builder rename is captured as BG-001 in `docs/archive/v2/v2.0/known-gaps.md` and deferred to Phase 7 where the rename surface broadens to `infrastructure/`.

## Test Results

- Hook test suite: **370 passed, 3 skipped** (matches the post-Phase-3-and-4 baseline; the 2 added during Phase 3 installer-migration smoke plus 2 added during Phase 4 MCP-rename guards bring the total above the 366 documented in the plan's pre-rename baseline).
- Skill validator: **PASS, 0 errors, 4 warnings** (the 4 WN-001 framework-specialist orphan-bundle warnings carried from v1.1.5).
- Build: not run (Phase 5 is a textual sweep; no Python build artifacts touched).
- Lint: bash syntax check across all `catalog/hooks/*.sh` returns no errors.

## Known Gaps Touched

See `docs/archive/v2/v2.0/known-gaps.md`. Phase 5 close state:

- **BG-001 (new, open)** -- catalog builder regression, deferred to Phase 7.
- **DF-001 (resolved)** -- Phase 5.1 sweep removed the precondition (DevAI strings in `catalog/`). The follow-up regeneration step is parked behind BG-001.
- **WN-001 (unchanged, open)** -- 4 framework-specialist orphan-bundle warnings, carry-over from v1.1.5.
- **WN-002 (unchanged, open)** -- Windows `make` / `shellcheck` environment workaround, carry-over from v1.3.0.

## Files Touched

- `catalog/` -- 66 unique files across hooks, commands, skills, rules, style-guides, agents, context, memory (pass 1 + pass 2 combined; see `docs/archive/v2/v2.0/rename-manifest.txt` for the partial pass 2 detail).
- `templates/ai-instructions/` -- 5 base templates + generic-instructions + coding-instructions/coding-snippets subdirectory contents.
- `.cursor/rules/` -- renamed `devai-hub.mdc` -> `nexus-hub.mdc`.
- `catalog/skills/workflow/using-devai-hub/` -> `catalog/skills/workflow/using-nexus-hub/` (git mv).
- `scripts/apply_rename.py` -- new maintainer-only helper.
- `catalog/hooks/tests/test_installer_smoke.py` -- added `apply_rename.py` to `DEV_ONLY_SCRIPTS`; rephrased the comment to keep the grep gate strict-clean.
- `docs/archive/v2/v2.0/rename-manifest.txt` -- per-file rename manifest.
- `docs/archive/v2/v2.0/known-gaps.md` -- BG-001 opened, DF-001 resolved.
- `docs/DEVLOG.md` -- Phase 5 entry prepended.

## Next Phase

Phase 6 -- README modernization. Copy `nexus_primary.png` and `nexus_monochrome.png` from the sibling Nexus repo into `assets/`. Rewrite `README.md` around the Nexus-Hub brand with the hero block, the "Renamed from DevAI-Hub at v2.0.0" callout, and the "How Nexus-Hub fits with Nexus" cross-link section that makes the relationship between the two projects obvious to anyone landing on either repo.
