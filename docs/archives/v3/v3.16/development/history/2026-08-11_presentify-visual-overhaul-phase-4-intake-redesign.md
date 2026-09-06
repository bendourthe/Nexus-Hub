# Session History - v3.16.5 Phase 4: intake redesign

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 4 of 7 (not the terminal phase)
**Branch**: `feat/v3.16.5-presentify-visual-overhaul` (worktree)
**Model**: Opus 5. The plan recommends the **strong** tier at high effort, which Opus 5 is in the plan's own map - the pre-flight agreed and no switch was needed.
**Prerequisites**: none (the phase is parallel-safe with 1-3). The plan places it after Phase 3 so its intake copy can reference the QA loop honestly, which it now can.

## Sub-tasks completed

### 4.1 - The four-option additional-imagery question (R8)

Procedural visuals became the ALWAYS-ON baseline, so the question asks only what to ADD: `none` / `stock` / `ai` / `both`. Legacy `--images` spellings still bind (`procedural` -> `none`, `auto` / `mix` -> `both`). Every consent invariant carried over verbatim - the gate, the offline default, the "a recalled preference is never consent" rule - with only the option names changed.

The `None` option is explicitly described as "the built-in visuals only, NOT a bare page", because a menu option called None reads as nothing at all, and the whole point of restructuring was that procedural visuals are no longer optional.

### 4.1b - Registry sync

The frontmatter `description`, `summary_l0`, and `overview_l1` all carried the superseded "tiered imagery" framing, so `data/skills.json` and `data/SKILL_INDEX.md` were hand-edited to match. Diff: 4 lines. `build_skills_catalog.py` was deliberately not run - it rewrites the whole tree and would have buried a three-field change in ~6000 lines.

### 4.2 - Two-round intake with content-derived schemes (R10)

Round 1 keeps its position and its four choices. Round 2 runs at the head of Step 5, after extraction and figure classification, offering three named schemes with 5-swatch previews plus Other. `design_seed.py --scheme-hint` accepts the choice as inline JSON or a file path and pins the palette. The pipeline diagram, the command doc's flow description, and its notes section all show both rounds.

### 4.3 - Testing

A new `tests/skills/test_presentify_intake.py`: 36 tests across doc-consistency (both surfaces agree on option values, aliases, the disclosed semantic change, pipeline order, the skips, the diagram) and `--scheme-hint` behavior (end-to-end through the real script, plus in-process unit tests for the two new helpers).

## The decisions worth recording

- **Round 2 runs after extraction because that is the only point it CAN.** A content-derived scheme needs content. The requirement that each proposal cite its content signal - the source figures' own series colors, an existing logo, the subject's era - is what separates this from three random palettes with nice names, so it is stated as a gate rather than a suggestion: a scheme with no citable signal is not content-derived and should not be offered.
- **The scheme is a CONSTRAINT on the roll, not a replacement for it.** `--scheme-hint` pins the palette and nothing else. Type voice, layout signature, motion personality, signature move, and spacing rhythm still roll, and `hue_family` - one of the three anti-convergence rejection axes - is deliberately left as ROLLED even when the palette is pinned. Rewriting it would have made the history comparison start measuring the user's color choice instead of the sampler's variety, quietly defeating the anti-convergence design. A `palette_source` field records where the colors actually came from so the design record stays honest about the discrepancy.
- **A malformed hint exits 2 rather than degrading.** Nearly every other failure path in this skill degrades to something safe. This one must not: silently rolling an unpinned palette would ship colors the user did not choose, which is worse than an error. No brief is written on failure.
- **The `none` semantic change is disclosed, not smoothed over** (DF-2). The alternative was a fifth `bare` option existing only to preserve a mode R8 deliberately removed. Both surfaces say "no longer exists" and a test asserts that disclosure so it cannot be dropped in a later edit.

## A test that passed for the wrong reason

Found while checking coverage of the new code rather than by a failure, which is the only way this class shows up.

Two of the five "malformed input" cases were exercising the wrong branch. `load_scheme_hint` treats any value that does not start with `{` as a FILE PATH, so `'["a"]'` - intended to test the "JSON is not an object" guard - failed earlier on "not a readable file". The test passed, the label was wrong, and the object guard was unreachable by any test in the suite. It now has a real test that writes a file containing a JSON array, and the mislabelled subprocess case was relabelled to describe what it actually checks.

Worth noting because the tell was not a failing test: it was two uncovered lines inside a function the suite claimed to cover thoroughly.

## Verification evidence

| Check | Result |
|---|---|
| New intake suite | 36 passed |
| Full presentify surface | 608 passed, 0 skipped |
| Lint (CI's target) | `ruff check --ignore RUF100` clean |
| Validators | all ten pass, including the trigger-eval gate after the frontmatter change |
| Registry diff | 4 lines across the two files (not a 6000-line rebuild) |
| `--scheme-hint`, end to end | palette pinned; type / layout / motion / signature / spacing / mood identical to the unpinned roll at the same seed; `hue_family` unchanged; a different seed still moves the other axes |
| `--scheme-hint` error paths | 5 malformed-input cases each exit 2 with no brief written |
| CI | no change needed - `presentify-extractor.yml` path-filters both changed catalog trees, and `ci.yml` uses `'**'` minus `docs/**`, so `catalog/commands/`, `data/`, and `tests/` are all covered |

## Deviations from the plan

- **`--images both` is the new canonical spelling** where the plan's prose sometimes says `mix`. `both` is the maintainer's own wording from R8's option list; `mix` and `auto` are retained as aliases. Recorded so a reader of the plan is not confused by the difference.
- **E2's contract text was already in place** from the errata pass, so 4.2 needed no measure-related change - only the intake wiring.

## Known gaps

Two new, no blockers. **NI-4**: the questions themselves are agent behavior - no test can assert a proposed scheme is relevant to a document, only that the instruction to make it relevant exists. The deterministic half is tested and the visual half is graded by the Phase 3 render loop. **DF-2**: the `none` semantic change, accepted and disclosed.

## Next steps

1. **Phase 5 - imagery placement intelligence.** Its prerequisites are now both met: Phase 3 built the loop that hosts the placement pass, and Phase 4 built the question that triggers it. It closes the remaining half of v3.15 MT-2.
2. Phase 6 (cinematic scroll-scrub) depends on Phases 3 and 4, so it is also unblocked.
3. Phase 7 owns MT-1's location half and reconciles BG-E1, NI-4, and DF-2 with the rest of v3.16.
