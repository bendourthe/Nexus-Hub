# Session History - v3.16.6 Phase 1: presentify coverage-depth (verbosity) intake axis

**Date**: 2026-08-12
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.6-presentify-verbosity-intake.md](../../plans/v3.16.6-presentify-verbosity-intake.md)
**Phase**: 1 of 2 (not final; Phase 2 is the terminal refactor / reconciliation / CI phase)
**Branch**: `feat/v3.16.6-presentify-verbosity-intake` (off `develop` at `8016cc13`, which carries the released v3.16.5 - the plan's hard prerequisite)

## Goal

Ship the coverage-depth (verbosity) axis end to end: a content-derived round-2 intake question, a `--verbosity` CLI flag, a `balanced` non-interactive fallback, design-record fields, per-level authoring rules, and the QA rubric criterion that catches an ignored answer.

## What was done, subtask by subtask

### 1.1 - Round-2 verbosity question and `--verbosity` flag

- `catalog/commands/presentify.md`: `--verbosity <distilled|balanced|comprehensive>` added to the usage line and the flag list, with the explicit content-axis vs `--qa-depth` (QA-thoroughness) distinction, the natural-language binding forms, the malformed-value degradation path (usage note, then ask or fall back; never blocks), the `verbosity -> balanced` entry in the non-interactive auto-pick list, and round-2 / delegation / notes prose updated to describe two content-dependent round-2 questions.
- `SKILL.md`: pipeline diagram round-2 box extended; Step 2's forward reference now names both round-2 choices; Step 5 retitled "color scheme + coverage depth" with three new bullets - the content-derived question (options carry an approximate section count for THIS source set; a tiny source still gets the question with generic descriptions), the skip/fallback contract (flag is a PRESET and always wins; memory never pre-answers; `balanced` default), and the design-record fields (level, provenance `flag-preset` / `asked` / `defaulted`, section-count target).

### 1.2 - Per-level authoring depth rules

- `SKILL.md` Step 6: a "Coverage depth" bullet directly after Structure defines the three levels operationally (Distilled collapses detail into summary devices; Balanced keeps every major topic, drops appendix-grade material to a reference list; Comprehensive drops nothing silently, may use collapsed regions). Compile-mode per-source attribution WINS over distillation; a design record without a level grades as `balanced`; depth never excuses the readability floors (more sections, not smaller text).
- New Common Rationalizations row guarding BOTH directions: cutting a comprehensive page for flow, and padding a distilled page that "looks thin".

### 1.3 - QA rubric criterion 10

- `references/visual-qa-rubric.md`: "The nine criteria" became "The ten criteria"; criterion 10 "Coverage-depth match" grades the RENDERED SECTION STRUCTURE against the design record's level and section-count target - page-level (graded once per iteration against a `page` segment id), AGENT-VISION only, never raw word counts, never N/A, missing record graded as `balanced` plus a MEDIUM incomplete-record finding. The maintainer's no-deterministic-check decision (2026-08-11) is recorded inside the criterion text. Schema enum gained `coverage-depth`.
- SKILL.md's two stale "all eight criteria" mentions (the rubric had been nine since the v3.16.5 errata) now say ten, and the Step 9 enumeration lists all ten.

### 1.4 - Testing and stabilization

- 16 new prose-contract tests appended to `tests/skills/test_presentify_intake.py` (section 4), in the file's existing drift-between-surfaces idiom: usage line, three levels on both surfaces, `--qa-depth` distinction, pipeline ordering of the question, content-derived stem, flag-preset semantics, `balanced` fallback, malformed-value degradation, design-record fields, three authoring rules, attribution-over-distillation, missing-record-as-balanced (both surfaces), criterion 10 presence and constraints, no stale criteria counts, floors boundary, and the two-direction rationalization row.
- CI (Phase 8.3 finding, fixed): `presentify-extractor.yml` path filters gained `catalog/commands/presentify.md` in both `push` and `pull_request` lists - the intake tests have asserted on the command text since v3.16.5 Phase 4, so a command-only edit would have merged without running its guard. A PowerShell 5.1 `Set-Content -Encoding utf8` BOM was introduced and immediately stripped with the BOM-free .NET writer (the exact trap AGENTS.md documents).

## Test results

- Full `tests/` suite: **2351 passed, 17 skipped** (27m29s), including the 16 new tests.
- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors, 0 warnings).
- `python scripts/run_trigger_evals.py --gate`: PASS (0 un-allowlisted collisions, 0 routing failures; this skill ships no trigger-cases.json - WARN by policy, never a gate failure).
- Quality heuristics, unicode-safety, version-sync: PASS (warnings pre-existing).
- Ruff on the modified test file reports pre-existing v3.16.5-era style findings only; the repo's lint gates (ShellCheck; CI ruff scoped to the skill's `scripts/`) do not cover the tests dir, and reformatting it would be out-of-scope churn.

## Deviations

- `# DEVIATION:` markers: none in code. One in-passing correction beyond the plan's literal text: fixing the stale "eight criteria" counts and enumerating criteria 9-10 in Step 9's list - required because adding criterion 10 made the existing number wrong, and the sentence claims to enumerate all criteria.
- Registries (`data/*.json`, `SKILL_INDEX.md`) deliberately untouched: no frontmatter changed.

## Known-gaps delta

v3.16.6 subsection added to `docs/v3/v3.16/known-gaps.md`: NI-1 (verbosity contract is agent behavior, no deterministic check - by design), DF-1 (the v3.16.5 deferral was never bookkept; Phase 2 sub-task 2.2 closes by reference to that note), QG-1 (closed: the CI path-filter gap above). Summary table row added; header Last-updated refreshed.

## Next steps

- Phase 2 (final): terminal refactor pass, known-gaps reconciliation (close DF-1 by reference), CI/CD verification, then hand off to `/update release` for the v3.16.6 cut. The maintainer merges/tags; nothing is tagged or pushed automatically.
