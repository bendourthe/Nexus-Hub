# Decision: Govern live-response communication with one canonical style guide

Status: implemented - `catalog/style-guides/agent-communication.md` is the single source of truth, distributed as a compact parity-locked pointer section in all 12 substantive instruction templates plus an `agent-communication` skill

## Problem

Nexus-Hub governs how agents write **documents** (`catalog/style-guides/markdown.md`, plus the `writing-editing`, `anti-slop-editing`, and `technical-writer` skills) and almost nothing about how agents write **chat responses**. Before this decision, the only live-response rules were four bullets under `Communication Style` in the instruction templates plus the `End-of-Task Summary` block, and the one per-response structure block that existed (`generic-instructions.md`, `## Response Format`) was not distributed to any platform at all.

The observed failure modes follow directly from that gap, and they are cross-platform:

- Template placeholders (`<container-name>`, `[YOUR_TOKEN]`) pasted verbatim into terminals, where they fail.
- A corrected step issued after an error without restating the remaining sequence, leaving the user to reassemble the instructions from two places in the scrollback.
- Wordy, jargon-heavy end-of-task reports that a non-engineer cannot act on.
- Technical detail inlined into a chat response instead of linked to a readable file.
- Turns that end with work still running, where the one sentence that matters ("tests are running, wait") is buried under a wall of implementation detail.

The constraint that shaped the answer: `docs/policy/doc-budgets.json` ceilings ratchet DOWN and never up. At the time of this decision the headroom was +133 words on `base-claude.md` and +94 or +95 on the other four lockstep templates. Whatever governs communication cannot be spelled out in the templates themselves.

## Decision

One canonical artifact, thin distribution, machine-locked against drift.

1. **`catalog/style-guides/agent-communication.md`** is the single source of truth. It covers seven areas: response structure, plain language, placeholder discipline in commands, the guided-steps protocol, the end-of-task report shape (Completed / Verified / Open / Next), the docs deep-link rule, and waiting-state interim updates. Every rule is written as a checkable behavior, never as an adjective. The guide states its boundary against `markdown.md` in its opening paragraph: this guide governs live responses, `markdown.md` governs files written to disk.
2. **Distribution channel A, always loaded**: a compact `## Communication Contract` section of at most 90 words in all 12 substantive instruction templates, ending with a deep link to the installed guide. `scripts/check_base_template_parity.py` treats it as an invariant block, so its body must be byte-identical across the five lockstep templates.
3. **Distribution channel B, loaded on demand**: the `agent-communication` skill under `catalog/skills/developer-experience/`, with the worked examples in a Tier-3 `references/` file so the detail costs nothing until the skill triggers.
4. **Workflow touchpoints**: the highest-traffic report producers (`implement-phase` completion report, `/plan` presentation, `/update release` closing output) prescribe the contract's report shape directly, so the outputs improve even for a user who never reads a template.

The installer needs no edit for any of this. `catalog/style-guides/` and `catalog/skills/` are already copied recursively.

## Alternatives considered

- **Inline the full contract into every instruction template.** Rejected: the doc-budget ceilings ratchet down and headroom was roughly 90 to 130 words per lockstep file. A 200-line contract inlined 12 times would either blow every ceiling or force ceiling raises, which the budget policy forbids without justification. It would also make the contract 12 files to keep in sync instead of one.
- **Enforce the contract with a hook gate.** Rejected: prose tone is not machine-checkable at `PreToolUse` time. A hook can check that a file exists or that a command matches a pattern; it cannot check that a response led with the outcome or that a term was defined in place. Hooks stay advisory here, and the parity gate covers the part that IS mechanical (that every template carries the same section).
- **Widen the scope of `markdown.md`.** Rejected: it governs generated files, and its readers are people writing READMEs and reports. Blurring it into live-response guidance would make both contracts harder to apply, because an agent reading it would no longer know which reader it is optimizing for.
- **Ship only the skill, with no template section.** Rejected: a skill loads on trigger, and the failure modes appear on turns that would not trigger a communication skill (an ordinary implementation turn that happens to end with a command block). The always-loaded pointer is what makes the contract apply by default; the skill is what makes the detail affordable.
- **Do nothing.** Rejected: the failure modes above are observed, cross-platform, and cost the user real time. An unfilled placeholder pasted into a terminal is a failed command; a corrected step with no remaining sequence is a scrollback hunt.

External grounding for the specific rules:

- Placeholder discipline: the GitHub CLI command-line-syntax documentation and the Google developer documentation style guide both warn that bracketed placeholders break copy-paste, and that click-to-copy examples must avoid brackets, pipes, and braces.
- Instruction writing: plain-language guidance and cognitive-load research converge on a grade 7 to 8 reading level, prerequisites stated first, one action per step, and restating the remaining sequence after a correction.
- Rule phrasing: community experience with always-loaded instruction files is that vague directives ("be concise") are ignored while measurable ones ("re-issue all remaining steps renumbered") are followed. Every rule in the guide is therefore testable.

## Consequences

- **One place to change communication policy.** A rule change edits the style guide; the templates carry a pointer, not a copy. The cost is one level of indirection for a reader who only has the template.
- **The parity gate covers five of twelve templates.** `check_base_template_parity.py` has a five-file roster by design, so the guardrails five, `base-google-shared.md`, and `generic-instructions.md` are not byte-locked. A data-driven aggregate test asserts all 12 carry the section heading, which catches an omission but not a wording drift in the non-lockstep seven. This residual risk is tracked in the version's known-gaps file.
- **The template section consumes scarce budget.** Roughly 85 words land in each lockstep template against headroom of 94 to 133. Future additions to those files have correspondingly less room, which is the intended direction of the ratchet.
- **The contract is unenforced at runtime.** Nothing blocks a response that violates it. The guide's own Verification checklist is the audit mechanism, and it is only as good as the agent's willingness to run it.
- **Two style guides now exist with adjacent names.** The boundary statement in each opening paragraph is load-bearing. If a future edit blurs it, an agent will apply file-formatting rules to chat responses or the reverse.
