# Nexus Hub Interactive Guide

This directory holds the public-facing Nexus Hub guide, its arcade-shooter Training data, and retained legacy fixtures. Everything reader-facing is self-contained, opens in a browser, and needs no build step. This `README.md` is for maintainers.

## Contents

| Item | What it is |
|---|---|
| `nexus-hub-guide.html` | Canonical interactive guide. One HTML file. The main entry point. |
| `example/training-scenes.json` | Maintainer source of truth for Training scenes. The guide inlines a verified copy. |
| `example/glow-booth/` | Legacy regression fixture retained pending explicit removal approval. Not reader-facing. |
| `example/glow-booth-shuffle-reference/` | Legacy comparison fixture retained pending explicit removal approval. Not reader-facing. |
| `glow-booth.zip` | Legacy archive fixture retained pending explicit removal approval. Not a reader download. |
| `example/trivia-quiz/` | Previous example. Stays on disk. Not taught in the published guide. |

The guide is the single home for orientation, installation, Foundations, Training, and Cheatsheets. It remains one self-contained HTML file with no runtime network dependency.

## The interactive guide

`nexus-hub-guide.html` is a single HTML file with zero runtime dependencies. No server, no CDN, no remote fonts, nothing to install.

- **To open:** double-click the file. It opens in any modern browser and works fully offline. GitHub does not render HTML inline, so use Download raw file, then open the download.
- **To share:** send that one file.
- **Primary navigation:** Home, Foundations, Training, Cheatsheets. Installation is not a primary page. GitHub is an icon-only external link. Theme toggles light and dark and persists only those two values under `portfolio-theme`.

URL grammar: `#<page-id>` for pages; `#training/<scene-id>` for Training; `#cheatsheets/<stop>` for Cheatsheets sections. A legacy `?beat=n` suffix is accepted and ignored. Compatibility: `#reference` and `#workflows` rewrite to `#cheatsheets`; `#explore`, `#plan`, `#build`, `#harden`, `#ship`, `#communicate` rewrite to `#cheatsheets/<id>`. `#home/install` scrolls to the Home install block. Unknown page ids rewrite to Home.

## Design system (v4.4.5, evolved from v4.2.2, v4.2.3, v4.4.0, v4.4.1, v4.4.2, v4.4.3, and v4.4.4)

The original design language remains recorded in `docs/releases/v4/v4.2/development/guide-rebuild/design-brief.md`. v4.4.1 kept that visual system while rebuilding Home around a five-platform rail, reordering Foundations into eight professionally titled scenes, and replacing the Asteroids walkthrough with a deterministic arcade shooter. v4.4.2 made it production-ready: a shared declarative motion sequencer (`NexusSeq`), connectors computed from live geometry (`NexusFlow`), an annotated-prompt primitive, a live audio waveform, pointer play in the arena, and a fullscreen presentation that fills the window with three panes. v4.4.3 rebuilt the illustrations from a direct visual review: the heading pair swapped weight, every figure that positioned text in a scaled coordinate space became nested elements, the two harness scenes became one, and the product stopped addressing the reader. v4.4.4 followed a second review and changed what several scenes SAY: Foundations reads title-then-subtitle, Models teaches next-token prediction rather than cataloguing outputs, the chatbot comparison merged into Agentic Platforms, and the harness became one flow carrying the operator's brain-degree-experience analogy. The load-bearing decisions:

