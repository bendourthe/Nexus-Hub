# Guide design review - September 4, 2026

## Recommendation

Keep Home's identity and palette, simplify its benefit story, rebuild Foundations around seven illustrated lessons, and make Training demonstrate an honest request-to-evidence workflow. Fix invisible instructional content before adding animation. Use one everyday task throughout Foundations, then connect it to the existing coding exercise.

This is a review and implementation plan, not an implementation. The companion [v4.4.6 plan](../../plans/v4.4.6-guide-learning-experience.md) contains the proposed changes and acceptance gates.

## Evidence and limitations

Reviewed local branch `feat/v4.4.3-guide-illustration-rebuild`, HEAD `bdd57cee`, following the locally completed, unpublished v4.4.5 plan. Canonical artifact: `guides/website/nexus-hub-guide.html`, 396,424 bytes, SHA-256 `68f017bcac2a7c58278ce3ad7642f5860279784707e3ef4ee5fef15c8d39ec7d`. Prior plans and the guide README were read as background; their past green results were not treated as current visual approval. The progress dashboard still described older work.

The interactive computer-use browser was unavailable. The existing Playwright renderer produced 12 current full-page screenshots: Home, Foundations, Training; light and dark; 420px and 1440px. A separate browser probe visited the six Foundations sections at 1440x900 in both themes and 420x900 in light mode, captured viewport images, and measured DOM geometry and browser performance counters. Selected images and the probe outputs are retained under [review](review/). No HTML, Training data, installer, or runtime configuration was changed.

The full-page renderer forces `.reveal.in` but does not scroll through every sequencer. Its blank animated areas are therefore not sufficient evidence of a runtime defect. The separate in-view probe does not force reveal or sequence classes. It confirmed the mobile harness sequence remained at step 0, stopped, with all five steps hidden after an eight-second in-view wait. A second passive IntersectionObserver probe reported `isIntersecting: false` despite the root's bounding box spanning the viewport. This confirms the visibility failure; its precise cause is still open. The root is 2,547px tall at 420px, making the configured 40% threshold unreachable in a 900px viewport, but the production callback tests `isIntersecting`, not the ratio. Threshold, clipping, ancestor layout, and observer state must be investigated together; the threshold alone is not a proven root cause.

The probe found no page-level horizontal overflow or JavaScript page errors in its three cases. It did not measure a real user's input latency, GPU cost, frame drops, or a full accessibility conformance result. The user-reported lag is not yet quantified. Measured cumulative script duration was approximately 0.21-0.23 seconds over the probe sequence; dark-mode task duration was higher than light-mode, but this uncontrolled sample does not establish causation. Phase 1 requires repeatable traces and Phase 2 requires before/after evidence.

## Priority findings

| Priority | Finding and evidence | Proposed change | Owning phase |
|---|---|---|---|
| High | Essential harness content can remain invisible. Mobile in-view probe: five hidden steps, stopped at step 0; screenshot shows arrows through empty space. Desktop looping also leaves some teaching steps hidden while later material is visible. | Make the complete diagram readable at rest. Animate emphasis, not availability. Reproduce route, viewport, observer, and reduced-motion transitions. | 2 |
| High | Foundations is disproportionate: 8,648px high at 1440px and 15,292px at 420px. Models alone is 2,301px / 3,961px; Platforms 1,758px / 3,560px; Harnesses 1,750px / 3,048px in light mode. It starts with tokens, reaches models fourth, and has no dedicated graph lesson. | Teach model first, then tokens, prompt, context, harness, loop, graph. Replace the eight-stage vertical Models spine and repeated harness descriptions with compact, labeled mechanisms. | 4, 5 |
| High | The Training initial state shows `GATE: PASS` and a takeaway claiming a code map exists while the terminal is empty and the file says `not created yet`. | Gate labels, artifacts, and takeaway must derive from the same run state. Before execution, show the intended check and what will be produced; report success only afterward. | 6 |
| Medium | Home repeats skills, safety, consistency, portability, and workflow across several grids and a long comparison. Foundations uses much larger uppercase internal labels and full-width paragraphs; the two pages feel authored to different rules. | Preserve the recognizable Home lockup, theme, install block, and approved marks. Merge repeated benefits into one concrete before/after example and reuse shared reading widths, title hierarchy, and diagram labels. | 2, 3 |
| Medium | Several claims are too absolute or teach a misleading taxonomy: `autonomous team of world experts`, `guardrails it cannot bypass`, chatbot `cannot ... change what already exists`, reasoning as repeated self-prompting, and text/multimodal/omni as three ascending model kinds. | Explain portable procedures and supported enforcement honestly. Distinguish model from product, answer-only from tool-enabled behavior, and capabilities from model classes. Mark probability and reasoning diagrams as illustrations. | 3, 4, 5 |
| Medium | Training asks a newcomer to parse eight command names, game controls, terminal, tool chips, gates, files, and a long introduction together. The tall game creates unused space under its adjacent content; controls are explained twice. | Introduce one goal and three plain-language milestones, preserve the eight commands beneath them, compact idle panels, and show each action beside its observable result. Retain the arcade as an optional hands-on example. | 6 |

