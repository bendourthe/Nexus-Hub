---
name: end-of-shift-validation
description: Run one composed, autonomous full-validation pass at the end of an autonomous or night-shift session - tests, performance-regression gate, visual regression, commit sweep, false-confidence test audit, multi-agent review, and lint repair - so the work is as pristine as possible when you return. Make sure to use this skill whenever the user says "end of shift validation", "full validation pass", "run everything before I'm back", "night shift wrap-up", "make it all pristine", "validate the whole session before I return", or wants a single comprehensive pre-return sweep rather than one isolated check. SKIP, do NOT use for, cutting a release (use /update release), a single review or a single test run (use /review or /test), or a one-off check of one dimension (invoke that dimension's skill directly).
summary_l0: "Compose tests, perf, visual, sweep, audit, review, and repair into one end-of-shift pass"
overview_l1: "This skill runs one composed, autonomous full-validation pass at the end of an autonomous or night-shift session so the work is as pristine as possible when the human returns. In a defined order it chains: the full test suite with coverage, the performance-regression gate, visual regression, a commit sweep over the session's commits, a false-confidence test audit of new or changed tests, a multi-agent code review of the session diff, and a lint-repair loop for residual lint - then emits a single consolidated report with a GO / work-remaining verdict and a prioritized follow-up list. It is explicitly NOT a release: it never bumps versions, merges, tags, or pushes (that is /update release). It cross-links the autonomous-run budget controls (hard caps, scope-first) because a full sweep carries a real token cost. Trigger phrases: end of shift validation, full validation pass, run everything before I'm back, night shift wrap-up, make it all pristine."
---

# End-of-Shift Validation

One command, at the end of an autonomous or night-shift session, that runs the full validation battery and leaves a single verdict - so when you return, the work is as pristine as it can be, and anything still open is named and prioritized. This is a composition skill: it orchestrates the individual validators rather than reimplementing them.

## When to Use This Skill

- Wrapping up an autonomous or asynchronous session (a night-shift run, a long unattended loop) and you want everything validated before you look at it.
- Before a release-readiness handoff, to confirm the whole session's work holds together (but NOT to cut the release itself).
- Any time you want one comprehensive pre-return sweep instead of running each check by hand.

**Trigger phrases**: "end of shift validation", "full validation pass", "run everything before I'm back", "night shift wrap-up", "make it all pristine".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Cut a release (version bump, tag, push) | `/update release` |
| Run one review or one test pass | `/review` or `/test` |
| Check a single dimension (just perf, just visuals) | that dimension's skill directly |

## The composed battery (run in this order)

Each step is a cross-linked skill; run it, capture its result, and continue even if one flags issues (collect everything, then verdict).

1. **Full test suite + coverage** - run the project's tests with coverage; record pass/fail and the coverage number.
2. **[[performance-regression-gate]]** - compare current metrics against the committed baseline; record any regression.
3. **[[visual-regression-testing]]** - diff current renders against the baselines; record any above-threshold visual change for review.
4. **[[commit-sweep]]** - sweep the session's commits at altitude for partial refactors, convention drift, and undocumented dependency changes.
5. **[[false-confidence-test-audit]]** - audit new or changed tests for tests that pass regardless of correctness.
6. **[[multi-agent-code-review]]** - review the session diff across reviewer personas.
7. **[[lint-repair-loop]]** - run linters/formatters and repair residual issues, leaving a reviewable diff.

## Verdict and follow-ups

Emit ONE consolidated report: per-step status (ran / passed / flagged, with the key numbers) and a single **GO** or **WORK-REMAINING** verdict. On WORK-REMAINING, list the open items prioritized by severity and offer to open them as tracked follow-ups (`[[tasks-to-issues]]`) or record them in the version's known-gaps log. The value is the single verdict plus a named, prioritized backlog - not a wall of raw output.

## This is NOT a release

This skill NEVER bumps a version, edits a changelog for release, merges, tags, or pushes. Those belong exclusively to `/update release`, which keeps its own confirmation gates. An end-of-shift pass makes the work *reviewable and pristine*; a human (or a deliberate `/update release` invocation) decides whether to ship. Cross-link, do not absorb, the release path.

## Autonomous-run cost and scope

A full sweep composes several multi-step skills and can carry a real token cost (a multi-agent review and a fan-out sweep especially). For unattended runs, put a hard budget cap in place first (`[[ai-billing-safeguards]]`) and calibrate scope before going wide - sweep the session's own commits and changed files, not the whole repository, unless explicitly asked. See `[[loop-engineering]]` and `[[agent-presets]]` for the night-shift orchestration this pass wraps up, and `[[quality-gate-definitions]]` for reusable GO / NO-GO gate definitions.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Everything's pristine, I'll just push it." | This skill validates; it does not release. Pushing from an unattended sweep bypasses the release gates - hand off to `/update release` and let a human decide. |
| "One step flagged an issue, I'll stop the pass there." | Stop-on-first-flag hides the rest of the picture. Run every step, collect all findings, then emit one verdict - a resuming human needs the whole backlog, not the first problem. |
| "Tests passed, so the session is good." | Passing tests are one of seven signals. A green suite with a performance regression, a visual break, or a false-confidence test is not pristine; the composed battery exists because no single check is sufficient. |
| "Run it against the whole repo to be safe." | Unbounded scope on an autonomous run burns budget and buries the session's real deltas. Scope to the session's commits and changed files unless told otherwise; cap the budget first. |
| "I'll just re-run everything myself each time." | Ad hoc re-running skips steps under time pressure and produces no consolidated verdict. The composition is what makes the pass repeatable and its output a single, trackable result. |

## Verification

- [ ] Every composed step (tests, perf gate, visual regression, commit sweep, false-confidence audit, review, lint-repair) ran, and its result is recorded in the report - a skipped step is named, not silently omitted.
- [ ] The report ends in an explicit GO or WORK-REMAINING verdict.
- [ ] On WORK-REMAINING, open items are prioritized and offered as tracked follow-ups (issues or known-gaps).
- [ ] No release action was taken (no version bump, changelog-for-release, merge, tag, or push).
- [ ] For an unattended run, a hard budget cap was in place and scope was bounded to the session's work.

## Related Skills

- [[performance-regression-gate]], [[visual-regression-testing]], [[commit-sweep]], [[false-confidence-test-audit]], [[lint-repair-loop]] -- the per-dimension validators this pass composes.
- [[multi-agent-code-review]] -- the review stage of the pass.
- [[loop-engineering]], [[agent-presets]] -- the autonomous / night-shift orchestration this pass wraps up.
- [[ai-billing-safeguards]] -- the hard budget caps to set before an unattended full sweep.
- [[quality-gate-definitions]] -- reusable GO / NO-GO gate definitions for the verdict.
- [[tasks-to-issues]] -- turns the WORK-REMAINING backlog into tracked issues.
- [[verification-before-completion]] -- the fresh-evidence rule each composed step's result must satisfy.

---

**Version**: 1.0.0
**Last Updated**: July 2026