- **An assertion has to describe the FAILURE, not the intent (v4.4.5).** Three defects in this plan shipped past a passing test, and all three passed for the same reason. A mark asserted as an ELEMENT rendered blank, because a `<use>` clone cannot resolve the mask it carries. A rebuilt scene asserted for presence, order, balance, and containment said everything TWICE, because nothing asked whether anything appeared more often than it should. An artifact chain asserted as `lefts == sorted(lefts)` stacked one chip per line, because four identical offsets sort perfectly well. The tests now measure a painted box larger than 8px, an exact occurrence count, and four DISTINCT offsets on one row. Where the property is visual, a screenshot found what the suite could not: two of this plan's defects were invisible to 333 tests and obvious in one image.
- **A rename is not finished until every sentence about the old name has been READ (v4.4.5).** Not searched: read. Renaming the four prompt parts left the flaw list and a summary sentence describing the old vocabulary, and `NINE PIECES` becoming `9 TOKENS` left a caveat that talked about "the nine-square grid" - a phrase containing none of the renamed words. Twice in one plan makes it a habit, not an incident.
- **One tag size, one token (v4.4.5).** Eleven rules were declaring `11px`, `11.5px`, or `12px` by hand; doubled, those are three sizes nobody can distinguish on an uppercase tag. They resolve to `--fx-tag`. The doubling covers BLOCK tags, which name a whole box or figure; in-cell descriptors inside quarter-width matrix cells keep their size, because a doubled 10.5px label in a 250px cell makes the cell three lines tall. Both halves of that decision are asserted, so the smaller sizes read as a choice rather than an omission.
- **An approved asset is copied, never shared, when sharing would rewrite it (v4.4.5).** The Home portability figure needed the four vendor marks the compatibility rail already carries. Hoisting them into `<symbol>` elements would have made two copies cheaper than one, and it failed three times: the Gemini mask rendered blank inside a `<use>` clone, hoisting that mask to document level rendered an unmasked square, and rewriting a rail chip into a `<use>` tripped the ledger hash guard, whose message states that re-approval is required rather than a ledger update. That guard is right. The figure gets a copy with namespaced ids, about 12 KB, and the approved bytes stay where they were approved.
- **A mockup is a source of teaching, not markup to paste (v4.4.5).** Three operator-supplied mockups drove the Models, Agentic Platforms, and Harnesses rebuilds. What came across is structure: an eight-stage spine, a model-plus-harness equation, a five-step work sequence, an artifact chain. What did not: four tablists, two absolutely-positioned SVG maps, a ring whose labels and arrows lived in unrelated coordinate systems, and every `<select>`, `<textarea>`, and run button. Each mockup hid at least one of its best lessons behind a control - a boundary that REPORTS a refusal rather than routing around it only appears if the reader presses read-only - so those states are all on the page at once, and the tests assert multiplicity rather than presence.
- **Label above title on Home, title above subtitle on Foundations (v4.4.4).** The two pages use the pair differently on purpose. A Home label is a CATEGORY (`Guardrails & Safety`), so it sits above the heading it categorises. A Foundations subtitle DESCRIBES the scene, and the scene name is what the reader scans for, so the name comes first and the description sits under it in dimmed ink at 17px, wrapping like prose rather than shrinking to one line.
- **A model name is one family per provider, with no version number (v4.4.4).** A family name ages slowly; a version ages in weeks, and a static offline file cannot refresh itself. Four providers are named, each read from that vendor's own documentation on the date recorded in `test_v444_phase6_models.py`. Naming the model's MAKER matters too: Grok is xAI's, whatever platform offers it.
- **An asset leaves the page when its teaching leaves (v4.4.4).** Audio was dropped from the Models teaching on instruction, so the WAV, the `<audio>` element, the waveform canvas, and the waveform engine all went with it, and the test inverted to assert their absence. A 12 KB payload nothing explains is worse than no payload. The provenance ledger keeps the row as the record of what was approved.
- **A sequence step is never HIDDEN under reduced motion (v4.4.4).** Zeroing the transition made a reveal instant but still waited for the observer to play, so a reader who asked for less motion saw an empty strip until they scrolled. This matters beyond motion: the contrast sweep samples only visible text, so anything hidden until played was never measured, and making these visible immediately exposed three light-theme AA failures.
- **The heading pair (v4.4.3).** Two tokens, never per-selector edits: `--eyebrow-scale` (3) sizes the segment label at 33px, `--title-scale` (1.2) sizes the segment title at 32.6px. The label is now the larger of the two by design, which is what the review asked for. The old `.6` clamp minimum is gone, because it existed only as a shrink mechanism before anything measured the container.
- **No heading wraps, and the rule is measured, not declared (v4.4.3).** A `font-size` cannot know how wide its container will be, so `NexusFit` measures what each label and title needs at `width: max-content` with the cap removed, compares it to the room the container has, and shrinks by the shortfall. One line always at 720px and wider; below that it holds a 15px floor and hands wrapping back, because a single line at 320px costs about 8px of type. Nothing spills past its container at any width. Refit runs on resize, on font load, and on page change, since a hidden page measures zero.
- **Never measure available space against a track the measured element can widen (v4.4.3).** This bit the plan three times: a `nowrap` label inflating a `1fr` scene track, a `width: max-content` label doing the same, and `width: max-content` on the harness model box pushing both rings 88px outside the scene at 320px. Bound the track with `minmax(0, 1fr)` AND put `min-width: 0` on the intrinsically sized item; either alone leaves one path open. It is the v4.4.1 `BG-11` flex circularity in grid form.
- **Text belongs in boxes that size to it (v4.4.3).** Every figure that drew labels as SVG `<text>` inside a scaled `viewBox` overlapped itself at some width, because the text and the shape behind it were positioned independently. The guardrails figure, the material kinds, the chatbot comparison, and the harness are now nested HTML elements with geometry-only SVG. Where SVG text remains (two fixed captions in the tokens image) it is short and asserted inside its viewBox.
- **The product never addresses the reader (v4.4.3).** No `you`, `your`, `yours`, `yourself`, or their contractions in visible prose or in a user-facing attribute. `test_v443_phase1_headings.py::test_static_document_never_addresses_the_reader` asserts it over the static document; text the Training simulation injects at runtime is out of that scope and the test says so rather than implying coverage.
- **A model name is read, never recalled (v4.4.3).** The Models scene names four released models from three providers, each taken from that vendor's own documentation on the date recorded in the test, with the declared list living beside the assertion. A name recalled from memory is how a fabricated model id reaches a reader.
- **A vendor mark is reused from the ledger, never re-sourced (v4.4.3).** The four platform chips carry marks this guide already approves at pinned hashes. Reusing an asset that carries internal ids requires re-namespacing them, or the second copy resolves its mask and filters against the first; the test derives the expected variant from the approved asset so the id prefix is provably the only difference. The chips label the PRODUCT while the mark is the VENDOR's, which is recorded as a substitution in the provenance ledger.
- **Motion that plays itself, with the access half kept (v4.4.3).** The video output has no control: the animation is the element's own `src`. Under `prefers-reduced-motion` the still frame is shown. That inverts the v4.4.1 press-to-play rule and keeps the half of it that was about access rather than about asking.
- **Every class in the markup has a rule (v4.4.3).** `test_v443_phase8_harness.py::test_every_class_used_in_foundations_has_a_style_rule` ties each class in the Foundations markup to a declaration in the stylesheet. It exists because Phase 4 of that plan deleted CSS after counting four usages of a class and reading that as "the two I am replacing"; the other two were in the harness trail, which rendered unstyled for four commits. A usage count cannot tell you where a class is used.
- **Fluid width (v4.2.3).** There is no per-text width cap. `.container`'s `--maxw` is the ONLY width constraint in the file: body copy fills the content column at every viewport. A test fails on any `max-width` in `px` or `ch` other than the present-mode stage bound, so a measure cannot creep back in. Headings use `text-wrap: balance` to shape wrapping without imposing one.
- **Copy affordance (v4.2.3).** A labelled button only where the control stands alone in a wide terminal row. Inside an inline `.cmd-cell` the button is bare - no background, no border, no label - because the host chip already draws the container and a chip inside a chip reads as a mistake. The bare variant keeps a 24px hit area, its `aria-label`, the live-region announcement, and an explicit focus ring.
- **Invocation convention (v4.2.3).** `.inv-cmd` renders a slash command in accent, `.inv-arg` its scope in plain ink, `.inv-ph` a placeholder dim italic. Used on Home, in Training's terminal, and in every Cheatsheets example. The `data-copy` payload is always the plain full string, so copy parity survives the split markup.
- **Compact rhythm.** A 4px spacing scale (`--sp-1` to `--sp-8`) with `--sec-pad: 32px` (22px under 720px). Sections are separated by an eyebrow and a heading, not by empty space.
- **Motion vocabulary.** `.reveal` elements fade and rise via one shared IntersectionObserver. Continuous motion (constellation, the Foundations work-cycle glyph, and the shooter loop) runs only while its surface is visible. `prefers-reduced-motion` renders a complete static equivalent, pauses the game, exposes Advance one step, and prints terminal output immediately; it never substitutes a crushed duration.
- **Themes.** All colors are tokens defined on `:root`, `html[data-theme="dark"]`, and `html[data-theme="light"]`. Every measured text style in both themes meets WCAG AA contrast. The v4.4.0 Phase 6 browser sweep measured 11,008 visible text samples across all pages and all eight Training states, including 552 generated pseudo-text samples and 265 unique computed styles, and found 0 below AA.
- **Light-mode brand chip.** In light theme the glow logo mark sits on a rounded dark chip so it reads against the light ground.
- **The Nexus mark is true vector geometry, and must stay that way (v4.4.1).** `#nexus-mark` was a single 220 KB base64 PNG inside an `<image>` element until v4.4.1 replaced it with about 2.1 KB of reviewed paths, circles, gradients, and one `feGaussianBlur` glow layer, measured from the original raster so the geometry is preserved. That one change bought roughly 218 KB of the 500,000-byte budget, and every later phase's byte allocation is drawn against that headroom. Do NOT re-embed a raster here, and do not reuse `assets/nexus-hub-primary_no-background.svg`: it is a 1 MB SVG-wrapped raster with zero `<path>` elements, not a vector source. `tests/guides/test_v441_phase1_contract.py` asserts the symbol has no base64 payload, carries real geometry rather than an empty shell, and stays compact.

