# Session History - v3.6.0 adoption-spec-kit Phase 1: skill-native doctrine folds (N2a + N3b)

**Date**: 2026-06-16
**Plan**: [`../../plans/adoption-spec-kit.md`](../../plans/adoption-spec-kit.md) Phase 1 (N2a + N3b, both skill-native / Bucket A)
**Branch**: `feat/spec-kit-delta-adoption`
**Outcome**: Implementation complete; quality gate GO. Phase 1 of 5, so Phase 2 (the `base-*.md` parity-governance check) follows. No release work this phase.

## Goal

Fold two policy-clean vocabularies surfaced by the v3.5.0 Spec Kit re-comparison into existing Nexus-Hub skills, as prose only: N2a (workflow gate / persisted-resume / continue-on-error control patterns) into the orchestration skills, and N3b (template composition strategies: replace / prepend / append / wrap) into the preset/theme skills. Pure local catalog enrichment of four existing files; no new skill, command, file, outbound call, dependency, or credential. The load-bearing constraint (from comparison candidates N2a and N2b) is to frame all three workflow-control patterns as agent-instruction patterns over the harness's existing Dynamic Workflows or a `/loop` driver, NEVER as a new runtime to build - because N2b (a portable YAML workflow engine) was deliberately declined.

## What shipped

### N2a - gate / resume / continue-on-error vocabulary (sub-task 1.1)

- **`catalog/skills/workflow/loop-engineering/SKILL.md`**: a new `## Workflow-Control Patterns: Gate, Resume, Continue-on-Error` section placed after `### Progressive hardening` and before `## Common Rationalizations`. An intro paragraph frames all three as agent-instruction patterns (not a new runtime) and maps each onto the harness's Dynamic Workflows (`AskUserQuestion` between stages = gate; the workflow journal = resume; per-item `try/catch` = continue-on-error) or the external memory layer for a plain `/loop` run. Three bullets, each with one short example: (a) human gate checkpoint with an explicit `on_reject` policy (abort / skip / retry); (b) persisted resume-from-checkpoint via a per-step run file so an interrupted run re-enters at the failed step; (c) per-step continue-on-error that records the failure and continues, paired with the existing two-or-three-retries-then-handoff rule from the Scheduled-Triage Recipe. A closing line warns against building a YAML workflow engine to host them (the declined N2b trap). A matching Verification bullet was added so the three patterns are checkable.
- **`catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md`**: a shorter `#### Workflow-control vocabulary: gate, resume, continue-on-error` subsection under Step 8 (the continuous-operation / goal-based-stopping area), since this skill is a decision guide rather than the loop-assembly authority. It names the same three patterns as LLM-native, maps each onto Dynamic Workflows, and hands off to `[[loop-engineering]]` for the actual loop assembly with an explicit "do not build a bespoke YAML workflow engine" note. The two skills divide the labor cleanly: `loop-engineering` carries the worked treatment; `agent-orchestration-primitives` names the vocabulary and points to it.

### N3b - template composition strategies (sub-task 1.2)

- **`catalog/skills/workflow/agent-presets/SKILL.md`**: a `### Composition strategies` subsection under `## Customizing a preset`, documenting `replace` (default), `prepend`, `append`, and `wrap` (with a `{CORE_TEMPLATE}` placeholder shown in a minimal block), each with a concrete preset-layering example. Framed as the vocabulary for layering a project preset over a catalog default without forking the bundle.
- **`catalog/skills/specialized-domains/theme-tokens/SKILL.md`**: a `## Composition Strategies` section after `## Instructions`, applying the same four strategies to token-set layering (slot-resolution order for replace/prepend/append; an embedded base object for wrap), with a minimal JSON example of a prepend override that wins on `accent` and inherits the rest of a bundled theme. It re-routes brand overrides through `[[brand-styling]]`.

All added content is ASCII-only (hyphens, `->`, straight quotes), follows the Markdown style guide (blank line before/after every heading, list, and code fence), and introduces no external repo/product attribution.

## Key decisions

