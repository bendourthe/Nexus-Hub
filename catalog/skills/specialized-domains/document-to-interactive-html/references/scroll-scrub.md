# Cinematic Scroll-Scrub Protocol

The opt-in cinematic surface: a scroll-scrubbed stage where scrolling drives a continuous camera movement through the document's own sections rather than triggering discrete reveals. It is the most expensive thing this skill can build - in bytes, in assets, and in the reader's tolerance for motion - so every rule below is about keeping it honest, offline, and cheap enough to justify.

## 1. When cinematic applies

Cinematic is **opt-in only**, reachable three ways and no other:

- `--interactivity cinematic` on the command line.
- The cinematic choice in the up-front interactivity menu (its fourth option).
- A confirmed proposal under `rich`: after extraction, when the content genuinely suits a continuous fly-through, the agent MAY propose scroll-scrub as the run's signature scrollytelling pattern. Proposed, priced, and confirmed - never silently selected. A headless or non-interactive run never selects it.

It **composes with** the RICH patterns rather than replacing them. Interactive charts stay interactive, the five-point minimum interaction budget still applies in full, and a cinematic page that shipped a static chart has failed the budget, not transcended it.

There is no separate cinematic command and no separate cinematic skill - no rival slash command exists or should be created for this. Cinematic is a level of `/presentify`, because the input contract is unchanged: existing files in, one offline interactive site out.

## 2. Job fidelity - present the document, do not invent a brand

Section order, headings, and copy come from the extracted content model (deck / report / compile / project). The camera grammar is PRESENTATION over those existing sections; it is not a narrative of its own.

Do **not** run a blank brand-industry interview and generate sections from the answers. That is a different product: it authors a new story rather than presenting an existing document, and it is exactly the boundary that keeps this a presentify level instead of a fork. When cinematic is chosen, the only questions worth asking are the ones that cannot be defaulted (see section 5), and every one of them is about how to MOVE through the sections the document already has.

## 3. Size and cost gate - state the numbers BEFORE building

Cinematic assets are the largest thing this skill embeds, and the output must stay a single offline file, so the size estimate is not a formality. BEFORE generating or embedding anything, state:

- **Clip count** and approximate duration per clip.
- **Approximate base64 / HTML size impact.** Base64 inflates binary by ~33%, so a 2 MB clip lands as ~2.7 MB of markup. State the projected total file size.
- **Stock-video key requirements**, if any clip would come from the consent-gated stock tier.
- **QA-depth cost**, since a cinematic build multiplies the render-loop's capture work.

Then get an explicit go / no-go. Prefer short clips, and prefer stills-only when the estimate is large - a stills-only cinematic build is a legitimate, good-looking outcome, not a degraded one. Cross-link `[[ai-billing-safeguards]]` for the hard budget controls.

A useful rule of thumb: past roughly 15-20 MB the single-file guarantee stops being a feature and becomes a delivery problem (mail gateways, browser memory on mobile). If the estimate crosses that, say so and offer stills-only.

## 4. Asset sources - the hard boundary

**Allowed:**

- User-supplied local clips and stills.
- Tier 1 procedural stills (generated inline, commercial-safe by construction).
- Tier 2 consent-gated license-free stock, including the existing stock-video path (Pexels-only, needs a key, degrades with a note).
- Tier 3 **LOCAL** AI stills, used as posters only.

**Forbidden, without exception:**

- Any hosted image or video generation service. This is the MCP Registry Policy's generation-as-service Hard-No, and it applies to CLIs and APIs equally. A cinematic build never calls a paid generation endpoint, never shells out to a vendor CLI, and never prints such a command for the user to run.
- Runtime hotlinks. Every asset is embedded; the delivered file makes zero network requests.
- Multi-file sibling asset layouts. A page that needs `clip-01.mp4` next to it is not a self-contained output, and the offline guarantee is the point.

## 5. Seam and pacing protocol

