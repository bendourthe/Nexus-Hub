---
name: anti-slop-editing
description: "Edit prose to remove AI-slop patterns (filler, robotic rhythm, chatbot leftovers, mannered prose, the therapist-voice register) and keep the writer's voice, or detect slop without rewriting. For 'de-slop this', 'make it less AI-sounding', 'does this read as AI', 'strip the chatbot leftovers', 'remove the mannered prose'. SKIP general writing (use writing-editing)."
summary_l0: "Remove named AI-slop prose patterns while preserving voice, or detect slop without rewriting"
overview_l1: "This skill acts as a sharp human editor that strips the recognizable AI-slop signature out of prose while protecting the writer's own voice. It carries a catalog of 20+ named prose-slop patterns (binary contrasts, throat-clearing openers, faux-insight setups, importance puffery, weasel attribution, synonym cycling, robotic rhythm, fake-profound kickers, formatting slop, and more), each with a quoted smell and a concrete before/after fix. It runs in two modes: Edit (default) makes the minimum effective edit and returns the edited draft plus a What-changed note; Detect names each pattern, quotes the offending line, and gives a short fix without rewriting, scoring, or guessing AI authorship. It preserves 3-5 identified voice signals, leaves strong human sentences alone, and grades its own output against a rubric before returning. Trigger phrases: de-slop this, make it less AI-sounding, does this read as AI, remove AI patterns, audit this draft for slop."
version: 1.0.0
author: Benjamin Dourthe
license: MIT
category: developer-experience
language: Multi-language
tags: [prose, editing, anti-slop, writing, voice, ai-detection, style]
tools_required: [Read, Write, Edit]
---

# Anti-Slop Editing

Remove the recognizable "AI slop" signature from prose while preserving the writer's voice. The most common failure mode of machine-drafted (and machine-edited) text is a set of tells: binary "not just X, it's Y" contrasts, throat-clearing openers, importance puffery, metronomic sentence rhythm, and a reach-for-depth closing line. This skill names those patterns, quotes each smell, and gives a concrete before/after fix.

It runs in two modes. Edit (the default) rewrites with the minimum effective touch and reports what changed. Detect names the patterns without rewriting, so a writer keeps full control of their own draft. In both modes the goal is the same: cut the slop, keep the human.

## When to Use This Skill

Use this skill when:

- The user asks to make text "less AI-sounding", "sound less like a robot wrote it", or "more human".
- The user asks whether a draft "reads as AI", "is AI slop", or wants a draft "audited for slop".
- The user says "de-slop this", "remove the AI patterns", or "cut the filler and cliches".
- A draft the agent itself produced needs a final pass to strip its own tells before it ships.

**When NOT to use**:

- For general writing, editing, structure, clarity, or proofreading of a document that is not specifically about the AI-slop failure mode, use `writing-editing`.
- For producing audience-appropriate technical documentation from scratch (README, API docs, guides), use `technical-writer` or `user-documentation`.
- For the visual "looks AI-generated" failure mode in UI (centered hero, gradient buttons, emoji bullets in an interface), use `hallmark-design`.

## The Two Modes

The skill is invoked in one of two modes. The default (no mode stated) is Edit.

| Mode | Intent | Output |
|---|---|---|
| Edit (default) | Rewrite the draft with the minimum effective edit that removes slop and preserves voice. | The edited draft, followed by a "What changed" list: each pattern removed and the one-line reason. |
| Detect | Find and name the slop without changing the draft. | A findings list: for each hit, the pattern name, the quoted offending line, and a short suggested fix. No rewrite, no score, no AI-authorship verdict. |

Detect mode has a hard rule: it never rewrites the draft, never assigns a numeric "AI probability" score, and never claims to know whether a human or a machine wrote the text. It reports checkable, named evidence only. "This line uses a binary contrast" is checkable; "this is 80% AI-written" is a guess, and guesses are out of scope.

## Instructions

Follow these steps in order for every request.

