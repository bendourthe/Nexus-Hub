# v4.4.5 targeted visual refinement

## Scope and direction

Preserve every existing section, heading, explanation, example, navigation destination, and Training scene from `bdd57cee4eb776304a09e862c1d956534db59e1e`. Retain the existing typography, constellation theme, colors, and page composition. Refine the token illustration and harness flow in place, and remove animation work when the Training game is idle or outside the viewport. The user's preservation requirement takes precedence over generic redesign prescriptions.

## Verification sequence

1. Capture the existing token illustration and harness flow at 1440 and 420 pixels in both themes. Record idle game frame callbacks on Foundations.
2. Refine each illustration independently; inspect matching after screenshots for clarity, wrapping, spacing, and consistency. Preserve full-opacity teaching text while using motion to emphasize relationships.
3. Check the original section order, text, and Training data against v4.4.5. Exercise game start, pause, resume, reset, offscreen, tab switching, and reduced motion. Check responsive widths including 320, 420, 700, 701, 768, 1024, and 1440 pixels, then run the guide regression suite.

One local corrective commit follows verification. CI configuration and publication are outside this visual refinement.

## Results

The token examples now use matching frames and the prompt uses its intended 19px typography. A dashed grid maps the source picture to the nine output patches; a single 4.8-second outline highlight emphasizes the split and is disabled under reduced motion. Five decorative harness symbols distinguish the request, model, platform, Nexus Hub, and result. Harness explanations stay at full opacity throughout sequence resets.

The Training canvas now schedules frames only while the game is running. Idle, paused, offscreen, and reset states stop scheduling; existing start/resume actions restart it. The four baseline Foundations samples recorded 61 game callbacks per second; the matching four after samples recorded zero. This isolates the unnecessary game work and is not a claim about whole-page frame rate.

- Content preservation: all 1,150 text fragments, 27 sections in order, 110 original IDs, and 38 link destinations match v4.4.5. Training JSON is unchanged. See [content-preservation.json](content-preservation.json).
- Responsive checks: 56 cases across 320, 420, 700, 701, 768, 1024, and 1440 pixels, in both themes, found no page errors, horizontal viewport overflow, or clipped text in the altered figures. See [responsive-checks.json](responsive-checks.json).
- Visual review: `view-*` screenshots show settled viewport captures at 1440x900 and 420x900. The long mobile harness headings wrap inside their label column; their symbols no longer occupy orphan rows. The token image remains paired with its explanation. Raw `before-*` element captures retain the original animated state and sticky-header behavior.
- Accessibility: the measured text pairs in the altered figures have minimum contrast of 5.67:1 in dark mode and 5.23:1 in light mode. Doubling the tested text size at 720 pixels produces no clipping. Reduced-motion checks disable the new token animation and keep the harness text visible. See [accessibility-checks.json](accessibility-checks.json).
- Regression suite: `NEXUS_REQUIRE_RENDER=1 python -m pytest tests/guides -q --tb=short` passed: 342 passed, one optional skip, 349.28 seconds. The new lifecycle module also passed after its browser fixture was aligned with the repository render gate (two tests, 3.59 seconds). See [guide-tests.txt](guide-tests.txt).

## Limits and reviewed alternatives

Native browser 200% zoom, OS occlusion, and a whole-site accessibility audit were not performed. The double-text-size check is recorded separately and is not native zoom evidence. Publication and repository-wide CI were not run for this scoped guide correction.

A broader Home layout change was considered and left out because the user's correction makes the v4.4.5 composition the baseline. Removing original explanations or changing the teaching sequence was rejected by the preservation contract. The original Training content and controls remain in place; its background frame scheduling was the confirmed performance defect.

## Screenshot-selected Home follow-up

The two Home sections selected by the user were subsequently rebuilt with larger text, clearer safety checks, a connected platform distribution diagram, and a roomier handoff. [Follow-up verification and screenshots](screenshot-segments/plan.md) record the final scope and tests.
