# Decision Note - Does `/test` coverage or task-scope restraint govern when they disagree?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md`, sub-task 5.2 (T019)
**Date**: 2026-09-05
**Decided by**: the maintainer, at the Phase 1 to Phase 2 boundary, after the plain-language walkthrough

## The two rules

`/test` (`catalog/commands/test.md`) drives coverage to a standardized threshold (80 percent line coverage by default) with a 100 percent pass rate, tier by tier, generating tests until the threshold is met. The vendor-documented restraint rule says to commit tests only where the task asks or the repository already keeps them for that change class, sized like the neighbouring test files at roughly one focused test per stated behavior, and never to promote scratch checks into permanent test files. On one task these give opposite instructions: `/test` says write until the number is reached; restraint says write what the task asked for and no more.

## What each optimizes for

`/test` optimizes for a measured floor on a codebase, which is what a user invoking it wants. Restraint optimizes for a diff that stays the size of its task, which is what every other change wants. The repository's own test-retention policy in AGENTS.md already separates tests that validate durable behavior from tests that assert transitional detail, and tells maintainers to delete the second kind; that is restraint's intent stated from the other end.

## Options presented

- **(a) `/test` governs when explicitly invoked; restraint governs otherwise.** A user who asks for coverage gets coverage; an agent doing any other task does not grow the test suite beyond the task.
- **(b) Restraint always governs; `/test` is rescoped** to raise coverage only where the task asks. Changes the command's contract for users who rely on it.
- **(c) The threshold becomes advisory** rather than a gate. Weakens an existing quality gate for every user.

## Decision

**(a).** `/test` governs when explicitly invoked. Everywhere else, the restraint rule governs, and it concerns extras only: tests for behavior the task did not ask for. Coverage that a verification owner requires (`verification-before-completion`, the security and accessibility owners) is not an extra, and `minimal-construction` already refuses to cut those floors. Both `minimal-construction` and `catalog/commands/test.md` cite this note so the boundary is findable from either side.

## What it changes for a user

Running `/test` behaves exactly as before. Any other task no longer accumulates tests beyond what it asked for, and scratch checks written while debugging are not promoted into the suite; a follow-up is reported instead.