1. **Confirm the mode.** Default to Edit. Switch to Detect when the user asks to find, name, audit, or flag slop without a rewrite ("what's slop here", "point out the AI tells", "don't rewrite it, just show me").
2. **Read the whole draft first and identify 3-5 voice signals to preserve.** Note the writer's characteristic moves before touching anything: sentence length preference, humor, directness, technical register, a recurring turn of phrase, first-person candor. These are protected. See "Voice-Preservation Discipline" below.
3. **Scan for the named patterns** in the catalog below, then against the extended register catalog in `references/cliche-patterns.md` (the reflective and faux-reveal registers, emphatic negation, performative honesty, the stranded auxiliary, chatbot leftovers, and mannered prose). Mark every hit with its pattern name and the exact line, and note its class: judgment (flag, cut only when it adds nothing) or defect (always remove).
4. **Run the deterministic detector as a floor, not a ceiling.** `python scripts/detect_prose_cliches.py <file>` (or `-` for stdin; `--json` for machine output) reports the patterns it encodes with line, column, and class: `defect` for chatbot leftovers and forbidden Unicode punctuation, `advisory` for the registers, the spaced-hyphen connector, and the three rhythm rules. In Detect mode run it first and fold its findings into your own reading; in Edit mode run it after editing as a check. It is stdlib-only and offline, exits zero by default, gates only with `--fail-on defect`, ignores quoted mentions, and skips list items in the rhythm rules. It catches what it encodes and nothing else: mannered prose and every judgment call about voice stay with you, so a clean detector run is not a clean draft.
5. **Consult the word and phrase lists** in `references/slop-wordlist.md` for banned words, often-empty adverbs, and empty phrases. Apply them with judgment, not as a hard lint: cut a word when it adds nothing, keep it when it carries real emphasis, contrast, uncertainty, or the writer's spoken rhythm.
6. **Act on the mode.**
    - Edit: make the minimum effective edit. Fix the flagged lines, leave strong human sentences untouched, and do not reach for a "better" word where the writer's word already works. Then assemble the "What changed" list.
    - Detect: produce the findings list (pattern name, quoted line, short fix) and stop. Do not rewrite.
7. **Self-check before returning.** Grade the output against the rubric in `references/self-check.md`. If any check fails, fix it and re-grade. Repeat until every check passes. This happens inside this one agent; do not spawn a separate evaluator.
8. **Return the result** in the mode's output shape.

## Named-Pattern Catalog

Each entry gives the pattern name, the smell in quotes, and a concrete before/after fix. This catalog is the core of the skill. In Detect mode, cite the pattern by name.

### Binary contrasts

Smell: "It's not X, it's Y" or "not just X, but Y" used to manufacture false emphasis.

- Before: "This isn't just a linter. It's a revolution in how you write code."
- After: "This linter catches the mistakes your compiler misses."

### Throat-clearing openers

Smell: a warm-up phrase that delays the actual sentence. "In today's fast-paced world," "When it comes to X," "At its core,".

- Before: "In today's fast-paced world, developers need fast tools."
- After: "Developers need fast tools."

### Faux-insight setups

Smell: a phrase that promises a revelation it does not deliver. "Here's the thing:", "The truth is,", "What most people miss is".

- Before: "Here's the thing: tests catch bugs."
- After: "Tests catch bugs."

### Colon reveals

Smell: a dramatic colon setup for a one-word or short payoff. "The result: chaos." "One word: speed."

- Before: "The outcome was clear: failure."
- After: "The deployment failed."

### Superficial analysis (trailing -ing clauses)

Smell: a comma then an "-ing" clause that restates the sentence as if adding analysis. "..., highlighting the importance of testing." "..., underscoring the need for speed."

- Before: "The build broke, highlighting the importance of CI."
- After: "The build broke because CI was not running."

### Importance puffery

Smell: telling the reader something matters instead of showing it. "It's important to note that", "crucial", "vital", "pivotal", "game-changing".

- Before: "It is important to note that caching is crucial for performance."
- After: "Caching cut the response time from 400ms to 40ms."

### Weasel attribution

Smell: an unsourced appeal to authority. "Experts say", "studies show", "it is widely believed", "many argue".

- Before: "Experts say microservices scale better."
- After: "Microservices let each service scale independently, at the cost of network latency between them."

### Fake-strong verbs

Smell: an inflated verb doing the work of a plain one. "delve", "unlock", "unleash", "harness", "supercharge", "leverage".

- Before: "Let's delve into how this unlocks your team's potential."
- After: "Here is how the team uses it."

### Synonym cycling

Smell: the same idea restated in two or three near-synonyms for padding. "fast, quick, and speedy", "clear, obvious, and evident".

- Before: "The API is fast, quick, and responsive."
- After: "The API responds in under 50ms."

