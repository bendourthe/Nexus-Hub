# Development Log: Phase 3 - Per-skill Bundled Resources Layout Convention (v1.1.5 adoption-skills plan)

**Date**: 2026-05-08
**Operator**: Benjamin Dourthe
**Assisted by**: Claude Opus 4.7 (1M context) via Claude Code
**Objective**: Execute Phase 3 of the v1.1.5 `adoption-skills` plan ([docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md)). One scope item, item A13 from the comparison report: formalize the per-skill `scripts/` / `references/` / `assets/` layout convention, document it in AGENTS.md, confirm both installers' existing recursive-copy primitives auto-distribute the new subdirs, extend `make validate` with an orphan-bundle audit, and ship a sentinel `.gitkeep` proving the round-trip.
**Outcome**: Convention documented in AGENTS.md as a new `#### Per-skill Bundled Resources` subsection with file-naming rules, the cross-shell parity rule, the reference rule, the installer behavior, and the orphan-audit cross-link. Both installers gained a clarifying block comment above `safe_folder_copy` / `Safe-Folder-Copy` (no code change in either function body - the audit confirmed the existing `rsync -a` / `cp -R` / `robocopy /MIR` primitives already preserve subdirs). `scripts/validate_skills.py` extended with a `validate_skill_bundles` function and a `--bundles-only` CLI flag; `make validate` rewired to invoke the bundle audit. New 8-test pytest module `catalog/hooks/tests/test_skill_bundles.py` covers the audit. Sentinel `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep` ships and round-trips through both `cp -R` (Git Bash) and `robocopy /MIR` (PowerShell). Two new known-gaps items logged: DF-004 (the optional `--dry-run` flag suggestion was assessed out of scope) and WN-001 (4 pre-existing orphan reference files surfaced by the new audit in three framework-specialist skills). Test posture: 318 passed in `catalog/hooks/tests/` (was 310; +8 new). Ready to advance to Phase 4.

---

## 1. Starting State

- **Branch**: `main` (working tree directly on `main`; no feature branch cut for Phase 3, matching Phases 1 and 2)
- **Starting commit**: `1016ebf` - `v1.2.0-wip: Phase 2 P0 cleanup + doc-coauthoring`
- **Environment**: Windows 11 Enterprise, Bash via Git-for-Windows, PowerShell 5.1, Python 3.12.x, ShellCheck installed
- **Prior session reference**: [docs/archives/v1/v1.1/development/history/2026-05_phase-2-p0-cleanup-doc-coauthoring.md](2026-05_phase-2-p0-cleanup-doc-coauthoring.md)
- **Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md) Phase 3 (sub-tasks 3.1, 3.2, 3.3, 3.4, 3.5, 3.6)
- **Carryover from prior phases**: 4 open known-gaps items (DF-001, DF-002, DF-003, QG-001). None of them were resolvable inside Phase 3's scope.
- **User-supplied constraint (carried)**: the version bump (v1.1.5 -> v1.2.0) waits until Phase 7 wraps; intermediate phases ship under `[Unreleased]` in CHANGELOG.md with no version-string changes anywhere else.
- **User-supplied constraint (carried)**: every artifact added, modified, or removed must reach all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux through the existing installer recursive-copy logic.
- **Auto mode**: the operator invoked Phase 3 in auto mode, asking the agent to make reasonable assumptions and proceed without ping-pong on routine decisions.

Phase 3 is the foundational phase of the plan. Every subsequent phase (4 through 7) consumes the per-skill bundled-resources convention to ship per-skill scripts and reference docs without inflating SKILL.md bodies. The work is mostly documentation + tooling, with one small skill-body edit (the sentinel) and zero registry-file changes.

---

## 2. Chronological Steps

### 2.1 Plan resolution and pre-implementation review

