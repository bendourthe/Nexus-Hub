# Design Invariants

Summary: three structural invariants that keep one domain's logic in one place: one owning module per domain, enumerate every copy before consolidating, and no business logic in rendering.
Read this when: a change adds to or consolidates logic (a formula, a format string, a threshold) that already appears in more than one module, or a review finds a value computed inside a template, client script, route, or view builder.
Covers: what each invariant requires, the signals that it is broken, and how to check a consolidation is complete.

## 1. One owning module per domain

Each domain (pricing, display formatting, alert thresholds, permissions) has exactly one module that owns its rules, and that module documents them in one place, a docstring or a rules doc beside it. Every other module asks the owner rather than re-deriving the answer.

- Consolidate a scattered domain before adding to it. A new rule added to one of several copies makes the copies disagree.
- A function-level import added to dodge a circular dependency is a signal that the logic sits in the wrong module. Move the logic to the owner, or move the shared piece into a module both sides can import at the top, instead of hiding the cycle inside a function.

## 2. Enumerate every copy before consolidating

Before moving logic, find all of it:

1. Search for the expression itself (the arithmetic, the format string, the threshold value), not only for a function name, since copies are often inlined.
2. List every copy with its file and line.
3. Move the logic into the owner.
4. Switch every caller to the owner, or name each copy left in place and why.

A new helper beside old copies is one more duplicate. The consolidation is complete only when a search of the final tree finds the expression in exactly one definition and every original caller uses it.

Preserve each caller's exact results while switching it. Copies drift: one copy may guard against zero, round to two places, or clamp to a range that another omits. Carry each difference into the owner explicitly (a parameter or a named variant), and prove it with that caller's existing tests, rather than silently adopting one copy's behavior for everyone.

## 3. No business logic in rendering

Templates, client scripts, routes, and view builders display values; they never compute them. A total, a status, an eligibility check, or a threshold comparison belongs to the domain owner, which hands the rendering layer a finished value.

Signals that this is broken: arithmetic or comparisons inside a template, the same calculation in a server route and in browser code, or a view builder that queries and decides instead of formatting.

## Sequencing

When the consolidation makes room for a requested change, follow [[refactoring-expert]]'s refactor-first step for the order of the two steps and how each is verified; this reference does not restate it.

## Follow-up

After a consolidation, measure it with `technical-debt-analyzer`'s `references/subsystem-baseline-review.md`: a baseline table, the same table re-measured, and a ratchet check per consolidated domain.