### Negative listing

Smell: defining a thing by a pile of what it is not. "This is not a fad, not a gimmick, not a trend."

- Before: "This is not a hack, not a workaround, not a shortcut."
- After: "This is the supported way to do it."

### Dramatic fragmentation

Smell: sentence fragments used for manufactured punch. "And that changes everything. Completely. Forever."

- Before: "The results were in. And they were staggering. Truly."
- After: "The results were clear: a 3x speedup."

### Robotic rhythm (three countable rules)

Smell: every sentence the same length and shape, so the prose reads metronomic and flat. "Metronomic" is not checkable on its own, so this entry states three rules with thresholds; the agent and the offline detector apply the same numbers.

1. **Echoing sentence runs**: two or more consecutive sentences that share the same four-word skeleton (the same four words in the same order after dropping articles). "The tool is fast. The tool is simple." trips it.
2. **Repeated sentence openers**: three or more consecutive sentences that start on the same non-function word (a word other than a, an, the, and, but, or, so, it, this, that, there). "Tests catch bugs. Tests document intent. Tests slow you down." trips it.
3. **Stacked rhetorical questions**: two or more consecutive sentences that are questions. "Why does it matter? What does it cost?" trips it; the `Rhetorical setups` entry below covers the single question posed only to be answered.

A run that trips a rule is a flag, not an automatic cut: parallel structure is sometimes the point. In Edit mode, break the run by varying length or merging; in Detect mode, quote the run and name the rule number.

- Before: "The tool is fast. The tool is simple. The tool is free. The tool is here."
- After: "The tool is fast and simple, and it is free. Try it."

### Rhetorical setups

Smell: a question posed only so the text can answer it. "But what does this mean for you?" "So why does this matter?".

- Before: "But what does this actually mean? It means faster builds."
- After: "This means faster builds."

Two or more questions in a row are counted separately under rule 3 of `Robotic rhythm` above.

### Fake-profound kickers

Smell: a closing line reaching for depth it did not earn. "And that makes all the difference." "Because in the end, it is about people."

- Before: "Ship early, ship often. Because that is what matters."
- After: "Ship early and often so you get feedback sooner."

### Summary-recap endings

Smell: a closing paragraph that restates what the reader just read. "In conclusion, we have seen that...", "To sum up,".

- Before: "In conclusion, we have seen that caching, batching, and indexing all help."
- After: (cut it; end on the last real point, or add one concrete next step.)

### Formatting slop

Smell: emoji bullets, bold on every other phrase, Title Case On Every Heading, and a bulleted list where a sentence would do.

- Before: a five-item bulleted list, each item two words, each with a leading emoji.
- After: one sentence, or a list only where the items are genuinely parallel and worth scanning.

### Em-dash discipline

Smell: em-dashes and clause-joining spaced hyphens sprinkled through the text as an all-purpose connector.

- Before: "The tool is fast - really fast - and it is free."
- After: "The tool is fast (really fast), and it is free."

This project sets a firm ceiling on this pattern, stronger than a generic "one or two em-dashes are fine" guideline. The rule here: no em-dashes at all, and no clause-joining spaced hyphens (the " - " connector) either. Replace them with parentheses, commas, colons, or separate sentences. Prose stays ASCII-only: straight quotes, hyphens, and "..." for ellipsis, never the Unicode punctuation variants. This keeps output consistent with the project Communication Style rules and avoids encoding corruption on Windows.

### Chatbot leftovers (defect, never a matter of taste)

Smell: assistant-role text from a conversation leaking into a document. "As an AI language model, ..." "Here is the revised version:" "I hope this helps." "Certainly!" "Great question."

- Before: "Certainly! Here is the revised version of your deployment guide. I hope this helps."
- After: (cut entirely; the guide begins at its first heading.)

This is the one catalog entry with no judgment call. Every other pattern is flagged and weighed against voice; a chatbot leftover is removed in Edit mode without asking and named as a defect in Detect mode, because it announces that a document was pasted from a chat window and never read.

### Reflective and faux-reveal register

Smell: the voice of a counsellor or a confessional essayist applied to a subject that has no inner life, and its companion move, staging an ordinary fact as a disclosure. "Sit with that for a moment." "That is worth naming." "That is not nothing." "You already know this." "Here is the twist." "Turns out, ..." "X is dead."

