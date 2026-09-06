# Session History - Presentify Slide Navigation Phase 4: QA Loop and Structural Scorer Support

**Date**: 2026-08-22
**Branch**: `feat/presentify-slide-navigation`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.3-presentify-slide-navigation.md`](../../plans/v3.18.3-presentify-slide-navigation.md)
**Phase**: 4 - QA loop and structural scorer support
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12.10, pytest; GNU Make unavailable, so `make validate` and `make test` were executed as their constituent commands
**Outcome**: The rubric carries criterion 12 (slide-mode integrity, N/A on every scrolling page), SKILL.md Step 9 carries the per-slide capture protocol with the settle-then-capture rule, and `visual_qa_score.py` gained a seven-check slide-mode family (348 lines) with 30 new tests (38 cases) - one seeded defect per check, the skip-not-fail proofs, and an aggregate malformed-input guard. The checks were exercised end to end against the real pages built in Phases 2 and 3, where they caught a genuine omission before any fixture proved anything.

## 1. Starting State

- **Starting commit**: `a58286fd` (Phase 3, same branch)
- **Worktree**: clean
- **Model routing**: the plan records `strong / high`; the session model is Opus 5, the `strong` tier in the plan's own model map - an exact match, so no switch was made.

## 2. What Was Implemented

### 4.1 - Rubric criterion and capture protocol

- **`references/visual-qa-rubric.md` grew from eleven criteria to twelve.** Criterion 12, "Slide-mode integrity", is N/A unless the design record says `nav=slides`, with four metric groups: **(a) slide fit** (no overflow at any of the four QA viewports, the 1366x768 leg checked explicitly because that is where the root clamp pins; no inner scrollbar except a declared region), **(b) fragment integrity** (states visually distinct, end states match the state table, deep-linking resolves rather than half-building), **(c) ambient-loop discipline** (one system per slide, background amplitude, paused off-slide, absent under reduced motion, nothing data-bearing looped), and **(d) navigation chrome** (rail, counter, hit zones present, focus-visible, active state correct). Each group names its kind (STRUCTURAL / RENDER PROBE / AGENT-VISION) and severity, matching the existing criteria's shape.
- A fifth structural check sits deliberately **outside** the four groups and outside the gate: the design record's `nav` field must agree with the markup. The rubric states why in one sentence, because the reason is the whole point (below).
- The page-level pass bar names slide-mode integrity alongside the other N/A cases.
- **The settle-then-capture rule was extended** where it now bites hardest, carrying forward the two facts Phases 2-3 recorded in known-gaps: a mid-transition frame shows two slides painted together while the deck state is correct, and a frame taken during a timed build records a number that was never the answer. Both are phantom defects that would be filed on every slide-mode run.
- **SKILL.md Step 9** gained the slide-mode capture set, explicitly leaving scroll mode unchanged: the unit of evidence becomes the SLIDE (each slide at four viewports), the interaction states become each slide's first / mid / last fragment state plus lightbox and one chart interaction, the smoke-set becomes title + one mid-deck + one chart slide, and the mid-scroll capture is replaced by a mid-TRANSITION capture only where a transition is judged risky. Three stale "eleven criteria" references (one in the rubric, two in Step 9) were corrected in the same pass.

### 4.2 - The scorer's slide-mode family

`scripts/visual_qa_score.py` gained seven checks (1360 -> 1726 lines), each emitting its own criterion so a reader sees which one failed:

| Criterion | Checks |
|---|---|
| `slide-record` | **Ungated.** The design record's `nav` agrees with the markup |
| `slide-structure` | Stages exist (zero = named hard failure); no bare generic class can collide |
| `slide-fit` | Page scroll disabled; stages declare viewport-fitted sizing |
| `slide-fragments` | Per slide, indices positive, unique, contiguous from 1 |
| `slide-scroll-keyed` | No global scroll listener, IO-driven reveal, or `animation-timeline: scroll()` |
| `slide-ambient` | Every infinite animation sits under a reduced-motion guard that touches `animation` |
| `slide-chrome` | Rail, counter, and both hit zones present by documented class name |

**The one design decision worth recording** is why `slide-record` runs ungated. Every other check keys off `data-nav="slides"`, which makes that attribute a single point of failure: lose it and all six checks skip, and the page scores a confident green. That is fail-OPEN - strictly worse than having no checks, because it produces a passing verdict rather than an absent one. Comparing two independently-written sources of truth (the design record comment from intake, the body attribute from authoring) and failing on disagreement means the gate can now only be wrong in the direction that gets caught.

Two smaller calls, both about not crying wolf: an **element-scoped** scroll listener is allowed (a declared scrollable region legitimately scrolls inside its stage) while a `window` / `document` listener is flagged, because page-scroll-keyed animation is the actual defect; and an `IntersectionObserver` is flagged only when the same script also toggles classes, so lazy-loading is not mistaken for a scroll-triggered reveal. Both have explicit negative tests.

Scroll-mode pages emit exactly **one** `n/a` finding rather than six, and `_fails()` never contains a `slide-*` criterion for them - the Phase 1 backward-compatibility rule (absent `nav` means scroll) now enforced in code rather than only documented.

### 4.3 - Tests and the end-to-end dry run

`tests/skills/test_presentify_slide_mode_scorer.py`, 30 test functions / 38 cases: a clean slide-mode fixture that raises no slide finding, one seeded defect per check (including the malformed-fragment and zero-stages failure modes the plan named, both asserted to produce findings rather than exceptions), the negative cases that keep the checks trustworthy (element-scoped listener allowed, lazy-load IO allowed, two slides both numbering from 1 allowed), four scroll-mode tests proving skip-not-fail plus the legacy-page rule, and one AGGREGATE parametrized guard over nine malformed shapes (empty document, unclosed stage, nested stages, unterminated style and media blocks, empty and negative fragment values, a padded / uppercased nav value). That last one is deliberately one test over nine cases rather than nine near-identical tests, per the repo's test-retention policy: it asserts a single durable property - the scorer scores, never raises - because a scorer that crashes on a broken page is worse than one that misses a defect, the loop grading nothing at all and the failure reading as tooling breakage.

## 3. Verification

| Gate | Result |
|---|---|
| New scorer tests | 38 passed (30 test functions; the malformed-input guard is parametrized) |
| Existing scorer tests (`test_presentify_visual_qa.py`, `test_presentify_first_shot_hardening.py`) | 114 passed, file diffs empty - unchanged and green, as the plan requires |
| `tests/skills` (whole directory) | 734 passed |
| `catalog/hooks/tests/` (the `make test` half) | 1023 passed, 36 skipped, 0 failed |
| `tests/validators` + `workflows` + `plans` + root | 1091 passed, 10 skipped, 0 failed |
| `tests/installer` | 418 passed, 17 skipped, 0 failed |
| `tests/integrations` | 661 passed, 1 skipped, 0 failed (32m44s) |
| **Repo-level total** | **3,927 passed, 64 skipped, 0 failed** |
| `make validate` (both suites) | All green |
| Unicode safety on both edited markdown files | 0 repaired each |
| Python syntax | `ast.parse` clean |
| End-to-end dry run | Both real pages from Phases 2-3 scored; see below |
| CI | **No change needed, and verified rather than assumed**: the tests job already runs `pytest tests/skills` as a whole directory, so the new file is covered. The job's own comment warns that it enumerates test *directories* by name - a new directory would be invisible; a new file in a listed directory is not. |

**The end-to-end dry run is where the checks earned their keep.** Rather than only running fixtures, both pages authored in earlier phases were scored:

- The Phase 2 sample deck: `nav=slides`, 0 high-severity, page_pass true, six passes and one N/A (no ambient animation) - the contract's own reference implementation grades clean.
- The Phase 3 grammar demo: `slide-chrome` **FAILED**, naming the progress rail and both hit zones. This was a true finding, not a false positive: that demo was built to exercise the three animation classes and genuinely shipped only a counter. Adding the missing chrome flipped it to pass with 0 high-severity, verifying the check in **both** directions on real content rather than on a fixture written to satisfy it.

## 4. Troubleshooting

**An existing guard test failed, and it was right to.** `test_no_stale_criteria_count_survives` in `test_presentify_intake.py` hardcodes the rubric's criteria count and denies older spellings, precisely so a surface cannot silently claim a stale count while the grader skips new criteria. Growing the rubric to twelve broke it, along with a sibling asserting the `## The eleven criteria` heading. Both were updated as part of this change (the denylist is now a loop over eight / nine / ten / eleven, and the guard additionally asserts criterion 12 is present by name), which is the maintenance this guard is designed to force. Worth noting the alternative that was not taken: loosening the assertion to a regex would have made the test pass forever and stopped it catching anything.

