# Session History - v3.16.5 Phase 3: the real render loop

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 3 of 7 (not the terminal phase) - the plan's designated enforcement keystone
**Branch**: `feat/v3.16.5-presentify-visual-overhaul`, worktree at `.claude/worktrees/v3.16.5-presentify`
**Model**: Opus 5 (strong tier). The plan recommends **frontier at MAX effort** for this phase, its highest recommendation. The delta was surfaced with the environment probe as context - Playwright already worked, so 3.1 and 3.4 were verification rather than exploration - and the maintainer chose to proceed on the session model.
**Prerequisites**: Phases 1 (`c45fb90b`) and 2 (`2b81bbc8`). Satisfied.
**Maintainer decision**: the CI shape was left open by sub-task 3.3 ("extend the workflow, or add a sibling job"); the maintainer chose a gated job inside the existing workflow.

## Sub-tasks completed

### 3.1 - `scripts/ensure_render_env.py`

Probes in order: an importable Playwright with a **launchable** chromium, then a local Chrome/Edge it can drive. Five states, five distinct exit codes (0 / 10 / 20 / 21 / 22), each with a note and the exact remedy commands. Never installs without `--install`; `--dry-run` prints the commands without running them. Windows-first browser detection. Wired into SKILL.md Step 9, the Bundled Resources list, the rubric's degradation contract, and the command doc's `--qa-depth` entry.

It launches rather than checking for a cache directory, because a cache can exist while the build inside it is unusable - and that failure would otherwise surface inside the QA loop, which is exactly where it degrades quietly.

### 3.2 - Step 9 is screenshot-first by default

Three viewports (1920x1080, 1366x768, 390x844) plus interaction states including the pinned-graphic mid-scroll state, per iteration. All eight rubric criteria graded per segment against both the rubric and the source. Findings-to-fix-to-re-render is mandatory until no high-severity finding remains or the `--qa-depth` cap hits. The evidence trail goes in the design-record comment. Three binary Verification items replace what was prose, and three rationalization rows were added or strengthened.

The 1366px capture is not decoration: a `clamp()` is usually still pinned at its MINIMUM at that width, so the readability floors bite there and not at 1920px.

### 3.3 - The gated CI render job

A `render` job on merges to `main`/`develop` plus a weekly cron; PRs keep the fast browser-free job, which now opts out of the cron so it is not double-billed. Installs chromium with a cache keyed on the resolved Playwright version, gates on the environment probe, runs the suite with `NEXUS_REQUIRE_RENDER=1`, and scores the calibration fixture. A `render_gate` fixture in `tests/conftest.py` converts the browser-dependent skips into failures under that variable.

### 3.4 - Dogfood, and what it found

Rendered the fixture at all three viewports and measured overflow, band width, smallest rendered text by role, pinned-graphic fit, and editorial dead space. Then seeded each defect class back in and confirmed detection.

### 3.5 - Stabilization

Full lint, test, and validator sweep; the gate verified in all three directions.

## What the render found that eleven deterministic checks had passed

This is the phase's real output, and it is the argument for its own existence.

1. **`.brand` at 12.48px** - a checker bug. `_font_role` matched `nav` anywhere in the selector, so `#nav .brand`, a static brand label, was graded against the 12px interactive floor instead of the 13px secondary one. It now reads only the LAST compound of a selector and distinguishes an interactive ELEMENT from a class merely named `label`.
2. **`code` at 12.22-12.81px** - a deliberate blind spot made visible. `font-size:.92em` is relative to the inherited size, which the checker explicitly skips because it cannot resolve it. Fixed with `max(.92em, 0.8125rem)`, and `min()`/`max()` was taught to the length resolver so the flooring construction the contract now recommends is itself verifiable.
3. **`.cmd-bar .label` at 12.07px** - my own Phase 1 mapping error, mapping a static caption onto the interactive type step because its class is named `label`.
4. **An inline `style="font-size:.72rem"` at 11.52px on every viewport** - invisible to a CSS-rule parser. Inline styles are now graded as pseudo-rules under the secondary floor, taking the checked-size count from 40 to 41.
5. **A 390px horizontal overflow that Phase 2 introduced.** The document scrolled to 512px and the pinned SVG looked like the culprit at 492px wide. It was a symptom. The mobile media queries override `grid-template-columns` to `1fr`, dropping the `minmax(0, ...)` the desktop rules use; `1fr` means `minmax(auto, 1fr)`, whose `auto` minimum is the content's min-content, so a wide `<pre>` stretched the track and the SVG merely filled it. Fixed in all five single-column overrides rather than by capping the SVG.

Two of the five were bugs in the checker, not in the page. That is the part worth remembering: a parser and a renderer answer different questions, and shipping only the parser means shipping the difference.

## The environment finding