- Before: "Turns out, the cache was never enabled. Sit with that for a moment."
- After: "The cache was never enabled, so every request hit the database."

This entry names the family. The full set, with one original before and after pair per pattern and each pattern's class (judgment or defect), lives in `references/cliche-patterns.md`, alongside emphatic negation, performative honesty, the stranded auxiliary, and mannered prose. These registers are judgment calls: a writer may sit with a feeling on purpose, so flag and quote rather than auto-cut, and apply the voice-preservation discipline in full.

For the full banned-word, empty-adverb, and empty-phrase lists that back this catalog, see `references/slop-wordlist.md`. For the extended register catalog, see `references/cliche-patterns.md`.

## Chain-of-Thought Leakage (Authoring-Session Vantage)

The catalog above catches slop at the sentence level. This family catches it at the level of *vantage*: prose written from the position of the person who authored the change, published to readers who only ever see the result. The patterns below are not clumsy sentences. They are well-formed sentences that silently assume the reader watched the document get written.

The acceptance test for the whole family:

> Could a reader at HEAD, with no transcript, resolve every reference?

Apply it to each referring expression. If resolving one requires the authoring conversation or the previous version of the file, it is leakage.

### Dead decision citations

Smell: a citation whose referent never shipped. "(decision 3)", "(see option B)", "per the earlier analysis" pointing at something that exists only in the authoring session.

- Before: "We use the containment metric here (see option 3) rather than the alternative."
- After: "We use containment overlap, `|A n B| / min(|A|, |B|)`, because the prompt is almost always the smaller set."

### Temporal vantage

Smell: "used to", "no longer", "previously", "now" describing a state transition no reader at HEAD can observe.

- Before: "The validator no longer rejects bare integers."
- After: "The validator accepts bare integers."

Legitimate in changelogs, migration guides, deprecation notices, and incident timelines, whose reader IS comparing two states. The failure is temporal vantage in a reference document.

### Stack vantage

Smell: prose addressed to a reviewer of the change rather than a reader of the document. Reassurance about scope, backward compatibility, or test status.

- Before: "Note that this does not change any existing behavior, and all existing tests still pass."
- After: (cut it; that belongs in the pull request description.)

### Justification residue

Smell: a paragraph defending the choice against an objection nobody reading the final document raised. Often opens "Some might argue" or "One could object".

- Before: "Some might argue that counting code blocks inflates the number unfairly. However, exempting them would create a loophole."
- After: "Code fences and tables are counted, because exempting them would make 'move the prose into a code fence' the cheapest way to pass the gate."

A Common Rationalizations table, a FAQ, or an alternatives-considered section is not residue: those documents exist to address objections, and the reader arrives expecting them.

Fix dead citations first. They frequently mask the other three, because inlining what a citation actually said tends to make the surrounding justification visibly redundant. Longer worked examples, the ambiguous cases, and the false positives worth protecting are in `references/cot-leakage.md`.

## Voice-Preservation Discipline

The catalog tells you what to cut. This section tells you what to protect. A de-slop pass that flattens the writer into generic "clean prose" has failed, even if every named pattern is gone.

- **Identify 3-5 voice signals before editing.** Sentence-length preference, humor, bluntness, technical density, first-person candor, a signature phrase. Write them down (internally) and treat them as constraints.
- **Make the minimum effective edit.** Change what is slop. Leave the rest. Do not rewrite a sentence that already works just to impose your own phrasing.
- **Leave strong human sentences alone.** A short, punchy, imperfect line that carries the writer's personality is not slop. Resist "improving" it.
- **Keep useful edge and character.** Opinions, mild profanity, a dig, an aside, a rhetorical flourish the writer clearly meant: these are voice, not slop. Cut the machine tells, not the human ones.
- **When in doubt, prefer the smaller edit** or, in Detect mode, flag it as optional and let the writer decide.

## Self-Check Loop

Before returning any result, grade it against the rubric in `references/self-check.md`. If a check fails, fix the output and grade again. Loop until every check passes. All of this happens inside this single agent; there is no separate evaluator agent and no external call.

These four quality surfaces are distinct and do not replace each other:

