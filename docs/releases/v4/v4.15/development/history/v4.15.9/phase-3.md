# v4.15.9 Phase 3 (reduced): delegation disciplines

Started 2026-11-18T00:00Z.

## Done

- T014: `### Effort escalation ladder` in `model-routing/references/effort-modifiers.md`, with the low-then-rerun-failures batch pattern and the source URL; one new ownership row.
- T015: one sentence in `model-routing/SKILL.md` Step 6 (Claude Code bullet) on the cache write after a model switch and compacting first.
- T016: `### Filter first for bulk data` in `context-optimization/SKILL.md`, with a Verification item.
- T017: one scoping sentence under section 5 of `direct-corpus-interaction/SKILL.md` pointing to `context-optimization`; the filter rule is not restated there.
- T021: `### Repeated-failure ownership` in `model-routing/SKILL.md`: detection "Not shipped", reset "Deferred", retry change "Shipped"; order reset first, then retry one rung up.

## Deferred (after v4.15.5 merges, or claimed elsewhere)

3.3 (T018, T019) and 3.4 (T020). The ownership table says "Not shipped" and "Deferred" for those rows until they land.

## Verification

- Anchor check: `git grep -n -F` over `catalog/skills/` returns exactly one hit each for the escalation ladder, filter-first, and repeated-failure ownership headings.
- `python scripts/validate_skills.py --bundles-only`: 0 errors. `python scripts/check_registry_entries.py --check --strict`: pass. Fast profile: 18 passed.

## CI impact

No new commands, dependencies, or test paths.

## Completion pass (2026-11-21)

v4.15.5 is merged to `develop` (branch refreshed at `af448b52a`), so 3.3 ran.

- T018: `### Two failed corrections reset` in `context-degradation/SKILL.md`, with a Verification item. It owns when to reset and links to `model-routing` for the retry.
- T019: `### Pilot before the full batch` and `### Throughput countermeasure` in `loop-engineering/SKILL.md` (Step 5), each with a Verification item.
- T021 update: the ownership table now names `catalog/hooks/stuck-turn-notice.sh` (v4.15.5, opt-in) for detection and `context-degradation` for the reset, both Shipped.
- T020 (3.4, deferrable) stays deferred: v4.15.11 claims `model-prompting-research/SKILL.md` and has not merged. Proposed for 6.2 as a known gap.

## Plan delta

No blocking delta. Evidence: the planned detection notice shipped under the name `stuck-turn-notice`, not the plan's working name, so the table cites the real file. Consequence: none for Phases 4 to 6.

## Verification (completion pass)

- Anchor check, `git grep -n -F` over `catalog/skills/`: one hit each for the escalation ladder, filter-first, two-failed-corrections reset, pilot, throughput countermeasure, and repeated-failure ownership headings; zero for the post-model-release audit (deferred, as expected).
- `python -B scripts/validate_skills.py --bundles-only`: PASS, 0 errors. `python -B scripts/check_registry_entries.py --check --strict`: pass. Fast profile: 18 passed, 0 failed.

## CI impact (completion pass)

No new commands, dependencies, or test paths.
