# Session History - v3.16.5 Phase 1: fluid layout and readability contract

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 1 of 7 (not the terminal phase)
**Branch**: `feat/v3.16.5-presentify-visual-overhaul`, in an isolated git worktree at `.claude/worktrees/v3.16.5-presentify`
**Model**: Opus 5 (strong tier). The plan recommends the frontier tier at high effort; the maintainer chose to proceed on the session model after the delta was surfaced, on the basis that contract authoring plus stdlib parsing sits inside Opus 5's range and the plan's frontier call was about downstream propagation risk rather than raw difficulty.

## Why an isolated worktree

A second session was concurrently fixing the GitHub Usage Monitor extension for v3.16.4 in the primary working directory, with 24 modified files on `develop`. A branch checkout is a property of the working directory rather than of a session, so creating a feature branch there would have moved that session's HEAD mid-task. A `git worktree` gives a second directory its own HEAD against one shared object database, which isolates both the checkout and the commit history - so cutting v3.16.4 cannot pull partial v3.16.5 work into that release. `.claude/` is gitignored, so the worktree does not appear in the other session's `git status`.

One consequence worth recording: the calibration fixture was untracked when the worktree was created, so it existed only in the primary directory and had to be copied in by hand. This phase commits it (see MT-1), which removes the copy step for later phases but leaves an untracked copy behind in the primary checkout that will block a `develop` update of that path until it is moved or removed.

## Sub-tasks completed

### 1.1 - Author `references/responsive-typography.md`

Six rules, each with a correct/incorrect CSS pair and an observable criterion: fluid macro spacing (the 24px macro/micro cut), wrapping that serves the viewport, a type scale declared once as custom properties, hard rendered-size floors (16 / 13 / 12px) checked at both the clamp minimum and 1920px, two-axis emphasis tokens, and computed contrast floors. Referenced twice from `SKILL.md` (a new Step 6 bullet and the Bundled Resources list), which satisfies the orphan-bundle audit.

Two forward references to Phase 2's `svg-diagram-quality.md` were written and then removed, because Phase 1 has to pass its own stability gate standalone and a reference file that does not exist yet is a dangling link. Phase 2 adds the reciprocal links when it creates that file.

### 1.2 - Extend `visual_qa_score.py` and the rubric

Four new criteria (`fluid-spacing`, `font-floor`, `emphasis-token`, `contrast`), a leaf-rule CSS parser, WCAG luminance math, `var()` resolution, `clamp()` minimum extraction, and additive-term support in the length resolver. Still stdlib-only. Rubric extended from five criteria to seven with the paired agent-vision judgments.

### 1.3 - Fix the calibration fixture

A nine-step fluid type scale on `:root`; 19 font-size declarations retargeted onto step tokens (17 that violated a floor, plus the footer and margin-note bodies lifted for the specific readability complaints R3 and R4); two fixed macro spacings made fluid; three palette values re-picked to clear AA; an emphasis-token treatment on the page-wide `code` rule; and a note rail that grows with the viewport. From 2 high-severity findings to 0.

### 1.4 - Testing and stabilization

Three rationalization rows and one Verification item added to `SKILL.md`. Full sweep run.

## What the phase found that the plan did not anticipate

Three of the four most useful findings were in the checker rather than in the fixture, and none would have surfaced from reading the plan alone.

1. **The readability defect had a single mechanical cause.** The fixture's fluid `clamp()` was on `body` while every child was sized in `rem`, which resolves against the ROOT element. `html` kept the 16px browser default, so the scale propagated to exactly one rule and `footer b{font-size:.7rem}` was a flat 11.2px at every viewport. This is why the contract mandates declaring the scale as `:root` custom properties rather than merely "use clamp()".
2. **The `font-floor` check initially skipped every `var()` value**, so tokenizing the fixture dropped its checked font count from 40 to 17. A linter that verifies the non-compliant form more thoroughly than the compliant one rewards the wrong behavior. Fixed by resolving `var()` against declared custom properties; a malformed `--step--2: 0.6rem` is now caught and the message names the declared token, not just the resolved pixels.
3. **The `emphasis-token` check initially passed the fixture for the wrong reason.** `footer code` declared a color while the page-wide `code` rule did not - which is precisely the shipped defect the check exists to catch. It now grades the unqualified base rule, falling back to scoped rules only when no base rule exists.
4. **Grading contrast needed a severity policy, not just a threshold.** Custom properties declare which colors exist, not which pairs co-occur on screen, so the fixture's 4 inks x 3 surfaces produce 12 ratios for pairs that are not all rendered together. Failing all of them at HIGH produces a gate people bypass.

## Verification evidence

| Check | Command | Result |
|---|---|---|
| Presentify visual-QA suite | `python -m pytest tests/skills/test_presentify_visual_qa.py -q` | 29 passed (up from 12) |
| Full presentify surface | `python -m pytest tests/skills/ -q` | 528 passed, 3 skipped |
| Coverage of the changed module | `pytest --cov=.../scripts` | `visual_qa_score.py` 92% (gate 80%) |
| Lint | `python -m ruff check <scorer> <tests>` | All checks passed |
| Catalog + bundle validation | the ten `make validate` guards, run individually | all OK, including the orphan-bundle audit and the skill quality pass (271 skills, 0 errors) |
| Scorer against the fixture | `python scripts/visual_qa_score.py nexus-hub-unit-test-workflow.html` | PASS, 0 high-severity, 40 font sizes checked |

`make` is absent on this host (the long-standing environmental WN-1), so each validator was invoked directly rather than through the Makefile target.

## Deviations from the plan

- **No `# DEVIATION:` markers were needed in code.** The two substantive departures are additive scope the plan's prompts implied but did not name: `var()` resolution (without which sub-task 1.2's own font-floor check would not cover the tokenized page sub-task 1.3 produces) and the base-rule scoping of the emphasis-token check (without which the check does not catch the defect the plan cites as its motivation).
- **Sub-task 1.3's editorial reflow was implemented by widening the note rail, not by multi-columning the prose.** This satisfies the plan's literal instruction (prose widens toward 85ch, the grid reflows) and cuts the dead corridor from ~690px to ~470px at 1920px, inside the rubric's one-third-of-band criterion. Full closure would need CSS multi-column, which is a larger design change than the plan scopes and which Phase 3 can judge from real screenshots.
- **`.nav a` was left at 12.16px.** It clears its 12px interactive floor, and its selector spelling did not match the retargeting map. Not a violation, recorded here for completeness rather than as a gap.

## Known gaps appended

Three open, one accepted-and-documented, none a release blocker. Recorded as v3.16.5 MT-1 / NI-2 / WN-1 / DF-1 in [docs/releases/v3/v3.16/known-gaps.md](../../known-gaps.md). MT-1 (fixture unhomed and unguarded; committed at the repo root in this phase so the fixes are not at risk) routes to Phase 7; NI-2 (contract rules 2-3 have no deterministic check) and WN-1 (status colors outside the automated contrast set) both route to Phase 3, which is the phase that acquires the rendered screenshots those judgments require.

## Next steps

1. **Phase 2 - SVG diagram-quality contract.** Creates `references/svg-diagram-quality.md` and adds the reciprocal cross-links Phase 1 deliberately omitted. Depends on the scorer plumbing this phase added, which is in place: `css_rules`, the finding schema, and the severity conventions all generalize to the SVG checks.
2. **Phase 3** closes NI-2 and WN-1 from real screenshots and re-verifies this phase's fixture fixes against an actual render, which is the first time the Phase 1 contract is tested by something other than a parser.
3. **Phase 7** homes the calibration fixture and closes MT-1.
