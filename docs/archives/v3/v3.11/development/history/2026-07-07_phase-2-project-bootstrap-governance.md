# Session History - v3.11.0 Phase 2: Project-bootstrap governance

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 2 of 8 - Project-bootstrap governance (setup / describe / review)
**Status**: Complete (stability gate PASS)

## Goal

`/setup` detects and bootstraps git, a `vX.Y.Z` version, a `develop`+main branch model, and the per-version docs tree; `/describe` and `/review` detect and report project health (git? version? branches? setup needed?) and offer a `/setup` handoff.

## What changed

### 2.1 - New skill: `setup-project` (project-setup)

Created `catalog/skills/project-setup/setup-project/SKILL.md` - the generic, cross-language delegate behind `/setup project` that `setup.md` already named. Every step is detection-first (idempotent, safe on an inherited repo): (a) git init + initial commit if not a repo; (b) version - detect from tag/CHANGELOG/manifest, else set `v0.1.0` on the canonical surface; (c) branch model - create a `develop` integration branch when only a default branch exists, delegating discipline to `[[git-branching-workflow]]`; (d) per-version docs tree `docs/v<MAJOR>/v<MAJOR>.<MINOR>/{plans,comparisons}/` per the Phase 1 scheme; (e) real README / CHANGELOG / DEVLOG. Includes When-to-Use (+ When-NOT), Instructions, Common Rationalizations, Verification (binary), and Related Skills. ~96 lines.

### 2.2 - `git-branching-workflow` develop-bootstrap + fuller prefix set

Added a new "Step 3: Bootstrap the integration branch when missing" (create `develop` from the default branch for an undeclared / greenfield / inherited project, with user confirmation; never for a declared trunk-based project), renumbering the later steps to 4-7. Extended the work-branch prefix set to `feat/` `fix/` `refactor/` `ci/` `docs/` `chore/` `test/`, all integrating through `develop`. Rewrote the "assume develop+main" rationalization so it permits the `/setup` bootstrap path while still forbidding auto-creating `develop` in a declared trunk-based repo, and added a Verification item that the integration branch exists after bootstrap.

### 2.3 - New skill: `analyze-codebase` (developer-experience)

Created `catalog/skills/developer-experience/analyze-codebase/SKILL.md` - the delegate behind `/describe`, writing `docs/<version>/analysis.md`. Twelve-section report (project type, layout, modules, dependencies, architecture with Mermaid, entry points, config, testing, onboarding, open questions) with a read-only **Project health** block as section 2: a binary git / version / branch-model / baseline-docs / docs-tree checklist that ends with an explicit `/setup project` handoff offer when any surface is MISSING. Read-only by default (reports and offers, never mutates); supports the focused scopes (structure/deps/architecture/onboarding). ~155 lines.

### 2.4 - Project-health block in `/review`

`run-deep-review` and `review-codebase` turned out to be prose-only delegates (no SKILL.md files, not in the index - the same missing-delegate situation the plan Overview flagged for setup-project/analyze-codebase/implement-phase). Per the plan's instruction to keep this sub-task scoped to the health block only (no phase schedules reconstituting those two), the read-only Project-health block was wired into `catalog/commands/review.md` for the `full` and `structure` scopes, reusing the exact `analyze-codebase` wording and preserving `/review`'s read-only contract, with a note that the delegates are prose-only until reconstituted.

### 2.5 - Registration and command updates

Registered both new skills in `data/SKILL_INDEX.md` (2 rows + total 260 -> 262), `data/skills.json` (2 entries, hand-edited to a minimal diff after the full generator was found to reorder the entire catalog), and `data/marketplace.json` (developer-experience 30 -> 31, project-setup 4 -> 5). Updated `setup.md`'s delegation note to state the detection-first bootstrap, and `describe.md`'s twelve-section-report claim to name the Project-health block.

## Verification

- Registry consistency: `skills.json` = 262 entries, `SKILL_INDEX.md` total = 262, marketplace `skill_count` sum = 262 (all match; both new skills present).
- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors) over 262 skills.
- `python scripts/validate_skills.py --quality`: PASS (0 errors); the two new skills raise no quality warnings.
- Frontmatter: `summary_l0` / `overview_l1` are quoted and YAML-parseable for both new skills (the MCP requirement). Fixed one accidental colon-space in the `analyze-codebase` description (`default:` -> `default -`) to match the catalog's colon-free description convention.
- `validate_unicode_safety.py`: 0 errors. `check_version_sync.py`: clean at 3.10.3. `check_base_template_parity.py`: all five base templates present (none touched). `validate_no_personal_paths.py`, `validate_workflow_security.py`, `scan_supply_chain_iocs.py`, `validate_solution_frontmatter.py`: clean.
- Phase 1 regression: `tests/skills/test_audit_docs_version_topic.py` still 13 passed.
- Dogfood: ran the `setup-project` procedure on a scratch directory - every Verification item passed (git repo + 1 commit, `v0.1.0` in CHANGELOG, `develop` branch, `docs/v0/v0.1/{plans,comparisons}`, and README/CHANGELOG/DEVLOG). The `analyze-codebase` and `/review` health blocks use the same detection commands (read-only), verified by construction.

## Notes and environment caveats

- `make` is not installed on this Windows host; the `make validate` steps were run individually and all runnable steps passed. The context-compressor accuracy-regression gate (extension-local, final `make validate` step) was not run - untouched by Phase 2.
- `validate_skills.py` *default* mode reports 160 "description > 250 chars" errors, but these are pre-existing across the catalog (long "pushy" descriptions are prescribed by AGENTS.md) and that mode is NOT part of the `make validate` gate (which runs `--bundles-only` and `--quality`). No action taken.
- `run-deep-review` / `review-codebase` remain prose-only; reconstituting them is out of scope for Phase 2 (no phase schedules it). The health block is documented at the command level in the meantime.

## Next steps

- Phase 3: Mandatory final refactor + known-gaps + CI/CD phase in planning (`implementation-plan` emits a required terminal refactor phase in every plan; per-phase CI/CD create/update/optimize language).
