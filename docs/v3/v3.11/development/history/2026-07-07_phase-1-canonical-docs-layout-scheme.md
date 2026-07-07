# Session History - v3.11.0 Phase 1: Canonical docs-layout scheme

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 1 of 8 - Canonical docs-layout scheme
**Status**: Complete (stability gate PASS)

## Goal

Standardize the per-version docs layout on `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` (active) and `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/` (archive), each with `plans/` and `comparisons/` subdirectories and patch releases sharing their minor directory, and make every skill, script, and reference that encodes a docs path speak this scheme.

## What changed

### 1.1 - Canonical scheme + version-directory resolution (`docs-layout-refactor/SKILL.md`)

- Rewrote the scheme throughout: frontmatter `description` / `overview_l1`, "What This Skill Does" step 5, the Step 4 disposition table, the entire Step 5 target-layout proposal, the Step 6 target-tree preview, the Step 7 gate text, and the Step 8 `--canonicalize-layout` / `--auto-archive-older-versions` targets - all moved from `docs/versions/v<MAJOR>/v<MAJOR>.<MINOR>.<PATCH>/` to `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`.
- Reconstituted the former "Step 0b.5" path-resolution algorithm (which had lived only in git history at `ad8409b~1:catalog/commands/generate-plan.md`) as a live, named `## Version-directory resolution` section, updated to the new scheme, with the four-step resolution algorithm, the per-file release-prefix naming convention (`v<MAJOR>.<MINOR>.<PATCH>-<slug>.md`), and the safety rules.
- Bumped the skill footer to v1.2.0 (July 2026).

### 1.2 - Two-level nesting in `audit-docs.py` + tests + `references/archive-layout.md`

- Added `MAJOR_BUCKET_RE` (`^v\d+$`) and `MINOR_DIR_RE` (`^v\d+\.\d+$`) and a new `_resolve_version_topic(abs_path, docs_root)` helper that recognizes the two-level scheme (`docs/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/...`, and the `docs/archive/...` equivalent one level down) while preserving backward compatibility with the legacy flat layout. `_version_dir` / `_topic_dir` now delegate to it; `cmd_inventory` calls the resolver once.
- Added `tests/skills/test_audit_docs_version_topic.py` (13 cases): two-level, archive-equivalent, legacy-flat, and non-version paths, plus wrapper delegation. All pass.
- Confirmed `audit-docs.ps1` only forwards to the Python script (no parsing logic) - no change needed.
- Rewrote `references/archive-layout.md` end-to-end to the minor-grouped scheme (layout convention, example tree, README index example, collision rule with release prefixes).

### 1.3 - Known-gaps shared-minor-dir collision (`known-gaps-tracker/SKILL.md`)

- Made the file multi-release aware: one `known-gaps.md` per minor directory with a single file-level header and one `## v<MAJOR>.<MINOR>.<PATCH>` subsection per patch release (Summary / Open Items / Resolved demoted under each patch section), so `v3.10.1` and `v3.10.2` no longer clobber a shared file.
- Updated Append and Sweep to locate/create the correct patch subsection; IDs are now monotonic per category across the minor file.
- Fixed the Ingest discovery glob to match both the two-level `docs/v*/v*/known-gaps.md` and the legacy `docs/v*/known-gaps.md`.
- Updated all path strings and the Verification checklist.

### 1.4 - Scheme sweep across dependent artifacts

- `implementation-plan/SKILL.md`: replaced every explicit `docs/versions/...` statement and dangling "Step 0b.5" pointer with the new scheme and a reference to the docs-layout-refactor Version-directory resolution; added the release-prefix (`v<MAJOR>.<MINOR>.<PATCH>-<slug>.md`) to the generated plan filename in Phase C, Step 4, and Verification.
- `catalog/style-guides/markdown.md`: updated the plans / comparison-reports / session-histories example paths (comparison reports now under `comparisons/`).
- `catalog/commands/compare.md`: comparison-report output path moved to `docs/v<MAJOR>/v<MAJOR>.<MINOR>/comparisons/comparison-<name>.md`.
- `catalog/skills/code-cleanup/project-refactor/SKILL.md`: active-version detection now reads the `docs/v*/` tree instead of `docs/versions/`.
- Repo-wide grep confirmed no remaining canonical statements of the old scheme; the only `docs/versions/` mentions left are intentional "recognize the legacy layout" clauses.

`docs/<version>/` placeholders that are version-agnostic (they resolve through the algorithm) were intentionally left in place; only stale *statements of the scheme* were changed, per the every-changed-line-traces-to-scope rule.

## Verification

- `tests/skills/test_audit_docs_version_topic.py`: 13 passed.
- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors) - `archive-layout.md`, `audit-docs.py`, `audit-docs.ps1` all still referenced from SKILL.md.
- `python scripts/validate_unicode_safety.py`: 0 errors (warnings are pre-existing curly quotes in a legacy `typescript.md` template).
- `python scripts/validate_no_personal_paths.py`: clean.
- `python scripts/check_version_sync.py`: clean at 3.10.3 (project version not bumped - that is Phase 8).
- `python scripts/check_base_template_parity.py`: all five base templates present and in parity (no base-*.md touched).
- `validate_workflow_security.py`, `scan_supply_chain_iocs.py`, `validate_solution_frontmatter.py`: clean.
- JSON catalogs (`skills.json`, `bundles.json`, `workflows.json`, `templates.json`) load.

## Notes and environment caveats

- `make` is not installed on this Windows host; the `make validate` steps were run individually. Every runnable step passed.
- The context-compressor accuracy-regression gate (`cd extensions/nexus-context-compressor && python -m evals --check`, the final `make validate` step) was not run: it lives in an extension with its own environment and is untouched by Phase 1. Re-run it in an environment with the extension deps before release.

## Next steps

- Phase 2: Project-bootstrap governance (`setup-project` + `analyze-codebase` skills, git/version/branch/setup-needed detection, Project-health block in `/describe` and `/review`).
- The actual on-disk migration of `docs/v3.x.y/` and `docs/archive/` to the new scheme is Phase 8 (dogfood), not Phase 1 - Phase 1 only made the documented contract consistent.
