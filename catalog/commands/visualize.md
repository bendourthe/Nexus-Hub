---
description: Turn data or a described structure into a chart or diagram at the smallest sufficient rung (table, Mermaid, or a script-free inline-SVG page), ending with a tier line that says which rung was used and why. Trigger phrases - "visualize this", "chart this data", "plot", "show me a graph of", "draw the architecture", "diagram this flow". SKIP - slide decks, charts inside spreadsheets, generative art, a full codebase architecture overview (use /describe architecture), or when a sentence or small table answers the question.
---

# /visualize Command

Turn data (CSV, JSON, a log excerpt, a pasted table) or a structure the user describes into the smallest visual that answers the question. The result may be a sentence, a small table, a Mermaid diagram, or a script-free inline-SVG chart page. Every answer ends with a tier line naming the rung used, why, whether redaction ran, and whether host capability was checked or assumed.

This is a thin dispatcher over the `inline-visualization` skill, following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The rung choice, data intake, escaping, and redaction rules live in the skill; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `chart`, `diagram`, `auto`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` starts with something that is not a recognized scope and is not a file path or data, reply with the recognized scopes and do nothing else.
- If `$ARGUMENTS` is a file path or pasted data with no scope, use `auto`.
- If no data is given at all, ask for it. Never fabricate sample data.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. auto     (recommended) - infer chart or diagram from the input
        2. chart    - data to a chart (bar, line, scatter, distribution)
        3. diagram  - a flow, a dependency graph, or an architecture diagram

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the skill:

      auto     -> inline-visualization (infer the form from the data shape, then pick the lowest eligible rung)
      chart    -> inline-visualization (chart forms only)
      diagram  -> inline-visualization (flow, dependency, and architecture forms only)

Pass the remaining arguments (the file path or the data) through unchanged.

## Notes

- The command never installs a dependency and never calls a network service. A missing renderer or headless browser drops one rung, and the tier line says so.
- Output that leaves the session passes through `egress-redaction` first. If it is unavailable, the output is withheld and the tier line says why.
- Keep this dispatcher thin. Rendering, intake, escaping, and redaction rules belong in the `inline-visualization` skill.