## Foundations (v4.4.1 order, v4.4.5 presentation)

The page opens with a centred `h1.page-title` in the Home hero-subtitle style and a centred `p.page-lead`; there is no page-level kicker. SIX scenes follow in this exact order, each `.fx-scene` with one `.fx-title` whose `h2.section-title` comes FIRST and whose `.fx-subtitle` sits under it. v4.4.3 merged the two harness scenes into one; v4.4.4 merged the chatbot comparison into Agentic Platforms and inverted the title pair. A scene whose diagram and copy cannot balance within a 1.35 height ratio at 1440 px stacks with `.fx-scene.fx-stack`; the compound selector is deliberate, because a lone class loses to the later base rule on source order.

1. **Tokens Definition** - a real prompt at a 19 px floor, its VERIFIED `cl100k_base` split into ten identically styled chips (`Summarise` costs three, which is the teaching point), and nine image cells that each hold a real 1:1 crop of one original inline picture through namespaced clip paths.
2. **Prompt Engineering** - the same contract request shown vague, then precise as Goal / Material / Done / Format.
3. **Context Engineering** - copy at full width, then the request beside the material it can name, each kind carrying a concrete EXAMPLE rather than a drawing (`checkout-error.png` under `Image`), then the same budget filled two ways side by side with the consequence named in four items each: more tokens, slower, costs more, likelier to miss, against the reverse. No legend and no percentages.
4. **Models** - how a model works, not a catalogue of outputs. An answer arriving one token at a time with each chosen against everything already produced, a base lane that answers in one pass beside a reasoning lane that prompts itself and loops, and three modality tiers (text, multimodal, omni). One family per provider with no version numbers. The provider region still reads training then release, and a prompt never retrains the model.
5. **Agentic Platforms** - one scene carrying the comparison. It names Claude Code, Codex, Cursor, and Antigravity with their marks, sends ONE request to two lanes that show the SAME two zones, and differs only in reach: the chatbot lane leaves the work surface untouched, the agentic lane reaches it when permitted and shows what changed. Four numbered chips say what the agentic lane runs, over the permission and tool boundary. The zone names are asserted identical between lanes, because a version that gave each lane its own zones would look tidier and teach nothing.
6. **Harnesses** - ONE flow, five steps: the request, the model like a powerful brain, the platform harness like a graduate degree with its five ports AND its stated limits, the Nexus Hub harness like decades of practice with its four, and reviewed verified work. Then the five repository-anchored claims with the artifact behind each, and the durable-trail comparison reading platform-loop-alone first. The analogy is load-bearing: it explains why a layer that adds no intelligence changes the result, and the limits box is what makes the outer layer necessary rather than decorative.

