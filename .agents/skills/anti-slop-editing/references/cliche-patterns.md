# Cliche Patterns: The Reflective Register and Its Neighbours

This reference extends the Named-Pattern Catalog in `SKILL.md` with the patterns that postdate it: the reflective, confessional, essay-voice register that spread through machine-drafted prose in 2025 and 2026, the faux-reveal moves that travel with it, the emphatic-negation and totality constructions, performative honesty, the stranded auxiliary, chatbot leftovers, and mannered prose. Every entry follows the catalog's format: a name in this project's vocabulary, the smell in one line, and an original before and after pair.

How to use this file: `SKILL.md` names the two clusters that change behavior most (chatbot leftovers and the reflective register) and sends you here for the rest. Scan a draft against these entries after the body catalog, and cite the entry name in Detect mode exactly as you would a body-catalog name.

## Two classes, treated differently

Every entry below carries one of two classes, and the distinction matters for both modes and for the offline detector that phase 4 of the v4.5.0 plan ships.

- **Judgment**: a register or move a writer may legitimately choose. A reflective essay can sit with a feeling on purpose; a metaphor can be the precise word. In Detect mode these are flagged, quoted, and left to the writer. In Edit mode they are cut only when they add nothing, and the voice-preservation discipline applies in full. The detector flags them and never fails a document on them.
- **Defect**: text that has no legitimate place in a shipped document, whatever the register. Chatbot leftovers are the whole of this class today. In both modes they are removed, and the detector may fail a document on them.

## Cluster 1: The reflective register (judgment)

The shared smell: the prose adopts the voice of a counsellor or a confessional essayist, addressing the reader's inner life about a subject that has none. It reads as warmth and lands as manipulation, because the warmth is templated.

### Dwelling instruction

Smell: the text tells the reader to pause and inhabit a feeling instead of making its point. "Sit with that for a moment." "Let that land."

- Before: "The migration deleted the index. Sit with that for a moment."
- After: "The migration deleted the index, so every lookup became a full scan."

### Naming ceremony

Smell: announcing that something deserves mention instead of mentioning it. "That is worth naming." "This deserves to be said."

- Before: "It is worth naming that the tests were never run before release."
- After: "The tests were never run before release."

### Understated significance

Smell: a double negative that claims importance while pretending modesty. "That is not nothing." "That is no small thing."

- Before: "Cutting the build from nine minutes to four is not nothing."
- After: "The build now takes four minutes instead of nine."

### Presumed knowledge

Smell: flattering the reader with what they supposedly already know, so the claim arrives pre-agreed. "You already know this." "You have felt this."

- Before: "You already know that flaky tests erode trust."
- After: "Flaky tests erode trust: after the third false failure, people stop reading the red."

### The isolated part

Smell: singling out one element as the one that matters, as a substitute for saying why. "That is the part that gets me." "This is the part people miss."

- Before: "The retry loop has no backoff. That is the part that gets me."
- After: "The retry loop has no backoff, so a slow dependency turns one failure into a thousand."

### The lone trusted source

Smell: elevating one thing by dismissing every alternative in a sweep. "The only metric I trust is X." "The only test that matters is the one in production."

- Before: "The only signal I trust is the p99."
- After: "The p99 catches the tail latency the average hides."

### Mock humility

Smell: inviting disbelief to perform confidence. "Do not take my word for it." "Do not just trust me on this."

- Before: "Do not take my word for it. Run the benchmark yourself."
- After: "The benchmark script is in `bench/`; it runs in under a minute."

## Cluster 2: The faux reveal (judgment)

The shared smell: the sentence is staged as a disclosure, so the reader braces for something the text does not deliver.

### The announced punchline

Smell: labelling the conclusion as a punchline or a twist. "The punchline is..." "Here is the twist."

- Before: "Here is the twist: the cache was never enabled."
- After: "The cache was never enabled."

### The discovery frame

Smell: presenting an ordinary fact as something uncovered. "Turns out, ..." "As it happens, ..."

- Before: "Turns out, the config file was read twice."
- After: "The config file was read twice."

### Retroactive significance

Smell: claiming an earlier point mattered, instead of having made it matter. "That is why X mattered." "This is where the earlier decision paid off."

- Before: "That is why the schema decision mattered."
- After: "Because the schema kept ids stable, the migration needed no data rewrite."

### The obituary

Smell: declaring a practice or tool dead to sound decisive. "X is dead." "The monolith is over."

