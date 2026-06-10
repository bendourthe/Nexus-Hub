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

## Notes

- This command replaces `/compile-deep-research` and `/generate-report` (removed in v3.2.0), and surfaces the `deep-research` skill as a first-class `/research deep` scope.
- `deep` already fans out across sources internally; it carries the scope-first token caution and adversarial verification built into the `deep-research` skill.
- Keep this dispatcher thin. The research, compilation, and export procedures live in the retained skills; this file owns only scope resolution and delegation.
