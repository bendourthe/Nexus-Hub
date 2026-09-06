# Document Generation Failure Analysis

**Historical evidence notice (2026-09-05)**: Observations and verification limits below describe the inspected specimen at the time. Implementation decisions are consolidated in the [master v4.9.0 plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md#evidence-reconciliation-and-precedence), whose conflict resolutions supersede earlier recommendations. A reference to a rejected local rebuild below does not describe the subsequently approved artifact or qualify the generic catalog.

**Date**: 2026-09-04
**Status**: Analysis and implementation requirements; catalog changes not implemented
**Companion**: [Interactive handbooks plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md)
**Subsequent correction**: [Presentation design and fit reassessment](presentation-design-and-fit-reassessment.md). The later 83-slide rebuild was also rejected: negative pattern review overcorrected toward plainness, the deck exceeded the source count, and expanded viewport checks found overflow. Read the positive design contract below with this inventory; it is not a minimalism mandate.

## Outcome and evidence boundary

The inspected presentation workflow lost substantive content, substituted flattened graphics for reconstructable figures, repeated sparse layouts, and failed to detect image placement defects. Adding a presentation button alone does not solve these problems. The generation contract must account for source content, design each view for its task, reconstruct figures from evidence, and inspect the final rendered result.

Evidence for this initial analysis includes the user's supplied failure screenshots, the local original PDF, two unsuccessful HTML outputs, a positive older HTML reference, five interactive codebase handbooks, their authoring guide, and the current presentify command and delegates. That inspected output had 29 presentation slides for a 68-page source; the subsequent rebuild and rejection are analyzed separately in the linked reassessment. Counts alone do not establish loss; the observed reductions, missing figure detail, and impoverished slide compositions establish the initial failure. Eight visible images accompanied that initial report; references to other numbered screenshots were treated as written observations, not as images independently inspected.

Private source documents, extracted figures, names, values, and rebuilt board artifacts remain in the user's Downloads folder. This report records generalizable behavior only. The separate board rebuild is an authorized local artifact experiment, not an implementation of Nexus-Hub v4.9 or a successful one-invocation benchmark.

## Failure mechanisms and required corrections

| Failure | Why the previous checks were insufficient | Required correction |
|---|---|---|
| Summary deck substituted for comprehensive source conversion | Section and slide counts were accepted without a claim-level coverage map. | Inventory every source page, substantive paragraph, figure, table, annotation, qualifier, and appendix. Map each to the reading view and the chosen deck depth. Deep dive requires all substantive units. |
| Repeated bullets with large unused regions | One layout was stretched across unlike content; whitespace was not reviewed in context. | Choose composition from the content: comparison, process, timeline, evidence figure, event schedule, financial table, or narrative. Review a contact sheet and each dense slide at actual size. |
| Static chart/map screenshots | Low-confidence extraction became a blanket excuse for skipping recoverable data. | Inspect native text, vectors, tables, source renders, and legends before deciding reconstructability. Preserve printed precision; distinguish recovered geometry from printed data. |
| Incorrect graphic captions or series labels | Captions were inferred from nearby prose rather than the actual figure. | Verify axes, category order, series keys, units, date ranges, and captions against the source image. Unknown labels remain unknown. |
| Incomplete map reconstruction | Geographic outlines were treated as sufficient without all regions, labels, and relationships. | Retain region boundaries, site/staff identifiers, legend roles, selection behavior, and searchable equivalent details. Do not misrepresent schematic label anchors as geocoded addresses. |
| Missing diagram relationships | Replacing an image with boxes can still omit arrows, branch direction, footnotes, or shared inputs. | Record nodes, edges, arrow direction, grouping, legend, and caveats before reconstruction. Verify the rendered graph against that inventory. |
| Cropped, tiny, or oversized photos | Image-loaded checks only proved the URL resolved. | Retain an asset ledger with source page/bounds, native dimensions, aspect ratio, intended role, visible annotations, displayed dimensions, and enlargement. Inspect the actual subject, not just the bounding rectangle. |
| Full-window reading transitions | Presentation-scale staging was reused in a scrolling document. | Reading dividers use content-sized spacing. Keep immersive staging for the optional presentation and cover; motion must not obstruct reading or create empty scroll journeys. |
| Generic ornament repeated across the artifact | Procedural backgrounds and visual motifs were treated as mandatory quality signals. | Remove unconditional decoration quotas while retaining purposeful reference-led color, depth, curves, surfaces, and motion. Calm unadorned pages are valid when suited to the task, not as a universal response to design criticism. |
| Completion despite failed visuals | Structural scores were presented as visual/content evidence. | Distinguish structural, factual, perceptual, and behavioral evidence. Any required failure prevents a production-ready claim. |

## Research and interpretation

Anthropic describes repeated generic typography, purple-on-white palettes, and predictable component arrangements as convergence toward common generated defaults. Its practical lesson is to specify a contextual visual direction and concrete examples. Replacing one default with another named font or palette does not establish originality. [Anthropic, Improving frontend design through Skills](https://claude.com/blog/improving-frontend-design-through-skills).

Nielsen Norman Group's prototyping work supports supplying specific task and interaction requirements instead of broad requests for an attractive interface. Its visual hierarchy guidance emphasizes relationships conveyed through scale, contrast, grouping, and placement. Apply these principles to the document's audience and message, rather than equating more decoration with better design. [AI prototyping](https://www.nngroup.com/articles/ai-prototyping/), [Visual hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/).

Datawrapper's visualization guidance treats titles, annotations, axes, direct labels, and explanatory text as parts of the visualization. Reconstruction must preserve those semantics as well as the plotted marks. A native SVG with unreadable labels is still a failed figure. [Text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations), [Accessible charts, maps, and tables](https://academy.datawrapper.de/article/206-how-we-make-sure-our-charts-maps-and-tables-are-accessible).

These sources support design and usability principles. They do not establish a reliable detector of AI authorship. The catalog must never promise that a result cannot be identified as AI-generated or invent an authorship probability. The goal is original, audience-appropriate, source-faithful professional work with observable quality evidence.

## Pattern inventory for cross-format authoring

This inventory combines observed failures and research-informed review candidates. It is a review checklist, not a claim that every listed pattern occurred in the supplied artifact. A permitted brand treatment can use any individual visual primitive; repeated, purposeless application is the concern. Hard defects such as clipping and unreadable contrast have no aesthetic waiver.

| ID | Pattern to challenge | Preferred decision or proving check |
|---|---|---|
| V01 | The same green or accent top rule on every box | Use rules for actual grouping or brand hierarchy; eliminate habitual decoration. |
| V02 | An equal-card grid for unrelated types and lengths of content | Use the natural structure: schedule rows, comparison columns, figure plus commentary, or a table. |
| V03 | Rounded containers nested around every paragraph | Remove containers that do not explain grouping or interaction; retain purposeful radius, surface depth, and elevation from the chosen reference. |
| V04 | A large headline followed by the same eyebrow and subtitle on every slide | Establish a strong hierarchy and vary composition by the material. Reference-led large headings, eyebrows, and subtitles are permitted. |
| V05 | All-caps, widely tracked labels repeated without navigational purpose | Use readable case and a real section/figure label only where it helps. |
| V06 | A stock font stack chosen solely because generators commonly use it | Match the supplied brand or justify a legible audience-appropriate choice; do not blacklist fonts categorically. |
| V07 | Neon gradient text, pills, or buttons as automatic emphasis | Preserve purposeful palette layering and brand emphasis; verify contrast. This is not a gradient or rounded-button ban. |
| V08 | An identical mesh, grid, glow, or particle field on every page | Match the supplied visual direction and vary emphasis by composition. A calm background is an option, not a mandatory replacement for expressive references. |
| V09 | Glass panels over a busy background | Test actual text contrast and remove distracting layers. |
| V10 | Decorative icons beside every bullet | Use icons only when they distinguish meaning and have accessible labels. |
| V11 | Invented dashboard statistics or oversized numbers disconnected from context | Keep source units, dates, denominators, uncertainty, and provenance adjacent. |
| V12 | A repeated three-part or four-part structure imposed on the source | Let source relationships determine grouping and count. |
| V13 | Every slide using a title, three bullets, and a large empty region | Design a source-specific composition; do not fill the gap with unrelated illustration. |
| V14 | A tiny graphic floating in unused space | Give the evidence figure enough space to read; compose secondary prose alongside or within the recorded slide budget. |
| V15 | A two-row continuation caused by fixed-size table chunking | Author table composition before chunking. Any continuation must respect the source-deck ceiling and retain headers, units, and context. |
| V16 | Dense content squeezed by scaling the whole slide | Reflow or use coherent progressive builds within the slide budget; measure rendered text after transforms and reject stage overflow. |
| V17 | Image `cover` crops that remove the photographed subject or annotations | Use contain for evidence and product imagery; inspect source bounds and full subject visibility. |
| V18 | Mismatched image heights that make meaningful assets tiny | Assign role-based sizing and provide usable enlargement with honest native resolution. |
| V19 | Low-resolution chart screenshots presented as a finished reconstruction | Rebuild recoverable data and diagrams; document precise exceptions. |
| V20 | The wrong chart caption, units, or legend reconstructed confidently | Cross-check the visible source; retain ambiguity instead of inventing labels. |
| V21 | A polished map that omits regions, cities, staff, or the legend | Verify a complete feature/label inventory and accessible selection equivalents. |
| V22 | A diagram with plausible boxes but missing or reversed arrows | Compare the full directed relationship inventory against the rendered graph. |
| V23 | Every chart using the same bright palette regardless of semantic role | Use stable series meaning, direct labels where helpful, and distinguish more than color alone. |
| V24 | Replacing footnotes, exclusions, and caveats with a reassuring summary | Preserve their association with the relevant claim in each required view. |
| V25 | Decorative animation that delays access to evidence | Prefer nonblocking, optional motion with reduced-motion support. |
| V26 | Full-viewport transition scenes in a detailed reading document | Size transitions to their content and verify the overall scroll length. |
| V27 | Theme changes that leave chrome or figures in an incompatible palette | Apply complete palettes and measure every assigned theme. |
| V28 | Fake interactivity, hover-only facts, or controls with no observable result | Exercise every control and provide keyboard/touch equivalents. |
| V29 | Stock photos added simply to satisfy an imagery quota | Use source imagery or explicitly authorized relevant assets; no quota. |
| V30 | Formulaic prose, inflated claims, and slogans substituted for specific information | Route prose through anti-slop-editing, retain facts and voice, and separate proposed revisions. |
| V31 | A file called final because it exists or a selector was found | Qualify the final bytes through the required factual, rendered, and functional gates. |
| V32 | Cosmetic changes claimed to guarantee human authorship or investor approval | Report observable design improvements and actual evidence only. |

## Positive design contract

The pattern inventory must not erase the user's chosen visual language. Preserve authentic brand assets, confident typography, coordinated color, purposeful curves and rounded surfaces, appropriate depth, and meaningful animation when the reference and output format call for them. No individual font, radius, border, gradient, shadow, or eyebrow establishes poor quality or machine authorship. The problem is unconsidered repetition, incorrect hierarchy, missing meaning, or a mismatch with the task. A static document uses format-appropriate equivalents; it need not simulate web motion.

Retain a positive visual brief and author representative cover, narrative, complex figure, dense table, and compact transition compositions before full generation. Review reading and presentation modes separately against the references, including supported motion and Replay states. This is an internal quality step within the existing user request, not a new mandatory approval gate. Factual fidelity, engineering behavior, and design merit each require a pass; one cannot compensate for another.

A source slide deck must preserve or reduce its logical slide count, with full coverage at the selected depth. Include title, divider, and appendix slides in the total. Progressive builds explain one coherent composition; they must not disguise unrelated extra slides. Ordinary reports and handbooks use their own recorded audience/time/content budget. If coverage, count, and readable fit conflict, report that conflict rather than imposing more slides, less detail, or smaller text. The earlier advice to split freely is superseded by this constraint.

## Ownership and distribution

`hallmark-design` owns the cross-format visual pattern review and brand exceptions, with a linked Tier-3 reference holding this inventory and positive/negative neutral examples. `anti-slop-editing` owns prose. `document-to-interactive-html` owns source coverage, reconstruction, asset handling, and dual-view authoring. `functional-verification` owns observable behavior and measured defect evidence; accessibility, color, typography, and layout delegates keep their existing measurement responsibilities.

HTML, slide, Word, PDF, and graphics generation owners must explicitly hand off to the shared design owner before final delivery. Commands remain thin dispatchers. Rules express the trigger and handoff, not duplicate checklists. Existing HTML hooks may enforce deterministic defects only, such as known clipping risks or omitted verification records when the lifecycle contract can establish that fact. A style heuristic can request inspection but cannot block based solely on a font, border color, or arbitrary card count. Non-HTML generation is covered through its owner workflow and format-native rendered checks, not an HTML-only hook.

## Required qualification cases

The neutral benchmark set must include a long source deck with tables and appendices, a multi-region map with overlapping labels, a branched diagram, mixed photographic aspect ratios, recoverable chart vectors with an unlabeled series, conflicting printed totals, and a document with sparse and dense pages. Use at least two brands and include a legitimate richly styled treatment as a false-positive case. Include a bland-but-technically-valid counterexample, source-count expansion, and a height-breakpoint overflow regression; the linked reassessment supplies observed failure mechanisms.

Required evidence includes source-unit and asset/figure inventories, page/deck mappings, extraction precision and exceptions, actual rendered text sizes, image subject visibility, label collision checks, whole-deck contact sheets, keyboard and touch actions, offline behavior, reduced motion, and final output hashes. Seed missing labels, wrong captions, hidden figures, clipped photographs, unreadable transformed text, dead controls, and a tiny continuation slide to prove checks fail for the intended reason.

Run one request through extraction, authoring, assembly, review, and bounded internal repair. Record first-build defects, repair iterations, and final results separately. Test breakpoint neighbors, wide/short windows, resizing, actual supported zoom conditions, and all authored motion states in addition to named viewport samples. Record qualitative design judgments independently of measurements. The later local specimen remains user-rejected and fails broader fit; its historical successful checks apply only to their recorded conditions and do not establish production readiness or shipped workflow quality.
