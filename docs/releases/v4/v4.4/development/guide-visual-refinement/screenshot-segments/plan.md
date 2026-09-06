# Screenshot-selected Home refinements

Preserve the text, examples, section order, approved platform marks, and existing controls. Redraw the safety boundary and its three action paths. Enlarge the platform labels, configuration paths, handoff steps, and comparison text, and separate these three groups with the existing spacing scale.

1. Capture both existing sections before editing.
2. Implement the two local compositions and purposeful, finite animations; keep every explanation visible and honor reduced motion and offscreen pause.
3. Inspect desktop/mobile captures in both themes, check breakpoint seams and text containment, verify content parity, and run the affected guide tests before one local commit.

## Implemented

The safety section puts its explanations above a two-column graphic: the model and permission boundary inside the Nexus Hub shield on the left, and three complete action paths on the right. Each action retains its platform decision, named hook decision, and outcome. All examples remain visible while short progress strokes illustrate the checks. The sequence runs once instead of repeatedly blanking its content.

The platform section uses a connected distribution diagram, larger approved platform marks, and a document-transfer motif for the mid-task handoff. The source, platform destinations, handoff, and comparison table have distinct spacing. Handoff steps stack on small screens; the full comparison table and all command examples remain available.

## Verification

- Content: normalized text, all 27 sections in order, and all original IDs match v4.4.5. The added nonbreaking span changes only the wrap opportunity in `mid-task`. See [content-parity.json](content-parity.json).
- Layout: 36 cases across 320, 420, 700, 720, 721, 999, 1000, 1024, and 1440 pixels, in light and dark themes. No horizontal viewport overflow, clipped text, or page errors. Screenshots include section and diagram detail views at 420 and 1440 pixels. See [layout-checks.json](layout-checks.json).
- Readability: platform names increase from 13.5px to 18px, handoff commands from 13px to 17px, and handoff platform labels from 11px to 15px. Table body text is 16px with more row padding. Measured contrast is at least 6.44:1 in dark mode and 5.23:1 in light mode. See [readability-checks.json](readability-checks.json).
- Motion: all three action examples remain visible at sampled start, intermediate, and final frames; all six progress strokes complete. New animation is finite, pauses offscreen and on the visibility event, and is disabled under reduced motion. The hidden-document event is simulated in headless Chromium; native OS occlusion is not claimed. See [animation-samples.json](animation-samples.json) and the browser lifecycle regression tests.
- Regression verification: the broad guide run completed with 342 passed, one skipped, and one header-size mismatch. After restoring the 26px comparison grade and widening its column, all 49 final focused checks passed, including that failure, heading/layout contracts, the byte limit, and motion lifecycle. The complete suite was not repeated after this last CSS correction. See [broad run](guide-suite-before-heading-fix.txt) and [final focused run](final-focused-tests.txt).

## Corrections during verification

The first browser pass found narrow handoff commands that needed a single-column layout. The visual pass also caught a split `mid-task` and a wrapping comparison header; both were corrected. The full suite then exposed a first-800-characters reduced-motion assertion and an exact observer selector string. Those checks now verify the actual reveal rule across reduced-motion blocks and the required observer roots. The new behavior tests independently exercise visibility and reduced motion.

The final screenshot review retains the original 26px desktop comparison-header grade, with a wider first column to prevent unnecessary wrapping.

The original 400,000-byte guide gate remains intact. Only the new CSS was compacted, retaining one rule per line, and unused layout/loop settings were removed. The final normalized HTML size is 399,952 bytes. No teaching content or approved platform artwork was removed to meet the limit.

## Scope limits

No publication, native 200% browser-zoom audit, or repository-wide CI run is included. The changes are confined to the screenshot-selected Home sections and their shared visibility handling. The previous Foundations refinement is retained.