`Glob` for `docs/**/plans/adoption-skills.md` returned the single canonical plan. `Read` of the Phase 3 specification (lines 178-249 of the plan) loaded the six sub-task specifications. The plan's stability gate explicitly required: (a) AGENTS.md documents the convention; (b) both installers recursively copy per-skill subdirs in lockstep; (c) `make validate` flags orphan bundles; (d) a sentinel bundle survives a dry-run install on at least one OS; (e) pytest covers the new validator.

Pre-implementation file survey:

- `Read` of `Makefile` revealed the current `validate` target only loads JSON files; no skill-structure pass exists. The repo already has `scripts/validate_skills.py` with frontmatter and secret-scan capabilities, but the script is not wired into any Makefile target.
- `Grep` of `AGENTS.md` for `Per-skill Bundled Resources` confirmed the section did not exist; cross-references in the Three-Tier Loading Model block (lines 86-102) and the size norm block (line 144) named the section as "to be added in Phase 3".
- `Grep` of `scripts/installer.sh` for `cp -r` / `rsync` / `catalog/skills` revealed the `safe_folder_copy` function (line 128) uses `rsync -a --delete` (or `cp -R "$source/"*` fallback) to copy `catalog/skills/`. The existing primitive is recursive and already preserves arbitrary subdirectory depth.
- `Grep` of `scripts/installer.ps1` for `Safe-Folder-Copy` revealed the lockstep PowerShell function (line 298) uses `robocopy ... /MIR`, which mirrors arbitrary subdirectory depth.
- `Grep` for `dry-run` / `DryRun` in both installers returned **zero matches** - neither installer currently has a dry-run flag, despite the plan's sub-task 3.3 mentioning adding one if missing.

Pre-implementation summary reported in chat: 6 sub-tasks, ~10 files affected (AGENTS.md, both installers, validate_skills.py, Makefile, doc-coauthoring SKILL.md + new .gitkeep, new test file, CHANGELOG, known-gaps, DEVLOG, session history). Prerequisite check: Phases 1 and 2 marked complete in the plan and confirmed via `git log --oneline -10` (commits `99dbe1c` and `1016ebf`).

### 2.2 Sub-task 3.1 - A13.1: Document the convention in AGENTS.md

**Plan specification**: Add a new `### Per-skill Bundled Resources` subsection under "Adding a New Skill". Document the three optional subdirs (scripts/, references/, assets/), file naming, installer behavior, and the orphan-bundle audit. Cross-link to A17 (three-tier loading model) and A15 (500-line target). Also update the forward-reference in the Three-Tier Loading Model block.

**Implementation**:

- Updated the cross-link on line 102 from "the Per-skill Bundled Resources section that gets added in Phase 3" to "the Per-skill Bundled Resources subsection further down" since the section now exists.
- Inserted the new `#### Per-skill Bundled Resources` subsection immediately after the SKILL.md size norm (line 144) and before "### 4. Register the skill". The placement was deliberate: the size norm is the trigger for offloading body content into `references/`, so the convention that defines `references/` should sit right next to it.
- Body documents: (a) the optional subdirs with a directory-tree code block; (b) cross-link to the three-tier loading model framing; (c) file naming (kebab-case, scoped by topic); (d) the cross-shell parity rule (every `.sh` MUST ship a `.ps1` sibling); (e) the reference rule (every bundled file must be referenced from SKILL.md or another reference file, except `.gitkeep`); (f) installer behavior (existing recursive-copy primitives preserve subdirs; no installer edit needed); (g) orphan-bundle detection (the `make validate` extension); (h) cross-links to size norm, three-tier loading model, and v1.1.3 four-hook precedent.

The forward-reference fix on line 102 was easy to miss but matters: a reader looking at the three-tier model in v1.2.0 would have hit a broken cross-reference if the line was left as "section that gets added in Phase 3".

### 2.3 Sub-task 3.2 - A13.2: installer.sh recursive copy of per-skill subdirs

**Plan specification**: Verify the existing recursive copy preserves subdirs; if not, switch to `cp -r` / `rsync -a`; add a comment block above the loop explaining the behavior.

