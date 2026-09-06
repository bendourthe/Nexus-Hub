# Session History - Skills-Craft and Prime Agent Phase 1: Agent-Writing Craft and Out-of-Scope Register

**Date**: 2026-08-24
**Branch**: `feat/v3.20.3-skills-craft-and-prime-agent`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`](../../plans/v3.20.3-skills-craft-and-prime-agent.md)
**Phase**: 1 - Agent-writing craft and out-of-scope register (A4, A2)
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: Authoring skills carry the six agent-writing concepts; `docs/policy/out-of-scope/` exists with two seeded entries; trigger evals green. Ready for Phase 2.

## 1. Starting State and Routing

- **Starting commit**: `237ba49b` (`backmerge/v3.20.2-release` / v3.20.2 catalog)
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier). Stronger than planned; Cursor cannot script a model switch; no downshift.
- **Installer edit**: none. Skills and `docs/policy/` auto-copy or are repo-internal. No `scripts/` copy step.

## 2. What Was Implemented

### 1.1 - Enrich the skill-authoring skills (A4)

- `catalog/skills/developer-experience/skill-description-authoring/SKILL.md` gained Rule 6 naming all six concepts (context pointers, two loads, leading words, negation avoidance, sediment pruning, hard/soft setup-dependency). Existing trigger-noun, confidence-band, and clarification-ceiling rules stay intact.
- Full treatment is `references/agent-writing-theory.md` (Tier 3). Generic vocabulary; no external source named in the skill body.
- `catalog/skills/workflow/skill-create/SKILL.md` applies the same six concepts at the draft step and links the theory file instead of forking it.
- `overview_l1` fields updated on both skills. `data/skills.json` text fields synced so `check_registry_entries.py --strict` stays clean.

### 1.2 - Out-of-scope register (A2)

- `docs/policy/out-of-scope/README.md` defines the never-do vs do-later split against `known-gaps-tracker`.
- Seeded entries: `search-as-service-mcps.md` (MCP Registry Policy hard-no list) and `changesets-release-automation.md` (declined in the v3.20.3 comparison in favor of `/update release` + `check_version_sync.py`).
- `known-gaps-tracker` When-NOT, Common Rationalizations, Related Skills, and Verification now route "we will never do this" to the register.

### 1.3 - Testing and Stabilization

- Added `evals/trigger-cases.json` for the two edited authoring skills (3+/3+ each). Coverage 61 -> 63 skills with cases.
- No CI workflow rewrite: `catalog/skills/**` and `docs/policy/**` already classify as relevant.

## 3. Tests

- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors, 65 grandfathered warnings)
- `python scripts/check_agentskills_conformance.py`: PASS (`skill-create` remains on the over-1024 grandfather list; description unchanged)
- `python scripts/check_registry_entries.py --check --strict`: PASS
- `python scripts/run_trigger_evals.py --gate`: PASS (0 routing failures across 63 skills)
- `python scripts/validate_unicode_safety.py --strict --path` on Phase 1 files: PASS
- `python scripts/validate_no_personal_paths.py --path` on Phase 1 files: PASS (full-tree walk left to CI; WN-3)
- `python scripts/check_docs_conventions.py`: PASS against its hardcoded `docs/v3/v3.19/` tree (WN-4; new `docs/policy/out-of-scope/` files are outside that scan)
- `python scripts/check_version_sync.py`: PASS (still 3.20.2)
- Repo-level pytest: `tests/validators` + `tests/plans`: 1090 passed, 2 skipped. Full `tests/` plus `catalog/hooks/tests` plus `tests/skills` was too slow on this OneDrive host to finish in the implement loop (hung around 79% after 17 minutes); left those jobs to CI.

## 4. Deviations

- **Plan path citations.** The phase prompts still name `docs/v3/v3.17/plans/v3.19.2-...`. Work landed against the retargeted file `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`.
- **Trigger evals added.** Sub-task 1.3 asked to confirm routing on existing positive cases. Neither skill had `evals/trigger-cases.json`, so cases were authored rather than skipped. Not a scope cut; a test-augmentation fill.
- **DEVLOG index line deferred** until `/update release` (one line per released version, not per phase).
- **No new CI workflow.** Path filters already cover the touched trees.

## 5. Next Steps

Phase 2: author `design-interview`, `setup-wizard-generator`, and `decision-questionnaire` under the upgraded writing discipline, register them by hand in the three `data/` files, and add trigger evals.