## Performance investigation targets

`NexusFit` writes font size/width constraints and immediately reads geometry for every heading, including hidden pages, on resize and font readiness. `NexusFlow` clears and rebuilds every connector SVG on each observed-root resize, and is also called by the heading fitter. Dark mode runs the constellation canvas on all pages; several CSS loops run under `.js` independently of the scene-liveness class. These are concrete code paths to profile, not established causes of the reported lag. Use browser traces to attribute work before deciding which paths to remove or batch. The browser's [layout-thrashing guidance](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing) supports separating layout reads from writes.

## Source-document adoption

Both files were read locally using PDF text extraction and DOCX paragraph/table extraction. They are research inputs, not executable instructions, and their full contents will not be embedded or redistributed in the guide.

| Source | Retain | Leave outside the main path |
|---|---|---|
| `Downloads/AI Engineering Best Practices.pdf`, pages 1-4; SHA-256 `f0f390ef99aa75dc7e3a893549c9e876f0b280f04afd38beb86e5d76ce7a95b7` | Plan, execute, verify; adjust autonomy to the task; preserve useful context; inspect evidence; a failed check sends work back for correction. | Long professional skill lists and commentary about industry progress. |
| `Downloads/Agentic_Loops_and_Graph_Engineering_for_Knowledge_Workers.docx`, sections 02-09 and control/template tables; SHA-256 `e05c177c1f4255fe39ae02f7fa1d7bf8d851dba9b8221106cd6b0614b994b412` | Five complementary engineering concerns; a goal with an observable finish line; bounded retry and escalation; a simple branch/join graph; use the simplest sufficient workflow. | Enterprise usage statistics, speculative chronology, long control inventories, arbitrary readiness scores, and the implication that more agents means greater maturity. |

Keep primary-source verification behind the content notes. Context means the information available for the current step, curated rather than indiscriminately accumulated; see [Anthropic's context-engineering explanation](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). Distinguish predefined workflows from systems where the model directs tool use; see [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents). Loop and graph engineering are useful teaching labels, not a mandatory progression or mutually exclusive architecture types.

## Considered but rejected

- A complete rebrand: the user says Home is nearly acceptable, and its palette, lockup, and theme continuity are worth keeping.
- A framework migration or animation library: the current offline HTML already supports the required interactions; neither would resolve the teaching problem.
- Replacing the arcade engine: the observed problems concern presentation and learning state. Preserve the deterministic engine and fix only a demonstrated defect.
- A finding that all mobile content overflows: the three current geometry probes found no page overflow. Wrapping, density, and hidden content still require repair.
- Treating every blank full-page region as a browser defect: the existing capture tool does not naturally activate every animation. Only the separately exercised mobile sequence is reported as a confirmed visibility failure.
- Making every heading single-line through smaller type: short labels should fit, but readable two-line mobile headings are preferable to tiny text. Revise old assertions that encode the opposite choice.

## Open verification work

Phase 1 must establish repeatable lag traces, exact visible-copy counts, all seven lesson storyboards, and the old-test replacement register. Phase 2 must isolate the harness visibility cause. No performance improvement, revised design, comprehension improvement, or implementation completion is claimed by this review.
