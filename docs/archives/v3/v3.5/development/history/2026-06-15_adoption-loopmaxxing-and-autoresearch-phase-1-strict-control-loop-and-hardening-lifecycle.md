# Session History - v3.5.0 adoption-loopmaxxing-and-autoresearch Phase 1: strict-control-loop doctrine + hardening lifecycle

**Date**: 2026-06-15
**Plan**: [`../../plans/adoption-loopmaxxing-and-autoresearch.md`](../../plans/adoption-loopmaxxing-and-autoresearch.md) Phase 1 (G1 + G2, both skill-native)
**Branch**: `feat/loop-engineering-enrichment`
**Outcome**: Implementation complete; quality gate GO. Phase 1 of 3, so Phase 2 (metric-optimization archetype + per-iteration budget + oracle carve-out) follows. No release work this phase.

## Goal

Teach, in the `loop-engineering` skill, the article's central "pragmatic path" thesis (deterministic code drives the loop; the LLM is invoked only for the dynamic decisions code cannot make) and the maturity progression behind the existing `maturity` flag. Pure local catalog enrichment of two existing files; no new skill, command, outbound call, dependency, or credential.

## What shipped

- **`catalog/skills/workflow/loop-engineering/SKILL.md`** (sub-tasks 1.1 + 1.2A): a new `## Strict Control Loops` section placed immediately after `## Scheduled-Triage Recipe` and before `## Common Rationalizations`. The section teaches the deterministic-shell model in an intro paragraph plus three bullets: (1) the operator owns the shell (writes the desired state and the check mechanism; code handles iteration, execution, and every tool/API call); (2) the LLM handles only the genuinely-dynamic decision, so a hallucinating model's blast radius is bounded by the surrounding hard-coded checks; (3) wrapping repetitive or risky steps in code-level checks is how you limit the blast radius. It cross-links `[[agent-orchestration-primitives]]` (cheapest-primitive discipline) and `[[ai-billing-safeguards]]` (cost bounding), and is explicitly framed as complementary to the host `/loop` + `/goal` driver model, not a replacement. A `### Progressive hardening` subsection records the lifecycle: start minimal with a human in the verification seat, run several times, then replace the LLM prompt for each consistently-correct step with deterministic code, so an `experimental` loop becomes `hardened`.
- **`catalog/skills/workflow/loop-engineering/references/loop-schema.md`** (sub-task 1.2B): expanded the `maturity` field description row to encode the same progression: `experimental` = new or unproven, run with a human in the verification seat; `hardened` = repeatedly successful locally AND its consistently-correct steps have been moved out of the LLM prompt into deterministic code. The field set and the worked example are unchanged.

All added content is ASCII-only (hyphens, straight quotes), follows the Markdown style guide (blank line before/after every heading and list), and introduces no external repo/product attribution.

## Key decisions

- **Reused existing wikilink targets only.** The two cross-links in the new section (`[[agent-orchestration-primitives]]`, `[[ai-billing-safeguards]]`) already appeared elsewhere in the same SKILL.md and both resolve to real skills, so the edit adds zero new wikilink targets and carries zero new dangling-wikilink risk.
- **Strict-control-loop framed as complementary, not a replacement.** Per the plan constraint, the new section reinforces that the host command still drives the run (Step 1's `/loop` + `/goal` model); the doctrine only pushes the loop body toward deterministic code. This keeps the new section consistent with the existing Step 1-5 body rather than contradicting it.
- **Hardening lifecycle documented in two consistent places.** The SKILL.md `### Progressive hardening` paragraph and the `loop-schema.md` `maturity` row tell the same `experimental` -> `hardened` story, so an operator reading either file gets the same definition.
- **Deterministic-oracle carve-out deliberately deferred to Phase 2.** This phase leaves the maker/checker rule and the "Maker self-certifies exit" anti-pattern intact; Phase 2's sub-task 2.2 adds the deterministic-oracle nuance, so nothing in Phase 1 pre-empts or softens it.
- **No frontmatter change, so no `data/` registry edit.** The skill's `name` / `description` / `summary_l0` / `overview_l1` are untouched, so `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` need no edit (confirmed: JSON catalogs still load and skill count is unchanged).

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so gates were run via the documented direct equivalents:

- **Orphan-bundle audit** (`validate_skills.py --bundles-only`, the gate `make validate` actually runs): PASS, exit 0 (0 errors, 1 pre-existing WN-v33-2 warning about `demo-capture`'s `scripts/__pycache__/*.pyc` build artifact). The `loop-engineering` skill produced no bundle finding, confirming both reference files are still linked from SKILL.md (no new orphans).
- **ASCII-only** (`validate_unicode_safety.py`): zero findings for either edited file (filtered for `loop-engineering`). The validator's repo-wide warnings are all pre-existing (e.g. AGENTS.md em-dashes) and unrelated to this phase.
- **Dangling-wikilink resolution**: all 11 distinct `[[...]]` targets across the two edited files resolve to existing `catalog/skills/**/<name>/` directories; the 2 used in new content both resolve.
- **SKILL.md body size**: 131 lines, under the 500-line size norm.
- **JSON catalog integrity**: `data/skills.json`, `data/bundles.json`, `data/workflows.json`, `data/templates.json`, `data/marketplace.json` all load; no `data/` file changed.
- **Full `validate_skills.py`** exits 1 due to 155 pre-existing `description is > 250 chars` errors and 1236 `missing optional field` warnings spread across the catalog (e.g. `ai-billing-safeguards`, `claude-agent-sdk`). None reference `loop-engineering` or the edited files, and no frontmatter was touched, so this is a pre-existing catalog-wide condition (the full mode's 250-char ceiling conflicts with the project's pushy-description authoring rule, which is why `make validate` uses `--bundles-only` + `--quality` instead). No regression.

Diff scope: +13 / -1 across exactly the two intended files; no scope creep.

## Files changed

- `catalog/skills/workflow/loop-engineering/SKILL.md`
- `catalog/skills/workflow/loop-engineering/references/loop-schema.md`
- `docs/v3/v3.5/plans/adoption-loopmaxxing-and-autoresearch.md` (Phase 1 exit checklist)
- `docs/archive/v3/v3.5/development/history/2026-06-15_adoption-loopmaxxing-and-autoresearch-phase-1-strict-control-loop-and-hardening-lifecycle.md` (this file)

## Next

Phase 2: add the `optimize-metric-keep-best` archetype to `references/loop-library.md` (G5), add the optional `per_iteration_budget` field to `references/loop-schema.md` (R2), and qualify the maker-self-certifies anti-pattern with the deterministic-oracle carve-out (R3). The hardening-lifecycle vocabulary established this phase is a prerequisite the new archetype's `maturity` note leans on.