Terminology is load-bearing: no visual claims to show reasoning, the one-pass block states plainly that it is not a transcript of hidden reasoning, and platform capability is always stated as "can", "when supported", "when permitted". v4.4.3 retired the spinning work-cycle ring in both scenes that carried it: it depicted no step count, no duration and no reasoning, and its own caption had to say so.

The story diagrams are semantic HTML node trees with small connector SVGs, not bespoke per-scene drawings. That change is what cut the 1440 px Foundations height from 7,235 px to about 5,150 px; `data-phase3-diagram` no longer exists and a guard test fails if an SVG story diagram returns without restoring its containment coverage.

## Browser evidence matrix (v4.4.2 Phase 7)

The retained browser gate is DECLARED before it runs, in `tests/guides/tools/browser_matrix.py`, and is Cartesian only across dimensions that own a distinct layout, theme, state, or interaction contract. The summary records the declared count beside the executed count so a silently dropped case is visible.

| Case group | Dimensions | Cases |
|---|---|---:|
| Base pages | 4 pages x 2 themes x 320/420/900/1440 | 32 |
| Foundations seam | 2 themes x 720/721 | 4 |
| Training states | 8 scene IDs x 2 themes at 1440x900 | 16 |
| Desktop fullscreen | 2 routes x native/fallback x 2 themes x 1280x720, 1366x768, 1440x900, 1920x1080 (coverage and stage fraction recorded) | 32 |
| Narrow fallback | 2 routes x 2 themes x 320/420/900 | 12 |
| Short window | presentify x 2 themes at 1280x600 | 2 |
| Reduced motion | 3 surfaces x 2 themes at 1440x900 | 6 |
| 200 percent zoom | 2 routes x 2 themes x 1280x720, 1366x768 | 8 |
| Home sections | 4 restored sections x 2 themes x 420/1440 | 16 |
| Annotated prompts | 2 scenes x mid-sequence/end x 2 themes | 8 |
| Audio waveform | playing/paused x 2 themes | 4 |
| Harness choreography | steps 1, 4, 7, end x 2 themes | 8 |
| Arena pointer pause | 2 themes at 1440x900 | 2 |
| **Total** | | **150** |

Run it with `python tests/guides/tools/browser_matrix.py --label phase-7`; retained screenshots and the JSON geometry, coverage, console, and request summary land under `docs/releases/v4/v4.4/development/guide-production-ready-rebuild/renders/<label>/`. Evidence stays under 30 MiB per label and a focused run targets 20 minutes; if one invocation would exceed that, split the declared groups with `--groups` into labelled batches rather than dropping or structurally scoring any case. The v4.4.1 110-case evidence remains under `guide-visual-and-arcade-rebuild/renders/phase-6/`.

## Home

Home opens with the floating `Nexus Hub` lockup, the v4.1.2 statement `Upgrade your agentic AI platforms with an autonomous team of world experts` (gradient span painted through `text-fill-color` so `color` stays measurable), and its lead paragraph, then a five-platform compatibility rail. The sections follow in a fixed order that a browser test asserts: `Why it matters` (four cards), `Installation` (the two canonical install commands behind OS tabs, **Windows first and default**), `How it works` (skills, hooks, governance), `Guardrails and safety` (an enforcement story whose layered illustration names only hooks that ship and are registered), `Raw prompting vs Nexus Hub` (the v4.1.2 comparison merged with the v4.4.1 five-row table, labels at 26 px), `Your favorite commands, leveled up` (a seven-row migration table that stacks into labelled cards below 720 px), and the workflow loop (also the first `NexusSeq` timeline). Every restored section is at most two-thirds of its v4.1.2 word count against `tests/guides/fixtures/v412-home-copy.json`. Platform-mark attribution lives in the site footer on every page, never in the Home flow (decision `2026-09-02-platform-mark-attribution-in-footer`).

