# v4.4.5 Phase Contract -- Guide Mockup Integration

**Plan**: [v4.4.5-guide-mockup-integration.md](../../plans/v4.4.5-guide-mockup-integration.md)
**Artifact**: `guides/website/nexus-hub-guide.html`

This is the running record for v4.4.5: what each phase changed, which earlier assertions it superseded, what it cost in bytes, and which mistakes it made. The superseded-assertion register exists because several tests in this suite pin a literal implementation string, and a literal that is silently repointed is a test that stopped meaning anything.

## 1. Scope

Two kinds of change, kept apart on purpose. Precise corrections to scenes that already work (Phases 1 to 4), and three full scene rebuilds from operator-supplied mockups (Phases 5 to 7). The mockups are read as sources of teaching structure, not as markup to paste: they are standalone pages built around interactive controls, and the same review round asks for fewer hidden panels rather than more.

## 2. Superseded assertions

| # | Assertion | Pinned | Superseded by | Recorded |
|---|---|---|---|---|
| S1 | `test_the_segment_carries_both_benefits` asserted `NexusSeq.state(fig).total == 3` on the portability figure | that the figure reveals itself in three steps | Phase 1 retired the reveal on instruction; the assertion is INVERTED to require no `data-seq-root` | Phase 1 |
| S2 | The same test counted `.ph-fan span` | the fan's connectors were bare `span` triangles | Phase 1 rebuilt each connector as a `.ph-lane` carrying a line, a travelling dot, and the triangle | Phase 1 |
| S3 | Eight rules declared a hand-written `11px`, `11.5px`, or `12px` tag size | that each tag owned its own number | Phase 2 moved them all onto one `--fx-tag` token | Phase 2 |
| S4 | `test_the_flaws_sit_beside_the_vague_prompt` asserted the flaws sit BESIDE the prompt | the v4.4.4 arrangement, itself a correction of the v4.4.3 one | Phase 3 INVERTED it: full-width prompt, flaws in a 2x2 grid below. Third arrangement in three rounds, each requested | Phase 3 |
| S5 | `PARTS = ("goal", "material", "done", "format")` and the `<dt>` and flaw-text assertions in the broad module | the pre-v4.4.5 vocabulary, where `Done` named the finish line | Phase 3 renamed the parts; `Goal` now names the finish line, and the old four are asserted ABSENT | Phase 3 |

## 3. Mistakes this plan made, and what they cost

### 3a. Two failed attempts to share one vendor mark (Phase 1)

The four platform boxes needed the same marks the compatibility rail already carries. Sharing them through `<symbol>` and `<use>` was the cheap option and it failed twice, in two different ways, and neither failure announced itself.

First, cloning the Gemini mark rendered a **blank box**. A `<use>` copies the symbol's content into a shadow tree, and Chromium resolves a `url(#id)` mask reference against that tree first, so the reference found the cloned mask instead of the real one and painted nothing. Second, hoisting the mask and filters to document level, which is the documented workaround, rendered an unmasked **square**: the blurred colour blobs with no mask to cut them into the mark's shape.

Both were only visible by LOOKING at the page. The element was present, the reference was correct, and a presence assertion passed in both states. What the test asserts now is a painted box larger than 8px, because that is the property that failed.

The third failure was the useful one. Rewriting the rail's chips to point at shared symbols tripped `test_home_lists_the_five_approved_platforms_from_ledger_bytes`, whose message says re-approval is required rather than a ledger update. That guard is correct and it settled the design: the approved bytes stay exactly where they were approved, and the figure gets a COPY. Copying costs about 12 KB, most of it the Gemini artwork. The alternative was to redraw a vendor's logo to suit a rendering bug.

The copy carries the mark's own internal ids, so they are namespaced per instance. `test_ids_are_unique` caught that immediately, which is the one part of this that worked first time.

### 3b. Measuring a hidden element against a real one (Phase 1)

The first centring measurement reported a triangle 530px off centre inside a 720px figure, which is not a thing that can happen. Below the collapse breakpoint the fan hides its extra lanes, a hidden lane reports a zero rect, and the check was comparing that zero rect against a real box. The figure was correct and the measurement was not.

The lesson is narrow and worth keeping: **a geometry check must filter for visibility before it compares.** The version in the test does, and it also asserts what the narrow layout is actually for, which is a single centred arrow rather than four arrows over a two-column list, where a per-box arrow would point at the gap between two boxes.

### 3c. A dead CSS rule found while measuring Phase 2 (pre-existing)

Phase 2's measurement reported `.fx-tokfig-cap` at 16px when every other block tag had moved to
23px. The rule is selected as `.fx-copy .fx-tokfig-cap`, and the captions it was written for live
in `.fx-diagram`, so it has matched NOTHING since the figure moved. Both token captions have been
rendering as plain 16px sentence-case body text.

This is why the review's screenshot 4 asks for one of them to be "styled like 'Vague'": it is
asking for the styling the rule already describes and never applied. Phase 4 owns the fix, because
that is the phase that renames the captions.

The class-coverage guard added in v4.4.3 could not catch this. It proves every class USED in the
markup has a style rule; it says nothing about whether a rule's selector matches anything. The two
questions are different and only one of them was being asked.

## 4. Byte ledger

| Phase | Change | Bytes | Running total |
|---|---|---:|---:|
| start | v4.4.4 final | | 366,529 |
| 1 | portability figure: reveal retired, flow pulse, four copied marks, full-width strip | +14,090 | 380,619 |
| 2 | one tag-size token; every Foundations block tag doubled | +105 | 380,724 |
| 3 | prompt parts renamed Query/Context/Goal/Format; vague prompt full width, flaws 2x2 | +29 | 380,753 |

Counts are of the file as stored (LF). The worktree copy is CRLF under `core.autocrlf`, so an on-disk byte count runs about 5 KB higher and is not the ledger's number.
