# Session History - v3.16.5 Phase 5: imagery placement intelligence

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 5 of 7 (not the terminal phase)
**Branch**: `feat/v3.16.5-presentify-visual-overhaul` (worktree)
**Model**: Opus 5. The plan recommends the **strong** tier at high effort, which Opus 5 is in the plan's map - the pre-flight agreed, no switch.
**Prerequisites**: Phase 3 (the render loop that hosts the pass) and Phase 4 (the question that triggers it). Both met.
**Closes**: v3.15 known-gap MT-2.

## Sub-tasks completed

### 5.1 - The placement-role taxonomy

Four roles in `references/interactive-features.md`, each with its own sizing and treatment: **hero / header**, **background**, **contextual illustration**, **gallery**. The background role carries a mandatory scrim recipe. The placement pass is specified to run inside the Phase 3 loop's first iteration and to produce, for every section, either a placement (role + why) or an explicit `no image: <reason>` - never silence. Relevance is checked before embedding, re-queried once, then declined rather than embedding filler. The `IMAGERY PLACEMENTS` record format is specified as a parseable block.

### 5.2 - The record check and the rubric

`visual_qa_score.py` gained `placement_decisions()` and an extension to criterion 4 rather than a tenth criterion. Rubric criterion 4 was rewritten to cover all four placement metrics with the structural/agent-vision split made explicit.

### 5.2b - Wiring and the MT-2 closure

SKILL.md Step 9 gained the placement-pass bullet, one Verification item, and three rationalization rows. The v3.15 MT-2 closure note was appended beneath the original record and its Phase 3 status note - neither was rewritten.

### 5.3 - Tests

Nine new tests covering all four record states, the `none`-path case, the parser, and the contract's content.

## What actually closes MT-2

Worth stating precisely, because it is not the obvious answer.

MT-2 deferred end-to-end grading of consented per-section integration to "the Phase 5 visual-QA loop". That loop now exists (Phase 3), and the placement decision now runs inside it. But running the decision there would NOT have closed the gap. The original problem was that nobody could tell, after the fact, whether a section had no image because it did not need one or because the pass forgot it - and no amount of instructing the agent to "integrate or explain" fixes that, because an instruction leaves no evidence.

What closes it is the RECORD, and the fact that the record is verified against the page. Three states fail:

- assets present with no `IMAGERY PLACEMENTS` block - the pass left no decision trail;
- a record claiming more embedded assets than the page contains - the record is fabricated;
- a decline with no reason - the outcome is fine, the silence is not.

That converts a hope into a checkable artifact. A skip is now distinguishable from a miss, which is the thing MT-2 was actually missing.

## Decisions worth recording

- **The embedded count is compared against the page's TOTAL `data:` count, not for equality.** A page's images include source figures extracted from the document, so a placement count BELOW the total is entirely normal while a count ABOVE it is provably wrong. Checking equality would have false-positived on every page carrying a source image - the kind of check people switch off, which is worse than no check.
- **An unexplained decline is MEDIUM.** A decline is valid, frequent, and often correct; an unexplained one is sloppy but does not break the page. Grading it HIGH would have made the gate noisier without making it stricter in any way that matters.
- **The scrim is a number, not an adjective.** "Use a dark overlay" is unverifiable. The recipe mandates ~82%, at which the composited background sits within a couple of percent of `--base`, so the EXISTING contrast check stays valid without knowing anything about the image behind it. The reason the number matters is documented too (WN-4): below roughly 75% the image shows through enough to move the effective background per-pixel, and at that point the answer is to move the text off the image rather than to lower the threshold.
- **The pass runs inside the loop, not before it.** Deciding placements from the content model was the earlier design, and it was guessing: a section that looks starved in the model may already read as full once rendered, and a band that looks fine may be visibly empty.
- **Relevance stays with the agent** (NI-5). A `data:` URI is opaque bytes. The render loop already has vision available at exactly the moment the judgment is needed; inventing image analysis inside a stdlib-only offline scorer would cost a great deal and buy nothing.

## Verification evidence

| Check | Result |
|---|---|
| Visual-QA suite | 79 passed (from 70) |
| Full presentify surface | 617 passed, 0 skipped |
| Lint (CI's target) | `ruff check --ignore RUF100` clean |
| Validators | all ten pass; orphan-bundle audit 0 warnings |
| Canonical fixture | still PASS across all criteria |
| Record states | matching record passes; no record fails HIGH; overclaiming record fails HIGH; unexplained decline fails MEDIUM and does NOT block |
| The `none` path | with no `--expect-images`, criterion 4 is n/a and the absence of a placement block is not a defect |
| Parser strictness | `placement:` is line-start anchored, so prose mentioning the word mid-sentence is not counted as a decision |

## Two test-mechanics notes

**The `_CLEAN` fixture needed updating, not working around.** It is scored with `expect_images=1`, i.e. as a consented run, so under the new check it required the placement record such a run must write. The fixture predates the convention; the check is correct. Weakening the check to accommodate an old fixture would have been the wrong repair.

**A bash heredoc collapsed escaped newlines inside a Python string literal again**, producing an unterminated-literal syntax error. Third occurrence of this trap in this plan - the first produced a backspace character inside a regex that silently matched nothing. The fix, as before, was to write the patch from a file rather than a heredoc, and to `ast.parse` the result before invoking pytest.

## Next steps

1. **Phase 6 - cinematic scroll-scrub.** Prerequisites (Phases 3 and 4) are met. It is the last feature phase and the largest remaining: a protocol reference, an offline scrub engine, intake wiring with rich-level agent discretion, and the reverse-engineering matrix row.
2. **Phase 7** is the terminal phase: refactor, known-gaps reconciliation (BG-E1, MT-1's location half, NI-4, NI-5, DF-2, WN-3, WN-4), CI/CD, then the `/update release` handoff.