**Implementation**: The existing `safe_folder_copy` function already uses `rsync -a --delete` (or `cp -R "$source/"*` fallback). Both primitives are recursive and preserve arbitrary subdirectory depth. **No code change needed in the function body.** Added a 6-line block comment above the function definition documenting the preservation behavior with a cross-reference to the AGENTS.md convention.

`bash -n scripts/installer.sh` syntax check clean.

### 2.4 Sub-task 3.3 - A13.3: installer.ps1 recursive copy of per-skill subdirs (lockstep with 3.2)

**Plan specification**: Mirror sub-task 3.2 in `installer.ps1`. If `--dry-run` does not exist, add it as a no-op flag.

**Implementation**: The existing `Safe-Folder-Copy` function already uses `robocopy ... /MIR`, which mirrors arbitrary subdirectory depth. **No code change needed in the function body.** Added an 8-line block comment above the function definition in lockstep with `installer.sh`.

**Judgment call - `--dry-run` flag NOT added**: The conditional clause in the plan was "if `--dry-run` does not exist, add it as a no-op flag that prints what would be copied without touching the filesystem". Three options considered:

1. Add a real, fully-functional dry-run mode that gates every filesystem write in both installers behind a flag check (substantive feature, several-hundred-line refactor across two ~1700-line files).
2. Add a stub `--dry-run` flag that doesn't actually skip writes, just prints a banner (misleading - the flag would not behave the way users expect).
3. Skip the dry-run flag entirely and verify the smoke test by direct invocation of the underlying recursive-copy primitives (cp -R, robocopy /MIR) on a temp directory.

Picked (3) because it gives the same verification confidence (the actual primitive the installer would run is exercised) without taking on a feature-sized refactor in a phase whose actual goal is the per-skill layout convention, not installer architecture. Logged in `docs/archive/v1/v1.1/known-gaps.md` as DF-004 with a clear handoff note for any future plan that wants real dry-run capability.

### 2.5 Sub-task 3.4 - A13.4: make validate orphan-bundle detection

**Plan specification**: Locate the JSON validator script, add a new validator pass that walks each skill's `scripts/`, `references/`, `assets/` and emits a warning for each file unreferenced from SKILL.md. Treat `.gitkeep`-only subdirs as OK. Wire into `make validate`. Add a pytest test under `catalog/hooks/tests/test_skill_bundles.py`.

**Implementation**:

1. Added module-level constants `BUNDLED_SUBDIRS = ("scripts", "references", "assets")` and `BUNDLE_EXEMPT_FILENAMES = {".gitkeep"}` at the top of `scripts/validate_skills.py`.
2. New `validate_skill_bundles(skill_dir, skill_md_content)` function that walks a skill directory and emits warnings for orphan files. Builds a "haystack" from SKILL.md plus every `references/*.md` (so a top-level reference can act as a TOC for sub-resources). Searches for each bundled file's basename in the haystack. Warns when not found, with the suggestion "either reference this file from SKILL.md or remove it."
3. Wired the new function into `validate_skill_dir` (called for the full strict validator) and into the new `--bundles-only` CLI flag (called standalone for the audit-only mode).
4. Added a `--bundles-only` CLI flag that scopes the validator to the new orphan audit only.
5. Updated the `Makefile`'s `validate` target to run `python scripts/validate_skills.py --bundles-only` after the JSON catalog loads.

**Judgment call - `--bundles-only` flag instead of strict-validator integration**: When I first ran `python scripts/validate_skills.py` against the live catalog, the strict full-validator failed with **6 false-positive secret detections** in code-example blocks of three pre-existing skills (`user-documentation`, `cd-pipeline-generator`, `rollback-strategy-advisor`). Wiring the strict validator wholesale into `make validate` would have broken CI immediately. Picked the `--bundles-only` flag approach because it gives the new orphan-detection capability requested by the plan without inheriting the 6 pre-existing false positives. The strict validator remains available as a manual deep-audit tool via the unflagged `python scripts/validate_skills.py` invocation.