- **Workflow-control patterns framed as instructions, never a runtime.** The single most important framing constraint: comparison candidate N2b (a portable YAML workflow engine) is a deliberate decline, so N2a's vocabulary had to be documented as agent-instruction patterns over the existing Dynamic Workflows / `/loop` surface. Both edited skills carry an explicit "do not build a bespoke YAML workflow engine" line so a future reader does not mistake the vocabulary for a green light to build the declined runtime.
- **Asymmetric depth across the two N2a skills.** `loop-engineering` owns loop assembly, so it got the full section (three bullets + code examples + a Verification item). `agent-orchestration-primitives` is a primitive-choice decision guide, so it got a concise subsection that names the vocabulary and hands off to `loop-engineering`. This avoids duplicating the loop schema across the two files, consistent with the existing cross-reference discipline between them.
- **Composition strategies placed where each skill already discusses layering.** In `agent-presets` the subsection sits under the existing `## Customizing a preset` (swap / add step / add preset); in `theme-tokens` it sits after the token-mapping `## Instructions`. This keeps the new vocabulary next to the content it modifies rather than as an orphaned appendix.
- **One example per strategy, minimal.** Per the plan's "prose plus one minimal example per strategy" constraint, each composition strategy carries a concrete usage example inline, with one literal code/JSON block per skill for the non-obvious `wrap` placeholder (presets) and `prepend` slot-resolution (themes).
- **No frontmatter change, so no `data/` registry edit.** All four skills' `name` / `description` / `summary_l0` / `overview_l1` are untouched, so `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` need no edit (confirmed: all five JSON catalogs still load and the skill count is unchanged at 256).
- **Reused existing wikilink targets only.** The cross-links added in the new content (`[[loop-engineering]]`, `[[filesystem-context-patterns]]`, `[[brand-styling]]`) already appeared elsewhere in their respective files and all resolve to real skills, so the edits add zero new dangling-wikilink risk.

## Verification (quality gate: GO)

`make` is not on PATH on this Windows host (WN-v33-1), so the gates were run via the documented direct equivalents:

- **Orphan-bundle audit** (`validate_skills.py --bundles-only`, the gate `make validate` actually runs): PASS, 0 errors, 1 pre-existing warning (the `demo-capture` `scripts/__pycache__/*.pyc` build artifact, WN-v33-2). None of the four edited skills produced a bundle finding (no files added under `scripts/`, `references/`, or `assets/`).
- **Quality heuristics** (`validate_skills.py --quality`): PASS, 0 errors, 2 pre-existing warnings; none reference the four edited files.
- **ASCII-only** (`validate_unicode_safety.py`): 0 errors. The 1051 repo-wide warnings are all pre-existing (AGENTS.md em-dashes, legacy template curly quotes); a filter for the four edited files returned no hits.
- **No-personal-paths** (`validate_no_personal_paths.py`): exit 0.
- **`make lint`** (ShellCheck on `scripts/installer.sh` + `install.sh`): clean. No shell script was touched this phase.
- **Frontmatter intact**: each of the four files has exactly one `summary_l0` and one `overview_l1`.
- **SKILL.md body sizes**: loop-engineering 156, agent-orchestration-primitives 157, agent-presets 122, theme-tokens 177 lines - all well under the 500-line soft norm.
- **JSON catalog integrity**: `data/skills.json` (256 skills), `data/bundles.json`, `data/workflows.json`, `data/templates.json`, `data/marketplace.json` all load; no `data/` file changed.

Diff scope: four SKILL.md files plus the plan's Phase 1 exit checklist and this session history; no scope creep, no registry edit.

## Files changed

- `catalog/skills/workflow/loop-engineering/SKILL.md` (N2a, +new section + 1 verification bullet)
- `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` (N2a, +new subsection)
- `catalog/skills/workflow/agent-presets/SKILL.md` (N3b, +new subsection)
- `catalog/skills/specialized-domains/theme-tokens/SKILL.md` (N3b, +new section)
- `docs/v3/v3.6/plans/adoption-spec-kit.md` (Phase 1 exit checklist checked off)
- `docs/archive/v3/v3.6/development/history/2026-06-16_adoption-spec-kit-phase-1-skill-native-doctrine-folds.md` (this file)

## Next

Phase 2: ship the repo-internal `scripts/check_base_template_parity.py` guard (N3a) modeled on `check_version_sync.py` - a structural (not byte) comparison of the five `templates/ai-instructions/base-*.md` files that catches lock-step drift while tolerating intentional per-platform lines, wired into `make validate` and proven by a pytest module (pass on the in-sync set, fail on a desynced fixture, no false positive on an allowed-difference fixture). The CHANGELOG `[Unreleased]` block enumerating all five v3.6.0 adoptions and the reverse-engineering-matrix rows for the N5 + N1b declines are deferred to Phase 5 per the plan.
