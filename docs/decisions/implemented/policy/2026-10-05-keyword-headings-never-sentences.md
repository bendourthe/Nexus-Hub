# Decision: Headings are keyword labels, never sentences

Status: implemented - v4.13.10 adds the rule to the shared Writing Discipline block of every substantive instruction template, to the Markdown style guide, and to the anti-slop editing skill.

## Problem

Reviewing the v4.13.10 Training page, the maintainer found section headings written as sentences ("Map the code before touching it", "Turn the finding into a plan") and named the pattern as an AI-writing tell. The same pattern appeared across the guide's pages, together with inconsistent heading styles. Nothing in the harness told an agent to avoid it, so every agent with Nexus Hub installed could reproduce it in any document, page, or interface it generates.

## Decision

Headings are keyword labels: a noun or a short noun phrase ("Project Mapping", "Damage Fix", "Release Notes"), with no verb clause, no trailing period, and no question. The rule binds every heading an agent writes, in documents, plans, reports, slides, web pages, and interface labels.

The rule lives in three places, each with its own job:

- **The Writing Discipline block** of all 13 substantive instruction templates, byte-identical across them (the existing parity validators enforce that), so every platform's agent carries it in context.
- **The Markdown style guide** (`catalog/style-guides/markdown.md`, section 9), beside the other heading rules.
- **The anti-slop editing skill**, as the named pattern "Sentence headings" with before and after examples, so Edit and Detect modes can find and fix it. Its "Formatting slop" entry no longer lists Title Case headings as slop: the rule concerns the form of a heading, not its capitalisation, and the maintainer's own examples are title-cased keyword phrases.

## Alternatives considered

**Leave it to the anti-slop skill alone.** The skill loads only when invoked, so an agent writing a plan or a page would not see the rule. Rejected: the pattern appears in ordinary generation, not only in editing passes.

**Ship the rule in a later minor.** Considered and declined by the maintainer, who asked for it with the Training rebuild that exposed it.

**Prescribe a capitalisation style as well.** Heading case varies by house style and by language; prescribing it would overrule projects with an established convention for no gain against the tell itself. Rejected.

## Consequences

- Every agent with Nexus Hub installed carries the rule from its next install or upgrade, on every supported platform.
- Existing repository documents keep their headings; the rule applies to what agents write from now on. The guide's own pages adopt keyword headings in the same release.
- The anti-slop skill's Detect mode can now flag sentence headings in any draft, and its Edit mode rewrites them as keyword labels.
- The template parity validators keep the block identical across all 13 templates, so a later edit to one template fails until the others match.

## Instruction budget

The rule ships in the always-loaded Writing Discipline block, so it is paid for in every session. It was condensed from 45 to 24 words, keeping the keyword form, an example, the three banned forms, and the full scope. The five lockstep template ceilings in `docs/policy/doc-budgets.json` rise by those 24 words only. Trimming other sections to make room was rejected because it would change rules outside this decision's scope.
