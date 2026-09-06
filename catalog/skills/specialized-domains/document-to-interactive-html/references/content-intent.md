# Content Intent and Decision-Brief Authoring

The contract that decides what the artifact must ACCOMPLISH, resolved before authoring and graded by Gates A, B, and E in `references/visual-qa-rubric.md`.

Every other reference in this bundle governs how the page is BUILT: how wide a band is, how type scales, how a diagram's arrowheads attach, whether a canvas painted. This one governs whether the page was worth building. That distinction is not academic. A real session (2026-08-13, a VectorCAST decision brief) delivered a page that was offline, responsive, browser-verified, and structurally clean, and was nonetheless the wrong artifact: it critiqued a draft the audience had never seen, estimated a reusable commercial platform when a bounded pilot was requested, and argued against an assumption the reader had already granted. Every existing gate passed, because every existing gate asks whether the page WORKS.

## Part 1: The content brief (Gate A input)

Four fields plus an exclusions list, resolved in the Step 5 intake round alongside the color scheme and coverage depth. INFER each from the request and the extracted source first; ask only when inference is unsafe, and ask in ONE batched clarification rather than several. The batched form is what makes this cheap:

> Before I build, I will treat this as a standalone decision brief for readers who have not seen the source. I will preserve your assumption that the corpus is available, estimate a bounded pilot rather than a reusable platform, and compare the three options you named. Is any part of that framing wrong?

That single prompt gives the user one place to correct the whole interpretation, which beats four disconnected questions and beats discovering the mismatch after delivery.

### 1.1 `source_relationship` (BINARY, default `standalone`)

| Value | The output ... |
|---|---|
| `standalone` | is informed by the source and never mentions it. **The default.** |
| `revision-aware` | may explain what changed from a known prior version. |
| `comparative` | intentionally compares sources or versions. |
| `faithful-adaptation` | preserves the source's own order and framing. |

Default to `standalone` unless the user explicitly asked for critique, redlining, version comparison, or change commentary. A source document can be an INPUT without becoming part of the story; transformation and critique are different tasks.

Observable criterion under `standalone`: the visible output contains none of "the original", "the prior draft", "what was right", "what was wrong", or "original preserved", unless the subject matter independently requires those words (a brief ABOUT a document revision legitimately uses them).

### 1.2 `decision_to_enable`

The one choice the reader must be able to make after reading. A page can be accurate, complete, and attractive and still fail by not supporting a decision.

When the request names options to choose among, decision coverage normally spans: what the subject does, the problem it solves, whether the proposed alternative is feasible, expected effort under named assumptions, the available alternatives, comparative cost and ownership, regulatory or operational constraints, a conditional recommendation, and a low-risk proof step that would validate it.

Observable criterion: the opening summary answers the decision question directly, and the body carries evidence for every option named in the recommendation.

### 1.3 `assumptions` (the assumption ledger)

Each stated user assumption, classified:

| Status | Meaning | Authoring consequence |
|---|---|---|
| `accepted` | Part of the task contract. | Build FROM it, in constructive language. |
| `needs-verification` | Plausible, unconfirmed. | Note the dependency once; do not build the narrative on rebutting it. |
| `bounded` | A planning assumption that shapes an estimate. | Name it wherever the estimate appears. |
| `material-risk` | Wrong in a way that changes the decision. | Challenge it, WITH the evidence and the decision consequence. |

Observable criterion: no section heading or lead sentence negates an `accepted` premise. The session's failure is the template to recognize: the user's premise already included agent-led extraction and verification, and the page opened its regulatory section by arguing that uploading documents is insufficient, which rebuts a position nobody took. The constructive form of the same content reads "given a controlled corpus, the agents extract, cross-check, and convert the guidance into operating rules".

### 1.4 `scope_class` (BINARY wherever an estimate is produced)

| Class | Produces |
|---|---|
| `working-demonstration` | The workflow shown on one small representative example. |
| `decision-grade-pilot` | Credible evidence on a real component, revealing the gaps. |
| `controlled-rollout` | The workflow repeated in a defined environment, with governance and review. |
| `reusable-platform` | Support for many products, toolchains, teams, integrations, and long-term maintenance. |

