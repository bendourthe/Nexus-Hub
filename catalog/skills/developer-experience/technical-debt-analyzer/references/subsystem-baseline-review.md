# Subsystem Baseline Review

Summary: a measured before-and-after review of one subsystem: record a baseline table, plan behavior-preserving steps, re-measure with the same table, report the delta row by row, and leave a ratchet check per consolidated domain.
Read this when: a subsystem holds the same formula, format, or threshold in several places and you want to show, with numbers, that a consolidation actually reduced it.
Covers: choosing the subsystem, the baseline table, planning the steps, the re-review, and the ratchet checks.

## 1. Pick one subsystem

Choose one bounded subsystem, such as pricing, report formatting, or alert thresholds. A review of a whole codebase produces totals nobody can act on; one subsystem produces rows that map to specific edits.

## 2. Record the baseline

Measure before changing anything and record the numbers in a table:

| Row | How to measure | Baseline |
|---|---|---|
| Files holding the subsystem's logic | search for each expression and list the files | |
| Copies per formula or threshold | count definitions of each expression, inlined copies included | |
| Copies that disagree | compare each copy's guards, rounding, and clamps | |
| Rule checks passing | run the project's own checks for the domain (tests, lint rules, ownership checks) | |

Keep the exact search patterns and commands with the table, so the re-review measures the same thing.

## 3. Plan behavior-preserving steps

List the consolidation steps in order, each small enough to verify on its own. Each step keeps every caller's results unchanged; the rules for consolidating copies are in `code-simplification`'s `references/design-invariants.md`, and the order of refactor and change follows [[refactoring-expert]].

## 4. Re-review with the same table

After the steps land, rerun the same searches and commands and fill a second column. Report the delta row by row (files, copies, disagreeing copies, checks), naming any row that did not move and why. A consolidation that leaves the copy count unchanged has moved code, not removed duplication.

## 5. Add a ratchet check per consolidated domain

For each domain you consolidated, add one check that fails when a copy returns, such as a test that searches the source tree for the expression and asserts it appears in exactly one definition. Run it with the project's normal checks, so the review's result cannot quietly erode.