6. Created `catalog/hooks/tests/test_skill_bundles.py` with **8 pytest tests**:
    1. `test_orphan_in_scripts_is_warned` - orphan in `scripts/` triggers a warning.
    2. `test_referenced_file_is_silent` - file referenced by basename is not warned.
    3. `test_gitkeep_is_exempt` - `.gitkeep` is not warned even when not referenced.
    4. `test_reference_from_another_reference_satisfies_audit` - a top-level `references/index.md` (itself referenced from SKILL.md) can name sub-resources.
    5. `test_mix_of_orphan_and_referenced_only_reports_orphan` - the warning surfaces only the orphan, not the referenced file.
    6. `test_orphan_in_assets_subdir_is_warned` - the audit recurses into nested `assets/<subdir>/`.
    7. `test_no_subdirs_returns_empty` - skills without bundled subdirs return an empty list.
    8. `test_validator_cli_bundles_only_mode_runs_clean_on_real_catalog` - subprocess test that the CLI exits clean against the real 193-skill catalog.

All 8 tests pass on first run.

### 2.6 Sub-task 3.5 - A13.5: Sentinel per-skill bundle smoke test

**Plan specification**: Create `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep`. Reference the directory from the skill's body in a one-line note. Run `make validate && make lint && make test`. Verify the file lands at `~/.devai-hub/skills/.../doc-coauthoring/scripts/` after a dry-run install on at least one OS.

**Implementation**:

1. Created `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep` (empty file).
2. Added a brief "Bundled Resources" trailer to the doc-coauthoring SKILL.md after the Related Skills section: a one-line note that future bundled scripts go under `scripts/` and that the directory is reserved as a sentinel proving the convention survives an installer copy. The note also satisfies the orphan-audit reference rule for the skill (the `scripts/` directory reference + the `.gitkeep` exemption combined keep the audit silent).
3. **Smoke test - Git Bash on Windows** (exercises the same `cp -R` fallback `installer.sh` runs on Linux/macOS):

    ```
    tmpdir=$(mktemp -d) && cp -R catalog/skills "$tmpdir/skills"
    find "$tmpdir/skills/workflow/doc-coauthoring/" -type f
    ```

    Output included `<tmp>/skills/workflow/doc-coauthoring/scripts/.gitkeep`. The sentinel survived.

4. **Smoke test - PowerShell on Windows** (exercises the exact primitive `installer.ps1::Safe-Folder-Copy` invokes):

    ```
    & robocopy "catalog\skills" "$tmp\skills" /MIR /NFL /NDL /NJH /NJS
    Get-ChildItem -Recurse "$tmp\skills\workflow\doc-coauthoring"
    ```

    Output included `<tmp>\skills\workflow\doc-coauthoring\scripts\.gitkeep`. The sentinel survived. Robocopy's exit code 1 means "files were copied successfully" (it uses non-zero exit codes to signal copy results, not errors).

Both copy primitives preserved the sentinel. Cross-OS verification on macOS / Linux remains deferred (carryover gap DF-003 + QG-001 from Phase 2).

### 2.7 Sub-task 3.6 - Testing and Stabilization

