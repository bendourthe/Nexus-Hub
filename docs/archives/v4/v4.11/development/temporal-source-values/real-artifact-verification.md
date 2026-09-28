# Real-Artifact Temporal Source-Value Verification

This frozen record qualifies the DOM-text temporal guard on the tracked five-slide presentation fixture. It closes v4.11 MT-5 only within that guard's declared measurement envelope; it does not accept the historical first build or certify canvas-painted and unmapped numbers.

## Independent source mapping

The source is `tests/fixtures/interactive-handbooks-qualification/presentation/inputs/service-review.pptx`, SHA-256 `994b418c0653c428182bb2bcc11707d04e8d4b03ec72356a45531a0748fd1843`. Slide 4's native chart contains 10, 15 and 20; the slide text says `East 10; Central 15; West 20. Total 45 visits.`. The three chart values sum to 45. The [inventory](real-artifact-inventory.json) maps the rendered total and sentence on slide `completed-visits`. Its total expectation, `45completed visits`, is the DOM's exact text-node concatenation of the source-backed 45 and source title `Completed visits`; the missing space is a serialization detail, not a different source value. Selectors identify only the two visible source-backed DOM strings, not SVG bar geometry, tooltips or generated axis ticks.

The measured artifact is the unchanged `docs/releases/v4/v4.11/development/interactive-handbooks/phase-6-native-attempts/presentation-final/first-build.html`, SHA-256 `9684417c7371db0c3968fab4e4023b2017c19e9c94ec6b6566f3a1a2801b880b`. It remains a historical non-pass.

## Observed result

The real browser walk measured 200 states over 10 viewports from 390x844 through 2560x1300. The source-value sub-verdict passed: two visible mapped strings per viewport, 20 observations, zero wrong values and zero source-value findings. The overall result failed with 412 separate errors, including oversized service-path annotations and an unassigned type role on the total. No overall pass or visual acceptance is claimed.

The full `tests/skills/test_presentify_measure_handbook.py` module passed 59 tests. Six focused source-value cases passed: static value, a brief wrong value between settled checkpoints, style-only reveal of a wrong value, absent mapping, missing mapped selector and an unrelated layout failure with a passing source-value sub-verdict. They provide the negative controls the unchanged real artifact cannot provide on its own.

The current repository has two handbooks, `overview` and `distribution`. Neither source Markdown file contains a numeric source fact, so their empty temporal mapping and `unchecked` result remain truthful. A future document with source-backed DOM numbers must declare independent mappings before claiming temporal coverage. Canvas pixels, SVG shape magnitudes and unmapped values remain outside this guard; figure worksheets and attestation own source computation and chart fidelity.