Timeline estimates are extremely sensitive to this boundary, and the classes differ by an order of magnitude. Agent acceleration changes the execution RATE; it does not collapse the scope difference, and treating it as though it does is how a bounded pilot inherited a platform-scale timeline.

Observable criterion: every visible timeline names its scope class and shows at least three planning assumptions (for example codebase count, toolchain count, target hardware, existing tests, CI access, corpus readiness, reviewer availability). A bounded pilot never inherits a reusable-platform estimate.

### 1.5 The design-record block

Record the resolved brief in the output's design-record HTML comment so it is inspectable and checkable:

```yaml
content_intent:
  source_relationship: standalone
  audience_familiarity: low
  decision_to_enable: choose commercial, agentic, or hybrid
  scope_class: decision-grade-pilot
  assumptions:
    - statement: the regulatory corpus is available and controlled
      status: accepted
    - statement: one codebase and one toolchain are in scope
      status: bounded
  exclusions:
    - critique of the source draft
    - internal production metadata
```

## Part 2: Decision-brief authoring rules

These apply when `decision_to_enable` is set. Trigger `decision_brief` mode on comparison, recommendation, selection, or business-case language in the request.

### 2.1 Explain the subject before comparing it (BINARY)

When the output compares a named product or approach against an alternative, a `subject_capability_summary` PRECEDES the comparison and answers: what work does it perform, what evidence or outcome does it produce, why do its users value it, and which parts are deterministic tools versus workflow control or documentation support.

Readers cannot evaluate a replacement for something they cannot describe. Observable criterion: a first-time reader can summarize the subject's role after one section, without the competitor table or the sources appendix.

### 2.2 Highlights answer, they do not preview

In `decision_brief` mode the first content segment gives CONCLUSIONS in question-and-answer form, not a table of contents. Each answer is concise and non-technical, and is supported later in the document.

Observable criterion: each Highlight maps to a later section, and each later section either supports a Highlight or supplies necessary decision context.

### 2.3 Select a comparison visual by the decision, not the metaphor

| Use | When |
|---|---|
| Matrix | Several options across repeated criteria. |
| Stacked bar | Defensible quantities exist. |
| Flow | Costs or effort arise across lifecycle stages. |
| Iceberg | Visible-versus-hidden is ITSELF the decision, AND the hidden categories can be organized. |

Without exact figures, label the comparison qualitative and avoid pseudo-precision. This composes with the data-fidelity rule in `references/figure-reconstruction.md` rather than sitting beside it: an invented magnitude in a cost chart is the same class of fabrication as a bar flat-clamped at the axis maximum.

Observable criterion: a cost visual identifies the options, the criteria, and the direction of the tradeoff, and implies no exact relative magnitude it has no data for.

### 2.4 Show responsibility lanes for a hybrid recommendation (BINARY)

A recommendation that combines systems or teams ships a lane visual naming the work performed by the automated system, the measurements produced by deterministic tools, the decisions retained by qualified people, the artifacts passed between lanes, and the conditions that would trigger a purchase.

"Use a hybrid approach" is a conclusion, not a plan. Observable criterion: every activity in the recommended workflow has ONE primary owner, and every system-generated conclusion with regulatory or financial significance shows its review point.

### 2.5 Hero-content budget (BINARY)

The hero carries at most: one context label, one title, one framing question or subtitle, and one concise answer or recommendation where appropriate. No production notes, preservation labels, internal QA labels, or workflow history.

Observable criterion: every hero element answers one of "What is this?", "Why should I care?", or "What is the main conclusion?". Provenance belongs in the method section, the sources appendix, or the design record. Labels like "Primary-source review" and "Original preserved" are process bookkeeping addressed to the author, not value addressed to the reader.

### 2.6 Credits are unobtrusive AND accessible (BINARY, both directions)

This extends the credits rule in `references/interactive-features.md`; it does not replace it. Attribution stays mandatory.

- Hide the visual credit until hover or keyboard focus on large screens.
- Expose it through a FOCUSABLE control, so keyboard users reach it.
- Provide a touch route, so hover is never the only path.
- Repeat the full attribution in the sources or credits section regardless.

Observable criterion: the credit is not visually prominent on initial load, is reachable by mouse AND keyboard AND touch, and remains present in the source record. Unobtrusive is not permission to make required information unreachable, which is why this rule is binary in both directions.

### 2.7 Competitor criteria are reader-centered

