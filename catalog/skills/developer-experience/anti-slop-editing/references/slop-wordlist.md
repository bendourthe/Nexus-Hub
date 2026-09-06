# Slop Word and Phrase Lists

These lists back the `anti-slop-editing` skill. They are the vocabulary that most reliably signals machine-drafted prose. Treat them as guidance an editor applies with judgment, NOT as a hard lint. Cut a word when it adds nothing. Keep it when it carries real emphasis, contrast, uncertainty, or the writer's spoken rhythm. Flattening every listed word out of a draft damages legitimate voice, which is the opposite of the goal.

How to use this file: after scanning a draft for the named patterns in `SKILL.md`, check it against these lists. For each hit, ask "does this word do work here, or is it filler?" before cutting. In Detect mode, name the list ("banned word", "empty adverb", "empty phrase") and quote the line; do not rewrite.

## Banned words (usually empty when they appear in AI prose)

These are inflated or vague words that a plainer word almost always beats. The parenthetical is the usual plain replacement.

- delve (into) -> look at, examine, dig into
- foster -> encourage, build, support
- leverage -> use
- utilize -> use
- facilitate -> help, make easier
- empower -> let, enable, give
- streamline -> simplify, speed up
- robust -> (name the actual property: reliable, well-tested, handles retries)
- seamless / seamlessly -> (usually cut; or name what is smooth)
- cutting-edge / state-of-the-art -> (cut, or name the actual capability)
- game-changing / revolutionary / groundbreaking -> (cut; show the change instead)
- unlock / unleash -> (cut, or name what becomes possible)
- harness -> use
- supercharge / turbocharge -> (cut, or give the number: 3x faster)
- elevate -> improve, raise
- navigate (the complexities of) -> handle, work through
- realm / landscape / space (as in "the AI landscape") -> (cut, or name it)
- tapestry / symphony / ecosystem (as forced metaphor) -> (cut)
- vibrant / rich (as filler adjectives) -> (cut, or be specific)
- meticulous / meticulously -> carefully, or (cut)
- comprehensive -> (cut, or say what it covers)
- crucial / vital / pivotal / paramount / essential -> important, or (show why it matters)

Keep-it examples (do NOT cut): "robust retry logic with exponential backoff" (robust names a real property), "we use bcrypt to hash passwords" (use is already plain), "this is essential: without it the migration corrupts data" (essential earns its place because the sentence then shows the stakes).

## Often-empty adverbs and intensifiers

These frequently add nothing and can be cut without changing meaning. Keep one when it carries genuine emphasis or the writer's voice.

- just
- literally
- honestly
- simply
- actually
- really
- very
- truly
- basically
- essentially
- clearly
- obviously
- definitely
- certainly
- arguably
- notably
- importantly
- ultimately

Keep-it example: "just run the installer, nothing else" (just carries the "and nothing else" emphasis). Cut-it example: "this is just a simple tool that just works" (both instances are filler).

## Often-empty phrases

These are throat-clearing, hedging, or recap phrases. Most can be cut whole; the sentence is stronger without them.

- it's worth noting that
- it's important to note that
- it's important to remember that
- at the end of the day
- when it comes to
- in today's world / in today's fast-paced world
- in the world of
- at its core
- the fact of the matter is
- needless to say
- as we all know
- it goes without saying
- in order to -> to
- due to the fact that -> because
- in the event that -> if
- for all intents and purposes
- that being said (as filler) -> but, still
- here's the thing
- the truth is
- let's dive in / let's delve into
- in conclusion / to sum up / to wrap up / Bottom Line: / In short: (the labelled closing-summary markers; a reply that has made its point does not need a line announcing that it has. Before: "In short: the cache was the cause." After: "The cache was the cause.")
- last but not least

Keep-it example: "when it comes to money, be precise" is weaker than "be precise about money", but "it comes down to one thing: latency" is fine because the phrase leads to a concrete point.

## Long-tail register phrases

Single phrases from the reflective, faux-reveal, and performative-honesty registers that do not warrant a named entry in `cliche-patterns.md`. Same rule as every list above: judgment, not lint. A writer may use one of these on purpose; cut it when it is templated warmth or a staged reveal, keep it when the sentence would lose something real.

- let that sink in
- read that again
- I will say it plainly
- if I am being honest
- full stop / period (as a rhetorical terminator)
- and that is okay / and that is fine
- quietly (as in "quietly one of the best")
- the real work is / the hard part is
- this is the thing nobody tells you
- most people never / most teams never
- it is easy to forget that
- the more I think about it
- there is a version of this where
- in the same breath
- which is to say
- and yet

Keep-it example: "and yet the test passed" carries a real reversal. Cut-it example: "And yet." as a one-word paragraph is a staged beat.

## Cross-reference

These lists operationalize the always-loaded `## Writing Discipline` block every instruction template carries since v4.5.0 (ASCII punctuation placed outside quotation marks by logic; no em-dashes and no clause-joining spaced hyphens; professional teaching tone; never hard-wrap paragraph text). The anti-slop pass and those rules are the same discipline applied to prose. Punctuation in this file and in all edited output stays ASCII-only: straight quotes, hyphens, and "..." for ellipsis.
