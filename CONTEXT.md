# Nexus-Hub Domain Glossary

Ubiquitous language for Nexus-Hub design discussions, plans, and reviews. Each term carries a definition, the synonyms the project does not use for it, and its relationships. Architecture lives elsewhere; this file names the language only.

## Keyword Style

**Definition**: A title or heading form that names a topic, category, or object as a noun phrase, with no finite verb, no clause, no stated conclusion, and no terminal punctuation (for example "Revenue by Region").

**Avoid**: topic sentence, label sentence, headline

**Relationships**: Required form for every generated title and heading (requirement S1). Not the same as sentence case, which governs capitalization only; "Revenue by region" is Keyword Style in sentence case. Opposite of Full Sentence Style.

## Full Sentence Style

**Definition**: A title or heading form that states an action or an assertion as a sentence (for example "Revenue grew 12% in EMEA" or "Configure database connections").

**Avoid**: action title, assertion title, takeaway title (use Full Sentence Style as the single name)

**Relationships**: Disallowed for generated titles and headings under requirement S1. Covers both imperative action titles and declarative assertion titles. Opposite of Keyword Style.

## Coverage Backfill

**Definition**: Writing tests after the implementation for the purpose of raising a coverage number, rather than to specify or protect a named behavior.

**Avoid**: test hardening, coverage improvement

**Relationships**: The behavior the Testing Discipline rule removes. Not the same as a characterization test (written before a refactor against the pre-refactor revision) or a regression test (fails on the pre-fix revision), both of which remain legitimate. Detected after the fact by `false-confidence-test-audit`.

## Legacy Instruction Block

**Definition**: The contiguous run of lines in an installed instruction file, outside the `NEXUS_HUB_START` / `NEXUS_HUB_END` markers, whose every line exactly matches a line some past Nexus-Hub release shipped; any line the user edited or added is not part of it.

**Avoid**: old install, stale section, pre-marker region (the region may also hold user content)

**Relationships**: Detected by the shared legacy-block detector and removable only by hash-bound consent. Not the same as the managed block (inside the markers) or user content (outside the markers, not fingerprint-matched).

## Skill-Index Pointer

**Definition**: The short block rendered in place of the embedded `{{SKILL_INDEX}}` table, stating that skills are installed natively and where the full index file lives.

**Avoid**: index stub, lazy index, index removal

**Relationships**: Opt-in via `NEXUS_HUB_SKILL_INDEX=pointer`; rendered only where Native Skill Enumeration holds. The full embedded index remains the default.

## Native Skill Enumeration

**Definition**: A platform lists installed skills to the model on its own, from a skills directory Nexus-Hub actually writes for the current install scope.

**Avoid**: skill support, skill-capable (both blur read support with an installed tree)

**Relationships**: Requires both a VERIFIED read path in `docs/policy/platform-read-contracts.json` and a matching Nexus-Hub skill destination for the scope. Gate for the Skill-Index Pointer.

## Tracer Bullet

**Definition**: The thinnest production-quality path that takes real input through every layer a piece of work touches to real output, built first and kept, so later phases widen it rather than add layers it never reached.

**Avoid**: golden path (means an internal-developer-platform paved road in `platform-engineer`), prototype, spike, stub path, hello world (when the work is a multi-layer feature)

**Relationships**: Alias: walking skeleton. Not the same as a spike, which is thrown away. Narrower than an MVP, which is judged by user value rather than by layer coverage. Required as Phase 1 of multi-layer plans by `implementation-plan` (plan v4.19.1).

## Leading Word

**Definition**: A compact, pretraining-anchored term the model already treats as a unit, used in place of a paragraph that describes the same concept.

**Avoid**: magic word, keyword, buzzword, prompt shortcut

**Relationships**: Two kinds: catalog-internal (`SKIP`, `Verification`) and borrowed canonical (tracer bullet, strangler fig). Owned for skill authoring by `agent-writing-theory.md` and for prompts and briefs by `prompt-engineering` (plan v4.19.1). Not the same as Keyword Style, which governs heading form.

## Tier Line

**Definition**: The closing line of a `/visualize` answer that names the output tier used, the observable reason a lower or higher rung was or was not used, whether redaction ran and how many values it changed, and whether host capability was assumed.

**Avoid**: render note, output footer, fallback notice

**Relationships**: Required by `inline-visualization` (plan v4.13.9). Reports a choice made on the `html-output-conventions` ladder; it is not the ladder itself. Exists so a terminal host that cannot draw a chart never implies that it did.

## Cut Phase

**Definition**: A plan phase declared independently droppable in the plan itself, so that omitting it is recorded as a known gap with a reason and never blocks the final phase.