When chaining local clips, continuity is a geometry problem, not a taste problem:

- **Hand off actual rendered boundary frames.** A connector between two clips must start from the LAST RENDERED FRAME of the outgoing clip and end on the FIRST RENDERED FRAME of the incoming one - not from the original still either clip was built from. Those two images differ, and the difference reads as a visible jump exactly at the moment the reader is paying most attention.
- **A short crossfade as insurance.** Even with correct frames, a 150-250 ms cross-dissolve at the seam absorbs sub-pixel and color-space mismatch. It costs nothing and hides the class of error you cannot fully eliminate.
- **Per-section `scroll` and `linger`.** `scroll` is how much page distance a section's clip consumes; `linger` is a mid-scene settle where scroll progress advances but the clip barely moves, so the reader can actually read the section's copy. Without a linger the text scrolls past under a moving camera and nobody reads it.
- **Local encode notes** (only for files the user already has): muted, a small GOP (`-g 4` or similar) so seeking is cheap, and `+faststart` so the first frame is available immediately. A large-GOP clip seeks badly and makes the scrub feel broken even when the engine is correct.

The only questions worth asking when cinematic is chosen, after extraction:

1. **Camera grammar** - forward walkthrough, dive-and-hop, or locked glide - framed as presentation grammar over the existing sections.
2. **Video assets or stills-only.**
3. **Confirmation of the size / cost estimate** from section 3.

## 6. Stills-only fallback (and the reduced-motion path)

When no video exists, or under `prefers-reduced-motion: reduce`, scroll drives a still crossfade plus a gentle scale only. **No video element is created and no clip is fetched or decoded.** This is not a lesser mode bolted on afterwards; it is the mode the engine is built around, with video as the enhancement.

Observable criterion: scrolling never produces vestibular video scrub for a reduced-motion user. Verify it, do not assume it - set the emulation and scroll.

## 7. Accessibility

- **Real section copy stays linearly readable.** The cinematic layer is behind or around the text, never instead of it. A screen reader encounters the document's sections in order, with no dependence on scroll position.
- **Route and nav jumps work.** An anchor jump to a section lands correctly with the stage in the right state, and `scroll-margin-top` applies as it does everywhere else.
- **Keyboard reaches everything.** No control is scroll-only.
- **The reduced-motion path is documented and tested**, per section 6.

## Verification

- [ ] Cinematic was reached only by an explicit choice or a CONFIRMED rich-level proposal, and the design record notes which - never a silent selection.
- [ ] The size / cost estimate was stated with clip count, projected base64 size impact, key requirements, and QA-depth cost, and a go / no-go was obtained BEFORE any asset was generated or embedded.
- [ ] No hosted generation service was called, and no vendor generation command was printed for the user to run.
- [ ] Every asset is embedded; the delivered `.html` is one file and makes zero network requests.
- [ ] Section order and copy come from the extracted content model; no invented brand narrative.
- [ ] Under `prefers-reduced-motion: reduce`, no video element is created - verified by emulating the preference and scrolling, not by reading the code.
- [ ] The five-point interaction budget and chart interactivity still hold on top of the cinematic layer.
- [ ] `assets/scroll-scrub-engine.js` was adapted rather than copied verbatim, and carries no vendor, product, or upstream repository name.

## Related

- `assets/scroll-scrub-engine.js` - the zero-dependency engine implementing this protocol: data-URI / Blob clip loading, seam crossfade, per-section scroll + linger, mobile seek-coalescing, and the stills-only reduced-motion path.
- `references/interactive-features.md` - the interactivity spectrum this level sits above, the scrollytelling catalog it joins, and the five-point interaction budget it must still satisfy.
- `references/visual-qa-rubric.md` - the per-segment grading a cinematic build is verified against, including the reduced-motion check.
- `[[ai-billing-safeguards]]` - the hard budget controls behind the size / cost gate.
