---
description: Specification and governance workflow - clarify an underspecified spec, analyze a feature directory for cross-artifact consistency and coverage, or author/amend the project constitution. Use to "clarify the spec", "drive the spec ambiguities", "analyze spec coverage", "check spec consistency", "write the project constitution", "ratify our principles", "amend the constitution". SKIP - writing a brand-new spec from a vague idea (use /idea-refine first) or implementation planning (use /plan).
---

# /spec Command

Run the specification and governance workflow. `/spec` drives a spec from underspecified to implementation-ready (sequential clarification), audits a feature directory for cross-artifact consistency and coverage, and authors or amends the versioned project constitution that every plan, spec, and ADR aligns with. Bare invocation asks for a scope.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive clarification, analysis, and governance logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `clarify`, `analyze`, `constitution`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a feature directory or spec path, route it to `analyze` and pass it through.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. clarify       (recommended) - sequential 5-question clarification loop to resolve spec ambiguities
        2. analyze       - cross-artifact consistency, coverage, and ambiguity audit of a feature directory
        3. constitution  - author or amend the project constitution (governance principles)

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the retained skill:

      clarify       -> clarify-spec (sequential ambiguity-resolution loop; integrates answers back into the spec)
      analyze       -> analyze-spec (read-only cross-artifact consistency / coverage / alignment report)
      constitution  -> project-constitution (author/amend the constitution end-to-end; placeholder collection, draft, propagation check, Sync Impact Report, write)

Pass any remaining arguments (spec path, feature directory, amend / check sub-mode) through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## constitution scope and the /constitution alias

The `constitution` scope drives the `project-constitution` skill - the same end-to-end governance workflow the old `/constitution` command ran. Because the constitution is cross-referenced by `/plan` (the Constitution Check gate), `analyze-spec` (the constitution-alignment pass), and `project-constitution` itself, `/constitution` is retained as a **permanent** convenience alias that forwards to `/spec constitution` (it is not a v3.x deprecation shim). The `check` sub-mode (`/spec constitution check <plan-path>`) runs the read-only Constitution Check gate against an existing plan.

## Notes

- This command replaces `/clarify-spec` and `/analyze-spec` (removed in v3.2.0). `/constitution` is a permanent alias (see above), not a shim.
- Keep this dispatcher thin. The spec and governance procedures live in the retained skills; this file owns only scope resolution and delegation.
