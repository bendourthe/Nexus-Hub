# Session History - v3.11.0 Phase 4: Refactor-engine upgrade (project-refactor)

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 4 of 8 - Refactor-engine upgrade (project-refactor)
**Status**: Complete (stability gate PASS)

## Goal

`project-refactor` can detect and propose fixes for empty directories, redundant/duplicate files and dirs, non-version orphans, and overcomplicated structure - the cleanliness heuristics the Phase 3 mandatory final phase (N.1) and the Phase 8 self-application depend on.

## What changed

All edits are in `catalog/skills/code-cleanup/project-refactor/SKILL.md`.

### 4.1 - Four new cleanliness detectors

- **Pipeline (step 3)**: extended Inventory and Classification to classify files AND directories as Stay / Move / Archive / Prune / Consolidate / Ambiguous, adding the four cleanliness detectors and pointing at the new sections.
- **New section "Detecting Empty and Redundant Artifacts"** with three subsections: (a) empty directories - prune candidate, `.gitkeep`/`.keep` never pruned, becomes-empty dirs need a second confirmation, propose-only; (b) redundant/duplicate files - byte-identical (sha256) duplicates propose keeping the canonical copy, name/purpose overlaps flag for manual review, duplicates with different callers are surfaced not collapsed; (c) non-version orphans - invert the reference-detection machinery to find zero-inbound-reference files, default them to Ambiguous (never auto-archive), with an allowlist for load-bearing standalone files (LICENSE, README, CHANGELOG, SECURITY, ignore files, entry points, Stay-rule files).
- **New section "Structure-Complexity Heuristics"**: single-child directory chains, deep nesting (>4 levels outside docs/ and vendored trees), and over-fragmentation, each proposing consolidation/flattening (propose-only) with reference-repair impact; under-fragmentation explicitly out of scope.
- **Verification**: added four binary checks (empty-dir prune respecting .gitkeep; duplicate/redundant flagged with callers surfaced; orphans flagged Ambiguous with allowlist honored; structure-complexity proposals with paths + repair impact).
- **Frontmatter**: widened `description` (added the new trigger phrases), `summary_l0`, and `overview_l1` to reflect the expanded scope. Bumped the footer to v2.1.0 (July 2026).
- Existing behavior (rule loading, prior-version archival, impact analysis, safe-move protocol, reference repair) is unchanged; the new detectors are additive and default to propose-only.

## Verification

- Built the fixture tree the plan specifies (empty dir, a `.gitkeep`-held dir, two byte-identical files in different locations, an unreferenced orphan, and an `a/b/c/d/only.md` single-child chain) and ran the actual detection logic each new heuristic describes:
    - Empty-dir: `empty_dir` flagged; `keeper_dir` (holds `.gitkeep`) correctly excluded.
    - Duplicate: `loc_a/dup1.txt` and `loc_b/dup2.txt` sha256-identical - detected.
    - Orphan: `orphan.md` -> 0 inbound refs (flagged); the referenced `dup1.txt` -> 1 inbound ref (not an orphan).
    - Structure-complexity: `a -> b -> c -> d` single-child chain detected and reported collapsible.
- `validate_skills.py --bundles-only`: PASS (0 errors). `--quality`: PASS (0 errors; no warning references project-refactor). `validate_unicode_safety.py`: 0 errors. `check_version_sync.py`: clean at 3.10.3. `skills.json` loads (262). Code-fence balance in the skill: 30 (even) - the new sections added no code fences.

## Notes and environment caveats

- **Deliberate scope decision**: the widened `summary_l0`/`description`/`overview_l1` were changed in the SKILL.md (the source the MCP reads live) but NOT in the generated `data/skills.json` / `data/SKILL_INDEX.md` copies. Those already drift from source and resync on `make build-catalog`, which Phase 8's sub-task 8.5 runs; hand-editing their escaped entries for a one-line summary change is outside Phase 4's scope and higher-risk than the drift it would fix. The skill count is unchanged (no new skill).
- `project-refactor` is skill instructions, not executable code, so "run project-refactor on the fixture" is an agent-execution simulation; the meaningful verification is that each detector's underlying logic fires correctly on the fixture (confirmed above) and the skill body now documents them with binary Verification.
- `make` is unavailable on this Windows host; gates were run individually. The extension-local compression eval was not run (untouched by Phase 4).

## Next steps

- Phase 5: Implement + update integration - reconstitute the `implement-phase` skill from git history, wire the mandatory final-phase gate into `/implement`, and integrate docs-structure + known-gaps + refactor + CI/CD into `/update`.
