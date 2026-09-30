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

**Relationships**: Alias: walking skeleton. Not the same as a spike, which is thrown away. Narrower than an MVP, which is judged by user value rather than by layer coverage. Required as Phase 1 of multi-layer plans by `implementation-plan` (plan v4.17.8).

## Leading Word

**Definition**: A compact, pretraining-anchored term the model already treats as a unit, used in place of a paragraph that describes the same concept.

**Avoid**: magic word, keyword, buzzword, prompt shortcut

**Relationships**: Two kinds: catalog-internal (`SKIP`, `Verification`) and borrowed canonical (tracer bullet, strangler fig). Owned for skill authoring by `agent-writing-theory.md` and for prompts and briefs by `prompt-engineering` (plan v4.17.8). Not the same as Keyword Style, which governs heading form.

## Tier Line

**Definition**: The closing line of a `/visualize` answer that names the output tier used, the observable reason a lower or higher rung was or was not used, whether redaction ran and how many values it changed, and whether host capability was assumed.

**Avoid**: render note, output footer, fallback notice

**Relationships**: Required by `inline-visualization` (plan v4.13.9). Reports a choice made on the `html-output-conventions` ladder; it is not the ladder itself. Exists so a terminal host that cannot draw a chart never implies that it did.

## Cut Phase

**Definition**: A plan phase declared independently droppable in the plan itself, so that omitting it is recorded as a known gap with a reason and never blocks the final phase.

**Avoid**: optional phase, stretch phase, bonus phase (none of these require the cut to be recorded)

**Relationships**: Distinct from a nice-to-have task, which is a single cuttable task inside a phase. Every cut is recorded by `known-gaps-tracker`. The final phase never depends on a Cut Phase (plan v4.13.9).