- Before: "Manual QA is dead."
- After: "Manual QA now covers the two flows the browser tests cannot reach."

### Head-sized praise

Smell: praising a design by its supposed mental footprint. "It fits in your head." "You can hold the whole thing in mind."

- Before: "The new API fits in your head."
- After: "The new API has six endpoints, each taking one resource id."

## Cluster 3: Emphatic negation and totality (judgment)

The shared smell: rhythm does the arguing. A chain of negations or a totalizing claim replaces the single positive statement that would carry the point.

### The negation chain

Smell: three or more items stacked as "no X, no Y, no Z", or as "did not X, did not Y, did not Z". The body catalog's Negative listing covers the adjectival form; this entry covers the chained clauses.

- Before: "No config, no setup, no dependencies, no surprises."
- After: "It runs from a single binary with the defaults."

### The verb reversal

Smell: negating a verb and then repeating it as the command. "Do not manage the state. Own it." "Do not ship it. Deliver it."

- Before: "Do not read the logs. Interrogate them."
- After: "Filter the logs by request id before reading them."

### The totality claim

Smell: asserting that one thing is the whole of another. "Context is the whole game." "The entire product is the onboarding."

- Before: "Latency is the entire product."
- After: "Users abandon the search page above 400 milliseconds, so latency is the constraint every feature is measured against."

## Cluster 4: Performative honesty (judgment)

Smell: sincerity announced instead of demonstrated. "I will be honest." "Let us be real." A sentence opening on "Honestly," or "Look,". The announcement implies that what came before was less than honest, and it delays the point.

- Before: "Honestly, the first design was a mistake."
- After: "The first design was a mistake: it coupled the parser to the renderer."

## Cluster 5: The stranded auxiliary (judgment)

Smell: a sentence reduced to a subject and an auxiliary verb, used as a beat. "It is." "They did." "It does not." Often paired with a contrast the previous sentence set up.

- Before: "People think caching is simple. It is not."
- After: "Caching looks simple until two writers invalidate the same key."

## Cluster 6: Chatbot leftovers (defect)

Smell: assistant-role text that belongs to a conversation, leaking into a document. "As an AI language model, ..." "Here is the revised version:" "I hope this helps." "Certainly!" "Great question." These are not a matter of taste. They are a visible defect that announces the document was pasted from a chat window without being read, and they have no legitimate place in a README, a report, a commit message, or a reply that is supposed to be the deliverable.

- Before: "Certainly! Here is the revised version of your deployment guide. I hope this helps."
- After: (cut entirely; the guide begins at its first heading.)

In Edit mode, remove them without asking. In Detect mode, name them as defects rather than as flagged style. The offline detector may fail a document on this class alone.

## Cluster 7: Mannered prose (judgment)

Smell: metaphor and flourish substituted for a direct statement. Instead of "a parameter worth varying", the mannered writer produces "a dial worth turning". Instead of "this point still matters", they write "this point earns its keep".

It fails for two reasons, and the second is the one writers dispute. First, the phrases exist to display the writer rather than to convey the idea, which makes the reader work harder so the writer can perform, and readers can tell. Second, it is imprecise: a metaphor drags in connotations the writer did not choose and cannot control, so "a dial worth turning" imports a picture of continuous, reversible adjustment that the parameter may not have.

The remedy: when a literal phrase is available, use it. A short-form instruction also works on its own and is the minimal intervention when a whole draft needs the pass: "Please remove all mannered prose."

- Before: "Observability is the flashlight you bring into the basement."
- After: "Observability lets you see what the service did when it failed."

This cluster is judgment, not defect. A metaphor can be the precise choice, and a writer who reaches for one on purpose is exercising voice. Flag it, quote it, and cut it only where a literal phrase says the same thing with less.

## Cross-reference

- The three countable rhythm rules (echoing sentence runs, repeated openers, stacked questions) live in the `Robotic rhythm` entry of `SKILL.md`, because a rule with a threshold belongs where the agent reads it every time.
- The offline detector `scripts/detect_prose_cliches.py` encodes the lexical entries above and the three rhythm rules, reports each finding with its class, and deliberately skips mannered prose.
- The lexical long tail of these registers (single phrases that do not warrant a named entry) lives in `references/slop-wordlist.md`.
- The always-loaded `## Writing Discipline` block in every instruction template names the highest-frequency moves in one item each and points at this skill; this file is where those names resolve to examples.
