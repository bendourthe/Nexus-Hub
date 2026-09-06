# Presentation Design and Fit Reassessment

**Historical evidence notice (2026-09-05)**: Observations and verification limits below describe the inspected specimen at the time. Implementation decisions are consolidated in the [master v4.9.0 plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md#evidence-reconciliation-and-precedence), whose conflict resolutions supersede earlier recommendations. A reference to a rejected local rebuild below does not describe the subsequently approved artifact or qualify the generic catalog.

**Date**: 2026-09-04
**Status**: User-rejected local specimen; design qualification failed; expanded viewport audit failed. Catalog implementation remains unstarted.
**Companions**: [Implementation plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md), [earlier failure analysis](document-generation-failure-analysis.md), [reference study](interactive-handbooks-source-analysis.md).

## Verdict and scope

The rebuild overcorrected from repetitive decoration to an underdesigned document. It improved reconstruction and source accounting but did not deliver the requested cinematic reading experience or polished presentation. The agent applied the negative pattern inventory too aggressively, failed to preserve the positive references' visual language, and treated bounded technical checks as stronger evidence of design quality than they were. The user's rejection is supported by inspection of both modes and by fresh browser measurements.

This is an audit and plan correction, not another redesign. The rejected HTML and its authoring scripts remain unchanged. Private source material, screenshots, and detailed measurements remain in Downloads. The report records reusable failures without copying board content into Nexus-Hub. It does not qualify the handbook examples as production-ready or re-audit every source claim.

## Evidence inspected

- The current board-review HTML, retained renderer, CSS, JavaScript, model, coverage map, previous QA scripts and records, and the five newly supplied screenshots.
- Existing full-deck captures and contact sheets; fresh reading-view captures of the cover and representative chart, process, and photographic sections; fresh presentation overflow reproduction.
- The preferred older board HTML and the suction handbook, including live entry into its presentation and navigation to content slides. The other four handbooks and authoring guide were covered by the earlier source study.
- A read-only Chromium audit of all 83 current slides at 14 CSS viewport sizes, plus source-level inspection of motion, layout, splitting, and theme behavior. External requests were blocked for reference rendering; these comparisons are local observations, not full reference-browser qualification.

Local evidence is under `board-rebuild/rejection-audit/` beside the output, notably `audit.json`, `current-slide14-1536x784.png`, `current-reading-17.png`, and `preferred-handbook-deck-2.png`. The executable probe is `board-rebuild/audit_followup.py`. The inspected HTML SHA-256 is `f6aad0e67a12a91f932cb3ecb7b83c6e260cb642f36edac26e7ffd5cbd5c6a7f`.

## Findings

| ID | Severity | Observation and cause | Required response |
|---|---|---|---|
| D01 | High | The scrolling cover loses the reference's recognizable mark, stronger type, layered navy field, and coordinated colored waves. A text approximation, thin oversized title, square white action, and largely empty field create a generic document front. The source-coverage count is exposed as prominent production metadata. | Retain supplied brand assets and establish a positive visual brief. Make the cover an authored composition with a purposeful motif, clear hierarchy, and title-page presentation entry. Keep generation diagnostics in the audit record. |
| D02 | High | Reading sections use repeated equal columns, paragraph rules, thin headings, and plain white fields. Removing tall transition scenes also removed meaningful motion and variation. The page became a long report without the cinematic rhythm requested. | Author compact chapter transitions, evidence-led compositions, purposeful surfaces, and nonblocking reveals. Reading depth and visual richness must coexist without full-window empty transition journeys. |
| D03 | High | Presentation covers and dividers are almost empty navy screens. Content layouts still distribute material through shared grids and automatic margins rather than a deliberate hierarchy. Changing light/dark backgrounds changes the palette without changing the composition. | Storyboard cover, chapter, narrative, comparison, diagram, photographic, and dense-data treatments. Use deliberate quiet space where it supports a message; do not confuse blank regions with visual sophistication or fill them to satisfy a percentage. |
| D04 | High | Meaningful animation and Replay were omitted. The current script's single animation-frame path moves the cover motif on scroll; slide changes replace content immediately. There is no staged diagram explanation or chart reveal. | Restore content-appropriate entrance, sequence, drawing, emphasis, and Replay behavior from the positive reference. Respect selected motion intensity, reduced motion, hidden-tab suspension, and readable initial/final states. |
| D05 | High | The rebuilt process figure is predominantly 24 similar outlined rectangles with text arrows. Shared inputs, independent lanes, and directional relationships receive little visual distinction. Reconstructing labels into HTML improved resolution but did not finish the visual explanation. | Design graph hierarchy and actual connected paths, distinguish shared and independent work, and use controlled progressive emphasis. Check every source relationship separately from judging polish. Color and motion must explain the diagram, not conceal missing edges. |
| D06 | High | The renderer produces 83 slides from 68 source pages: 15 extra, a 22.1% increase. Fourteen pages are split and no pages are merged. The plan explicitly permitted unlimited deep-dive slides and enforced a short-bullet recipe, creating the wrong incentive. | Make the source-deck ceiling explicit before authoring. Preserve or reduce logical slide count, with all cover/divider/appendix slides included. Replace automatic splitting with authored compositions and bounded progressive builds. |
| D07 | High | Slides overflow at ordinary desktop sizes. The scrollable stage masks a failed viewport fit; height-specific overrides cause a discontinuity where a taller window fits less content. | Reserve actual navigation space, size evidence within remaining space, test breakpoint neighbors and resize transitions, and reject stage overflow. Never conceal failure with clipping or unreadable global scaling. |
| D08 | High | The earlier report emphasized 28 behavioral checks and 600 viewport observations. Those did not test creative/reference fidelity, a source-slide ceiling, or the failing viewport boundaries. Capturing screenshots did not ensure the qualitative review was adequate. | Separate factual, engineering, and design verdicts. Require all to pass; a high technical score cannot compensate for a rejected visual result. Record tested conditions and distinguish observations, assertions, and qualitative judgments. |

The title-only divider screenshot alone does not prove a content omission: some original pages are dividers. The failure is the unpolished treatment and overall pacing. Similarly, using rectangles or a standard sans-serif font is not itself a defect. Their repetitive, undifferentiated use and mismatch with the accepted references are the problems here.

## Positive reference comparison

| Dimension | Preferred references | Rejected rebuild | Authoring lesson |
|---|---|---|---|
| Brand and hierarchy | Recognizable two-color mark, stronger headings, coordinated accent roles, confident contrast. | Approximate wordmark, thin large titles, mostly flat navy/white. | Preserve brand identity and hierarchy before choosing individual decorative effects. |
| Depth and surfaces | Softly rounded surfaces, restrained shadows, layered fields and curves where appropriate. | Predominantly flat, nearly square controls and outlined content. | Anti-pattern review must allow the visual primitives the user explicitly selected. |
| Evidence layout | Large aligned charts with supporting claims, captions, legends, and deliberate grouping. | Content often flows into interchangeable grids or is split away from supporting evidence. | Choose spatial relationships from the explanation, not the number of child elements. |
| Motion | Active-slide entrance and staged draw/reveal behaviors; Replay; reduced-motion handling. | A small cover-scroll effect and instant slide replacement. | Motion is part of the teaching design, not a binary decorative add-on. |
| Rhythm | Coordinated light/dark beats, evidence-dense content, purposeful introductory moments. | Theme alternation without sufficient compositional variation; empty dividers recur. | Theme variety is only one part of visual variety. |

Source inspection found no positive CSS keyframe animation in the rebuild; its animation/transition declarations disable motion for reduced-motion preferences. The older positive board also has no CSS keyframes but implements motion through JavaScript. Therefore counts of keyframes, gradients, shadows, or rounded corners are diagnostic clues, never quality scores or quotas. The stronger evidence is the rendered difference and the missing runtime behaviors.

The existing hallmark-design skill already allows radius, elevation, and motion. The failure was not entirely demanded by that skill. However, application-interface prescriptions such as a single-theme shell or blanket suspicion of certain hero/card arrangements must not be exported unchanged to every document format. The earlier pattern inventory should constrain purposeless repetition while preserving reference-led art direction. No available evidence establishes that a model temperature or other creativity parameter caused this result.

## Slide count and narrative structure

The renderer splits source page 12 into three slides and pages 7, 17, 27, 37, 41, 43, 44, 46, 58, 59, 62, 63, and 64 into two each. That accounts for all 15 additional slides. The deck contains 12 divider slides, largely retained from the source; those dividers must not be incorrectly blamed for all the expansion.

Source-specific split branches and table chunking preceded a complete narrative composition review. This can separate a comparison, explanation, photograph, or time-series context that would be clearer together. The guide's advice that longer presentations are acceptable belongs to its handbook context and conflicts with this user's source-deck ceiling. It must not override that ceiling.

For slide-source conversion, the default maximum is the original logical slide/page count. This case requires at most 68, with fewer acceptable only if the chosen coverage remains intact. The storyboard records each retained or merged source page and every content unit. Meaningful progressive builds may explain one composition within a slide; a sequence of unrelated full-screen panels must not be mislabeled as one slide to evade the budget. If coverage, readable fit, and the limit conflict after composition work, report the conflict instead of silently adding slides, dropping detail, or shrinking text. A handbook or ordinary report has no inherent source-slide ceiling; its saved audience/time/content budget is the appropriate constraint.

## Reproduced viewport failures

The new audit checks stage overflow greater than 3 CSS pixels. These are geometry probes, not complete perceptual or accessibility tests.

| CSS viewport | Failing slides out of 83 |
|---|---:|
| 1920 x 1080 | 0 |
| 1920 x 990 | 0 |
| 1920 x 980 | 0 |
| 1920 x 900 | 10 |
| 1536 x 792 | 2 |
| 1536 x 784 | 3 |
| 1536 x 850 | 0 |
| 1536 x 851 | 4 |
| 1440 x 900 | 1 |
| 1366 x 768 | 0 |
| 1280 x 720 | 7 |
| 1280 x 640 | 33 |
| 1600 x 850 | 0 |
| 1600 x 851 | 5 |

There are 65 failing slide/viewport pairs among 1,162 probes, across eight of the fourteen configurations. Slide 14 exceeds its stage by 36 pixels at 1536 x 784 and 83 pixels at 1920 x 900. Raising height from 850 to 851 pixels introduces failures at both 1536 and 1600 widths because compact layout overrides deactivate. These failures reproduce without needing to know the user's browser zoom. The screenshots do not establish their exact zoom, display scaling, or CSS viewport, and this audit does not claim to have reproduced those settings.

The deck reserves 58 and 64 CSS pixels for its top and bottom controls. Its stage uses `overflow:auto`; slide/body automatic margins, fixed gaps, headings, notes, and an SVG whose height follows width compete for the remaining space. Later height-specific CSS overrides repair selected examples instead of maintaining a continuous fit contract. The next runtime must measure the actual usable stage, including controls and content states, and qualify representative wide/short windows and the immediate neighbors of each relevant breakpoint.

Mobile reading/reflow remains useful and must not be confused with desktop presentation fit. On a declared presentation viewport, the slide stage must not acquire a scrollbar. Explicitly opened detail exploration can provide its own accessible navigation without becoming an excuse to hide required presentation content. Any genuinely unsupported presentation viewport must be identified honestly and offer the reading view rather than claim that clipped or tiny content fits.

## Corrections to the implementation plan

1. Add R22: source-deck count ceiling, with complete coverage and no implicit splitting exception. Remove the unlimited deep-dive and four-bullet prescriptions. Keep source consolidation traceable.
2. Add R23: positive, reference-calibrated design and motion qualification. Retain a visual brief and representative cover, narrative, figure, dense table, and transition compositions before full generation. This is an internal authoring gate using the user's existing direction, not a mandatory extra approval round.
3. Add R24: continuous viewport-fit qualification, breakpoint neighbors, resize transitions, actual CSS viewport reporting, representative zoom/display-scale conditions, and every progressive state. Preserve text floors; do not hide overflow.
4. Extend the existing design owner to challenge both generic ornament and overcorrected plainness across HTML, PPTX, DOCX, PDF, and graphics. Motion applies only to supporting formats and the requested mode. No universal effect quota, no universal minimal aesthetic, and no authorship-detection claim.
5. Apply the positive design contract through presentify, documentation updates, and release handbook refresh. Preserve a project's approved reference treatments and motion policy during regeneration. Source-deck budgets apply to deck conversion; handbook refresh preserves its own storyboard budget.
6. Keep deterministic checks and qualitative review separate and independently required. Add a bland-but-technically-valid negative benchmark, a legitimate richly styled positive benchmark, source-count violations, and height-breakpoint regressions. Occupied-area percentages remain diagnostic, not proof of beauty or an instruction to fill space.

These requirements amend existing tasks and their acceptance gates; the plan remains seven phases and 31 pending implementation tasks. They are planned catalog changes, not installed functionality.

## Considered but rejected responses

- Add random gradients, animations, or rounded cards everywhere: this repeats the original decoration failure without improving communication.
- Ban all shadows, curves, accent rules, or common fonts: this rejects elements present in the user's positive references and promotes another generic default.
- Hide the stage scrollbar or apply one scale transform: this conceals unavailable content or violates readable text floors.
- Add continuation slides until everything fits: this violates the clarified source-deck ceiling and may separate evidence from its message.
- Require a fixed occupied-area target on every slide: this treats content-independent geometry as an aesthetic standard and can encourage filler.
- Treat a source archive, successful image load, SVG output, or screenshot inventory as finished quality: none proves source semantics, subject visibility, or an effective visual explanation.

## Completion boundary

The local HTML is still a rejected review specimen. Its historical checks remain valid only for the conditions they actually exercised; broader fit and design qualification now explicitly fail. The next rebuild should start with a source-budgeted storyboard and representative compositions grounded in the supplied references, then expand only after those internal design and fit gates pass. Another full-deck styling pass without those corrections would repeat the same failure mechanism.
