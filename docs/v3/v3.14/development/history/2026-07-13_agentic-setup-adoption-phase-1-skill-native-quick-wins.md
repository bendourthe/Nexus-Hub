# Session History -- agentic-setup-adoption, Phase 1 (skill-native quick wins)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 1 of 8 -- Skill-native quick wins: false-confidence test audit + commit sweep
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Ship the two lowest-effort, highest-leverage skill-native items from the v3.12.1 comparison: a skill that audits an existing test suite for false confidence, and a skill that sweeps recent commits at a higher altitude than per-diff review. No new local artifacts.

## What was done

### 1.1 false-confidence-test-audit skill

Authored `catalog/skills/tests-generation/false-confidence-test-audit/SKILL.md` (92 lines). It teaches a fast, read-the-assertions audit that classifies each test REAL / WEAK / FALSE-CONFIDENCE against a concrete anti-pattern catalog (tautological assertions, assertion-on-a-mock, subject-fully-mocked-away, no-assertion, catch-and-pass, over-broad exception match, rubber-stamped snapshot, frozen-clock-only truth), proposes a concrete repair per non-REAL test, and optionally verifies the repair with a single-mutation check. The description and a dedicated section fence it off from the compute-heavy `mutation-testing` (empirical proof) so the two do not fight over triggers.

### 1.2 commit-sweep skill

Authored `catalog/skills/workflow/commit-sweep/SKILL.md` (85 lines). It sweeps a window of recent commits (default 10) read-only, clusters changes by subsystem, and evaluates each cluster for what emerged across commits that a single-diff review cannot see (partial/abandoned refactors, convention drift, TODO debt, undocumented dependency changes, security-relevant deltas, thrash), then emits severity-tagged findings and offers follow-ups. Distinguished from `/review diff`, `git-bisect-assistant`, and `regression-root-cause-analyzer`.

### 1.3 Registration + validation

Registered both skills across the three metadata files: `data/skills.json` (entries inserted next to their category siblings, with the `size` metrics computed via the generator's own formulas), `data/SKILL_INDEX.md` (+2 rows), and `data/marketplace.json` (tests-generation 18 -> 19, workflow 43 -> 44). The `SKILL_INDEX.md` total was corrected 265 -> 268 to match the true skill count (it was already stale by one before this phase).

## Deviations

- **Version renumber**: the plan was drafted as v3.13.0, but v3.13.0 is the committed presentify-universal-ingestion version, so it was renumbered to v3.15.0 (user-confirmed) during this phase. A later consolidation refactor moved it from v3.15.0 to v3.14.0 (this file's current home), pairing agentic-setup with codex-lb-adoption under the v3.14 cycle.
- **Generator not used**: `infrastructure/tools/build_skills_catalog.py` was NOT run to regenerate `data/`, because it rewrites the whole tree (a 6281-line diff - the committed files diverge from that generator's output/ordering). The three registry files were hand-edited for a minimal, reviewable diff instead; JSON validity and the skill count were verified afterward.

## Validation

- `data/skills.json`: valid JSON, 268 skills, no duplicate names, both new skills present.
- Bundle-orphan audit: PASS (0 errors). Quality heuristics: PASS (0 errors, no warnings on the new skills). Unicode safety: the two new skills are ASCII-clean. No-personal-paths: PASS. `data/marketplace.json`: valid.
- Quality gate: GO. No code tests apply to Markdown skills (coverage N/A); 0 lint-applicable changes; the catalog builds and validates.

## Next steps

- Phase 2: skill-native lint-repair loop + an opt-in deterministic autofix precommit hook. Note the `catalog/hooks/settings.json` edit is an ask-first gate.