Canonical install constants (must match `tests/guides/test_nexus_hub_guide.py`):

- Windows: `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`
- macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`

The verify step (`/skills list`, `/commands`) renders as copyable inline cells. wget, flags, and `--workspace` live in a Home disclosure and in Cheatsheets. Do not hardcode skill counts, command counts, or installer versions on Home.

There is no untrusted-origin warning box. It was removed in v4.2.2 along with `isDocumentedGuideOrigin()`; do not reintroduce either.

## Foundations

**v4.4.2 primitives.** `NexusSeq` is the one declarative motion engine: a `[data-seq-root]` reveals `[data-seq=N]` steps in order (`is-on`), starts at 40 percent visibility, pauses offscreen and on a hidden tab, resumes from the same step, and under reduced motion applies the end state synchronously; text carriers never lose contrast during a sequence (use `seq-glow`, never `seq-fade`, on text: BG-13 and BG-14). `NexusFlow` draws every flow connector as an overlay SVG from live card rectangles (three roots: the Models flow, the request region nested inside it, and the Agentic flow) so an arrow cannot overlap a card. The annotated prompt (`.ann-text` with `mark.ann[data-part]` and a `dl.ann-legend`) shows one continuous text whose labelled parts light in sequence; nesting is forbidden by test. The Models outputs are `Text`, `Image`, `Video`, `Audio`; the audio draws a static waveform decoded from the embedded PCM and a live analyser trace while playing (`canvas.fx-wave`, `data-wave-state`). Harnesses and Nexus Hub Harness share one layered SVG (`.fx-hstack`): static and platform-focused in scene 7, a seven-step choreography in scene 8 with a dashed `raw answer` ghost at full contrast.

Foundations is eight scrollytelling scenes, each teaching one concept through a title-plus-subtitle lesson and a hand-authored inline SVG diagram:

1. **What Is a Model** - training precedes platform integration; a later request carries context into processing and a result comes out.
2. **What Is a Token** - one verified sentence split into tokenizer pieces, plus an illustrative image-to-token grid.
3. **What Is Prompt Engineering** - the same non-coding job shown first as a weak request and then with Goal, Material, Done, and Format.
4. **What Is an Agent Platform** - a model operating inside a host loop that can propose actions, observe results, and continue.
5. **Chatbot or Agentic Platform?** - the same request ending as guidance to apply or as checked work completed in the active work surface.
6. **What Is Context** - a finite token budget shown noisy and focused, including what can happen when it fills and why task-matched loading matters.
7. **What Is a Harness** - the model, platform loop and built-in harness, and Nexus Hub's portable workflow layer shown as distinct nested layers.
8. **What Changes in Practice** - an honest comparison between a saved platform result and the same job with matched procedure, written gate, and durable evidence.

Hard rules: no element pins itself over the content, and there is **no toggle** between the two states - both are always visible, because a selector for something already on screen is noise. Diagram colors come from theme tokens so one markup serves both themes. Do not restore a `type="range"` hero, the station cards, the carousel, or the per-scene number badges (removed in v4.2.3 as a full line carrying no information).

**Conventions added in v4.2.3, enforced by tests:**

- **Without-then-with ordering.** Every comparison in the guide reads the less structured state first and the more structured state second - Foundations scenes 3, 5, 6, and 8, and Home's comparison. Differentiation is carried by colour across the whole lane (amber for the weaker path, accent for the stronger path), not only on the outcome badge.
- **Filled arrowheads.** `.fx-head` draws a closed filled triangle. The earlier open two-line chevron drew a single side and read as half an arrow.
- **Pulse paint order.** SVG has no `z-index`; paint order is document order. Phase 3 diagrams declare connectors first, pulses second, and node groups last, so a pulse remains above its path but behind the boxes it crosses. A test enforces the exact layer sequence.
- **Project-generic teaching language.** Explanatory copy avoids "repo", "repository", "terminal", "git", and "codebase" - a vocabulary test guards the Foundations section. Factual claims stay accurate: the hero still names the AI coding assistants, "paste into Terminal" still says Terminal because you literally do, and Cheatsheets still describes what each command really does.

## Training walkthrough

Training is an eight-step interactive arcade-shooter walkthrough (`#nhTraining`, `[data-training-root]`) driven entirely by the scene JSON. Each step composes five things:

1. The step's intent, in second person.
2. **The playable arcade shooter** - a seeded damage bug destroys the ship on the FIRST enemy shot while the HUD still reads three lives, so the defect is observable before `/implement`; the implementation step makes a hit cost one life (3, 2, 1, 0, with a 90-tick invulnerability window), and `/compare` plus its follow-on implementation enables band-clamped vertical movement. Asteroid contact is always fatal in both modes. The full contract is `docs/releases/v4/v4.4/development/arcade-shooter-scenario.md`.
3. **The simulated terminal** - the step's command is pre-filled with a Run affordance; running shows a brief working line, reveals the reply, applies the file changes, and advances the game state. The command is not echoed a second time because the prompt line above already shows it.
4. **The cumulative file explorer** - the tree shows everything created so far, marks the current step's new and changed files, and paints the selected file or diff with text nodes only. A requested path that does not exist yet says so explicitly.
5. The artifact, gate verdict, and takeaway that explain what the command produced and why it matters.

