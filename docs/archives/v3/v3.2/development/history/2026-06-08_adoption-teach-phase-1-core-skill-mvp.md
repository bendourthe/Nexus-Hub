# Session History -- v3.2.0 adoption-teach Phase 1: Core skill (solo-mode MVP)

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-teach.md`](../../plans/adoption-teach.md)
**Phase**: 1 of 3 -- core skill (solo-mode MVP)
**Branch**: `feat/adoption-teach` (created off `origin/develop`, `--no-track`)
**Outcome**: complete; all three sub-tasks (T001-T003) closed, all quality gates green.

## Goal

Ship one new `workflow` skill, `session-teach-back`, that adds a Socratic mastery-confirmation loop quizzing the HUMAN operator on what a session produced -- item by item against a persistent dated checklist, with a hard completion gate. Per the MCP Registry Policy reverse-engineer-first decision tree, the capability is `skill-native` (tier 2): pure catalog content with no new code, dependency, credential, or outbound call. The two hardest pieces are reused rather than rebuilt -- the session source is digested via the existing `session-query` extractor (tier-3 `re-full`, already built), and the dated checklist follows the `dev-progress-tracker` checkbox-file pattern.

## Subtasks completed

1. **T001 -- Core SKILL.md.** Created `catalog/skills/workflow/session-teach-back/SKILL.md` (133 lines). Implements the solo-mode Socratic loop (I1), the calibration opener (I9), the dated mastery checklist (I5), drill-into-why (I8), and the hard completion gate (I11). Pushy `description` (5 verbatim trigger phrases + a 3-way SKIP clause routing to `generate-session-history`/`session-history`, `session-query`, and `dev-progress-tracker`), `summary_l0` (15 words), `overview_l1` (133 words), and the full body contract: When to Use (with an explicit When NOT to use), Instructions (source resolution via `session-query`'s `discover-sessions`/`extract-session` scripts, the dated checklist spec, the one-question-per-exchange solo loop, the hard gate), Common Rationalizations (7 rows, each a concrete failure mode -- batching, deferred marking, skipping calibration, what-without-why, generic items, re-grepping, finishing early), a binary Verification checklist, and Related Skills cross-linking `[[session-query]]`, `[[session-history]]`, `[[generate-session-history]]`, `[[dev-progress-tracker]]`, `[[quality-gate-definitions]]`. No `scripts/` subdir (prompt-only), no slash command.
2. **T002 -- Register across the three registries.** Hand-registered (hand-edit over generator regen -- see Key decisions): 1 row in `data/SKILL_INDEX.md` + the Total label bumped 248 -> 249; 1 full entry in `data/skills.json` (schema-matched to `session-query`/`demo-capture`; version 1.0.0, security 100/100/95, size 133 lines / 13231 chars / 2927 tokens); and the `workflow` `skill_count` 37 -> 38 in `data/marketplace.json`. The pushy 828-char description was added to `scripts/validate_skills.allowlist.json` (mirroring `session-query` and the two most-recent skills, `skill-security-scan` and `agent-orchestration-primitives`).
3. **T003 -- Stabilization.** Emulated `make validate` (all validators invoked directly; `make` unavailable on host) and ran the skill-security scanner gate -- all green, 0 HIGH/CRITICAL. Confirmed the orphan-bundle audit is clean (no bundled subdirs), every `[[wikilink]]` resolves to a real skill, and the three registries agree (skills.json 251, marketplace category-sum 251, SKILL_INDEX rows 251; no duplicate names).

## Key decisions

- **Pushy description kept; allowlisted, not trimmed.** `scripts/validate_skills.py` default mode flags `description` > 250 chars as an error (mine is 828), but neither `make validate` nor the CI `validate` job runs default mode -- they run only `--bundles-only` and `--quality` (both PASS). The 250-char cap conflicts with the AGENTS.md mandatory pushy-description rule, and the plan's T001 explicitly requires 5 verbatim trigger phrases + a 3-way SKIP clause (which cannot fit in 250 chars). The two most-recent new skills (`skill-security-scan` ~886c, `agent-orchestration-primitives` ~900c) both ship pushy descriptions and are allowlisted, so `session-teach-back` followed that exact convention rather than mutilating the description (WN-v32-1).
- **Hand-registration over `build_skills_catalog.py` regen.** Per the recurring WN-v30-2 / v3.1.0 finding, the generator rewrites curated `data/` from SKILL.md frontmatter (which carries only the 4 required fields), so it would strip the curated `tags`/`based_on`/`size` and reset `version`. Registration was done by hand to keep every changed line traceable; the new `skills.json` entry was appended adjacent to `demo-capture` (the array tail).
- **Count label +1, not reconciled.** On `origin/develop` the `SKILL_INDEX.md` Total label read 248 while `skills.json` already had 250 entries -- the v3.1.0 release-time count reconciliation to 250 was applied on the release/main side and has not flowed back to `develop`. The in-scope action for adding one skill is +1 (248 -> 249); reconciling all count-prose surfaces to the truthful total (now 251) is the v3.2.0 release bump's job (`/update version`), exactly as the resolved WN-v31-3 did at the v3.1.0 release (WN-v32-3).
- **`based_on` attribution is generic.** Per the Reverse-Engineering Attribution Rule, the `skills.json` `based_on` describes the pattern ("net-new skill composing the session-query extractor and the dev-progress-tracker checklist pattern with a Socratic teach-back loop") and points at the in-repo comparison doc rather than naming the external source repo in the distributed artifact.

## Test results

- Emulated `make validate` (each validator invoked directly; `make` unavailable on host): JSON catalogs OK (**skills.json 251 skills**); orphan-bundle audit **PASS (0 errors, 0 warnings)**; quality heuristics **0 errors on `session-teach-back`** (the 1 catalog warning is the pre-existing `git-branching-workflow` overview-length one); no-personal-paths, unicode-safety (the new SKILL.md is ASCII-clean), supply-chain-iocs, workflow-security, solution-frontmatter all clean; `check_version_sync.py` green.
- Skill-security scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0, clean** (no HIGH/CRITICAL). The skill ships no scripts, so there is no behavioral-AST surface.
- Strict `validate_skills.py --allow-existing` scoped to the new skill: **0 errors, 6 warnings** -- an identical warning set to its sibling `session-query` (the grandfathered >250-char description demotion plus the 5 optional-field-absent warnings that every catalog skill carries, since `version`/`tags`/etc. live in `skills.json`, not the SKILL.md frontmatter).
- Registry consistency: skills.json array == 251; `workflow` `skill_count` 38 in marketplace; marketplace category-sum 251 == skills.json count; SKILL_INDEX gained 1 workflow row (every skills.json skill has a SKILL_INDEX row); no duplicate skill names.
- Markdown style spot-check on the new SKILL.md: blank lines around all lists/tables/code fences, single document H1, ASCII-clean, no hard-wrapping.

## CI/CD edits

- None. GitHub Actions (`ci.yml`) is the active CI; its `validate` job loads `skills.json` and runs the same validators + the scanner gate over `catalog/skills` + `catalog/mcp-configs`, so the new skill auto-discovers. The phase added no new script command, environment variable, or dependency, and the skill folder auto-distributes via the installers' recursive folder copy (no installer edit). The strict description-length check is not run by CI, so the grandfathered description does not affect the green build. 0 workflows touched, 0 proposed edits.

## Deviations

- None. The plan was followed exactly (T001-T003 as written). The allowlist edit is the established mechanical consequence of the plan's pushy-description requirement (see Key decisions), not a scope deviation.

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with prior phases' WN), so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly. `make lint` is not applicable -- the phase added only Markdown + JSON, no shell surface (WN-v32-2, covered by CI).
- The YAML frontmatter `description` initially failed to parse because of a `: ` (colon-space) in the SKIP clause, which YAML reads as a mapping separator inside an unquoted scalar; it was rewritten to use commas (mirroring `session-query`'s style) so the unquoted scalar parses.
- `data/marketplace.json` has no `statistics.total_skills` field; the per-category `skill_count` sum is the machine-readable total (now 251), and the catalog headline total lives in prose surfaces reconciled at release.

## Known gaps

See [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md). Three new open items this phase, all WN: WN-v32-1 (the default-mode 250-char description cap is not a gate and conflicts with the pushy-description rule; the long description was kept and allowlisted by design), WN-v32-2 (local make/shellcheck absent, covered by CI), WN-v32-3 (count-prose surfaces on `develop` predate the v3.1.0 release reconciliation; all count surfaces reconcile to the truthful total at the v3.2.0 release bump). 0 resolved (Phase 1 is the first phase).

## Next steps

- **Phase 2 -- modes + interaction enhancements**: add the teach-someone-else mode (I14, with `student`/`mode: teaching` checklist frontmatter, triggered by phrase not a flag), eli5/eli14/intern depth levels (I12), the multiple-choice discipline (I13, vary answer position, reveal only after the user responds), and the opt-in (off-by-default, confirmation-gated) checklist commit (adaptation N1). Keep the body <=500 lines; push the teaching-mode walkthrough to `references/teaching-mode.md` if it approaches the cap. Re-run `make validate` + the scanner; refresh the `skills.json` `size` field for the grown body.
