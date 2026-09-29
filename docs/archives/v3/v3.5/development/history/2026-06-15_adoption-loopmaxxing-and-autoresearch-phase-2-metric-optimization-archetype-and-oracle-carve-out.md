# Session History - v3.5.0 adoption-loopmaxxing-and-autoresearch Phase 2: metric-optimization archetype + per-iteration budget + oracle carve-out

**Date**: 2026-06-15
**Plan**: [`../../plans/adoption-loopmaxxing-and-autoresearch.md`](../../plans/adoption-loopmaxxing-and-autoresearch.md) Phase 2 (G5 + R2 + R3, all skill-native)
**Branch**: `feat/loop-engineering-enrichment`
**Outcome**: Implementation complete; quality gate GO. Phase 2 of 3, so Phase 3 (observability fields, retries-then-handoff default, "loopmaxxing" label) follows. No release work this phase.

## Goal

Add the one loop shape the library lacked (scalar-metric optimization), a per-iteration compute-budget field, and the deterministic-oracle carve-out to the maker-self-certifies anti-pattern. Pure local catalog enrichment of two existing reference files; no new skill, command, outbound call, dependency, or credential, and no frontmatter change.

## What shipped

- **`catalog/skills/workflow/loop-engineering/references/loop-library.md`** (sub-task 2.1): a new sixth archetype `optimize-metric-keep-best`, added after `pr-self-review` in the same YAML-in-fenced-block format as the existing five entries. Its YAML block uses only the nine schema-defined fields (`name`, `goal`, `iteration_cap: 20`, `check_command` placeholder for a project metric command emitting one scalar, `exit_condition` keyed to the optimization target with the best result retained, `driver: /loop` with manual fallback, `maturity: experimental`, `agents`, `tags: [optimization, metric, benchmark, keep-best]`). A 2-4 line note below the block explains that this loop differs from the green/not-green archetypes because its exit is an optimization target rather than a binary pass (each iteration makes a change, reads one scalar metric, keeps the change only if the metric improved, reverts otherwise), forward-references the optional `per_iteration_budget` and `progress_check` schema fields, and describes the shape generically as the one behind overnight metric-optimization runs (e.g. an ML experiment loop) with no external repo/product attribution.
- **`catalog/skills/workflow/loop-engineering/references/loop-schema.md`** (sub-task 2.2): (A) a new optional `per_iteration_budget` field row in the Fields table - a hard cost ceiling for a single iteration (wall-clock, tokens, or tool calls), orthogonal to `iteration_cap`, which bounds the iteration count rather than the cost of each pass - plus a clarifying line after the table stating that the first nine fields are required and any field whose Purpose begins with "Optional" is additive (existing loop definitions stay valid without it). (B) the "Maker self-certifies exit" anti-pattern bullet now carries a carve-out: the maker and checker may be the same agent only when the checker is a deterministic, non-LLM oracle (a numeric metric, an exit code, or a compiler result), because a deterministic oracle is its own independent check; whenever the checker is itself an LLM, the maker must not also be the checker. The original rule's intent is intact - the carve-out adds the precise boundary rather than removing the rule.

All added content is ASCII-only (hyphens, straight quotes), follows the Markdown style guide (blank line before/after every heading, fenced block, and the new note paragraph), preserves the file's existing CRLF line endings, and introduces no external repo/product attribution.

## Key decisions

