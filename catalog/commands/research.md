---
description: Deep multi-source research, report compilation, and document export in one command. Use to "research this topic", "do a deep dive on X", "fact-check this with sources", "compile these reports into one document", "merge my research into a single cited doc", "export this markdown to a Word doc / slide deck". SKIP - comparing this project to a specific external source (use /compare) or a quick single-fact lookup you can answer directly.
---

# /research Command

Run deep research, compile existing research, and export reports - the full "gather, synthesize, deliver" surface in one command. `/research` fans out web searches with adversarial verification and a cited synthesis, merges multiple research documents into one deduplicated and citation-managed report, and exports Markdown to a polished Word document or slide deck via the template-aware generator.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive research, compilation, and export logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `deep`, `compile`, `report`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a research question, route it to `deep` and pass it through.
- If `$ARGUMENTS` is a list of document paths / URLs, route it to `compile`.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. deep     (recommended) - fan-out multi-source web research with adversarial verification and a cited synthesis
        2. compile  - merge multiple research reports into one deduplicated, citation-managed document
        3. report   - export a Markdown document to a Word (.docx) or PowerPoint (.pptx) report via a template

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the retained skill:

      deep     -> deep-research (fan-out search, source fetch, adversarial claim verification, cited report)
      compile  -> compile-deep-research (merge .docx/.md/.pdf/.pptx/.html/URL/.txt sources into one cited document)
      report   -> generate-report (Markdown -> .docx / .pptx using a project or global template)

Pass any remaining arguments (the research question, source list, target format, template name) through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## Completion evidence (ADVISORY in this release)

Every research and compile run appends this block to its closing summary, computed from the deliverable itself. It gives the run a finish line other than the producer's own confidence.

Report each item as a count and, where it is a proportion, as a fraction:

- **Citation coverage**: factual claims carrying at least one source, over all factual claims. A claim with no citation is COUNTED AS UNCOVERED and listed; it is never dropped from the denominator to improve the fraction.
- **Duplicate sources**: distinct URLs or works cited more than once under different labels, which is how one source silently becomes two corroborating ones.
- **URL resolution**: cited URLs that resolved during the run, with every unresolved one listed by reason (timeout, non-200, paywall). Only URLs the run already fetched are counted; this block adds no new fetch, no script, and no dependency.
- **Required sections present**: the requested template's sections, each marked present or missing.
- **Source freshness**: the oldest and newest source dates in the deliverable.

Two rules make the numbers honest rather than flattering. An unresolvable URL is recorded as unresolved with its reason, never as resolved and never as a hard failure of the run. And when these metrics conflict with the user's explicit scope (they asked for a paywalled corpus, say), the block still reports the numbers AND states the conflict.

A third rule keeps a zero from reading as a failure. When the corpus is entirely LOCAL (files, a repository, documents the user supplied), URL resolution is reported as `0 of 0` WITH the reason "local corpus, no web sources", because a bare zero next to four healthy metrics reads as a broken run. Citation coverage and freshness still apply in that case; they resolve against the local documents and their dates rather than against URLs.

**This block is advisory in v4.8.0: it reports and never blocks.** The reason is specific, not timidity: no measured baseline exists yet for what citation coverage a good deliverable of each type actually reaches, and a threshold picked without one would either pass everything or fail honest work. Setting a blocking threshold is a later release's decision, to be made from the numbers this block starts collecting.

The verifier classes involved here (deterministic for sections, duplicates, and resolution; evidence-based for coverage and freshness) are defined in [`ai-output-evaluation/references/verifier-taxonomy.md`](../skills/developer-experience/ai-output-evaluation/references/verifier-taxonomy.md), whose natural-verifier table lists these same checks under deep research and report generation.

## Notes

- This command replaces `/compile-deep-research` and `/generate-report` (removed in v3.2.0), and surfaces the `deep-research` skill as a first-class `/research deep` scope.
- `deep` already fans out across sources internally; it carries the scope-first token caution and adversarial verification built into the `deep-research` skill.
- When the user instead wants a portable brief to hand to a human researcher or an external deep-research tool, apply the `prompt-engineering` research-brief authoring technique to produce one self-contained paragraph; `/research` otherwise executes the research itself.
- Keep this dispatcher thin. The research, compilation, and export procedures live in the retained skills; this file owns only scope resolution and delegation.