Training navigation uses Previous, Next, and Restart icon buttons in a right-aligned cluster below the takeaway, each with an `aria-label`, a `title`, and a visible focus ring. Outline keeps a text label because a glyph does not carry its meaning. ArrowRight, Space, and PageDown advance; ArrowLeft and PageUp go back; `f` toggles full screen when focus is not in the game or a form field. The focused game owns Left / Right or A / D for horizontal movement and Space for fire; Up / Down or W / S move vertically only after `/compare` enables the feature. The game starts idle behind a real `Click to start` button. **Pointer contract (v4.4.2):** a primary click inside the arena fires with the same cooldown as Space, starts nothing while idle and resumes nothing while paused; the pointer leaving the arena pauses with reason `pointer` and releases held keys; re-entering does not resume, the visible Resume control does; secondary buttons are ignored and the context menu is suppressed. Under `(pointer: fine)` a `kbd` key guide replaces the touch buttons; under `(pointer: coarse)` the five labelled touch controls remain. Pause / Resume, Reset demo, and the reduced-motion Advance one step sit beside the HUD. **Spawning (v4.4.2):** every fixture spawns continuously from a second seeded stream (`seed ^ 0x9E3779B9`) so the teaching beats never move; three enemy velocity bands and three asteroid size and speed tiers; teaching fixtures spawn from tick 120 and keep the centre band clear so a stationary player receives only the seeded beats. The full contract is `docs/releases/v4/v4.4/development/arcade-shooter-scenario.md`.

**Full screen mode** requests fullscreen on the training root and applies a viewport overlay class either way, so a denied or unavailable Fullscreen API still presents as slides. The control lives INSIDE the fullscreen root, in `.nht-bar` immediately before Outline, labelled `Full screen` / `Exit full screen` with a four-corner icon and an `aria-pressed` state synchronized from `fullscreenchange` (the user agent may consume Escape and exit natively, so the handler reconciles rather than assuming script initiated the change).

**Outline** is a nonmodal disclosure, not a dialog: `aria-expanded` on the trigger, a labelled `region` panel, normal tab order, no focus trap, and dismissal by outside click or Escape with focus returning to the trigger.

**Escape precedence** in the overlay is exactly: close Outline first; otherwise, if focus is inside the active game, the game pauses and releases its keys; otherwise the overlay exits and focus returns to the fullscreen trigger.

**Presentation layout (v4.4.2).** At viewports at least 1024 px wide and 640 px tall the slide is a three-pane grid that fills the window: `.nht-grid` is `display: contents` in present mode, so the arena column, the evidence column (terminal, tools, artifacts), and the sibling explorer are direct grid items in tracks `minmax(300px, 34fr) 33fr 33fr`, with head, takeaway, and controls spanning all three. Every pane height is the body row's definite track (the BG-11 lesson); the stage derives its width from the available height, the terminal output is the one secondary scroll, and the explorer stacks tree over file. Acceptance floors, measured by `test_v441_phase6_workspace.py`: viewport coverage at least 0.88 and stage height at least 0.45 of the viewport at 1280x720, 1366x768, 1440x900, and 1920x1080 (achieved 0.93 to 0.95 and 0.47 to 0.61); no pairwise intersection; no horizontal overflow; no region below the fold. Outline is `position: absolute` in present mode and moves nothing; a `matchMedia` listener closes it if the window crosses a breakpoint. Below 1024 px wide OR 640 px tall the slide reflows into ONE scroll surface; a short-but-wide window between 640 and 768 px tall sheds a line of chrome to keep the stage floor. Baseline, target, and arithmetic: `docs/releases/v4/v4.4/development/guide-production-ready-rebuild/presentation-geometry.md`.

**Position and progress** read in plain language: `Understand | 1 of 8 | /describe full`. The progress strip is eight labelled loop stages - each names its command, the current one carries `aria-current="step"`, completed ones dim, and clicking one jumps to it.

URL: `#training/<scene-id>`. The legacy `?beat=n` suffix remains accepted but no longer changes state. An unknown scene id keeps the current step.

Fixture strings are painted with `textContent` / `createElement` only. The Training engine assigns `innerHTML` nowhere, and a test enforces that, so the hostile fixture strings (`<img onerror>`, `</script>`) can never execute.

Eight closed scenes, hard-capped at twelve: `describe`, `review`, `plan`, `implement`, `compare`, `test`, `update`, `presentify`. Do not invent a ninth scene for the follow-on `/implement` after `/compare`; that is the same command with a different plan.

## Cheatsheets

Cheatsheets groups every command under seven **intent-named** sections - Understand and evaluate, Plan the work, Build it, Prove it, Ship and govern, Communicate, Catalog and session. The "Band 1 / Band 2" labels are gone and must not return.