Playwright and a cached chromium were **already installed** on this host, yet the three browser-dependent checks skipped across every Phase 1 and Phase 2 run - and then passed consistently (21 passed, ~5s, twice) after a single warm-up launch. The silent fallback was not protecting anyone from a missing dependency; it was hiding a working one. That is the whole case for an explicit probe, and it is recorded in the v3.15 MT-1 closure note.

## Troubleshooting loop

Three iterations, three distinct classifications.

1. **TEST** - `test_calibration_fixture_has_no_stale_palette_literals` failed because the superseded hexes appear legitimately inside Phase 1's explanatory comment, which spans two lines, so a per-line exclusion missed the continuation. Fixed by stripping HTML and CSS comments before scanning: a live value can only be in markup, CSS, or script, never in a comment.
2. **IMPL** - the inline-style check silently matched nothing. A heredoc had delivered a single backslash to Python, which read `'\b'` as a backspace character (0x08) and compiled a regex that could never match - invisible in the file and silent at runtime. The tell was that the checked-size count stayed at exactly 40 after adding a check that should have raised it. Fixed by writing the constant from a file rather than a heredoc, and the same mechanism was then used for every subsequent multi-line edit.
3. **ENV** - `ruff` flagged three `BLE001` blind-exception catches in the new script, and CI lints that directory. The catches are deliberate (the probe must classify, never crash), so they carry `# noqa: BLE001 - <reason>` following the convention already used four times in `extract_content.py`.

## Verification evidence

| Check | Command | Result |
|---|---|---|
| Visual-QA suite | `pytest tests/skills/test_presentify_visual_qa.py -q` | 59 passed (from 42) |
| Full presentify surface | `pytest tests/skills/ -q` | **561 passed, 0 skipped** (was 541 passed / 3 skipped) |
| Coverage | `pytest --cov=.../scripts` | `visual_qa_score.py` 93% at 531 statements; `ensure_render_env.py` 83% |
| Lint (CI's exact target) | `ruff check --ignore RUF100 .../scripts/` | All checks passed |
| Validators | the ten `make validate` guards, individually | all OK, including `validate_workflow_security.py` on the modified workflow |
| Workflow YAML | `yaml.safe_load` | valid; jobs `verify` + `render`; triggers push / schedule / pull_request |
| Scorer on the fixture | `visual_qa_score.py nexus-hub-unit-test-workflow.html` | PASS, 0 high-severity across 12 criteria |
| Real render, 3 viewports | ad-hoc Playwright harness | no horizontal overflow anywhere; secondary text >= 13px, interactive >= 12px at all three; pinned graphic fits its slot at all three |
| Seeded-regression proof | 8 mutations over the fixture | all 8 detected, each blocking the page |
| Gate direction A | browser + `NEXUS_REQUIRE_RENDER=1` | 21 passed |
| Gate direction B | playwright shimmed to ImportError + flag | 2 FAILED loudly (not skipped) |
| Gate direction C | no browser, no flag | 2 skipped (local behavior preserved) |
| Probe on a browserless host | `find_local_browser` patched to None | NEED_ALL / exit 22, remedy named, degradation disclosed |

## Deviations from the plan

- **The seeded-regression bar was raised from one case to eight.** The plan named the loop-back arrow. A gate that catches one seeded defect and misses the others is not proven, so every contract family is seeded, and the durable half was promoted into a parametrized mutation test rather than left as a scratch script.
- **A calibration-fixture regression test and a stale-palette test were added**, which the plan assigned to Phase 7 via MT-1. They cost two tests and narrow MT-1 to its LOCATION half only; sub-task 3.3's "against the repo's presentify fixtures" covers them.
- **BG-2's fixes touch Phase 1's typography domain** (`.brand`, `code`, `.cmd-bar .label`) and Phase 2's grid overrides. Justified: they are the defects this phase's render exists to find, and two are bugs in Phase 1's own checker.
- **An invented `actions/cache` SHA was typed and then corrected.** The repo pins that action nowhere else, so there was no local reference; the real SHA was resolved through the GitHub API. Recorded because the repo has a standing do-not-invent rule earned from a fabricated config file, and the near-miss is the point.

## Known gaps

One new open (WN-3, `em`-relative sizes render-verified only). Three closed: BG-2, **v3.15 MT-1**, and Phase 1's NI-2 / WN-1 plus Phase 2's WN-2 / NI-3 are now answered by the render rather than carried forward. v3.15 MT-2 stays open by design with a status note appended so no reader assumes this phase closed it. Zero release blockers.

## Next steps

1. **Phase 4 - intake redesign** (imagery question + content-aware color schemes). Prerequisite-free and parallel-safe with 1-3; the plan places it after 3 so its intake copy can reference the QA loop honestly, which it now can.
2. **Phase 5** hosts the imagery placement pass inside the loop this phase built, and closes the remaining half of v3.15 MT-2.
3. **Phase 7** still owns MT-1's location half.
