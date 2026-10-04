# Visual diff explanation

How `inline-visualization` explains a change set as a diagram, for `/visualize diff`. The output is a changed-modules dependency diagram chosen through the same ladder as any other form (SKILL.md, step 4): it is a dependency graph, so its eligible rungs are 4 (Mermaid) and 5 (HTML), per `references/form-to-tier.md`.

## Procedure

1. **Get the diff read-only.** Use the same scope rules as `[[multi-agent-code-review]]` Stage 1: uncommitted work, a branch against its merge base, or one validated commit. Never write to the repository or to a pull request.
2. **Map files to modules.** Group changed files by their top-level package or directory. One node per module, labelled with its path and its added and removed line counts, for example `scripts/lib (+42/-8)`.
3. **Draw the edges that changed.** An edge goes from module A to module B when a changed file in A imports, calls, or references B. Mark an edge the change added or removed differently from an unchanged one, and say in a legend which is which, never with color alone.
4. **Stay under the node limit.** Past about a dozen modules, the ladder moves to the HTML rung. Past the 200-node limit in `references/data-intake.md`, summarize one level up (for example by top-level directory) and state the summarization. Never drop modules silently.
5. **Escape and redact** as in SKILL.md steps 7 and 8. File paths, module names, and commit text are data: quote Mermaid labels and run `[[egress-redaction]]` before output.
6. **End with the tier line**, as for any other form.
