---
name: anti-slop-editing
description: "Edit prose to remove AI-slop patterns (filler, robotic rhythm) and keep the writer's voice, or detect slop without rewriting. For 'de-slop this', 'make it less AI-sounding', 'does this read as AI'. SKIP general writing (use writing-editing)."
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
3. **Scan for the named patterns** in the catalog below. Mark every hit with its pattern name and the exact line.
4. **Consult the word and phrase lists** in `references/slop-wordlist.md` for banned words, often-empty adverbs, and empty phrases. Apply them with judgment, not as a hard lint: cut a word when it adds nothing, keep it when it carries real emphasis, contrast, uncertainty, or the writer's spoken rhythm.
5. **Act on the mode.**
    - Edit: make the minimum effective edit. Fix the flagged lines, leave strong human sentences untouched, and do not reach for a "better" word where the writer's word already works. Then assemble the "What changed" list.
    - Detect: produce the findings list (pattern name, quoted line, short fix) and stop. Do not rewrite.
6. **Self-check before returning.** Grade the output against the rubric in `references/self-check.md`. If any check fails, fix it and re-grade. Repeat until every check passes. This happens inside this one agent; do not spawn a separate evaluator.
7. **Return the result** in the mode's output shape.

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

### Robotic rhythm

Smell: every sentence the same length and shape, so the prose reads metronomic and flat.

- Before: "The tool is fast. The tool is simple. The tool is free. The tool is here."
- After: "The tool is fast and simple, and it is free. Try it."

### Rhetorical setups

Smell: a question posed only so the text can answer it. "But what does this mean for you?" "So why does this matter?".

- Before: "But what does this actually mean? It means faster builds."
- After: "This means faster builds."

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

For the full banned-word, empty-adverb, and empty-phrase lists that back this catalog, see `references/slop-wordlist.md`.

## Voice-Preservation Discipline

The catalog tells you what to cut. This section tells you what to protect. A de-slop pass that flattens the writer into generic "clean prose" has failed, even if every named pattern is gone.

- **Identify 3-5 voice signals before editing.** Sentence-length preference, humor, bluntness, technical density, first-person candor, a signature phrase. Write them down (internally) and treat them as constraints.
- **Make the minimum effective edit.** Change what is slop. Leave the rest. Do not rewrite a sentence that already works just to impose your own phrasing.
- **Leave strong human sentences alone.** A short, punchy, imperfect line that carries the writer's personality is not slop. Resist "improving" it.
- **Keep useful edge and character.** Opinions, mild profanity, a dig, an aside, a rhetorical flourish the writer clearly meant: these are voice, not slop. Cut the machine tells, not the human ones.
- **When in doubt, prefer the smaller edit** or, in Detect mode, flag it as optional and let the writer decide.

## Self-Check Loop

Before returning any result, grade it against the rubric in `references/self-check.md`. If a check fails, fix the output and grade again. Loop until every check passes. All of this happens inside this single agent; there is no separate evaluator agent and no external call.

These three quality surfaces are distinct and do not replace each other:

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
| "There's slop, so I should rewrite the whole thing cleanly." | The minimum effective edit is the rule. A wholesale rewrite that removes slop AND the writer's character has traded one failure for another. Change what is slop; leave what works. |

## Verification

- [ ] The mode is explicit in the response (Edit or Detect), and Detect output contains no rewritten draft, no numeric score, and no AI-authorship claim.
- [ ] In Edit mode, the output includes a "What changed" list naming each pattern removed.
- [ ] Every flagged item cites a named pattern from the catalog and quotes the offending line.
- [ ] No em-dashes and no clause-joining spaced hyphens appear in the edited output; punctuation is ASCII-only.
- [ ] The 3-5 identified voice signals are preserved in the edited draft (strong human sentences left intact).
- [ ] The output was graded against `references/self-check.md` and every check passes.

## Related Skills

- [[writing-editing]] -- general clarity, concision, structure, and active-voice editing; the default for any writing task that is not specifically about the AI-slop failure mode.
- [[hallmark-design]] -- the visual counterpart, removing the "looks AI-generated" signature from UI rather than from prose.
- [[technical-writer]] -- produces audience-appropriate technical documentation from scratch; hand a de-slopped draft to it, or run this skill over its output.
- [[strategic-comments]] -- the same "cut the noise, keep the signal" discipline applied to in-code explanatory comments.
