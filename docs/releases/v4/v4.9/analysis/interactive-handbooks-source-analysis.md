# Interactive handbooks: source analysis and adoption decisions

**Historical evidence notice (2026-09-05)**: Observations and verification limits below describe the inspected specimen at the time. Implementation decisions are consolidated in the [master v4.9.0 plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md#evidence-reconciliation-and-precedence), whose conflict resolutions supersede earlier recommendations. A reference to a rejected local rebuild below does not describe the subsequently approved artifact or qualify the generic catalog.

**Date**: 2026-09-04
**Project**: Nexus-Hub
**Adoption target**: v4.9.0
**Scope**: Analyze the supplied rd-data-dev handbooks and authoring standard; plan a shared default for presentify, documentation updates, and release preparation.
**Verification level**: Local source and structure inspection. Browser inspection was attempted through the available browser tool, which returned "No browser is available". No rendered visual, fullscreen, accessibility, or clinical correctness pass is claimed.
**Companion plan**: [v4.9.0 interactive handbooks](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md).

## Outcome

Adopt the format and its measurable authoring discipline: one offline HTML file, a detailed scrolling reference, and a presentation at the selected depth available from the title page. Keep the project-specific voice and branding. Share figures and data between the views, retain build inputs in the project, and require proof of content freshness and rendered quality before calling a release-ready handbook complete.

The examples are a strong design reference, but they are not a ready-to-distribute component. Several source/guide differences need deliberate resolution. Nexus-Hub also explicitly forbids dual navigation today, so adding a button alone would leave contradictory instructions and blind QA.

## Evidence scope and provenance

Inspected source root: `<workspace>/rd-data-dev/docs/handbooks/`. The guide is `authoring-interactive-handbooks.md`; the five outputs are under `algorithms/`. This is a local, work-in-progress snapshot: Git reports staged additions/renames and further unstaged edits, and the authoring guide is untracked. No source repository files were modified by this planning work.

Nexus-Hub inspected HEAD: `5bdb35870311ffc2f24da656e9af9d3a54dfa9ff`, branch `feat/v4.4.3-guide-illustration-rebuild`. Concurrent guide implementation and reserved v4.7/v4.8 documents were present. These observations are a planning baseline, not a claim about later branch state.

| File | Bytes | Actual slide count | Content and teaching structure |
|---|---|---|---|
| algorithm-review-and-validation-plan.html | 513790 | 25 | Cross-cutting overview, signal chain, algorithm-by-algorithm detail, gap register, priorities, scope, capabilities, and validation planning. Seven cover/divider-class slides establish the larger narrative. |
| lvedp-algorithm.html | 278863 | 7 | Definition, current computation, steps with evidence, failure modes, reference implementation, porting, verification versus validation, and external inputs. |
| suction-alarm.html | 355281 | 8 | Existing rule, reproduction evidence, threshold analysis, correction issue, false-positive mechanism, proposed filter, recommendation, and validation requirements. |
| pump-position-feedback.html | 296618 | 8 | Problem, device geometry and position states, available signals, evidence, proposal, uncertainty, and staged validation. |
| failure-detection.html | 268436 | 7 | Problem framing, observable signals, failure signatures, rules and guards, alerting behavior, unused event logs, sequencing, and sources. |

Counts came from parsing actual `article.dkslide` markup: 55 slides total. An initial probe for a nonexistent `dk-slide` class returned zero and was corrected; zero examined instances is not evidence of passing coverage.

| Source | SHA-256 at inspection |
|---|---|
| authoring-interactive-handbooks.md | 6f33a1b20ff4979a6000bf336c5bf0c72c7c021e3992461e21c882ba5aa27099 |
| algorithm-review-and-validation-plan.html | 767a433ed02c233b00da9675cfcb831ecc07c9ac25fd486ca3f8b48baa86e65f |
| lvedp-algorithm.html | 385275c909fcd2565d0b1fb822e382b2b7b33948ef3d13642ed4af69369a2fb2 |
| suction-alarm.html | 3faac98c996ac93c1e765f6c485d4c9848f3740a33c66622ede209ce8885cad1 |
| pump-position-feedback.html | d97b17b27fd6f9b663511393e4beda5da1fb2e8932a4e3e8806b0b68336cd3a1 |
| failure-detection.html | 099c346eccbc738d03a5d8728471376c2b35641beca7a69fd6b909e0f948a67d |

The inspection covers headings, body structure, styles, embedded scripts, figure references, and the entire authoring guide. Numeric/clinical claims were treated as documentary content, not independently verified against patient data or the algorithm implementations. Generic catalog fixtures must use synthetic data and neutral subjects; no Supira branding or clinical corpus is needed in Nexus-Hub.

## What makes these documents effective

### Content: two deliberately different levels

The page explains the system in enough detail to inspect it: named implementation paths, concrete steps, evidence figures, failure cases, limits, and sources. The presentation extracts a reasoned story. For example, the LVEDP page has a section about its shipped algorithm while its deck states the claim "Nine steps, every one of them already in the shipped Python". This is purposeful condensation rather than turning every paragraph into a slide.

Current behavior, proposed changes, empirical evidence, and unanswered validation questions remain distinct. This distinction should survive any generic handbook update; a release must not convert a proposal into an implemented fact just because its document was regenerated.

### Visual style and hierarchy

The inspected CSS uses navy structural bands, light reading surfaces, teal and supporting semantic accents, locally available heading/body/monospace fonts, responsive gutters and spacing, and a fluid root type scale. Dark cover/divider slides and light content slides create a clear change of pace. Source typography includes Trebuchet MS and Verdana; these are project choices, not required Nexus-Hub defaults.

The hero holds the title, lead, presentation row, and status. Page sections have anchors and navigation; detailed figures have captions and explanatory prose. The deck prefers large visuals with a small number of claims, split figure/text compositions, or wide visual compositions. The presentation button belongs in the hero, not in a detached section that interrupts the document.

### Construction and reuse

The guide describes this build chain:

```text
retained page source + figure model + chart renderer
    + authored slide fragments + presentation renderer
    -> figure build and normalization
    -> idempotent deck injection into the hero/page
    -> one standalone HTML file
    -> structural and rendered audits
```

The inspected HTML supports key parts of that design. The chart script exposes a chart constructor and figure-model lookup; deck holders select existing models by `data-fig`. The deck invokes the same chart renderer at presentation dimensions. Some schematics use `data-clone` to clone existing page figures rather than redraw them. Cloned container layout is preserved; marker/gradient references are rewritten.

The presentation uses a 1600 by 900 design canvas, scaled by one factor, and a bottom control bar with Back, Replay, Next, count, section, dots, and Exit. It gates animation with the active slide's `play` class and contains reduced-motion rules. Native fullscreen change is used to close the presentation when the browser exits fullscreen.

## Guide-to-implementation gaps and portability decisions

These are source-level findings and risks, not reproduced browser defects.

| Finding | Evidence | Decision for adoption |
|---|---|---|
| Browser titles were copied forward | All five `title` elements say "Supira Algorithm Review & Validation Plan v2.6.0", despite different H1 subjects. | Validate document-specific title, H1, identity, and revision from one metadata source. |
| Rebuild inputs were not located | Normal and hidden/ignored file inventories under the handbook tree, plus a bounded repository search excluding VCS/dependency environments, did not find the named deck/figure builders, slide fragments, or model files. | Require retained inputs and a clean-checkout rebuild. Do not claim the source example build can currently be reproduced. Re-inspect at implementation; recover or minimally reimplement neutral primitives. |
| Fullscreen behavior differs from the written rule | Guide section 5 says fullscreen only; inspected `fullscreen()` catches denial while `openDeck()` has already opened the overlay and locked page scrolling. | Prefer native fullscreen on a user gesture; provide an explicit viewport presentation fallback with working Exit and focus restoration. No silent half-open state. |
| Focus containment is asserted but not implemented in the inspected LVEDP handler | Its key switch has no Tab handling and its open/close functions do not make the background inert. Four standalone outputs have no `inert` token. | Test actual Tab/Shift+Tab containment, background inertness, active-slide exposure, and return focus. Do not accept token searches as accessibility proof. |
| SVG clone IDs are not globally unique by construction | The counter resets inside each holder, producing `dkc1-<source-id>` for repeated instances. Root ID removal and descendant-only rewriting also need edge-case coverage. | Use a document/slide/instance prefix and rewrite root and descendant references, including ARIA IDREFs and SVG href forms. Test two uses of the same figure with the original removed from the deck test context. |
| Plot/diagram fidelity has two layers | Shared data-model figures and some cloned schematics are present; the files also contain slide-specific inline SVGs. | Share canonical fact/data/figure definitions. Permit genuinely different teaching illustrations when identified as such and source-linked; do not falsely claim all illustrations are clones. |
| A fixed canvas can undermine mobile legibility | Scaling 1600 design pixels to a phone shrinks authored type; the guide's 11-design-pixel floor is weaker than existing Nexus-Hub rendered floors. | Keep 16/13/12 CSS-pixel role floors from the current typography contract. Use responsive rearrangement or authored continuation slides; never shrink indiscriminately. |
| Corpus-specific QA counts do not generalize | Guide boxfit requires at least 100 boxes; many valid future handbooks will have fewer. | Derive expected counts from the document inventory; require complete coverage and fail accidental zero coverage. Explicit N/A is valid for a genuinely absent feature. |
| Layout measurements can be gamed | Guide rejects bounding-box fill, one-way shrinking, and checks against hidden/clipped containers. | Measure real occupied regions and visible descendants. Record exceptions by slide type; never pad slides to meet a number. |
| Current generic guidance contradicts sloped annotation labels | Presentify rationalizations reject rotated annotations; source guide explicitly aligns trend labels to measured line slope. | Keep axis/trend labels as a narrow chart-owned exception; ordinary schematic prose stays horizontal. |
| Flat source/output folders conflict with the examples | Current Nexus-Hub policy requires markdown/html subfolders; examples use topic folders and retained authored HTML. | Recognize both layouts through an explicit source/output map. Preserve paths and anchors; support native project generators. |

## Transfer the authoring guide by concern

| Guide sections | Reusable rule | Adaptation |
|---|---|---|
| 1-2: delivery and title | Detailed page and concise deck in one file; one discoverable hero entry; shared figures/data. | Project title/status and branding are inputs; avoid production/debug notes in the visible hero. |
| 3: plots | Preserve exported panel geometry, ticks per subplot, zero lines, readable strokes, centered titles, legends outside plots, and measured annotation placement. | Keep exact source units/data. The 1.7px stroke and spacing numbers are calibrated defaults, not universal visual pass evidence. |
| 4: space | Occupied-area decomposition, measured descendants, bidirectional fitting, and every-instance auditing. | Retain measurements as diagnostics. The guide's 12% unattributed area, 40% plot area, and 88% content-span values are corpus-specific examples, not default aesthetic pass thresholds or instructions to fill space. |
| 5: presentation | Unified navigation, Replay, count, section, dots, Escape/Exit, and focus containment. | Add unsupported/denied fullscreen behavior, native interaction priority, touch, history, print, and no-JS reading. |
| 6: story and themes | Cover, outline where useful, chapter dividers, claim-led content, and a short-bullet composition recipe in the guide. | Retain narrative structure without imposing the guide's bullet/figure quota or longer-deck allowance. Source-deck conversion preserves or reduces logical slide count. Selected light-only or dark-only overrides the example rhythm; mixed mode saves randomized per-slide assignments. |
| 7: SVG | Box-fit checks, measured centering, source reuse, unique IDs, and safe internal references. | Preserve deliberate multi-column label placement and semantic artwork; avoid mechanically recentering every text node. |
| 8: motion | Entrance, sequence, reveal, draw, and at most one meaningful live loop; unified Replay; reduced-motion instant content. | Respect restrained mode and existing fragment stepping; stop work on inactive slides and hidden tabs. |
| 9: build | Retained inputs, shared assets, deterministic and idempotent assembly, valid nesting, index update. | Reuse the existing extractor/content model; no second generic framework or copied brand-specific build chain. |
| 10: QA | Positive rules, measurements plus screenshots, distributions, complete inventory coverage. | Check all page sections and all slides across the existing four Nexus-Hub viewports; structural-only remains a disclosed non-pass for production readiness. |
| 11: portability | Separate branding from structure. | Use project-owned tokens and stable document identities; do not randomize established handbook branding during a release update. |

## Nexus-Hub seams that must change together

| Surface | Current state | Required change |
|---|---|---|
| `catalog/commands/presentify.md` | Thin dispatch, two-stage design intake, scroll/slides choice, explicit ban on runtime toggle. | Scrolling-canvas menu without Slide deck; presentation Yes/No plus conditional light-only/dark-only/random-mix question. Automated handbook callers preserve enabled mode and saved themes without repeated interviews. |
| `document-to-interactive-html/SKILL.md` and `references/slide-navigation.md` | Deep authoring/QA discipline, mutually exclusive modes. | Own the shared dual-view output contract and runtime lifecycle. |
| `references/content-model.md` and `scripts/build_presentation.py` | Normalized extraction model and optional plain deterministic builder. | Preserve existing models; add authored presentation structure and deterministic assembly without reducing the output to the plain template. |
| `scripts/visual_qa_score.py` | Slide checks run only when `nav_mode(html) == "slides"`. | Check both views when both exist, even when the initial view is scroll. Preserve honest structural-only labels. |
| `catalog/commands/update.md` | Docs run first before version bump; hardcoded markdown/html path pair; later fail-on-stale and snapshot duties. | Inventory all handbook HTML and source mappings at entry, refresh against the candidate tree, and fail on stale/missing/unverified output. |
| `technical-documentation`, `user-documentation`, `documentation-consistency` | General authoring and consistency delegates. | Own content refresh, documentation scope, coverage, and freshness; hand off visual production to the existing HTML skill. |
| `docs-layout-refactor`, `setup-project` | Required living tree and fixed markdown/html layout. | Recognize existing layouts and source ownership; scaffold portable defaults only when absent. |
| `implementation-plan`, `implement-phase` runbook, `version-upgrade` | Terminal living-docs check and release integration gates. | Require the same handbook evidence on both direct release and plan handoff; preserve green-integration and publication boundaries. |
| `tests/skills/test_presentify_*.py`, `test_living_docs_architecture.py`, `test_plan_lifecycle_contract.py` | Many prose/structure contracts and reusable behavioral tests. | Update contradictory contracts and add real build/runtime/staleness fixtures. Do not assert historical wording. |
| Installer distribution and generated catalogs | Catalog bundles copied recursively; metadata generated from source. | Verify new assets arrive on supported hosts; regenerate indexes/manifests using the existing pipeline only. |

## Considered but rejected

- Copying the five HTML files into the catalog: couples every project to Supira content and carries copied titles and an unverified build chain.
- Adding a title button while retaining separate rendering paths: creates data drift and leaves the current scorer blind to the hidden deck.
- Replacing every existing Markdown document with HTML: removes useful editable/API/README sources and exceeds the requested format default.
- Rewriting every handbook on every release: produces unnecessary churn. Inventory and verify all; regenerate only changed/stale outputs after the one-time migration.
- Mandatory full-screen-only behavior on every device: conflicts with denied API requests and mobile browser capabilities.
- Accepting a structural score as production readiness: cannot establish typography, clipping, painted chart content, focus behavior, or truth of the narrative.
- Duplicating all design rules across commands: makes later corrections diverge. Assign one owner and thin handoffs.
- Treating existing guide comprehension or selector-audit gaps as solved by this plan: they remain separate work. Reuse their lessons, not their completion labels.

## Planning limits and follow-through

During the initial handbook analysis pass, clinical claims, visual measurements, and runtime interactions were not independently verified. The later local board rebuild has its own source review and rendered/behavioral evidence; it does not qualify these five handbook examples. Source/build recovery and browser qualification are explicit implementation tasks. No new MCP, hosted rendering service, framework dependency, or skill is needed by default. The plan can adapt the shared runtime and local compiler within the existing HTML skill; any dependency proposal must show a concrete unmet need first.

The first delivery benchmark must include a repository handbook, a report with figures, and a presentation source, across at least two brands. Its acceptance is one user invocation, no human repair between generation and delivery, complete content accounting, and a final rendered pass after bounded internal corrections. Record first-build failures as well as final results so the quality claim is measurable.

## User refinement: presentation inclusion and theme

On 2026-09-04 the user clarified the presentify intake using the existing output-format screenshot. Remove the "Slide deck (16:9, arrow keys)" option from the scrolling-canvas menu. Ask whether to include presentation mode on the title page; Yes then exposes Light theme only, Dark theme only, or Random light/dark mix to catch attention. No skips deck authoring and the theme question. Keep design direction as a separate choice. The companion plan specifies this flow in R01, R13, R14, Phase 4, and the QA matrix.

The source examples use a deliberate dark/light rhythm; randomized assignment is the requested portable option, not an assertion about how those examples were generated. Mixed assignments are made once and retained per slide, so navigation, Replay, and unchanged rebuilds are stable. Documentation/release updates keep presentation enabled by default and preserve saved project policy, using mixed for new decks when no policy exists. These are planning changes only.

## User refinement: independent presentation depth

The user also requested a depth choice when presentation mode is enabled: Concise and compact, Balanced, or Deep dive presenting the entire main-page content. The plan now asks unresolved theme and depth choices together after Yes and skips both after No. Presentation depth is independent of page verbosity. Concise summarizes key messages, balanced covers every major topic, and deep dive maps every substantive page content unit to slides without reducing readability. Balanced is the recommended/non-interactive default when no saved project policy exists. Documentation and release refreshes preserve the saved depth and update its page-to-slide coverage map. R15 and the existing authoring, intake, refresh, and QA tasks cover this addition; the plan remains seven phases and 31 tasks.

## Follow-up: observed generation failures

The user subsequently supplied failed board-document outputs and authorized a separate local rebuild. [Document-generation failure analysis](document-generation-failure-analysis.md) records the inspected failures, primary-source design research, a 32-pattern contextual review inventory, cross-format ownership, and new R16-R21 acceptance requirements. Private board content and repair evidence remain in Downloads. Nexus-Hub catalog implementation remains 0/7 phases and 0/31 tasks.

### Correction after rejection of the local rebuild

The later 83-slide rebuild was rejected for plain styling, absent meaningful motion, weak compositions, source-count expansion, and viewport overflow. [Presentation design and fit reassessment](presentation-design-and-fit-reassessment.md) records fresh browser evidence and adds R22-R24 to the plan. The local specimen is not qualified by its earlier bounded technical passes.

The guide's allowance for longer presentations must not be generalized into permission to expand an existing source deck. This user requires the same number of logical slides or fewer, including covers, dividers, and appendices. Handbook presentations retain their own audience/time/content budget. Likewise, negative design-pattern review must preserve the positive examples' stronger hierarchy, coordinated color, purposeful rounded surfaces and depth, and active-slide motion/Replay. The rebuild omitted those qualities even though existing design guidance permits them.

Fresh reference inspection opened the suction handbook presentation and navigated to content slides, confirming the reference's large evidence graphics, layered palette, strong headings, and visible Replay control. This targeted comparison does not constitute a complete runtime or accessibility qualification of the five handbooks. Occupied-area measurements from those examples remain diagnostics rather than universal aesthetic thresholds.