Each command lists **every scope with a one-line description of what that scope does**, plus flags, an alias badge where one applies, and a Training deep link for the eight taught commands. Commands with no scopes say so explicitly.

Since v4.2.3 the scope list is a **single column** (reading across columns was the readability complaint), and every command carries a small terminal captioned "type it like this" showing a real invocation. That terminal reuses the shared `.term` chrome rather than inventing a third terminal style, and the invocation convention colours the command apart from its argument - which is what makes the ordering legible: the scope visibly follows the command instead of floating as a bare token.

A scope shown on the page must exist in that command's own file in `catalog/commands/` - `test_rendered_scopes_match_their_command_files` enforces this, so the page cannot silently rot when a command changes. Old hashes still rewrite with `replaceState`, and every `cs-<stop>` anchor resolves.

## Keyboard and reduced motion

Page-level ArrowLeft / ArrowRight move between pages when Training is not current and focus is not in a self-keyed pane (`[data-nhg-keys='self']`). The five platform marks (Claude, ChatGPT, Gemini, Cursor, GitHub Copilot) are labelled compatibility information, not interactive controls. Each is inlined verbatim from an approved asset in the v4.4.1 provenance ledger, and the suite hashes the embedded bytes against that ledger, so a re-fetched or hand-edited mark fails rather than ships. Dark mode may show the constellation; light mode must not. `prefers-reduced-motion` stops decorative transitions, shows every reveal and diagram in its final state, hides the Foundations motion-path pulses, pauses the shooter with Advance one step available, and prints Training terminal output instantly.

## Fixture maintenance

1. Edit `example/training-scenes.json`. Keep eight scenes unless a later plan raises the cap (never above twelve). The top-level `initial` object defines the starting game and source files. Every scene needs `title`, second-person `intent`, `command`, `tools`, `output`, `game`, `files`, `focus_file`, `artifact`, `gate`, and `takeaway`. File entries carry real display content and declare whether they are created or modified.
2. Copy the parsed JSON into the `<script type="application/json" id="nh-training-scenes">` block. Encode a literal `</script>` inside a string as `<\/script>` so the HTML parser does not close the block.
3. Run `python -m pytest -q tests/guides/test_nexus_hub_guide.py tests/guides/test_arcade_shooter_game.py`. The suite asserts the inline JSON equals the file after parse, hostile fixture strings survive as text, direct step entry is coherent, rerunning a command is idempotent, `/implement` changes damage to one life per hit, and `/compare` records its follow-on implementation before vertical movement appears.

## Command inventory

Every file in `catalog/commands/` is either a Training scene, a Cheatsheets entry, or declined as Training with a reason. New catalog commands after this redesign do not require new Training scenes.

| Command | Placement |
|---|---|
| `/describe` | Training |
| `/review` | Training |
| `/plan` | Training |
| `/implement` | Training |
| `/compare` | Training |
| `/test` | Training |
| `/update` | Training |
| `/presentify` | Training (communicate closer) |
| `/spec` | Cheatsheets |
| `/constitution` | Cheatsheets (alias of `/spec constitution`) |
| `/setup` | Cheatsheets |
| `/skills` | Cheatsheets |
| `/commands` | Cheatsheets (alias of `/skills list`) |
| `/route` | Cheatsheets |
| `/session` | Cheatsheets |
| `/commit` | Cheatsheets (alias of `/update commit`) |
| `/memory` | Cheatsheets; declined as Training |
| `/usage` | Cheatsheets; declined as Training |
| `/research` | Cheatsheets; declined as Training |
| `/org` | Cheatsheets; declined as Training |
| `/tune-prompting` | Cheatsheets; declined as Training |

The same table is frozen in `docs/releases/v4/v4.2/development/guide-redesign-content-map.md`.

## Legacy example fixtures

`example/glow-booth/`, `example/glow-booth-shuffle-reference/`, and `glow-booth.zip` remain in the repository only as legacy regression fixtures while removal awaits explicit approval. They are not linked from the guide, offered as a reader download, or used by the shooter walkthrough. Tests may inspect their frozen historical behavior, but new Training work must use `example/training-scenes.json` and the in-browser game.

## Copy contract (canonical publication)

Canonical source: `guides/website/nexus-hub-guide.html` in this repository.

Published copy (sibling portfolio, outside this tree): `<portfolio-root>/nexus-hub/index.html`. Common local layout is `../online-portfolio/` next to Nexus Hub. Absence of that clone does not block Nexus Hub CI or a release.

Publication is a copy:

- Prefer a byte-identical copy of the canonical HTML.
- An allowlisted head delta such as a favicon `<link>` is acceptable if the portfolio origin still requires it.
- Maintainers copy by hand, or a later portfolio-side script may copy. This release does not add `scripts/sync-nexus-hub-guide.mjs` to the sibling repository.
- Never fetch the guide from the network to check it.

