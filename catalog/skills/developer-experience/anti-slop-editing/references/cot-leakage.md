# Chain-of-Thought Leakage: Extended Examples

Companion to the "Chain-of-Thought Leakage" family in `SKILL.md`. That section defines the four patterns and the acceptance test; this file carries longer worked examples, the cases that are genuinely ambiguous, and the false positives worth protecting.

## The acceptance test, applied

> Could a reader at HEAD, with no transcript, resolve every reference?

Run it literally. For each referring expression in the draft (a pronoun, a citation, a comparative, a temporal marker), ask what the reader would have to know to resolve it. If the answer is "the conversation where this was written" or "the previous version of this file", it is leakage.

The test has one important limit: it asks whether a reference is *resolvable*, not whether it is *interesting*. A changelog entry saying "renamed `foo` to `bar`" is resolvable by anyone (both names are given) and belongs in a changelog. "Renamed it to the clearer name" is not.

## Dead decision citations

The authoring session had numbered options, a decision log, or a comparison table. The final document cites those numbers, but the thing being cited never shipped.

- Before: "We use the containment metric here (see option 3) rather than the alternative."
- After: "We use containment overlap, `|A n B| / min(|A|, |B|)`, because the prompt is almost always the smaller set."

A subtler form cites a document that exists but does not say what the citation implies:

- Before: "Per the design discussion, this is intentionally fail-closed."
- After: "This is fail-closed: `confine()` throws rather than spawning unwrapped, because a silent downgrade would remove confinement exactly on the machines that could not provide it."

The fix is the same in both cases. Inline the substance and drop the pointer. A citation earns its place only when the target is reachable and says what you claim.

## Temporal vantage

Prose written from the position of someone who watched the change happen, published to readers who did not.

- Before: "The validator no longer rejects bare integers."
- After: "The validator accepts bare integers."
- Before: "This used to live in `utils.py` but was moved here."
- After: (cut it, unless a reader following an old link needs the redirect, in which case say so directly: "Older references may point to `utils.py`.")

**Protected case.** Temporal language is correct whenever the document's job is to describe change. Changelogs, migration guides, deprecation notices, release notes, incident timelines, and "what changed in this version" sections all legitimately say "previously" and "no longer", because their reader is precisely someone comparing two states. Do not strip temporal markers from those. The failure is temporal vantage in a *reference* document, where the reader has only the current state.

## Stack vantage

Prose addressed to a reviewer of the change rather than a reader of the document. It answers "why should you accept this edit?" instead of "how does this work?".

- Before: "Note that this does not change any existing behavior, and all existing tests still pass."
- After: (cut it; that belongs in the pull request description.)
- Before: "I kept the original function signature so nothing downstream breaks."
- After: "The function signature is part of the public API; changing it would break downstream callers." (Only keep this if a reader needs to know the constraint. If it is purely a reassurance to a reviewer, cut it.)

The tell is second-person reassurance or first-person justification in a document whose reader has no stake in the review.

## Justification residue

A paragraph defending a choice against an objection that only ever existed in the authoring session. Nobody reading the final document raised it, so the defense reads as unprompted anxiety.

- Before: "Some might argue that counting code blocks inflates the number unfairly. However, exempting them would create a loophole, and besides, the tokens are real."
- After: "Code fences and tables are counted, because exempting them would make 'move the prose into a code fence' the cheapest way to pass the gate."

Keep the reasoning, drop the argument frame. The rule of thumb: if the paragraph would survive being rewritten as a plain statement of the rule and its purpose, rewrite it that way. If it only makes sense as a rebuttal, the objection belongs in a decision record, not in the reference document.

**Protected case.** A "Common Rationalizations" table, a FAQ, or an explicit alternatives-considered section is not residue. Those are documents whose declared job is to address objections, and the reader arrives expecting them.

## Ordering note

Fix dead citations first. They frequently mask the other three: once you inline what a citation actually said, the surrounding justification residue usually becomes visibly redundant and deletes itself.