- The **deterministic detector** (`scripts/detect_prose_cliches.py`) finds the encoded patterns offline with line and column, before the model reads in Detect mode and after it edits in Edit mode. It is a floor: it never sees mannered prose or a voice judgment.
- The **self-check loop** (`references/self-check.md`) grades the CONTENT of a specific edit or detection at runtime, and drives the fix-and-recheck loop above.
- The **Verification** section below checks OBSERVABLE ARTIFACTS after authoring the skill (files exist, checks pass).
- The **`evals/trigger-cases.json`** file checks ROUTING (that a de-slop request reaches this skill and not `writing-editing`). It is consumed by the trigger-eval runner, not read at edit time.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The draft is short, it can't have slop." | A two-sentence draft can open with a throat-clearing phrase and close with a fake-profound kicker. Length does not immunize prose against the named patterns; scan it anyway. |
| "The user wrote it, so I should not touch their voice." | Edit mode is explicitly a rewrite request. Preserving voice means keeping the 3-5 voice signals, not refusing to cut the machine tells. Detect mode exists precisely for when the user wants zero rewriting. |
| "I'll just tell them it reads about 70% AI." | Detect mode forbids authorship scores and guesses. A probability is unfalsifiable; a named pattern with a quoted line is checkable. Report the evidence, not a verdict. |
| "A couple of em-dashes read naturally, the source guideline even allows one or two." | This project sets a firm ceiling: no em-dashes and no clause-joining spaced hyphens at all. Parentheses, commas, colons, or separate sentences carry the same break and stay ASCII-safe. |
| "The banned-word list says cut 'robust', so I'll cut every instance." | The word lists are judgment guidance, not a lint. "Robust" in "robust error handling" describing real retry logic is fine; cut it only when it is empty praise. Flattening every listed word damages legitimate voice. |
| "The phrase 'no longer validates X' is accurate, so it is not slop." | Accuracy is not the test; resolvability is. A reader at HEAD cannot see the state you are contrasting against, so the sentence spends words on a comparison they cannot make. Accurate in a changelog, leakage in a reference doc. |
| "There's slop, so I should rewrite the whole thing cleanly." | The minimum effective edit is the rule. A wholesale rewrite that removes slop AND the writer's character has traded one failure for another. Change what is slop; leave what works. |
| "The essay sits with a feeling on purpose, so the reflective register is fine here and I should leave every instance." | It may be. That is exactly why the register is a judgment class: flag each instance and quote it, then keep the ones the writer clearly meant and cut the ones that are templated warmth. Neither "leave all" nor "cut all" is the rule; the per-instance call is. |
| "'I hope this helps' at the end is friendly, not slop." | In a chat reply it is a sign-off. In a shipped document it is a chatbot leftover, the one defect class in the catalog, and it tells the reader the text was pasted from a conversation and never read. Remove it without asking. |

## Verification

- [ ] The mode is explicit in the response (Edit or Detect), and Detect output contains no rewritten draft, no numeric score, and no AI-authorship claim.
- [ ] In Edit mode, the output includes a "What changed" list naming each pattern removed.
- [ ] Every flagged item cites a named pattern from the catalog and quotes the offending line.
- [ ] No em-dashes and no clause-joining spaced hyphens appear in the edited output; punctuation is ASCII-only.
- [ ] The 3-5 identified voice signals are preserved in the edited draft (strong human sentences left intact).
- [ ] Every referring expression resolves for a reader at HEAD with no transcript: no citation points at an unshipped option, and no temporal contrast appears outside a changelog, migration guide, deprecation notice, or incident timeline.
- [ ] `python scripts/detect_prose_cliches.py <file>` was run (first in Detect mode, after editing in Edit mode) and its `defect` count on the returned draft is zero.
- [ ] Every chatbot leftover in the draft is gone in Edit mode, or named as a defect (not a flagged style) in Detect mode.
- [ ] Each `Robotic rhythm` finding cites the rule number and the run that tripped its threshold, so the same finding is reproducible by the offline detector.
- [ ] The output was graded against `references/self-check.md` and every check passes.

## Related Skills

- [[writing-editing]] -- general clarity, concision, structure, and active-voice editing; the default for any writing task that is not specifically about the AI-slop failure mode.
- [[hallmark-design]] -- the visual counterpart, removing the "looks AI-generated" signature from UI rather than from prose.
- [[technical-writer]] -- produces audience-appropriate technical documentation from scratch; hand a de-slopped draft to it, or run this skill over its output.
- [[strategic-comments]] -- the same "cut the noise, keep the signal" discipline applied to in-code explanatory comments.
