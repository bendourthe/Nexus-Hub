# Decision: The Writing Discipline rule binds live chat replies, not only generated files

Status: implemented - every substantive instruction template carries an always-loaded `## Writing Discipline` block whose self-check clause names chat replies explicitly; the lockstep parity guard byte-compares it and a companion validator asserts it on the seven unguarded templates

## Problem

The v4.5.0 comparison against a prose-cliche detection source found that Nexus-Hub's only always-loaded writing rule was a Claude-only `## Communication Style` section (ASCII punctuation, no em-dashes, teaching tone), while the cliche catalog in `anti-slop-editing` loads only when an agent decides to edit prose. The moves the source names most often (throat-clearing openers, "not just X, but Y" contrasts, importance puffery, weasel attribution, faux-insight setups, trailing "-ing" analysis, fake-profound closers, recap endings, chatbot leftovers) appear as readily in a live chat reply as in a generated file, and a rule that reaches only files leaves the reply, which the user reads first and most, ungoverned.

Two facts shaped the choice. An instruction file is in context on every turn, so anything placed there is paid for on every request. And the difference between "do not write this way" and "check what you wrote before you return it" is not wording: the first is a preference the model weighs against fluency, the second is a step it performs.

## Decision

Every substantive instruction template (the five lockstep files plus `base-google-shared.md`, the five guardrails-only files, and `generic-instructions.md`) carries a byte-identical `## Writing Discipline` block of 163 words. Its self-check clause reads: "before returning any response or writing any file, scan your own output against this list and fix what you find. This binds live chat replies, not only generated documents." The block absorbs the former Claude-only punctuation rule, so that rule now reaches every platform, and the Claude-only section is retired.

Enforcement is mechanical in two tiers. `scripts/check_base_template_parity.py` treats `Writing Discipline` as an invariant block across the lockstep five. `tests/validators/test_writing_discipline_rule.py` asserts presence, byte identity, the self-check marker, the word and line budget, and ASCII-only text across all twelve, and asserts absence from the four include-only shims. Breaking any one of the twelve fails the validator; breaking a lockstep file also fails the release gate. The five word ceilings in `docs/policy/doc-budgets.json` were raised by exactly the measured delta, recorded under Recorded raises.

## Alternatives considered

- **Prohibition only, no self-check.** A list of forbidden moves with no instruction to re-read the output. Rejected because a prohibition competes with fluency at generation time and loses often; the self-check turns the rule into a step with an observable action (scan, fix), which is what the platform-wide detector in `anti-slop-editing` can later measure against. Cost difference is one sentence.
- **Self-check scoped to files.** "Before writing any file, scan it." Rejected because the reply is the surface the user meets first, the comparison's evidence came from chat output as much as from documents, and a file-only clause would have let the rule's most visible failure mode continue while reporting compliance. The stronger reading costs no additional words.
- **On-demand skill only, nothing always loaded.** Leave the catalog in `anti-slop-editing` and rely on the agent to trigger it. Rejected because the source's patterns occur in every reply, not only in editing tasks, and a skill that loads on trigger cannot govern a reply the agent did not classify as prose work. Zero per-turn cost, which is why it was the default before this decision and why it failed.
- **Hook-enforced detection on every reply.** Run the offline detector as a `Stop` hook. Rejected for this release: the detector's defect class is narrow by design (chatbot leftovers, forbidden Unicode), the advisory class needs judgment, and a hook that flags advisories on every turn trains the user to ignore it. The detector ships as a skill-bundled script the agent runs in Detect and Edit modes; a hook can be reconsidered once the false-positive rate on real replies is known.

## Consequences

- Every platform pays roughly 215 tokens per turn for the block (163 words at about 1.3 tokens per word), once per platform in use; prompt caching makes repeat reads cheaper but not free. The measured cost and the ceiling raise are recorded in `docs/releases/v4/v4.5/development/writing-discipline-block.md` and `docs/policy/doc-budgets.md`.
- Whether the clause improves replies or merely stiffens them is not something a test can decide. The v4.5.0 plan names a human check (ask a question that ordinarily draws a cliche-heavy answer on two platforms and judge the change); it is recorded as an open deferred item in `docs/releases/v4/v4.5/known-gaps.md` until a person runs it.
- The block is guidance, not enforcement. It grants no authority, transmits nothing, and a consuming project's own `CLAUDE.md` or equivalent can override it. Runtime adherence is not proven by parity, only distribution is.
- Editing the block now means editing the source-of-truth file first and propagating to twelve templates; the validator makes a partial propagation a failing test rather than a silent drift.
- The former Claude-only punctuation rule now reaches every platform, which is a behavior change for eleven of them; it is the same rule Claude Code users have had since the section was introduced.