Local publication check: `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. That module lives in this repo (not installer-copied). It asserts the file is self-contained, the inline Training JSON is valid, the install constants match, and the file stays below the strict 500,000-byte (500 KB) budget. If `NEXUS_HUB_PORTFOLIO_ROOT` is set, the suite diffs `<portfolio-root>/nexus-hub/index.html` against the canonical file and fails on unexpected drift. If the env var is unset, that leg is skipped and the rest of the suite still passes.

## Browser verification

The pytest suite parses HTML and JSON; it does not execute JavaScript. Rendered verification is a first-class step, run per phase with the local harness:

```bash
python tests/guides/tools/browser_matrix.py --label phase-7
```

That runs the declared 150-case matrix described above (`render_guide.py` remains for ad-hoc page renders). Local use needs Playwright (`pip install playwright && playwright install chromium`); the required `guide-render` job runs the browser suites fail-closed with `NEXUS_REQUIRE_RENDER=1` and is aggregated into `ci-required`, so a skipped browser is a red check, never a silent pass.

Before a workshop or a portfolio publish, also open the file by hand and check:

- Light and dark themes, including a reload (theme must persist only `light` or `dark`)
- Reduced motion across all four pages, including the static Foundations end states, the paused shooter with its single-step control, and immediate Training terminal output
- Home install copy on the Windows and macOS/Linux tabs, and the verify-command copy cells
- Foundations: eight scenes, correct responsive diagram variant, no pinned overlay, no comparison toggle
- Training: playable shooter controls, the damage fix at `/implement`, vertical movement after `/compare` and its follow-on implementation, terminal output, cumulative explorer, missing-file state, Outline, full screen mode, and a mid-walkthrough URL
- Cheatsheets: every scope readable, jump nav, and a deep link such as `#cheatsheets/explore`
- Keyboard-only path through all four pages

Lighthouse Accessibility is a last-phase human bar, not a mid-plan merge gate.

## Naming and counts (v4.4.2)

- The product is written `Nexus Hub` in every visible string, `aria-label`, and pseudo-element label. `Nexus-Hub` survives only inside `code`, `pre`, `kbd`, `[data-copy]`, and repository links, which is the enumerated allowlist in `tests/guides/test_v442_phase1_foundation.py`; the check is case-insensitive.
- No catalog count is typed by hand. Every count is a `<span data-count="skills|hooks|pretooluse|commands">` marker that `python scripts/stamp_guide_counts.py` rewrites from `data/skills.json`, `catalog/hooks/settings.json`, and `catalog/commands/`; `--check` runs in `make validate` and fails on any stale marker, and `tests/guides/test_guide_counts.py` fails on any bare count phrase.
- Section titles share `.section-title`, driven by `--title-scale` (2.4). Tune the token, never a selector.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the two `<script>` blocks at the bottom (the app shell, then the Training engine after the scene JSON). Class prefixes: `fx-` for Foundations scenes (`fx-hstack` and its `h-` children for the layered harness), `ann-` for the annotated prompt, `seq-` for NexusSeq step primitives, `nht-` for Training, `nag-` for the arcade game, `g-` for the Home guardrails figure, and `cs-` for Cheatsheets. Scene data is `example/training-scenes.json` plus the matching inline JSON block. Do not edit or regenerate the retained Glow Booth fixtures as part of reader-facing Training work.


## Targeted visual refinement after v4.4.5 restoration

The guide retains the complete v4.4.5 teaching content and section order. The token prompt uses its intended typography; the paired image illustration shares its frame and shows the source grid. Harness layer symbols carry the timeline emphasis while explanations remain visible. The Training canvas schedules frames only while running, and resumes from the existing pause state without idle background work. [Verification and screenshots](../../docs/releases/v4/v4.4/development/guide-visual-refinement/verification.md) record content parity, responsive rendering, and lifecycle checks.

The screenshot-selected Home safety and platform sections now use persistent action examples, finite progress animation, larger platform/handoff text, and connected distribution graphics. [Home verification](../../docs/releases/v4/v4.4/development/guide-visual-refinement/screenshot-segments/plan.md) includes before/after screenshots, breakpoint checks, contrast measurements, and content parity.

The Home and Foundations closing Next sections are removed. Their page navigation remains available. The safety figure reuses the transparent Nexus Hub logo, with a gentle float that pauses off-screen and respects reduced motion.

The Foundations prompt examples use Vague Prompt and Engineered Prompt labels. The context example repairs a checkout UI: separate Attachments and Context folder boxes sit below the prompt. Clicking the screenshot opens an enlarged SVG, the illustrative PDF opens a guideline cover and checklist, and the selected asset folder opens an expandable explorer. Native dialogs support Escape, focus return, and keyboard scrolling of the enlarged image. Context Engineering Best Practices shares the section subtitle typography.

The Home platform handoff is an illustrative Claude Code/Codex conversation in the same project workspace. It shows a Nexus Hub plan, Phase 2 interrupted by a usage limit, and Codex resuming the saved work before Phase 3. The transcript windows align on desktop and stack in reading order on mobile.

Context previews stay embedded and offline. Stylesheet whitespace is compacted to stay below 400,000 bytes; browser CSSOM comparison confirms unrelated rules are unchanged. Keep quoted CSS values and comments intact when reformatting.