No other failures. The new tests passed on their first run, which is only meaningful because each defect test asserts the criterion appears in the failure set - a check that had only ever been shown passing would be indistinguishable from a check that cannot fail.

**One process lesson, recorded because it cost real time.** `tests/integrations` takes about 33 minutes on this tree, and every run was piped through `tail`, which buffers until the process exits. The output file therefore sat at 0 bytes for the whole run, and three successive watch windows expired before it finished - which read as "the run died silently" when the run was simply slow. Two corrections for next time: redirect a long suite to a file (or `tee` it) so progress is observable rather than piping it, and size a watch window against a measured rate (a 120-second sample showed 34 of 662 tests, which projects the true duration in one step) rather than against a guess.

## 5. Files Changed

| File | Change |
|---|---|
| `catalog/.../scripts/visual_qa_score.py` | The seven-check slide-mode family, `nav_mode` / `record_nav_mode` / `slide_sections` helpers, wiring into `score_html`, and `nav` in the result payload |
| `catalog/.../references/visual-qa-rubric.md` | Criterion 12 with its four metric groups and the ungated record check; eleven -> twelve; pass-bar N/A case; the settle-then-capture rule extended to slide transitions and timed builds |
| `catalog/.../SKILL.md` | Step 9 slide-mode capture protocol; three stale criteria counts corrected |
| `tests/skills/test_presentify_slide_mode_scorer.py` | New: 28 tests |
| `tests/skills/test_presentify_intake.py` | The criteria-count guard updated to twelve and extended to assert criterion 12 |
| `docs/v3/v3.18/known-gaps.md`, `CHANGELOG.md`, `docs/todos.md` | Phase 4 status |
| this file | Session history |

No installer edit (the skill tree is copied recursively); no registry edit (frontmatter unchanged).

## 6. Next Steps

Phase 5 (`frontier` / `max`), the final phase: architecture refactor, known-gaps reconciliation, and CI/CD. It also triggers the release-readiness workflow, which hands the version bump, changelog finalization, tag, and push to `/update release`.
