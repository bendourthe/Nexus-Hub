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
