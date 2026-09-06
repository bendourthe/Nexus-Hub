---
name: visual-regression-testing
description: Catch unintended UI changes by capturing baseline screenshots, diffing current renders against them, and gating on the difference with an agent visual review. Make sure to use this skill whenever the user says "visual regression", "screenshot tests", "did the UI change", "pixel diff", "catch unintended UI changes", "visual review of the render", "baseline screenshots", or wants to detect visual drift in a rendered UI over time rather than testing behavior. SKIP, do NOT use for, functional or end-to-end behavior testing (use e2e-testing-automation), one-off demo or PR screenshot capture (use demo-capture), or non-visual regressions (use commit-sweep / regression-root-cause-analyzer).
summary_l0: "Baseline screenshots, perceptual diff, and an agent visual-review gate for UI drift"
overview_l1: "This skill catches unintended UI changes by layering a regression discipline on top of screenshot capture: capture BASELINE screenshots of key views at defined viewports, store them (git-lfs when available, otherwise attach baseline + current + diff to the PR), diff current renders against the baseline with a perceptual metric, and GATE on the difference - below threshold passes silently, above threshold triggers an agent visual review that reads the before / after / diff images and decides whether the change is intended, and only a reviewed-and-approved change re-baselines. The bundled scripts/perceptual_diff.py computes the diff and exits non-zero on regression (a size change is treated as a regression); scripts/capture_screenshot.py is a best-effort headless-browser capture that degrades gracefully when no browser is present. It builds on browser-testing-with-devtools and demo-capture (which capture) and adds the missing baseline + diff + review gate. Trigger phrases: visual regression, screenshot tests, did the UI change, pixel diff, catch unintended UI changes."
---

# Visual Regression Testing

Catch UI changes you did not intend. `demo-capture` and `browser-testing-with-devtools` already take screenshots; this skill adds the regression loop on top - a committed baseline, a perceptual diff against it, and an agent visual-review gate - so a layout that shifted or a component that broke is caught before it ships.

## When to Use This Skill

- A rendered UI (web page, component, generated HTML artifact) should not change appearance without someone noticing.
- You want a CI or pre-merge gate that flags visual drift between a baseline and the current render.
- After a UI change, to review the before/after and lock in a new baseline deliberately.

**Trigger phrases**: "visual regression", "screenshot tests", "did the UI change", "pixel diff", "catch unintended UI changes", "visual review of the render", "baseline screenshots".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Test functional behavior / user flows | `e2e-testing-automation` |
| Capture a one-off demo or PR screenshot | `demo-capture` |
| Debug behavior in the browser (network, console) | `browser-testing-with-devtools` |
| Catch non-visual regressions | `commit-sweep` / `regression-root-cause-analyzer` |

## Instructions

1. **Choose the views and viewports.** Pick the key screens / components and the widths that matter (for example desktop 1400px and mobile 480px). Gating every pixel of every page is noisy; gate the views whose appearance is load-bearing.
2. **Capture a baseline and store it.** Render each view and screenshot it. When git-lfs is set up, commit the baselines under lfs; otherwise use the fallback the source post itself allows - attach baseline + current + diff images to the PR rather than committing binaries. The bundled `scripts/capture_screenshot.py` captures via a headless Chromium-family browser and degrades with a clear message when none is present (fall back to your CI's browser or a manual capture).
3. **Diff current against the baseline.** On each run, capture the current render and compare:

    ```bash
    python scripts/perceptual_diff.py baseline.png current.png --diff out-diff.png --threshold 0.01
    ```

    The script exits non-zero when the mean normalized difference exceeds the threshold, or when the two images differ in size (a dimension change is a regression). It writes a diff image for review.
4. **Gate on the diff, with an agent visual review above threshold.** Below threshold: pass silently. Above threshold: do NOT auto-fail-forever - the agent READS the baseline, current, and diff images and judges whether the change is intended. An intended change is approved and re-baselined; an unintended change fails the gate with the diff attached.
5. **Re-baseline deliberately.** Only an approved, intended visual change updates the baseline, committed in the same reviewed change. Never re-baseline just to turn a red gate green.

The deterministic diff lives in the bundled `scripts/perceptual_diff.py` (Pillow lazy-imported, zero-network); the capture helper is `scripts/capture_screenshot.py`. The skill body stays thin and the scripts run on demand without being read into context.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We screenshot in CI already." | Capturing is not gating. Without a committed baseline and a diff-with-threshold, a broken layout just produces a screenshot no one compares. |
| "A pixel diff will be too flaky to be useful." | A raw exact-pixel compare is flaky; a mean-normalized perceptual metric with a small threshold tolerates anti-aliasing and font jitter while still catching real changes. Tune the threshold, do not skip the gate. |
| "The diff is over threshold, I will just bump the baseline." | Re-baselining to silence a red gate hides the regression. Re-baseline only after reviewing the before/after and confirming the change is intended. |
| "I will resize the images so they compare." | A size change is a real layout regression. Resizing to force a comparison masks exactly the kind of drift this gate exists to catch, which is why the diff fails on a size mismatch. |
| "git-lfs is not set up, so we cannot do visual regression." | The PR-attach fallback (baseline + current + diff in the PR) needs no lfs and still gives a reviewer the evidence to approve or reject the change. |

## Verification

- [ ] A baseline image exists for each gated view (committed via lfs or attached to the PR).
- [ ] `perceptual_diff.py` exits non-zero on a seeded over-threshold change and on a size mismatch, and zero within threshold (proven, not assumed).
- [ ] Above-threshold diffs trigger an agent visual review of the before / after / diff, not a silent pass or a blind re-baseline.
- [ ] Re-baselining happens only for a reviewed, intended visual change.
- [ ] The diff image is produced and available to the reviewer (committed or attached to the PR).

## Related Skills

- [[demo-capture]] -- captures screenshots / GIFs for PR evidence; this skill adds the baseline + diff + review gate on top.
- [[browser-testing-with-devtools]] -- drives the browser to render and capture; the capture side of this discipline.
- [[e2e-testing-automation]] -- tests behavior and user flows; visual regression tests appearance, and the two are complementary.
- [[frontend-ui-engineering]] -- builds the UI whose appearance this gate defends.

---

**Version**: 1.0.0
**Last Updated**: July 2026