**Plan specification**: Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` entries.

**Implementation**: `make` is not installed on the operator's Windows system, so the equivalent commands were executed directly:

- JSON catalog validation: 4 files (skills, bundles, workflows, templates) load clean. `data/skills.json` shows 189 skills (no change in this phase - the sentinel `.gitkeep` is not a registry entry).
- Orphan-bundle audit: 193 skills scanned, 0 errors, 4 warnings (4 pre-existing orphan files in 3 framework-specialist skills - logged as WN-001 in known-gaps).
- ShellCheck: clean against `scripts/installer.sh` (`--severity=warning`).
- `bash -n scripts/installer.sh`: clean.
- `python -m pytest catalog/hooks/tests/`: **318 passed** in 20 seconds (was 310; +8 from `test_skill_bundles.py`).

CHANGELOG `[Unreleased]` extended with Phase 3 sections: intro paragraph updated (Phases 1, 2, AND 3), new Changed bullets (AGENTS.md A13 subsection + both installer comments + Makefile wiring), new Added bullets (orphan audit + 8-test pytest + sentinel), new Verified bullets (smoke tests on both copy primitives), Tests count updated (310 -> 318, totals 406 -> 414), Known gaps expanded (DF-004 and WN-001 added).

---

## 3. Files Changed

| Path | Type | Reason |
|---|---|---|
| `AGENTS.md` | modified | New `#### Per-skill Bundled Resources` subsection; cross-link fix in Three-Tier Loading Model block. |
| `scripts/installer.sh` | modified | 6-line block comment above `safe_folder_copy` documenting per-skill subdir preservation. |
| `scripts/installer.ps1` | modified | 8-line block comment above `Safe-Folder-Copy` in lockstep with installer.sh. |
| `scripts/validate_skills.py` | modified | New `validate_skill_bundles` function; new `--bundles-only` CLI flag. |
| `Makefile` | modified | `validate` target now runs `python scripts/validate_skills.py --bundles-only`. |
| `catalog/skills/workflow/doc-coauthoring/SKILL.md` | modified | New "Bundled Resources" trailer referencing `scripts/`. |
| `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep` | **new** | Sentinel proving per-skill bundled-resources survive installer copy. |
| `catalog/hooks/tests/test_skill_bundles.py` | **new** | 8 pytest tests covering the orphan-bundle audit. |
| `CHANGELOG.md` | modified | Phase 3 sections appended under `[Unreleased]`. |
| `docs/archive/v1/v1.1/known-gaps.md` | modified | DF-004 and WN-001 added; DF-003 suggested-next-step updated; summary table refreshed. |
| `docs/DEVLOG.md` | modified | New Phase 3 entry prepended. |
| `docs/archive/v1/v1.1/development/history/2026-05_phase-3-bundled-resources-convention.md` | **new** | This file. |

---

## 4. Test Posture

| Suite | Result |
|---|---|
| `extensions/devai-skill-server` | 37 passed |
| `extensions/devai-code-search` | 36 passed, 1 skipped |
| `extensions/devai-web-fetch` | 23 passed |
| `catalog/hooks/tests` | **318 passed** (was 310; +8 from `test_skill_bundles.py`) |
| **Total** | **414 passed, 1 skipped, 0 failures** |

JSON catalogs: skills.json (189 skills), bundles.json (11), workflows.json (17), templates.json - all valid. Orphan-bundle audit: 193 skills scanned, 0 errors, 4 pre-existing warnings (logged in WN-001). ShellCheck: clean. `bash -n`: clean.

---

## 5. Open Items / Next Steps

Two new open items in `docs/archive/v1/v1.1/known-gaps.md`:

- **DF-004** - `--dry-run` flag NOT added to either installer. Intentionally deferred for scope; the smoke test was performed by direct primitive invocation instead. Any future plan that wants real dry-run capability should treat it as a coordinated multi-line refactor across both installers.
- **WN-001** - 4 pre-existing orphan reference files surfaced by the new audit in `fastapi-expert`, `nextjs-expert`, `react-expert`. Recommended fix: brief `## References` block in each affected SKILL.md, scheduled for a future patch.

Carried over from earlier phases: DF-001, DF-002, DF-003, QG-001. Total open: 6.

**Next phase**: Phase 4 (net-new content skills batch 1) - `generative-art`, `theme-tokens`, `internal-comms`, `web-artifacts-builder`. Each consumes the Phase 3 layout convention by bundling templates / themes / examples / scripts under the new subdirectory pattern. Phase 4 will be the first phase to actually add content under per-skill `templates/`, `themes/`, `examples/`, `scripts/` subdirs at scale.