- **Forward-referenced optional fields kept out of the YAML block.** The new archetype's note points ahead to `per_iteration_budget` (added this phase) and `progress_check` (Phase 3), but the YAML block itself uses only the nine schema-defined fields, so it stays validatable against the schema as it exists today. The acceptance criterion ("uses only schema-defined fields plus the two new optional ones it forward-references") is satisfied by confining the forward-references to prose.
- **Carve-out makes the new archetype self-consistent.** `optimize-metric-keep-best` lets one agent both make and check, which would otherwise trip the "Maker self-certifies exit" anti-pattern. The deterministic-oracle carve-out authorizes exactly that case (the checker is a scalar metric, an independent deterministic oracle), so the new archetype and the qualified anti-pattern agree by construction.
- **Optionality marked in-cell, single Fields table.** Per the plan's phasing (Phase 3 adds three more optional fields to the same table), `per_iteration_budget` was added as a row of the existing Fields table with "Optional" leading its Purpose cell, plus one clarifying note, rather than splitting into a separate optional-fields table. This keeps the schema forward-compatible with the Phase 3 additions.
- **No new wikilinks introduced.** The archetype's note links the schema with a relative Markdown link (`[loop-schema.md](loop-schema.md)`), and the schema edits add no `[[...]]` wikilinks, so Phase 2 carries zero new dangling-wikilink risk.
- **No frontmatter change, so no `data/` registry edit.** Only the two reference files changed; the skill's `name` / `description` / `summary_l0` / `overview_l1` are untouched, so `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` need no edit (the registry-edit decision is formally re-checked at Phase 3's 3.4).
- **CHANGELOG entry deferred to Phase 3.** Matching Phase 1's precedent and the plan's exit-checklist phasing, the single consolidated `## [Unreleased]` CHANGELOG entry for the whole v3.5.0 loop-engineering enrichment is added at Phase 3 closeout rather than churned per phase.

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so gates were run via the documented direct equivalents:

- **Orphan-bundle audit** (`validate_skills.py --bundles-only`, the gate `make validate` actually runs): PASS, exit 0 (0 errors, 1 pre-existing WN-v33-2 warning about `demo-capture`'s `scripts/__pycache__/*.pyc` build artifact, unrelated to this phase). The `loop-engineering` skill produced no bundle finding, confirming both reference files are still linked from SKILL.md (no new orphans).
- **ASCII-only** (`validate_unicode_safety.py`): exit 0, zero errors; a locale-safe (`LC_ALL=C`) byte scan of both edited files found no non-ASCII characters and no tabs. The validator's repo-wide warnings are all pre-existing (e.g. a legacy `templates/ai-instructions/legacy/.../typescript.md` curly quote) and unrelated to this phase.
- **No external repo/product name**: grep for `autoresearch`, `karpathy`, and `alphasignal` across both reference files returned zero matches.
- **New archetype uses schema-defined fields only**: the top-level YAML keys in the `optimize-metric-keep-best` block are exactly the nine required fields (`name`, `goal`, `iteration_cap`, `check_command`, `exit_condition`, `driver`, `maturity`, `agents`, `tags`); the optional `per_iteration_budget` / `progress_check` appear only in the prose note.
- **Markdown rendering**: the new heading, fenced YAML block, and note paragraph have correct blank-line spacing; the schema's new field row sits inside the table and the clarifying note is one blank line off it.
- **SKILL.md untouched**: Phase 2 edits only the two reference files, so the SKILL.md body is unchanged at 131 lines (under the 500-line size norm).

Diff scope: the two intended reference files plus the plan's Phase 2 exit checklist and this session-history doc; no scope creep, no frontmatter or `data/` change.

## Files changed

- `catalog/skills/workflow/loop-engineering/references/loop-library.md`
- `catalog/skills/workflow/loop-engineering/references/loop-schema.md`
- `docs/v3/v3.5/plans/adoption-loopmaxxing-and-autoresearch.md` (Phase 2 exit checklist)
- `docs/archive/v3/v3.5/development/history/2026-06-15_adoption-loopmaxxing-and-autoresearch-phase-2-metric-optimization-archetype-and-oracle-carve-out.md` (this file)

## Next

Phase 3: add optional `trace_log` and `progress_check` schema fields plus a Production Loops note (G3), add the retries-then-handoff default and the optional `handoff` field (G4), and name "loopmaxxing" as a recognition label in the Common Rationalizations table without weakening any guardrail (G6). Phase 3's 3.4 also runs the full cross-file consistency read-through, makes the formal registry-edit decision, and adds the consolidated CHANGELOG `## [Unreleased]` entry for the whole v3.5.0 enrichment. The `progress_check` notion that this phase's `optimize-metric-keep-best` archetype forward-references is formalized in Phase 3.