Default criteria: what it provides, best fit, relative cost or pricing model, internal work required, regulatory or qualification support, and the important limitation. Engineering feature detail and certification terminology move to an expandable note or the appendix unless they change the recommendation.

Observable criterion: every comparison label is understandable without domain knowledge, or the term is defined immediately where it appears.

## Part 3: Visual contracts (Gate B input)

A visual is not successful because it is attractive or animated. It is successful when it makes a relationship easier to understand than prose alone. The session's first VectorCAST graphic was an orbit diagram that rendered correctly, sized correctly, contrasted correctly, painted correctly, and explained nothing.

### 3.1 The contract

Record one per MAJOR visual in the design record, BEFORE implementation:

| Field | Answers |
|---|---|
| Question | What reader question does this visual answer? |
| Message | What single conclusion should the reader retain? |
| Encoding | What do position, color, size, sequence, and connection mean? |
| States | What changes during interaction? |
| Trigger | What user action causes each state? |
| Fallback | What does a static or reduced-motion reader see? |
| Evidence | Which claims or data support it? |

**The subtractive test.** Remove the visual. If the section loses no explanatory value, redesign the visual or OMIT it. Omission is an explicitly permitted, frequent, correct outcome: a concise table or process flow beats an elaborate interactive graphic whenever the relationship is already clear. A gate that can only demand more visual work is a cost generator, not a quality control.

```yaml
visual_contracts:
  - section: vectorcast
    question: How does the tool turn code into review-ready evidence?
    message: The value is the controlled chain, not any one measurement.
    encoding: left-to-right sequence is pipeline order; fill means the stage is active
    states: five synchronized scroll states
    trigger: the matching prose stage entering the viewport
    fallback: all five stages visible as a static process
    evidence: the vendor's documented workflow, cited in sources
```

### 3.2 Scrollytelling state tables

Scroll animation earns its cost only when the visual transition matches the SEMANTIC transition in the text. Each scrollytelling section declares a state table:

| Step | Prose claim | Visual change | Reader takeaway |
|---|---|---|---|
| 1 | The unit is prepared for testing | Inputs and harness stage activate | Testing begins by controlling the unit |
| 2 | The unit runs in the intended environment | Execution stage activates | Environment matters to the evidence |
| 3 | Objective measurements are collected | Coverage stage activates | The tool measures; the agent does not |
| 4 | Tests connect to requirements | Traceability stage activates | Evidence must show what each test proves |
| 5 | Artifacts are packaged repeatably | Evidence package completes | Repeatability is part of the value |

Step 9's browser QA scrolls to EVERY declared step and verifies the expected state is active, under reduced motion and keyboard navigation too. This composes with rubric criterion 11 rather than duplicating it: criterion 11 asks whether the surface painted at all, the state table asks whether it painted the RIGHT state.

## Verification

- [ ] The design record carries a `content_intent` block with `source_relationship`, `decision_to_enable`, `assumptions`, `scope_class`, and `exclusions`.
- [ ] Under `standalone`, the visible output carries none of the banned draft-reference phrases.
- [ ] No section heading or lead sentence negates an `accepted` assumption.
- [ ] Every visible timeline names its scope class and at least three planning assumptions.
- [ ] A comparison of a named subject is preceded by its capability summary.
- [ ] The comparison visual matches the decision shape per the selection table, and a qualitative comparison is labelled as such.
- [ ] A hybrid recommendation ships responsibility lanes with one owner per activity.
- [ ] The hero carries no production metadata, and every hero element answers one of the three questions.
- [ ] Image credits are unobtrusive on load and reachable by mouse, keyboard, and touch, and appear in full in the credits section.
- [ ] Every major visual has a recorded `visual_contract` and survives the subtractive test.
- [ ] Every scrollytelling section declares a state table, and Step 9 verified each declared state.

## Related

- `references/visual-qa-rubric.md` - defines Gates A, B, and E that grade this contract, and the four QA layers they belong to.
- `references/interactive-features.md` - the placement-role taxonomy and the credits rule that 2.6 extends.
- `references/scroll-scrub.md` - the cinematic protocol whose sections carry the 3.2 state tables.
- `references/figure-reconstruction.md` - the data-fidelity rule that 2.3's qualitative-labelling rule composes with.