**Avoid**: optional phase, stretch phase, bonus phase (none of these require the cut to be recorded)

**Relationships**: Distinct from a nice-to-have task, which is a single cuttable task inside a phase. Every cut is recorded by `known-gaps-tracker`. The final phase never depends on a Cut Phase (plan v4.13.9).

## Refactor-First

**Definition**: The rule that a change landing in scattered, duplicated, or tangled code is preceded by a behavior-preserving refactor proven by a green test run, and that the refactor and the change are never verified as one step.

**Avoid**: cleanup-first, prep refactor, refactor-and-change (the last names the violation, not the rule)

**Relationships**: Owned by `refactoring-expert` (plan v4.14.2). Sequencing only; what structure to aim for is owned by `code-simplification`'s design invariants. Composes with one local commit per phase: two verified steps inside one phase commit, not two commits.

## Anchor Clause

**Definition**: A distinctive clause of a rule, recorded in a rule-ownership test, whose presence marks the owner file and whose absence from non-owner files is checked as a copy-paste tripwire.

**Avoid**: anchor phrase, rule title, keyword (a title is what a handoff legitimately repeats)

**Relationships**: Used by `tests/skills/test_rule_ownership.py` (plan v4.14.2). Narrower than rule ownership: absence of the clause does not prove a paraphrased restatement is absent.

## UNGATED

**Definition**: A quality-gate outcome meaning the gate could not judge the work, because it has no required criteria, or a required criterion has no evidence. For an automatic criterion, no evidence means no measured value or a zero denominator; for a manual criterion, no recorded judgment.

**Avoid**: skipped, N/A, pass-by-default, inconclusive (the last is `verification-before-completion`'s word for a review that ran without a verdict)

**Relationships**: One of the outcomes in `quality-gate-definitions` (plan v4.14.4), beside PASS, PARTIAL, FAIL (fixable), and FAIL (blocking). Never a kind of PASS. The user-facing "not verified" report it leads to is owned by `verification-before-completion`.

## Harness-Native Index

**Definition**: A memory file the agent itself writes during its turn with ordinary file tools, holding pointers into the `nexus-memory` substrate and harness-only preferences, which the agent repairs when it disagrees with the substrate (Claude Code's `MEMORY.md` is one).

**Avoid**: host memory, native store, second store

**Relationships**: Defined in `docs/policy/memory-substrate-contract.md`. Not the same as a Host-Generated Store, which the agent never writes or repairs (plan v4.14.5).

## Host-Generated Store

**Definition**: A memory store the host platform fills outside the agent's turn, by background extraction or consolidation, and that the vendor documents as generated state not to be edited; Codex Memories under `~/.codex/memories/` is the first instance.

**Avoid**: harness-native index, host index, memory file, platform memory (ambiguous between the two classes)

**Relationships**: Proposed for `docs/policy/memory-substrate-contract.md` by plan v4.14.5. Not the same as a Harness-Native Index. Its content reaches the agent only when the host injects it, and is treated as untrusted data.

## Settings Control

**Definition**: One user-facing default in Nexus-Hub Settings (for example default effort) that maps to one documented key per tool and is offered only after its effect was observed in a fresh session of each tool it writes.

**Avoid**: toggle, switch, preference, option (each suggests a setting with no proof behind it)

**Relationships**: Defined in `scripts/lib/settings_control/catalog.json` (plan v4.14.6). Broader than a vendor key; a control fans out to one key per tool. A control's per-tool cell is either backed by a Proof Record or marked Not-Settable.

## Proof Record

**Definition**: The dated observation, in a fresh session of the real tool, that a settings write changed what the tool did, quoting the observed output or naming the manual observation steps.

**Avoid**: test result, verification, evidence (too broad), docs check

**Relationships**: Required for every Settings Control write (plan v4.14.6, Phase 1). Not the same as a vendor source URL, which proves a key is documented, not that it takes effect.

## Override Layer

**Definition**: Any place that can beat a user-level default in a tool's documented precedence order: an environment variable, a project or repository settings file, a managed or organization policy, a launch flag, or a choice the tool's own UI remembers.

**Avoid**: higher scope, conflict, overwrite

**Relationships**: Reported by `nexus-hub settings show` as `overridden-by <layer>` with a fix line (plan v4.14.6). Read by Nexus-Hub Settings, never written.

## Not-Settable

**Definition**: The catalog state of a tool cell for which no vendor-documented user-level key exists or no Proof Record could be produced, always shown with its reason instead of a control.

**Avoid**: unsupported, disabled, greyed out, coming soon

**Relationships**: Opposite of an admitted Settings Control cell (plan v4.14.6). Each Not-Settable cell a vendor could later make settable is recorded as a known gap.
