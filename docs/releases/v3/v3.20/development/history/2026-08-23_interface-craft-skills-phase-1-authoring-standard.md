# Session History - Interface-Craft Skills Phase 1: Authoring-Standard Foundation

**Date**: 2026-08-23
**Branch**: `feat/v3.20.2-interface-craft-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.2-interface-craft-skills.md`](../../plans/v3.20.2-interface-craft-skills.md)
**Phase**: 1 - Authoring-standard foundation (A7, A10, A9, A11)
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: Rule-ownership, missing-delegate honesty, Considered-but-Rejected, and mode-based finding cap are in `AGENTS.md`; `multi-agent-code-review` is the canonical review-output contract. No cluster skill was written. Ready for Phase 2.

## 1. Starting State and Routing

- **Starting commit**: `0d4ec0dd` (`backmerge/v3.20.1-release` / `origin/main`, v3.20.1 catalog)
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier). Stronger than planned; Cursor cannot script a model switch; no downshift.
- **Installer edit**: none. Authoring rules live in `AGENTS.md` and one existing skill body. The five lockstep `base-*.md` templates were not edited (plan forbids it).

## 2. What Was Implemented

### 1.1 - Rule-ownership convention (A7)

`AGENTS.md` gained a "Rule ownership for overlapping skills" subsection next to the size-norm rule. A cluster must name exactly one owning skill per concern; non-owners describe only the handoff. The table lives in the coordinator, or in `AGENTS.md` if there is none. Tie-break: one skill decides WHEN a constraint applies and how severe a violation is; another owns measuring and remediating it.

### 1.2 - Missing-delegate honesty (A10)

Immediately after 1.1. An unavailable delegate is named, that portion is marked not covered, and work continues. Reconstructing rules from memory, substituting a neighbour, or claiming unearned coverage is forbidden. The gap must appear in the output. Cross-references `[[verification-before-completion]]`.

### 1.3 - Review-output contract (A9, A11)

- `AGENTS.md` carries a short inherited-conventions note.
- `catalog/skills/code-review/multi-agent-code-review/SKILL.md` Stage 7 now requires a Considered-but-Rejected table of real inspected candidates and binds quick (P0/P1, cap 5) vs full (all gate survivors, cap 20) depth modes. Confidence-gating is unchanged. Verification checklist and Common Rationalizations were extended.

### 1.4 - Testing and Stabilization

Existing CI already covers `AGENTS.md` and `catalog/skills/**` (unfiltered workflow trigger, job-level `changes` classifier, concurrency cancel-in-progress, pip cache). No workflow rewrite. `validate_skills.py --bundles-only` still reports 315 skills; frontmatter was not changed so `data/skills.json` was not synced.

## 3. Tests

- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors, 66 grandfathered warnings)
- `python scripts/check_agentskills_conformance.py`: PASS (315 skills)
- `python scripts/run_trigger_evals.py --gate`: PASS
- `python scripts/validate_doc_budgets.py`: PASS after condensing the three new `AGENTS.md` subsections (first draft exceeded the 8150-word ceiling by 154 words)
- `python scripts/check_registry_entries.py --check --strict`: PASS
- `python scripts/check_version_sync.py`: PASS (still 3.20.1)
- `python scripts/validate_unicode_safety.py --strict --path` on the three touched files: PASS
- `python -m pytest catalog/hooks/tests/test_hook_sibling_parity.py tests/validators/test_agentskills_conformance.py tests/validators/test_validate_doc_budgets.py tests/validators/test_validate_skills.py`: 361 passed
- Full-tree `validate_no_personal_paths.py` did not finish locally (WN-3); scoped `--path` scan of Phase 1 files was clean

## 4. Deviations

- **Word-budget condensation.** Plan asked for ~25 and ~20 line subsections. The first draft blew the `AGENTS.md` 8150-word ceiling. The shipped text is denser paragraphs that still state every required rule, tie-break, failure mode, and cross-link.
- **No new CI workflow.** Plan asked to create or update CI path-filtered to `AGENTS.md` and `catalog/skills/**`. Those paths already trigger the existing `validate` job; adding a second workflow would create a new required-check context. Left as-is.
- **DEVLOG index line deferred** until `/update release` (one line per released version, not per phase).

## 5. Next Steps

Phase 2: author `accessibility-engineering` with a `references/` bundle, register it by hand in the three `data/` files, and add the skill-native matrix row.
