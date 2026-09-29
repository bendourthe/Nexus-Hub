# v4.9.2 real-deck scorer follow-up

This record closes Task 6 Step 1's missing execution evidence for the archived [v4.9.2 plan](../../plans/v4.9.2-slide-build-contract-and-projection-floors.md). It does not certify the deck's slide-specific rules or rendered type floor.

## Artifact and method

On 2026-09-27, the `rd-data-dev` repository at `C:/Users/BEDOURTHE/Documents/Supira/software/algorithms` was clean. The pre-rule handbook was read from its historical Git blob, `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html`, without modifying that repository. The blob is 773,172 bytes and has SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`. The Nexus-Hub scorer was the `visual_qa_score.py` at `accfbd92` on `develop`; the blob was decoded as UTF-8 and passed to `score_html` in memory. The plan's illustrative `--slide-mode` CLI option is not supported by the current scorer and was not invoked.

## Observed output

| Probe | Result |
|---|---|
| Historical deck | `nav: scroll`; `page_pass: false`; three high-severity failures |
| `presentation-declared` | `fail`, high severity; the deck-like content was detected despite no slide declaration |
| `slide-mode` | `n/a`; the slide-specific checks were not run on this undeclared deck |
| Existing compliant two-slide fixture | `page_pass: true` and no failing findings from `score_html(_CLEAN_SLIDES)` |
| Focused test suite | `118 passed in 180.76s` for `test_presentify_slide_mode_scorer.py` and `test_presentify_measure_handbook.py` |
| Isolated worktree baseline | Fast profile: `17 passed, 0 failed, 0 skipped, 0 advisory` at `accfbd92` |

The real artifact proves the declaration guard rejects this pre-rule deck. The clean fixture proves the structural scorer accepts at least one declared two-slide page. Neither result shows the historical deck exercising `slide-fragments`, `slide-type-variety`, `slide-figure-scaled`, or the rendered stage-type floor. The floor has separate positive and negative fixture tests in the earlier [stage-floor evidence](../../../../../releases/v4/v4.9/development/v4.9.2-stage-floor-evidence.md); no real-deck render probe was run here. This residual real-artifact coverage is tracked as [v4.9 MT-3](../../known-gaps.md).
