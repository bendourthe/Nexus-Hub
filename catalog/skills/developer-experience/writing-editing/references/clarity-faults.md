# Clarity Faults

Summary: a judgment-based reference for the three clarity faults in prose a person reads, a point-first check that comes before them, how to repair each fault, and how to measure an unclear rate on a sample. `writing-editing` owns it, and `anti-slop-editing` Detect mode applies it as a second output section. No lint backs it.

A text can pass every cliche check and still be hard to read. Cliche signatures and clarity faults are independent, so a clean cliche scan is not a clarity check. Run the cliche scan with `anti-slop-editing` and run this reference separately.

## Point-First Check

Run this check before looking at sentences.

1. Write in one sentence what the text wants its reader to know.
2. If that sentence cannot be written, or most of the text does not serve it, rebuild the text from that sentence. Do not repair sentence by sentence.
3. If the point is the author's to supply, ask the author. Do not invent it.

A text that fails this check has no sentence-level fix.

## Fault 1: Hidden Actor or Action

The actor is buried in a noun, or the action is turned into a noun. The reader has to rebuild who did what.

- Before: "The tool performs validation of the input before the execution of the job."
- After: "The tool validates the input, then runs the job."

Repair: make the actor the subject and the action a verb. Nominalizations such as "performs validation of", "makes a determination", and "is in agreement with" are the usual signs.

## Fault 2: Vague Wording

The reader cannot tell what a word points to, or the wording is hard to parse. Four forms occur, plus one more in the compressed-syntax family.

- Unclear reference. Before: "The cache was cleared and the build restarted. This fixed it." After: "Clearing the cache fixed the stale-build error."
- Noun stack (three or more nouns in a row). Before: "the user session token expiry handler". After: "the handler that expires user session tokens".
- Word pairing a person would not say. Before: "The service executes a lookup of the record." After: "The service looks up the record."

Compressed syntax, one example each:

- Noun stack: "release candidate build artifact checksum" becomes "the checksum of the build artifact for the release candidate".
- A noun pressed into service as a verb: "We will owner the migration." becomes "We will own the migration."
- A dropped "that": "The file the script reads the target from is edited each release." becomes "The file that the script reads the target from is edited each release."
- A subject waiting behind a long list for its verb: "The importer, which reads the schema, checks each row, skips empty ids, and logs counts, stops." becomes "The importer stops. Before it does, it reads the schema, checks each row, skips empty ids, and logs counts."

Repair: name what the pronoun refers to, break the stack with a preposition or a verb, and use the wording a person would say aloud.

## Fault 3: Empty Statements and Misplaced Emphasis

The sentence carries no claim, or it stresses the wrong thing.

- Empty. Before: "There are many factors to consider here." After: delete it, or name the factors.
- Misplaced emphasis. Before: "It is worth noting that the deadline is Friday." After: "The deadline is Friday."
- Certainty without its evidence. A word such as "byte-identical", "verified", or "nothing" stands in for a check that the sentence does not name. Before: "The output is byte-identical." After: "The output matches the saved copy under a byte comparison."

Repair for certainty: name the check or its scope. Do not swap in a hedge instead. A certainty word whose check is cited in the same text is fine.

## Overcorrection Guard

A repair must not make the text worse.

- A rewrite that is shorter but slower to parse is worse. Prefer the longer sentence when the shorter one is harder to read.
- Keep first-person judgment and varied sentence length.
- This guards prose a person reads. It does not govern command output, which Output Minimization governs.

## Repair Rule

A vague sentence becomes specific only with a fact from the source or from the author. Without one, ask or cut. Do not invent a specific. For dropped claims, use the preservation check in `anti-slop-editing` (v4.22.0) instead of restating it here.

## Annotation Procedure

Use this to measure an unclear rate on a sample.

1. Take a sample of sentences from the text.
2. Mark each sentence with zero or more fault labels: actor or action, vague wording, empty statement.
3. Report the share of sentences with at least one label.
4. The annotator must not be the session that wrote the sample. When that is impossible, the report says the read was not independent.

The rate describes the sample only. It is not a score of the author or of the model.
