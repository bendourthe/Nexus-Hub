---
description: Understand a project by producing a clear, structured description of any directory (software or not). Use to get familiar with an inherited project, map a codebase, summarize architecture, or onboard. Trigger phrases - "describe this project", "analyze the codebase", "what is this repo", "help me understand this directory", "give me an overview", "onboard me to this code". SKIP - single-file explanations, line-by-line code reading, or generating a README (use /update docs).
---

# /describe Command

Understand a project by producing a clear, well-structured description of a selected directory. The directory does not have to be a codebase - `/describe` works on any project folder (documents, research, configuration, mixed content) and adapts its sections to what it finds. Reach for it when you inherit an unfamiliar project, need a map of a large codebase, or want a fast path to being productive in a directory you did not write.

This is a thin dispatcher over the retained `analyze-codebase` skill, following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive analysis logic lives in the skill; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `full`, `structure`, `deps`, `architecture`, `onboarding`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a directory path, treat it as the target directory to describe and continue resolving scope (default to `full` when only a path is given).
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. full          (recommended) - complete structured description of the directory
        2. structure     - layout, modules, and how the pieces are organized
        3. deps          - dependencies, external services, and version constraints
        4. architecture  - design, data flow, and key components (with diagrams)
        5. onboarding    - the fast-start guide: what to read first and how to run it

      Reply with a number or a scope name.

- `full` runs the complete `analyze-codebase` flow (every section), then synthesizes a top-level summary.

## Generalization to any directory

Before delegating, detect whether the target directory is a software project (presence of a manifest, source files, version control) or a non-software project (documents, data, mixed content):

- **Software project**: run `analyze-codebase` as written - version detection, structure, dependencies, architecture, Mermaid diagrams, the 12-section report.
- **Non-software project**: adapt the same skill to the content present. Replace "dependencies" with "external references / inputs", "architecture" with "how the material is organized and how the parts relate", and "how to run it" with "how to use or navigate it". Skip sections that do not apply rather than inventing them. The goal is always the same: a clear, well-structured description that makes an inherited project understandable.

State which mode was detected before producing the description.

## Delegation

Dispatch the resolved scope to the retained skill:

      full          -> analyze-codebase (all sections, full report)
      structure     -> analyze-codebase (structure / layout section only)
      deps          -> analyze-codebase (dependencies section only)
      architecture  -> analyze-codebase (architecture + data-flow sections, with diagrams)
      onboarding    -> analyze-codebase (entry points, run instructions, "read this first")

Pass any remaining arguments (for example the target directory path) through unchanged. Heavy logic stays in the `analyze-codebase` skill; this file only resolves scope and delegates.

## Output

The `full` scope writes its report to `docs/<version>/analysis.md` per the `analyze-codebase` skill. Focused scopes produce the corresponding section inline (or appended to the same file when the user is building up a description incrementally). Confirm the output location with the user when it is ambiguous.

## Notes

- This command replaces the deprecated `/analyze-codebase`. The old name forwards here via a deprecation shim through v3.x (removed at v4.0.0).
- Keep this dispatcher thin. If you find yourself adding analysis steps here, they belong in the `analyze-codebase` skill instead.
