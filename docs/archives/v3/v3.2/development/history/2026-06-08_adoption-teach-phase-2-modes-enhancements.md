# Session History -- v3.2.0 adoption-teach Phase 2: Modes + interaction enhancements

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-teach.md`](../../plans/adoption-teach.md)
**Phase**: 2 of 3 -- modes + interaction enhancements
**Branch**: `feat/adoption-teach`
**Outcome**: complete; all four sub-tasks (T004-T007) closed, all quality gates green.

## Goal

Extend the `session-teach-back` skill body (shipped in Phase 1) with the four remaining `/teach` insights, all as prompt-only edits to the same SKILL.md: the teach-someone-else mode (I14), eli5/eli14/intern depth levels (I12), the multiple-choice discipline (I13), and an opt-in off-by-default checklist commit (adaptation N1). No new code, dependency, credential, outbound call, slash command, `scripts/` subdir, or `references/` file. Keep the body within the 500-line size norm.

## Subtasks completed

1. **T004 -- Teach-someone-else mode + depth levels.** Added a new "Teach-someone-else mode (optional)" Instructions section (renumbered the hard completion gate 4 -> 5): it reuses the same mastery checklist as a teaching guide, setting `mode: teaching` + `student: <name>` in the frontmatter, suggesting an explanation strategy per section, proposing the questions to pose to the student, and confirming an item `[x]` only once the student demonstrates it. Triggered by phrase ("help me teach this to <name>", "teaching mode"), explicitly NOT a `--student` argv flag. Depth levels landed as a new step 8 in the solo loop (concise, under ~2000 chars per turn; eli5/eli14/intern framing on request). The two teaching-mode phrases were added to the Tier-1 `description` and a "When to Use" bullet (so the mode is cold-discoverable), and the checklist-frontmatter item-rule was updated to document the `mode` (solo|teaching) / `student` fields.
2. **T005 -- Multiple-choice discipline.** Folded into the existing solo-loop "ask one targeted question" step (step 4): when a question is multiple choice, vary the correct-answer position across questions (not always "C") and never reveal the answer until after the user responds.
3. **T006 -- Opt-in checklist commit.** Added an "Opt-in: commit the mastery checklist (off by default)" section: the default is to write the checklist locally and stop; the skill MAY OFFER to commit with a suggested `data(teaching): add <slug> mastery checklist` message, but only after explicit user confirmation, and never auto-pushes -- respecting the `git-guardrails` hook and the global outward-git-requires-confirmation rule. The Phase 1 gate parenthetical ("committing is out of scope for this core version") was updated to point at the new section. Added a Common-Rationalizations row ("I'll just auto-push the checklist to save the user a step") and three Verification items (teaching-mode frontmatter, multiple-choice discipline, confirmation-gated commit).
4. **T007 -- Stabilization.** Emulated `make validate` (each validator invoked directly; `make` unavailable on host) and ran the skill-security scanner gate -- all green, 0 HIGH/CRITICAL with 0 findings on `session-teach-back`. Refreshed the `data/skills.json` `size` field for the grown body and confirmed the SKILL.md is 158 lines (under the 500-line norm) with no `references/` file to orphan.

## Key decisions

- **Description synced for teaching mode, not left to drift.** Teaching mode is a cold-start trigger surface, so the two phrases ("help me teach this to someone", "put me in teaching mode") were added to the Tier-1 `description` -- the only place a cold trigger phrase fires, since "When to Use" is Tier-2 (loaded after the skill already triggered). The `data/skills.json` `description` was synced to match the SKILL.md so the registry stays truthful. The pushy description grew 828 -> 923 chars; it remains allowlisted in `scripts/validate_skills.allowlist.json`, and the >250-char default-mode check is still not a `make validate` / CI gate (WN-v32-1, char count updated).
- **Body edits only; no Tier-3 externalization needed.** The plan allowed moving the teaching-mode walkthrough to `references/teaching-mode.md` if the body approached the 500-line cap. It did not (134 -> 158 lines), so the detail stayed inline and no bundled subdir was created (keeps the orphan-bundle audit trivially clean).
- **`size` refreshed by hand, not via regen.** Consistent with Phase 1 (and the recurring WN-v30-2 finding that `build_skills_catalog.py` clobbers curated `data/`), the `skills.json` `size` block was edited by hand to 158 lines / 16889 chars / 3738 tokens rather than running `make build-catalog`.
- **No marketplace count change.** Phase 2 grows an existing skill; it adds none, so the catalog stays at 251 and `data/marketplace.json` / `data/SKILL_INDEX.md` counts were untouched.

## Test results

- Emulated `make validate` (each validator invoked directly; `make` unavailable on host): JSON catalogs OK (**skills.json 251 skills**, unchanged); `validate_skills.py --bundles-only` (orphan audit -- no bundled subdirs) and `--quality`, no-personal-paths, unicode-safety (the additions are ASCII-clean), supply-chain-iocs, workflow-security, solution-frontmatter all clean; `check_version_sync.py` green. 0 failures across all 8 validators.
- Skill-security scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0, score 100/100, 0 HIGH/CRITICAL**. The 15 catalog findings (13 MEDIUM, 2 LOW) are all pre-existing in other skills (`skill-security-scan`, `code-review`, `ai-attack-patterns`, `mcp-builder`, `context-optimization`, `skill-description-authoring`, `demo-capture`, `advanced-attack-patterns`, `mcp-servers.json`); **0 on `session-teach-back`** -- the prompt-only skill has no behavioral-AST surface.
- Size / norm: SKILL.md is 158 lines (under the 500-line norm) and 16889 ASCII bytes; `skills.json` `size` refreshed to match. The `description` is 923 chars (allowlisted).
- Markdown style spot-check on the edited SKILL.md: blank lines around all lists/tables/headings, single document H1, ASCII-clean, no hard-wrapping.

## CI/CD edits

- None. The GitHub Actions `validate` job loads `skills.json` and runs the same validators + the scanner gate over `catalog/skills` + `catalog/mcp-configs`, so the grown skill is re-validated automatically. The phase added no new script command, environment variable, or dependency, and no `scripts/<name>.py` artifact, so no installer edit is required (the skill folder auto-distributes via the installers' recursive copy). 0 workflows touched, 0 proposed edits.

## Deviations

- None. The plan was followed exactly (T004-T007 as written). Syncing the `skills.json` description and adding the teaching-mode trigger phrases to the Tier-1 `description` are the mechanical consequence of T004's "trigger by phrase" requirement (so the mode is cold-discoverable), not a scope deviation.

## Troubleshooting / environment notes

- `make` and `shellcheck` remain unavailable on the Windows dev host, so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly. `make lint` is not applicable -- the phase added only Markdown + JSON, no shell surface (WN-v32-2, re-confirmed; covered by CI).
- No new YAML-parse pitfalls: the teaching-mode phrases were added with commas (the SKIP-clause convention established in Phase 1), so the unquoted `description` scalar still parses.

## Known gaps

See [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md). 0 new open items this phase, 0 resolved; 3 WN open total. WN-v32-1 was updated (description grew 828 -> 923 chars with the two teaching-mode trigger phrases; still allowlisted, still not a gate) and WN-v32-2 was re-confirmed for Phase 2 (local make/shellcheck absent; phase added only Markdown + JSON). WN-v32-3 (count-prose reconciliation at the release bump) is unchanged -- the catalog is still 251.

## Next steps

- **Phase 3 -- integration + discoverability**: add bidirectional `[[session-teach-back]]` back-links to the Related Skills sections of `session-query`, `session-history`, and `dev-progress-tracker`; add a one-line `session-teach-back` mention to `using-nexus-hub`; add a CHANGELOG `## [Unreleased]` -> `### Added` entry for the new skill; then run the final green check (`make validate` + `make lint` + scanner, every `[[...]]` link resolves, no new slash command, no installer edit). Phase 3 is the final phase, which triggers the release-readiness routing to `/update release` at the develop -> main release.
